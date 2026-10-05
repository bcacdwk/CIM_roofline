"""PCM finite accepted-endpoint model using native periphery and explicit state/reference RC."""
import math
from adapter import passive_reference_develop, full_cover_counts, serial_mac, verify_binary_readback, nominal_full_cover_lifecycle, source_grid, coupled_reference_develop

NATIVE_FIELDS=('technology_nm','device_node_nm','temperature_K','rows','cols','read_mux','write_mux',
 'resistance_on_ohm','resistance_off_ohm','access_resistance_ohm','cell_pitch_x_m','cell_pitch_y_m',
 'read_voltage_V','access_voltage_V','write_port_voltage_V','wire_ohm_per_m','clock_Hz','extra_column_cap_F',
 'sense_threshold_V','precharge_width_F','precharge_error_fraction','input_port_bits','resident_port_bits','read_mux_IR_fraction','write_mux_target_ohm')

def prepare(resolved):
    p=resolved['resolved_parameters']
    return {'identity':resolved['input']['implementation_id']+' native circuit request only',
            'point_eligibility':'probe_only','parameters':dict({k:p[k] for k in NATIVE_FIELDS},extra_column_cap_F=p['extra_column_cap_F']+source_grid(p)['source_BL_coupling_F'],write_current_A=max(p['reset_current_A'],p['set_current_A'])),
            'limitations':['Endpoint resistance/read bias are conditional engineering ports, not a measured global population.',
             'Native write port only selects; source current-waveform engine and terminal compliance are separate conditions.']}

def stage(name,t,count,kind,ids,resources,includes,excludes,clock=None):
    d={'id':name,'duration_s':t,'count':count,'source_class':kind,'source_ids':ids,'resources':resources,'includes':includes,'excludes':excludes}
    if kind=='native_circuit':d.update(native_return_unit='seconds',included_internal_clock_phases=clock or 'none; native circuit delay')
    return d

