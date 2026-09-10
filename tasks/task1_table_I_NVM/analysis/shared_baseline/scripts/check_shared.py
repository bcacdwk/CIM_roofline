#!/usr/bin/env python3
"""Recompute v0.2 templates, R0 regression and bounded sensitivity (stdlib only).

Default is read-only. --emit refreshes generated TeX and sensitivity_results.json.
The formulas model sequential execution; they do not infer pipeline throughput.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE.parents[1]
D = json.loads((BASE / 'data/shared_parameters.json').read_text())
C = D['common_conditions']
L = C['logical_configuration']
P = C['periphery_parameters']
R = D['reference_instance']
V = C['propagation']['profile_values']['reference']


def chunks(total, width):
    assert isinstance(total, int) and isinstance(width, int) and total > 0 and width > 0
    return [min(width, total-start) for start in range(0, total, width)]


def seconds(value, unit):
    return value * {'s': 1, 'ms': 1e-3, 'us': 1e-6, 'ns': 1e-9}[unit]


def metrics(bs, br, ds, dr):
    assert min(bs, br, ds, dr) > 0
    rho, tau = bs / seconds(ds, 'ns'), br / seconds(dr, 'ns')
    return dict(B_S_Byte=bs, B_R_Byte=br, delta_S_ns=ds, delta_R_ns=dr,
                rho_Byte_per_s=rho, tau_Byte_per_s=tau, ridge=rho/tau)


def acim_counts(a, v=V, logical=L):
    ins = chunks(int(8*logical['b_S']), a['input_bits_per_slice'])
    rows = chunks(logical['n_in'], a['rows_per_group'])
    weights = chunks(a['weight_planes'], a['parallel_weight_planes'])
    outputs = chunks(logical['n_out'], a['evaluation_output_width'])
    batches = [chunks(e, a['adc_per_weight_plane']) for e in outputs]
    f = len(ins)*len(rows)*len(weights)
    nr = f*sum(math.ceil(o/a['digital_output_lanes']) for group in batches for o in group)
    needs_hold = any(len(g) > 1 for g in batches)
    window = max(sum(v['adc_batch'] + a['digital_ticks_per_reconstruction_round']
                     * math.ceil(o/a['digital_output_lanes'])*v['digital_tick']
                     for o in group) for group in batches) if needs_hold else 0
    if needs_hold:
        assert a['hold_sample_slots'] >= max(weights)*max(outputs), 'insufficient analog sample slots'
        assert a['hold_guarantee_ns'] >= window, 'hold guarantee shorter than serial readout window'
        assert a['hold_capture_ns_per_evaluation'] > 0, 'explicit hold capture budget required'
    return dict(input_slices=len(ins), row_groups=len(rows), weight_groups=len(weights),
                base_combinations=f, evaluations=f*len(outputs),
                adc_batches=f*sum(len(g) for g in batches), reconstruction_rounds=nr,
                digital_ticks=nr*a['digital_ticks_per_reconstruction_round'],
                useful_scalar_conversions=len(ins)*len(rows)*sum(weights)*sum(outputs),
                adc_total=a['parallel_weight_planes']*a['adc_per_weight_plane'],
                max_batch_code_slots=max(weights)*max(o for g in batches for o in g),
                max_hold_window_ns=window)


def acim_service(a, v, read_ns):
    n = acim_counts(a, v)
    hold = n['evaluations']*a['hold_capture_ns_per_evaluation']
    ds = (n['evaluations']*(v['input_step']+read_ns) + n['adc_batches']*v['adc_batch']
          + n['digital_ticks']*v['digital_tick'] + hold + a['boundary_ticks']*v['digital_tick'])
    return ds, n, hold


def dcim_counts(d, logical=L):
    ni = len(chunks(int(logical['b_S']*8), d['input_bits_per_round']))
    nw = len(chunks(int(logical['b_R']*8), d['weight_bits_per_round']))
    nr = len(chunks(logical['n_in'], d['rows_per_group']))
    no = len(chunks(logical['n_out'], d['output_lanes']))
    nd = ni*nw*nr*no
    reads = nd
    if d['read_reuse_input_slices']:
        reads = nw*nr*no
        assert d['weight_latch_bits'] >= (min(logical['n_in'], d['rows_per_group'])
               *min(logical['n_out'], d['output_lanes'])*min(int(logical['b_R']*8), d['weight_bits_per_round']))
    return dict(input_slices=ni, weight_groups=nw, row_groups=nr, output_groups=no,
                compute_rounds=nd, read_rounds=reads, digital_ticks=nd*d['digital_ticks_per_round'])


def dcim_service(d, v, read_ns):
    n = dcim_counts(d)
    ds = (n['read_rounds']*read_ns+n['digital_ticks']*v['digital_tick']
          +d['latch_extra_ns']+d['boundary_ticks']*v['digital_tick'])
    return ds, n


def front_ns(encoded_bits, td, first_data_in_command):
    beats = math.ceil(encoded_bits/R['resident']['physical_write_data_lanes'])
    assert beats >= 1
    return (R['resident']['control_ticks']+beats-int(first_data_in_command))*td, beats


def direct_service(x, td):
    # Aligned independent cell batches; media with native grouping must enumerate actual batches.
    front, beats = front_ns(x['encoded_load_bits'], td, x['first_data_in_command'])
    batches = math.ceil(x['logical_weights_completed']*x['cells_per_weight']/x['parallel_cells'])
    dr = front+batches*x['complete_physical_update_ns']
    return x['logical_weights_completed']*L['b_R'], dr, batches, beats


def program_sequence_ns(front, pre, steps, erase=0, pages_per_erase=1):
    assert pages_per_erase > 0
    return front+pre+sum(s['count']*(s['drive_program_ns']+s['verify_ns']+s['recover_ns'])
                         for s in steps)+erase/pages_per_erase


def page_service(x, td):
    front, beats = front_ns(x['mapped_page_bits'], td, x['first_data_in_command'])
    # Full program already includes verify: represented once as a complete operation block.
    dr = program_sequence_ns(front, 0, [dict(count=1, drive_program_ns=1000*x['page_program_full_us'],
              verify_ns=0, recover_ns=0)], 1000*x['erase_us'], x['pages_per_erase'])
    return x['logical_page_Byte'], dr, beats


def recompute(e, s):
    v = C['propagation']['profile_values'][s['profile']]
    x = s['inputs']
    if e['id'].endswith('direct'):
        ds = acim_service(R['acim'], v, x['media_read_ns'])[0]
        br, dr, _, _ = direct_service(x, v['digital_tick'])
    else:
        ds = dcim_service(R['dcim'], v, x['media_read_ns'])[0]
        br, dr, _ = page_service(x, v['digital_tick'])
    return metrics(L['n_in']*L['b_S'], br, ds, dr)


def sensitivity_results():
    spec = D['structural_sensitivity']
    x = spec['common_inputs']
    rows, by_id = [], {}
    for s in spec['scenarios']:
        cfg = {**R[s['path']], **s['overrides']}
        if s['path'] == 'acim':
            ds, counts, hold = acim_service(cfg, V, x['acim_read_ns'])
        else:
            ds, counts = dcim_service(cfg, V, x['dcim_read_ns'])
            hold = 0
        br, dr, batches, beats = direct_service(x, V['digital_tick'])
        row = dict(id=s['id'], path=s['path'], label=s['label'], counts=counts,
                   hold_extra_ns=hold, write_batches=batches, data_beats=beats,
                   required_conditions=s['required_conditions'],
                   **metrics(L['B_S_Byte'], br, ds, dr))
        by_id[s['id']] = row
        base = by_id[s['baseline_id']]
        row['rho_ratio_to_path_R0'] = row['rho_Byte_per_s']/base['rho_Byte_per_s']
        row['ridge_ratio_to_path_R0'] = row['ridge']/base['ridge']
        row['tau_ratio_to_path_R0'] = row['tau_Byte_per_s']/base['tau_Byte_per_s']
        rows.append(row)
    timing = []
    for path, base_id in [('acim','A0'), ('dcim','D0')]:
        for key, values in [('adc_batch', spec['small_timing_checks']['adc_ns']),
                            ('digital_tick', spec['small_timing_checks']['digital_tick_ns'])]:
            if path == 'dcim' and key == 'adc_batch':
                continue
            for value in values:
                v = {**V, key:value}
                service = acim_service if path == 'acim' else dcim_service
                ds = service(R[path], v, x[path+'_read_ns'])[0]
                br, dr, _, _ = direct_service(x, v['digital_tick'])
                row = dict(path=path, changed_parameter=key, changed_value_ns=value,
                           **metrics(L['B_S_Byte'], br, ds, dr))
                for metric in ['rho_Byte_per_s','tau_Byte_per_s','ridge']:
                    row[metric+'_relative_change'] = row[metric]/by_id[base_id][metric]-1
                timing.append(row)
    return dict(baseline_version=D['baseline_version'], status=D['status'],
                kind='illustrative_derived_no_medium_binding', structural=rows, small_timing=timing)


def outward(value, lower, digits=2):
    scale = 10**(math.floor(math.log10(value))-digits+1)
    rounded = (math.floor(value/scale+1e-10) if lower else math.ceil(value/scale-1e-10))*scale
    return float(f'{rounded:.10g}')


def interval(values):
    return f'{outward(min(values), True):g}--{outward(max(values), False):g}'


def parameter_table():
    text = [r'% Generated by scripts/check_shared.py --emit.', r'\begingroup\small',
            r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{23mm}>{\raggedright\arraybackslash}p{49mm}>{\raggedright\arraybackslash}p{24mm}>{\raggedright\arraybackslash}p{58mm}@{}}',
            r'\caption{共同外围能力范围。每项按自身粒度使用，完整服务的次数由结构推导。}\label{tab:periphery}\\',
            r'\toprule 模块 & 服务粒度 & 范围/推荐 & 依据与用途\\\midrule\endfirsthead',
            r'\toprule 模块 & 服务粒度 & 范围/推荐 & 依据与用途\\\midrule\endhead']
    for p in P.values():
        refs = ', '.join(r'\sid{'+s+'}' for s in p['sources'])
        text.append(f"{p['label']} ${p['symbol']}$ & {p['granularity']}。 & {p['range'][0]}--{p['range'][1]} ns\\newline 推荐 {p['reference']} ns & {refs}。\\newline {p['use']}。\\\\")
    return '\n'.join(text+[r'\bottomrule\end{longtable}', r'\endgroup',''])


def example_table():
    text = [r'% Generated by scripts/check_shared.py --emit; illustrative, no medium binding.',
            r'\begin{table}[htbp]\centering\small',
            r'\begin{tabular}{@{}llrrrrr@{}}\toprule',
            r'示意 & 情景 & $\Delta_S$ (ns) & $\Delta_R$ (ns) & $\rho$ (GB/s) & $\tau$ (GB/s) & $\RI^*$\\\midrule']
    labels = {'short': '短时隙', 'reference': '参考', 'long': '长时隙'}
    for i, e in enumerate(D['examples'], 1):
        for s in e['scenarios']:
            text.append(f"{i} & {labels[s['profile']]} & {s['delta_S_ns']:g} & {s['delta_R_ns']:g} & {s['rho_Byte_per_s']/1e9:.4g} & {s['tau_Byte_per_s']/1e9:.4g} & {s['ridge']:.4g}\\\\")
        if i == 1:
            text.append(r'\midrule')
    text += [r'\bottomrule\end{tabular}',
             r'\caption{两个算例的成对情景。时间列保留算术结果用于复算，非器件测量精度；GB 为 $10^9$ Byte。}',
             r'\label{tab:examples}\end{table}']
    for i, e in enumerate(D['examples'], 1):
        ss = e['scenarios']
        rr, tt, ri = ([s[key] / (1e9 if key != 'ridge' else 1) for s in ss]
                      for key in ['rho_Byte_per_s', 'tau_Byte_per_s', 'ridge'])
        outer = [min(rr) / max(tt), max(rr) / min(tt)]
        text.append(f"示意 {i} 的展示范围为 $\\rho$={interval(rr)} GB/s、$\\tau$={interval(tt)} GB/s，成对 ridge 为 {interval(ri)}；独立端点外包络为 {interval(outer)}。")
    return '\n'.join(text) + '\n'


def sensitivity_table(result):
    text = [r'% Generated by scripts/check_shared.py --emit.', r'\begin{table}[htbp]\centering\small',
            r'\begin{tabular}{@{}llrrrrr@{}}\toprule',
            r'情景 & 主要变化 & $N_E/N_C/N_{\rm dig}$ & $\Delta_S$ (ns) & $\rho$ (GB/s) & $\RI^*$ & 倍率\\\midrule']
    for s in result['structural']:
        n = s['counts']
        counts = (f"{n['evaluations']}/{n['adc_batches']}/{n['digital_ticks']}" if s['path']=='acim'
                  else f"{n['compute_rounds']}/---/{n['digital_ticks']}")
        text.append(f"{s['id']} & {s['label']} & {counts} & {s['delta_S_ns']:g} & {s['rho_Byte_per_s']/1e9:.4g} & {s['ridge']:.4g} & {s['rho_ratio_to_path_R0']:.3f}\\\\")
    text += [r'\bottomrule\end{tabular}',
             r'\caption{结构敏感性示意。DCIM 第一计数列为计算轮数 $N_D$，无 ADC；倍率为各路径相对 R0 的 $\rho$ 与 ridge 倍率。本表 $B_S=128$ Byte、$B_R=16$ Byte、$\Delta_R=60$ ns、$\tau=0.2667$ GB/s 均不变。}',
             r'\label{tab:sensitivity}\end{table}']
    return '\n'.join(text)+'\n'


def timing_text(result):
    def vals(path, param, metric):
        return [s[metric+'_relative_change']*100 for s in result['small_timing']
                if s['path']==path and s['changed_parameter']==param]
    def span(values):
        return f'{min(values):+.2f}\\% 至 {max(values):+.2f}\\%'
    a = vals('acim','adc_batch','rho_Byte_per_s')
    ad = [span(vals('acim','digital_tick',m)) for m in ['rho_Byte_per_s','tau_Byte_per_s','ridge']]
    dd = [span(vals('dcim','digital_tick',m)) for m in ['rho_Byte_per_s','ridge']]
    return ('% Generated by scripts/check_shared.py --emit.\n'
        '另作单参数小扰动：固定 R0 与合成物理时间，将 $T_A$ 从 20 ns 改为 16/24 ns，'
        f'ACIM 的 $\\rho$ 和 ridge 变化为 {span(a)}，$\\tau$ 不变。'
        '将 $T_D$ 从 5 ns 改为 4/6 ns 并同步重算写控制，'
        f'ACIM 的 $\\rho$、$\\tau$、ridge 分别变化 {ad[0]}、{ad[1]}、{ad[2]}；'
        f'DCIM 的 $\\rho$ 与 ridge 分别变化 {dd[0]}、{dd[1]}，$\\tau$ 变化同 ACIM。\n')


def generated_files():
    result = sensitivity_results()
    return {'tex/generated_parameters.tex':parameter_table(), 'tex/generated_examples.tex':example_table(),
            'tex/generated_sensitivity.tex':sensitivity_table(result),
            'tex/generated_timing_sensitivity.tex':timing_text(result),
            'data/sensitivity_results.json':json.dumps(result, ensure_ascii=False, indent=2)+'\n'}


class SharedChecks(unittest.TestCase):
    def test_units_payload_and_precision(self):
        self.assertEqual(L['B_S_Byte'], L['n_in']*L['b_S'])
        self.assertEqual(L['resident_capacity_Byte'], L['n_in']*L['n_out']*L['b_R'])
        self.assertEqual(L['output_count'], L['n_out'])
        self.assertEqual(L['resident_capacity_Byte']*8, 131072)
        self.assertGreaterEqual(2**R['acim']['partial_sum_code_bits'], 129)
        self.assertLess(128*128*128, 2**(L['output_container_bits']-1))
        self.assertAlmostEqual(seconds(1000,'ns'), seconds(1,'us'))
        self.assertAlmostEqual(seconds(1000,'us'), seconds(1,'ms'))
        self.assertAlmostEqual(1/(100e6), seconds(10,'ns'))
        self.assertAlmostEqual(1e9/(455e6), 2.1978021978)
        self.assertAlmostEqual(metrics(1,1,1,1)['rho_Byte_per_s']/1e9, 1)

    def test_R0_general_templates_match_v01(self):
        self.assertEqual(acim_counts(R['acim']), R['acim']['derived'])
        self.assertEqual(dcim_counts(R['dcim']), R['dcim']['derived'])
        for v in C['propagation']['profile_values'].values():
            for tm in [0, 3, 25, 40]:
                self.assertEqual(acim_service(R['acim'],v,tm)[0],
                    64*(v['input_step']+tm+v['adc_batch']+2*v['digital_tick'])+2*v['digital_tick'])
                self.assertEqual(dcim_service(R['dcim'],v,tm)[0],256*(tm+v['digital_tick'])+2*v['digital_tick'])

    def test_acim_logical_coverage_and_tail_batches(self):
        # Enumerate actual output batches: every required partial sum exactly once.
        for a in [R['acim'], {**R['acim'], **D['structural_sensitivity']['scenarios'][1]['overrides']},
                  {**R['acim'], **D['structural_sensitivity']['scenarios'][2]['overrides']},
                  {**R['acim'], 'rows_per_group':48, 'parallel_weight_planes':3,
                   'evaluation_output_width':35, 'digital_output_lanes':10,
                   'hold_sample_slots':105, 'hold_guarantee_ns':1000, 'hold_capture_ns_per_evaluation':5}]:
            n = acim_counts(a)
            seen = set()
            visits = 0
            for inp in range(n['input_slices']):
                for row in range(n['row_groups']):
                    for weight in range(a['weight_planes']):
                        for start in range(0,L['n_out'],a['evaluation_output_width']):
                            for batch in range(start,min(start+a['evaluation_output_width'],L['n_out']),a['adc_per_weight_plane']):
                                for out in range(batch,min(batch+a['adc_per_weight_plane'],start+a['evaluation_output_width'],L['n_out'])):
                                    visits += 1
                                    seen.add((inp,row,weight,out))
            expected = n['input_slices']*n['row_groups']*a['weight_planes']*L['n_out']
            self.assertEqual(visits,len(seen))
            self.assertEqual(visits,expected)
            self.assertEqual(n['useful_scalar_conversions'],expected)
        # 4 evaluation groups of 35,35,35,23; ADC batches 3+3+3+2 per F.
        self.assertEqual(n['adc_batches'], n['base_combinations']*11)

    def test_dcim_bit_and_spatial_coverage(self):
        for u,w,r,d in [(1,8,32,16),(2,8,32,16),(1,1,32,16),(8,8,128,128),(3,3,48,35)]:
            cfg={**R['dcim'],'input_bits_per_round':u,'weight_bits_per_round':w,'rows_per_group':r,'output_lanes':d}
            n=dcim_counts(cfg)
            # Sum actual products, excluding padding in the last group.
            total=sum(i*j*k*m for i in chunks(8,u) for j in chunks(8,w)
                      for k in chunks(128,r) for m in chunks(128,d))
            self.assertEqual(total, 8*8*128*128)
            self.assertEqual(n['compute_rounds'],len(chunks(8,u))*len(chunks(8,w))*len(chunks(128,r))*len(chunks(128,d)))
        self.assertEqual(dcim_counts({**R['dcim'],'input_bits_per_round':2})['compute_rounds'],128)
        self.assertEqual(dcim_counts({**R['dcim'],'weight_bits_per_round':1})['compute_rounds'],2048)

    def test_holding_and_latching_require_resources(self):
        held={**R['acim'], **D['structural_sensitivity']['scenarios'][2]['overrides']}
        self.assertEqual(acim_counts(held)['max_hold_window_ns'],240)
        for key,value in [('hold_sample_slots',1023),('hold_guarantee_ns',239),('hold_capture_ns_per_evaluation',0)]:
            with self.assertRaises(AssertionError): acim_counts({**held,key:value})
        latch={**R['dcim'],'read_reuse_input_slices':True,'weight_latch_bits':4096,'latch_extra_ns':10}
        self.assertEqual(dcim_counts(latch)['read_rounds'],32)
        self.assertEqual(dcim_counts(latch)['compute_rounds'],256)
        with self.assertRaises(AssertionError): dcim_counts({**latch,'weight_latch_bits':4095})

    def test_complete_updates_and_payload(self):
        x=D['structural_sensitivity']['common_inputs']
        self.assertEqual(direct_service(x,5),(16,60,1,1))
        self.assertEqual(direct_service({**x,'parallel_cells':64},5),(16,110,2,1))
        # Complementary encoding: complete all 16 weights, not twice the logical payload.
        self.assertEqual(direct_service({**x,'cells_per_weight':16,'encoded_load_bits':256},5),(16,115,2,2))
        self.assertEqual(front_ns(2048,5,False),(90,16))
        self.assertEqual(front_ns(2048,5,True),(85,16))
        steps=[dict(count=4,drive_program_ns=20,verify_ns=10,recover_ns=2)]
        self.assertEqual(program_sequence_ns(10,5,steps),143)
        self.assertEqual(program_sequence_ns(10,5,[dict(count=1,drive_program_ns=128,verify_ns=0,recover_ns=0)]),143)
        # Full block service and effective-page amortization give the same tau.
        self.assertAlmostEqual(256*16/(16*(90+10000)+200000),256/(90+10000+200000/16))
        xpage=D['examples'][1]['scenarios'][1]['inputs']
        self.assertEqual(page_service(xpage,5),(256,22590,16))
        self.assertEqual(page_service({**xpage,'logical_page_Byte':128},5),(128,22590,16))
        self.assertEqual(page_service({**xpage,'erase_us':0},5),(256,10090,16))

    def test_granularity_ridge_aggregation(self):
        s=metrics(128,16,3850,60)
        self.assertAlmostEqual(s['ridge'],8*60/3850)
        self.assertAlmostEqual(s['ridge']/(60/3850),8)
        self.assertAlmostEqual(metrics(128,256,3850,22590)['ridge'],.5*22590/3850)
        for e in D['examples']:
            for s in e['scenarios']:
                r,t=s['rho_Byte_per_s'],s['tau_Byte_per_s']
                self.assertAlmostEqual((7*r)/(7*t),s['ridge'])
                self.assertAlmostEqual(1024*s['B_R_Byte']/seconds(1024*s['delta_R_ns'],'ns'),t)
                self.assertLess(s['B_S_Byte']/seconds(2*s['delta_S_ns'],'ns'),r)

    def test_preserved_regression_pairs(self):
        self.assertEqual(len(D['examples']),2)
        for e in D['examples']:
            self.assertFalse(e['bound_to_medium'])
            for s in e['scenarios']:
                for key,value in recompute(e,s).items():
                    self.assertTrue(math.isclose(s[key],value,rel_tol=1e-12),(e['id'],key))
                    self.assertLessEqual(outward(value,True),value+1e-10)
                    self.assertGreaterEqual(outward(value,False)+1e-10,value)
        self.assertEqual([s['delta_S_ns'] for s in D['examples'][0]['scenarios']],[1668,3850,7700])
        self.assertEqual([s['delta_S_ns'] for s in D['examples'][1]['scenarios']],[1284,3850,10260])

    def test_sensitivity_independent_arithmetic(self):
        result=sensitivity_results()
        ss={s['id']:s for s in result['structural']}
        # Independently summed stages; unlike the model, these use the selected scenario's fixed counts.
        expected={'A0':64*30+64*20+128*5+10,
                  'A1':32*30+32*20+128*5+10,
                  'A2':8*30+64*20+128*5+8*5+10,
                  'D0':256*10+256*5+10,'D1':128*10+128*5+10}
        for key,ds in expected.items():
            s=ss[key]
            self.assertEqual(s['delta_S_ns'],ds)
            self.assertEqual(s['tau_ratio_to_path_R0'],1)
            self.assertAlmostEqual(s['rho_ratio_to_path_R0'],3850/ds)
            self.assertAlmostEqual(s['ridge_ratio_to_path_R0'],3850/ds)
        self.assertEqual(ss['A1']['counts']['digital_ticks'],128)
        self.assertEqual(ss['A2']['counts']['useful_scalar_conversions'],8192)
        self.assertEqual(ss['A2']['hold_extra_ns'],40)
        self.assertEqual([s['delta_S_ns'] for s in result['small_timing']],[3594,4106,3720,3980,3592,4108])
        self.assertEqual([s['delta_R_ns'] for s in result['small_timing']],[60,60,58,62,58,62])

    def test_profiles_and_unchanged_periphery(self):
        self.assertEqual(D['baseline_version'],'v0.2')
        self.assertEqual(D['status'],'pending_review')
        self.assertFalse(R['structure_changed_from_v01'])
        self.assertEqual([(p['range'],p['reference']) for p in P.values()],
                         [([2,10],5),([10,50],20),([2,10],5),([4,20],10)])
        for v in C['propagation']['profile_values'].values():
            for key,val in v.items():
                self.assertLessEqual(P[key]['range'][0],val)
                self.assertLessEqual(val,P[key]['range'][1])
        self.assertEqual([acim_service(R['acim'],v,0)[0] for v in C['propagation']['profile_values'].values()],[1028,2250,5140])
        self.assertEqual([dcim_service(R['dcim'],v,0)[0] for v in C['propagation']['profile_values'].values()],[516,1290,2580])

    def test_sources(self):
        manifest={s['source_id']:s for s in json.loads((CORPUS/'source_manifest.json').read_text())['sources']}
        bib=(BASE/'tex/references.bib').read_text()
        evidence=(BASE/'notes/evidence.zh.md').read_text()
        for key,source in D['sources'].items():
            self.assertEqual(source['pdf'],manifest[key]['pdf'])
            self.assertEqual(hashlib.sha256((CORPUS/source['pdf']['path']).read_bytes()).hexdigest(),source['pdf']['sha256'])
            self.assertTrue(('@article{'+key+',' in bib) or ('@inproceedings{'+key+',' in bib))
            self.assertIn(key,evidence)

    def test_generated_data_and_manuscript_contract(self):
        for path,value in generated_files().items():
            self.assertEqual((BASE/path).read_text(),value,path)
        one=(BASE/'tex/01_cmos_periphery.tex').read_text()
        two=(BASE/'tex/02_estimation_method.tex').read_text()
        self.assertEqual((one+two).count(r'\section{'),2)
        for label in ['A. ACIM','B. DCIM','C. 直接更新','D. 分步编程']:
            self.assertIn(label,two)
        for label in ['acount','acim','dcim','direct','program','page']:
            self.assertIn(r'\label{eq:'+label+'}',two)
        for f in ['generated_examples','generated_sensitivity','generated_timing_sensitivity']:
            self.assertIn(r'\input{'+f+'}',two)
        self.assertIn(r'\input{generated_parameters}',one)
        for text in ['1028、2250、5140','516、1290、2580']:
            self.assertIn(text,one)
        for text in ['8192','22590','1024','240','3850']:
            self.assertIn(text,two)
        self.assertIn('v0.2',(BASE/'tex/shared_baseline.tex').read_text())


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit',action='store_true')
    args=parser.parse_args()
    if args.emit:
        for path,value in generated_files().items():
            (BASE/path).write_text(value)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SharedChecks))
    raise SystemExit(0 if result.wasSuccessful() else 1)
