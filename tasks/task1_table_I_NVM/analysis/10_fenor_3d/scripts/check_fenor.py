#!/usr/bin/env python3
"""Recompute the native FeFET reference with shared APIs; --emit updates derivatives."""
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
M, W = X['mapping'], X['resident']
L = API.logical_configuration(**{k:X['logical_configuration'][k] for k in ['K','N','b_S','b_R']})


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_service(profile, cells=None, strips=None, observation_ns=None):
    cells = W['parallel_cells'] if cells is None else cells
    strips = W['parallel_strips'] if strips is None else strips
    td = API.C['propagation']['profile_values'][profile['profile']]['digital_tick']
    physical_bits = W['logical_weights_completed']*X['state']['cells_per_weight']
    assert physical_bits % cells == 0
    batches = physical_bits//cells
    assert cells == strips*M['outputs_per_strip'] and cells <= W['binary_sense_lanes_available']
    compare_ticks = math.ceil(cells/W['compare_lanes'])
    edge = profile['bias_transition_ns']
    requested_guard = W['guard_after_final_pulse_ns'] if observation_ns is None else observation_ns
    stage = dict(bias_setup_and_interphase_return_ns=3*edge,
                 polarization_plateaus_ns=W['pulse_phases_per_batch']*W['pulse_width_ns'],
                 post_last_pulse_guard_including_return_ns=max(requested_guard,edge),
                 terminal_binary_read_ns=profile['complete_binary_read_ns'],
                 terminal_capture_ns=W['terminal_capture_ticks']*td,
                 terminal_compare_ns=compare_ticks*td)
    front, beats = API.front_ns(W['encoded_load_bits'],td,W['first_data_in_command'])
    dr = API.program_sequence_ns(front,0,[dict(count=batches,
        drive_program_ns=stage['bias_setup_and_interphase_return_ns']+stage['polarization_plateaus_ns'],
        verify_ns=stage['terminal_binary_read_ns']+stage['terminal_capture_ns']+stage['terminal_compare_ns'],
        recover_ns=stage['post_last_pulse_guard_including_return_ns'])])
    driver=X['engineering_driver_budget']
    nodes=strips*driver['driven_nodes_per_strip']
    required_current=driver['maximum_effective_capacitance_per_driven_node_fF']*driver['worst_swing_V']/edge
    return dr, dict(physical_bits=physical_bits,physical_batches=batches,data_beats=beats,
        chosen_observation_ns=requested_guard,final_return_counted_in_observation=True,
        terminal_read_begins_after_observation=True,terminal_capture_ticks=batches*W['terminal_capture_ticks'],
        cells_per_batch=cells,strips_per_batch=strips,polarity_pulse_slots=2*batches,
        verify_reads=batches,compare_ticks=compare_ticks*batches,front_ns=front,
        per_batch_stage_ns=stage,total_stage_ns={k:val*batches for k,val in stage.items()},
        complete_batch_ns=sum(stage.values()),driven_nodes=nodes,
        required_slew_current_uA_per_node=required_current,required_supply_current_mA=nodes*required_current/1000,
        installed_slew_current_uA_per_node=driver['installed_slew_current_uA_per_node'],
        installed_supply_current_mA=nodes*driver['installed_slew_current_uA_per_node']/1000)


def row_result(p, ds, dr, wc, scenario_type, **extra):
    transactions=L['n_in']*math.ceil(L['n_out']/W['logical_weights_completed'])
    # The configured output dimension has no partial word. Tail payloads require an explicit map.
    assert L['n_out'] % W['logical_weights_completed'] == 0
    br=W['logical_weights_completed']*L['b_R']
    load=API.full_load_service(L,[dict(payload_Byte=br,service_ns=dr,count=transactions)])
    interface=API.mapping_metrics(L,ds,load['T_R_ns'])
    local=API.metrics(L['B_S_Byte'],br,ds,dr)
    return dict(profile=p['profile'],mode=X['mode'],baseline_id=API.D['baseline_id'],
        scenario_type=scenario_type,feasibility='conditional_on_binary_sensing_and_terminal_verify',
        maintenance='none_in_local_service_window',resident_counts=wc,
        mapping_interface=interface,full_load=load,
        maintenance_service=dict(raw=copy.deepcopy(interface),effective=copy.deepcopy(interface),
            availability=1,feasible=True,maintenance_payload_Byte=0,refresh_ns=0,restore_ns=0),
        **local,**extra)


