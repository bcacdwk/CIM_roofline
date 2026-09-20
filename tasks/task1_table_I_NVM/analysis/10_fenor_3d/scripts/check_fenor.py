#!/usr/bin/env python3
"""Read-only recomputation by default. --emit refreshes results and generated TeX.

Uses the shared baseline API for counts, interface, update sequences and metrics.
Only the FeFET bias/guard/verify adapter is local.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE.parents[1]
SHARED = BASE.parent / 'shared_baseline'
SPEC = importlib.util.spec_from_file_location('fenor_shared_api', SHARED/'scripts/check_shared.py')
API = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(API)
X = json.loads((BASE/'data/inputs.json').read_text())
M = X['mapping']
W = X['resident']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_service(profile, cells=None, strips=None):
    v = API.C['propagation']['profile_values'][profile['profile']]
    cells = cells or W['parallel_cells']
    strips = strips or W['parallel_strips']
    td = v['digital_tick']
    physical_bits = W['logical_weights_completed'] * X['state']['cells_per_weight']
    assert physical_bits % cells == 0
    batches = physical_bits // cells
    assert cells == strips * M['outputs_per_strip']
    assert cells <= W['binary_sense_lanes_available']
    compare_ticks = math.ceil(cells/W['compare_lanes'])
    edge = profile['bias_transition_ns']
    guard = W['guard_after_final_pulse_ns']
    assert guard >= edge
    # Ramp+, pulse+, return+, ramp-, pulse-, guard (including final return), read, compare.
    # Two ramps plus one inter-polarity return: no additional final return.
    stage = dict(bias_setup_and_interphase_return_ns=3*edge,
                 polarization_plateaus_ns=W['pulse_phases_per_batch']*W['pulse_width_ns'],
                 post_last_pulse_guard_including_return_ns=guard,
                 terminal_binary_read_ns=profile['complete_binary_read_ns'],
                 terminal_compare_ns=compare_ticks*td)
    front, beats = API.front_ns(W['encoded_load_bits'], td, W['first_data_in_command'])
    dr = API.program_sequence_ns(front, 0, [dict(count=batches,
           drive_program_ns=stage['bias_setup_and_interphase_return_ns']+stage['polarization_plateaus_ns'],
           verify_ns=stage['terminal_binary_read_ns']+stage['terminal_compare_ns'],
           recover_ns=stage['post_last_pulse_guard_including_return_ns'])])
    # program_sequence_ns is a sum API; chronological order is explicitly in the ledger above.
    return dr, dict(physical_bits=physical_bits, physical_batches=batches, data_beats=beats,
             cells_per_batch=cells, strips_per_batch=strips, polarity_pulse_slots=2*batches,
             verify_reads=batches, compare_ticks=compare_ticks*batches,
             front_ns=front, per_batch_stage_ns=stage,
             total_stage_ns={k:val*batches for k,val in stage.items()},
             complete_batch_ns=sum(stage.values()))


def recompute():
    cfg = copy.deepcopy(API.R['dcim'])
    cfg.update(M['r0_dcim_overrides'])
    out = []
    for p in X['profiles']:
        v = API.C['propagation']['profile_values'][p['profile']]
        ds, counts = API.dcim_service(cfg, v, p['complete_binary_read_ns'])
        dr, wc = write_service(p)
        metrics = API.metrics(API.L['B_S_Byte'], W['logical_weights_completed']*API.L['b_R'], ds, dr)
        out.append(dict(profile=p['profile'], mode=X['mode'], baseline_id=API.D['baseline_id'],
                   mapping_id='R0_32_lateral_lanes_4_capacity_layers',
                   input_parameters=p, common_periphery_ns=v, streaming_counts=counts, resident_counts=wc,
                   streaming_stages_ns=dict(binary_read=counts['read_rounds']*p['complete_binary_read_ns'],
                         digital=counts['digital_ticks']*v['digital_tick'], boundary=cfg['boundary_ticks']*v['digital_tick']),
                   dominant_streaming='binary read service over 256 rounds',
                   dominant_resident='post-pulse observation-window guard over eight strips',
                   **metrics))
    ref = next(r for r in out if r['profile']=='reference')
    p = next(p for p in X['profiles'] if p['profile']=='reference')
    contrast = X['structural_contrast']
    dr, wc = write_service(p, contrast['parallel_cells'], contrast['parallel_strips'])
    c = dict(id=contrast['id'], profile='reference', baseline_id=API.D['baseline_id'],
             mode=X['mode'], resident_counts=wc,
             **API.metrics(API.L['B_S_Byte'],ref['B_R_Byte'],ref['delta_S_ns'],dr))
    c['rho_ratio_to_reference'] = c['rho_Byte_per_s']/ref['rho_Byte_per_s']
    c['tau_ratio_to_reference'] = c['tau_Byte_per_s']/ref['tau_Byte_per_s']
    c['ridge_ratio_to_reference'] = c['ridge']/ref['ridge']
    manifest = json.loads((CORPUS/'source_manifest.json').read_text())
    sources = {s['source_id']:s['pdf'] for s in manifest['sources'] if s['group']=='10_fenor_3d'}
    rows = API.L['n_in']; outputs = API.L['n_out']; bits = int(API.L['b_R']*8)
    aggregation_count = rows*(outputs//W['logical_weights_completed'])
    return dict(case_id=X['case_id'], baseline_id=API.D['baseline_id'],
        units=dict(time='ns', payload='Byte', throughput='Byte/s; divide by 1e9 for GB/s', ridge='dimensionless'),
        input_sha256=sha(BASE/'data/inputs.json'),
        shared_parameter_sha256=sha(SHARED/'data/shared_parameters.json'),
        shared_api_sha256=sha(SHARED/'scripts/check_shared.py'), sources=sources,
        local_physical_cells=rows*outputs*bits, source_selection='FENOR-02 timing/bias; FENOR-01 mechanism; FENOR-04 and 06 state-specific cross-checks',
        main_scenarios=out, structural_contrast=c,
        paired_range={key:[min(s[key] for s in out),max(s[key] for s in out)] for key in ['rho_Byte_per_s','tau_Byte_per_s','ridge']},
        full_matrix_aggregation=dict(native_logical_transactions=aggregation_count, logical_Byte=API.L['resident_capacity_Byte'],
                  reference_time_ns=aggregation_count*ref['delta_R_ns'], tau_Byte_per_s=ref['tau_Byte_per_s']),
        guard_sensitivity=dict(extra_guard_ns_per_batch=10, extra_transaction_ns=80,
                  relative_ridge_change=80/ref['delta_R_ns']))


def tex_table(result):
    s=[r'% Generated by scripts/check_fenor.py --emit.', r'\begin{table}[htbp]\centering\small',
       r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
       r'情景 & $\Delta_S$ (ns) & $\Delta_R$ (ns) & $\rho$ (GB/s) & $\tau$ (GB/s) & $\RI^*$\\\midrule']
    for r,label in zip(result['main_scenarios'],['短','参考','长']):
        s.append(f"{label} & {r['delta_S_ns']:.0f} & {r['delta_R_ns']:.0f} & {r['rho_Byte_per_s']/1e9:.5f} & {r['tau_Byte_per_s']/1e9:.5f} & {r['ridge']:.4f}"+r'\\')
    r=result['structural_contrast']
    s += [r'\midrule', f"参考，128-cell 写 & {r['delta_S_ns']:.0f} & {r['delta_R_ns']:.0f} & {r['rho_Byte_per_s']/1e9:.5f} & {r['tau_Byte_per_s']/1e9:.5f} & {r['ridge']:.4f}"+r'\\',
       r'\bottomrule\end{tabular}',
       r'\caption{同一二状态映射的配对结果。主情景每批16 cell；最后一行增加八倍写驱动资源，另列为结构对照。}', r'\label{tab:result}\end{table}']
    return '\n'.join(s)+'\n'


def checks(result):
    assert X['baseline_id']==API.D['baseline_id']=='shared_baseline'
    assert len(result['main_scenarios'])==3
    # Enumerate the entire physical address map and each native logical transaction.
    addr=set()
    for i in range(API.L['n_in']):
        for o in range(API.L['n_out']):
            for b in range(8):
                address=(i%32, i//32, (o//16)*8+b, o%16)
                assert address not in addr
                addr.add(address)
    assert len(addr)==result['local_physical_cells']==131072
    assert M['independent_row_read_lanes']*M['strips_per_row_lane']*M['cells_per_strip']==len(addr)
    assert M['parallel_binary_sense_nodes']==32*16*8
    # Voltage-table proof for both polarities and both existing binary states.
    for polarity in [-1,1]:
        vw=W['full_selected_gate_channel_V']; unit=polarity*vw/3
        selected_wl,unselected_wl=2*unit,unit
        target_channel,inhibit_channel=-unit,unit
        assert math.isclose(selected_wl-target_channel,polarity*vw)
        assert math.isclose(selected_wl-inhibit_channel,polarity*vw/3)
        assert math.isclose(unselected_wl-target_channel,2*polarity*vw/3)
        assert math.isclose(unselected_wl-inhibit_channel,0)
        assert math.isclose(selected_wl-unselected_wl,polarity*vw/3)
    for row,p in zip(result['main_scenarios'],X['profiles']):
        v=API.C['propagation']['profile_values'][p['profile']]
        assert row['streaming_counts']['compute_rounds']==256
        assert row['streaming_counts']['read_rounds']==256
        assert row['delta_S_ns']==256*(p['complete_binary_read_ns']+v['digital_tick'])+2*v['digital_tick']
        wc=row['resident_counts']
        assert wc['physical_batches']==8 and wc['physical_bits']==128 and wc['data_beats']==1
        assert wc['polarity_pulse_slots']==16 and wc['verify_reads']==8
        expected=2*v['digital_tick']+8*(3*p['bias_transition_ns']+40+100+p['complete_binary_read_ns']+v['digital_tick'])
        assert row['delta_R_ns']==expected
        assert math.isclose(row['ridge'],8*row['delta_R_ns']/row['delta_S_ns'])
        assert math.isclose(row['rho_Byte_per_s']/row['tau_Byte_per_s'],row['ridge'])
        assert row['delta_R_ns']==wc['front_ns']+sum(wc['total_stage_ns'].values())
        assert row['delta_S_ns']==sum(row['streaming_stages_ns'].values())
        driver=X['engineering_driver_budget']
        required=driver['maximum_effective_capacitance_per_driven_node_fF']*driver['worst_swing_V']/p['bias_transition_ns'] # fF*V/ns = uA
        assert required<=driver['slew_current_uA_by_profile'][p['profile']]
    ref=result['main_scenarios'][1]
    assert ref['delta_S_ns']==11530 and ref['delta_R_ns']==1730
    assert result['structural_contrast']['delta_R_ns']==260
    assert result['structural_contrast']['resident_counts']['compare_ticks']==8
    assert result['full_matrix_aggregation']['native_logical_transactions']==1024
    assert result['full_matrix_aggregation']['reference_time_ns']==1771520
    assert math.isclose(16384/(1771520e-9),ref['tau_Byte_per_s'])
    for source in result['sources'].values():
        assert sha(CORPUS/source['path'])==source['sha256']
    assert not W['erase_block'] and not W['pre_reset']
    assert X['state']['independent_service_units']==W['write_domains']==1
    assert result['structural_contrast']['rho_ratio_to_reference']==1


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit',action='store_true')
    args=parser.parse_args()
    result=recompute(); checks(result)
    generated={BASE/'data/results.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n',
               BASE/'tex/generated_results.tex':tex_table(result)}
    if args.emit:
        for p,content in generated.items(): p.write_text(content)
    for p,content in generated.items():
        assert p.read_text()==content, f'Stale generated file: {p}; run --emit explicitly'
    print('PASS: shared API, all-cell mapping, bias masks, staged services, paired units, matrix aggregation, source hashes and generated files')
    for row in result['main_scenarios']:
        print(f"{row['profile']}: DS={row['delta_S_ns']} ns DR={row['delta_R_ns']} ns rho={row['rho_Byte_per_s']/1e9:.7f} GB/s tau={row['tau_Byte_per_s']/1e9:.7f} GB/s RI*={row['ridge']:.7f}")


if __name__=='__main__': main()
