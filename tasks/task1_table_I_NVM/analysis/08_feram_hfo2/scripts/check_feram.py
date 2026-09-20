#!/usr/bin/env python3
"""Read-only paired calculation/check. --emit refreshes JSON and generated TeX."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True

BASE = Path(__file__).resolve().parents[1]
SHARED = BASE.parent / 'shared_baseline'
CORPUS = BASE.parents[1]
spec = importlib.util.spec_from_file_location('shared_api', SHARED / 'scripts/check_shared.py')
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)
I = json.loads((BASE / 'data/inputs.json').read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def make_row(name, media, profile, reuse=True, scenario_type='paired_engineering'):
    mapping = I['mapping']
    cfg = copy.deepcopy(api.R['dcim'])
    assert cfg['rows_per_group'] == mapping['shards']
    assert cfg['output_lanes'] * cfg['weight_bits_per_round'] == mapping['local_row_bits']
    cfg['read_reuse_input_slices'] = reuse
    # Already present in the original D0 data path: no second copy or extra capture.
    cfg['weight_latch_bits'] = mapping['D0_round_readout_register_bits']
    cfg['latch_extra_ns'] = 0
    v = api.C['propagation']['profile_values'][profile]
    sense, pulse, edges = (media[k] for k in ('sense', 'polarization_hold_per_phase', 'open_close_bias_total'))
    read = sense + pulse + edges
    front, beats = api.front_ns(mapping['local_row_bits'], v['digital_tick'], True)
    dr = api.program_sequence_ns(front, edges, [dict(count=2, drive_program_ns=pulse, verify_ns=0, recover_ns=0)])
    br = mapping['local_row_bits'] / 8
    ds, counts = api.dcim_service(cfg, v, read)
    metrics = api.metrics(api.L['B_S_Byte'], br, ds, dr)
    write_rows = api.L['resident_capacity_Byte'] / br
    assert write_rows.is_integer()
    stream_components = dict(sense=counts['read_rounds'] * sense,
                             destructive_restore=counts['read_rounds'] * pulse,
                             dedicated_open_close=counts['read_rounds'] * edges,
                             compute=counts['digital_ticks'] * v['digital_tick'],
                             boundary=cfg['boundary_ticks'] * v['digital_tick'])
    write_components = dict(interface_control=front, target_polarity_phases=2*pulse,
                            dedicated_open_close=edges)
    return dict(id=name, profile=profile, scenario_type=scenario_type,
                mode=I['mode'] if reuse else I['mode'].replace('existing 4096-bit read-code register reused across 8 input bits', 'same 4096-bit read-code register with per-input-bit repeated reads'),
                schedule='group_then_all_input_bits' if reuse else 'reread_each_input_bit',
                baseline_id=api.D['baseline_id'], mapping_id=mapping['id'],
                media_budgets_ns=media, media_read_complete_ns=read,
                media_write_complete_ns=edges+2*pulse, counts=counts,
                existing_operand_register_bits=4096, extra_weight_latch_bits=0, latch_capture_extra_ns=0,
                read_bits_per_round=mapping['shards']*mapping['local_row_bits'],
                restore_rows_per_round=mapping['shards'],
                restore_row_services_per_vector=counts['read_rounds']*mapping['shards'],
                restore_bits_per_vector=counts['read_rounds']*mapping['shards']*mapping['local_row_bits'],
                logical_update_rows=1, physical_write_phases=2, encoded_data_beats=beats,
                update_pattern='one aligned 128-bit physical row: 16 adjacent INT8 weights from one logical input row and one aligned output group',
                matrix_write_rows=int(write_rows), matrix_delta_R_ns=write_rows*dr,
                matrix_B_R_Byte=api.L['resident_capacity_Byte'],
                stream_components_ns=stream_components, write_components_ns=write_components,
                stream_dominant=max(stream_components, key=stream_components.get),
                resident_dominant=max(write_components, key=write_components.get),
                periodic_maintenance_fraction=0, raw_equals_effective=True,
                feasibility='conditional engineering design with full destructive restore included',
                evidence_and_choices=I['budget_rationale'], **metrics)


def calculate():
    rows = [make_row('D0_'+name, media, name,
                    scenario_type='recommended_reference' if name=='reference' else 'paired_engineering')
            for name, media in I['paired_media_budgets_ns'].items()]
    ref = next(r for r in rows if r['profile']=='reference')
    compare = make_row('D_repeat_reference', I['paired_media_budgets_ns']['reference'],
                       'reference', reuse=False, scenario_type='scheduling_sensitivity')
    compare['rho_ratio_to_reference'] = compare['rho_Byte_per_s']/ref['rho_Byte_per_s']
    compare['tau_ratio_to_reference'] = compare['tau_Byte_per_s']/ref['tau_Byte_per_s']
    hold_rows=[]
    for pulse in I['polarization_sensitivity']['values_ns']:
        media=dict(sense=20, polarization_hold_per_phase=pulse, open_close_bias_total=40)
        hold_rows.append(make_row('fixed_hold_'+str(pulse)+'ns', media, 'reference',
                                 scenario_type='independent_hold_sensitivity'))
    # Counterfactual for contribution only: dropping restore violates the main mode.
    no_restore_ds = ref['delta_S_ns'] - ref['stream_components_ns']['destructive_restore']
    envelopes = {key:[min(r[key] for r in rows), max(r[key] for r in rows)]
                 for key in ('rho_Byte_per_s','tau_Byte_per_s','ridge')}
    return dict(baseline_id=api.D['baseline_id'], mode=I['mode'], mapping=I['mapping'],
                units=I['units'], provenance=I['provenance'], paired=rows,
                sensitivity=compare, polarization_sensitivity=hold_rows,
                paired_ranges=envelopes, scenario_semantics=I['scenario_semantics'],
                restore_contribution_reference=dict(fraction=ref['stream_components_ns']['destructive_restore']/ref['delta_S_ns'],
                     invalid_if_omitted_delta_S_ns=no_restore_ds,
                     rho_overstatement_if_omitted=ref['delta_S_ns']/no_restore_ds))


def tex_tables(r):
    labels={'short':'短','reference':'参考','long':'长'}
    table=[r'% Generated by check_feram.py --emit.',
           r'\begin{table}[htbp]\centering\small',
           r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
           r'情景 & $\Delta_S$ ($\mu$s) & $\Delta_R$ (ns) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for x in r['paired']:
        table.append(f"{labels[x['profile']]} & {x['delta_S_ns']/1000:.3f} & {x['delta_R_ns']:.0f} & {x['rho_Byte_per_s']/1e6:.3f} & {x['tau_Byte_per_s']/1e6:.3f} & {x['ridge']:.5f}"+r'\\')
    table += [r'\bottomrule\end{tabular}',r'\caption{D0同寄存器跨位复用的成对条件工程情景。$B_S=128$ Byte、$B_R=16$ Byte；整矩阵写为1024次局部行事务，短/参考/长为53.248/153.600/307.200 $\mu$s。}',r'\end{table}']
    comp=r['sensitivity']; ref=next(x for x in r['paired'] if x['profile']=='reference')
    table += [r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
              r'组织（参考时隙） & 读/计算轮 & $\Delta_S$ ($\mu$s) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for label,x in [('D0 同寄存器八位复用',ref),('逐输入bit重读对照',comp)]:
        table.append(f"{label} & {x['counts']['read_rounds']}/{x['counts']['compute_rounds']} & {x['delta_S_ns']/1000:.3f} & {x['rho_Byte_per_s']/1e6:.3f} & {x['tau_Byte_per_s']/1e6:.3f} & {x['ridge']:.5f}"+r'\\')
    table += [r'\bottomrule\end{tabular}',r'\caption{同一硬件的调度对照。已有4096-bit读码寄存器，无第二份权重锁存或额外捕获拍；每次真实破坏读均恢复整行。}',r'\end{table}']
    table += [r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
              r'$t_p$ (ns) & $\Delta_S$ ($\mu$s) & $\Delta_R$ (ns) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for x in r['polarization_sensitivity']:
        table.append(f"{x['media_budgets_ns']['polarization_hold_per_phase']} & {x['delta_S_ns']/1000:.3f} & {x['delta_R_ns']:.0f} & {x['rho_Byte_per_s']/1e6:.3f} & {x['tau_Byte_per_s']/1e6:.3f} & {x['ridge']:.5f}"+r'\\')
    table += [r'\bottomrule\end{tabular}',r'\caption{独立保持窗口对照：固定$T_D=5$ ns、$t_s=20$ ns和$t_e=40$ ns，只改变同一$t_p$，共同进入一次读恢复与两相外部写。不是额外不确定性区间。}',r'\end{table}']
    return '\n'.join(table)+'\n'


def check(result):
    assert I['provenance']['shared_json_sha256']==sha(SHARED/'data/shared_parameters.json')
    assert I['provenance']['shared_api_sha256']==sha(SHARED/'scripts/check_shared.py')
    for s in I['sources']:
        assert sha(CORPUS / s['path']) == s['sha256'], s['id']
    # Exhaustive bijection: 131072 logical bits occupy 32 * 32 * 128 sites.
    seen=set()
    for i in range(api.L['n_in']):
        for j in range(api.L['n_out']):
            for k in range(8):
                seen.add((i%32,(i//32)*8+j//16,(j%16)*8+k))
    assert len(seen)==api.L['resident_capacity_Byte']*8
    assert max(x[1] for x in seen)==31 and max(x[2] for x in seen)==127
    # Check both target states and both prior states under the two plate phases.
    for old in (0,1):
        for target in (0,1):
            state=old
            for pl in (1,0):
                field=pl-target
                if field>0: state=0
                elif field<0: state=1
            assert state==target
    for r in result['paired'] + result['polarization_sensitivity']:
        assert r['counts']['read_rounds']==32 and r['counts']['compute_rounds']==256
        assert r['read_bits_per_round']==4096
        assert r['restore_bits_per_vector']==api.L['resident_capacity_Byte']*8
        assert r['restore_row_services_per_vector']==1024
        assert r['encoded_data_beats']==1 and r['physical_write_phases']==2
        assert math.isclose(sum(r['stream_components_ns'].values()),r['delta_S_ns'])
        assert math.isclose(sum(r['write_components_ns'].values()),r['delta_R_ns'])
        assert math.isclose(r['ridge'],r['B_S_Byte']/r['B_R_Byte']*r['delta_R_ns']/r['delta_S_ns'])
        assert math.isclose(r['tau_Byte_per_s'],r['matrix_B_R_Byte']/api.seconds(r['matrix_delta_R_ns'],'ns'))
    comp=result['sensitivity']
    assert comp['counts']['read_rounds']==256 and comp['counts']['compute_rounds']==256
    assert comp['restore_bits_per_vector']==api.L['resident_capacity_Byte']*8*8
    assert comp['tau_ratio_to_reference']==1
    assert I['mapping']['additional_weight_latch_bits']==0
    assert all(r['latch_capture_extra_ns']==0 for r in result['paired'])
    hold_ref=next(x for x in result['polarization_sensitivity'] if x['media_budgets_ns']['polarization_hold_per_phase']==50)
    main_ref=next(x for x in result['paired'] if x['profile']=='reference')
    assert hold_ref['delta_S_ns']==main_ref['delta_S_ns'] and hold_ref['delta_R_ns']==main_ref['delta_R_ns']
    assert I['stage_coverage']['destructive_restore_counted_in_media_read']
    assert not I['stage_coverage']['extra_restore_after_complete_read']
    assert not I['stage_coverage']['c2feram_timing_imported']


def main():
    p=argparse.ArgumentParser(); p.add_argument('--emit',action='store_true'); args=p.parse_args()
    r=calculate(); check(r)
    generated={BASE/'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n',
               BASE/'tex/generated_results.tex':tex_tables(r)}
    for path,text in generated.items():
        if args.emit: path.write_text(text)
        else: assert path.read_text()==text, f'Stale generated file: {path}; run --emit explicitly.'
    print('FeRAM checks passed: shared hashes, PDF hashes, mapping, two-polarity write, full-row restore, units, aggregation, paired results and reuse.')
    for x in r['paired']:
        print(x['id'], 'DS=',x['delta_S_ns'],'ns DR=',x['delta_R_ns'],'ns rho=',x['rho_Byte_per_s']/1e6,'MB/s tau=',x['tau_Byte_per_s']/1e6,'MB/s ridge=',x['ridge'])


if __name__=='__main__': main()
