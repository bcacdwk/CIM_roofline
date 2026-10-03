#!/usr/bin/env python3
"""Independent stage/geometry review, with production-path perturbation probes.

Expected services are reconstructed from input geometry, resources and stage
budgets, never from unified exports or an old table of expected result values.
Production functions supply observations only; expected values and derivatives
come from this separate stage ledger. The JSON binds the exact reviewed files.
"""
import argparse
import copy
import csv
import hashlib
import importlib.util
import json
import math
import re
import sys
from fractions import Fraction
from pathlib import Path
sys.dont_write_bytecode = True

A = Path(__file__).resolve().parents[1]
T = A.parent
CASES = ['01_sram_acim','02_sram_dcim','03_nor_2d','04_nand_3d',
         '05_rram','06_mram','07_pcm','08_feram_hfo2','09_gain_cell_edram','10_fenor_3d']
PROFILES = ['short','reference','long']
FORMULAE = {
 '01_sram_acim':'DS=8 ceil(N/16)(F+TA+2TD)+2TD; TR=(KN/16)*complete_write_cycle',
 '02_sram_dcim':'DS=8 ceil(K/16)ceil(N/16)*complete_MAC_cycle+2TD; TR=(KN/16)*complete_write_cycle',
 '03_nor_2d':'tiles=ceil(K/32)ceil(N/16); DS=tiles*(read+TD+8TD)+2TD; TR=pages*(P+(page_bits/128+2)TD)+sectors*(E+2TD)',
 '04_nand_3d':'DS=output_WL*tWL+rounds*(tBL+tSL+TA+3TD)+(ceil(K/16)+2ceil(N/16)+2)TD; TR=physical_pages*(P+(page_bits/128+2)TD)+blocks*E+N*8*ceil(K/128)TD+C',
 '05_rram':'DS=8ceil(K/32)ceil(N/16)*(TI+front+TA+2TD)+2TD; TR=rail_entry+rail_exit+(KN/16)*[front_control+sum_polarities attempts*(pulse+local_setup+local_return+TI+verify_front+TB+2TD)]',
 '06_mram':'tiles=ceil(K/32)ceil(N/16); DS=tiles*(read+TD+8TD)+2TD; TR=(KN/8)*[2TD+2write+TD+2(read+TD+TD)]',
 '07_pcm':'DS=8ceil(K/8)ceil(N/16)*(F+TA+2TD)+2TD; TR=(KN/32)*[3TD+8*(TD+3g+RESET+SET+2(F+TA+TD))]',
 '08_feram_hfo2':'tiles=ceil(K/32)ceil(N/16); DS=tiles*(sense+one_restore+open_close+8TD)+2TD; TR=(KN/16)*(2TD+2polarization+open_close)',
 '09_gain_cell_edram':'DSraw=8ceil(K/64)ceil(N/16)*(TI+read+TA+2TD)+2TD; TRraw=(KN/16)*(3TD+two_step_write); Frefresh=(KN/16)*(TI+read+TA+TD+3TD+two_step_write); alpha=(period-Frefresh-max(read_group,write_group))/period; DSeff=DSraw/alpha; TReff=TRraw/alpha',
 '10_fenor_3d':'tiles=ceil(K/32)ceil(N/16); DS=tiles*(read+TD+8TD)+2TD; TR=(KN/16)*[2TD+3transition+2plateau+observation_including_return+read+TD+8TD]'
}

def read(p):
    return json.loads(p.read_text())

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def close(a,b,label):
    assert math.isfinite(a) and math.isfinite(b) and math.isclose(a,b,rel_tol=2e-11,abs_tol=1e-9), (label,a,b)

def ceildiv(a,b):
    return math.ceil(a/b)

def input_provenance_checks(case,d):
    """Validate existing provenance declarations against actual files.

    A calculator may read the current shared API while stale input metadata
    still claims a previous one. Both identities must agree; no timing value
    or expected model answer is changed to satisfy this check.
    """
    shared=A/'shared_baseline';checks=[]
    def check(field,path,declared):
        actual=sha(path)
        assert declared==actual,(case,'stale declared provenance',field,str(path.relative_to(T)),declared,actual)
        checks.append({'field':field,'path':str(path.relative_to(T)),'sha256':actual})
    for name in ['baseline_files','baseline_hashes']:
        for path,declared in d.get(name,{}).items():check(name+'.'+path,shared/path,declared)
    for field,path in {'json_sha256':'data/shared_parameters.json','script_sha256':'scripts/check_shared.py',
                       'method_tex_sha256':'tex/02_estimation_method.tex'}.items():
        if field in d.get('baseline',{}):check('baseline.'+field,shared/path,d['baseline'][field])
    for field,path in {'shared_json_sha256':'data/shared_parameters.json','shared_api_sha256':'scripts/check_shared.py'}.items():
        if field in d.get('provenance',{}):check('provenance.'+field,shared/path,d['provenance'][field])
    if 'source_manifest_sha256' in d:check('source_manifest_sha256',T/'source_manifest.json',d['source_manifest_sha256'])
    return checks

def local_front(bits,td,first=True):
    # Command+completion: two ticks. First data beat may share command.
    return (2+max(0,ceildiv(bits,128)-int(first)))*td

def dimensions(d):
    l=d.get('logical_configuration',d.get('native_configuration',{}))
    if 'K' in l:
        return l['K'],l['N'],l.get('b_S',1),l.get('b_R',1)
    m=d.get('mapping',{})
    if 'K' in m:
        return m['K'],m['N'],m.get('b_S',1),m.get('b_R',1)
    c=d.get('configuration',{})
    return c['logical_K'],c['logical_N'],1,1

