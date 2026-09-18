#!/usr/bin/env python3
"""Recompute only 05_rram artifacts using the unchanged shared calculation API."""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE.parents[1]
SHARED = BASE.parent / 'shared_baseline'
X = json.loads((BASE / 'data/inputs.json').read_text())
PROV = json.loads((BASE / 'data/provenance.json').read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

spec = importlib.util.spec_from_file_location('rram_shared_api', SHARED / 'scripts/check_shared.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)

def write_service(profile, extra_ns=0, attempts=1, extra_frontend_ns=0):
    """One mandatory program/verify loop per selected cell, sequential, successful only.

    extra_ns comprises all unknown HV setup + pulse + recovery in an attempt.
    extra_ns=0 is a mathematical bound, never a physical RRAM update claim.
    """
    assert extra_ns >= 0 and attempts >= 1 and extra_frontend_ns >= 0
    cfg = X['configuration']
    n_cells = cfg['logical_weights_per_update'] * cfg['cells_per_weight']
    front, beats = S.front_ns(cfg['encoded_load_bits'], profile['digital_tick'], cfg['first_data_in_command'])
    verify = (profile['input_step'] + X['adopted_inputs']['front_end_settle_ns']['value']
              + extra_frontend_ns + profile['adc_batch'] + profile['digital_tick'])
    steps = [dict(count=n_cells * attempts,
                  drive_program_ns=profile['digital_tick'] + extra_ns,
                  verify_ns=verify, recover_ns=0)]
    return S.program_sequence_ns(front, 0, steps), dict(
        cells=n_cells, data_beats=beats, front_ns=front, program_verify_attempts=n_cells*attempts,
        control_ns_per_attempt=profile['digital_tick'], verify_including_compare_ns=verify,
        unknown_HV_pulse_recover_ns_per_attempt=extra_ns,
        steps=steps)

def cell_update_at_ridge(ridge, ds, profile):
    """Solve a capacity threshold through shared direct_service/metrics, not a media value."""
    cfg = X['configuration']
    x = dict(logical_weights_completed=cfg['logical_weights_per_update'],
             cells_per_weight=cfg['cells_per_weight'], parallel_cells=cfg['parallel_program_cells'],
             encoded_load_bits=cfg['encoded_load_bits'], first_data_in_command=True,
             complete_physical_update_ns=0)
    def evaluate(u):
        xx = {**x, 'complete_physical_update_ns':u}
        br, dr, _, _ = S.direct_service(xx, profile['digital_tick'])
        return S.metrics(S.L['B_S_Byte'], br, ds, dr)['ridge']
    low, high = 0, 1
    while evaluate(high) < ridge:
        high *= 2
    for _ in range(80):
        mid = (low+high)/2
        if evaluate(mid) < ridge:
            low = mid
        else:
            high = mid
    assert math.isclose(evaluate(high), ridge, rel_tol=1e-10)
    return high

def calculate():
    acim = {**copy.deepcopy(S.R['acim']), **X['configuration']['acim_overrides']}
    a = X['adopted_inputs']['front_end_settle_ns']['value']
    rows = []
    for name, profile in S.C['propagation']['profile_values'].items():
        ds, counts, hold = S.acim_service(acim, profile, a)
        dr_bound, write_details = write_service(profile)
        br = X['configuration']['logical_weights_per_update'] * S.L['b_R']
        bound = S.metrics(S.L['B_S_Byte'], br, ds, dr_bound)
        ds_r0 = S.acim_service(S.R['acim'], profile, a)[0]
        rho = bound['rho_Byte_per_s']
        rows.append(dict(profile=name, periphery_ns=profile, counts=counts, hold_extra_ns=hold,
            B_S_Byte=S.L['B_S_Byte'], B_R_Byte=br, delta_S_ns_conditional_hA0=ds,
            rho_Byte_per_s_conditional_hA0=rho,
            R0_same_frontend_delta_S_ns=ds_r0,
            rho_ratio_to_unconstrained_R0=ds_r0/ds,
            write_absolute_time_identified=False,
            tau_Byte_per_s=None, ridge=None,
            write_boundary_not_physical_estimate=dict(
                assumptions='p=1; K_j=1; unknown HV/pulse/recovery contribution is set to its zero mathematical lower boundary; h_A=0',
                delta_R_ns_lower_boundary=dr_bound,
                tau_Byte_per_s_upper_boundary=bound['tau_Byte_per_s'],
                ridge_lower_boundary=bound['ridge'],
                complete_cell_update_ns_lower_boundary=(dr_bound-write_details['front_ns'])/write_details['cells'],
                details=write_details),
            complete_cell_update_threshold_ns={str(k):cell_update_at_ridge(k,ds,profile) for k in [1,10,100]},
            unknown_hA_extra_streaming_multiplier=counts['evaluations']))
    sens=[]
    v=S.C['propagation']['profile_values']['reference']
    for h in [0,5]:
        ds=S.acim_service(acim,v,a+h)[0]
        dr,_=write_service(v,extra_frontend_ns=h)
        b=S.metrics(S.L['B_S_Byte'],16,ds,dr)
        sens.append(dict(h_A_ns=h,meaning='additional one-PH0-sized interface allowance, not measured delay range',
                         delta_S_ns=ds,rho_Byte_per_s=b['rho_Byte_per_s'],
                         tau_upper_boundary_Byte_per_s=b['tau_Byte_per_s'],ridge_lower_boundary=b['ridge']))
    return dict(schema_version='rram-pilot-results-1.0',status=X['status'],
        baseline_json_sha256=digest(SHARED/'data/shared_parameters.json'),
        baseline_script_sha256=digest(SHARED/'scripts/check_shared.py'),
        input_sha256=digest(BASE/'data/inputs.json'),
        numerical_media_write_point_available=False,
        rho_conditional_range_Byte_per_s=[min(r['rho_Byte_per_s_conditional_hA0'] for r in rows),max(r['rho_Byte_per_s_conditional_hA0'] for r in rows)],
        warning='The read range assumes h_A=0 and compatible calibrated analog interface. Write boundaries are mathematical bounds for the declared serial verified update policy, not finite media throughput estimates.',
        scenarios=rows,frontend_sensitivity=sens)

LABEL={'short':'短时隙','reference':'参考','long':'长时隙'}
def esc(s):
    for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:
        s=s.replace(a,b)
    return s.replace('µ',r'$\mu$').replace('×',r'$\times$').replace('Ω',r'$\Omega$').replace('−','-')

def generate(result):
    lines=[r'% Generated from data/inputs.json through shared calculation API.',
        r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
        r'情景 & $T_I/T_A/T_D$ (ns) & $\Delta_S$ (ns) & $\rho$ (GB/s) & $\tau_{\rm ceiling}$ (GB/s) & $\RI^*_{\rm floor}$\\\midrule']
    for r in result['scenarios']:
        v=r['periphery_ns'];b=r['write_boundary_not_physical_estimate']
        lines.append(f"{LABEL[r['profile']]} & {v['input_step']}/{v['adc_batch']}/{v['digital_tick']} & {r['delta_S_ns_conditional_hA0']:g} & {r['rho_Byte_per_s_conditional_hA0']/1e9:.5f} & {b['tau_Byte_per_s_upper_boundary']/1e9:.5f} & {b['ridge_lower_boundary']:.4f}\\\\")
    lines += [r'\bottomrule\end{tabular}',r'\caption{B32 的条件读侧结果与串行校验写策略的数学边界。全部取 $h_A=0$。$\tau_{\rm ceiling}$ 忽略未知脉冲、高压建立与恢复并令每 cell 一次成功，是上边界；$\RI^*_{\rm floor}$ 是对应下边界。两列均非 RRAM 完整写入实测或预测点。}\label{tab:read}\end{table}']
    thresholds=[r'% Generated capacity thresholds, not assumed RRAM times.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrr@{}}\toprule',r'情景 & 已计控制/校验下边界 (ns/cell) & $u_{\RI^*=1}$ & $u_{\RI^*=10}$ & $u_{\RI^*=100}$\\\midrule']
    for r in result['scenarios']:
        b=r['write_boundary_not_physical_estimate'];t=r['complete_cell_update_threshold_ns']
        thresholds.append(f"{LABEL[r['profile']]} & {b['complete_cell_update_ns_lower_boundary']:g} & {t['1']:.3f} & {t['10']:.3f} & {t['100']:.3f}\\\\")
    thresholds += [r'\bottomrule\end{tabular}',r'\caption{完整单 cell 服务时间 $u$ 的 ridge 门槛，后三列单位均为 ns。由 $\Delta_R=2T_D+128u$ 与共同服务公式反解，只回答“多快的完整更新对应这个 ridge”，不宣称器件具备该速度。}\label{tab:threshold}\end{table}']
    evidence=[r'% Generated original/choice evidence table.',r'\begingroup\footnotesize',r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{16mm}>{\raggedright\arraybackslash}p{50mm}>{\raggedright\arraybackslash}p{42mm}>{\raggedright\arraybackslash}p{48mm}@{}}',r'\caption{参数证据与采用方式。页码均为本地 PDF 第1页起的页序。}\label{tab:evidence}\\',r'\toprule ID/来源 & 原值、单位、条件 & 定位 & 采用/换算及限制\\\midrule\endfirsthead',r'\toprule ID/来源 & 原值、单位、条件 & 定位 & 采用/换算及限制\\\midrule\endhead']
    md=['# RRAM 参数证据表','','原值、参考选择与推导分开；从 `data/inputs.json` 生成。','','| ID/来源 | 原值与单位 | 条件与定位 | 采用/换算理由 |','|---|---|---|---|']
    for e in X['reported_evidence']:
        evidence.append(f"{esc(e['id'])}\\newline {esc(e['source_id'] if e['source_id']!='shared_baseline' else '共享基线')} & {esc(e['original'])}\\newline {esc(e['condition'])} & {esc(e['locator'])} & {esc(e['adoption'])}\\\\")
        md.append(f"| {e['id']} / {e['source_id']} | {e['original']} | {e['condition']}；{e['locator']} | {e['adoption']} |")
    evidence += [r'\bottomrule\end{longtable}\endgroup']
    return {'data/results.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n',
            'tex/generated_read.tex':'\n'.join(lines)+'\n',
            'tex/generated_thresholds.tex':'\n'.join(thresholds)+'\n',
            'tex/generated_evidence.tex':'\n'.join(evidence)+'\n',
            'notes/parameter_evidence.zh.md':'\n'.join(md)+'\n'}

def check(result):
    assert digest(SHARED/'data/shared_parameters.json') == X['baseline']['json_sha256']
    assert digest(SHARED/'scripts/check_shared.py') == X['baseline']['script_sha256']
    for s in PROV['corpus_sources']:
        assert digest(CORPUS/s['path']) == s['sha256'], s['source_id']
    for s in PROV['read_files']:
        assert digest(CORPUS/s['path']) == s['sha256'], s['path']
    assert X['configuration']['physical_data_cells'] == S.L['resident_capacity_Byte']*8
    assert 64*32*64 == X['configuration']['physical_data_cells']
    for r in result['scenarios']:
        n=r['counts'];b=r['write_boundary_not_physical_estimate'];detail=b['details']
        assert (n['input_slices'],n['row_groups'],n['weight_groups']) == (8,4,1)
        assert (n['evaluations'],n['adc_batches'],n['digital_ticks']) == (256,256,512)
        assert n['useful_scalar_conversions'] == 32768
        assert detail['cells'] == 128 and detail['data_beats'] == 1
        assert r['B_S_Byte']==128 and r['B_R_Byte']==16
        assert r['tau_Byte_per_s'] is None and r['ridge'] is None
        assert 3.99 < b['ridge_lower_boundary'] < 4.01
        assert r['complete_cell_update_threshold_ns']['1'] < b['complete_cell_update_ns_lower_boundary']
        # Verify exactly the same total complete-cell grouping via the other shared template.
        cfg=X['configuration'];v=r['periphery_ns']
        br,dr,nb,_=S.direct_service(dict(logical_weights_completed=16,cells_per_weight=8,parallel_cells=1,
              encoded_load_bits=128,first_data_in_command=True,
              complete_physical_update_ns=b['complete_cell_update_ns_lower_boundary']),v['digital_tick'])
        assert dr==b['delta_R_ns_lower_boundary'] and br==16 and nb==128
        # A positive unknown physical step cannot exceed the zero-step throughput bound.
        drplus,_=write_service(v,extra_ns=1)
        m=S.metrics(128,16,r['delta_S_ns_conditional_hA0'],drplus)
        assert m['tau_Byte_per_s'] < b['tau_Byte_per_s_upper_boundary']
    assert math.isclose(S.seconds(1,'us'), S.seconds(1000,'ns'), rel_tol=1e-12)
    assert result['numerical_media_write_point_available'] is False
    print('PASS: baseline/source hashes, B32 mapping, 256/256/512 counts, bytes/units, program/direct agreement, symbolic threshold roots, bound direction, generated-file equality.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    result=calculate();check(result)
    files=generate(result)
    for name,text in files.items():
        path=BASE/name
        if args.emit:path.write_text(text)
        else:assert path.read_text()==text, f'stale generated file: {name}; run --emit'
    if args.emit:print('Emitted generated artifacts inside 05_rram only.')
    for r in result['scenarios']:
        print(r['profile'],r['delta_S_ns_conditional_hA0'],r['rho_Byte_per_s_conditional_hA0']/1e9,r['complete_cell_update_threshold_ns'])

if __name__=='__main__':main()
