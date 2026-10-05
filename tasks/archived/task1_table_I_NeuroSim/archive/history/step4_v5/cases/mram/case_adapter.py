"""MRAM model-reference adapter. Does not write shared code or import old results."""
from pathlib import Path
import importlib.util, math
_sp=importlib.util.spec_from_file_location('v5_mram_umem',Path(__file__).with_name('umem_port.py'))
u=importlib.util.module_from_spec(_sp);_sp.loader.exec_module(u)

def local_return(p):return p['source_strap_resistivity_ohm_m']*(p['rows']*p['cell_pitch_y_m'])/(p['source_strap_width_m']*p['source_strap_thickness_m'])
def return_cap(p):
 length=p['rows']*p['cell_pitch_y_m'];return 8.8541878128e-12*p['source_dielectric_relative_permittivity']*p['source_strap_width_m']*length/p['source_BL_spacing_m']+p['source_fringe_F_per_m']*length
def strap(p,n):return p['source_strap_resistivity_ohm_m']*n['array_row_m']/(p['source_strap_width_m']*p['source_strap_thickness_m'])
def model(p):return {k:p['umem_'+k] for k in u.PARAMETERS}
def prepare(resolved):
 p=resolved['resolved_parameters'];m=model(p)
 fields=('technology_nm','device_node_nm','temperature_K','rows','cols','read_mux','write_mux','access_resistance_ohm','cell_pitch_x_m','cell_pitch_y_m','read_voltage_V','access_voltage_V','write_port_voltage_V','wire_ohm_per_m','clock_Hz','extra_column_cap_F','sense_threshold_V','precharge_width_F','precharge_error_fraction','input_port_bits','resident_port_bits','read_mux_IR_fraction','write_mux_target_ohm','write_current_A')
 v={k:p[k] for k in fields};v['extra_column_cap_F']+=return_cap(p);v.update(resistance_on_ohm=u.resistance(p['read_voltage_V'],1,m),resistance_off_ohm=u.resistance(p['read_voltage_V'],-1,m))
 return {'identity':resolved['input']['implementation_id'],'point_eligibility':'probe_only','parameters':v,'limitations':['UMEM deterministic model-reference, not a measured macro or WER model','Static native resistance used only for initialization; real development solved by nonlinear transistor/MTJ discharge']}

def native_mos(n):
 ov=n['actual_tech_vdd_V']-n['actual_tech_vth_V'];ion_n=n['actual_tech_Ion_N_A_per_m']
 ion_p=(n['write_mux_native_Ion_A']-ion_n*n['write_mux_width_N_m'])/n['write_mux_width_P_m']
 return {'vdd':n['actual_tech_vdd_V'],'vth':n['actual_tech_vth_V'],'beta_access':2*n['actual_access_Ion_at_native_bias_A']/ov**2,'ion_n_per_m':ion_n,'ion_p_per_m':ion_p,'beta_read_n':2*ion_n*n['actual_mux_n_m']/ov**2,'beta_read_p':2*ion_p*n['actual_mux_p_m']/ov**2,'beta_write_n':2*ion_n*n['write_mux_width_N_m']/ov**2,'beta_write_p':2*ion_p*n['write_mux_width_P_m']/ov**2,'beta_reference_n':4*ion_n*n['actual_mux_n_m']/ov**2,'native_effective_R_multiplier': n['input_access_ohm']*n['actual_access_Ion_at_native_bias_A']/n['actual_tech_vdd_V']}
def bias_port(p,n,m,write=False):
 q=native_mos(n);which='write' if write else 'read'
 return u.BiasPort(m,q['vdd'],q['vth'],q['beta_access'],q['beta_'+which+'_n'],q['beta_'+which+'_p'],n['array_col_res_ohm']+local_return(p),strap(p,n),int(p['write_lanes'] if write else p['cols']),n['array_col_res_ohm']+local_return(p),write,None if write else p['read_voltage_V']*(1+p['precharge_error_fraction']))

