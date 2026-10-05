"""NAND full service: compact string/TIA, actual native peripherals, complete P/E."""
import json,math,hashlib
from pathlib import Path
from device_model import ports,channel_settling
from tia_model import diagnostics
from mapping_probe import counts,diagnostic

def prepare_nand(resolved):
 p=resolved['resolved_parameters'];g=ports(p)
 keys=('technology_nm','temperature_K','logical_K','logical_N','lanes','adc_count','adc_bits','row_groups','page_bits','wordlines','blocks','bitlines','clock_Hz','HV_level_input_F','BL_switch_R_ohm','external_IO_load_F','ADC_bank_width_m','ADC_input_C_F')
 q={k:p[k] for k in keys};q['BL_cap_F']=g['BL_cap_F']
 return {'identity':resolved['input']['implementation_id'],'point_eligibility':'native_components_only','parameters':q,'derived_geometry':g}

def stage(name,seconds,count,source,resources,includes,excludes):
 kind={'MLP':'native_circuit','TRAINING':'native_circuit','HYBRID':'adapter','HV':'external_primitive','PE':'external_primitive','DESIGN':'service_policy'}[source]
 sources=['EKV','LTC','DESIGN'] if source=='HYBRID' else [source]
 r={'id':name,'duration_s':seconds,'count':int(count),'source_class':kind,'source_ids':sources,'resources':resources,'includes':includes,'excludes':excludes}
 if kind=='native_circuit':r.update(native_return_unit='seconds',included_internal_clock_phases='Native DFF capture halfcycle; completelegalcontrollercycles used without duplicate capture')
 return r

