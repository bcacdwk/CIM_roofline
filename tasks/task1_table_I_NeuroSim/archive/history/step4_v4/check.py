#!/usr/bin/env python3
"""Causal input, resource, state and service checks; no target throughput values."""
import json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True

def close(a,b):return math.isclose(a,b,rel_tol=2e-10,abs_tol=1e-18)
def check(out):
    rows=json.loads((out/'summary.json').read_text())['case_results'];checks={};snap={}
    for r in rows:
        cid,sc=r['case_id'],r['scenario'];path=out/cid/sc;d=json.loads((path/'resolved.json').read_text());inp=json.loads((path/'input.json').read_text());p=inp['resolved_parameters'];snap[(cid,sc)]=d
        f={'logical_payload':r['K']==256 and r['N']==31 and r['B_S_Byte']==256 and r['B_R_Byte']==7936,'balanced_metrics':close(r['U_star'],31*r['RI_star']),'nonoverlap_declared':close(r['single_latency_ns'],r['delta_S_ns']),'temperature_consumed':d.get('temperature_K',d.get('temperature_k'))==p['temperature_K'],'clock_policy':p['clock_reservation_factor']==2,'finite_positive':all(math.isfinite(r[k]) and r[k]>0 for k in ('delta_S_ns','T_R_ns','rho_MB_per_s','tau_MB_per_s')),'actual_field_consumption':all(v['matches'] for v in json.loads((path/'consumption.json').read_text()).values())}
        if cid=='ns_sram_acim':
            f.update({'one_accepted_input_held':d['input_acceptances']==1,'native_resources':d['resolved_adc_count']==32 and d['resolved_adc_levels']==512 and d['write_port_bits']==256,
              'stream_stages':close(d['delta_s'],d['input_capture_per_pass_s']+2*(d['native_unsigned_8bit_s']+d['pass1_hold_capture_s'])+d['correction_s']+d['input_serialization_s']),
              'resident_stages':close(d['resident_s'],d['write_all_s']+d['write_capture_all_s']+d['write_batches']*d['write_encode_inv_s']+d['recovery_s']),
              'complete_matrix_overwrite':d['write_batches']==256,'clock_qualification':close(d['clock_period_s'],2*d['critical_comb_s']),
              'sized_mux_with_load':d['mux_driver_scale']==110 and d['mux_driver_input_F']>0 and d['mux_select_wire_R_ohm']>0 and d['mux_select_fanout']==32})
        elif cid=='ns_sram_dcim':
            f.update({'native_fixed_array':d['physical_rows']==256 and d['physical_cols']==256 and d['native_tree_count']==64 and d['native_tree_bits']==4,
             'paid_full_sign_pass':d['native_unsigned_cycles']==9 and d['all8slots_second_pass_retained']==1,
             'direct_operand_state':d['merge_direct_operand_capture']==1 and d['a_bank_hold_during_b_pass']==1,
             'stream26':close(d['delta_s'],26*d['clock_period_s']),'resident512':close(d['resident_s'],512*d['clock_period_s']),
             'write_quantization':d['write_beats']==256 and d['write_busy_cycles']==math.ceil(d['write_analog_s']/d['clock_period_s']),
             'physical_and_policy_separate':close(d['clock_period_s'],2*d['critical_comb_s']) and d['clock_reserved_s']>0,
             'NOR_load_and_polarity':d['input_polarity_inv_s']>0 and d['write_cell_node_cap_f']>d['native_product_NOR_input_cap_f']})
        else:
            f.update({'banked_physical_mapping':d['banks']==16 and d['bank_rows']==16 and d['physical_cells']==73728,
             'fixed_resources':d['adc_count']==512 and d['verify_comparator_count']==1024 and d['resident_port_bits']==32,
             'Q4_container':d['output_fractional_bits']==4 and d['correction_bits']==29 and d['bank_held_unsigned_max']<2**24 and d['global_unsigned_max']<2**28,
             'actual_gain':close(d['nominal_adc_gain_codes_per_A'],16/(p['read_voltage_V']*(1/d['r_on_ohm']-1/d['r_off_ohm']))),
             'target_codes_rederived':d['verify_expected_LRS_code']-d['verify_expected_HRS_code']==16,
             'full_matrix_count':d['write_pulses']==4608 and d['verify_rows']==512 and d['resident_input_beats']==2304,
             'bounded_verify':d['program_attempt_limit']==2 and d['program_attempts']==1 and d['verify_sticky_lane_bits']==32,
             'no_indefinite_read_hold':d['neutral_stream_updates']==32 and d['neutral_resident_updates']==16 and d['neutral_return_s']>0,
             'staging_lifetime_resources':d['gather_beats_per_pass']==512 and d['staging_bits']==12288 and d['global_reduction_levels']==4,
             'directional_links':d['bus_direction_count']==2 and d['read_point_links']==16 and d['write_broadcast_point_branches']==16,
             'data_pin_fanout_not_clock_enable':d['staging_data_loads_per_bit']==512 and close(d['staging_data_drive_cap_F'],512*d['staging_D_pin_cap_F']) and d['write_data_total_loads_per_port_bit']==144,
             'native_terminal_load_budget':d['hub_mux_channel_input_cap_F']<=d['link_terminal_load_budget_F'],
             'ADC_settling':close(d['onehot_10bit_settle_diagnostic_s'],math.log(2048)*d['onehot_col_tau_s']),
             'stream_stages':close(d['delta_s'],d['stream_input_capture_s']+2*(d['bank_unsigned_8bit_service_s']+d['neutral_return_s']+d['gather_one_pass_s']+d['reduction_one_pass_s']+d['operand_capture_per_pass_s'])+d['signed_correction_s']),
             'resident_stages':close(d['resident_s'],sum(d[k] for k in ['write_pulse_s','write_enable_s','write_release_s','write_levelshift_s','write_data_capture_s','verify_total_s','retry_control_total_s','bank_select_capture_s','bank_decode_route_s','write_data_bus_s','write_neutral_return_s'])),
             'actual_area_containment':close(d['area_total_m2'],sum(d[k] for k in ['area_all_local_banks_m2','area_staging_m2','area_reduction_m2','area_correction_m2','area_bank_select_m2','area_hub_select_m2','area_all_directional_links_and_root_m2'])) and d['area_total_m2']<=d['layout_area_m2']*(1+1e-10),
             'near_square_rule':close(d['layout_width_m'],d['layout_height_m']),'clock_qualification':close(d['clock_period_s'],2*d['max_combinational_s'])})
        checks[r['paired_id']]=f
    thermals={}
    for cid in set(r['case_id'] for r in rows):
        if all((cid,s) in snap for s in ('optimistic','reference','pessimistic')):
            a,b,c=[snap[(cid,s)] for s in ('optimistic','reference','pessimistic')]
            field='metal0_ohm_per_m' if cid=='ns_sram_dcim' else 'wire_resistance_ohm_per_m'
            thermals[cid]={'actual_wire_temperature50K':close(b[field]/a[field],1.2255),'actual_wire_temperature100K':close(c[field]/a[field],1.451)}
            if cid=='ns_sram_dcim':thermals[cid]['RI_U_clock_cancel']=all(close(x['resident_s']/x['delta_s'],512/26) for x in (a,b,c))
    diagnostics={}
    for r in json.loads((out/'diagnostics.json').read_text())['case_results']:
        cid=r['case_id'];d=json.loads((out/cid/r['scenario']/'resolved.json').read_text());ref=snap.get((cid,'reference'))
        if ref is None:continue
        f={}
        if r['scenario']=='diagnostic_driver55':f={'driver_input_cap_changed':d['mux_driver_input_F']<ref['mux_driver_input_F'],'not_a_main_corner':True}
        elif r['scenario'] in ('diagnostic_wire2','diagnostic_wire125'):
            key='metal0_ohm_per_m' if cid=='ns_sram_dcim' else 'wire_resistance_ohm_per_m';factor=1.25 if cid=='ns_sram_dcim' else 2
            f={'real_wire_consumption':close(d[key],factor*ref[key])}
        elif r['scenario']=='diagnostic_pulse20ns':f={'pulse_only_resident':close(d['delta_s'],ref['delta_s']),'exact_parallel_pulse_delta':close(d['resident_s']-ref['resident_s'],4608*1e-8)}
        elif r['scenario']=='diagnostic_attempt2':f={'same_hardware_demand':d['program_attempt_limit']==2,'pulses_double':d['write_pulses']==2*ref['write_pulses'],'verify_double':d['verify_adc_rounds']==2*ref['verify_adc_rounds'],'row_capture_not_repeated':close(d['write_data_capture_s'],ref['write_data_capture_s'])}
        elif r['scenario']=='diagnostic_activity50':f={'resident_not_polluted':close(d['resident_s'],ref['resident_s']),'read_RC_changed':d['native_read_other_s']!=ref['native_read_other_s']}
        diagnostics[r['paired_id']]=f
    valid=all(all(f.values()) for groups in (checks,thermals,diagnostics) for f in groups.values())
    report={'status':'PASS' if valid else 'FAIL','qualification':'Checks of declared inputs, resource/state bookkeeping, source return units and causal effects; not a physical accuracy percentage.','service':checks,'thermal_input_chain':thermals,'separate_diagnostics':diagnostics}
    (out/'checks.json').write_text(json.dumps(report,indent=2)+'\n')
    if not valid:raise AssertionError(report)
    print(report['status'])
if __name__=='__main__':check(Path(sys.argv[1]))