def transient_reference(p,n,m,initial_states=(1.,-1.)):
 cap=n['sa_effective_node_cap_F'];v=p['read_voltage_V'];need=p['sense_threshold_V']+p['sense_offset_budget_V'];eps=p['precharge_error_fraction'];skew=p['reference_enable_skew_bound_s']
 sp,sm=initial_states;vp=v*(1+eps);vm=v*(1-eps);step=p['read_integrator_step_s'];best=(-1,None);cross=None;capture=None;traj=[]
 port=bias_port(p,n,m);port_ap=bias_port(p,n,m);port_ap.ret=0.
 q=native_mos(n);R=p['reference_resistance_ohm']+local_return(p)
 def rf(vx):return -port.resistive_reference_current(max(vx,0),R,q['beta_reference_n'],int(n['native_sa_count']),strap(p,n))/cap
 def advance_ref(vx,h):
  a=rf(vx);b=rf(vx+a*h/2);c=rf(vx+b*h/2);d=rf(vx+c*h);return vx+h*(a+2*b+2*c+d)/6
 early=v;late=v;nominal=v
 for _ in range(max(1,math.ceil(skew/step))):early=advance_ref(early,skew/max(1,math.ceil(skew/step)))
 def f(vx,sx,which):
  ix=which(vx,sx)[0];return -ix/cap,u.rhs(sx,ix,m)
 for j in range(1,10001):
  t=j*step
  def stepstate(vx,sx,which):
   a,b=f(vx,sx,which);c,d=f(vx+a*step/2,sx+b*step/2,which);e,g=f(vx+c*step/2,sx+d*step/2,which);h,i=f(vx+e*step,sx+g*step,which)
   return vx+step*(a+2*c+2*e+h)/6,sx+step*(b+2*d+2*g+i)/6
  vp,sp=stepstate(vp,sp,port);vm,sm=stepstate(vm,sm,port_ap)
  early=advance_ref(early,step);nominal=advance_ref(nominal,step)
  if t>skew:late=advance_ref(late,min(step,t-skew))
  margin=min(early*(1-eps)-vp,vm-late*(1+eps))
  if margin>best[0]:best=(margin,t)
  if cross is None and margin>=need:cross=t;capture={'V_P_V':vp,'V_AP_V':vm,'V_ref_V':nominal,'state_P':sp,'state_AP':sm,'P_worst_margin_V':early*(1-eps)-vp,'AP_worst_margin_V':vm-late*(1+eps)}
  if j%100==0:traj.append([t,vp,vm,nominal,margin,sp,sm])
  if cross and t>max(4*cross,10e-9):break
 return {'capture':capture,'cap_each_F':cap,'threshold_plus_offset_V':need,'develop_s':cross,'max_worst_margin_V':best[0],'max_margin_time_s':best[1],'final_states':[sp,sm],'trace':traj,'matched_reference_branches_per_bank':int(n['native_sa_count']),'reference_resistor_only_ohm':R,'reference_switch':'actualN-onlyIon/width/Vthbranch;notconstantnativeRon','data_switch':'actualcomplementaryTGwithVGS/VDS;notconstantnativeRon','precharge_error_fraction':eps,'step_enable_skew_bound_s':skew,'max_shared_source_drop_V':port.max_drop,'source_contexts':{'P':'all64physicaldata columns heldatmaximuminitialVread*(1+prechargeerror),strongestON,includingunsensedwithoutreadMUX;constantIRupperbounddoesnotshrinkwithvictimVP','AP':'zero-return-dropconservativelowerboundmaximizesAPdischarge;notadifferenthardware','reference':'samephysicalquietreturn32referencebranchesandmatchedCforbothstates'}}

def stage(id,t,count,kind,source,resources,includes,excludes):
 d={'id':id,'duration_s':t,'count':int(count),'source_class':kind,'source_ids':source,'resources':resources,'includes':includes,'excludes':excludes}
 if kind=='native_circuit':d.update(native_return_unit='seconds',included_internal_clock_phases='Explicit field only; VSA precharge/enable separated by adapter')
 if t==0:d['zero_reason']='No operation in this declared boundary'
 return d