def recompute():
    cfg=copy.deepcopy(API.R['dcim']); cfg.update(M['r0_dcim_overrides'])
    out=[]
    for p in X['profiles']:
        v=API.C['propagation']['profile_values'][p['profile']]
        ds,counts=API.dcim_service(cfg,v,p['complete_binary_read_ns'],L)
        dr,wc=write_service(p)
        out.append(row_result(p,ds,dr,wc,
            'recommended_reference' if p['profile']=='reference' else 'paired_engineering_scenario',
            mapping_id='32_lateral_lanes_4_capacity_layers_single_tile_hold',input_parameters=p,
            common_periphery_ns=v,streaming_counts=counts,
            streaming_stages_ns=dict(binary_read=counts['read_rounds']*p['complete_binary_read_ns'],
                tile_capture=counts['capture_ticks']*v['digital_tick'],
                digital=counts['digital_ticks']*v['digital_tick'],boundary=cfg['boundary_ticks']*v['digital_tick']),
            dominant_streaming='32 complete tile reads plus 256 digital reduction rounds',
            dominant_resident='100 ns chosen observation, two polarization phases, terminal read/capture/compare'))
    ref=out[1]; p=X['profiles'][1]; contrast=X['structural_contrast']
    dr,wc=write_service(p,contrast['parallel_cells'],contrast['parallel_strips'])
    c=row_result(p,ref['delta_S_ns'],dr,wc,'resource_comparison',id=contrast['id'])
    for key,field in [('rho','rho_Byte_per_s'),('tau','tau_Byte_per_s'),('ridge','ridge')]:
        c[key+'_ratio_to_reference']=c[field]/ref[field]
    window=[]
    for guard in X['observation_sensitivity']['observation_ns']:
        dr,wc=write_service(p,observation_ns=guard)
        window.append(row_result(p,ref['delta_S_ns'],dr,wc,
            'independent_engineering_reserve_sensitivity',id=f'reference_guard{guard}',observation_ns=guard))
    manifest=json.loads((CORPUS/'source_manifest.json').read_text())
    sources={s['source_id']:s['pdf'] for s in manifest['sources'] if s['group']=='10_fenor_3d'}
    physical_cells=L['n_in']*L['n_out']*X['state']['cells_per_weight']
    native=dict(K=L['K'],N=L['N'],b_S=L['b_S'],b_R=L['b_R'],
        logical_capacity_Byte=L['resident_capacity_Byte'],effective_logical_capacity_Byte=L['resident_capacity_Byte'],
        physical_cells=physical_cells,physical_storage_bits=physical_cells,physical_capacity_Byte=physical_cells/8,
        encoding='eight binary FeFET cells per signed INT8 weight; two-complement sign in digital reduction',
        signal_enhancement_replication=1,weight_planes=8,independent_service_units=1,
        physical_organization='32 lateral row lanes x 64 local strips x (4 layers x 16 BL/SL column pairs)',
        output_container_bits=L['output_container_bits'],input_register_bits=L['input_register_bits'],
        output_register_bits=L['output_register_bits'],update_payload_Byte=ref['B_R_Byte'],
        update_shape='one input index x sixteen aligned outputs; all eight binary planes together',
        full_load_transactions=ref['full_load']['transactions'],
        resources=dict(binary_sense_nodes=M['parallel_binary_sense_nodes'],sense_bits_per_read=cfg['read_bits_per_batch'],
            adc_count=0,weight_tile_register_bits=cfg['weight_latch_bits'],weight_tile_register_banks=1,
            digital_output_lanes=cfg['output_lanes'],active_input_rows=cfg['rows_per_group'],
            partial_sum_register_bits=cfg['output_lanes']*L['output_container_bits'],
            capture_ticks_per_read=1,encoded_update_register_bits=W['encoded_load_bits'],
            write_compare_lanes=W['compare_lanes'],write_domains=W['write_domains'],
            parallel_write_cells=W['parallel_cells'],parallel_write_strips=W['parallel_strips'],
            driven_bias_nodes=X['engineering_driver_budget']['installed_nodes'],
            installed_slew_current_uA_per_node=X['engineering_driver_budget']['installed_slew_current_uA_per_node'],
            installed_supply_current_mA=X['engineering_driver_budget']['installed_supply_current_mA'],
            streaming_update_overlap=False),
        maintenance='no periodic refresh or destructive restore; local service only',
        display_conversion='average_update_ns_per_16KiB = T_R_ns * 16384 / logical_capacity_Byte')
    return dict(case_id=X['case_id'],baseline_id=API.D['baseline_id'],native_configuration=native,
        units=dict(time='ns',payload='Byte',throughput='Byte/s; divide by 1e6 for decimal MB/s',ridge='dimensionless'),
        input_sha256=sha(BASE/'data/inputs.json'),shared_parameter_sha256=sha(SHARED/'data/shared_parameters.json'),
        shared_api_sha256=sha(SHARED/'scripts/check_shared.py'),sources=sources,local_physical_cells=physical_cells,
        source_selection='FENOR-02 timing/bias; FENOR-01 digital mechanism only; FENOR-04/06 state-specific cross-checks',
        main_scenarios=out,structural_contrast=c,observation_sensitivity=window,recommended_reference_profile='reference',
        range_meaning='Paired engineering scenarios with identical installed resources and fixed 100 ns observation; no probability or all-combinations claim.',
        paired_range={key:[min(s[key] for s in out),max(s[key] for s in out)] for key in ['rho_Byte_per_s','tau_Byte_per_s','ridge']},
        full_matrix_aggregation=dict(native_logical_transactions=ref['full_load']['transactions'],
            logical_Byte=L['resident_capacity_Byte'],reference_time_ns=ref['mapping_interface']['T_R_ns'],tau_Byte_per_s=ref['tau_Byte_per_s']),
        guard_sensitivity=dict(reference_formula_ns='delta_R = 165 + observation_ns, observation_ns >= 10',
            evidence_limit='RAWD < 100 ns does not establish a shorter definite waiting bound; 150 ns is extra engineering reserve.',
            extra_guard_ns_per_batch=10,extra_transaction_ns=10,relative_ridge_change=10/ref['delta_R_ns']))


