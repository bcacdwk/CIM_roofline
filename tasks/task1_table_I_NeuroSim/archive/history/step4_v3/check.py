#!/usr/bin/env python3
"""Causal and service-total checks on actual outputs (no target performance values)."""
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode=True

def same(a,b): return math.isclose(a,b,rel_tol=1e-11,abs_tol=1e-18)
def check(out):
    rows=json.loads((out/'summary.json').read_text())['case_results']
    facts={}
    for row in rows:
        cid=row['case_id']; d=out/cid
        m=json.loads((d/'resolved.json').read_text())
        variants=json.loads((d/'diagnostics.json').read_text())
        v={k:z['raw'] for k,z in variants.items()}
        f={
            'positive_finite_services':all(math.isfinite(row[k]) and row[k]>0 for k in ('single_latency_ns','delta_S_ns','T_R_ns','rho_MB_per_s','tau_MB_per_s')),
            'logical_payload_256_by_31_bytes':row['B_S_Byte']==256 and row['B_R_Byte']==7936,
            'balance_identity':same(row['U_star'],31*row['RI_star']),
            'explicit_nonoverlap':same(row['single_latency_ns'],row['delta_S_ns']),
            'selector_control_initialized_with_area':m['input_selector_control_bits']==5 and m['input_selector_control_area_m2']>0,
        }
        if cid=='ns_sram_acim':
            f.update({
                'read_stage_total':same(m['delta_s'],2*(m['native_unsigned_8bit_s']+m['input_capture_per_pass_s']+m['pass1_hold_capture_s'])+m['correction_s']+m['input_serialization_s']),
                'write_stage_total':same(m['resident_s'],m['write_all_s']+m['write_capture_all_s']+m['write_batches']*m['write_encode_inv_s']+m['recovery_s']),
                'full_row_overwrite':m['write_batches']==256,
                'cell_flip_positive':m['write_all_s']>m['wl_write_s']+m['precharge_write_s']+m['write_driver_s'],
            })
            if v:
                f.update({'read_activity_no_write_pollution':same(v['activity_quarter']['resident_s'],m['resident_s']),
                    'write_port_half_doubles_batches':v['write_128']['write_batches']==2*m['write_batches'],
                    'wire_resistance_consumed':same(v['wire_double']['rrow_ohm'],2*m['rrow_ohm']),
                    'access_capacitance_consumed':v['access_wider']['capcol_F']>m['capcol_F'],
                    'ADC_bits_consumed':v['adc_10bit']['adc_s']>m['adc_s'],
                    'shape_consumed':v['half_rows']['capcol_F']<m['capcol_F'],
                    'compatible_ADC_resource_change':v['half_columns']['physical_cols']==128 and v['half_columns']['logical_N']==15})
        elif cid=='ns_rram_1t1r':
            f.update({'fixed_RESET_SET_pulses':m['write_pulses']==2*256*9,
                'two_edges_per_pulse':m['write_transitions']==2*m['write_pulses'],
                'same_array_verify_rounds':m['verify_adc_rounds']==2*256*9 and m['verify_comparator_count']==64,
                'one_row_buffer':m['expected_row_buffer_bits']==288,
                'resident_port_covers_physical_cells':m['resident_input_beats']*m['resident_port_bits']==m['physical_cells'],
                'access_input_preserved':m['access_resistance_ohm']==5000,
                'read_stage_total':same(m['delta_s'],m['stream_input_capture_s']+2*(m['unsigned_8bit_service_s']+m['operand_capture_per_pass_s'])+m['input_serialization_s']+m['signed_correction_s']),
                'resident_stage_total':same(m['resident_s'],sum(m[k] for k in ['write_pulse_s','write_enable_s','write_release_s','write_levelshift_s','write_data_capture_s','verify_total_s'])),
                'verify_stage_total':same(m['verify_total_s'],512*m['verify_one_row_s']),
                'fixed_onehot_HRS_read_envelope':m['read_activity']==1/256})
            if v:
                f.update({'read_activity_no_write_pollution':same(v['activity25']['resident_s'],m['resident_s']),
                    'read_activity_consumed_in_RC':v['activity25']['native_read_other_s']!=m['native_read_other_s'],
                    'pulse_has_no_stream_effect':same(v['pulse20ns']['delta_s'],m['delta_s']),
                    'pulse_delta_equals_physical_batches':same(v['pulse20ns']['resident_s']-m['resident_s'],4608*1e-8),
                    'write_port_half_doubles_pulses':v['batch16']['write_pulses']==2*m['write_pulses'],
                    'wire_resistance_consumed':same(v['wire2x']['res_row_ohm'],2*m['res_row_ohm']),
                    'access_device_consumed':v['access6k']['access_width_f']!=m['access_width_f'] and v['access6k']['access_resistance_ohm']==6000,
                    'ADC_bits_consumed':v['adc9bit']['native_read_adc_s']<m['native_read_adc_s'],
                    'shape_consumed':v['rows128']['physical_cells']==m['physical_cells']/2})
        else:
            f.update({'native_fixed_bit_array':m['physical_rows']==256 and m['physical_cols']==256,
                'native_tree_organization':m['native_tree_count']==64 and m['native_tree_bits']==4 and m['native_tree_rows']==256,
                'native_8bit_pipeline':m['native_unsigned_cycles']==9,
                'native_DFF_cycle_unit':m['dff_capture_return_cycles']==1,
                'direct_operand_capture':m['merge_direct_operand_capture']==1,
                '26cycle_streaming':same(m['delta_s'],26*m['clock_period_s']),
                'full_cover_write':m['write_beats']*m['write_port_bits']==65536,
                'clock_aligned_write':same(m['resident_s'],m['write_beats']*(1+math.ceil(m['write_analog_s']/m['clock_period_s']))*m['clock_period_s'])})
            if v:
                f.update({'read_activity_no_write_pollution':same(v['activity1']['resident_s'],m['resident_s']),
                    'write_groups_half_double_beats':v['write_groups2']['write_beats']==2*m['write_beats'],
                    'write_groups_half_double_resident':same(v['write_groups2']['resident_s'],2*m['resident_s']),
                    'wire_consumed':v['wire125']['native_wl_s']!=m['native_wl_s'],
                    'access_consumed':v['access125']['write_cap_col_f']!=m['write_cap_col_f'],
                    'diagnostics_preserve_fixed_native_size':all(z['physical_rows']==256 and z['physical_cols']==256 for z in v.values())})
        facts[cid]=f
    result={'status':'PASS' if all(all(f.values()) for f in facts.values()) else 'FAIL','checks':facts,
            'scope':'Causal/operation/service arithmetic checks; not analog precision or silicon validation.'}
    (out/'checks.json').write_text(json.dumps(result,indent=2)+'\n')
    if result['status']!='PASS': raise AssertionError(result)
    return result

if __name__=='__main__':
    print(check(Path(sys.argv[1]))['status'])
