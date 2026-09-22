#!/usr/bin/env python3
"""Read-only verification by default; --emit regenerates this case's tables/results.
All service, operation-count and metric formulas are imported from shared_baseline.
Complete-cycle replacement composes shared operation blocks; no shared files are edited.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE.parents[1]
SHARED = BASE.parent / 'shared_baseline'
D = json.loads((BASE/'data/inputs.json').read_text())
spec = importlib.util.spec_from_file_location('shared_dcim_reference', SHARED/'scripts/check_shared.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def block(front, duration, count=1):
    """Use the shared full-operation composition, not a new timing equation."""
    return S.program_sequence_ns(front, 0, [dict(count=count, drive_program_ns=duration,
                                                 verify_ns=0, recover_ns=0)])


def compute():
    rows, comparisons = [], []
    cfg = {**S.R['dcim'], **D['dcim_overrides']}
    for x in D['scenarios']:
        v = S.C['propagation']['profile_values'][x['common_profile']]
        td, tc, tm = v['digital_tick'], x['complete_compute_round_ns'], x['complete_memory_cycle_ns']
        # Complete local MAC slot replaces both media-read and digital stages.
        # Common boundary ticks are composed separately at their unchanged T_D.
        ds_core, counts = S.dcim_service(cfg, {**v, 'digital_tick':tc}, 0)
        ds = block(S.R['dcim']['boundary_ticks']*td, ds_core)
        update = {**D['update_geometry'], 'complete_physical_update_ns':tm}
        br, uncollapsed_dr, batches, beats = S.direct_service(update, td)
        legacy_front, _ = S.front_ns(update['encoded_load_bits'], td, update['first_data_in_command'])
        # Full synchronous one-beat memory cycle already covers command/data capture
        # and compute-ready endpoint. No further task-level handshake is assumed.
        dr = block(0, tm, batches)
        row = dict(id=x['id'], label=x['label'], common_profile=x['common_profile'],
                   inputs=dict(common_T_D_ns=td, complete_compute_round_ns=tc,
                               complete_memory_cycle_ns=tm, extra_physical_read_ns=0),
                   counts=counts, physical_static_row_group_activations=counts['row_groups']*counts['output_groups'],
                   write_batches=batches, write_data_beats=beats,
                   stage_coverage=dict(streaming=[
                       dict(stage='whole_vector_capture',count=1,duration_each_ns=td,coverage='1024-bit local input latch and schedule admission'),
                       dict(stage='complete_MAC_round',count=counts['compute_rounds'],duration_each_ns=tc,coverage='static SRAM read/hold, NOR multiplication, HCA reduction, BFA sign/shift/accumulation'),
                       dict(stage='whole_vector_commit',count=1,duration_each_ns=td,coverage='all128 results ready in24-bit registers; sign extension wiring'),
                       dict(stage='extra_read_or_ADC',count=0,duration_each_ns=0,coverage='read already included; no ADC/DAC')],
                       resident=[dict(stage='complete_synchronous_memory_cycle',count=batches,duration_each_ns=tm,
                                      coverage='command/address/all128 data captured; decode, BL/WL write, flip, recovery; compute-ready at next edge'),
                                 dict(stage='additional_task_handshake',count=0,duration_each_ns=0,coverage='none assumed; shared front replaced by covered macro cycle')],
                       replaced_shared_front_ns=legacy_front, direct_template_without_replacement_ns=uncollapsed_dr),
                   **S.metrics(S.L['B_S_Byte'],br,ds,dr))
        rows.append(row)
        # Resource sensitivity: hypothetical R0 32-term datapath retaining the same clock.
        r0cfg = {**S.R['dcim'], 'boundary_ticks':0}
        r0core, r0counts = S.dcim_service(r0cfg,{**v,'digital_tick':tc},0)
        r0ds = block(S.R['dcim']['boundary_ticks']*td,r0core)
        comparisons.append(dict(id='R0_same_clock_'+x['id'], kind='conditional_resource_comparison',
                                premise='32-term/16-output round reaches same full clock; not measured D6 timing',
                                counts=r0counts, **S.metrics(S.L['B_S_Byte'],br,r0ds,dr)))
        comparisons.append(dict(id='extra_handshake_'+x['id'],kind='boundary_sensitivity',
                                premise='additional external preparation/completion not covered by primitive; one common tick each',
                                added_handshake_ns=legacy_front,
                                **S.metrics(S.L['B_S_Byte'],br,ds,uncollapsed_dr)))
    def span(key): return [min(r[key] for r in rows), max(r[key] for r in rows)]
    ranges={key:span(key) for key in ['delta_S_ns','delta_R_ns','rho_Byte_per_s','tau_Byte_per_s','ridge']}
    ranges['independent_endpoint_ridge_envelope']=[ranges['rho_Byte_per_s'][0]/ranges['tau_Byte_per_s'][1],
                                                 ranges['rho_Byte_per_s'][1]/ranges['tau_Byte_per_s'][0]]
    return dict(analysis_id=D['analysis_id'],baseline_id=S.D['baseline_id'],
                baseline_files_actual={f:sha(SHARED/f) for f in D['baseline_files']},
                status='conditional_reference_estimate_not_measured_paired_chip',scenarios=rows,
                sensitivities=comparisons,ranges=ranges,
                whole_matrix_updates=dict(logical_payload_Byte=S.L['resident_capacity_Byte'],
                                           aligned_transactions=S.L['resident_capacity_Byte']//rows[0]['B_R_Byte']))


def esc(s):
    for a,b in [('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]: s=s.replace(a,b)
    for a,b in [('≈', r'$\approx$'), ('≠', r'$\ne$'), ('χ', r'$\chi$'), ('−', '-'), ('Σ', r'$\Sigma$')]: s=s.replace(a,b)
    return s


def table_results(result):
    lines=[r'% Generated by scripts/check_sram_dcim.py --emit from data/inputs.json.',
           r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrrrr@{}}\toprule',
           r'情景 & $T_D$ & $T_C$ & $\Delta_S$ & $\Delta_R$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$\\\midrule']
    for r in result['scenarios']:
        x=r['inputs']
        lines.append(f"{r['label']} & {x['common_T_D_ns']:g} & {x['complete_compute_round_ns']:g} & {r['delta_S_ns']:g} & {r['delta_R_ns']:g} & {r['rho_Byte_per_s']/1e9:.4g} & {r['tau_Byte_per_s']/1e9:.4g} & {r['ridge']:.4g}"+r'\\')
    lines += [r'\bottomrule\end{tabular}',r'\caption{D6CIM型16项结构的成对情景。所有时间单位为ns，吞吐为十进制GB/s；$\Delta_R=T_M$。时间列保留复算值，非实测有效位数。}\label{tab:dcim-results}\end{table}']
    return '\n'.join(lines)+'\n'


def table_sensitivity(result):
    rows=[r'% Generated by scripts/check_sram_dcim.py --emit.',r'\begin{table}[htbp]\centering\small',
          r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
          r'参考时隙条件 & $\Delta_S$ (ns) & $\Delta_R$ (ns) & $\rho$ (GB/s) & $\tau$ (GB/s) & $\mathrm{RI}^{*}$\\\midrule']
    items=[('主情景：16项，完整写周期', result['scenarios'][1]),
           ('条件对照：32项，同MAC时钟',next(x for x in result['sensitivities'] if x['id']=='R0_same_clock_reference')),
           ('另有两拍外部写握手',next(x for x in result['sensitivities'] if x['id']=='extra_handshake_reference'))]
    for label,r in items:
        rows.append(f"{label} & {r['delta_S_ns']:g} & {r['delta_R_ns']:g} & {r['rho_Byte_per_s']/1e9:.4g} & {r['tau_Byte_per_s']/1e9:.4g} & {r['ridge']:.4g}"+r'\\')
    rows += [r'\bottomrule\end{tabular}',r'\caption{结构及边界条件的独立影响。32项同钟需要相应归约和读带宽；最后一行只适用于确有额外握手的实现。}\label{tab:dcim-sensitivity}\end{table}']
    return '\n'.join(rows)+'\n'


def evidence_tex():
    lines=[r'% Generated from data/inputs.json raw_evidence; original and adopted values separated.',
           r'\begingroup\footnotesize\setlength{\tabcolsep}{3pt}\renewcommand{\arraystretch}{1.08}',
           r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{27mm}>{\raggedright\arraybackslash}p{62mm}>{\raggedright\arraybackslash}p{65mm}@{}}',
           r'\caption{参数证据与采用方法。页码均为本地PDF页序；原始值与本文预算分列。}\label{tab:dcim-evidence}\\',
           r'\toprule 证据与定位 & 原值、单位和条件 & 采用值与换算理由\\\midrule\endfirsthead',
           r'\toprule 证据与定位 & 原值、单位和条件 & 采用值与换算理由\\\midrule\endhead']
    locs={'E01':'p.1 Fig.1；p.2首段','E02':'p.2 II-D；p.3 Fig.5','E03':'p.4 Fig.10(a)；p.3 III','E04':'p.1 Fig.1','E05':'p.2 Fig.2；p.9 Tables II/III','E06':'p.9 Table II','E07':'p.1 II；p.3 IV-C','E08':'p.1；p.2 Figs.11.7.2-5','E09':'JSON共同条件/R0','E10':'通用方法C及R4'}
    for e in D['raw_evidence']:
        sid='共享基线' if e['source_id']=='shared_baseline' else r'\texttt{'+e['source_id']+'}'
        left=f"{e['id']} {sid}\\newline {locs[e['id']]}"
        middle=esc(e['parameter']+'：'+e['original_value']+'。'+e['conditions'])
        right=esc(e['adopted']+'。'+e['conversion_reason'])
        lines.append(left+' & '+middle+' & '+right+r'\\\addlinespace[2pt]')
    lines += [r'\bottomrule\end{longtable}\endgroup']
    return '\n'.join(lines)+'\n'


def notes_evidence():
    s=['# SRAM DCIM 参数证据表','', '由 `data/inputs.json` 生成；页码为本地PDF页序。原始证据与采用值分开。', '',
       '| 编号/来源/定位 | 原值与单位 | 条件与证据性质 | 采用与换算理由 |', '|---|---|---|---|']
    for e in D['raw_evidence']:
        s.append('| '+' | '.join([e['id']+' / '+e['source_id']+' / '+e['locator'],e['original_value']+' ['+e['unit']+']',e['conditions']+'；'+e['kind'],e['adopted']+'；'+e['conversion_reason']]).replace('\n',' ')+' |')
    s += ['', 'SDCIM-02/04/05 保留目录与清单记录，但未用于本情景数值：02是65 nm；04性能标签混用且近似模式有不同延时；05有容量和FP8模式标注差异。主分析避免将这些headline拼接到D6型结构。',
          '', '关键原始页面已渲染目视核验：SDCIM-01 pp.1/4、CMOS-03 p.3、CMOS-07 p.9；另外原文全文/相关页文字核验包括SDCIM-03 pp.1-3、CMOS-07 pp.1-2/7-9。',
          '', '局限：128-bit 6T普通写完成周期没有同芯片实测值。本分析用同步28 nm CMOS证据、成功终点及共同节拍形成明确参考预算；不宣称0.9 V/25 °C严格PVT保证。']
    return '\n'.join(s)+'\n'


def generated():
    r=compute()
    return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n',
            'tex/generated_results.tex':table_results(r),'tex/generated_sensitivity.tex':table_sensitivity(r),
            'tex/generated_evidence.tex':evidence_tex(),'notes/evidence.zh.md':notes_evidence()}


class Checks(unittest.TestCase):
    def test_frozen_shared_and_sources(self):
        for f,expected in D['baseline_files'].items(): self.assertEqual(sha(SHARED/f),expected,f)
        self.assertEqual(sha(CORPUS/'source_manifest.json'),D['source_manifest_sha256'])
        for sid,s in D['sources'].items(): self.assertEqual(sha(CORPUS/s['pdf']['path']),s['pdf']['sha256'],sid)
    def test_mapping_and_payload(self):
        m=D['device_state_and_mapping']
        self.assertEqual(m['capacity_tiles']*math.prod(m['tile_physical_bits']),S.L['resident_capacity_Byte']*8)
        self.assertEqual(m['capacity_tiles']*m['tile_logical_weights'][1],S.L['n_out'])
        self.assertEqual(S.L['B_S_Byte'],128)
        self.assertLessEqual(128*128*128,2**23-1)
        self.assertEqual(S.L['resident_capacity_Byte']//16,1024)
    def test_round_coverage_against_original(self):
        r=compute()['scenarios'][0]
        self.assertEqual(r['counts']['compute_rounds'],512)
        self.assertEqual(r['counts']['compute_rounds']//8,64)
        self.assertEqual(r['physical_static_row_group_activations'],64)
        self.assertEqual(r['counts']['compute_rounds']*16*16,8*128*128)
        self.assertEqual(S.dcim_counts(S.R['dcim'])['compute_rounds'],256)
    def test_anchor_rounding_and_profiles(self):
        self.assertGreaterEqual(D['scenarios'][0]['complete_compute_round_ns'],1000/233)
        self.assertGreaterEqual(D['scenarios'][0]['complete_memory_cycle_ns'],1000/455)
        for r in compute()['scenarios']:
            v=S.C['propagation']['profile_values'][r['common_profile']]
            self.assertEqual(r['inputs']['common_T_D_ns'],v['digital_tick'])
            self.assertGreaterEqual(r['inputs']['complete_compute_round_ns'],v['digital_tick'])
    def test_complete_stages_no_double_count(self):
        for r in compute()['scenarios']:
            for service,key in [('streaming','delta_S_ns'),('resident','delta_R_ns')]:
                stages=r['stage_coverage'][service]
                self.assertAlmostEqual(sum(s['count']*s['duration_each_ns'] for s in stages),r[key])
            self.assertEqual(r['write_data_beats'],1)
            self.assertEqual(r['write_batches'],1)
            self.assertEqual(r['B_R_Byte'],16)
            self.assertEqual(r['delta_R_ns'],r['inputs']['complete_memory_cycle_ns'])
    def test_metrics_hand_checks_and_aggregation(self):
        r=compute()['scenarios'][1]
        self.assertEqual(r['delta_S_ns'],2570)
        self.assertEqual(r['delta_R_ns'],5)
        self.assertAlmostEqual(r['rho_Byte_per_s']/1e9,128/2570)
        self.assertAlmostEqual(r['tau_Byte_per_s']/1e9,16/5)
        self.assertAlmostEqual(r['ridge'],8*5/2570)
        agg=S.metrics(128,16384,2570,1024*5)
        self.assertAlmostEqual(agg['tau_Byte_per_s'],r['tau_Byte_per_s'])
        self.assertAlmostEqual(agg['ridge'],r['ridge'])
    def test_comparisons_do_not_replace_main(self):
        r=compute(); c={x['id']:x for x in r['sensitivities']}
        self.assertEqual(c['R0_same_clock_reference']['delta_S_ns'],1290)
        self.assertEqual(c['extra_handshake_reference']['delta_R_ns'],15)
        self.assertEqual(c['extra_handshake_reference']['delta_S_ns'],2570)
        self.assertEqual(len(r['scenarios']),3)
    def test_generated_files_current(self):
        for f,s in generated().items(): self.assertEqual((BASE/f).read_text(),s,f)


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--emit',action='store_true'); args=ap.parse_args()
    if args.emit:
        for f,s in generated().items(): (BASE/f).write_text(s)
    outcome=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    if outcome.wasSuccessful():
        r=compute()
        print(json.dumps({'baseline_sha256':r['baseline_files_actual']['data/shared_parameters.json'],'ranges':r['ranges']},ensure_ascii=False,indent=2))
    raise SystemExit(0 if outcome.wasSuccessful() else 1)
