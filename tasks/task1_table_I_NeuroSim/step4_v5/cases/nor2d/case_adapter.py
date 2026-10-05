"""NOR two-part native boundary. Initial physical-port snapshot; no old access replay."""
import json,math
from pathlib import Path
from threshold_model import operating_point

def table():return json.loads(Path(__file__).with_name('transfer_samples.json').read_text())

def prepare_components(resolved):
 p=resolved['resolved_parameters'];op=operating_point(p,table());g=op['geometry']
 req={'identity':resolved['input']['implementation_id']+' three-terminal state frontend','point_eligibility':'probe_only','front_end':'case_terminal_ports','frontend_identity':'ESF1 threshold endpoints plus explicitly engineered physical-terminal network','source_ids':['NOR-04','MODEL','DESIGN'],'applicability':'300K;gate1.1..1.3V;drain .8..1V compactdomain;noRRAMwriting','operating_states':op,'parameters':{'technology_nm':p['technology_nm'],'temperature_K':p['temperature_K'],'rows':p['rows'],'cols':p['cols'],'layers':1,'read_mux':p['read_mux'],'selected_gate_V':p['read_gate_V'],'unselected_gate_V':0.,'drain_rail_V':p['read_drain_V'],'source_rail_V':0.,'mux_target_ohm':p['mux_target_ohm'],'sense_threshold_V':p['sense_threshold_V'],'clock_Hz':p['clock_Hz'],'precharge_voltage_V':p['read_drain_V'],**{k:p[k] for k in ('gate_driver_width_F','precharge_width_F','reference_switch_target_ohm','precharge_error_fraction')}},'terminal_ports':{'actual_gate_load_F':g['gate_load_F'],'actual_BL_load_F':g['BL_load_F'],'actual_SL_load_F':g['SL_load_F'],'sense_current_high_A':op['erased_slowest']['I_A'],'sense_current_low_A':op['programmed_fastest']['I_A']}}
 digital={'identity':resolved['input']['implementation_id']+' actual local digital service','point_eligibility':'component_only','parameters':{'technology_nm':p['technology_nm'],'temperature_K':p['temperature_K'],'logical_K':resolved['input']['logical']['K'],'logical_N':resolved['input']['logical']['N'],'mac_lanes':p['mac_lanes'],'accumulator_bits':p['accumulator_bits'],'weight_hold_rows':1,'weight_hold_outputs':resolved['input']['logical']['N'],'weight_capture_bits':p['cols']//p['read_mux'],'input_port_bits':p['input_port_bits'],'resident_port_bits':p['resident_port_bits'],'program_lanes':p['program_lanes'],'clock_Hz':p['clock_Hz'],'operand_route_cap_F':p['operand_route_cap_F'],'program_control_cap_F':p['program_control_cap_F']}}
 return {'frontend':{'kind':'threshold','request':req},'digital':{'kind':'digital','request':digital}}

def electrical_port(n):
 return {'vdd_V':n['actual_native_gate_rail_V'],'vth_V':n['native_vth_V'],'ion_N_A_per_m':n['native_Ion_N_A_per_m'],'ion_P_A_per_m':n['native_Ion_P_A_per_m'],'reference_off_current_upper_A':n['native_Ioff_N_A_per_m']*n['reference_TG_width_n_m']+n['native_Ioff_P_A_per_m']*n['reference_TG_width_p_m'],'mux_N_width_m':n['actual_mux_width_n_m'],'mux_P_width_m':n['actual_mux_width_p_m'],'reference_N_width_m':n['reference_TG_width_n_m'],'reference_P_width_m':n['reference_TG_width_p_m'],'reference_gate_N_cap_F':n['reference_TG_gate_n_F'],'reference_gate_P_cap_F':n['reference_TG_gate_p_F'],'reference_main_cap_F':n['reference_capacitor_node_total_F'],'reference_internal_cap_F':n['reference_TG_drain_each_side_F'],'reference_N_control_tau_s':n['reference_TG_N_gate_rise_tau_s'],'reference_P_control_tau_s':n['reference_TG_P_gate_fall_tau_s'],'reference_control_delay_s':n['gate_enable_control_s'],'reference_N_additional_delay_s':n['reference_TG_N_gate_delay_s'],'gate_P_width_m':n['gate_driver_width_p_m'],'gate_total_load_F':n['actual_gate_load_F']+n['gate_driver_output_cap_F'],'gate_control_delay_s':n['gate_enable_control_s']+n['gate_enable_NAND_s'],'data_BL_cap_F':n['actual_BL_load_F'],'data_SA_cap_F':n['native_sense_node_cap_F']-n['actual_BL_load_F'],'precharge_P_width_m':n['precharge_PMOS_width_m'],'precharge_output_cap_F':n['precharge_PMOS_drain_F'],'precharge_control_delay_s':n['precharge_control_s']}

def stage(ident,time,count,kind,source,resources,includes,excludes):
 s={'id':ident,'duration_s':time,'count':int(count),'source_class':kind,'source_ids':source,'resources':resources,'includes':includes,'excludes':excludes}
 if kind=='native_circuit':s.update(native_return_unit='seconds',included_internal_clock_phases='OnefulllegalclockslotincludescorrespondingnativeDFFhalfcycle;notdoublebilled')
 return s

def lifecycle(K,N,page,sector,fault=False):
 target=bytes((i*37+i//16+128)%256 for i in range(K*N));old=bytearray((255-i*53)%256 for i in range(sector))
 physical=bytearray([255]*sector);seen=set();pages=0
 for start in range(0,len(target),page):
  buffer=target[start:start+page]
  assert len(buffer)==page and start%page==0
  for j,b in enumerate(buffer):
   addr=start+j;assert addr not in seen;seen.add(addr);physical[addr]&=b
  pages+=1
 if fault:physical[page+3]^=1
 ok=physical[:len(target)]==target
 return {'physical_bytes_erased':sector,'physical_data_bits':K*N*8,'pages_received_programmed':pages,'unique_covered_bytes':len(seen),'peak_page_buffer_bits':page*8,'successful':ok,'completed_payload_Byte':K*N if ok else 0,'old_state_was_arbitrary':any(old),'encoding':'rowmajor16signedINT8two-complementbytes;erasedconductive=1/programmedlowcurrent=0;noextraencodedpayload'}

def signed_vectors(K,N):
 tests=[('zero',[0]*K,[[127]*N for _ in range(K)]),('negative_extreme',[-128]*K,[[-128]*N for _ in range(K)]),('cancel',[127 if i%2 else -127 for i in range(K)],[[63]*N for _ in range(K)]),('mixed',[i%256-128 for i in range(K)],[[((i*31+j*17)%256)-128 for j in range(N)] for i in range(K)]),('group_boundary',[1]+[0]*(K-1),[[j-8 for j in range(N)] for _ in range(K)])]
 out=[]
 for name,x,w in tests:
  acc=[0]*N
  for r in range(K):
   for group in range(2):
    for bit in range(8):
     for col in range(group*8,(group+1)*8):
      term=((x[r]&255)>>bit)&1;acc[col]+=term*(w[r][col]<<bit)*(-1 if bit==7 else 1)
  truth=[sum(x[r]*w[r][j] for r in range(K)) for j in range(N)]
  out.append({'name':name,'passed':acc==truth and all(-(1<<24)<=v<(1<<24) for v in acc),'min':min(acc),'max':max(acc)})
 return out

def evaluate(resolved,native):
 from read_network import integrate,precharge_bound
 p=resolved['resolved_parameters'];tab=table();op=operating_point(p,tab);n=native['frontend'];d=native['digital'];K=resolved['input']['logical']['K'];N=resolved['input']['logical']['N'];period=1/p['clock_Hz'];groups=p['read_mux'];tiles=K*groups
 e=electrical_port(n);pre=precharge_bound(p,tab,e)
 Rref_effective=p['reference_resistance_ohm']+op['geometry']['source_column_R_ohm']+n['native_sense_count']*op['geometry']['source_common_R_ohm']
 e['reference_internal_initial_upper_V']=e['reference_off_current_upper_A']*Rref_effective+e['vdd_V']*math.exp(-(n['native_sense_control_s']/2)/(e['reference_internal_cap_F']*Rref_effective))
 dyn=integrate(p,tab,e,step_s=10e-12)
 # Source clock2/f hasoneprechargeandoneSAenable/outputphase. Theoriginal
 # constantDeltaI developtermisreplacedbytheactualcase network, notadded.
 internal_precharge_clock=n['native_sense_control_s']/2;output_phase=n['native_sense_control_s']/2
 # EverygroupstartsandendswithallWL/refOFF. Explicitfinitecontrolsettling.
 settle_log=math.log(1/p['precharge_error_fraction']);control_factor=settle_log/math.log(2)
 gate_release=n['gate_enable_control_s']+n['gate_enable_NAND_s']+n['gate_fall_tau_s']*settle_log
 ref_release=n['gate_enable_control_s']+n['reference_TG_N_gate_delay_s']+max(n['reference_TG_P_gate_fall_tau_s'],n['reference_TG_N_gate_rise_tau_s'])*settle_log
 release=max(gate_release,ref_release)
 selected=max(n['native_gate_address_s'],n['native_mux_select_s']+n['native_mux_s'])
 internal_reset=e['reference_internal_cap_F']*dyn['reference_R_including_returns_ohm']*math.log(e['vdd_V']/(p['read_drain_V']*p['precharge_error_fraction']))
 prephase=max(internal_precharge_clock,n['native_sense_precharge_s'],pre.get('complete_precharge_s',math.inf),internal_reset)
 pre_release=n['precharge_control_s']*control_factor
 develop=dyn['capture']['time_s'] if dyn['capture'] else 0.
 front_raw=release+selected+prephase+pre_release+develop+output_phase+release
 front=math.ceil(front_raw/period)*period if math.isfinite(front_raw) else 0.
 clear=max(period,math.ceil(d['state_clear_s']/period)*period)
 ref_initial_upper=e['reference_internal_initial_upper_V']
 checks=[]
 def check(id,ok,evidence):checks.append({'id':id,'passed':bool(ok),'critical':True,'evidence':evidence})
 check('one_authority',n['precharge_voltage_V']==p['read_drain_V'] and n['precharge_error_fraction']==p['precharge_error_fraction'],'Oneauthoritativebias/errorinputfeedsnativeprechargeandcaseinitialstates')
 check('geometryfits',op['geometry']['area_gate_plus_two_diffusion_m2']<=op['geometry']['cell_pitch_area_m2'],op['geometry'])
 check('threshold_separation',op['erased_slowest']['I_A']>op['programmed_fastest']['I_A'],{'ON':op['erased_slowest'],'OFF':op['programmed_fastest']})
 check('native_lowrail_gate',n['native_gate_driver_compatible']==1,{'rail':p['read_gate_V'],'nativeVdd':e['vdd_V'],'actualwidthP':e['gate_P_width_m'],'actualgateC':e['gate_total_load_F'],'finite_ramp':True})
 check('precharge_PMOS_and_supply',n['precharge_bias_compatible']==1 and pre['feasible'] and pre.get('source_current_upper_A',math.inf)<=p['precharge_supply_limit_A'],pre)
 check('reference_physical_match',n['reference_match_feasible']==1 and n['reference_TG_count']==p['cols']/groups,{'match_C_each_F':n['reference_match_cap_F'],'TG_internal_node_C_F':e['reference_internal_cap_F'],'separate_internal_node_notprematchedto1V':True})
 check('reference_initial_history',ref_initial_upper<p['read_drain_V']*p['precharge_error_fraction'],{'reset_phase_s':prephase,'residual_internal_upper_V':ref_initial_upper,'initial_voltagemax':e['vdd_V'],'off_TG_current_upper_A':e['reference_off_current_upper_A'],'meaning':'ActualR/CremovesprevioushistorybutnativeOFFleakageleavesafiniteupperinitialvoltage;ONuseslower0/OFFusesupperinitialtoavoidfavourableassumption'})
 check('dynamic_reference_and_false_latch',dyn['feasible'],{'capture':dyn['capture'],'required_V':dyn['required_V'],'early_min_V':dyn['wrong_polarity_extreme_V'],'false_early_latch_excluded':dyn['false_early_latch_excluded'],'gate_injection_upper':dyn['unfavourable_gate_injection_bound_C']})
 check('native_clock_and_fullcycle',d['digital_clock_budget_satisfied']==1 and d['digital_mac_comb_s']<=period/2,{'chosen_period_s':period,'required_s':d['digital_halfcycle_min_period_s']})
 check('complete_sector_mapping',K*N==p['sector_Byte'] and K*N%p['page_Byte']==0,'All4096logicalBytesoccupyonephysical4KiBsector/16completepages;noerasedforeignpayload')
 check('clock_phase_accounting',math.isclose(internal_precharge_clock+output_phase,n['native_sense_control_s']),{'native_clocktotal_s':n['native_sense_control_s'],'prechargeclock_s':internal_precharge_clock,'outputphase_s':output_phase,'originalconstantDeltaIterm_excluded':True})
 life=lifecycle(K,N,p['page_Byte'],p['sector_Byte']);failed=lifecycle(K,N,p['page_Byte'],p['sector_Byte'],True);vec=signed_vectors(K,N)
 check('state_full_cover',life['successful'] and life['completed_payload_Byte']==K*N and failed['completed_payload_Byte']==0,{'success':life,'failure':failed})
 check('signed_local_mapping',all(q['passed'] for q in vec),vec)
 pages=K*N//p['page_Byte'];transactions=3*(pages+1);commandbits=8*(pages+1)+32+pages*32+16*(pages+1);databits=K*N*8
 nativeids=['NATIVE'];both=['NATIVE','MODEL','DESIGN']
 stream=[stage('input_admission',period,math.ceil(K*8/p['input_port_bits']),'native_circuit',nativeids,'2048bitinputhold/128bitlocalport','All256logicalinputBytesacceptedinnativeingressclockslots','NoexternalDRAM'),stage('clear_output_status',clear,1,'native_circuit',nativeids,'RealclearAND/control400bitoutputs/status/retry','Clearoldrequestdatausingnativehardware','Noimplicitzeroinitialstate'),stage('input_row_selection',period,K,'native_circuit',nativeids,'Nativeinputrowselector/8bitrowhold','Onebyteheldperlogicalrow','Not8independentinputports'),stage('physical_binary_frontend',front,tiles,'adapter',both,'128physicalcolumns/64dataSA+64matchedreferencebranches','AllWL/refOFF,address/MUX,PMOSprecharge,realreferenceinternalreset,PMOSoff,finitegate/refdevelopment,thresholdlatch,nativeSAoutputphase,release,clockalignment','NoRRAMreadfrontorold100/120/130ns;nativeclockprechargephasecountedonce'),stage('weight_capture',period,tiles,'native_circuit',nativeids,'128bitrowholdwithpartial64bitcapture/feedbackkeeps','Retainrealrowbitgroupsfor8input-bitMACupdates','Nofullmatrixshadow'),stage('eight_input_bit_MAC',period,tiles*8,'native_circuit',nativeids,'8native25bitadd/sub/shift/zero-mask/groupkeep/16outputholds','Sevenpositiveandoneinput-signupdates;weightbit7signextends;fulllegalfeedbackclock','NoextraunsignedSubArrayarithmetic'),stage('result_ready',period,1,'service_policy',['DESIGN'],'existingstatusregister','Resultsalreadyheld;publishready','Nooffdomaintransport')]
 resident=[stage('resident_state_clear',clear,1,'native_circuit',nativeids,'Actualstatus/retry/outputs','Clearsarbitrarypriorcontrolflagsbeforeadmission','Doesnoterasecells'),stage('SPI_data_reception',1/p['program_SPI_Hz'],databits,'external_primitive',['NOR-02-IO'],'Source3VsingleDI/CLK/CSportandactual256Bytepagebuffer','All4096logicalBytesclockedexactlyoncein16pagewindows','Noencodingpayloadduplication'),stage('SPI_commands_status',1/p['program_SPI_Hz'],commandbits,'external_primitive',['NOR-02-IO'],'WREN/address/opcode/statuscommands','17WREN,one32bitsectorcommand,16page32bitheaders,17opcode+status16bitcompletions','NotinternaltPP/tSE'),stage('SPI_transaction_boundaries',p['SPI_CS_gap_s']+p['SPI_setup_hold_s'],transactions,'external_primitive',['NOR-02-IO'],'ActualCSboundary','50nsdeselectplus3nssetup/3nsholdpertransaction','Noarraypulse'),stage('full_sector_erase',p['sector_erase_s'],1,'external_primitive',['NOR-02'],'Onecompleteallocated4KiBsectorengine','Arbitraryoldstate-toerasedFF;selftimedHVengine/pulse/verify/recoveryuntilBUSY0','SPIingressandcustomreadexcluded;notESF1guarantee'),stage('full_page_program',p['page_program_s'],pages,'external_primitive',['NOR-02'],'Onecomplete256Bytepageengine/realpagebuffer','All16completepagewritesincludinginternalprogram/verify/HVreturnuntilreadready;eachpagebufferreusedonlyaftercompletion','Noadditionalpulse/verify/recoveryfee;noexpectedretry'),stage('matrix_ready',period,1,'service_policy',['DESIGN'],'Existingmatrixstatus','Publishonlyafterall16pagesandBUSY0;newreadfrontendisincompatiblewithHVmodeandremainsoffuntilenginehandsbackreadsafeports','Noextraweightpayload')]
 resources={'physical_data_bits':K*N*8,'physical_shape':[K,N*8],'logical_payload_Byte':K*N,'SA_count':int(n['native_sense_count']),'reference_TGs':int(n['reference_TG_count']),'reference_resistors':int(n['reference_TG_count']),'reference_R_ohm':p['reference_resistance_ohm'],'reference_match_C_each_F':n['reference_match_cap_F'],'reference_internal_C_each_F':e['reference_internal_cap_F'],'reference_off_leak_A_each':e['reference_off_current_upper_A'],'reference_internal_initial_upper_V':e['reference_internal_initial_upper_V'],'data_extra_integration_cap_each_F':p['other_BL_cap_F'],'data_extra_integration_caps':p['cols'],'precharge_PMOS_count':int(n['precharge_count']),'precharge_supply_limit_A':p['precharge_supply_limit_A'],'all_WL_off_gate_rows':p['rows'],'native_gate_enable_area_m2':n['gate_enable_area_m2'],'input_hold_bits':int(d['input_hold_bits']),'weight_hold_bits':int(d['weight_hold_bits']),'target_hold_bits':int(d['target_hold_bits']),'signed_output_hold_bits':int(d['signed_output_hold_bits']),'MAC_lanes':p['mac_lanes'],'full_matrix_shadow_bits':0,'external_PE_page_buffer_bits':p['page_Byte']*8,'engine_physical_sector_Byte':p['sector_Byte'],'resident_SPI_data_lanes':1,'resident_SPI_Hz':p['program_SPI_Hz'],'geometry':op['geometry'],'native_frontend_unused_hold_bits':int(n['native_hold_bits']),'native_frontend_hold_scope':'Allocatedbyperipheryprobeandarea-paid,butactualcompleteMACusesseparatedigitalweightHold;noextraunbilledstorage','native_frontend_area_m2':n['native_periphery_area_m2'],'native_digital_area_m2':d['native_digital_area_m2'],'area_qualification':'Nativepartialareaexcludesexplicitpassivecapacitor/resistorlayoutsandopaqueHVPEengine;notcompleteequalareamacrocomparison'}
 conditions=['ESF1 measured-figureendpointI-V plusnewengineeredEOT/depletion/pitch/C;notoriginalanalogclassifierorfabricatedsamechip.','130nmLSTPperipherywithreal1.1/1.2/1.3Vlowerrailgatebufferand1VPMOSprecharge;Ion/W/VthMOSextensionisnominal,noindependentbodyeffect/velocitysaturationcalibration.','ReferenceR600k/matchedC,SA20mV+atmost10mVtotalremainingoffset/noise,andindependent±0.2%precharge/±1nscontrolshiftareexplicitdesignconditions.','FullunfavourableN/Pgatechargecouplingisboundedwithoutassumingcancellation;fixed4pFadditionalBLintegrationCpreventsfalseearlythresholdlatchinthemodel.','NativeVSAdecisionisabstractthresholdlatchwithfalseearlysigncheck;following1/fisoutput-readyphase,notsustainedpassivedevelopmentorSTA/comparatornoisevalidation.','Local1Vprechargerailmustprovide20mA;actualinitialparallelcurrentchecked;notglobalPDNsignoff.','CompleteW25Q-likepage/sectorengineincludesitsHVrouting/isolation/internalverify/returnandactualpagebuffer;transfertoESF1readstatesandreadsafeportsisexplicitlyconditional,notguaranteedbyproductspecfornewarray.','Inputweightdataareavailableatlocal3VSPIpins;inputvectoratnative128bitport;offchipDRAM/interconnect/powerupareexcluded.','NoWER/yield/retentiondistributionclaimed;thethreefinitegate/PEpackagesarenotstatisticalprocesscorners;typisproductspeclabelnotmedian.']
 return {'status':'conditional' if all(c['passed'] for c in checks) else 'infeasible','qualification':'Binarythreshold/circuit-reference withnominalexactsignedarithmetic;completeP/Econditionalcrossimplementationprimitive','conditions':conditions,'program_outcome':'success' if life['successful'] else 'failed','scheduling':'serial_nonoverlap','physical_checks':checks,'resources':resources,'stream_stages':stream,'resident_stages':resident,'diagnostics':{'network_operating_point':op,'electrical_port':e,'precharge':pre,'dynamic':dyn,'read_phase_s':{'all_off':release,'address_and_mux':selected,'precharge':prephase,'precharge_release':pre_release,'enable_and_develop':develop,'native_output_phase':output_phase,'final_release':release,'raw':front_raw,'clock_ready':front,'alignment':front-front_raw},'reference_internal_residual_upper_V':ref_initial_upper,'counts':{'tiles':tiles,'MACupdates':tiles*8,'input_beats':math.ceil(K*8/p['input_port_bits']),'pages':pages,'sectors':1,'SPI_transactions':transactions,'SPI_command_status_bits':commandbits,'SPI_payload_bits':databits},'full_cover_state':life,'failure_state':failed,'signed_vectors':vec,'stage_order':'Receive/programonepageatatimeaftersectorerase;SPIstagecountsareinterleaved,notallpagespreloadedintoashadow.'}}
