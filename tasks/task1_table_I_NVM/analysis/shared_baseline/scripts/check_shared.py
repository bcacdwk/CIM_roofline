#!/usr/bin/env python3
"""Recompute service templates, the R0 reference and bounded sensitivity (stdlib only).

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


def resolve_service_parameters(parameter_values, service_bindings, overrides=None):
    """Resolve one parameter value into every declared service consumer.

    Bindings are {service: {local_slot: parameter_name}}; there are no expressions,
    cached derived times or implicit mode changes. A distinct operation may bind a
    different parameter, with its physical qualification documented by the caller.
    """
    overrides = {} if overrides is None else overrides
    assert set(overrides) <= set(parameter_values), 'unknown parameter override'
    values = {**parameter_values, **overrides}
    assert service_bindings and all(service_bindings.values()), 'empty service bindings'
    used = {name for binding in service_bindings.values() for name in binding.values()}
    assert used <= set(values), 'unknown bound parameter'
    assert set(overrides) <= used, 'overridden parameter has no service consumer'
    assert all(isinstance(values[name], (int, float)) and math.isfinite(values[name])
               and values[name] >= 0 for name in used), 'invalid service parameter'
    return {service: {slot: values[name] for slot, name in binding.items()}
            for service, binding in service_bindings.items()}


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


def logical_configuration(K, N, b_S=1, b_R=1):
    """One logical W[N,K]; binary physical encoding and replicas remain separate."""
    assert isinstance(K,int) and isinstance(N,int) and min(K,N)>0
    assert min(b_S,b_R)>0 and float(8*b_S).is_integer() and float(8*b_R).is_integer()
    bits = int(8*b_S+8*b_R)+math.ceil(math.log2(K))
    return dict(n_in=K,n_out=N,K=K,N=N,b_S=b_S,b_R=b_R,
                B_S_Byte=K*b_S,resident_capacity_Byte=K*N*b_R,
                output_count=N,output_container_bits=bits,
                input_register_bits=int(K*b_S*8),output_register_bits=N*bits)


def mapping_metrics(logical, delta_S_ns, T_R_ns):
    """Complete-vector interval and complete resident load of the same matrix."""
    r = metrics(logical['B_S_Byte'],logical['resident_capacity_Byte'],delta_S_ns,T_R_ns)
    r.update(K=logical['n_in'],N=logical['n_out'],b_S=logical['b_S'],b_R=logical['b_R'],
             full_resident_payload_Byte=logical['resident_capacity_Byte'],RI_star=r['ridge'],T_R_ns=T_R_ns,
             U_star=T_R_ns/delta_S_ns,
             average_update_ns_per_16KiB=T_R_ns*16384/logical['resident_capacity_Byte'])
    return r


def full_load_service(logical, transactions):
    """Enumerated completed payloads, including tails; zero-payload setup allowed."""
    assert transactions
    total = sum(x.get('count',1)*x['payload_Byte'] for x in transactions)
    assert math.isclose(total,logical['resident_capacity_Byte']), 'load does not cover logical matrix once'
    assert all(x.get('count',1)>0 and x['payload_Byte']>=0 and x['service_ns']>=0 for x in transactions)
    return dict(logical_payload_Byte=total,
                T_R_ns=sum(x.get('count',1)*x['service_ns'] for x in transactions),
                transactions=sum(x.get('count',1) for x in transactions))


def native_block_service(pages, erase_ns, td, resident=None):
    """One complete sustained block cycle. Reference/replica pages carry no useful bytes."""
    assert pages and erase_ns>=0
    payload=0; total=erase_ns; count=0
    for p in pages:
        assert p['logical_payload_Byte']>=0 and p['program_full_ns']>0
        n=p.get('count',1); assert isinstance(n,int) and n>0
        front=front_ns(p['encoded_load_bits'],td,p.get('first_data_in_command',False),resident)[0]
        payload+=n*p['logical_payload_Byte']; count+=n
        total+=n*(front+p['program_full_ns'])
    assert payload>0
    return dict(logical_payload_Byte=payload,physical_pages=count,erase_ns=erase_ns,
                T_R_ns=total,tau_Byte_per_s=payload/seconds(total,'ns'),
                average_update_ns_per_16KiB=total*16384/payload)


def apply_maintenance(raw, period_ns, busy_ns, guard_ns=0):
    """One explicitly shared serial reservation; no implicit overlap or write credit."""
    assert period_ns>0 and busy_ns>=0 and guard_ns>=0
    alpha=1-(busy_ns+guard_ns)/period_ns
    effective=dict(raw)
    for k in ['delta_S_ns','delta_R_ns','T_R_ns','average_update_ns_per_16KiB']:
        if k in effective: effective[k]=raw[k]/alpha if alpha>0 else None
    for k in ['rho_Byte_per_s','tau_Byte_per_s']:
        effective[k]=raw[k]*alpha if alpha>0 else None
    for k in ['ridge','RI_star','U_star']:
        if k in effective: effective[k]=raw[k] if alpha>0 else None
    return dict(raw=raw,effective=effective,availability=alpha,feasible=alpha>0,
                period_ns=period_ns,busy_ns=busy_ns,guard_ns=guard_ns,
                maintenance_payload_Byte=0)


def acim_counts(a, v=V, logical=None):
    assert logical is not None, "pass the case logical configuration"
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


def acim_service(a, v, read_ns, logical):
    n = acim_counts(a, v, logical)
    hold = n['evaluations']*a['hold_capture_ns_per_evaluation']
    ds = (n['evaluations']*(v['input_step']+read_ns) + n['adc_batches']*v['adc_batch']
          + n['digital_ticks']*v['digital_tick'] + hold + a['boundary_ticks']*v['digital_tick'])
    return ds, n, hold


def dcim_counts(d, logical):
    ni = len(chunks(int(logical['b_S']*8), d['input_bits_per_round']))
    weights = chunks(int(logical['b_R']*8), d['weight_bits_per_round'])
    rows = chunks(logical['n_in'], d['rows_per_group'])
    outputs = chunks(logical['n_out'], d['output_lanes'])
    tile_bits = [w*r*o for w in weights for r in rows for o in outputs]
    reuse = d.get('read_reuse_input_slices', True)
    source = d.get('hold_source', 'added_latch' if reuse else 'none')
    assert source in {'none','added_latch','existing_capture','static_connection'}
    assert reuse == (source != 'none'), 'hold source and reuse disagree'
    if reuse and source != 'static_connection':
        assert d['weight_latch_bits'] >= max(tile_bits), 'insufficient digital tile storage'
    width = d['read_bits_per_batch']
    assert width > 0
    repeats = 1 if reuse else ni
    batches = repeats*sum(math.ceil(bits/width) for bits in tile_bits)
    capture_ticks = batches*d.get('capture_ticks_per_read_batch', 1) if source == 'added_latch' else 0
    return dict(input_slices=ni, weight_groups=len(weights), row_groups=len(rows),
                output_groups=len(outputs), compute_rounds=ni*len(tile_bits),
                tile_reads=repeats*len(tile_bits), read_rounds=batches,
                max_tile_bits=max(tile_bits), capture_ticks=capture_ticks,
                digital_ticks=ni*len(tile_bits)*d['digital_ticks_per_round'])


def dcim_service(d, v, read_ns, logical):
    n = dcim_counts(d, logical)
    ds = (n['read_rounds']*read_ns+(n['digital_ticks']+n['capture_ticks'])*v['digital_tick']
          +d.get('latch_extra_ns',0)+d['boundary_ticks']*v['digital_tick'])
    return ds, n


def front_ns(encoded_bits, td, first_data_in_command, resident=None):
    r = R['resident'] if resident is None else resident
    assert encoded_bits > 0 and td > 0
    beats = math.ceil(encoded_bits/r['physical_write_data_lanes'])
    return (r['control_ticks']+beats-int(first_data_in_command))*td, beats


def direct_service(x, td, logical, resident=None):
    # Only independently selectable, aligned cells may use this batch template.
    front, beats = front_ns(x['encoded_load_bits'], td, x['first_data_in_command'], resident)
    batches = math.ceil(x['logical_weights_completed']*x['cells_per_weight']/x['parallel_cells'])
    dr = front+batches*x['complete_physical_update_ns']
    return x['logical_weights_completed']*logical['b_R'], dr, batches, beats


def program_sequence_ns(front, pre, steps, erase=0, pages_per_erase=1):
    assert pages_per_erase > 0
    return front+pre+sum(s['count']*(s['drive_program_ns']+s['verify_ns']+s['recover_ns'])
                         for s in steps)+erase/pages_per_erase


def page_service(x, td, resident=None):
    front, beats = front_ns(x['mapped_page_bits'], td, x['first_data_in_command'], resident)
    # Full program already includes verify: represented once as a complete operation block.
    dr = program_sequence_ns(front, 0, [dict(count=1, drive_program_ns=1000*x['page_program_full_us'],
              verify_ns=0, recover_ns=0)], 1000*x['erase_us'], x['pages_per_erase'])
    return x['logical_page_Byte'], dr, beats


def recompute(e, s):
    v = C['propagation']['profile_values'][s['profile']]
    x = s['inputs']
    if e['id'].endswith('direct'):
        ds = acim_service(R['acim'], v, x['media_read_ns'], L)[0]
        br, dr, _, _ = direct_service(x, v['digital_tick'], L)
    else:
        ds = dcim_service(R['dcim'], v, x['media_read_ns'], L)[0]
        br, dr, _ = page_service(x, v['digital_tick'])
    return metrics(L['n_in']*L['b_S'], br, ds, dr)


def sensitivity_results():
    spec = D['structural_sensitivity']
    x = spec['common_inputs']
    rows, by_id = [], {}
    for s in spec['scenarios']:
        cfg = {**R[s['path']], **s['overrides']}
        if s['path'] == 'acim':
            ds, counts, hold = acim_service(cfg, V, x['acim_read_ns'], L)
        else:
            ds, counts = dcim_service(cfg, V, x['dcim_read_ns'], L)
            hold = 0
        br, dr, batches, beats = direct_service(x, V['digital_tick'], L)
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
                ds = service(R[path], v, x[path+'_read_ns'], L)[0]
                br, dr, _, _ = direct_service(x, v['digital_tick'], L)
                row = dict(path=path, changed_parameter=key, changed_value_ns=value,
                           **metrics(L['B_S_Byte'], br, ds, dr))
                for metric in ['rho_Byte_per_s','tau_Byte_per_s','ridge']:
                    row[metric+'_relative_change'] = row[metric]/by_id[base_id][metric]-1
                timing.append(row)
    return dict(baseline_id=D['baseline_id'],
                kind='illustrative_derived_no_medium_binding', structural=rows, small_timing=timing,
                mapping_examples=[dict(id='native',**mapping_metrics(logical_configuration(64,32),100,3200)),
                    dict(id='N_double_input_shared_writer_serial',**mapping_metrics(logical_configuration(64,64),100,6400)),
                    dict(id='both_services_double',**mapping_metrics(logical_configuration(64,64),200,6400))])


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
    def test_mode_parameter_and_profile_propagation(self):
        values={**V,'shared_front':20,'long_observation':768}
        binding={'evaluation':{'front':'shared_front','ti':'input_step','ta':'adc_batch','td':'digital_tick'},
                 'verify':{'front':'shared_front','ti':'input_step','ta':'adc_batch','td':'digital_tick'},
                 'write_control':{'td':'digital_tick'}}
        def schedule(override=None, modes=binding):
            p=resolve_service_parameters(values,modes,override)
            a,b,c=p['evaluation'],p['verify'],p['write_control']
            # Full frontend already includes TI; changing TI partitions this fixed total.
            ds=8*(a['ti']+(a['front']-a['ti'])+a['ta']+2*a['td'])+2*a['td']
            local=3*c['td']+2*(100+b['front']+b['ta']+b['td'])
            load=full_load_service(logical_configuration(8,4),[dict(payload_Byte=8,service_ns=local,count=4)])
            return p,ds,load['T_R_ns']
        base= schedule()
        self.assertEqual(base[1:],(410,1220))
        for name,delta,ds_change,tr_change in [('shared_front',7,56,56),
                ('adc_batch',3,24,24),('digital_tick',2,36,40),('input_step',1,0,0)]:
            changed=schedule({name:values[name]+delta})
            self.assertEqual(changed[1]-base[1],ds_change)
            self.assertEqual(changed[2]-base[2],tr_change)
            if name=='input_step':
                self.assertEqual(changed[0]['evaluation']['ti'],6)
                self.assertEqual(changed[0]['verify']['ti'],6)
        with self.assertRaises(AssertionError): schedule({'typo':1})
        with self.assertRaises(AssertionError): schedule({'long_observation':1})
        with self.assertRaises(AssertionError): resolve_service_parameters(values,{'x':{'a':'missing'}})

    def test_distinct_mode_and_maintenance_propagation(self):
        # Synthetic independently qualified physical verify path, not an observation-only override.
        values={**V,'front':20,'separate_verify_front':768,'residual':86,'mac_pulse':1,'refresh_pulse':64}
        modes={'evaluation':{'front':'front','ta':'adc_batch','td':'digital_tick'},
               'verify':{'front':'separate_verify_front','ta':'adc_batch','td':'digital_tick'},
               'mac':{'residual':'residual','pulse':'mac_pulse','ta':'adc_batch','td':'digital_tick'},
               'refresh':{'residual':'residual','pulse':'refresh_pulse','ta':'adc_batch','td':'digital_tick'}}
        base=resolve_service_parameters(values,modes)
        altered=resolve_service_parameters(values,modes,{'separate_verify_front':900})
        self.assertEqual(altered['evaluation'],base['evaluation'])
        self.assertEqual(altered['verify']['front']-base['verify']['front'],132)
        # Same-path observation-only mode must preserve the common settling lower bound.
        same_path={'evaluation':{'front':'front'},
                   'verify':{'front':'front','minimum_observation':'observation_floor'}}
        for front,expected in [(20,768),(768,768),(900,900)]:
            p=resolve_service_parameters({'front':20,'observation_floor':768},same_path,{'front':front})
            self.assertEqual(p['evaluation']['front'],front)
            self.assertEqual(max(p['verify'].values()),expected)
        # Independent synthetic maintenance schedule: shared residual propagates to both modes.
        def maintained(override=None):
            p=resolve_service_parameters(values,modes,override)
            m,f=p['mac'],p['refresh']
            read=m['residual']+m['pulse']+m['ta']+m['td']
            h=4*(f['residual']+f['pulse']+f['ta']+f['td']+75)
            guard=max(read,75)
            return apply_maintenance(mapping_metrics(logical_configuration(8,4),8*read,2400),10000,h,guard)
        b=maintained(); c=maintained({'residual':96})
        self.assertEqual(b['busy_ns'],1000)
        self.assertEqual(c['busy_ns'],1040)
        self.assertEqual((b['guard_ns'],c['guard_ns']),(112,122))
        self.assertAlmostEqual(c['availability'],1-(1040+122)/10000)
        self.assertEqual(c['raw']['delta_S_ns']-b['raw']['delta_S_ns'],80)
        self.assertLess(c['effective']['rho_Byte_per_s'],b['effective']['rho_Byte_per_s'])
        self.assertLess(c['effective']['tau_Byte_per_s'],b['effective']['tau_Byte_per_s'])
        self.assertAlmostEqual(c['effective']['U_star'],4*c['effective']['ridge'])

    def test_quantized_reconstruction_is_not_ideal_identity(self):
        a=R['acim']; l=logical_configuration(128,128)
        self.assertEqual((a['adc_nominal_bits'],a['adc_effective_bits_target'],l['output_container_bits']),(10,8,23))
        # Synthetic normalized signals, not PCM/NAND device distributions.
        # 0.4 - 0.2 - 0.2 vanishes algebraically; rounding each sample first need not.
        def quantized(value,bits):
            clipped=min(1,max(0,value)); levels=2**bits-1
            return math.floor(clipped*levels+.5)/levels,clipped!=value
        ideal=.4-.2-.2
        reconstructed=quantized(.4,2)[0]-2*quantized(.2,2)[0]
        self.assertEqual(ideal,0)
        self.assertAlmostEqual(reconstructed,-1/3)
        self.assertEqual(quantized(1.2,10),(1,True))
        self.assertEqual(quantized(-.1,10),(0,True))
        self.assertNotEqual(1/(2**a['adc_nominal_bits']-1),1/2**a['adc_effective_bits_target'])
        self.assertIn('ENOB',D['numerical_service_policy']['enob_rule'])

    def test_units_and_logical_shapes(self):
        for k,n,bs,br in [(128,128,1,1),(64,64,1,1),(70,35,1,1),(17,9,2,1)]:
            l=logical_configuration(k,n,bs,br)
            self.assertEqual(l['B_S_Byte'],k*bs)
            self.assertEqual(l['resident_capacity_Byte'],k*n*br)
            self.assertEqual(l['input_register_bits'],8*k*bs)
            self.assertEqual(l['output_register_bits'],n*(int(8*bs+8*br)+math.ceil(math.log2(k))))
        self.assertAlmostEqual(seconds(1000,'ns'),seconds(1,'us'))
        self.assertTrue(math.isclose(metrics(1,1,1,1)['rho_Byte_per_s'],1e9,rel_tol=1e-12))
        with self.assertRaises(AssertionError): logical_configuration(0,16)

    def test_explicit_logical_and_resource_inputs(self):
        with self.assertRaises(TypeError): acim_service(R['acim'],V,1)
        with self.assertRaises(TypeError): dcim_service(R['dcim'],V,1)
        with self.assertRaises(TypeError): direct_service(D['structural_sensitivity']['common_inputs'],5)
        with self.assertRaises(AssertionError): acim_counts(R['acim'])
        self.assertEqual(acim_counts(R['acim'],V,L),R['acim']['derived'])
        self.assertEqual(dcim_counts(R['dcim'],L),R['dcim']['derived'])

    def test_acim_non_square_tail_coverage(self):
        l=logical_configuration(70,35)
        a={**R['acim'],'input_bits_per_slice':3,'rows_per_group':32,
           'parallel_weight_planes':3,'evaluation_output_width':17,
           'adc_per_weight_plane':8,'digital_output_lanes':5,
           'hold_sample_slots':51,'hold_guarantee_ns':200,'hold_capture_ns_per_evaluation':5}
        ds,n,h=acim_service(a,V,7,l)
        self.assertEqual((n['input_slices'],n['row_groups'],n['weight_groups']),(3,3,3))
        self.assertEqual((n['evaluations'],n['adc_batches'],n['reconstruction_rounds']),(81,189,297))
        self.assertEqual(n['useful_scalar_conversions'],3*3*8*35)
        self.assertEqual(ds,81*(5+7)+189*20+594*5+81*5+10)
        # Independent weighted enumeration excludes input, row and plane padding.
        products=sum(i*r*w*o for i in [3,3,2] for r in [32,32,6]
                     for w in [3,3,2] for o in [17,17,1])
        self.assertEqual(products,8*70*8*35)
        with self.assertRaises(AssertionError): acim_counts({**a,'hold_sample_slots':50},V,l)
        with self.assertRaises(AssertionError): acim_counts({**a,'hold_guarantee_ns':1},V,l)

    def test_dcim_hold_sa_batches_and_static_connection(self):
        l=logical_configuration(70,35)
        d={**R['dcim'],'input_bits_per_round':3,'weight_bits_per_round':3,
           'read_bits_per_batch':1536,'weight_latch_bits':1536}
        ds,n=dcim_service(d,V,11,l)
        self.assertEqual((n['compute_rounds'],n['tile_reads'],n['read_rounds']),(81,27,27))
        self.assertEqual(n['max_tile_bits'],1536)
        self.assertEqual(ds,27*11+(81+27+2)*5)
        # At 128-bit sensing, actual per-tile width (including tails) controls reads.
        d['read_bits_per_batch']=128
        nd=dcim_counts(d,l)
        hand=sum(math.ceil(w*r*o/128) for w in [3,3,2] for r in [32,32,6] for o in [16,16,3])
        self.assertEqual(nd['read_rounds'],hand)
        self.assertEqual(nd['capture_ticks'],hand)
        static={**d,'hold_source':'static_connection','weight_latch_bits':0}
        self.assertEqual(dcim_counts(static,l)['capture_ticks'],0)
        with self.assertRaises(AssertionError): dcim_counts({**d,'weight_latch_bits':1535},l)
        nohold={**d,'read_reuse_input_slices':False,'hold_source':'none'}
        self.assertEqual(dcim_counts(nohold,l)['read_rounds'],3*hand)

    def test_direct_payload_encoding_and_interface(self):
        x=D['structural_sensitivity']['common_inputs']
        self.assertEqual(direct_service(x,5,L),(16,60,1,1))
        self.assertEqual(direct_service({**x,'parallel_cells':64},5,L),(16,110,2,1))
        self.assertEqual(direct_service({**x,'cells_per_weight':16,'encoded_load_bits':256},5,L),(16,115,2,2))
        self.assertEqual(direct_service(x,5,logical_configuration(7,9,1,2))[0],32)
        self.assertEqual(front_ns(129,5,False,dict(physical_write_data_lanes=64,control_ticks=2)),(25,3))
        self.assertEqual(program_sequence_ns(10,5,[dict(count=4,drive_program_ns=20,verify_ns=10,recover_ns=2)]),143)

    def test_full_load_tail_and_native_block(self):
        l=logical_configuration(7,5)
        q=full_load_service(l,[dict(payload_Byte=16,service_ns=60,count=2),dict(payload_Byte=3,service_ns=60)])
        self.assertEqual(q['T_R_ns'],180)
        with self.assertRaises(AssertionError): full_load_service(l,[dict(payload_Byte=32,service_ns=120)])
        pages=[dict(logical_payload_Byte=24,encoded_load_bits=384,program_full_ns=100,count=3),
               dict(logical_payload_Byte=0,encoded_load_bits=384,program_full_ns=100)]
        z=native_block_service(pages,1000,5)
        self.assertEqual(z['physical_pages'],4)
        self.assertEqual(z['logical_payload_Byte'],72)
        self.assertEqual(z['T_R_ns'],1000+4*(25+100))
        self.assertAlmostEqual(z['tau_Byte_per_s'],72/1500*1e9)
        page=page_service(dict(mapped_page_bits=2048,first_data_in_command=False,
            page_program_full_us=10,erase_us=200,pages_per_erase=16,logical_page_Byte=256),5)
        self.assertEqual(page,(256,22590,16))

    def test_mapping_interface_and_non_symmetric_expansion(self):
        l=logical_configuration(64,32)
        r=mapping_metrics(l,100,3200)
        self.assertEqual(r['U_star'],32)
        self.assertAlmostEqual(r['ridge'],1)
        self.assertAlmostEqual(r['U_star'],l['n_out']*l['b_R']/l['b_S']*r['ridge'])
        wide=mapping_metrics(logical_configuration(64,64),100,6400)
        self.assertEqual(wide['U_star'],64) # input-shared compute, shared serial writer
        serial=mapping_metrics(logical_configuration(64,64),200,6400)
        self.assertEqual(serial['U_star'],32) # both services scale identically
        other=mapping_metrics(logical_configuration(13,9,2,1),80,720)
        self.assertAlmostEqual(other['U_star'],9/2*other['ridge'])
        self.assertEqual(r['average_update_ns_per_16KiB'],25600)

    def test_maintenance_raw_effective_and_infeasible(self):
        raw=mapping_metrics(logical_configuration(64,32),100,3200)
        r=apply_maintenance(raw,1000,200,50)
        self.assertEqual(r['availability'],.75)
        self.assertEqual(r['effective']['rho_Byte_per_s'],raw['rho_Byte_per_s']*.75)
        self.assertEqual(r['effective']['U_star'],raw['U_star'])
        self.assertEqual(r['maintenance_payload_Byte'],0)
        for busy in [1000,1100]:
            z=apply_maintenance(raw,1000,busy)
            self.assertFalse(z['feasible'])
            for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge','U_star','delta_S_ns','T_R_ns']:
                self.assertIsNone(z['effective'][k])
            self.assertEqual(z['raw'],raw)

    def test_illustrative_scenarios_independent_arithmetic(self):
        for e in D['examples']:
            for z in e['scenarios']:
                for k,v in recompute(e,z).items(): self.assertAlmostEqual(z[k],v)
        self.assertEqual([z['delta_S_ns'] for z in D['examples'][0]['scenarios']],[1668,3850,7700])
        self.assertEqual([z['delta_S_ns'] for z in D['examples'][1]['scenarios']],[676,1770,3860])
        result=sensitivity_results(); rows={x['id']:x for x in result['structural']}
        expected={'A0':64*30+64*20+128*5+10,'A1':32*30+32*20+128*5+10,
                  'A2':8*30+64*20+128*5+8*5+10,'D0':32*10+(256+32+2)*5,
                  'D1':16*10+(128+16+2)*5}
        for key,ds in expected.items():
            self.assertEqual(rows[key]['delta_S_ns'],ds)
            self.assertEqual(rows[key]['tau_ratio_to_path_R0'],1)
        self.assertEqual(rows['A2']['hold_extra_ns'],40)

    def test_sources_and_policy(self):
        manifest={s['source_id']:s for s in json.loads((CORPUS/'source_manifest.json').read_text())['sources']}
        bib=(BASE/'tex/references.bib').read_text(); evidence=(BASE/'notes/evidence.zh.md').read_text()
        for key,source in D['sources'].items():
            self.assertEqual(source['pdf'],manifest[key]['pdf'])
            self.assertEqual(hashlib.sha256((CORPUS/source['pdf']['path']).read_bytes()).hexdigest(),source['pdf']['sha256'])
            self.assertIn('{'+key+',',bib);self.assertIn(key,evidence)
        self.assertEqual([x['id'] for x in D['selection_rules']],['R'+str(i) for i in range(1,9)])
        self.assertEqual(D['resource_policy']['digital_tile_storage_bits'],4096)

    def test_generated_data_and_manuscript_contract(self):
        for path,value in generated_files().items(): self.assertEqual((BASE/path).read_text(),value,path)
        one=(BASE/'tex/01_cmos_periphery.tex').read_text();two=(BASE/'tex/02_estimation_method.tex').read_text()
        self.assertEqual((one+two).count(r'\section{'),2)
        for label in ['acount','acim','dcim','direct','program','page','mapping']:
            self.assertIn(r'\label{eq:'+label+'}',two)
        for f in ['generated_examples','generated_sensitivity','generated_timing_sensitivity']:
            self.assertIn(r'\input{'+f+'}',two)
        self.assertIn(r'\input{generated_parameters}',one)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit',action='store_true')
    args=parser.parse_args()
    if args.emit:
        for path,value in generated_files().items():
            (BASE/path).write_text(value)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(SharedChecks))
    raise SystemExit(0 if result.wasSuccessful() else 1)