def evaluate(resolved,n):
    p=resolved['resolved_parameters'];L=resolved['input']['logical'];K=L['K'];N=L['N'];groups=p['read_mux']
    lanes=int(n['native_sa_count']);write_lanes=p['cols']//p['write_mux'];period=1/p['clock_Hz']
    cnt=full_cover_counts(K,N,write_lanes,lanes)
    parasitic=p['access_resistance_ohm']+n['array_col_res_ohm']+n['actual_mux_res_ohm']
    C=n['sa_effective_node_cap_F'];Cref=C*p['reference_cap_ratio']
    # Guard windows are prequalified model conditions. Hardware verify compares binary values only.
    grid=source_grid(p)
    ref=passive_reference_develop(p['on_accept_max_ohm']+parasitic,p['off_accept_min_ohm']+parasitic,
         p['reference_resistance_ohm']+parasitic,C,Cref,p['read_voltage_V'],p['sense_threshold_V']+p['sense_error_budget_V'])
    # Reference isolationTG fields are consumed once the final commonport is available.
    if 'reference_switch_R_ohm' in n:
        ref=coupled_reference_develop(p,n,grid,n['reference_switch_R_ohm'])

    check=lambda ident,passed,evidence,critical=True:dict(id=ident,passed=bool(passed),critical=critical,evidence=evidence)
    checks=[check('reference_matched_control',n['reference_enable_load_match_feasible'] and abs(n['reference_isolation_edge_s']-n['WL_enable_edge_only_s'])<=p['enable_skew_limit_s'],'Actualreplica/NAND/INV/controlmatchingcap instantiated; finite residualskew propagated'),
      check('finite_attempt_policy',p['write_attempt_limit']==1,'Thisadapterimplementsonecompleteattempt;noimplicitretryorprobability'),
      check('write_switch_drop',p['reset_current_A']*n['write_column_TG_ohm']<n['actual_tech_vdd_V']-n['actual_tech_vth_V'],'DeclaredCMOSwritepath must supportprogramcurrent;thermalvoltageisnotR_read*I'),
      check('reference_precharge_isolation','reference_switch_R_ohm' in n,'RealreferenceTGandcontrolrequired;oldpointsareunqualified'),
      check('program_access_source_IR',n['actual_access_Ion_at_native_bias_A']*(1-grid['write_source_drop_V']/(n['actual_tech_vdd_V']-n['actual_tech_vth_V']))>=p['reset_current_A'],'Sourcebounce-correctednativeaccessIon;nohotPCMreadRextrapolation'),
      check('shared_source_topology',grid['write_source_drop_V']<n['actual_tech_vdd_V']-n['actual_tech_vth_V'],grid),
      check('mapping',K==p['rows'] and N*8==p['cols'],'K rows and8physicalbinarycells/weight; no payload duplicates'),
      check('reference_aperture',ref['feasible'],ref),
      check('precharge_headroom',n['precharge_bias_feasible'],'nativeVdd-readV-Vth='+str(n['precharge_headroom_V'])),
      check('clock',n['digital_clock_budget_satisfied'],'period='+str(period)+'; minimum='+str(n['digital_halfcycle_min_period_s'])),
      check('access_current',n['actual_access_bias_matches_native'] and n['actual_access_Ion_at_native_bias_A']>=p['reset_current_A'],
       'Native-biased access current capability only: '+str(n['actual_access_Ion_at_native_bias_A'])+'A. Not PCM hot-state I-V or complete write compliance.'),
      check('shared_return',write_lanes*p['reset_current_A']<=p['shared_return_limit_A'],'Actual16laneRESET requires8mA; rated supply is explicit fixed architecture condition.'),
      check('native_write_route_nonzero',n['write_column_driver_one_edge_s']>0,'Physical route edge must be derived from transistor RC, never zero native pulse-return.'),
      check('endpoint_windows',p['resistance_on_ohm']<=p['on_accept_max_ohm']<p['off_accept_min_ohm']<=p['resistance_off_ohm'],'Nominal selected working endpoints lie inside assumed characterized windows; no population guarantee.'),
      check('pulse_domain',10e-9<=p['reset_waveform_s']<=200e-9 and 100e-9<=p['set_waveform_s']<=2000e-9,'Source Figs3/5 same-material pulse-duration plateau; finite policies not PVT.')]
    resources={'source_grid':grid,'program_routing_compliance_overhead_V':p['reset_current_A']*(p['access_resistance_ohm']+n['array_col_res_ohm']+n['write_column_TG_ohm'])+grid['write_source_drop_V'],'physical_data_bits':K*N*8,'logical_weight_Byte':K*N,'array_rows':K,'physical_columns':N*8,
      'sense_lanes':lanes,'read_groups_per_row':groups,'write_current_lanes':write_lanes,
      'input_hold_bits':int(n['input_hold_bits']),'row_input_hold_bits':8,'weight_hold_bits':int(n['weight_hold_bits']),
      'write_target_hold_bits':int(n['target_hold_bits']),'output_hold_bits':int(n['signed_output_hold_bits']),
      'wide_add_lanes':int(n['extra_25bit_adder_lanes']),'wide_add_bits':25,'verify_compare_byte_lanes':int(n['verify_compare_lanes']),
      'unsensed_WL_active_columns':p['cols']-lanes,'unsensed_BL_history_V':[0.,p['unselected_BL_initial_max_V']],'reference_enable_matching_cap_F':n['reference_enable_matching_cap_F'],'reference_isolation_TGs':int(n['reference_isolation_count']),'reference_switch_R_ohm':n['reference_switch_R_ohm'],'reference_switch_drain_F':n['reference_switch_drain_F'],'data_zero_mask_gates':int(n['data_zero_mask_gates']),'reference_resistors':lanes,'reference_resistance_ohm':p['reference_resistance_ohm'],'reference_total_cap_F_each':Cref,'reference_matched_shunt_cap_F_each':Cref-n['reference_switch_drain_F']-n['precharge_added_drain_cap_F']-(n['sa_effective_node_cap_F']-n['adapted_sa_input_cap_F']),
      'reference_cap_layout_requirement':'Dedicated matched branch withsameR/Cparasitic/loading;64referencecaps/resistors;fixedR is architecturechoice, not PCMintermediate state.',
      'precharge_branches':int(n['precharge_branches']),'precharge_device_width_F':p['precharge_width_F'],
      'state_clear_bits':int(n['state_clear_bits']),'state_clear_area_m2':n['state_clear_area_m2'],'program_engine_target_mask_bits':write_lanes,'program_engine_per_column_target_gates':p['cols'],'external_program_sources':write_lanes,'reset_peak_A_per_lane':p['reset_current_A'],'set_peak_A_per_lane':p['set_current_A'],
      'reset_shared_current_A':write_lanes*p['reset_current_A'],'write_supply_compliance':'Must reproduce same-source terminal current waveforms at new array; source did not tabulate compliance voltage.',
      'actual_access_width_m':n['actual_access_width_m'],'cell_pitch_x_m':p['cell_pitch_x_m'],'cell_pitch_y_m':p['cell_pitch_y_m'],
      'native_array_area_m2_partial':n['native_area_m2'],'area_qualification':'Reference passives/current sources/isolation layout uncalibrated; do not treat native area as complete macroarea.',
      'native_short_arithmetic':'Native15bitadder/subtractor instantiated but unused in complete signedMAC schedule; extra25bitpath explicitly used.'}
    conditions=[
      'Selected working PCM cells reach Ron<=20kohm orRoff>=200kohm after specified pulses; this is prior characterization/service condition, not an online resistance-window measurement or population yield.',
      'Native VSA adapted to10mV design target; combined input-referred offset/noise/reference error must stay within5mV. NeuroSim does not predict this budget or statistical BER.',
      'Fixed40kohmreference/matchedtotalC andactualWLmatched-enablereplica are real resources;referenceTGisOFFduringprecharge.Threefinite residualenable-skews(-1/0/+1ns) timesfourloadcontexts are explicitlyexercised.±1ns is adesignqualification, notmeasuredjitterorcompleteSTA.',
      '0.2V read is a declared nondestructive low-bias engineering condition; source does not establish this exact bias or a long-term read-disturb limit.',
      'External16lane current-waveform engine must deliver source-equivalent .5mARESET/.2mASET with sufficient compliance and source-equivalent quench/terminal recovery. Published pulse widths are retained as indivisible characterized waveform service; separate edge/cooling detail is not available. New routing setup/release is charged separately, and native write RC is not claimed to generate thermal-write waveforms.',
      'Allcolumns,includingnot-sensedcolumns,mustbeinthe0..0.2Vread-safeinitialdomainbeforeevaluation/verify;theirnonzerohistoryandallWLactivecellsareexplicitlyintheKCL. Programengine returntothisdomain remainsanexternalportcondition. Finitepostprogramstatewindowonly;no long-term driftrecalibrationguarantee.',
      'Nominal register timing atchosenclock is constrained by native models; not transistor-level STA or silicon signoff.']
    if not all(c['passed'] for c in checks):
        return dict(status='infeasible',qualification='PCM binary reference candidate',conditions=conditions,program_outcome='blocked',scheduling='serial_nonoverlap',physical_checks=checks,resources=resources,stream_stages=[],resident_stages=[],counts=cnt,reference_network=ref)
    select=n['group_select_s']+n['native_mux_s']
    wl_setup=n['WL_enable_edge_only_s'];wl_release=n['WL_release_s'];address=n['WL_address_setup_s']
    # The native precharge clock phase is lengthened only when the explicit low-rail BL/reference port needs it.
    extpre=n['precharge_external_RC_s']*max(1.,Cref/C)+n['precharge_control_s']
    pre=n['sa_precharge_per_group_s']+max(period,extpre)
    refedge=n['reference_isolation_edge_s']
    read=address+select+pre+n['precharge_control_s']+max(wl_setup,refedge)+ref['develop_s']+period+max(wl_release,refedge) # allWLoffduringprecharge; latchthenrelease
    io=max(period,n['input_ingress_select_s']+n['input_capture_s'])
    target_io=max(period,n['target_ingress_select_s']+n['target_hold_capture_s'])
    rowpick=max(period,n['input_row_select_s']+n['input_row_capture_s'])
    operand=n['group_select_s']+max(n['weight_group_select_s']+n['extra_shift_select_s']+n['extra_shifted_weight_mux_s']+n['data_zero_mask_s'],n['input_bit_select_s']+n['data_zero_mask_s'],n['extra_accumulator_feedback_mux_s'])
    result_select=n['add_sub_result_select_s']+n['accumulator_keep_s']
    add=max(period,operand+n['extra_25bit_adder_s']+result_select+n['signed_capture_s'])
    subtract=max(period,operand+n['signed_correction_s']+result_select+n['signed_capture_s'])
    verify=max(period,n['verify_target_select_s']+n['verify_byte_compare_s']+n['verify_fail_reduce_s']+n['verify_sticky_or_s']+n['verify_status_capture_s'])
    case_combo=operand+max(n['extra_25bit_adder_s'],n['signed_correction_s'])+result_select
    checks.append(check('case_connected_MAC_halfcycle',case_combo<=period/2,{'case_combinational_s':case_combo,'halfcycle_s':period/2,'group_decode_is_in_series':True}))
    stream=[stage('input_admission',io,math.ceil(K*8/p['input_port_bits']),'service_policy',['DESIGN','NATIVE'],'128bit localport/full inputregister','Localportbeats including physicalDFFcapture','no offmacrotransport'),
      stage('result_clear',max(period,n['state_clear_s']),1,'service_policy',['DESIGN'],'400bit resultregister','Synchronouszero init of all16outputs','no phantomresultpayload'),
      stage('input_row_select',rowpick,K,'native_circuit',['NATIVE'],'inputrowmux/decoder/8bitrowregister','Select/capture onebyte perrow','not8freeinputports',clock='onefullclockslotincludingnativeDFFcapture'),
      stage('binary_row_read_groups',read,K*groups,'adapter',['NATIVE','RCMODEL'],'arrayWL/MUX/64SAs/64references/128prechargebranches','AllWL/refOFF,addressandcolumnselect/precharge;matcheddata/refenablewithfiniteskew;coupledRC;nativeSAlatchthenbothrelease','excludesidle15bitnativearithmetic; originalconstantDeltaItiming replaced'),
      stage('weight_capture',max(period,n['weight_keep_s']+n['weight_hold_capture_s']),K*groups,'native_circuit',['NATIVE'],'128bitweighthold, selected64bits/group','Holdcomplete row through8inputbits','no matrixshadow',clock='onefullclockslotincludingnativeDFFcapture'),
      stage('positive_bit_add',add,K*groups*7,'adapter',['NATIVE','DESIGN'],'8parallel25bitadder+shift/feedbackMUX+16outputholds','Sevenpositiveinputbits;inputbitselect/zero-mask,signextension,shiftMUX,adder,result/holdMUX,captureeachgroup inonelegalclockslot','native15bitadder/subtractoridle'),
      stage('sign_bit_subtract',subtract,K*groups,'adapter',['NATIVE','DESIGN'],'8parallel25bitsubtract+shift/feedbackMUX+16outputholds','Inputbitselect/zero-mask;inputsignbit subtract weight<<7,result/holdMUX,captureinonelegalclockslot','no additionalmultiplyunit')]
    batches=K*p['write_mux']
    resident=[stage('state_initialize',max(period,n['state_clear_s']),1,'adapter',['NATIVE','DESIGN'],'realoutput/status/retryclear gates','Resetarbitrarypriorflags beforefirstprogram/verify','notfreeinitialzero'),
      stage('target_admission',target_io,K*math.ceil(p['cols']/p['resident_port_bits']),'service_policy',['DESIGN','NATIVE'],'128bittargetbuffer/localport','Allrowtargets held throughRESET/SET/readback','no same-dataskip'),
      stage('write_WL_select',n['write_WL_select_one_s'],K,'native_circuit',['NATIVE'],'selectedphysicalWL','OneWLselection held throughoutrowprogram','excludescolumnbatches'),
      stage('program_engine_mask_admission',max(period,n['program_target_select_s']+n['program_target_mask_logic_s']),2*batches,'service_policy',['DESIGN'],'16bitcurrent-engine enablemask/128pertarget gates','Selectstabletargetmask and latchbeforeeachRESET/SETslot; fixedsource-interfaceoneclockcontract','notmaterialpulse; analogcurrentdriverreadiness remainscondition'),
      stage('write_column_select',n['write_column_decoder_one_batch_s'],2*batches,'native_circuit',['NATIVE'],'16lanes/column decoder','Onecolumn batch select perRESETorSETreservedslot','nativewriteMuxmultiplicity already divided'),
      stage('write_route_setup_release',n['write_column_driver_one_edge_s'],4*batches,'adapter',['NATIVE','DESIGN'],'Native-compatible selectedrouteTG load','Setup and release for each of two direction waveforms;4edges perphysicalbatch','notPCMcurrentwaveform/tail; no nativezero-writepulse used'),
      stage('RESET_waveform',p['reset_waveform_s'],batches,'external_primitive',['PCM-V5-01'],'16externallyrated.5mAcurrentlanes/8mAreturn','FullsourcecharacterizedRESETcurrentwaveform service underdeclarededge/quenchcondition','selection andfinalreadback excluded'),
      stage('SET_waveform_reserved',p['set_waveform_s'],batches,'external_primitive',['PCM-V5-01'],'16externallyrated.2mAcurrentlanes,targetbitmask','Maskedtarget-oneSET;allbatchslots reserved fordata-independentcompletecoverboundary','no inventedretryoradditionalSETtail'),
      stage('verify_read_groups',read,K*groups,'adapter',['NATIVE','RCMODEL'],'Samearray/64SAs/referencebranches','Finalbinaryreadbackofeverybitafterbothdirections','notperpulseverifyorresistancewindowmeasurement'),
      stage('verify_target_compare',verify,K*groups,'adapter',['NATIVE'],'8bytecomparators/failtree/stickyDFF','All64bitspergroupcomparetarget and retainrowfailure','failure commitsnopayload'),
      stage('row_commit_status',max(period,n['state_clear_s']),K,'service_policy',['DESIGN','NATIVE'],'sticky/status/retrystate registers','Successfulrowcommit or terminateone-attemptservice;statusclearedfornextrow','no successprobability or secondpayload')]
    patterns=[('zero',[0]*K,[[0]*N for _ in range(K)]),('extreme',[-128]*K,[[-128]*N for _ in range(K)]),
      ('mixed',[i%256-128 for i in range(K)],[[((i*31+j*17)%256)-128 for j in range(N)] for i in range(K)]),
      ('cancel',[127 if i%2 else -127 for i in range(K)],[[127]*N for _ in range(K)])]
    vectors=[]
    for name,x,w in patterns:
        actual=serial_mac(x,w);expected=[sum(x[i]*w[i][j] for i in range(K)) for j in range(N)]
        vectors.append(dict(name=name,matches=actual==expected,max_abs=max(map(abs,actual))))
    checks.append(check('signed_mapping',all(x['matches'] for x in vectors),vectors))
    ok=verify_binary_readback([0,1]*64,[0,1]*64);bad=verify_binary_readback([0,1]*64,[1,1]*64)
    life=nominal_full_cover_lifecycle(K,N,write_lanes);fault=nominal_full_cover_lifecycle(K,N,write_lanes,(K//2,7))
    checks.append(check('full_cover_lifecycle',life['verified_bits']==K*N*8 and life['reset_batches']==batches and fault['payload_Byte']==0,{'accepted':life,'failed':fault}))
    checks.append(check('failed_verify_no_payload',ok['payload_committed'] and not bad['payload_committed'],bad))
    checks.append(check('resident_high_voltage_return_port',False,'SourcePCMcurrentpulse does not establishpost-programBLvoltage or qualifiedHVreturn/readisolation; lowvoltage nativeTG cannot claimthis role.',critical=False))
    stream_total=sum(x['duration_s']*x['count'] for x in stream)
    return dict(status='blocked' if all(c['passed'] for c in checks if c['critical']) else 'infeasible',qualification='Read-chain candidate only; resident blocked pending ratedHVreturn/isolation port',conditions=conditions,
       program_outcome='blocked',scheduling='serial_nonoverlap',physical_checks=checks,resources=resources,stream_stages=stream,resident_stages=[],partial_resident_stages=resident,partial_stream_rho_MB_s=K/stream_total/1e6,blocked_stage='post_program_HV_return_and_read_isolation',
       counts=cnt,reference_network=ref,digital_vectors=vectors,verify_failure_probe=bad,full_cover_state_diagnostic=life,failed_full_cover_state_diagnostic=fault,
       primitive_scope_open_conditions=['Publishedwidths do not separatelyresolveedges/cooling; source-equivalentterminalwaveform completion required.','Current-source compliance andread-disturb are statedconditions, not inferredfromlowreadR.'],
       read_phase_breakdown_s=dict(address=address,column_selection=select,precharge=pre,WL_enable_setup=wl_setup,reference_isolation_edge=refedge,precharge_release=n['precharge_control_s'],develop=ref['develop_s'],sense_enable=period,WL_release=wl_release,one_group_total=read),
       event_order='Eachrow: admission, WLselect;8RESETbatches;8maskedSETslots;2verifyread/comparegroups;commit. Streaming:rowinput/select,2weightread/capturegroups,8inputbits×2outputgroups;releaseweightrow.')