def tex_table(result):
    s=[r'% Generated by scripts/check_fenor.py --emit.',r'\begin{table}[htbp]\centering\small',
       r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
       r'情景 & $\Delta_S$ (ns) & $\Delta_R$ (ns) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    rows=[*zip(result['main_scenarios'],['乐观','典型','悲观']), (result['structural_contrast'],'16-cell 资源对照')]
    for row,label in rows:
        s.append(f"{label} & {row['delta_S_ns']:.0f} & {row['delta_R_ns']:.0f} & {row['rho_Byte_per_s']/1e6:.3g} & {row['tau_Byte_per_s']/1e6:.3g} & {row['ridge']:.3g}"+r'\\')
    s += [r'\bottomrule\end{tabular}',r'\caption{所选原生 $128\times128$ INT8 配置；主情景固定128-cell写资源、4096-bit单tile保持与100 ns观察窗口。最后一行独立减少写驱动，MB=$10^6$ Byte。}',r'\label{10_fenor_3d:tab:result}\end{table}']
    return '\n'.join(s)+'\n'


def checks(result):
    assert X['baseline_id']==API.D['baseline_id']=='shared_baseline'
    addr=set()
    for i in range(L['n_in']):
        for o in range(L['n_out']):
            for b in range(int(8*L['b_R'])):
                address=(i%M['independent_row_read_lanes'],i//M['independent_row_read_lanes'],
                    (o//M['outputs_per_strip'])*X['state']['cells_per_weight']+b,o%M['outputs_per_strip'])
                assert address not in addr; addr.add(address)
    assert len(addr)==result['local_physical_cells']
    assert M['independent_row_read_lanes']*M['strips_per_row_lane']*M['cells_per_strip']==len(addr)
    assert M['parallel_binary_sense_nodes']==M['independent_row_read_lanes']*M['outputs_per_strip']*X['state']['cells_per_weight']
    for polarity in [-1,1]:
        vw=W['full_selected_gate_channel_V']; unit=polarity*vw/3
        assert math.isclose(2*unit-(-unit),polarity*vw)
        assert math.isclose(2*unit-unit,polarity*vw/3)
        assert math.isclose(unit-(-unit),2*polarity*vw/3)
        assert math.isclose(unit-unit,0)
    # Independent stage arithmetic, not a call back into the service function.
    tiles=(L['n_in']//M['independent_row_read_lanes'])*(L['n_out']//M['outputs_per_strip'])
    digital_rounds=tiles*int(8*L['b_S'])
    for row,p in zip(result['main_scenarios'],X['profiles']):
        td=API.C['propagation']['profile_values'][p['profile']]['digital_tick']
        read=p['complete_binary_read_ns']; edge=p['bias_transition_ns']
        expected_ds=tiles*read+tiles*td+digital_rounds*td+2*td
        expected_dr=2*td+3*edge+2*W['pulse_width_ns']+max(W['guard_after_final_pulse_ns'],edge)+read+td+8*td
        assert row['delta_S_ns']==expected_ds and row['delta_R_ns']==expected_dr
        assert row['streaming_counts']['read_rounds']==tiles and row['streaming_counts']['compute_rounds']==digital_rounds
        wc=row['resident_counts']; assert wc['physical_batches']==1 and wc['physical_bits']==128
        assert wc['terminal_capture_ticks']==1 and wc['compare_ticks']==8
        assert row['delta_R_ns']==wc['front_ns']+sum(wc['total_stage_ns'].values())
        assert row['delta_S_ns']==sum(row['streaming_stages_ns'].values())
        assert wc['required_slew_current_uA_per_node']<=wc['installed_slew_current_uA_per_node']
        assert wc['required_supply_current_mA']<=wc['installed_supply_current_mA']
        mi=row['mapping_interface']; tr=expected_dr*L['n_in']*(L['n_out']//16)
        assert mi['T_R_ns']==tr
        assert math.isclose(row['rho_Byte_per_s'],L['B_S_Byte']/(expected_ds*1e-9))
        assert math.isclose(row['tau_Byte_per_s'],L['resident_capacity_Byte']/(tr*1e-9))
        assert math.isclose(mi['U_star'],L['N']*L['b_R']/L['b_S']*row['ridge'])
        assert mi['RI_star']==row['ridge']
    ref=result['main_scenarios'][1]
    td=ref['common_periphery_ns']['digital_tick']; p=X['profiles'][1]
    c=result['structural_contrast']
    assert c['delta_R_ns']==2*td+8*(3*p['bias_transition_ns']+40+100+p['complete_binary_read_ns']+2*td)
    assert c['resident_counts']['terminal_capture_ticks']==8
    assert c['resident_counts']['driven_nodes']*8==ref['resident_counts']['driven_nodes']
    assert c['rho_ratio_to_reference']==1
    for row in result['observation_sensitivity']:
        assert row['delta_R_ns']==ref['delta_R_ns']-W['guard_after_final_pulse_ns']+row['observation_ns']
        assert row['delta_S_ns']==ref['delta_S_ns']
    for source in result['sources'].values(): assert sha(CORPUS/source['path'])==source['sha256']
    assert not W['erase_block'] and not W['pre_reset']
    assert X['state']['independent_service_units']==W['write_domains']==1
    assert result['native_configuration']['output_container_bits']>=16+math.ceil(math.log2(L['K']))


def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--emit',action='store_true'); args=parser.parse_args()
    result=recompute(); checks(result)
    generated={BASE/'data/results.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n',BASE/'tex/generated_results.tex':tex_table(result)}
    if args.emit:
        for p,content in generated.items(): p.write_text(content)
    for p,content in generated.items(): assert p.read_text()==content,f'Stale generated file: {p}; run --emit explicitly'
    print('PASS: native payload/address map, single-tile hold, complete write/capture/verify, fixed driver ratings, full-load interface and source hashes')
    for r in result['main_scenarios']:
        print(f"{r['profile']}: DS={r['delta_S_ns']} ns DR={r['delta_R_ns']} ns rho={r['rho_Byte_per_s']/1e6:.7f} MB/s tau={r['tau_Byte_per_s']/1e6:.7f} MB/s RI*={r['ridge']:.7f} U*={r['mapping_interface']['U_star']:.7f}")


if __name__=='__main__': main()