def evaluate(resolved,native):
 p=resolved['resolved_parameters'];d=native['logic'];a=native['sar'];T=1/p['clock_Hz'];align=lambda s:max(T,math.ceil((s-1e-18)/T)*T)
 g=ports(p);channel=channel_settling(p);ct=counts(p);rawports=json.loads(Path(__file__).with_name('string_ports.json').read_text());front=diagnostics(p,rawports)
 model_hash=hashlib.sha256(Path(__file__).with_name('string_probe.py').read_bytes()).hexdigest()
 if model_hash!=rawports['model_sha256']:raise ValueError('Electrical table and compact source differ')
 # Actual low-read-rail N branch conservatively carries the BL drive. This is
 # only an R/C and IR envelope, not an unqualified channel programming model.
 Ron=2*d['native_BL_switch_actual_R_ohm']*(d['native_vdd_V']-d['native_vth_V'])/(d['native_vdd_V']-.2-d['native_vth_V'])+g['BL_wire_ohm']
 Cbl=g['BL_cap_F']+3*d['native_BL_switch_drain_F'];bl_settle=-math.log(p['bias_relative_error'])*Ron*Cbl
 maximum_unit=max(rawports['tables']['data_low_pass']['active_on']);BLcurrent=p['blocks']*p['ssl_count']*maximum_unit;drop=BLcurrent*Ron
 ingress=align(d['native_ingress_comb_s']+d['native_capture_s']);format_time=align(d['native_format_comb_s']+d['native_capture_s']);mask_time=align(d['native_input_mask_format_s']+d['native_capture_s'])
 select=align(d['native_WL_decode_s']+g['read_bias_setup_s']+channel['settle_allowance_s']);sense=align(d['native_BL_mask_s']+bl_settle+channel['settle_allowance_s']+front['maximum_settle_s']+a['native_ADC_s']+d['native_capture_s']);release=align(d['native_BL_mask_s']+bl_settle)
 arithmetic=align(d['native_arithmetic_comb_s']+d['native_capture_s']);clear=align(d['native_state_clear_s']);byte_period=max(T,p['PE_min_bus_cycle_s'],d['native_page_byte_select_s'])
 masks=4*2*p['row_groups'];reads=ct['stream_analog_reads'];batches=p['adc_count']//p['lanes']
 # One offset subtraction, one realwork clear,11 signed bit-serial multiply
 # steps, one rounding step per16channel batch;8group contributions per8outputs.
 affine_cycles=(p['adc_bits']+4)*batches;merge_cycles=8
 stream=[stage('new_request_clear',clear,1,'MLP','output/work/controlholds','newrequest physicalclear','residentpayload'),
  stage('input_receive_abs_hold',ingress,ct['input_beats'],'MLP','128bitport,16abs lanes,41472bitinputhold','alllogicalinput once','no preloadedwholevector'),
  stage('build_input_masks',mask_time,masks*ct['input_beats'],'MLP','16laneinputselector/encoding,13824BLmaskhold','32actualmasks reusedacross30dataWL each','notonefreeparallelmaskoperator'),
  stage('select_data_WL',select,reads,'HYBRID','nativeaddress+64parallelratedreadbiasports','inputmaskouterloop,30WLs;allpass/GSL/SSLloads','notlegacy303ns'),
  stage('read_settle_ADC_capture',sense,reads,'HYBRID','64actualSLreceivers/64nativeSAR/codehold','BLRC,internalchannel differentialRC,finite2AMPKCL,ADC,capture','no oldSLslot,noENOBclaim'),
  stage('return_BL_before_digital',release,reads,'HYBRID','actualBLmask/gate','allBL0aftercapture whilemaskholdretained','notfreeongoingpayload'),
  stage('affine_fixed_point',arithmetic,reads*affine_cycles,'MLP','16x35bitAddSub+workhold/24bitcoefficients','clear+offset+11serialmult+round perbatch','notCPUtruecountcorrection'),
  stage('base4_sign_accumulate',arithmetic,reads*merge_cycles,'MLP','8activeoutputlanes of16,240x32bithold','fourweightdigits,twoWsigns andtwoinputphases,wirepowers4','notfree32parallelMAC'),
  stage('read_bias_release',align(g['read_bias_release_s']),1,'HV','2304readbiascontrols','readnormalbiasreturn','PEinternalrecovery'),
  stage('result_ready',T,1,'DESIGN','outputhold','all240Q4outputsready','noextratransferpayload')]
 pages=ct['page_programs'];coeffs=ct['calibration_coefficients'];calreads=ct['calibration_analog_reads'];calarith=(32+3)*(coeffs//p['lanes'])
 resident=[stage('invalidate_and_clear',clear,1,'MLP','status/stagingcontrols','arbitraryoldmatrix invaliduntilfinish','notfreepreerase'),
  stage('logical_weight_encode',ingress,ct['resident_encoding_beats'],'MLP','128bitport,16abslanes,one4608x9rowstaging','fulllogicalmatrixonce,rowretainedthrough24pages','notwholematrixshadow'),
  stage('format_all_data_and_reference',format_time,pages*ct['packets_per_page'],'MLP','48bitphysicalformatterpacket','all5760data+384referencepages','notduplicatelogicalpayload'),
  stage('physical_page_data_input',byte_period,ct['physical_page_bytes'],'PE','one8bitPEengineport,itsfullpagebuffer','allencodedphysicalbytes,onebyteperlegalcontrollercycle>=25ns','no P/E pulses here'),
  stage('PE_commands_and_status',T*p['engine_command_cycles'],pages+ct['block_erases'],'PE','oneengine/controlstate','finitecommand/address/statushandshake','no internalverifyduplication'),
  stage('complete_block_erase',p['erase_s'],ct['block_erases'],'PE','oneconditionalfullP/Eengine','all64blocks erased,HV/pump/verify/recovery/readsafeisolationincluded','no pre-erasedappend'),
  stage('complete_page_program',p['program_s'],pages,'PE','oneconditionalfullP/Eengine','all6144pages successinclinternalverify/biasrecovery','no extra programloopguess'),
  stage('calibration_reference_select',select,calreads,'HYBRID','twoactualreferenceWLs/fourinputgroups','zero/half/fullmasks perreference','notfreecalibration'),
  stage('calibration_ADC_acquisition',sense+release,calreads,'HYBRID','64TIA/SARs andactualreferencecells','bothreferencepages,threefinitelevels,no inventednoiseaverage','notpayload'),
  stage('calibration_coefficient_arithmetic',arithmetic,calarith,'MLP','16lane35bitrestoringdivider/AddSub,256x48bitcoefhold','32divisionsteps+offset/store/clear; Q8.16gain,integeroffset','notfreehostdivision'),
  stage('publish_compute_ready',T,1,'DESIGN','successstatus','onlyafterallcompletePEandcalibration','failurehaszero completedpayload')]
 nominal=diagnostic(p,front['gain_count_per_code'],front['calibration_zero_code'])
 checks=[{'id':'string_receiver_valid','passed':front['valid'],'evidence':{'nominal_settle_s':front['maximum_settle_s'],'independent_2C_s':front['double_C_settle_s']}},
  {'id':'payload_encoding_capacity','passed':ct['data_cells']+ct['reference_cells']==ct['physical_cells'] and ct['page_programs']==6144 and ct['block_erases']==64,'evidence':ct},
  {'id':'native_resources_present','passed':d['BL_mask_hold_bits']==p['bitlines'] and d['calibration_coefficient_bits']==256*48 and a['native_ADC_count']==64,'evidence':{'BLmask':d['BL_mask_hold_bits'],'coef':d['calibration_coefficient_bits'],'ADC':a['native_ADC_count']}},
  {'id':'read_bias_IR_domain','passed':drop<.006 and .2-drop-p['amp_offset_V']>.15,'evidence':{'BL_drop_upper_V':drop,'native_effective_path_R_ohm':Ron,'scope':'smallvoltage-domain/quantitycheck;compactsource notsiliconsignoff'}},
  {'id':'nominal_mapping','passed':nominal['status']=='PASS' and nominal['code_perturbation_propagates'],'evidence':nominal},
  {'id':'calibration_coefficient_range','passed':front['gain_count_per_code']<256 and front['calibration_full_code']<1024,'evidence':{'gain':front['gain_count_per_code'],'offset':front['calibration_zero_code'],'full':front['calibration_full_code']}}]
 resources={'physical_cells':ct['physical_cells'],'reference_cells':ct['reference_cells'],'physical_data_cells':ct['data_cells'],'cells_per_INT8_weight':72,'blocks':64,'logical_shape':[4608,240],'native_ADC_count':64,'native_ADC_bits':10,'external_amplifiers':128,'external_amplifier_static_power_W':front['static_power_typ_W'],'external_AMP_total_supply_current_A':128*p['amp_Iq_A'],
  'page_programs':pages,'block_erases':64,'physical_page_bytes':ct['physical_page_bytes'],'PE_engine_pagebuffer_source_Byte':2112,'local_formatter_packet_bits':d['formatted_page_buffer_bits'],'logical_input_hold_bits':d['input_hold_bits'],'resident_row_staging_bits':d['resident_row_staging_bits'],'result_hold_bits':d['output_hold_bits'],'BL_mask_bits':d['BL_mask_hold_bits'],'coefficient_bits':d['calibration_coefficient_bits'],'native_arithmetic_lanes':16,'reconstruction_parallel_outputs':8,'controller_period_s':T,'physical_byte_accept_period_s':byte_period,'front_end_topology':'128 externalAMPS,notintegratedlowpowerNANDmacro','geometry_and_HV':g,'internal_string_dynamics':channel,'native_logic':d,'native_SAR':a,'shared_read_write':'mutuallyexclusive;P/Eengine includes ratedHV/read-safe isolation,readbiasports neversee20V'}
 conditions=['This is a new hybrid model-reference: 16layer measured DC normalization extended to32layer;not fabricated32layerSGVC macro.',
 'Finite calibrated approximate output only: nominal dense error about3percent,isolatedunit quantizeszero;pass-background extremes near+44/-22percent remain visible. No equal precision with binarydigitalcases.',
 'TIA single-pole/slew model and component bounds do not certify actualPCB stability/noise/ENOB;Cf/Rf/Cin and outputlevel conversion are explicit.',
 '128externalamplifiers consume10.56Wtypicalsteady5Vpower (pessimisticIqbound separatelyreported). No equal-area/energyclaim.',
 'Rated5VreadbiasdriverI/C and engineeringinterconnectgeometry give conservative localestimates;complete20V P/E/read-portisolation is a separate conditionalengineprimitive.',
 'P/E timing and pageports transfer fromdifferentSLCorganization; no targetSGVC guarantee, no size scaling or duplicateverify. Sourceengine success andtwo-stateprogramdomain are required.',
 'Both inputsignphases execute,retaining actualfixed-point codes;fixedbaseline cancels butno truth-based correction ofbackgroundgain orweak outputs.',
 'Room-temperatureSGVCmodel; amplifierpessimistic datasheetbounds arefinitecomponent envelope,not wholematerialPVT. Long-windowdrift/read-disturb/endurance areoutside localservice.']
 return {'status':'conditional','program_outcome':'success','scheduling':'serial_nonoverlap','qualification':'finitehybridcalibratedanalogQ4service;notexactINT8/ENOB/siliconguarantee','conditions':conditions,'physical_checks':checks,'resources':resources,'stream_stages':stream,'resident_stages':resident,'diagnostics':{'receiver':front,'nominal_mapping':nominal,'counts':ct,'BL_IR':{'R_ohm':Ron,'C_F':Cbl,'drop_V':drop},'coverage':'Actualstringnetwork/nativeports/SAR/digitalplusopaquecompleteP/E;old aggregate times never consumed'}}