def evaluate(resolved,n):
 p=resolved['resolved_parameters'];m=model(p);checks=[];period=1/p['clock_Hz'];banks=int(p['banks']);K=resolved['input']['logical']['K'];N=resolved['input']['logical']['N']
 def check(id,ok,evidence):checks.append({'id':id,'passed':bool(ok),'critical':True,'evidence':evidence})
 check('one_authority_dimensions',K==p['rows'] and N*8==banks*p['cols'],'K rows; eight binary cells per signed weight; banks disjoint output groups')
 ref_parasitic=n['reference_switch_drain_F']+n['precharge_added_drain_cap_F']+(n['sa_effective_node_cap_F']-n['adapted_sa_input_cap_F'])
 matching_cap=n['sa_effective_node_cap_F']-ref_parasitic
 check('reference_isolation_and_matching',n['reference_isolation_count']==n['native_sa_count'] and matching_cap>=0,{'TG_count_per_bank':n['reference_isolation_count'],'TG_R_ohm':n['reference_switch_R_ohm'],'matching_cap_F_each':matching_cap,'lifecycle':'OFFduringprecharge;ONonlyduringdevelopment;nativeSAcapturesbeforedata/referenceOFF'})
 check('matched_reference_enable',n['reference_enable_load_match_feasible']==1,{'matched_cap_F':n['reference_enable_matching_cap_F'],'scope':'step-port nominalmatcheddata/referenceedge;no arbitrarilydifferentenabletimes'})
 check('write_route_compliance',n['write_mux_current_compliance']==1,{'actual_R_ohm':n['write_column_TG_ohm'],'rated_A':p['write_current_A'],'native_Ion_A':n['write_mux_native_Ion_A']})
 check('native_gate_bias',n['actual_access_bias_matches_native']==1,'Native gate bias equals requested access voltage')
 check('native_digital_timing',n['digital_clock_budget_satisfied']==1,{'period_s':period,'required_s':n['digital_halfcycle_min_period_s']})
 operand=n['group_select_s']+max(n['weight_group_select_s']+n['extra_shift_select_s']+n['extra_shifted_weight_mux_s']+n['data_zero_mask_s'],n['input_bit_select_s']+n['data_zero_mask_s'],n['extra_accumulator_feedback_mux_s'])
 connected=operand+max(n['extra_25bit_adder_s'],n['signed_correction_s'])+n['add_sub_result_select_s']+n['accumulator_keep_s']
 check('case_connected_MAC_halfcycle',connected<=period/2,{'combinational_s':connected,'halfcycle_s':period/2,'groupdecoder_in_series':True})
 rd=transient_reference(p,n,m)
 check('reference_reachable',rd['develop_s'] is not None,{'max_margin_V':rd['max_worst_margin_V'],'required_V':rd['threshold_plus_offset_V']})
 check('read_state_lifecycle',rd['final_states'][0]>.98 and rd['final_states'][1]<-.98,rd['final_states'])
 clear_slot=max(period,math.ceil(n['state_clear_s']/period)*period)
 check('physical_state_clear',n['state_clear_bits']>=n['signed_output_hold_bits'] and n['state_clear_s']>0,{'native_clear_s':n['state_clear_s'],'scheduled_s':clear_slot,'physical_bits_per_bank':n['state_clear_bits']})
 check('low_rail_precharge',n['precharge_bias_feasible']==1,{'headroom_V':n['precharge_headroom_V']})
 mos=bias_port(p,n,m,write=True)
 cal=native_mos(n)
 common_modes=[p['write_port_voltage_V']*j/200 for j in range(201)]
 tg_g=[cal['beta_write_n']*max(cal['vdd']-v-cal['vth'],0)+cal['beta_write_p']*max(v-cal['vth'],0) for v in common_modes]
 tg_bias_Rmax=1/min(tg_g)
 route_RC=math.log(1000)*(tg_bias_Rmax+n['array_col_res_ohm']+local_return(p)+p['write_lanes']*strap(p,n))*n['write_total_connected_cap_F']
 edge=max(p['minimum_edge_s'],n['write_column_driver_one_edge_s'],route_RC)
 pulses=[]
 # Both initial states, both required polarities: force every cell even if already target.
 for target in [-1,1]:
  voltage=-target*p['write_port_voltage_V']
  for initial in [-1,1]:
   pulse=u.pulse(initial,voltage,p['program_plateau_s'],p['access_resistance_ohm'],p['write_integrator_step_s'],0,False,m,mos)
   pulse['edge_each_s']=edge;pulse['waveform_s']=p['program_plateau_s']+2*edge;pulse['state_integration_scope']='Conservativeplateau-onlyafterelectricalsettling;edgecurrentnotusedtoforceearliersuccess'
   pulse.pop('trace');pulse['target_state']=target;pulses.append(pulse)
 check('all_write_endpoints',all(x['final_state']*x['target_state']>=p['accepted_state_magnitude'] and abs(x['final_state'])<=1.001 for x in pulses),pulses)
 # Verify with real worst final states from all initial/target transitions;
 # do not reset a partial state to an ideal endpoint before physical sensing.
 written=(min(x['final_state'] for x in pulses if x['target_state']==1),max(x['final_state'] for x in pulses if x['target_state']==-1))
 rd=transient_reference(p,n,m,written)
 check('actual_written_state_sense',rd['develop_s'] is not None,{'worst_final_states':written,'max_margin_V':rd['max_worst_margin_V'],'required_V':rd['threshold_plus_offset_V']})
 peak=max(x['max_current_A'] for x in pulses);active=int(p['write_lanes'])
 edge_charge_current=n['write_total_connected_cap_F']*p['write_port_voltage_V']/edge
 check('edge_current_and_settling',active*(peak+edge_charge_current)<=p['shared_write_current_limit_A'],{'dc_peak_perlane_A':peak,'capacitive_ramp_budget_perlane_A':edge_charge_current,'shared_required_A':active*(peak+edge_charge_current),'shared_rated_A':p['shared_write_current_limit_A'],'RC99p9_settle_s':route_RC,'counted_each_edge_s':edge,'TG_max_differential_R_ohm':tg_bias_Rmax,'meaning':'Boundedfinite-slewlocalpulseportcondition;notinstantaneousunlimitedrail'})
 edge_disturb=[]
 for st in [-1,1]:
  z=u.pulse(st,st*p['write_port_voltage_V'],2*edge,p['access_resistance_ohm'],min(p['write_integrator_step_s'],edge/30),0,False,m,mos);z.pop('trace');edge_disturb.append(z)
 check('finite_opposite_edge_no_state_loss',all(x['initial_state']*x['final_state']>0 and abs(x['final_state'])>=p['accepted_state_magnitude'] for x in edge_disturb),{'opposite_fullbias_s':2*edge,'cases':edge_disturb,'domain':'Finiteedgealignmentcondition;notarbitraryhalfselectduration'})
 check('write_driver_current',peak<n['actual_access_Ion_at_native_bias_A'] and peak<=p['write_current_A'] and active*peak<=p['shared_write_current_limit_A'],{'per_path_A':peak,'plateau_current_kind':'actualbias-resolvedMTJcurrent;100uAfieldisDCsizingconditionnotedgecurrentlimit','native_access_Ion_A':n['actual_access_Ion_at_native_bias_A'],'active_lanes':active,'shared_limit_A':p['shared_write_current_limit_A'],'source_degenerated_MOS_adapter':True,'source_strap_R_ohm':strap(p,n),'conservative_shared_drop_upper_V':active*peak*strap(p,n)})
 # Slow and strong direction use the same qualified plateau, hardware and rails.
 precharge_phase=max(period,n['precharge_external_RC_s']+n['precharge_control_s'])+n['sa_precharge_per_group_s']
 develop=rd['develop_s'] or 0.
 selection=max(n['WL_address_setup_s'],n['group_select_s']+n['native_mux_s'])
 enable=max(n['WL_enable_edge_only_s'],n['reference_isolation_edge_s']);release=max(n['WL_release_s'],n['reference_isolation_edge_s'])
 front_raw=selection+precharge_phase+n['precharge_control_s']+enable+develop+period+release
 front=math.ceil(front_raw/period)*period
 read_window=enable+develop+period+release
 read_mos=bias_port(p,n,m)
 read_stress=[]
 for source_case in ['maximum_return','zero_drop_lower_bound']:
  read_mos=bias_port(p,n,m)
  if source_case=='zero_drop_lower_bound':read_mos.ret=0.
  for initial in written:
   q=u.pulse(initial,p['read_voltage_V'],read_window,p['access_resistance_ohm'],p['write_integrator_step_s'],0,False,m,read_mos);q.pop('trace');q['source_context']=source_case;read_stress.append(q)
 check('full_WL_window_read_stability',all(x['final_state']*x['initial_state']>0 and p['accepted_state_magnitude']<=abs(x['final_state'])<=1.001 for x in read_stress),{'window_s':read_window,'conservative_constant_read_bias':'ActualpassiveBLdischarges;holdingfullbiasthroughentireWLenable/develop/SAoutput/releasewindowisstrongerreadstress','pulses':read_stress})
 groups=int(p['read_mux']);tiles=int(K*groups);write_batches=int(K*N*8/active)
 wp_setup_raw=max(n['write_WL_select_one_s'],n['write_column_decoder_one_batch_s'])
 wp_setup=math.ceil(wp_setup_raw/period)*period
 wave=2*(p['program_plateau_s']+2*edge)
 # Four waveform ramps already cover native column TG edge; never bill twice.
 wf=2*math.ceil((p['program_plateau_s']+2*edge)/period)*period
 verify_combo=n['verify_target_select_s']+n['verify_byte_compare_s']+n['verify_fail_reduce_s']+n['verify_sticky_or_s']
 verify_clocks=max(1,math.ceil((verify_combo+n['verify_status_capture_s'])/period))
 source=['U-MRAM','POLICY'];native=['MLP']
 stream=[stage('input_accept',period,math.ceil(K/p['input_port_bytes']),'service_policy',['POLICY'],'one input port','logicalinputbeats includingnative ingressfeedback/capturewithincheckedperiod','no external DRAM'),stage('clear_output_status',clear_slot,1,'native_circuit',native,'physical per-D clearANDs/globaldriver acrossall8bank result/status/retry','fullclockphysicalclearbeforefirstMAC;oldrequestdatacannotpersist','notfreeDFFreset'),stage('select_input_row',period,K,'native_circuit',native,'row selector and row hold','native row selector/capture within checked clock','no bank data read'),stage('physical_binary_frontend',front,tiles,'adapter',source+native,'8 disjoint banks;32 SA/data-reference pairs per bank','WL off and mux selection, external data/reference precharge, WL enable, nonlinear development, native decision latch/output phase','no native endpoint linear develop; no unsigned native arithmetic'),stage('capture_weight',period,tiles,'native_circuit',native,'32-bit weight hold per bank','fulllegalcaptureclockincludingnativeDFFhalfcycleandgroupkeep;tileheldthrough8inputbits','no whole-matrix shadow'),stage('eight_input_bit_updates',period,tiles*8,'native_circuit',native,'native input-bit selector, shifted weight mux, signed25bit add/sub and feedback holds','wired8-to25bitsignextensionfromweightHold;8bitserialupdates,sevenaddandoneinputsignsubtract;all32lanesparallel','no duplicate native short unsigned adder'),stage('output_ready_status',period,1,'service_policy',['POLICY'],'existingcontrollerstatus;64outputs alreadyinholds','finaloutput-readyflag afterlastupdate','no recaptureofalreadyheldresult')]
 resident=[stage('resident_state_clear',clear_slot,1,'native_circuit',native,'physicalresult/status/retryclear','initpriorstickyfailureandcontrolstatebeforefirstprogram/verify','doesnoteraseMTJdata'),stage('target_load',period,write_batches,'service_policy',['POLICY'],'32bit interface and native target hold','4logicalByte/batch ingressselect/capture+feedbackincludedinperiod','no encoding duplication'),stage('write_selection',wp_setup,write_batches,'native_circuit',native,'native WL/col decode','one selectedphysicalrow/group;zero-biasconditioningduringwholecontrolslotbeforewaveforms removespriorBLcharge','two direction driver edges separately'),stage('program_mask_select',period,2*write_batches,'native_circuit',native,'native targetgroupmux +maskgates','one stabletargetmask preparation beforeeachpolarity;otherbitsinhibited','no thermal/materialpulse'),stage('bidirectional_full_cover',wf,write_batches,'adapter',source+native,'32 active drivers; unselected bits inhibit; shared return rail','two source-degeneratedtrapezoids;eachram pincludesnativecolumnedge/lineRC;zerobiaswaitalignseachpolaritycompletiontonextcontrolclock','no old20/30ns accesses; no retry probability'),stage('verify_binary_frontend',front,write_batches,'adapter',source+native,'same physical reference/sense path, one bank at a time','read all32 programmedbits after final return','no payload'),stage('verify_capture',period,write_batches,'native_circuit',native,'existing32bitweight hold','fulllegalcaptureclockholdsensedbitsagainsttargets;nativehalfcycleisnotrepeatedserviceinterval','streaming idle'),stage('verify_compare_status',verify_clocks*period,write_batches,'native_circuit',native,'byte comparators/reduction/sticky status','compare all32bits then accept group; failure invalidates matrix','no hidden retry'),stage('matrix_publish',period,1,'service_policy',['POLICY'],'matrix status','publish only after allbitsaccepted','reference resistors are fixedhardware notprogrammed')]
 status='conditional' if all(x['passed'] for x in checks) else 'infeasible'
 return {'status':status,'qualification':'deterministic nonlinear STT model reference + binary read conditional on declared sense offset; exact local signed arithmetic; no WER/silicon claim','conditions':['UMEM1.0.1 electrode convention retained; its positive bias drives AP unlike displayed Carboni polarity.','65nmactualnativeN/Pwidth,Ion,Vthanchorsdefineoneconsistentbiasmodel;beta=2Ion/(VDD−Vth)^2. CACTIeffectiveRon isnotDCdifferentialR;onlynativearea/timingsizingusesit. Bodyeffect/velocitysaturationnotindependentlycalibrated.','Fixed12kΩ reference resistor and matched capacitor are explicit reference-design components; no reference resistance variation claimed.','SA resolves5mV with at most2mV offset/noise budget; this is model qualification, not measured comparator certification.','Data/referenceenableusesnativeequal-loadstep-portmodel;finite±100psresidualstepoffsetischecked,notmeasurementsorfulledgewaveformvalidation.', 'Native VSA decision is abstractly latched when threshold is reached; subsequent native clock phase is output-ready wait, not prolonged passive signal development. No transistor-level comparator regeneration/mismatch validation.', 'Room-temperature domain; read disturb assessed deterministically and fixed-positive lowbias is not Carboni experimentally qualified read policy.','Single128bitinputport broadcasts to8physicalbank-local inputholds;all8copiescountasresources,only64logicalBytesaspayload;portdrive/fanout8withinselected100ns islocalinterfacecondition.', 'Read/write mutually exclusive; one finite complete pulse pair and physical verify; failed target check produces no completed payload.'],'program_outcome':'success' if all(x['final_state']*x['target_state']>=p['accepted_state_magnitude'] for x in pulses) else 'failed','scheduling':'serial_nonoverlap','event_templates':{'stream':'admitfull64Bytevector;foreachrow:pickinput;foreachof2colgroups:read,capture,eightbitupdateswithwiredsignextension;thenpublish','resident':'foreachbank,row,colgroup:load4targetBytes,captureinwholeingressclock,select;mask0,pulse0+return+clockalign;mask1,pulse1+return+clockalign;readverify,capturefullclock,comparestatus;onlythenreusecurrenttargetgroup;publishafterallgroups','stage_ledger_semantics':'countsmeasuretheseinterleavedperrequesttemplates;notalltargetloadsbeforeservice;noextrashadow'},'physical_checks':checks,'resources':{'banks':banks,'data_cells':K*N*8,'reference_resistors':banks*int(n['native_sa_count']),'state_clear_bits_total':banks*int(n['state_clear_bits']),'state_clear_area_m2_total':banks*n['state_clear_area_m2'],'reference_resistance_ohm':p['reference_resistance_ohm'],'source_strap_R_ohm':strap(p,n),'source_local_return_R_ohm':local_return(p),'source_BL_coupling_F':return_cap(p),'source_return_column_count_per_bank':int(p['cols']+n['native_sa_count']),'separate_data_reference_straps_per_bank':2,'source_strap_geometry_m':{'length':n['array_row_m'],'width':p['source_strap_width_m'],'thickness':p['source_strap_thickness_m']},'read_electrically_selected_cells_per_bank':int(p['cols']),'read_active_source_policy':'All64selectedrowcellsboundsourcecurrentalthoughonly32SAoutputsconverted;upperboundusesno readMUX forALLbackgroundcells;selectedvictimretainsreadMUX;unobservedBLinitialVboundedbyVreadafterprogramreturn/priorpassivedischarge','source_current_envelope':'Self-consistentall-Pphysical-lane givesmaximumcurrentoverstate;fixedenvelopeusedforvictimstategivesconservativeIRbound;not probability.','quiet_reference_return':'samegeometryseparatequietreturn;32referencebranchcurrentincludedinreferenceequivalentR','matched_reference_cap_F_each':rd['cap_each_F'],'added_reference_matching_cap_F_each':matching_cap,'reference_isolation_TGs':banks*int(n['reference_isolation_count']),'reference_switch_R_ohm':n['reference_switch_R_ohm'],'reference_switch_area_m2_total':banks*n['reference_switch_area_m2'],'reference_control_area_m2_total':banks*n['reference_control_area_m2'],'physical_SAs':banks*int(n['native_sa_count']),'simultaneous_output_lanes':banks*int(n['extra_25bit_adder_lanes']),'write_lanes':active,'write_lanes_scope':'32 globally active lanes;one selected bank atatime;nativebankdriversinstalled but single shared programming domain','logical_write_group_bytes':active//8,'input_hold_bits_total':banks*int(n['input_hold_bits']),'input_hold_replication':'same64Bytevectorbroadcastto8countedbank-localholds;payloadonce;single128bitportmustdrivefanout8withintheactualcheckedperiod','target_hold_bits_total':banks*int(n['target_hold_bits']),'installed_bank_write_paths':banks*int(p['cols']/p['write_mux']),'program_route_TG_ohm':n['write_column_TG_ohm'],'program_current_rating_per_lane_A':p['write_current_A'],'weight_hold_bits':banks*int(n['weight_hold_bits']),'signed_output_hold_bits':banks*int(n['signed_output_hold_bits']),'full_matrix_shadow_bits':0,'physical_cell_pitch_m':[p['cell_pitch_x_m'],p['cell_pitch_y_m']],'reference_and_precharge':'each sense lane has a fixed-resistor matched-C reference and two low-rail precharge NMOS branches','area_qualification':'native data/periphery+precharge reported; fixed-resistor/matching-layout area is not signed off'},'stream_stages':stream,'resident_stages':resident,'diagnostics':{'read_reference':rd,'full_WL_read_stress':read_stress,'read_phases_s':{'physical_group_raw':front_raw,'clock_ready_group':front,'alignment_wait':front-front_raw,'mux_select':selection,'isolated_precharge':precharge_phase,'precharge_release':n['precharge_control_s'],'data_reference_enable':enable,'develop':develop,'native_decision_output_phase':period,'data_reference_release':release},'write_pulses':pulses,'mos_calibration':native_mos(n),'write_shared_drop_upper_V':mos.max_drop,'edge_s':edge,'edge_disturb':edge_disturb,'TG_differential_common_mode_probe':{'V':common_modes,'R_ohm':[1/g for g in tg_g]},'program_phase_timing_s':{'one_physical_waveform':p['program_plateau_s']+2*edge,'one_clock_ready_waveform':wf/2,'physical_select':wp_setup_raw,'clock_ready_select':wp_setup},'counts':{'stream_tiles':tiles,'input_bit_updates':tiles*8,'write_batches':write_batches,'two_polarities_per_batch':2,'verify_clocks_per_batch':verify_clocks},'native_aggregate_excluded':'native short unsigned adder/capture/subtractor not used; their resources remain present but service uses explicit25bit path'}}
