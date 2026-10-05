"""Vertical-AND FeFET finite model-reference service; case-owned adapter."""
import math
from fenor_model import ports,sense

def prepare_components(resolved):
 p=resolved['resolved_parameters'];q=ports(p)
 front={'point_eligibility':'probe_only','front_end':'case_terminal_ports','identity':resolved['input']['implementation_id']+' oneof32physicalparallelunits','frontend_identity':'4layerANDstate-dependentI-V andsharedBL/SL;nativearrayperipheryonly','source_ids':['FENOR02','PORT','EKV'],'applicability':'Negativegate/zero-resetandactivebiasprovidedbyexplicitcaseport;notnativepositivegate','operating_states':{'four_layer_high_A':q['read_high_A'],'four_layer_low_A':q['read_low_A']},
 'parameters':{'technology_nm':p['technology_nm'],'temperature_K':p['temperature_K'],'rows':1,'cols':p['physical_cols'],'layers':p['layers'],'read_mux':p['read_mux'],'selected_gate_V':p['selected_gate_V'],'unselected_gate_V':p['unselected_gate_V'],'drain_rail_V':.2,'source_rail_V':0.,'mux_target_ohm':p['mux_target_ohm'],'sense_threshold_V':p['sense_threshold_V'],'clock_Hz':p['clock_Hz'],'precharge_voltage_V':.2,**{k:p[k] for k in ('gate_driver_width_F','precharge_width_F','reference_switch_target_ohm','precharge_error_fraction')}},
 'terminal_ports':{'actual_gate_load_F':q['gate_C_each_WL_F'],'actual_BL_load_F':q['BL_C_F'],'actual_SL_load_F':q['SL_C_F'],'sense_current_high_A':q['read_high_A'],'sense_current_low_A':q['read_low_A']}}
 l=resolved['input']['logical']
 d={'identity':resolved['input']['implementation_id']+' 32rowtile digital bank','point_eligibility':'component_only','parameters':{'technology_nm':p['technology_nm'],'temperature_K':p['temperature_K'],'logical_K':l['K'],'logical_N':l['N'],'mac_lanes':p['mac_lanes'],'accumulator_bits':p['accumulator_bits'],'weight_hold_rows':p['lateral_lanes'],'weight_hold_outputs':l['N'],'weight_capture_bits':p['lateral_lanes']*p['physical_cols']//p['read_mux'],**{k:p[k] for k in ('input_port_bits','resident_port_bits','program_lanes','clock_Hz','operand_route_cap_F','program_control_cap_F')}}}
 return {'frontend':{'kind':'threshold','request':front},'digital':{'kind':'digital','request':d}}

def st(i,t,c,kind,ids,r,inside,outside):
 z={'id':i,'duration_s':t,'count':int(c),'source_class':kind,'source_ids':ids,'resources':r,'includes':inside,'excludes':outside}
 if kind=='native_circuit':z.update(native_return_unit='seconds',included_internal_clock_phases='Eachcapture/MACusesonecompletelegalperiod;nativeSApre/outputphasesassignedonce')
 return z

def lifecycle(K,N,lanes,inject_failure=False):
 # Actualsimulatedcellstate, not a hardwaregolden shadow. Onlyonetargetrow
 # is acceptedandheldwhilethetwo fullpulsesandreadbackexecute.
 bits=8*N;state=[(i*17+i//5)%2 for i in range(K*bits)];seen=set();success=True
 for r in range(K):
  layer,lane=divmod(r,lanes);base=(layer*lanes+lane)*bits
  target=[(r*31+j*17+33)%256 for j in range(N)]
  for b in range(bits):state[base+b]=0
  for j,w in enumerate(target):
   for b in range(8):state[base+j*8+b]=(w>>b)&1;seen.add(base+j*8+b)
  if inject_failure and r==K//2:state[base+3]^=1
  actual=[sum(state[base+j*8+b]<<b for b in range(8)) for j in range(N)]
  success=success and actual==target
 return {'successful':success,'covered_bits':len(seen),'physical_state_bits':len(state),
   'payload_bytes':K*N if success else 0,'layers':K//lanes,'lanes':lanes,
   'readback_scope':'wholelayer4096physicalbits,then128bittargetrowcompare;nocorrectionfromtruth'}

def arithmetic_vectors(K,N):
 cases=[('zero',[0]*K),('negative_extreme',[-128]*K),('positive_extreme',[127]*K),('mixed',[i%256-128 for i in range(K)]),('isolate_group_boundary',[1 if i in (31,32,63,64) else 0 for i in range(K)])]
 out=[]
 for name,x in cases:
  w=[[(i*31+j*17+33)%256-128 for j in range(N)] for i in range(K)];acc=[0]*N
  for layer in range(K//32):
   # Layerisreadintothe32rowtile; actual32parallelreadpaths do not create
   # a free32inputcompute tree. DigitalrowMACremainsexplicit.
   tile=w[layer*32:(layer+1)*32]
   for i,row in enumerate(tile):
    xr=x[layer*32+i]
    for bit in range(8):
     for col in range(N):acc[col]+=((xr&255)>>bit&1)*(row[col]<<bit)*(-1 if bit==7 else 1)
  expected=[sum(x[i]*w[i][j] for i in range(K)) for j in range(N)]
  out.append({'name':name,'passed':acc==expected,'min':min(acc),'max':max(acc)})
 return out

def evaluate(resolved,native):
 p=resolved['resolved_parameters'];n=native['frontend'];d=native['digital'];l=resolved['input']['logical'];K,N=l['K'],l['N'];P=1/p['clock_Hz'];q=ports(p);ele=sense(p,n);L=p['layers'];lanes=p['lateral_lanes'];bits=p['physical_cols'];totalSA=lanes*int(n['native_sense_count'])
 align=lambda t:max(P,math.ceil((t-1e-18)/P)*P)
 # Externalzero-park hasreal32FNMOS/node andonebuffer/lane. It remainsactive
 # throughHVmodeentry;10nscontrol+nativeRCfitinsideexistingSAprechargephase.
 Wreset=32*p['technology_nm']*1e-9;vdd=n['actual_native_gate_rail_V'];vth=n['native_vth_V'];beta=2*Wreset*n['native_Ion_N_A_per_m']/(vdd-vth)**2
 resetR=1/(beta*(vdd-vth));resetRC=resetR*ele['C_each_node_F']*math.log(.3/p['reset_residual_V'])
 follower_peak=.5*ele['beta_A_per_V2']*(p['follower_gate_V']-ele['effective_vth_V'])**2
 reset_drop=follower_peak*resetR
 pre=max(n['native_sense_control_s']/2,p['HV_control_allowance_s']+resetRC)
 readraw=pre+n['native_select_s']+n['native_mux_select_s']+q['HV_gate_transition_s']+p['read_pulse_s']+n['native_sense_control_s']/2+q['HV_gate_transition_s']+resetRC
 front=align(readraw)
 clear=align(d['state_clear_s']);capture=align(d['weight_hold_capture_s']);row_select=align(d['input_row_select_s']+d['input_row_capture_s'])
 mac=align(d['digital_mac_comb_s']+d['signed_capture_s'])
 program=align(2*q['HV_gate_transition_s']+p['program_pulse_s']+d['program_target_select_s']+d['program_target_mask_logic_s'])
 compare=align(d['digital_verify_comb_s']+d['verify_status_capture_s']);target=align(d['target_hold_capture_s'])
 stream=[st('input_admission',P,math.ceil(K*8/p['input_port_bits']),'native_circuit',['NATIVE'],'128bitport/inputhold1024bits','128Blogicalvectoronce','nooffdomainDRAM'),
  st('stream_clear',clear,1,'native_circuit',['NATIVE'],'nativeclearandresult/statushold','oldoutput/statusclear','nocellstatechange'),
  st('layer_read',front,L*p['read_mux'],'adapter',['NATIVE','PORT','SKY','FENOR02'],'32parallelunits×128SA/ref,oneactiveof4layers','nativeinternalprecharge,actualzero-park,HVisolation/negativegate/currentbias,20nsfinitefront,nativeSAoutput,earlylatchedhold,release','no4xlayerthroughput;noold20/40/80nsslots'),
  st('tile_capture',capture,L*p['read_mux'],'native_circuit',['NATIVE'],'4096bit32rowtilehold','physicalSAoutputstolocaltilehold','nofull16384bitshadow'),
  st('input_weight_row_select',row_select,K,'native_circuit',['NATIVE'],'128inputrowselect/32weightrowselect','oneinputrowheldfor8bitupdates','noreloadingpayload'),
  st('signed_MAC',mac,K*8,'native_circuit',['NATIVE'],'16lane25bitadd/sub/shift','8inputbitsandactualsignedweightmapping','notfree32inputaddertree'),
  st('output_ready',P,1,'service_policy',['DESIGN'],'resultstatus','all16resultsheld','nooutputtransport')]
 resident=[st('resident_clear',clear,1,'native_circuit',['NATIVE'],'target/status/retry','clearpriorcontrol','noterase'),
  st('target_ingress',target,K,'native_circuit',['NATIVE'],'128bittargethold','one16weightrowatatime','nofullmatrixpreload'),
  st('row_reset',program,K,'external_primitive',['FENOR02','SKY'],'128targetcellHVports,allothersinhibit','full−2V20nsbinaryreset+realHVcontrol/settle','notRRAMcurrentwrite'),
  st('row_program',program,K,'external_primitive',['FENOR02','SKY'],'same128targetports,bitmasked','+2V20nssettarget1,inhibit0 andallotherlateralrows','nooldstatepayloadskip'),
  st('verify_layer_read',front,K*p['read_mux'],'adapter',['NATIVE','PORT','SKY','FENOR02'],'4096physicalbitsreadpereachlogicalrowverification','wholelayerreadincludingallfourlayerloads','not128bitfreeisolatedsense'),
  st('verify_capture',capture,K*p['read_mux'],'native_circuit',['NATIVE'],'4096bittilehold','readallphysicalstateswhiletarget128bitsretained','notargetshadow'),
  st('verify_compare',compare,K,'native_circuit',['NATIVE'],'rowselect+16bytecompare/status','targetphysicalrowequalslogical128bits;failedpayload0','nostatisticalWER'),
  st('row_commit',P,K,'service_policy',['DESIGN'],'explicitrowaddress/progress','advanceonlyaftercompletewrite/verify','nofreetrainingupdate'),
  st('matrix_ready',P,1,'service_policy',['DESIGN'],'matrixstatus','2048Bcorrectlyloaded/readsafe','noextraencodedpayload')]
 life=lifecycle(K,N,lanes);failure=lifecycle(K,N,lanes,True);vectors=arithmetic_vectors(K,N)
 checks=[]
 def ck(i,ok,e):checks.append({'id':i,'passed':bool(ok),'critical':True,'evidence':e})
 ck('whole_state_lifecycle',life['successful'] and life['covered_bits']==K*N*8 and failure['payload_bytes']==0 and all(v['passed'] for v in vectors),{'success':life,'failure':failure,'vectors':vectors})
 ck('four_layer_binary_margin',ele['feasible'],ele)
 ck('subcoercive_read_field',ele['read_domain_field_bound_V']<=p['qualified_read_field_V'],{'maximum_Vgc_V':ele['read_domain_field_bound_V'],'finite_qualification_V':p['qualified_read_field_V'],'conditional_exposure_s':p['read_pulse_s']+2*q['HV_gate_transition_s']})
 ck('one_layer_not_parallel_multiplier',n['active_layer_count']==1 and L*lanes==K and n['capacity_cells']*lanes==K*N*8,{'active_layers':n['active_layer_count'],'nativeunitcells':n['capacity_cells'],'parallel_lateral_units':lanes})
 ck('active_bias_supply',2*totalSA*follower_peak<=p['local_bias_supply_limit_A'],{'peak_A':2*totalSA*follower_peak,'limit_A':p['local_bias_supply_limit_A']})
 ck('zero_park_residual',reset_drop<p['reset_residual_V'],{'I_timesR_V':reset_drop,'allowed_V':p['reset_residual_V'],'resetRC_s':resetRC})
 ck('full_cover_and_sign',K*N*8==L*lanes*bits and d['weight_hold_bits']==lanes*bits and d['target_hold_bits']==128,{'logical_bytes':K*N,'physical_bits':L*lanes*bits,'target_bits':d['target_hold_bits'],'tile_hold_bits':d['weight_hold_bits']})
 ck('native_legal_clock',d['digital_clock_budget_satisfied']==1,{'required_s':d['digital_halfcycle_min_period_s'],'actual_s':P})
 ck('bounded_HV_voltage',p['program_voltage_V']==2 and p['layers']==4,{'WL_V':[-4/3,4/3],'BL_SL_V':[-2/3,2/3],'gate_control_V':[-2/3,3.],'rated_VGS_V':5.5,'rated_VDS_V':11.,'qualification':'isolatedwellsandfiniteleveltranslatedportassumed,notpositiveportmerelyrenamed'})
 resources={'logical_payload_bytes':K*N,'physical_cells':L*lanes*bits,'active_layers':1,'lateral_parallel_lanes':lanes,'data_SA':totalSA,'reference_SA_branches':totalSA,'source_followers':2*totalSA,'source_follower_width_m':ele['nativeW_m'],'source_follower_L_over_native':p['follower_length_ratio'],'zero_park_NMOS':2*totalSA,'array_parked_by_existing_HV_zero_drivers':lanes*bits,'park_width_m':Wreset,'local_park_buffers':lanes,'HV_read_isolation_FETs':lanes*bits,'HV_BL_SL_program_ports':lanes*bits,'HV_WL_ports':L*lanes,'simultaneous_program_bits':bits,'native_digital':d,'native_frontend_unit':n,'array_port':{k:v for k,v in q.items() if k!='device_model'},'extra_reference_matching_cap_F_each':ele['C_each_node_F'],'whole_matrix_shadow_bits':0,'native_unused_hold_bits':lanes*n['native_hold_bits'],'native_area_qualification':'partialnativearea;compactHV/follower/passivecaplayoutnotfullPPA;notanequal-areafabricatedmacro'}
 return {'status':'conditional','program_outcome':'success' if life['successful'] else 'failed','scheduling':'serial_nonoverlap','qualification':'finitefour-layerANDmodelreference,binarysenseconditional,exactsignedINT8digital',
  'physical_checks':checks,'resources':resources,'stream_stages':stream,'resident_stages':resident,
  'external_gate_port':{'qualified':True,'source_ids':['SKY','PORT','FENOR02'],'domain':'±1.333VWL/±.667VBL_SL,isolatedwellbodyrails;SKY130fixedgeometry,currentandC+8nsconditionalcontrolallowance','stage_ids':['layer_read','row_reset','row_program','verify_layer_read']},
  'diagnostics':{'state_lifecycle':life,'failed_lifecycle':failure,'arithmetic_vectors':vectors,'sense':ele,'stage_read_raw_s':readraw,'stage_read_clock_s':front,'program_slot_s':program,'reset_park_s':resetRC,'counts':{'layer_reads_stream':L*p['read_mux'],'MAC_updates':K*8,'program_pulses':K*2,'verify_physical_reads':K*totalSA*p['read_mux'],'logical_byte_compares':K*N}},
  'conditions':['FourlayerverticalANDand32lateralpaths retained;source32x32prototypeisnotthisN16logicalmacro.',
   'NativeMOSsource-followerport usesIon/width/Vthandexplicitbodyallowance/longchannelW/L;nominalconditionalcircuitmodel,notPDKcalibration.',
   'SameSLHZO20nsprogramandreadpulse source;finiteedgesmakebiasexposureupto~39ns below2Vw/3 field. Repeatedoperation/offsetqualification is acondition,notproved10year/yieldguarantee.',
   'SKY130bipolarHVport is a sourcedfixed-sizecurrent/C/rated-domainblock withqualifiedisolatedwellsand8nscontrolallowance;negativelevelshiftnottransistor-implementedorclaimedmeasured. Stablebipolarrails/startupexcluded.',
   'SourceVdsnotreported;0.1Vcurrentfit/continuousEKVparametersareexplicitengineeringmodelreference,withothergate/stateandphysical-limitchecks.',
   'NativeVSA is abstractthresholdlatch;5mVsenseplus2mVremainingerrorcondition. Earlyresultheldwhilearraybiasreleased;outputphasecountedonce. NotENOB/BER/STA.',
   'Threefinite±50mVstatepackagescanhaveidenticalrateswhen20nspulseanddigitalclockdominate;notstatisticalbounds orartificiallyseparatedpoints.']}