def stage_expectation(case,d,profile,p):
    """Return raw full-vector/full-load service and independent stage ledger."""
    K,N,bs,br=dimensions(d)
    ti,ta,td=(p[k] for k in ['input_step','adc_batch','digital_tick'])
    cap=K*N*br
    alpha=1
    extra={}
    if case=='01_sram_acim':
        q=next(x for x in d['scenarios'] if x['id']==profile)
        r=d['native_configuration']['resources']; rounds=8*ceildiv(N,r['digital_lanes'])
        S={'front':rounds*q['frontend_complete_ns'],'ADC':rounds*ta,
           'reconstruction':rounds*r['digital_ticks_per_batch']*td,'boundaries':2*td}
        tx=cap/d['update_geometry']['logical_weights_completed']
        R={'complete_synchronous_writes':tx*q['complete_memory_cycle_ns']}
        assert r['write_drivers']==d['update_geometry']['parallel_cells']
        extra={'vector_rounds':rounds,'full_load_transactions':tx,'physical_cells':K*N*8}
    elif case=='02_sram_dcim':
        q=next(x for x in d['scenarios'] if x['id']==profile)
        r=d['native_configuration']['resources']
        rounds=8*ceildiv(K,r['digital_terms_per_round'])*ceildiv(N,r['digital_lanes'])
        S={'complete_MAC_rounds':rounds*q['complete_compute_round_ns'],'boundaries':2*td}
        tx=cap/d['update_geometry']['logical_weights_completed']
        R={'complete_synchronous_writes':tx*q['complete_memory_cycle_ns']}
        assert r['added_operand_hold_bits']==0 and d['dcim_overrides']['hold_source']=='static_connection'
        extra={'complete_MAC_rounds':rounds,'row_groups':ceildiv(K,r['digital_terms_per_round']),
               'full_load_transactions':tx,'physical_cells':K*N*8}
    elif case=='03_nor_2d':
        q=next(x for x in d['scenarios'] if x['profile']==profile)
        m=d['mapping'];v=d['stream_configuration_overrides']
        tiles=ceildiv(K,v['rows_per_group'])*ceildiv(N,v['output_lanes'])
        S={'binary_sense':tiles*q['read_full_ns'],'new_tile_capture':tiles*td,
           'digital_reduction':tiles*8*td,'boundaries':2*td}
        pages=ceildiv(cap,m['page_Byte']);sectors=ceildiv(cap,m['sector_Byte'])
        R={'page_program':pages*q['page_program_ms']*1e6,
           'sector_erase':sectors*q['sector_erase_ms']*1e6,
           'page_load_control':pages*(ceildiv(m['page_Byte']*8,128)+2)*td,
           'erase_control':sectors*2*td}
        assert pages*m['page_Byte']==cap==sectors*m['sector_Byte']
        assert m['read_slices']*m['sense_amplifiers_per_slice']==v['weight_latch_bits']
        extra={'tile_reads':tiles,'full_pages':pages,'full_sectors':sectors,
               'single_tile_hold_bits':v['weight_latch_bits'],'physical_cells':K*N*8}
    elif case=='04_nand_3d':
        m=d['mapping'];v=d['design_choices'];e=d['reported_numeric'];cal=v['calibration']
        groups=ceildiv(K,m['rows_per_group']);digits=ceildiv(bs*8,m['input_bits_per_slice'])
        wl=ceildiv(N,m['outputs_per_wl_group']);rounds=groups*digits*wl
        sl=v['sl_setup_budget_ns_by_profile'][profile]
        input_ticks=ceildiv(K,v['input_sum_lanes'])
        signed_ticks=ceildiv(N,m['outputs_per_wl_group'])*v['output_correction_ticks_per_group']
        S={'WL_setup':wl*e['wl_setup_ns'],'BL_formation':rounds*e['bl_setup_ns'],
           'SL_establishment':rounds*sl,'ADC':rounds*ta,
           'affine_merge_accumulate':rounds*v['digital_ticks_per_reconstruction_round']*td,
           'input_offset_sum':input_ticks*td,'final_signed_correction':signed_ticks*td,'boundaries':2*td}
        blocks=m['blocks_per_subarray']*m['subarrays'];pages=blocks*m['wordlines_per_block']*m['ssl_per_block']
        metadata_ticks=N*8*ceildiv(K,v['metadata_popcount_width'])
        channels=blocks*cal['row_groups'];cal_rounds=cal['row_groups']*cal['samples_per_group']
        cal_ticks=ceildiv(channels,cal['arithmetic_lanes'])*(cal['division_ticks']+cal['other_ticks_per_channel_batch'])+cal['boundary_ticks']
        C=cal['wordline_setups']*e['wl_setup_ns']+cal_rounds*(e['bl_setup_ns']+sl+ta)+cal_ticks*td
        R={'page_program':pages*v['program_full_budget_us_by_profile'][profile]*1000,
           'block_erase':blocks*v['erase_full_budget_ms_by_profile'][profile]*1e6,
           'encoded_page_load_control':pages*(ceildiv(m['bitlines_per_page'],128)+2)*td,
           'canonical_weight_sum_metadata':metadata_ticks*td,'finite_calibration':C}
        physical=pages*m['bitlines_per_page'];data=blocks*m['data_wl_per_block']*m['ssl_per_block']*m['bitlines_per_page']
        assert data==K*N*m['weight_digit_groups']*m['input_copies']*m['weight_cells_per_digit']
        assert m['data_wl_per_block']+m['calibration_wl_per_block']==m['wordlines_per_block']
        dense=m['rows_per_group']*m['input_copies']*m['weight_cells_per_digit']*e['cell_on_current_nA']/1000
        assert dense<v['current_sense_full_scale_uA'] and groups*dense>v['current_sense_full_scale_uA']
        assert v['added_feedback_capacitance_pF']==0
        extra={'row_groups':groups,'analog_rounds':rounds,'physical_pages':pages,'blocks':blocks,
               'physical_cells':physical,'data_cells':data,'reference_cells':physical-data,
               'logical_fraction_of_physical_bits':cap*8/physical,'dense_current_uA':dense,
               'calibration_rounds':cal_rounds,'calibration_ticks':cal_ticks,
               'metadata_generation_ticks':metadata_ticks,'intermediate_signed_bits_required':1+math.ceil(math.log2(K*255**2+1))}
    elif case=='05_rram':
        c=d['configuration'];v=d['adopted_inputs'];w=c['write_resources']
        rounds=8*ceildiv(K,c['native_subarray_input_terms'])*ceildiv(N,16)
        S={'input':rounds*ti,'media_front':rounds*(v['front_end_settle_ns']['value']+v['additional_frontend_ns']['value']),
           'ADC':rounds*ta,'reconstruction':rounds*2*td,'boundaries':2*td}
        tx=ceildiv(cap,c['logical_weights_per_update'])
        batches=ceildiv(c['logical_weights_per_update']*c['cells_per_weight'],c['parallel_program_cells'])
        attempts=v['group_attempt_scenarios'][profile]
        R={'rail_entry_once':v['rail_lifecycle_ns']['setup'],'rail_exit_once':v['rail_lifecycle_ns']['exit'],
           'encoded_load_control':tx*local_front(c['encoded_load_bits'],td,c['first_data_in_command'])}
        for phase in ['RESET','SET']:
            count=tx*batches*attempts[phase]
            R[phase+'_pulse']=count*v['program_pulse_ns'][phase]
            R[phase+'_local_bias_setup']=count*v['high_voltage_setup_ns_per_attempt']['by_profile'][profile]
            R[phase+'_local_isolate_return']=count*v['high_voltage_return_recover_ns_per_attempt']['by_profile'][profile]
            # The endpoint comparator is provisioned to the same common slot
            # policy as the ADC, despite being a distinct physical read mode.
            R[phase+'_binary_verify']=count*(ti+v['binary_verify_frontend_ns']['value']+ta)
            R[phase+'_address_and_done']=count*(v['address_and_pulse_control_ticks_per_attempt']['value']+v['verify_group_done_commit_ticks_per_attempt']['value'])*td
        voltage=w['voltage_rated_program_IO_required_V'];static_uA=voltage/v['binary_windows']['LRS_resistance_kOhm'][0]*1000
        headroom=w['current_compliance_uA_per_lane']-static_uA
        assert headroom>0
        min_edge_ns=w['local_switch_load_limit_pF_per_lane']*voltage/headroom*1000
        assert min_edge_ns<=v['high_voltage_setup_ns_per_attempt']['by_profile'][profile]
        close(w['peak_array_current_budget_mA'],w['high_voltage_program_lanes']*w['current_compliance_uA_per_lane']/1000,'RRAM supply provision')
        assert w['binary_comparators_total']==2*w['high_voltage_program_lanes']
        assert c['physical_data_cells']==K*N*c['cells_per_weight']
        assert c['physical_subarrays']*c['native_subarray_input_terms']*c['native_subarray_output_positions']==K*N*c['cells_per_weight']
        extra={'analog_rounds':rounds,'full_load_transactions':tx,'write_batches_per_transaction':batches,
               'attempts_per_batch':attempts,'rail_entry_exit_times_per_full_load':1,
               'physical_cells':c['physical_data_cells'],'write_lanes':w['high_voltage_program_lanes'],
               'static_load_uA_per_lane':static_uA,'minimum_charge_edge_ns':min_edge_ns,
               'isolated_transaction_requires_extra_rail_lifecycle':True}
    elif case=='06_mram':
        q=next(x for x in d['scenarios'] if x['profile']==profile);m=d['mapping'];v=d['stream_configuration_overrides']
        tiles=ceildiv(K,v['rows_per_group'])*ceildiv(N,v['output_lanes'])
        S={'binary_digitization':tiles*q['read_response_ns'],'new_tile_capture':tiles*td,
           'digital_reduction':tiles*8*td,'boundaries':2*td}
        tx=cap/m['logical_weights_per_write_group']
        R={'encoded_load_control':tx*local_front(m['encoded_load_bits'],td,m['first_data_in_command']),
           'two_direction_writes':tx*2*q['write_access_slot_ns'],
           'direction_change':tx*m['polarity_switch_ticks']*td,
           'both_branch_sense':tx*m['verify_branch_batches']*q['read_response_ns'],
           'verify_capture':tx*m['verify_branch_batches']*m['verify_capture_ticks_per_batch']*td,
           'verify_compare':tx*m['verify_branch_batches']*m['compare_ticks_per_verify_batch']*td}
        assert K*N*8==m['banks']*m['rows_per_bank']*m['weight_bits_per_bank_row']
        assert m['physical_direction_driver_lanes']==m['first_phase_active_MTJs']
        assert m['selected_pairs_per_write_group']*2==m['first_phase_active_MTJs']
        assert m['verify_branch_batches']*m['verify_single_ended_sense_lanes']==m['encoded_load_bits']
        extra={'tile_reads':tiles,'digital_rounds':tiles*8,'full_load_transactions':tx,
               'physical_MTJs':K*N*8*m['MTJs_per_weight_bit'],
               'new_weight_latch_bits':m['digital_weight_hold_bits'],'new_AND_gates':m['new_digital_AND_gates']}
    elif case=='07_pcm':
        q=d['profiles'][profile];m=d['mapping'];w=d['program']
        rounds=8*ceildiv(K,m['rows_per_group'])*ceildiv(N,16)
        S={'complete_read_front':rounds*q['read_front_including_TI_ns'],'ADC':rounds*ta,
           'voltage_decode_reconstruction':rounds*2*td,'boundaries':2*td}
        tx=ceildiv(cap,m['logical_weights_per_transaction'])
        planes=ceildiv(m['physical_cells_per_weight'],m['write_planes_parallel'])
        physical_batches=tx*planes
        verify_passes=ceildiv(m['writeheads'],16)
        R={'encoded_load_control':tx*local_front(m['logical_weights_per_transaction']*8,td),
           'write_selection':physical_batches*td,
           'driver_establish_quench_return':physical_batches*3*q['drive_transition_ns'],
           'RESET':physical_batches*w['reset_attempts']*w['reset_pulse_ns'],
           'SET_including_tail':physical_batches*w['set_attempts']*w['set_total_budget_ns'],
           'repeated_complete_verify_front':physical_batches*verify_passes*q['read_front_including_TI_ns'],
           'verify_ADC':physical_batches*verify_passes*ta,
           'verify_endpoint_compare':physical_batches*verify_passes*td}
        assert w['set_total_budget_ns']==w['set_flat_ns']+w['set_trailing_ns']
        assert m['native_bank_rows']*m['native_bank_columns']*m['physical_banks']==K*N*m['physical_cells_per_weight']
        assert m['writeheads']==m['logical_weights_per_transaction']
        extra={'analog_rounds':rounds,'active_rows':m['rows_per_group'],'full_load_transactions':tx,
               'serial_weight_planes':planes,'physical_write_batches':physical_batches,
               'fresh_verify_reads_per_plane':verify_passes,'physical_cells':K*N*m['physical_cells_per_weight'],
               'simultaneous_RESET_current_mA':m['writeheads']*w['reset_current_uA']/1000,
               'simultaneous_SET_current_mA':m['writeheads']*w['set_current_uA']/1000}
    elif case=='08_feram_hfo2':
        q=d['paired_media_budgets_ns'][profile];m=d['mapping']
        tiles=ceildiv(K,m['digital_active_rows'])*ceildiv(N,m['digital_output_lanes'])
        S={'sense':tiles*q['sense'],'destructive_restore':tiles*q['polarization_hold_per_phase'],
           'bias_precharge_return':tiles*q['open_close_bias_total'],'digital_reduction':tiles*8*td,'boundaries':2*td}
        tx=ceildiv(cap*8,m['local_row_bits'])
        R={'encoded_load_control':tx*local_front(m['local_row_bits'],td),
           'two_target_polarities':tx*m['write_target_phases']*q['polarization_hold_per_phase'],
           'bias_precharge_return':tx*q['open_close_bias_total']}
        assert m['shards']*m['rows_per_shard']*m['local_row_bits']==K*N*8
        assert tiles*m['read_active_rows']*m['local_row_bits']==K*N*8
        assert m['D0_round_readout_register_bits']==4096 and m['additional_weight_latch_bits']==0
        drive=d['drive_resources'];demand=drive['BL_capacitance_fF']*drive['memory_voltage_V']/drive['edge_each_ns'][profile]
        assert demand<=drive['BL_installed_rating_uA']
        extra={'tile_reads':tiles,'restore_bits_per_vector':K*N*8,'full_load_transactions':tx,
               'physical_data_cells':K*N*8,'reference_capacitors':m['reference_capacitors'],
               'BL_edge_demand_uA':demand,'restore_BL_edge_demand_mA':demand*drive['restore_BL_drivers']/1000}
    elif case=='09_gain_cell_edram':
        q=next(x for x in d['profiles'] if x['id']==profile);m=d['mapping'];w=d['write'];f=d['refresh']
        rounds=8*ceildiv(K,m['rows_per_group'])*ceildiv(N,m['evaluation_output_width'])
        sp=d['service_parameters'];mode=d['service_modes']['fixed_slot']
        assert mode['service_bindings']['normal_evaluation']['integration_reservation_ns']=='read_slot_reservation_ns'
        assert mode['service_bindings']['refresh_read']['integration_reservation_ns']=='read_slot_reservation_ns'
        front=ti+sp['profile_common_overhead_ns'][profile]+sp['read_slot_reservation_ns']+ta
        S={'input_front_ADC':rounds*front,'digital_reconstruction':rounds*2*td,'boundaries':2*td}
        tx=ceildiv(cap,w['logical_weights_completed']);wf=local_front(w['encoded_load_bits'],td,w['first_data_in_command'])
        R={'encoded_load_control':tx*wf,'complete_two_step_program':tx*q['program_complete_ns']}
        refresh=tx*(front+f['decode_ticks']*td+wf+q['program_complete_ns'])
        guard=max(front+2*td,wf+q['program_complete_ns'])
        alpha=(f['period_ns']-refresh-guard)/f['period_ns']
        assert alpha>0 and q['program_complete_ns']==q['program_coarse_ns']+q['program_fine_ns']
        assert m['physical_cells']==K*N*m['cells_per_weight']
        assert d['native_configuration']['resources']['full_matrix_shadow_bits']==0
        assert f['single_pair_pulse_ns']<=q['dedicated_read_ns']
        extra={'analog_rounds':rounds,'full_load_transactions':tx,'refresh_groups':tx,
               'refresh_busy_ns':refresh,'refresh_guard_ns':guard,'availability':alpha,
               'refresh_period_ns':f['period_ns'],'refresh_payload_Byte':0,
               'physical_cells':m['physical_cells'],'sign_decode_lanes':w['pair_drivers']}
    elif case=='10_fenor_3d':
        q=next(x for x in d['profiles'] if x['profile']==profile);m=d['mapping'];w=d['resident'];v=m['r0_dcim_overrides']
        tiles=ceildiv(K,v['rows_per_group'])*ceildiv(N,v['output_lanes'])
        S={'binary_sense':tiles*q['complete_binary_read_ns'],'new_tile_capture':tiles*td,
           'digital_reduction':tiles*8*td,'boundaries':2*td}
        tx=cap/w['logical_weights_completed'];batches=ceildiv(w['encoded_load_bits'],w['parallel_cells'])
        R={'encoded_load_control':tx*local_front(w['encoded_load_bits'],td,w['first_data_in_command']),
           'initial_interphase_transitions':tx*batches*3*q['bias_transition_ns'],
           'two_polarization_plateaus':tx*batches*w['pulse_phases_per_batch']*w['pulse_width_ns'],
           'observation_including_final_return':tx*batches*w['guard_after_final_pulse_ns'],
           'terminal_sense':tx*batches*q['complete_binary_read_ns'],
           'terminal_capture':tx*batches*w['terminal_capture_ticks']*td,
           'terminal_compare':tx*ceildiv(w['encoded_load_bits'],w['compare_lanes'])*td}
        drv=d['engineering_driver_budget'];demand=drv['maximum_effective_capacitance_per_driven_node_fF']*drv['worst_swing_V']/q['bias_transition_ns']
        assert demand<=drv['installed_slew_current_uA_per_node']
        assert demand*drv['installed_nodes']/1000<=drv['installed_supply_current_mA']
        assert m['independent_row_read_lanes']*m['strips_per_row_lane']*m['cells_per_strip']==K*N*8
        extra={'tile_reads':tiles,'full_load_transactions':tx,'write_batches_per_transaction':batches,
               'physical_cells':K*N*8,'bias_node_demand_uA':demand,
               'fixed_installed_bias_nodes':drv['installed_nodes']}
    else:
        raise NotImplementedError(case)
    return K,N,bs,br,S,R,alpha,extra

