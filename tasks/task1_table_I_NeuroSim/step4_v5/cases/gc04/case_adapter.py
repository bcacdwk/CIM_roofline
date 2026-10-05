"""GC04 case-owned component adapter. Work-in-progress; no legacy performance."""
import math
from maintenance import work_conserving_schedule
from gc_model import Cell
from qualification import qualify

def prepare_components(resolved):
    p=resolved['resolved_parameters'];K=resolved['input']['logical']['K'];N=resolved['input']['logical']['N']
    q={'technology_nm':p['technology_nm'],'temperature_K':p['temperature_K'],
       'adc_lanes':2*p['adc_pair_lanes'],'adc_bits':p['adc_bits'],'physical_rows':p['physical_rows'],
       'physical_arrays':p['weight_planes']*p['row_halves']*p['output_groups'],
       'bank_choices':p['row_halves']*p['output_groups'],
       'row_driver_fanout':p['weight_planes']*p['output_groups'],
       'clock_Hz':p['clock_Hz'],'array_width_m':p['array_width_m'],
       'bank_mux_resistance_basis_ohm':p['array_isolation_target_ohm'],
       'sample_switch_resistance_basis_ohm':p['sample_switch_target_ohm'],
       'array_intrinsic_cap_F':p['array_intrinsic_column_cap_F'],
       'program_qualified_cap_F':p['write_qualified_cap_F'],
       'integration_cap_F':p['integration_cap_F'],'integration_parasitic_cap_F':0.,'external_hold_cap_F':p['external_hold_cap_F'],
       'adc_input_cap_F':p['adc_input_cap_F'],'precharge_width_F':p['precharge_width_F'],
       'precharge_voltage_V':p['precharge_voltage_V'],'precharge_error_fraction':p['precharge_error_fraction'],
       'current_valid_min_V':p['current_valid_min_V'],'current_valid_max_V':p['current_valid_max_V'],
       'rwl_driver_target_ohm':p['rwl_target_ohm'],'rwl_idle_voltage_V':p['rwl_voltage_V'],
       'rwl_wire_ohm':p['rwl_wire_ohm'],'rwl_gate_load_F':p['rwl_load_F'],
       'pulse_short_s':p['pulse_short_s'],'pulse_long_s':p['active_rows']*p['pulse_short_s']}
    # These fields are required once the independentWWL component is installed.
    q.update({k:p[k] for k in ('wwl_gate_load_F','wwl_wire_ohm','wwl_driver_target_ohm','wwl_active_voltage_V') if k in p})
    return {'frontend':{'kind':'gc_current','request':{'kind':'gc_current','identity':resolved['input']['implementation_id']+' actual branch ports','point_eligibility':'component_only','parameters':q}}}

def prepare_additional_components(resolved,raw):
    p=resolved['resolved_parameters'];l=resolved['input']['logical'];f=raw['frontend']
    q={k:p[k] for k in ('technology_nm','temperature_K','mac_lanes','accumulator_bits','adc_bits','adc_pair_lanes','xsum_bits','input_port_bits','resident_port_bits','clock_Hz')}
    q.update(logical_K=l['K'],logical_N=l['N'],rwl_control_load_per_row_F=f['RWL_control_load_per_logical_row_F'],program_control_cap_F=p['program_control_cap_F'])
    return {'digital':{'kind':'gc_digital','request':{'identity':resolved['input']['implementation_id']+' actual ADC/Xsum/maintenance operators','point_eligibility':'component_only','parameters':q}}}

def stage(name,time,count,source,resource,includes,excludes):
    cls={'TRAINING':'native_circuit','MLP':'native_circuit','GC04':'external_primitive','COMPACT':'adapter','SCHEDULER':'service_policy','POLICY':'service_policy'}[source]
    d={'id':name,'duration_s':time,'count':int(count),'source_class':cls,'source_ids':[source],
       'resources':resource,'includes':includes,'excludes':excludes}
    if cls=='native_circuit':d.update(native_return_unit='seconds',included_internal_clock_phases='Native components containhalfcyclecaptures;case rounds each independent launch tooneormore completelegalcycles withoutdoublebilling')
    return d

