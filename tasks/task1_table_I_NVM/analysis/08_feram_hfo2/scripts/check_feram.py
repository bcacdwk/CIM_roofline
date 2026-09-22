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


def calculate():
    rows = []
    mapping = I['mapping']
    cfg = copy.deepcopy(api.R['dcim'])
    assert cfg['rows_per_group'] == mapping['shards']
    assert cfg['output_lanes'] * cfg['weight_bits_per_round'] == mapping['local_row_bits']
    for name, media in I['paired_media_budgets_ns'].items():
        v = api.C['propagation']['profile_values'][name]
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
        rows.append(dict(id='D0_'+name, profile=name, mode=I['mode'], baseline_id=api.D['baseline_id'],
                         mapping_id=mapping['id'], media_read_complete_ns=read,
                         media_write_complete_ns=edges+2*pulse, counts=counts,
                         read_bits_per_round=mapping['shards']*mapping['local_row_bits'],
                         restore_rows_per_round=mapping['shards'],
                         restore_row_services_per_vector=counts['read_rounds']*mapping['shards'],
                         restore_bits_per_vector=counts['read_rounds']*mapping['shards']*mapping['local_row_bits'],
                         logical_update_rows=1, physical_write_phases=2, encoded_data_beats=beats,
                         matrix_write_rows=int(write_rows), matrix_delta_R_ns=write_rows*dr,
                         matrix_B_R_Byte=api.L['resident_capacity_Byte'],
                         stream_components_ns=stream_components, write_components_ns=write_components,
                         stream_dominant=max(stream_components, key=stream_components.get),
                         resident_dominant=max(write_components, key=write_components.get),
                         evidence_and_choices=I['budget_rationale'], **metrics))
    ref = next(r for r in rows if r['profile']=='reference')
    v = api.C['propagation']['profile_values']['reference']
    reuse = copy.deepcopy(cfg)
    reuse['read_reuse_input_slices'] = True
    reuse['weight_latch_bits'] = I['reuse_sensitivity']['extra_weight_latch_bits']
    # One capture tick per group; read API reports 32 physical groups.
    reuse['latch_extra_ns'] = api.dcim_counts(reuse)['read_rounds'] * v['digital_tick']
    ds, counts = api.dcim_service(reuse, v, ref['media_read_complete_ns'])
    compare = dict(id='D1_reuse', mode=I['mode'], baseline_id=api.D['baseline_id'],
                   mapping_id=mapping['id'], counts=counts,
                   extra_weight_latch_bits=reuse['weight_latch_bits'], latch_capture_ns=reuse['latch_extra_ns'],
                   restore_bits_per_vector=counts['read_rounds']*mapping['shards']*mapping['local_row_bits'],
                   **api.metrics(api.L['B_S_Byte'], ref['B_R_Byte'], ds, ref['delta_R_ns']))
    compare['rho_ratio_to_reference'] = compare['rho_Byte_per_s']/ref['rho_Byte_per_s']
    compare['tau_ratio_to_reference'] = compare['tau_Byte_per_s']/ref['tau_Byte_per_s']
    # Counterfactual for contribution only: dropping restore violates the main mode.
    no_restore_ds = ref['delta_S_ns'] - ref['stream_components_ns']['destructive_restore']
    envelopes = {key:[min(r[key] for r in rows), max(r[key] for r in rows)]
                 for key in ('rho_Byte_per_s','tau_Byte_per_s','ridge')}
    return dict(baseline_id=api.D['baseline_id'], mode=I['mode'], mapping=mapping,
                units=I['units'], provenance=I['provenance'], paired=rows,
                sensitivity=compare, paired_ranges=envelopes,
                independent_endpoint_ridge_envelope=[envelopes['rho_Byte_per_s'][0]/envelopes['tau_Byte_per_s'][1],
                                                     envelopes['rho_Byte_per_s'][1]/envelopes['tau_Byte_per_s'][0]],
                restore_contribution_reference=dict(fraction=ref['stream_components_ns']['destructive_restore']/ref['delta_S_ns'],
                     invalid_if_omitted_delta_S_ns=no_restore_ds,
                     rho_overstatement_if_omitted=ref['delta_S_ns']/no_restore_ds))


def tex_tables(r):
    labels={'short':'短','reference':'参考','long':'长'}
    table=[r'% Generated by check_feram.py --emit.',
           r'\begin{table}[htbp]\centering\small',
           r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
           r'情景 & $\Delta_S$ ($\mu$s) & $\Delta_R$ (ns) & $\rho$ (GB/s) & $\tau$ (GB/s) & $\RI^*$ & 整矩阵写 ($\mu$s)\\\midrule']
    for x in r['paired']:
        table.append(f"{labels[x['profile']]} & {x['delta_S_ns']/1000:.3f} & {x['delta_R_ns']:.0f} & {x['rho_Byte_per_s']/1e9:.5f} & {x['tau_Byte_per_s']/1e9:.5f} & {x['ridge']:.5f} & {x['matrix_delta_R_ns']/1000:.3f}\\\\")
    table += [r'\bottomrule\end{tabular}',r'\caption{同一1T1C二元映射的成对工程情景。$B_S=128$ Byte、$B_R=16$ Byte；末列为1024次局部行事务的聚合。}',r'\end{table}']
    comp=r['sensitivity']; ref=next(x for x in r['paired'] if x['profile']=='reference')
    table += [r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
              r'组织（参考时隙） & 读/计算轮 & $\Delta_S$ ($\mu$s) & $\rho$ (GB/s) & $\tau$ (GB/s) & $\RI^*$\\\midrule']
    for label,x in [('D0 每输入bit重读',ref),('D1 锁存后八次复用',comp)]:
        table.append(f"{label} & {x['counts']['read_rounds']}/{x['counts']['compute_rounds']} & {x['delta_S_ns']/1000:.3f} & {x['rho_Byte_per_s']/1e9:.5f} & {x['tau_Byte_per_s']/1e9:.5f} & {x['ridge']:.5f}\\\\")
    table += [r'\bottomrule\end{tabular}',r'\caption{只改变数字锁存复用。D1另有4096-bit权重锁存和32拍捕获，不改resident更新宽度。}',r'\end{table}']
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
    for r in result['paired']:
        assert r['counts']['read_rounds']==r['counts']['compute_rounds']==256
        assert r['read_bits_per_round']==4096
        assert r['restore_bits_per_vector']==api.L['resident_capacity_Byte']*8*8
        assert r['restore_row_services_per_vector']==8192
        assert r['encoded_data_beats']==1 and r['physical_write_phases']==2
        assert math.isclose(sum(r['stream_components_ns'].values()),r['delta_S_ns'])
        assert math.isclose(sum(r['write_components_ns'].values()),r['delta_R_ns'])
        assert math.isclose(r['ridge'],r['B_S_Byte']/r['B_R_Byte']*r['delta_R_ns']/r['delta_S_ns'])
        assert math.isclose(r['tau_Byte_per_s'],r['matrix_B_R_Byte']/api.seconds(r['matrix_delta_R_ns'],'ns'))
    comp=result['sensitivity']
    assert comp['counts']['read_rounds']==32 and comp['counts']['compute_rounds']==256
    assert comp['restore_bits_per_vector']==api.L['resident_capacity_Byte']*8
    assert comp['tau_ratio_to_reference']==1
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
        print(x['id'], 'DS=',x['delta_S_ns'],'ns DR=',x['delta_R_ns'],'ns rho=',x['rho_Byte_per_s']/1e9,'GB/s tau=',x['tau_Byte_per_s']/1e9,'GB/s ridge=',x['ridge'])


if __name__=='__main__': main()