def scenario_rows(r):
    for key in ['main_scenarios','paired','paired_scenarios','scenarios']:
        if key in r:return r[key]
    raise KeyError('main scenario array')

def scenario_profile(x):
    p=x.get('profile',x.get('common_profile',x.get('id','')))
    if isinstance(p,dict):p=x['id']
    for name in PROFILES:
        if p==name or str(p).endswith('_'+name):return name
    raise ValueError(('unknown profile',p))

SOURCE_INSPECTIONS = {
 '01_sram_acim':[('SACIM-03',[2,5],'128 rows, 9T1C/HCA architecture and full 100MHz operation; SAR adaptation remains engineering'),('CMOS-07',[2,9],'complete synchronous SRAM write-cycle anchor, not read access')],
 '02_sram_dcim':[('SDCIM-01',[1],'128x128 bit physical macro = K128N16 INT8; 16 HCA/BFA and 64 clocks')],
 '03_nor_2d':[('NOR-02',[66],'full tPP 0.4/3ms and 4KiB tSE45/400ms')],
 '04_nand_3d':[('NAND-04',[3],'native 13824BL,64blocks,base4 mapping;303nsWL/12nsBL and native16pFSL'),('NAND-05',[2,3,4],'2nA current and actual bias;25uA application scale is not universal full-scale'),('NAND-06',[58],'SLC full page program300/600us,blockerase1/3.5ms;cross-implementation bridge')],
 '05_rram':[('RRAM-05',[3,5,7],'native four64x32 subarrays with sharedTBL;PH0 frontend5ns'),('RRAM-01',[10,11],'1us actual SET/RESET waveform;external readback distinct from local binary verify')],
 '06_mram':[('MRAM-06',[5,9],'64banks x256rows x4bit;two-step complementary writes and actual row readback')],
 '07_pcm':[('PCM-03',[1,2,3],'8activeWL,256inputs in32groups,native256x1024cellbank;pureSLC is an organization choice'),('PCM-01',[7],'32IDACs,RESET125ns700uA and SET250ns/50ns tail wording;current resource and waveform bridge'),('PCM-06',[4],'selected-row programming with independent column conditions;supports row-wise mechanism,not imported512lanes')],
 '08_feram_hfo2':[('FERAM-03',[1,2],'14ns write vs8ns sense;destructive read/writeback inFig9;250fF BL Fig12')],
 '09_gain_cell_edram':[('GC-04',[9,10],'5ns coarse+60ns fine;row-wise retention read;0.4ms99.7% original-LSB criterion')],
 '10_fenor_3d':[('FENOR-02',[2,3],'SL+O-poor +/-2V20ns,RAWD<100ns,Vw/3 bias and simulated readRC')]
}

