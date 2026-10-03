#!/usr/bin/env python3
"""Independent stage/geometry review. No case or shared calculator is imported.

Expected services are reconstructed from input geometry, resources and stage
budgets, never from unified exports or an old table of expected result values.
The JSON record binds this review to the exact inputs/results/evidence files.
"""
import argparse
import csv
import hashlib
import json
import math
import re
from pathlib import Path

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
            R[phase+'_binary_verify']=count*(ti+v['binary_verify_frontend_ns']['value']+v['binary_sense_slot_ns'][profile])
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
        front=ti+q['dedicated_read_ns']+ta
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

def run(check_export=True):
    shared=A/'shared_baseline/data/shared_parameters.json';s=read(shared)
    profiles=s['common_conditions']['propagation']['profile_values']
    checks=[]
    for case in CASES:
        ip=A/case/'data/inputs.json';rp=A/case/'data/results.json';d=read(ip);r=read(rp)
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
                             'pdf_pages_inspected':pages,'sha256':sha(matches[0]),'checked_claim':judgment})
        checks.append({'case_id':case,'inputs_sha256':sha(ip),'results_sha256':sha(rp),
                       'native_configuration':r['native_configuration'],'independent_stage_formula':FORMULAE[case],
                       'main_scenarios':sc,'primary_evidence_checks':evidence})
    geometry=geometry_checks()
    export_review=check_unified(checks) if check_export else {'not_run':'authoring-stage-only invocation'}
    labels=[]
    for case in CASES:
        for p in (A/case/'tex').glob('*.tex'):
            for label in re.findall(r'\\label\{([^}]+)\}',p.read_text()):
                assert label.startswith(case+':'),(p,label)
                labels.append(label)
    assert len(labels)==len(set(labels)),'duplicate TeX labels'
    return {'validation_kind':'independent input-derived stage arithmetic, native geometry and resource/maintenance semantics; not silicon qualification or user acceptance',
            'independence':'No case/shared calculation functions imported; no unified result or old expected point used to derive answers.',
            'cases':checks,'geometry_and_cross_case_checks':geometry,'unified_export_checks':export_review,
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
    print('PASS: ten input-derived native configurations; 30 stage reconstructions; full-load/Table II interface; encoding, resources and maintenance semantics.')