def evaluate(resolved,raw):
    p=resolved['resolved_parameters'];l=resolved['input']['logical'];f=raw['frontend'];d=raw['digital'];P=1/p['clock_Hz'];K=l['K'];N=l['N']
    align=lambda t:max(P,math.ceil((t-1e-18)/P)*P)
    outgroups=math.ceil(N/p['mac_lanes']);rowgroups=math.ceil(K/p['active_rows'])
    analog_groups=rowgroups*outgroups*8;refresh_groups=K*outgroups
    # Address/mask is prepared while RWL remains idle. Parallel independent
    # control paths overlap only in this explicit phase; precharge waits on bank.
    setup=align(max(d['input_bit_select_s']+d['input_row_mask_s'],d['output_group_select_s'])+
                f.get('bank_address_setup_s',0)+f['bank_MUX_control_s']+f['sample_TG_control_s']+
                f['precharge_control_s']+f['precharge_ladder_RC_s'])
    # Finite three-node settling: timing upper bound from the actual R/C envelope.
    # Full numerical network and sample injection qualification are separate gates.
    eqsettle=-math.log(p['sampling_error_fraction'])*(f['bank_MUX_effective_R_envelope_ohm']*f['array_read_node_C_F']+
              f['sample_TG_effective_R_envelope_ohm']*f['ADC_node_C_F'])
    short=f.get('PWM_actual_short_s',p['pulse_short_s']);long=f.get('PWM_actual_long_s',p['active_rows']*short)
    read_fixed=f['PWM_fanout_control_s']+f['RWL_mask_to_driver_s']+7*f['RWL_rise_tau_s']+eqsettle+f['sample_TG_control_s']+f['native_ADC_s']+d['ADC_capture_s']
    read=align(read_fixed+short);refresh_read=align(read_fixed+long)
    diff=align(d['ADC_difference_s']+d['difference_capture_s'])
    MAC=align(d['MAC_comb_s']+d['MAC_capture_s'])
    correction=align(d['final_Xsum_correction_comb_s']+d['MAC_capture_s'])
    # Feedback primitive covers originalcell/currentdriver/coarse/fine. New WWL
    # setup/release and bank allOFF are added where physically present.
    wwl=f.get('WWL_address_setup_s',0)+2*(f.get('WWL_enable_control_s',0)+f.get('WWL_mask_to_driver_s',0))+7*(f.get('WWL_rise_tau_s',0)+f.get('WWL_fall_tau_s',0))
    force=f.get('RWL_mode_capture_s',0)+2*(f.get('RWL_program_force_control_s',0)+f['RWL_mask_to_driver_s'])+7*(f['RWL_rise_tau_s']+f['RWL_fall_tau_s'])
    write=align(d['program_resident_refresh_select_s']+f.get('bank_all_OFF_control_s',f['bank_MUX_control_s'])+wwl+force+p['feedback_write_s'])
    target=align(d['target_capture_s']);progress=align(d['resident_progress_increment_s']+d['maintenance_state_capture_s'])
    clear=align(d['stream_clear_comb_s']+P/2);rclr=align(d['resident_progress_clear_comb_s']+P/2)
    stream=[stage('stream_clear',clear,1,'MLP','result/Xsum clear only','physicalclearandcapture','residentprogress/refreshstate'),
      stage('input_ingress',align(d['input_capture_s']+d['input_ingress_select_s']),int(d['input_ingress_beats']),'MLP','128bitport,inputhold512bits','fullinputpayloadonce','no per-bitpayload'),
      stage('Xsum_accumulate',align(d['Xsum_comb_s']+d['Xsum_capture_s']),K,'MLP','one16bitadder/Xsumfeedback','64realINT8inputadds','no inputtruthoracle'),
      stage('analog_group_setup',setup,analog_groups,'TRAINING','selectedbank/RWLmask/precharge','addressthenbank/sampleconnect/precharge;RWLidle','notintegration'),
      stage('analog_integrate_convert_capture',read,analog_groups,'COMPACT','256branchintegration/11bitSAR/rawhold','PWMphysicaldeadtime,shortpulse,RWLrelease,nodeequalize,SAMPoff,SARandcapture','notdiff/MAC;noDFFasPWMsynthesis'),
      stage('pair_subtract',diff,analog_groups,'MLP','128parallel12bitdifference/hold','twoindependentADCcodes subtract','no free differentialADC'),
      stage('plane_MAC',MAC,analog_groups*8,'MLP','16lane32bitoperator/hold','8planesignedshiftandinputsign,actualoperandselect','no Xsumfinalcorrection'),
      stage('Xsum_correction',correction,outgroups,'MLP','16lane32bitoperator/hold','subtractXsum<<4,wiredivide2','no free numerictruth')]
    resident=[stage('resident_progress_clear',rclr,1,'MLP','resident8bitprogressclear','separateclear','streamresultsuntouched'),
      stage('resident_target',target,refresh_groups,'MLP','128bitport/targethold','16weightsperbatch','nexttargetnotintakenduringrefresh'),
      stage('feedback_write',write,refresh_groups,'GC04','128pairreplicated50fFfeedbackengines','complete75/65nsprimitiveplusnewisolation/WWL','no additionalinternalcoarseorverify'),
      stage('resident_commit',progress,refresh_groups,'MLP','8bitprogressandterminalcarry','commitcompletedbatch,addressadvance','notmodulowrapasfreepayload')]
    S=sum(x['duration_s']*x['count'] for x in stream);TR=sum(x['duration_s']*x['count'] for x in resident)
    # One sign-read refresh group; its binarycode is latched fromactualADCdiff,
    # then restored throughsamefeedbackengine. It does notclearstreamXsum/result.
    refresh_code=align(d['refresh_capture_s']);refresh_progress=align(d['refresh_progress_increment_s']+d['maintenance_state_capture_s'])
    q=setup+refresh_read+diff+refresh_code+write+refresh_progress
    # Clear is a real once-perrequest atomicsetup, never a fractional pergroup fee.
    B=target+write+progress
    sched=work_conserving_schedule(p['retention_limit_s'],q,refresh_groups,S,B,p['maintenance_guard_cycles']*P,keep_trace=True,resident_request_setup_s=rclr)
    maintenance={'basis':'actual_event_schedule','feasible':sched['feasible'],'schedule_policy':'workconservingfixedgrouporder;whole streamatomic,residentcommitbatchatomic',
      'event_summary':sched,'raw_stream_s':S,'raw_resident_s':TR,'retention_limit_s':p['retention_limit_s'],
      'long_term_stream_interval_s':sched.get('long_term_stream_interval_s'),
      'long_term_resident_interval_s':sched.get('long_term_resident_interval_s'),
      'single_admitted_stream_latency_s':S if sched['feasible'] else None,
      'single_resident_post_refresh_latency_s':sched.get('resident_single_post_refresh_latency_s'),
      'max_group_writeback_gap_s':max(sched.get('max_stream_group_writeback_gap_s',0),sched.get('max_resident_group_writeback_gap_s',0)) if sched['feasible'] else None}
    electrical=qualify(p,f)
    checks=[{'id':'program_load_50fF','passed':bool(f['program_load_feasible']),'evidence':{'actual_F':f['program_connected_load_F'],'match_F':f['program_match_cap_F']}},
      {'id':'ADC_parallel_physical_count','passed':int(f['ADC_lanes'])==2*p['adc_pair_lanes'],'evidence':{'SAR':f['ADC_lanes'],'pair':p['adc_pair_lanes']}},
      {'id':'input_Xsum_width','passed':p['xsum_bits']>=14,'evidence':{'extremes':[-128*K,127*K]}},
      {'id':'separate_WWL_RWL_program_ports','passed':bool(f.get('WWL_native_rail_feasible',0)) and bool(f.get('RWL_program_force_control_s',0)), 'critical':True,'evidence':{'WWLarea':f.get('WWL_area_m2'),'programforce_s':f.get('RWL_program_force_control_s')}}]+electrical['checks']
    resources={'physical_cells':K*N*16,'physical_subarrays':p['weight_planes']*p['row_halves']*p['output_groups'],'pair_ADC_lanes':p['adc_pair_lanes'],'physical_single_ended_SAR':f['ADC_lanes'],
       'physical_feedback_pair_engines':p['adc_pair_lanes'],'logical_weights_per_write':p['mac_lanes'],'refresh_groups':refresh_groups,'refresh_group_s':q,
       'normal_analog_groups':analog_groups,'normal_MAC_updates':analog_groups*8,'native_frontend':f,'native_digital':d,'external_hold_total_F':2*p['adc_pair_lanes']*p['external_hold_cap_F'],'source_cell_area_lower_bound_m2':K*N*16*6e-12,
       'stage_policy':'fulllegalclock eachnewlaunch; explicitparallelonlyinsetup;phasecounternotfreework'}
    return {'status':'conditional','program_outcome':'success','scheduling':'serial_nonoverlap','qualification':'conditional_GC04_finite_model_domain_Q4_analog_approximation',
      'conditions':['Same50fFcompletefeedbackwrite source transfer at353Kisconditional,not same-temperature measurement.','Finitecharge/leakmodelnotallcellretentionguarantee;sourceFF80Csimulationandunspecified-temperaturepairmeasurementseparate.', 'NominalQ4analogapproximationonly;fullTGgatechargeandADCinputconditionsboundlocalerror,notENOB. Fixed4pFexternalholdperbranchcounts1.024nFphysicalresource.', 'Declaredinitialstateisinperiodicmaintenancewitharbitraryolddata;firstmaintenancewritesgroupssequentially,notallfreeagezero. Residentprogressandold/newstatespersist.','Actualclock200ns;PWMrequiresseparatecalibrateddelayline,notarbitraryclockedge.'],
      'physical_checks':checks,'resources':resources,'stream_stages':stream,'resident_stages':resident,'maintenance':maintenance,
      'electrical_model':electrical,
      'refresh_stage_durations_s':{'setup':setup,'read':refresh_read,'difference':diff,'codehold':refresh_code,'write':write,'progress':refresh_progress}}