def mapping_from_stages(case,d,p):
    K,N,bs,br,S,R,alpha,extra=stage_expectation(case,d,'reference',p)
    ds,tr=sum(S.values()),sum(R.values())
    return {'delta_S_ns':ds/alpha,'T_R_ns':tr/alpha,
            'rho_Byte_per_s':K*bs/ds*1e9*alpha,'tau_Byte_per_s':K*N*br/tr*1e9*alpha,
            'RI_star':bs*tr/(N*br*ds),'U_star':tr/ds},(ds,tr,alpha,extra)


def production_probe_adapter(case):
    """Import an observation path, never used for an expected answer."""
    names=['sram_acim','sram_dcim','nor','nand','rram','mram','pcm','feram','gain_cell_edram','fenor']
    path=A/case/'scripts'/('check_'+names[CASES.index(case)]+'.py')
    spec=importlib.util.spec_from_file_location('review_observation_'+case,path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    api=next(getattr(mod,n) for n in ['S','api','s','API'] if hasattr(mod,n))
    d=read(A/case/'data/inputs.json')
    def observe(overrides=None,mode=None):
        overrides={} if overrides is None else overrides
        if case=='01_sram_acim':
            q=next(x for x in d['scenarios'] if x['id']=='reference')
            return mod.calculate('reference',q['frontend_complete_ns'],q['complete_memory_cycle_ns'])
        if case=='02_sram_dcim':return mod.compute()['scenarios'][1]
        if case=='03_nor_2d':return mod.evaluate(next(x for x in d['scenarios'] if x['profile']=='reference'))
        if case=='04_nand_3d':return mod.scenario('reference',overrides=overrides)
        if case=='05_rram':return mod.calculate(parameter_overrides=overrides)['scenarios'][1]
        if case=='06_mram':return mod.calculate(next(x for x in d['scenarios'] if x['profile']=='reference'))
        if case=='07_pcm':return mod.compute('reference',weak_verify=mode=='long_observation',parameter_overrides=overrides)
        if case=='08_feram_hfo2':return mod.make_row('reference',d['paired_media_budgets_ns']['reference'],'reference')
        if case=='09_gain_cell_edram':return mod.calc('reference',release_policy=mode or 'fixed_slot',parameter_overrides=overrides)
        if case=='10_fenor_3d':return mod.recompute()['main_scenarios'][1]
        raise NotImplementedError(case)
    return mod,api,observe


def dependency_checks():
    """Perturb the real common profile dictionary across all ten consumers.

    The independent stage ledger determines the full response, including zero
    responses when a complete primitive already includes a common stage.
    """
    common=read(A/'shared_baseline/data/shared_parameters.json')['common_conditions']['propagation']['profile_values']['reference']
    records=[];adapters={}
    for case in CASES:
        d=read(A/case/'data/inputs.json');mod,api,observe=production_probe_adapter(case)
        adapters[case]=(mod,api,observe)
        expected,stages=mapping_from_stages(case,d,common)
        base=observe()['mapping_interface']
        for key,value in expected.items():close(value,base[key],case+'/probe baseline/'+key)
        for param in ['input_step','adc_batch','digital_tick']:
            profile=api.C['propagation']['profile_values']['reference'];old=profile[param]
            try:
                profile[param]=old+1
                actual=observe()['mapping_interface']
            finally:profile[param]=old
            expected,changed=mapping_from_stages(case,d,{**common,param:common[param]+1})
            for key,value in expected.items():close(value,actual[key],case+'/shared '+param+'/'+key)
            records.append({'case_id':case,'parameter':param,'perturbation_ns':1,
                'expected_raw_vector_change_ns':changed[0]-stages[0],
                'expected_raw_full_load_change_ns':changed[1]-stages[1],
                'expected_availability':changed[2],'observed_mapping':{k:actual[k] for k in expected},
                'all_affected_services_recomputed':True})
    # Local front-end dependencies: expectation is a separate stage count,
    # not the production resolver's binding graph.
    local=[]
    def check_local(case,name,value,dds,dtr,mode=None,dh=0,dguard=0):
        observe=adapters[case][2];base=observe(mode=mode);row=observe({name:value},mode=mode)
        b=base['mapping_interface'];m=row['mapping_interface']
        if case=='09_gain_cell_edram':
            raw_s=base['nominal']['delta_S_ns']+dds
            raw_r=base['raw_mapping_interface']['T_R_ns']+dtr
            period=base['refresh']['period_ns']
            busy=base['refresh']['total_ns']+dh;guard=base['refresh']['scheduling_guard_ns']+dguard
            alpha=1-(busy+guard)/period
            close(row['refresh']['total_ns'],busy,'GC busy propagation')
            close(row['refresh']['scheduling_guard_ns'],guard,'GC guard propagation')
            close(row['refresh']['availability'],alpha,'GC availability propagation')
        else:raw_s=b['delta_S_ns']+dds;raw_r=b['T_R_ns']+dtr;alpha=1
        K,N,bs,br=dimensions(read(A/case/'data/inputs.json'))
        expected={'delta_S_ns':raw_s/alpha,'T_R_ns':raw_r/alpha,
                  'rho_Byte_per_s':K*bs/raw_s*1e9*alpha,'tau_Byte_per_s':K*N*br/raw_r*1e9*alpha,
                  'RI_star':bs*raw_r/(N*br*raw_s),'U_star':raw_r/raw_s}
        for key,v in expected.items():close(v,m[key],case+'/local '+name+'/'+key)
        local.append({'case_id':case,'mode':mode or 'main','parameter':name,'value_ns':value,
                      'independent_raw_delta_S_ns':dds,'independent_raw_delta_T_R_ns':dtr,
                      'independent_refresh_busy_change_ns':dh,'independent_guard_change_ns':dguard,
                      'all_affected_services_recomputed':True})
    # 30 selected WL, 480 grouped evaluations, 12 calibration reads,
    # 2 calibration WL setups; 6144 pages and 64 block erases.
    for name,value,ds,tr in [('sl_setup_ns',641,480,12),('bl_setup_ns',13,480,12),
          ('wl_setup_ns',304,30,2),('adc_batch_ns',21,480,12),
          ('digital_tick_ns',6,1790,6144*110+480*8*36+450),
          ('program_full_ns',300001,0,6144),('erase_full_ns',1000001,0,64)]:
        check_local('04_nand_3d',name,value,ds,tr)
    # 128 compute rounds; 512 full-load groups; RESET/SET attempts 2/1.
    for name,value,ds,tr in [('cim_frontend_ns',6,128,0),('verify_frontend_ns',6,0,512*3),
          ('local_setup_ns',101,0,512*3),('local_return_ns',101,0,512*3),
          ('reset_pulse_ns',1001,0,512*2),('set_pulse_ns',1001,0,512),
          ('rail_setup_ns',1001,0,1),('rail_exit_ns',1001,0,1)]:
        check_local('05_rram',name,value,ds,tr)
    # 2048 evaluations; 1024 updates x 16 fresh end-point reads.
    check_local('07_pcm','shared_front_ns',21,2048,1024*16)
    check_local('07_pcm','shared_front_ns',768,2048*748,1024*16*748)
    check_local('07_pcm','long_observation_ns',769,0,1024*16,mode='long_observation')
    # A minimum observation quota on the same physical voltage-read path
    # cannot hide an even longer common settling requirement.
    check_local('07_pcm','shared_front_ns',768,2048*748,0,mode='long_observation')
    check_local('07_pcm','shared_front_ns',900,2048*(900-20),1024*16*(900-768),mode='long_observation')
    # 32 compute groups, 256 refresh/update groups; exact max-group guard.
    for mode,name,value,ds,tr,h,g in [
        ('fixed_slot','common_overhead_ns',87,32,0,256,1),
        ('fixed_slot','read_slot_reservation_ns',65,32,0,256,1),
        ('fixed_slot','mac_integration_ns',2,0,0,0,0),
        ('fixed_slot','program_complete_ns',66,0,256,256,0),
        ('early_release','common_overhead_ns',87,32,0,256,1),
        ('early_release','mac_integration_ns',2,32,0,0,1),
        ('early_release','refresh_integration_ns',65,0,0,256,0)]:
        check_local('09_gain_cell_edram',name,value,ds,tr,mode=mode,dh=h,dguard=g)
    return {'expected_method':'Independent input-derived stage counts; production functions are observation-only, with in-memory parameters restored after each probe.',
            'common_parameter_probes':records,'local_and_mode_parameter_probes':local}


def mode_comparison_checks():
    pcm=read(A/'07_pcm/data/results.json');d=read(A/'07_pcm/data/inputs.json')
    p=read(A/'shared_baseline/data/shared_parameters.json')['common_conditions']['propagation']['profile_values']
    normal=pcm['paired_scenarios'][1];long=pcm['verify_organization_comparison'];slow=pcm['shared_front_parameter_sensitivity']
    # An independent acceptance observation quota is a conditional protocol,
    # not PCM-01's 0.2 V PWM/CCO transplanted into the voltage/SAR circuit.
    assert '0.2V PWM/CCO' in d['service_modes']['long_observation_verify']['bias_load_endpoint']
    assert 'conservative operation quota' in d['service_modes']['long_observation_verify']['qualification']
    assert long['scenario_class']=='operation_mode_comparison'
    assert slow['scenario_class']=='parameter_uncertainty'
    for row,front in [(long,20),(slow,768)]:
        ds=2048*(front+p['reference']['adc_batch']+2*p['reference']['digital_tick'])+2*p['reference']['digital_tick']
        tr=1024*(3*5+8*(5+3*20+125+300+2*(768+20+5)))
        m=row['mapping_interface']
        close(m['delta_S_ns'],ds,'PCM mode deltaS');close(m['T_R_ns'],tr,'PCM mode full load')
        close(m['rho_Byte_per_s'],256e9/ds,'PCM mode rho');close(m['tau_Byte_per_s'],32768e9/tr,'PCM mode tau')
        close(m['U_star'],tr/ds,'PCM mode U*')
    assert long['rho_Byte_per_s']==normal['rho_Byte_per_s'] and slow['rho_Byte_per_s']<normal['rho_Byte_per_s']
    gc=read(A/'09_gain_cell_edram/data/results.json');gd=read(A/'09_gain_cell_edram/data/inputs.json')
    records=[]
    for mode in gc['mode_comparisons']:
        profile=mode['profile'];v=p[profile];sp=gd['service_parameters']
        q=next(x for x in gd['profiles'] if x['id']==profile)
        front=v['input_step']+sp['profile_common_overhead_ns'][profile]+sp['mac_integration_ns']+v['adc_batch']
        refresh_front=v['input_step']+sp['profile_common_overhead_ns'][profile]+sp['refresh_integration_ns']+v['adc_batch']
        ds=32*(front+2*v['digital_tick'])+2*v['digital_tick']
        local=3*v['digital_tick']+q['program_complete_ns'];tr=256*local
        busy=256*(refresh_front+v['digital_tick']+local)
        guard=max(front+2*v['digital_tick'],local);alpha=1-(busy+guard)/gd['refresh']['period_ns']
        assert mode['scenario_class']=='operation_mode_comparison'
        close(mode['nominal']['delta_S_ns'],ds,'GC early-release raw DS')
        close(mode['refresh']['total_ns'],busy,'GC early-release refresh')
        close(mode['refresh']['scheduling_guard_ns'],guard,'GC early-release guard')
        close(mode['refresh']['availability'],alpha,'GC early-release alpha')
        m=mode['mapping_interface']
        for key,value in {'delta_S_ns':ds/alpha,'T_R_ns':tr/alpha,'rho_Byte_per_s':64e9/ds*alpha,
                          'tau_Byte_per_s':4096e9/tr*alpha,'RI_star':tr/ds/64,'U_star':tr/ds}.items():
            close(m[key],value,'GC early-release '+key)
        records.append({'profile':profile,'raw_delta_S_ns':ds,'raw_T_R_ns':tr,
                        'refresh_busy_ns':busy,'guard_ns':guard,'availability':alpha})
    return {'PCM_long_observation':'conditional separate acceptance protocol; source PWM/CCO architecture not transplanted',
            'PCM_shared_front_uncertainty':'propagates to evaluation and every terminal read; not a measured performance correction',
            'GC_early_release_independent_stages':records,
            'GC_fixed_slot':'intentional sampling reservation, including post-pulse analog hold; original 180 ns is only a whole-cycle anchor'}


def nand_quantization_checks():
    """Rebuild vectors and finite ADC arithmetic independently of case code."""
    d=read(A/'04_nand_3d/data/inputs.json');path=A/'04_nand_3d/data/quantization_diagnostics.json';diag=read(path)
    m=d['mapping'];v=d['design_choices'];K=m['K'];width=m['rows_per_group'];bits=v['quantization_diagnostic']['nominal_ADC_bits']
    full_scale=Fraction(str(v['current_sense_full_scale_uA']))*1000
    current=Fraction(str(d['reported_numeric']['cell_on_current_nA']))
    def nearest(value):return (2*value.numerator+value.denominator)//(2*value.denominator)
    def adc(count,i=current):
        unbounded=nearest(count*i*(1<<bits)/full_scale)
        return min((1<<bits)-1,max(0,unbounded)),unbounded<0 or unbounded>=(1<<bits)
    dense=width*9;full_code,clipped=adc(dense)
    gain=nearest(Fraction(dense*(1<<16),full_code))
    half_code,_=adc(dense//2);residual=Fraction(half_code)-Fraction(full_code,2)
    assert not clipped and abs(residual)<=v['calibration']['residual_limit_ADC_codes']
    assert gain<2**v['calibration']['coefficient_bits']
    makers={
      'zero':lambda k:(0,0),'unit_positive':lambda k:(1,1),'unit_negative':lambda k:(-1,1),
      'alternating_cancel':lambda k:(1 if k%2==0 else -1,1),
      'large_cancel':lambda k:(127 if k%2==0 else -127,127),
      'large_positive':lambda k:(127,127),'large_negative':lambda k:(-128,127),
      'small_ramp':lambda k:(k%7-3,k%5-2),'wide_ramp':lambda k:(k%256-128,(73*k)%256-128),
      'isolated_unit':lambda k:((1,1) if k==0 else (0,0))}
    checked=[]
    assert {x['id'] for x in diag['cases']}==set(makers)
    for row in diag['cases']:
        pairs=[makers[row['id']](k) for k in range(K)]
        exact=sum(x*w for x,w in pairs);unsigned=0;real=Fraction(0);maximum=0;clipped_partials=0
        for group,actual in enumerate(row['groups']):
            pairs_group=pairs[group*width:(group+1)*width]
            counts=[[sum(((x+128)//(4**a)%4)*((w+128)//(4**b)%4) for x,w in pairs_group) for b in range(4)] for a in range(4)]
            codes=[[adc(c)[0] for c in line] for line in counts]
            decoded=[[nearest(Fraction(c*gain,1<<16)) for c in line] for line in codes]
            assert counts==actual['nominal_unit_counts_by_input_weight_digit']
            assert codes==actual['ADC_codes_by_input_weight_digit']
            assert decoded==actual['decoded_integer_counts_by_input_weight_digit']
            group_sum=sum(decoded[a][b]*4**(a+b) for a in range(4) for b in range(4))
            assert group_sum==actual['reconstructed_unsigned_group_sum']
            unsigned+=group_sum
            real+=sum(Fraction(codes[a][b]*dense,full_code)*4**(a+b) for a in range(4) for b in range(4))
            maximum=max(maximum,max(c for line in counts for c in line)*current)
            clipped_partials+=sum(adc(c)[1] for line in counts for c in line)
        correction=128*sum(x+128+w+128 for x,w in pairs)-16384*K
        finite=unsigned-correction;real-=correction
        assert exact==row['exact_signed_dot'] and finite==row['quantized_reconstructed_signed_dot']
        assert finite-exact==row['signed_error'] and real==Fraction(row['ideal_real_coefficient_signed_dot_fraction'])
        assert clipped_partials==row['clipped_partials']==0
        close(float(maximum/1000),row['maximum_partial_current_uA'],'NAND maximum current')
        assert row['calibration']['gain_Q8_16_integer']==gain and row['calibration']['full_code']==full_code
        assert row['calibration']['finite_calibration_pass'] is True
        checked.append({'id':row['id'],'exact_signed_dot':exact,'quantized_signed_dot':finite,
                        'signed_error':finite-exact,'sign_reversal':exact*finite<0,'clipped_partials':clipped_partials})
    by_id={q['id']:q for q in checked}
    assert by_id['zero']['quantized_signed_dot']!=0 and by_id['unit_positive']['sign_reversal']
    assert by_id['large_cancel']['quantized_signed_dot']!=0
    qualification=d['numerical_service_qualification']
    assert qualification==diag['qualification'] and qualification['weak_signal_guarantee'] is False
    assert qualification['quantized_service_status']=='weak_signal_and_cancellation_not_qualified'
    close(diag['ENOB_resolution_scale_only']['full_scale_divided_by_2_to_ENOB_nA'],float(full_scale/2**8),'NAND ENOB scale')
    pressure=diag['current_headroom'];pressure_i=Fraction(str(pressure['deterministic_pressure_current_nA']))
    pc,clip=adc(dense,pressure_i);ph,_=adc(dense//2,pressure_i)
    assert clip and abs(Fraction(ph)-Fraction(pc,2))>v['calibration']['residual_limit_ADC_codes']
    assert pressure['pressure_calibration']['finite_calibration_pass'] is False
    return {'method':'Independent integer/Fraction reconstruction of all ten deterministic vectors, four physical row groups and sixteen digit partials per group.',
            'nominal_bits':bits,'gain_Q8_16_integer':gain,'full_reference_code':full_code,
            'half_reference_residual_codes':float(residual),'vector_checks':checked,
            'ENOB_is_resolution_scale_only':True,'pressure_clipping_detected':True,
            'diagnostic_reproduction_passed':True,'weak_signal_numerical_service_qualified':False,
            'diagnostic_sha256':sha(path)}

def run(check_export=True):
    shared=A/'shared_baseline/data/shared_parameters.json';s=read(shared)
    profiles=s['common_conditions']['propagation']['profile_values']
    checks=[]
    for case in CASES:
        ip=A/case/'data/inputs.json';rp=A/case/'data/results.json';d=read(ip);r=read(rp)
        input_provenance=input_provenance_checks(case,d)
        rows=scenario_rows(r)
        paired=[x for x in rows if scenario_profile(x) in PROFILES]
        assert len(paired)==3,(case,len(paired))
        sc=[]
        for x in paired:
            profile=scenario_profile(x)
            K,N,bs,br,S,R,alpha,extra=stage_expectation(case,d,profile,profiles[profile])
            ds,tr=sum(S.values()),sum(R.values());cap=K*N*br
            expected={'K':K,'N':N,'b_S':bs,'b_R':br,'B_S_Byte':K*bs,
                      'full_resident_payload_Byte':cap,'delta_S_ns':ds/alpha,'T_R_ns':tr/alpha,
                      'rho_Byte_per_s':K*bs/ds*1e9*alpha,'tau_Byte_per_s':cap/tr*1e9*alpha,
                      'RI_star':bs*tr/(N*br*ds),'U_star':tr/ds,
                      'average_update_ns_per_16KiB':tr/alpha*16384/cap}
            native=r['native_configuration']
            for key,value in [('K',K),('N',N)]:
                assert native[key]==value,(case,'native dimensions',key,native[key],value)
            width=native.get('output_bits',native.get('output_container_bits'))
            if width is not None:assert width>=16+math.ceil(math.log2(K)),(case,'output width')
            observed=x['mapping_interface']
            for key,value in expected.items():close(value,observed[key],f'{case}/{profile}/{key}')
            close(expected['U_star'],N*br/bs*expected['RI_star'],case+'/TableII interface')
            assert ds>0 and tr>0 and cap>0
            sc.append({'profile':profile,'raw_stream_stages_ns':S,'raw_full_load_stages_ns':R,
                       'raw_delta_S_ns':ds,'raw_T_R_ns':tr,'counts_and_resources':extra,
                       'independent_mapping':expected,'pass_check':True})
        ordered=sorted(sc,key=lambda x:PROFILES.index(x['profile']))
        assert [x['raw_delta_S_ns'] for x in ordered]==sorted(x['raw_delta_S_ns'] for x in ordered)
        assert [x['raw_T_R_ns'] for x in ordered]==sorted(x['raw_T_R_ns'] for x in ordered)
        evidence=[]
        for prefix,pages,judgment in SOURCE_INSPECTIONS[case]:
            matches=[p for p in (T/'literature').rglob(prefix+'_*.pdf') if 'Supplement' not in p.name];assert len(matches)==1,(prefix,matches)
            evidence.append({'source_id':prefix,'path':str(matches[0].relative_to(T)),
                             'prior_source_review_page_locators':pages,'sha256':sha(matches[0]),'inherited_claim_locator':judgment,
                             'review_scope':'Existing source-review locator retained; this execution checks file identity, not a new visual inspection of every original page.'})
        checks.append({'case_id':case,'inputs_sha256':sha(ip),'results_sha256':sha(rp),
                       'declared_input_provenance_checks':input_provenance,
                       'native_configuration':r['native_configuration'],'independent_stage_formula':FORMULAE[case],
                       'main_scenarios':sc,'primary_evidence_checks':evidence})
    geometry=geometry_checks()
    dependencies=dependency_checks()
    modes=mode_comparison_checks()
    numerical=nand_quantization_checks()
    export_review=check_unified(checks) if check_export else {'not_run':'authoring-stage-only invocation'}
    labels=[]
    for case in CASES:
        for p in (A/case/'tex').glob('*.tex'):
            for label in re.findall(r'\\label\{([^}]+)\}',p.read_text()):
                assert label.startswith(case+':'),(p,label)
                labels.append(label)
    assert len(labels)==len(set(labels)),'duplicate TeX labels'
    return {'validation_kind':'independent input-derived stage arithmetic, native geometry and resource/maintenance semantics; not silicon qualification or user acceptance',
            'independence':'Independent expected values derive from input geometry and stage ledgers. Case/shared functions are imported only for observed perturbation responses; no generator result or old expected point derives an answer.',
            'cases':checks,'geometry_and_cross_case_checks':geometry,'unified_export_checks':export_review,
            'actual_parameter_dependency_checks':dependencies,'mode_comparison_checks':modes,
            'numerical_service_checks':{'04_nand_3d':numerical},
            'numerical_service_qualifications':{'04_nand_3d':read(A/'04_nand_3d/data/inputs.json')['numerical_service_qualification']},
            'remaining_qualification':'NAND weak signed outputs and cancellation are not qualified. PCM shared weakest-code settling, GC control/hold conditions and RRAM cross-stack endpoint completion remain explicitly conditional engineering assumptions.',
            'all_passed_scope':'Execution, independent arithmetic, parameter propagation, deterministic diagnostic reproduction and export consistency only; not numerical-service adequacy, circuit qualification or user acceptance.',
            'shared_hashes':{'data/shared_parameters.json':sha(shared),'scripts/check_shared.py':sha(A/'shared_baseline/scripts/check_shared.py')},
            'unique_case_prefixed_labels':len(labels),
            'external_review_judgments':[
                'NAND: selected 25uA current frontend at original bias/native16pFSL, row grouping and settling budgets; SGVC SLC full-program/erase bridge; offset-encoding quantization error.',
                'RRAM/PCM: cross-implementation program waveform and binary acceptance-window completion; finite attempt scenarios are not measured yield distributions.',
                'FeRAM/FeFET/MRAM: explicitly provisioned driver, isolation, sense/mux/hold paths and supply load must meet engineering timing; FeRAM simultaneous PL restoration supply remains a sizing condition.',
                'GC-04: endpoint sign retention and adapted integration frontend, isolation to original write load, and repeated no-shadow refresh need physical qualification.'
            ],'all_passed':True}


def check_unified(checks):
    jp=A/'data/ten_case_results.json';cp=A/'data/ten_case_results.csv'
    doc=read(jp);rows=doc['results']
    main=[x for x in rows if x['scenario_type'] in ['recommended_reference','paired_conditional']]
    assert len(main)==len(checks)*3==30,'unified main table must contain exactly three scenarios per case'
    for case in checks:
        selected=[x for x in main if x['case_id']==case['case_id']]
        assert len(selected)==3 and {x['scenario_profile'] for x in selected}==set(PROFILES)
        assert sum(x['recommended'] for x in selected)==1
        assert next(x for x in selected if x['recommended'])['scenario_profile']=='reference'
        assert all(x['key_resources']==selected[0]['key_resources'] for x in selected),case['case_id']+' resource changed inside paired scenarios'
        for expected in case['main_scenarios']:
            x=next(x for x in selected if x['scenario_profile']==expected['profile'])
            m=expected['independent_mapping']
            for key,value in m.items():close(value,x['mapping_interface'][key],case['case_id']+'/unified/'+key)
            for key,value in [('B_S',m['B_S_Byte']),('B_R',m['full_resident_payload_Byte']),
                              ('rho',m['rho_Byte_per_s']/1e6),('tau',m['tau_Byte_per_s']/1e6),
                              ('RI_star',m['RI_star']),('U_star',m['U_star']),('T_R_ns',m['T_R_ns']),
                              ('delta_S_ns',m['delta_S_ns'])]:
                close(value,x[key],case['case_id']+'/unified/'+key)
            close(expected['raw_delta_S_ns'],x['raw_service_time']['streaming_ns'],'unified raw streaming')
            close(expected['raw_T_R_ns'],x['raw_service_time']['resident_ns'],'unified raw full-load')
            close(m['delta_S_ns'],x['effective_service_interval']['streaming_ns'],'unified effective streaming')
            close(m['T_R_ns'],x['effective_service_interval']['resident_ns'],'unified effective full-load')
            for suffix in ['inputs','results']:
                assert x['source_hashes'][case['case_id']+'/data/'+suffix+'.json']==case[suffix+'_sha256']
    for x in rows:
        if x['feasibility'].startswith('infeasible'):
            assert all(x[k] is None for k in ['rho','tau','RI_star','U_star','T_R_ns','delta_S_ns'])
            assert x not in main
        if 'append' in x['scenario_id']:
            assert x not in main,'finite pre-erased append cannot be a sustained paired point'
        if x['case_id']=='07_pcm':
            if 'verify_organization_comparison' in x['scenario_id']:
                assert x['scenario_type']=='operation_mode_comparison' and x not in main
            if 'shared_front_parameter_sensitivity' in x['scenario_id']:
                assert x['scenario_type']=='parameter_uncertainty' and x not in main
        if x['case_id']=='09_gain_cell_edram' and 'mode_comparisons' in x['scenario_id']:
            assert x['scenario_type']=='operation_mode_comparison' and x not in main
        if x['case_id']=='04_nand_3d':
            q=x['numerical_service_qualification']
            assert q['weak_signal_guarantee'] is False and q['quantized_service_status']=='weak_signal_and_cancellation_not_qualified'
            assert q['diagnostic_path']=='04_nand_3d/data/quantization_diagnostics.json'
            assert (A/q['diagnostic_path']).is_file()
    # CSV and JSON serialize the identical full ledger, including all contrasts.
    with cp.open(newline='') as stream:csvrows=list(csv.DictReader(stream))
    assert len(csvrows)==len(rows)
    for x,y in zip(rows,csvrows):
        assert set(x)==set(y)
        for key,value in x.items():
            if isinstance(value,(dict,list)):assert json.loads(y[key])==value,(key,'CSV structured data')
            else:assert y[key]==('' if value is None else str(value)),(key,'CSV scalar')
    return {'main_scenarios_matched_to_independent_arithmetic':len(main),
            'all_ledger_rows_JSON_CSV_identical':len(rows),'fixed_main_resources':True,
            'full_matrix_payload_time_boundary':True,'source_hashes_current':True,
            'unified_json_sha256':sha(jp),'unified_csv_sha256':sha(cp)}

def geometry_checks():
    # Physical addressing is checked as injective coverage, separately from timing.
    fd=read(A/'08_feram_hfo2/data/inputs.json');fm=fd['mapping'];K,N,_,_=dimensions(fd)
    shards=fm['shards'];outputs=fm['digital_output_lanes']
    feram={(i%shards,ceildiv(N,outputs)*(i//shards)+j//outputs,8*(j%outputs)+b)
           for i in range(K) for j in range(N) for b in range(8)}
    assert len(feram)==fm['shards']*fm['rows_per_shard']*fm['local_row_bits']==K*N*8
    xd=read(A/'10_fenor_3d/data/inputs.json');xm=xd['mapping'];K,N,_,_=dimensions(xd)
    lanes=xm['independent_row_read_lanes'];width=xm['outputs_per_strip']
    fefet={(i%lanes,i//lanes,(j//width)*8+b,j%width) for i in range(K) for j in range(N) for b in range(8)}
    assert len(fefet)==xm['independent_row_read_lanes']*xm['strips_per_row_lane']*xm['cells_per_strip']==K*N*8
    md=read(A/'06_mram/data/inputs.json');mm=md['mapping'];K,N,_,_=dimensions(md);columns=mm['weight_bits_per_bank_row']
    mram={(ceildiv(8,columns)*j+b//columns,i,b%columns) for i in range(K) for j in range(N) for b in range(8)}
    assert len(mram)==mm['banks']*mm['rows_per_bank']*columns==K*N*8
    rd=read(A/'05_rram/data/inputs.json');rc=rd['configuration'];K,N,_,_=dimensions(rd)
    group=rc['native_subarray_input_terms'];batch=rc['logical_weights_per_update']
    rram={(j,group*g+batch*s+b) for j in range(N) for g in range(ceildiv(K,group))
          for s in range(ceildiv(group,batch)) for b in range(batch) if group*g+batch*s+b<K}
    assert len(rram)==K*N
    pd=read(A/'07_pcm/data/inputs.json');pm=pd['mapping'];K,N,_,_=dimensions(pd)
    width=pm['program_source_line_group_width'];heads=pm['writeheads']
    pcm={(row,width*head+stripe) for row in range(K) for stripe in range(width)
         for head in range(heads) if width*head+stripe<N}
    assert len(pcm)==K*N and heads*width==N
    pr=read(A/'07_pcm/data/results.json')['native_configuration']['resources']
    assert pr['mode_gate_mux_per_cell'] is False
    assert pr['column_mode_isolation_channels']==K*N*8/K
    assert pr['IDAC_count']==heads and pr['compute_WL_lines']==K and pr['plane_isolation']
    assert pr['shared_return_RESET_rating_mA']>=heads*pd['program']['reset_current_uA']/1000
    assert pr['shared_return_SET_rating_mA']>=heads*pd['program']['set_current_uA']/1000
    # Exhaustive signed scalar identity with physical base4 copies counted once.
    for x in range(-128,128):
        for w in range(-128,128):
            xp,wp=x+128,w+128
            physical=0
            for a in range(4):
                xd=(xp>>(2*a))&3
                for b in range(4):
                    wd=(wp>>(2*b))&3
                    # x and w each use one LSB plus two MSB physical copies.
                    xb=[xd&1,(xd>>1)&1,(xd>>1)&1]
                    wb=[wd&1,(wd>>1)&1,(wd>>1)&1]
                    physical+=sum(xx*ww for xx in xb for ww in wb)*(4**(a+b))
            assert physical-128*xp-128*wp+16384==x*w
    nand=read(A/'04_nand_3d/data/results.json')['native_configuration']
    assert nand['resources']['intermediate_container_bits']>=1+math.ceil(math.log2(nand['K']*255**2+1))
    # GC fixed-order guard reserves the actual longest nonpreemptible group.
    gc=read(A/'09_gain_cell_edram/data/results.json')
    stress=gc['infeasible_stress']
    if isinstance(stress,dict):stress=[stress]
    assert stress
    for x in stress:
        assert x['refresh']['availability']<=0
        assert x['rho_Byte_per_s'] is None and x['tau_Byte_per_s'] is None and x['ridge'] is None
    assert all(x['refresh']['availability']>0 and x['refresh']['workload_slack_ns']>x['nominal']['delta_S_ns'] for x in gc['scenarios'])
    return {'FeRAM_address_coverage_bits':len(feram),'FeFET_address_coverage_bits':len(fefet),
            'MRAM_complementary_weight_bits':len(mram),'RRAM_update_coverage_weights':len(rram),'PCM_row_striped_update_coverage_weights':len(pcm),'PCM_isolated_columns_and_common_return_ratings_declared':True,'NAND_exhaustive_signed_scalar_pairs':256*256,
            'NAND_offset_intermediate_width_valid':True,
            'GC_main_scenarios_sustainable_with_fixed_refresh_and_no_shadow':True,
            'GC_infeasible_cases_have_null_effective_throughput':len(stress)}

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--emit',action='store_true');args=parser.parse_args()
    report=run();text=json.dumps(report,ensure_ascii=False,indent=2)+'\n';out=A/'data/ten_case_validation.json'
    if args.emit:out.write_text(text)
    else:assert out.read_text()==text,'stale independent validation record; rerun after resolving model/check failures'
    print('PASS: 30 independent stage reconstructions; 30 common and 27 local/mode parameter probes; full-load/U*; nominal quantization diagnostics reproduced. NAND weak-signal/cancellation numerical service remains NOT QUALIFIED.')
