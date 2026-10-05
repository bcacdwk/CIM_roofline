#!/usr/bin/env python3
"""Reviewer recalculation from independent-run raw fields; never imports the production evaluator."""
import json, math, sys, hashlib
from pathlib import Path
root=Path(sys.argv[1]).resolve()
report={'run':str(root),'checks':[],'case_points':[],'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
def close(label,a,b):
    passed=math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-20)
    report['checks'].append({'label':label,'actual':a,'independent_expected':b,'passed':passed})
    if not passed: raise AssertionError((label,a,b))
rows=json.loads((root/'summary.json').read_text())['case_results']
assert len(rows)==9
for row in rows:
    cid,scenario=row['case_id'],row['scenario']; d=root/cid/scenario
    raw=json.loads((d/'resolved.json').read_text()); inp=json.loads((d/'input.json').read_text()); p=inp['resolved_parameters']; tag=cid+'/'+scenario
    delta=raw['delta_s'];resident=raw['resident_s'];period=raw['clock_period_s']
    close(tag+'/payloadS',row['B_S_Byte'],256);close(tag+'/payloadR',row['B_R_Byte'],256*31)
    close(tag+'/rho',row['rho_MB_per_s'],256/delta/1e6);close(tag+'/tau',row['tau_MB_per_s'],7936/resident/1e6)
    close(tag+'/RI',row['RI_star'],resident/delta/31);close(tag+'/U',row['U_star'],resident/delta)
    close(tag+'/point_temperature',row['temperature_K'],{'optimistic':300,'reference':350,'pessimistic':400}[scenario])
    assert row['paired_id']==cid+'__'+scenario and row['status'].startswith('conditional')
    close(tag+'/clock',period,p['clock_reservation_factor']*raw.get('critical_comb_s',raw.get('max_combinational_s',0)))
    if cid=='ns_sram_acim':
        expected_delta=raw['input_capture_per_pass_s']+2*(raw['native_unsigned_8bit_s']+raw['pass1_hold_capture_s'])+16*(raw['input_select_comb_s']+raw['input_select_address_capture_s'])+3*period
        expected_resident=raw['write_all_s']+raw['write_capture_all_s']+raw['write_batches']*raw['write_encode_inv_s']+raw['recovery_s']
        close(tag+'/delta_stages',delta,expected_delta);close(tag+'/resident_stages',resident,expected_resident)
        close(tag+'/ADC_per_plane',raw['adc_s'],8*10e-9)
        close(tag+'/wire_thermal',raw['wire_rho_ohm_m'],4.51e-8*(1+.00451*(p['temperature_K']-300)))
        close(tag+'/write_batches',raw['write_batches'],256)
    elif cid=='ns_sram_dcim':
        close(tag+'/delta_cycles',delta,26*period)
        analog=2*raw['write_decoder_one_edge_s']+raw['write_precharge_s']+raw['write_driver_s']+raw['write_cell_flip_s']+raw['write_encode_s']
        close(tag+'/write_analog_stages',raw['write_analog_s'],analog)
        close(tag+'/resident_stages',resident,256*(1+math.ceil(analog/period))*period)
        close(tag+'/critical_paths',raw['critical_comb_s'],max(raw[k] for k in ('native_bit_core_s','native_shiftadd_comb_s','nibble_merge_s','correction_comb_s','input_select_comb_s')))
        close(tag+'/trees',raw['native_tree_count'],64);close(tag+'/tree_rows',raw['native_tree_rows'],256);close(tag+'/tree_precision',raw['native_tree_bits'],4)
    else:
        expected_pass=sum(raw[k] for k in ('bank_unsigned_8bit_service_s','neutral_return_s','gather_one_pass_s','reduction_one_pass_s','operand_capture_per_pass_s'))
        close(tag+'/per_pass_stages',raw['global_unsigned_service_s'],expected_pass)
        close(tag+'/delta_stages',delta,raw['stream_input_capture_s']+2*expected_pass+3*period)
        resident_keys=('write_pulse_s','write_enable_s','write_release_s','write_levelshift_s','write_data_capture_s','verify_total_s','retry_control_total_s','bank_select_capture_s','bank_decode_route_s','write_data_bus_s','write_neutral_return_s')
        close(tag+'/resident_stages',resident,sum(raw[k] for k in resident_keys))
        close(tag+'/read_bus_transfer_count',raw['gather_beats_per_pass'],16*32)
        close(tag+'/write_bus_transfer_count',raw['resident_input_beats'],256*9)
        close(tag+'/physical_cells',raw['physical_cells'],16*16*288)
        close(tag+'/total_ADC',raw['adc_count'],16*32)
        close(tag+'/program_pulses',raw['write_pulses'],2*256*9*p['program_attempts'])
        close(tag+'/verify_adc_rounds',raw['verify_adc_rounds'],2*256*9*p['program_attempts'])
        close(tag+'/staging_bits',raw['staging_bits'],16*32*24)
        close(tag+'/neutral_stream',raw['neutral_stream_updates'],2*16)
        close(tag+'/neutral_resident',raw['neutral_resident_updates'],16)
        close(tag+'/area_sum',raw['area_total_m2'],sum(raw[k] for k in ('area_all_local_banks_m2','area_staging_m2','area_reduction_m2','area_correction_m2','area_bank_select_m2','area_hub_select_m2','area_all_directional_links_and_root_m2')))
        assert raw['area_total_m2']<=raw['layout_area_m2']*(1+1e-12)
        close(tag+'/staging_load',raw['staging_data_drive_cap_F'],512*raw['staging_D_pin_cap_F'])
        close(tag+'/write_local_load',raw['write_sink_drive_cap_F'],9*raw['write_data_D_pin_cap_F'])
        close(tag+'/root_load',raw['write_root_drive_cap_F'],16*raw['link_input_cap_F'])
        close(tag+'/Ron_device',raw['input_r_on_ohm'],8000)
        close(tag+'/Roff_device',raw['input_r_off_ohm'],24000)
        close(tag+'/Raccess',raw['access_resistance_ohm'],5000)
        close(tag+'/Ron_total',raw['r_on_ohm'],13000)
        close(tag+'/Roff_total',raw['r_off_ohm'],29000)
        close(tag+'/MUX_conductance_target',raw['mux_res_tg_ohm'],13000/256*.25)
        close(tag+'/physical_column_R',raw['res_col_ohm'],16*4*22e-9*raw['wire_resistance_ohm_per_m'])
        close(tag+'/read_voltage',raw['read_voltage_v'],.5)
        close(tag+'/perbank_row_buffer',raw['expected_row_buffer_bits'],16*288)
        close(tag+'/read_directional_links',raw['read_point_links'],16)
        close(tag+'/write_directional_links',raw['write_broadcast_point_branches'],16)
        close(tag+'/nominal_HRS',raw['verify_expected_HRS_code'],13)
        close(tag+'/nominal_LRS',raw['verify_expected_LRS_code'],29)
        close(tag+'/read_10bit_settle',raw['onehot_10bit_settle_diagnostic_s'],math.log(2048)*raw['onehot_col_tau_s'])
        close(tag+'/native_ADC_per_pass',raw['native_read_adc_s'],8*9*11e-9)
        close(tag+'/Q4_no_early_shift',raw['adc_baseline_right_shift'],0)
        close(tag+'/Q4_output',raw['fractional_output_bits'],4)
        close(tag+'/signed_container',raw['output_bits'],29)
        close(tag+'/wire_thermal',raw['wire_rho_ohm_m'],4.51e-8*(1+.00451*(p['temperature_K']-300)))
    report['case_points'].append({'paired_id':row['paired_id'],'delta_s':delta,'resident_s':resident,'temperature_K':p['temperature_K'],'output_bits':row['output_bits'],'fractional_bits':row['fractional_output_bits']})
report['complete']=all(x.get('passed',False) for x in report['checks'])
(Path(__file__).resolve().parent/'independent_services.json').write_text(json.dumps(report,indent=2)+'\n')
print('Independent service stage audit complete:',report['complete'])
