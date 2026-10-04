#!/usr/bin/env python3
"""Read-only v3 extraction into Step 2 input specifications; never run calculators."""
import argparse
import ast
import hashlib
import json
import math
import runpy
from pathlib import Path
import sys
sys.dont_write_bytecode = True

BASELINE = "a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0"
V14 = "8a88abf85844c0e1ba17cc771ea535fff6040456"
CASES = ["01_sram_acim", "02_sram_dcim", "03_nor_2d", "04_nand_3d", "05_rram", "06_mram", "07_pcm", "08_feram_hfo2", "09_gain_cell_edram", "10_fenor_3d"]
CALCULATORS = ["sram_acim", "sram_dcim", "nor", "nand", "rram", "mram", "pcm", "feram", "gain_cell_edram", "fenor"]
IDENTITIES = ["binary charge-coupled 9T1C SRAM; eight independent planes", "D6CIM binary 6T SRAM; native HCA/BFA MAC", "binary 2D NOR; digital sensed weights", "SGVC SLC 3D NAND; split-sign magnitude/base-4", "WH-2T1R m=1 binary RRAM; distinct CIM and memory paths", "complementary 2T2MTJ IBMD; digital read-before-adder tap", "binary/SLC voltage-mode PCM; native bank", "HZO remanent 1T1C FeRAM; destructive read with restore", "GC-04 silicon CMOS pseudo-differential 3T1C gain-cell; NOT IGZO or MLP hybrid", "vertical AND FeFET; lateral strips and four capacity layers"]
SHAPES = [(128,128),(128,16),(128,128),(4608,240),(128,64),(256,32),(256,128),(128,128),(64,64),(128,128)]
CELLS = [8,8,8,72,8,16,8,8,16,8]
ADC = [128,0,0,64,128,0,128,0,128,0]
SA = [0,None,4096,0,256,65536,0,4096,0,4096]
WRITES = [128,128,None,None,128,128,32,128,128,288]
HOLD = [0,0,4096,0,0,4096,0,4096,128,4096]
ACTIVE_ROWS = [128,16,32,1152,32,32,8,32,64,32]
UPDATE_BYTES = [16,16,16384,1105920,16,8,32,16,16,16]
ENCODED_BITS = [128,128,2048,13824,128,128,256,128,256,128]
CALC_FUNCTION = ["calculate","compute","evaluate","scenario","write_service","calculate","compute","make_row","calc","write_service"]

def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
def dump(p,obj): Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n")
def ref(source="inputs",pointer="",function=None):
    return {"source_id":source, **({"function":function} if function else {"json_pointer":pointer})}

def source(repo,path):
    p=repo/path
    result={"path":path,"sha256":digest(p),"baseline_sha":BASELINE}
    if p.suffix==".py":
        result["functions"]={n.name:{"start_line":n.lineno,"end_line":n.end_lineno} for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    return result

def stage(sid,kind,provider,entry,count,unit,per,inputs,resources,source_refs,included=(),depends=(),outputs=("service_time_s",),processing=None):
    return {"id":sid,"service_kind":kind,"provider":provider,
      "call":{"entrypoint":entry,"status":"specified_not_executed","inputs":inputs,"outputs":list(outputs)},
      "depends_on":list(depends),"count":{"value":count,"unit":unit,"per":per},
      "processing_range":processing or {"scope":per},"resources":resources,
      "included_stages":list(included),"overlap":{"allowed":False,"reason":"Serial baseline; no additional banks, resources or scheduling proof."},
      "source_refs":source_refs}

def primitive(pid,value,unit,source_refs,kind="primitive_budget",mode=None,includes=()):
    factors={"ns":1e-9,"us":1e-6,"ms":1e-3,"nA":1e-9,"uA":1e-6,"mA":1e-3,"fF":1e-15,"pF":1e-12,"V":1,"kOhm":1e3}
    normalized={"ns":"s","us":"s","ms":"s","nA":"A","uA":"A","mA":"A","fF":"F","pF":"F","V":"V","kOhm":"ohm"}
    return {"id":pid,"original":{"value":value,"unit":unit},"normalized":{"value":value*factors[unit],"unit":normalized[unit]},"status":"retained_v3_input","kind":kind,"mode":mode,"included_stages":list(includes),"source_refs":source_refs}

def base(repo,cid,index):
    prefix="tasks/task1_table_I_NVM/analysis/"+cid
    inp=read(repo/(prefix+"/data/inputs.json")); res=read(repo/(prefix+"/data/results.json"))
    native=res["native_configuration"]
    k,n=SHAPES[index]; bits=16+math.ceil(math.log2(k)); cap=k*n
    s={"inputs":source(repo,prefix+"/data/inputs.json"),"results":source(repo,prefix+"/data/results.json"),"calculator":source(repo,prefix+"/scripts/check_"+CALCULATORS[index]+".py")}
    for key,path in (("shared","data/shared_parameters.json"),("shared_calculator","scripts/check_shared.py"),("method","tex/02_estimation_method.tex")):
        s[key]=source(repo,"tasks/task1_table_I_NVM/analysis/shared_baseline/"+path)
    physical={key:value for key,value in native.items() if key not in ("resources","display_conversion","b_S","b_R","B_S_Byte","n_in","n_out","K","N","output_count","output_bits","output_container_bits","logical_matrix_order","input_register_bits","output_register_bits")}
    physical.update({"cells_per_INT8_weight":CELLS[index],"data_storage_sites":cap*CELLS[index],"effective_capacity_Byte":cap,"independent_payload_replicas":1,"signal_enhancement_replication":3 if index==3 else 1,"complementary_encoding_factor":2 if index in (3,5,8) else 1,"neurosim_array_assignment":{"numRowSubArray":None,"numColSubArray":None,"status":"requires_per_primitive_topology_adapter","rule":"Never substitute logical K,N for a physical array; preserve native banks, plane orientation, active rows, isolation and access direction."},"source_refs":[ref("results","/native_configuration")]})
    resources={"installed":{"adc_count":ADC[index],"sense_or_verify_nodes":SA[index],"digital_output_channels":16,"operand_hold_bits":HOLD[index],"analog_cross_group_hold_slots":0,"input_register_bits":k*8,"output_register_bits":n*bits,"encoded_interface_bits":128,"real_write_driver_count":WRITES[index],"external_update_domains":1},"active":{"streaming":{"input_terms_per_group":ACTIVE_ROWS[index],"output_lanes":8 if index==3 else 16,"weight_planes_parallel":8 if index in (0,4,6,8) else None,"adc_count":ADC[index]},"resident":{"logical_Byte_per_transaction":UPDATE_BYTES[index],"encoded_bits_per_load_unit":ENCODED_BITS[index],"physical_write_driver_count":WRITES[index]}},"native_declared":native.get("resources",{}),"capacity_policy":"Installed capacity is not active parallelism. No extra ADC, SA, hold bank, driver or mux lane may appear without a resource edit.","source_refs":[ref("results","/native_configuration"),ref("shared","/resource_policy")]}
    configuration={"contract_version":"2.0.0","status":"input_specification","case_id":cid,
      "provenance":{"baseline_repository":"https://github.com/bcacdwk/CIM_roofline","baseline_v3_sha":BASELINE,"profile":"reference","sources":s,"prior_performance_values_imported":False},
      "logical":{"K":k,"N":n,"matrix_order":"W[N,K]","input_bits":8,"weight_bits":8,"signed":True,"bytes_per_input":1,"bytes_per_weight":1,"B_S_Byte":k,"B_R_Byte":cap,"resident_transaction_Byte":UPDATE_BYTES[index],"output_bits":bits,"numerical_contract":"calibrated_approximate_partial_sums" if ADC[index] else "exact_signed_integer_conditional_on_correct_storage_and_sensing","byte_bit_rule":"v3 b_S=b_R=1 means Byte/element, not 1-bit arithmetic. Encoded copies add physical occupancy, never logical payload.","source_refs":[ref("results","/native_configuration"),ref("shared_calculator",function="logical_configuration")]},
      "physical":physical,
      "device":{"identity":IDENTITIES[index],"primitives":[],"native_technology_policy":"Retain native device bias/load/geometry independently of the low-voltage peripheral technology; no 28nm Technology table or enum relabeling.","source_refs":[ref()]},
      "periphery":{"policy_id":"lv_v14_22nm_lstp_300k_v1","candidate_branch":"2DInferenceV1.4","locked_sha":V14,"technode_nm":22,"device_roadmap":"LSTP","temperature_K":300,"clock":{"clock_id":"lv_core","target_period_ns":5,"actual_period_ns":None,"status":"requires_critical_path_measurement","rule":"actual=max(target_period_ns, measured used sensing/combinational critical path); DFF alone does not prove closure"},"unit_conversion":{"backend_output":"s","contract_time":"ns","scale":1e9,"apply_exactly_once":True},"native_loads_transplanted":False,"scope":"Low-voltage peripheral candidates only; native array/driver/sense complete services retain their original load and bias."},
      "resources":resources,"services":[],"parameter_bindings":[],"unresolved":[],
      "implementation_plan":{"status":"design_only","run_formal_ten_case_performance":False,"code_generation":"No full NAND matrix and no model/dataset download.","candidate_modules":["DFF::Initialize/CalculateLatency","Adder::Initialize/CalculateLatency","AdderTree::Initialize/CalculateLatency","SarADC::Initialize/CalculateLatency"],"comparison_only_modules":["ShiftAdd: internal DFF/read-pulse capacity and overlap require separate proof"],"next":"Root integrates source probes and pins coverage decisions before Step 3."}}
    return configuration,inp,res

def add_bindings(c):
    shared=[("input_step",5,"/common_conditions/propagation/profile_values/reference/input_step"),("adc_batch",20,"/common_conditions/propagation/profile_values/reference/adc_batch"),("digital_tick",5,"/common_conditions/propagation/profile_values/reference/digital_tick")]
    for name,value,pointer in shared:
        consumers=[]
        for s in c['services']:
            if name in json.dumps(s['call']['inputs']): consumers.append(s['id'])
        c['parameter_bindings'].append({"id":name,"status":"active" if consumers else "not_applicable","single_source":{"source_id":"shared","json_pointer":pointer,"v3_reference_value_ns":value},"replacement_status":"neurosim_candidate_not_resolved" if consumers else "not_applicable_or_already_inside_complete_front","replacement_value_ns":None,"clock_id":"lv_core" if name=='digital_tick' else None,"consumers":consumers,"conversion":"C++ seconds * 1e9 once; cycle count multiplied by actual clock period only when explicitly cycle-domain","included_overhead_rule":"Do not add to complete opaque cycles or fronts where already included.","maintenance_recompute":"Recompute every affected stage, busy reservation and nonpreemptive guard; never copy old rho/tau/T_R as targets."})
        binding=c['parameter_bindings'][-1]
        binding['selected_implementation']={'digital_tick':'lv_core.actual_period_ns','adc_batch':'SarADC::Initialize(levelOutput=2^nominal_bits); CalculateLatency(numRead=1); readLatency_s * 1e9','input_step':'v3 dedicated input/reset budget; not inferred from DFF'}[name]
        binding['replacement_status']='selected_function_pending_case_instantiation' if consumers else 'not_applicable'
        if name=='input_step' and consumers:
            binding['replacement_status']='retained_v3_input_reset_budget';binding['replacement_value_ns']=value
    for p in c['device']['primitives']:
        consumers=[s['id'] for s in c['services'] if p['id'] in json.dumps(s['call']['inputs'])]
        c['parameter_bindings'].append({"id":p['id'],"status":"active" if consumers else "qualification_only","single_source":{"local_json_pointer":"/device/primitives/"+str(c['device']['primitives'].index(p))+"/normalized","source_refs":p['source_refs']},"consumers":consumers,"conversion":"Use normalized SI once; preserve complete-cycle included stages.","included_overhead":p['included_stages'],"maintenance_recompute":"Apply to all named modes; update refresh/restore reservation and guard if this parameter is consumed."})

def digital_read_stages(c,tiles,read_param,entry,sref,existing_capture=False):
    stages=[stage('binary_read','streaming','v3_native_service',entry+' / retained complete binary read',tiles,'tiles','vector',{'duration_parameter':read_param,'read_bits':4096},['native_declared','operand_hold_bits'],[sref],included=['bias/read/sense','existing capture' if existing_capture else 'no new capture'],processing={'input_rows':32,'outputs':16,'weight_bits':8,'hold_through_input_slices':8,'replace_after_last_input_slice':True})]
    if not existing_capture:
        stages.append(stage('operand_capture','streaming','neurosim_native','DFF::Initialize; DFF::CalculateLatency',tiles,'capture_cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','numRead':1,'numDff':4096},['operand_hold_bits'],[sref],depends=['binary_read']))
    stages.append(stage('digital_mac','streaming','neurosim_composed','AdderTree::CalculateLatency; ShiftAdd::CalculateLatency; DFF::CalculateLatency',tiles*8,'cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','rows_per_group':32,'output_lanes':16,'input_slices':8},['digital_output_channels','operand_hold_bits'],[ref('shared','/reference_instance/dcim')],depends=['binary_read' if existing_capture else 'operand_capture']))
    return stages

def analog_stages(c,evaluations,front_param,front_includes_input,sref):
    return [stage('analog_front','streaming','v3_native_service','retained native frontend primitive from v3',evaluations,'evaluations','vector',{'duration_parameter':front_param,**({} if front_includes_input else {'input_step':'binding'})},['native_declared'],[sref],included=['input_step'] if front_includes_input else []),stage('sar','streaming','neurosim_native','SarADC::Initialize; SarADC::CalculateLatency',evaluations,'batches','vector',{'adc_batch':'binding','numCol':c['resources']['installed']['adc_count'],'levelOutput':1024,'numRead':1},['adc_count'],[ref('shared','/reference_instance/acim')],depends=['analog_front']),stage('digital_reconstruct','streaming','neurosim_composed','AdderTree::CalculateLatency; ShiftAdd::CalculateLatency; DFF::CalculateLatency',evaluations*2,'cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','output_bits':c['logical']['output_bits']},['digital_output_channels'],[ref('shared','/reference_instance/acim')],depends=['sar'])]

def scheduling(c,index):
    def use(sid,count=1,**more):return {'stage_id':sid,'count':count,**more}
    def repeat(count,steps,axis):return {'repeat':count,'axis':axis,'steps':steps}
    def get(sid):return next(s for s in c['services'] if s['id']==sid)
    def extra(sid,count,unit,inputs,resources,source_refs):
        c['services'].append(stage(sid,'resident','neurosim_native','DFF::Initialize; DFF::CalculateLatency',count,unit,'full_matrix',dict(digital_tick='binding',clock_id='lv_core',**inputs),resources,source_refs))
    if index in (2,5,7,9):
        tiles=get('binary_read')['count']['value'];steps=[use('binary_read')]
        if index!=7:steps.append(use('operand_capture'))
        steps.append(repeat(8,[use('digital_mac')],'input_bit'))
        streaming=[use('input_capture'),repeat(tiles,steps,'row_output_tile'),use('output_commit')]
    elif index==1:streaming=[use('input_capture'),repeat(64,[use('native_mac')],'complete_MAC_round'),use('output_commit')]
    elif index==3:streaming=[use('input_capture'),use('input_magnitude_sign',288),repeat(30,[use('native_wl'),repeat(32,[use('native_bl_sl'),use('sar'),use('affine_merge_sign',4)],'input_digit_sign_row_group')],'output_WL_group'),use('output_commit')]
    else:
        front='charge_front' if index==0 else 'analog_front';recon='reconstruct' if index==0 else 'digital_reconstruct';n=get(front)['count']['value']
        streaming=[use('input_capture'),repeat(n,[use(front),use('sar'),use(recon,2)],'input_bit_row_output_group'),use('output_commit')]
    if index in (0,1):resident=[repeat(1024 if index==0 else 128,[use('sram_write')],'aligned_16B_transaction')]
    elif index==2:
        get('page_program')['depends_on'].append('sector_erase')
        resident=[repeat(4,[use('sector_erase'),repeat(16,[use('page_load'),use('page_program')],'page_in_sector')],'dedicated_sector')]
    elif index==3:
        get('page_program')['depends_on'].append('block_erase')
        resident=[repeat(64,[use('block_erase')],'native_block'),repeat(240,[use('resident_encode',288),repeat(24,[use('page_load',page_kind='data',effective_port_bits=48),use('page_program')],'data_page_for_output_row')],'logical_output_row'),repeat(384,[use('page_load',page_kind='reference',effective_port_bits=128),use('page_program')],'reference_page'),use('load_calibration')]
        cal=get('load_calibration');cal['provider']='neurosim_composed';cal['call']['native_components']=[{'provider':'v3_native_service','parameter':'wl_setup','count':2},{'provider':'v3_native_service','parameters':['bl_setup','sl_setup'],'count':12},{'provider':'neurosim_native','module':'SarADC','method':'CalculateLatency','numRead':1,'count':12},{'provider':'neurosim_composed','modules':['Adder','DFF'],'reference_digital_cycles':450,'clock_id':'lv_core'}]
    elif index==4:
        p=get('program_attempts');p['count']={'value':1536,'unit':'program_attempts','per':'full_matrix'}
        p['call']['inputs']['control_cycles_per_attempt']=1
        for key in ('front_data_beats','front_control_cycles','first_data_in_command'):p['call']['inputs'].pop(key,None)
        extra('resident_front',512,'transactions',{'encoded_bits':128,'data_beats':1,'control_cycles':2,'first_data_in_command':True},['encoded_interface_bits'],[ref('calculator',function='write_service')])
        extra('attempt_done',1536,'commit_cycles',{'numDff':128,'numRead':1,'done_mask_commit_cycles':1},['native_declared.mask_done_bits'],[ref(pointer='/adopted_inputs/verify_group_done_commit_ticks_per_attempt')])
        attempt=[use('program_attempts'),use('endpoint_verify'),use('attempt_done')]
        resident=[use('rail_setup'),repeat(512,[use('resident_front'),repeat(2,attempt,'RESET_attempt'),repeat(1,attempt,'masked_SET_attempt')],'16B_transaction'),use('rail_exit')]
        get('endpoint_verify')['call']['policy_link']={'id':'binary_sense_capability','bound_to':'adc_batch','same_physical_ADC':False,'physical_resource':'256 window comparators; distinct T1/IO/BL/SL memory frontend'}
    elif index==5:
        get('direction_write')['call']['inputs'].pop('turn_cycles',None)
        get('direction_write')['call']['inputs'].pop('digital_tick',None)
        get('direction_write')['call']['inputs'].pop('clock_id',None)
        get('direction_write')['call']['timing_role']='opaque complete physical direction-write slot only; polarity turn and terminal capture/compare are separate stages'
        extra('polarity_turn',1024,'turn_cycles',{'numDff':128,'numRead':1},['native_declared.target_register_bits'],[ref(pointer='/stage_coverage/turn')])
        resident=[repeat(1024,[use('encoded_load'),use('direction_write',phase=1,active_MTJs=128),use('polarity_turn'),use('direction_write',phase=2,active_MTJs=64),repeat(2,[use('terminal_verify')],'absolute_verify_branch')],'8B_transaction')]
    elif index==6:
        resident=[repeat(1024,[use('resident_front'),repeat(8,[use('program_reset_set'),repeat(2,[use('endpoint_verify')],'fresh_mux_verify_pass')],'weight_plane')],'row_striped_32B_transaction')]
        v=get('endpoint_verify');v['provider']='neurosim_composed';v['call']['native_components']=[{'provider':'v3_native_service','parameter':'shared_voltage_front','count':1,'includes_input_reset':True},{'provider':'neurosim_native','module':'SarADC','numRead':1,'count':1},{'provider':'neurosim_composed','modules':['Adder','DFF'],'reference_compare_cycles':1,'clock_id':'lv_core'}]
    elif index==7:resident=[repeat(1024,[use('external_load'),use('external_polarization_write')],'aligned_128bit_row')]
    elif index==8:
        resident=[repeat(256,[use('resident_load'),use('current_program')],'16B_transaction')]
        for sid in ('refresh_read','refresh_decode_load_rewrite'):
            get(sid)['provider']='neurosim_composed'
        get('refresh_read')['call']['native_components']=[{'provider':'v3_native_service','parameters':['common_read_overhead','refresh_integration'],'count':1},{'provider':'neurosim_native','module':'SarADC','numRead':1,'count':1},{'provider':'neurosim_composed','operation':'input/reset capability binding','count':1}]
        get('refresh_decode_load_rewrite')['call']['native_components']=[{'provider':'neurosim_composed','operation':'sign decode and encoded port/control','code_bits':128,'encoded_bits':256,'clock_id':'lv_core'},{'provider':'v3_native_service','parameter':'program_complete','count':1}]
    else:
        resident=[repeat(1024,[use('resident_load'),use('two_phase_write'),use('post_pulse_guard'),use('terminal_verify')],'aligned_16B_transaction')]
        get('terminal_verify')['provider']='neurosim_composed';get('terminal_verify')['call']['native_components']=[{'provider':'v3_native_service','parameter':'binary_read','count':1},{'provider':'neurosim_native','module':'DFF','numRead':1,'count':1},{'provider':'neurosim_composed','operation':'128bit compare through16lanes','cycles':8,'clock_id':'lv_core'}]
    maintenance=[repeat(256,[use('refresh_read'),use('refresh_decode_load_rewrite')],'refresh_group_in_fixed_period')] if index==8 else []
    c['service_schedules']={'semantics':'Ordered loops; execute each nested stage before advancing the enclosing group/attempt. Top-level flat dependencies must not globally reorder phases. Zero new payload in maintenance.','streaming':{'per':'vector','steps':streaming},'resident':{'per':'full_matrix','update_domain':1,'steps':resident},'maintenance':{'per':'refresh_period' if index==8 else 'not_scheduled','steps':maintenance}}

def electrical_modes(c,x,index):
    def q(value,unit,pointer,status='retained_v3_mode_input'):
        scale={'V':1,'nA':1e-9,'uA':1e-6,'fF':1e-15,'pF':1e-12,'kOhm':1000,'mV':1e-3}
        si={'V':'V','nA':'A','uA':'A','fF':'F','pF':'F','kOhm':'ohm','mV':'V'}
        normalized=None if value is None else [v*scale[unit] for v in value] if isinstance(value,list) else value*scale[unit]
        return {'value':value,'unit':unit,'normalized_value':normalized,'normalized_unit':si[unit],'status':status,'source_refs':[ref(pointer=pointer)]}
    modes={'native_electrical_parameter_policy':{'read_bias_V':None,'native_RC_load':None,'status':'not_separately_specified_for_instantiated_adapter','fallback':'retain native complete service or stated primitive; never silently use upstream default device/load'}}
    if index==0:
        modes['charge_cell']={'MOM_capacitance':q(1.33,'fF','/raw_evidence/0/original_value','reported_bitcell_anchor_not_complete_frontend_load'),'raw_ADC_transfer':None,'analog_full_scale':None,'reason':'v3 only specifies calibrated partial sums; no voltage-to-code transfer or load closure'}
    elif index==1:modes['complete_MAC']={'array_bias_and_RC':None,'status':'native complete HCA/BFA MAC retained opaque; no separately measured substage imported'}
    elif index==2:modes['page_and_binary_read']={'cell_state':'binary','internal_pulse_voltage':None,'program_parallel_cells':None,'status':'native complete read and page/sector P/E retained; internal implementation not separately specified'}
    elif index==3:
        modes['normal_evaluation']={'gate':q(1,'V','/service_modes/normal_evaluation/bias'),'BL':q(.2,'V','/service_modes/normal_evaluation/bias'),'pass':q(4.5,'V','/service_modes/normal_evaluation/bias'),'on_current':q(2,'nA','/reported_numeric/cell_on_current_nA'),'SL_capacitance':q(16,'pF','/reported_numeric/native_sl_capacitance_pF'),'full_scale':q(25,'uA','/design_choices/current_sense_full_scale_uA')}
        modes['calibration']={'same_electrical_mode_as':'normal_evaluation','reference_WL':2,'source_refs':[ref(pointer='/service_modes/load_calibration')]}
        modes['program_verify']={'bias_and_pulse_decomposition':None,'status':'native full page service includes internal bias,program,verify,recovery; no generic string/RC substitution'}
    elif index==4:
        modes['normal_evaluation']={'VBL':q(.3,'V','/adopted_inputs/binary_windows/qualification'),'VWL':q(.6,'V','/adopted_inputs/binary_windows/qualification'),'VTBL':q(.1,'V','/adopted_inputs/binary_windows/qualification'),'ON_current_reference':q(.5,'uA','/adopted_inputs/binary_windows/qualification'),'HRS_contribution':'low after same-bias calibration; not assigned zero','m':1,'active_terms':32}
        modes['memory_endpoint']={'LRS_window':q([8,12],'kOhm','/adopted_inputs/binary_windows/LRS_resistance_kOhm'),'HRS_min':q(70,'kOhm','/adopted_inputs/binary_windows/HRS_min_resistance_kOhm'),'memory_read_bias_V':None,'qualification':'Independent T1/IO/BL/SL memory path; conditional window budget, not CIM transfer equivalence'}
        modes['program']={'SET_initial':q(1.2,'V','/adopted_inputs/program_voltages/initial_SET_V'),'RESET_initial':q(1.5,'V','/adopted_inputs/program_voltages/initial_RESET_V'),'same_polarity_retry_increment':q(.1,'V','/adopted_inputs/program_voltages/increment_on_same_polarity_retry_V'),'reference_RESET_attempts':2,'reference_SET_attempts':1,'retry_RESET_sequence_V':[1.5,1.6],'retry_SET_sequence_V':[1.2],'source_refs':[ref(pointer='/adopted_inputs/group_attempt_scenarios/reference')]}
    elif index==5:modes['IBMD']={'state':'P/AP complementary pair','R_P_ohm':None,'R_AP_ohm':None,'actual_pulse_current_A':None,'actual_read_bias_V':None,'status':'full direction-write/read slots retained; 200uA driver rating is not actual switching current','source_refs':[ref(pointer='/driver_budget'),ref(pointer='/stage_coverage')]}
    elif index==6:modes['voltage_sum']={'active_WL':8,'IM_A':None,'clamp_V':None,'native_column_load_F':None,'raw_ADC_transfer':None,'reference_verify_mode':'same configured IM/clamp/load conditional mode,oneWL per verify; excludes optional0.2V weak observation mode','status':'not_separately_specified; retain v3 shared full front and mode qualification','source_refs':[ref(pointer='/service_modes/normal_evaluation'),ref(pointer='/service_modes/endpoint_verify')]}
    elif index==7:modes['read_restore_write']={'memory_voltage':q(2.5,'V','/drive_resources/memory_voltage_V'),'BL_capacitance':q(250,'fF','/drive_resources/BL_capacitance_fF','transplanted_load_condition'),'FeCAP_area_um2':1,'FeCAP_area_m2':1e-12,'two_Pr_lower_bound_uC_per_cm2':40,'two_Pr_lower_bound_C_per_m2':.4,'PL_total_capacitance_F':None,'PL_complete_current_rating_A':None,'reason':'polarization lower bound plus dielectric/routing load is not a sufficient PL rating','source_refs':[ref(pointer='/drive_resources')]}
    elif index==8:modes['GC04']={'endpoint_current':q([0,700],'nA','/reported_evidence/0/value'),'program_BL_load':q(50,'fF','/write/load_isolation','program_load_condition_with_added_integrator_isolated'),'differential_integrator_each_branch':q(200,'fF','/refresh/integration_capacitance_fF_per_branch'),'ADC_differential_range':q([-224,224],'mV','/refresh/differential_adc_range_mV'),'operating_rail_voltages_V':None,'cell_technology':'silicon CMOS3T1C; original65nm source; not low-voltage peripheral node scaling','source_refs':[ref(pointer='/nominal_diagnostic_model')]}
    else:modes['vertical_AND_FeFET']={'selected_gate_channel':q(2,'V','/resident/full_selected_gate_channel_V'),'local_bias_scheme':x['resident']['write_bias_scheme'],'driven_node_load_limit':q(100,'fF','/engineering_driver_budget/maximum_effective_capacitance_per_driven_node_fF','qualification_limit_not_measured_actual_RC'),'read_bias_V':None,'read_bias_status':'complete40ns engineering read retained; source-0.5V stress pulse is not silently transplanted as operating bias','source_refs':[ref(pointer='/engineering_read_budget')]}
    c['device']['mode_inputs']=modes

def specify(c,x,r,index):
    # Filled below with per-case, source-grounded stage schedules.
    if index==0:
        c['device']['primitives']=[primitive('charge_front',20,'ns',[ref(pointer='/scenarios/1/frontend_complete_ns')],kind='opaque_complete_front',mode='normal_evaluation',includes=['input reset','charge array settle','selected column ADC readiness']),primitive('sram_write_cycle',5,'ns',[ref(pointer='/scenarios/1/complete_memory_cycle_ns')],kind='opaque_complete_cycle',mode='resident_write',includes=['command/address/data capture','BL/WL drive','cell flip','recovery to compute-ready'])]
        c['physical']['access_direction']='128 logical input rows across each of eight binary planes; 16 selected output columns/plane per evaluation; HCA bypassed.'
        c['services']=[stage('charge_front','streaming','v3_native_service','check_sram_acim.calculate / retained frontend_complete_ns',64,'evaluations','vector',{'duration_parameter':'charge_front'},['adc_count','physical.native'],[ref(pointer='/cycle_semantics/frontend')],included=['input_step','array settling']),stage('sar','streaming','neurosim_native','SarADC::Initialize; SarADC::CalculateLatency',64,'batches','vector',{'numCol':128,'levelOutput':1024,'numRead':1,'shared_binding':'adc_batch'},['adc_count'],[ref('shared','/reference_instance/acim')],depends=['charge_front']),stage('reconstruct','streaming','neurosim_composed','AdderTree::CalculateLatency; ShiftAdd::CalculateLatency; DFF::CalculateLatency',128,'cycles','vector',{'shared_binding':'digital_tick','clock_id':'lv_core','output_bits':23},['digital_output_channels'],[ref('shared','/reference_instance/acim')],depends=['sar']),stage('sram_write','resident','v3_native_service','check_sram_acim.block / retained complete_memory_cycle_ns',1024,'transactions','full_matrix',{'duration_parameter':'sram_write_cycle','payload_Byte':16,'encoded_bits':128},['real_write_driver_count','encoded_interface_bits'],[ref(pointer='/cycle_semantics/memory')],included=['one-beat write front','ordinary SRAM update'])]
        c['unresolved']=[{'id':'charge_front_physics','status':'retained_v3_service','reason':'NeuroSim generic current-resistance array is not the 9T1C charge frontend. Preserve front and replace only explicitly uncovered SAR/digital stages.'}]
    elif index==1:
        c['device']['primitives']=[primitive('native_mac_cycle',5,'ns',[ref(pointer='/scenarios/1/complete_compute_round_ns')],kind='opaque_complete_cycle',mode='normal_evaluation',includes=['static weight connection','SRAM/NOR read','HCA/BFA reduction','sign handling','local accumulation']),primitive('sram_write_cycle',5,'ns',[ref(pointer='/scenarios/1/complete_memory_cycle_ns')],kind='opaque_complete_cycle',mode='resident_write',includes=['command/address/data capture','BL/WL drive','cell flip','recovery'])]
        c['physical']['access_direction']=x['device_state_and_mapping']['mapping']
        c['services']=[stage('native_mac','streaming','v3_native_service','check_sram_dcim.compute / complete_compute_round_ns',64,'complete_MAC_cycles','vector',{'duration_parameter':'native_mac_cycle','terms':16,'outputs':16,'input_slices':8,'row_groups':8},['native_declared.installed_HCA_BFA'],[ref(pointer='/cycle_semantics/compute_slot')],included=['native read','HCA/BFA','sign','accumulate']),stage('sram_write','resident','v3_native_service','check_sram_dcim.block / complete_memory_cycle_ns',128,'transactions','full_matrix',{'duration_parameter':'sram_write_cycle','payload_Byte':16},['real_write_driver_count','encoded_interface_bits'],[ref(pointer='/cycle_semantics/memory_slot')],included=['one-beat write front','ordinary SRAM update'])]
        c['unresolved']=[{'id':'d6cim_mac','status':'retained_opaque','reason':'DCIM branch generic adder tree is not D6CIM HCA/BFA. No ADC and no extra read or generic MAC latency on top of the complete native cycle.'}]
    elif index==2:
        c['device']['primitives']=[primitive('nor_read',120,'ns',[ref(pointer='/scenarios/1/read_full_ns')],kind='opaque_complete_cycle',mode='binary_read',includes=['selection','bias settle','binary sense','result ready']),primitive('page_program',0.4,'ms',[ref(pointer='/scenarios/1/page_program_ms')],kind='opaque_complete_cycle',mode='program',includes=['internal program','verify loops','recovery to ready']),primitive('sector_erase',45,'ms',[ref(pointer='/scenarios/1/sector_erase_ms')],kind='opaque_complete_cycle',mode='erase',includes=['native erase sequence','ready status'])]
        c['physical']['access_direction']=x['mapping']['resident_partition'];c['physical']['native_page_Byte']=256;c['physical']['native_sector_Byte']=4096
        c['services']=digital_read_stages(c,32,'nor_read','check_nor.evaluate',ref(pointer='/stage_coverage/read_full'))
        c['services'] += [stage('page_load','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',64,'pages','full_matrix',{'encoded_bits':2048,'port_bits':128,'data_beats':16,'control_cycles':2,'digital_tick':'binding','clock_id':'lv_core'},['native_declared.page_buffer_bits','encoded_interface_bits'],[ref(pointer='/stage_coverage/write_front')]),stage('page_program','resident','v3_native_service','check_nor.evaluate / page_program_ms',64,'pages','full_matrix',{'duration_parameter':'page_program','page_Byte':256},['native_declared.physical_write_parallelism'],[ref(pointer='/stage_coverage/program_full')],included=['internal verify','native HV setup/recovery'],depends=['page_load']),stage('sector_erase','resident','v3_native_service','check_nor.evaluate / sector_erase_ms',4,'sectors','full_matrix',{'duration_parameter':'sector_erase','control_cycles_per_erase':2,'digital_tick':'binding','clock_id':'lv_core'},['external_update_domains'],[ref(pointer='/stage_coverage/erase_full')],included=['native erase and recovery'])]
        c['unresolved']=[{'id':'native_page_engine','status':'retained_opaque','reason':'No native NOR page program/erase implementation in selected generic resistive array. Internal cell parallelism is not reported and cannot be inferred from 128-bit port.'}]
    elif index==3:
        primitives=[('sl_setup',640,'ns','/design_choices/sl_setup_budget_ns_by_profile/reference'),('bl_setup',12,'ns','/reported_numeric/bl_setup_ns'),('wl_setup',303,'ns','/reported_numeric/wl_setup_ns'),('cell_on_current',2,'nA','/reported_numeric/cell_on_current_nA'),('sl_capacitance',16,'pF','/reported_numeric/native_sl_capacitance_pF'),('frontend_full_scale',25,'uA','/design_choices/current_sense_full_scale_uA'),('page_program',300,'us','/design_choices/program_full_budget_us_by_profile/reference'),('block_erase',1,'ms','/design_choices/erase_full_budget_ms_by_profile/reference')]
        c['device']['primitives']=[primitive(a,b,u,[ref(pointer=p)],kind='opaque_complete_cycle' if a in ('page_program','block_erase') else 'native_or_engineering_primitive',mode='page_program_verify' if a=='page_program' else 'native_string_read') for a,b,u,p in primitives]
        for p in c['device']['primitives']:
            if p['id']=='page_program':p['included_stages']=['pump/driver setup','all program/verify loops','recovery to ready']
        c['device']['mode_bias_load_endpoint']=x['service_modes']
        c['physical']['access_direction']='64 native blocks;32 WL/block;3 SSL/WL;13824 bitline page;30 data and2 calibration WL;positive/negative magnitude blocks; four base4 digits; LSB once/MSB twice; three input copies.'
        c['physical']['native_mapping']=x['mapping']; c['physical']['reference_storage_sites']=5308416
        c['resources']['installed'].update({'mux_channels':13824,'mux_fanin':None,'resident_staging_bits':41472,'resident_staging_read_width_bits':144,'data_page_effective_encoded_bits_per_tick':48,'reference_page_effective_encoded_bits_per_tick':128,'page_buffer_bits':13824,'real_write_driver_count':None,'native_page_program_targets':13824,'calibration_coeff_register_bits':12288})
        c['resources']['active']['resident'].update({'physical_pages_per_matrix':6144,'data_pages':5760,'reference_pages':384,'erase_blocks':64,'native_program_domains':1})
        c['services']=[stage('input_magnitude_sign','streaming','neurosim_composed','AdderTree/ShiftAdd/DFF candidate signed-to-magnitude datapath',288,'cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','logical_inputs':4608,'lanes':16},['native_declared.input_encoding_lanes','native_declared.input_sign_register_bits'],[ref('calculator',function='scenario')]),stage('native_wl','streaming','v3_native_service','check_nand.scenario / wl_setup_ns',30,'WL_setups','vector',{'duration_parameter':'wl_setup'},['physical.native_mapping'],[ref(pointer='/reported_numeric/wl_setup_ns')]),stage('native_bl_sl','streaming','v3_native_service','check_nand.scenario / BL_formation + SL_establishment',960,'evaluations','vector',{'duration_parameters':['bl_setup','sl_setup'],'input_sign_phases':2,'input_base4_digits':4,'row_groups':4,'output_WL_groups':30},['native_declared.current_frontends'],[ref(pointer='/service_parameter_bindings/normal_evaluation')],included=['input_step via native BL formation'],depends=['input_magnitude_sign','native_wl']),stage('sar','streaming','neurosim_native','SarADC::Initialize; SarADC::CalculateLatency',960,'batches','vector',{'adc_batch':'binding','numCol':64,'levelOutput':1024,'numRead':1},['adc_count'],[ref(pointer='/design_choices/quantization_diagnostic')],depends=['native_bl_sl']),stage('affine_merge_sign','streaming','neurosim_composed','AdderTree::CalculateLatency; ShiftAdd::CalculateLatency; DFF::CalculateLatency',3840,'cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','operations':['affine correction','base4 merge','weight polarity subtraction','signed input accumulation']},['native_declared.affine_multipliers','native_declared.base4_merge_trees','digital_output_channels'],[ref(pointer='/design_choices/read_order')],depends=['sar']),stage('resident_encode','resident','neurosim_composed','DFF/Buffer plus signed-magnitude formatter; circuit realization unresolved',69120,'cycles','full_matrix',{'digital_tick':'binding','clock_id':'lv_core','rows':240,'cycles_per_row':288,'staging_bits':41472},['native_declared.resident_encoding_lanes','native_declared.resident_row_staging_bits'],[ref(pointer='/design_choices/resident_encoding_lifecycle')]),stage('page_load','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',6144,'pages','full_matrix',{'digital_tick':'binding','clock_id':'lv_core','data_page_beats':288,'reference_page_beats':108,'control_cycles':2,'data_pages':5760,'reference_pages':384,'nominal_port_bits':128,'data_effective_bits':48},['encoded_interface_bits','native_declared.page_buffer_bits'],[ref(pointer='/resident/data_page_effective_encoded_bits_per_beat'),ref(pointer='/resident/reference_page_effective_encoded_bits_per_beat')],depends=['resident_encode']),stage('page_program','resident','v3_native_service','check_nand.scenario / program_full_ns',6144,'opaque_page_programs','full_matrix',{'duration_parameter':'page_program','page_bits':13824},['native_declared.actual_write_domain'],[ref(pointer='/resident/P_includes')],included=['HV setup','verify/retry','recovery'],depends=['page_load']),stage('block_erase','resident','v3_native_service','check_nand.scenario / erase_full_ns',64,'opaque_block_erases','full_matrix',{'duration_parameter':'block_erase'},['external_update_domains'],[ref(pointer='/design_choices/erase_full_budget_ms_by_profile/reference')]),stage('load_calibration','resident','v3_native_service','check_nand.scenario / calibration schedule',1,'calibration','full_matrix',{'wl_setup_count':2,'analog_rounds':12,'arithmetic_cycles':450,'duration_parameters':['wl_setup','bl_setup','sl_setup'],'adc_batch':'binding','digital_tick':'binding','clock_id':'lv_core','publish_requires':'all page verify and half-input residual <=4 nominal ADC codes'},['native_declared.calibration_gain_offset_register_bits','native_declared.calibration_arithmetic_lanes','adc_count'],[ref(pointer='/design_choices/calibration'),ref(pointer='/service_parameter_bindings/load_calibration')],depends=['page_program','block_erase'])]
        c['unresolved']=[{'id':'nand_string_and_calibration','status':'retained_v3_service','reason':'Native NAND WL/SSL/SL organization and full page/block engine have no validated substitute in generic NeuroSim NVM. Native current front is preserved; ADC/digital replacement must also propagate to load calibration.'}]
    elif index==4:
        vals=[('cim_front',5,'ns','/adopted_inputs/front_end_settle_ns/value'),('memory_verify_front',5,'ns','/adopted_inputs/binary_verify_frontend_ns/value'),('reset_pulse',1000,'ns','/adopted_inputs/program_pulse_ns/RESET'),('set_pulse',1000,'ns','/adopted_inputs/program_pulse_ns/SET'),('local_setup',100,'ns','/adopted_inputs/high_voltage_setup_ns_per_attempt/by_profile/reference'),('local_return',100,'ns','/adopted_inputs/high_voltage_return_recover_ns_per_attempt/by_profile/reference'),('rail_setup',1000,'ns','/adopted_inputs/rail_lifecycle_ns/setup'),('rail_exit',1000,'ns','/adopted_inputs/rail_lifecycle_ns/exit')]
        c['device']['primitives']=[primitive(a,b,u,[ref(pointer=p)],mode='CIM' if a=='cim_front' else 'memory_program_or_verify') for a,b,u,p in vals]
        c['device']['mode_bias_load_endpoint']=x['service_modes'];c['physical']['access_direction']=x['configuration']['native_organization'];c['physical']['update_mapping']=x['configuration']['physical_update_mapping']
        c['resources']['installed'].update({'binary_window_comparators':256,'program_voltage_rating_V':1.8,'program_current_rating_uA_per_lane':300,'program_current_rating_mA_total':38.4,'switched_load_limit_pF_per_lane':1,'mux_groups_per_plane':2})
        c['services']=analog_stages(c,128,'cim_front',False,ref(pointer='/service_modes/0'))
        c['services'] += [stage('rail_setup','resident','v3_native_service','check_rram.write_service / rail_setup_ns',1,'rail_start','full_matrix',{'duration_parameter':'rail_setup'},['external_update_domains'],[ref(pointer='/adopted_inputs/rail_lifecycle_ns')]),stage('program_attempts','resident','v3_native_service','check_rram.write_service / finite RESET then masked SET',512,'transactions','full_matrix',{'transaction_Byte':16,'reset_attempts':2,'set_attempts':1,'duration_parameters':['reset_pulse','set_pulse','local_setup','local_return'],'digital_tick':'binding','clock_id':'lv_core','control_cycles_per_attempt':2,'first_data_in_command':True,'front_data_beats':1,'front_control_cycles':2},['real_write_driver_count','binary_window_comparators'],[ref(pointer='/adopted_inputs/group_attempt_scenarios/reference'),ref('calculator',function='write_service')],depends=['rail_setup']),stage('endpoint_verify','resident','v3_native_service','check_rram.write_service / independent memory path window comparator',1536,'attempt_verifies','full_matrix',{'input_step':'binding','duration_parameter':'memory_verify_front','adc_batch':'common capability policy for binary sense, not shared physical ADC','LRS_window_kOhm':[8,12],'HRS_min_kOhm':70},['binary_window_comparators'],[ref(pointer='/adopted_inputs/binary_sense_slot_ns'),ref(pointer='/adopted_inputs/binary_windows')],depends=['program_attempts']),stage('rail_exit','resident','v3_native_service','check_rram.write_service / rail_exit_ns',1,'rail_exit','full_matrix',{'duration_parameter':'rail_exit','commit_condition':'all lanes meet both window endpoints within finite attempts; else invalid matrix'},['external_update_domains'],[ref(pointer='/adopted_inputs/failure_policy')],depends=['endpoint_verify'])]
        c['unresolved']=[{'id':'wh2t1r','status':'retained_v3_frontend','reason':'Preserve resistive divider to T2 subthreshold current and shared TBL/CIMSEL; direct conductance-array RRAM model is not a transfer-equivalent device.'},{'id':'finite_attempt_qualification','status':'conditional_input','reason':'2 RESET/1 SET are finite engineering budgets, not measured yield probabilities; no hidden rescue or retry.'}]
    elif index==5:
        c['device']['primitives']=[primitive('ibmd_read',5,'ns',[ref(pointer='/scenarios/1/read_response_ns')],kind='opaque_complete_slot',mode='read_or_low_bias_branch_verify',includes=['initialization','sense/reset','tap/mux selection']),primitive('direction_write_slot',30,'ns',[ref(pointer='/scenarios/1/write_access_slot_ns')],kind='opaque_complete_slot',mode='resident_directional_write',includes=['drive initialization','pulse/switching','stop/recovery'])]
        c['physical']['access_direction']=x['mapping']['bank_address'];c['physical']['native_mapping']=x['mapping']
        c['resources']['installed'].update({'installed_ibmd_digitizers':65536,'active_ibmd_digitizers':4096,'mux_channels':4096,'mux_fanin':16,'absolute_verify_sense_lanes':64,'verify_state_latch_bits':128,'verify_comparators':64,'additional_AND_gates':4096,'write_current_rating_uA_per_lane':200,'write_SL_rating_mA':25.6})
        c['resources']['active']['resident'].update({'selected_pairs':64,'phase1_active_MTJs':128,'phase2_active_MTJs':64,'terminal_verify_branch_batches':2,'full_load_transactions':1024})
        c['services']=digital_read_stages(c,16,'ibmd_read','check_mram.calculate',ref(pointer='/stage_coverage/stream'))
        c['services'] += [stage('encoded_load','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',1024,'transactions','full_matrix',{'logical_Byte':8,'encoded_bits':128,'digital_tick':'binding','clock_id':'lv_core','data_beats':1,'control_cycles':2,'first_data_in_command':True},['encoded_interface_bits','native_declared.target_register_bits'],[ref(pointer='/mapping/encoding_location')]),stage('direction_write','resident','v3_native_service','check_mram.calculate / two complete direction slots',2048,'direction_slots','full_matrix',{'duration_parameter':'direction_write_slot','finite_attempts':1,'direction_slots_per_transaction':2,'phase1_MTJs':128,'phase2_MTJs':64,'turn_cycles':1,'digital_tick':'binding','clock_id':'lv_core'},['real_write_driver_count'],[ref(pointer='/stage_coverage/write_access'),ref(pointer='/retry_model')],included=['pulse start/stop/recovery'],depends=['encoded_load']),stage('terminal_verify','resident','v3_native_service','check_mram.calculate / both-branch absolute-state verification',2048,'branch_reads','full_matrix',{'duration_parameter':'ibmd_read','branches_per_transaction':2,'digital_tick':'binding','clock_id':'lv_core','capture_cycles_per_branch':1,'compare_cycles_per_branch':1,'verify_payload':'128 physical states,64 expected complementary pairs','failure':'no completed logical payload'},['absolute_verify_sense_lanes','verify_state_latch_bits','verify_comparators'],[ref(pointer='/stage_coverage/verify_read'),ref(pointer='/mapping/verify_branch_batches')],depends=['direction_write'])]
        c['unresolved']=[{'id':'ibmd_tap','status':'retained_v3_service','reason':'Generic MTJ enum does not instantiate original IBMD tap/isolation or complementary write and absolute branch verification.'}]
    elif index==6:
        vals=[('shared_voltage_front',20,'ns','/profiles/reference/read_front_including_TI_ns'),('drive_transition',20,'ns','/profiles/reference/drive_transition_ns'),('reset_pulse',125,'ns','/program/reset_pulse_ns'),('set_complete_pulse',300,'ns','/program/set_total_budget_ns'),('reset_current',700,'uA','/program/reset_current_uA'),('set_current',125,'uA','/program/set_current_uA')]
        c['device']['primitives']=[primitive(a,b,u,[ref(pointer=p)],kind='complete_front' if a=='shared_voltage_front' else 'primitive_budget',mode='evaluation_and_verify' if a=='shared_voltage_front' else 'program') for a,b,u,p in vals]
        c['device']['primitives'][0]['included_stages']=['input_step','read reset','voltage settle']
        c['device']['primitives'][3]['included_stages']=['250ns plateau','50ns trailing edge']
        c['device']['mode_bias_load_endpoint']=x['service_modes'];c['physical']['access_direction']=x['mapping']['mode_access_selection'];c['physical']['update_mapping']=x['mapping']['transaction_pattern']
        c['resources']['installed'].update({'mux_channels':128,'mux_fanin':8,'IDAC_count':32,'return_RESET_rating_mA':22.4,'return_SET_rating_mA':4,'transaction_buffer_bits':256,'write_mask_bits':32,'column_mode_isolation_channels':1024,'per_cell_gate_mux':False})
        c['resources']['active']['resident'].update({'one_selected_WL':True,'physical_columns_per_batch':32,'serial_planes':8,'verify_passes_per_plane':2,'full_load_transactions':1024})
        c['services']=analog_stages(c,2048,'shared_voltage_front',True,ref(pointer='/service_modes/normal_evaluation'))
        c['services'] += [stage('resident_front','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',1024,'transactions','full_matrix',{'encoded_bits':256,'digital_tick':'binding','clock_id':'lv_core','data_beats':2,'first_data_in_command':True,'control_cycles':2},['encoded_interface_bits','transaction_buffer_bits'],[ref('calculator',function='compute')]),stage('program_reset_set','resident','v3_native_service','check_pcm.compute / 8-plane row-striped current programming',8192,'32_cell_batches','full_matrix',{'duration_parameters':['drive_transition','reset_pulse','set_complete_pulse'],'driver_transitions_per_batch':3,'reset_attempts':1,'set_attempts':1,'digital_tick':'binding','clock_id':'lv_core','selection_cycles_per_batch':1,'reset_current':'qualification','set_current':'qualification'},['IDAC_count','return_RESET_rating_mA','return_SET_rating_mA'],[ref(pointer='/program/pulse_sequence'),ref('calculator',function='geometry')],included=['SET tail once'],depends=['resident_front']),stage('endpoint_verify','resident','v3_native_service','check_pcm.compute / fresh single-row endpoint read and SAR',16384,'fresh_verify_passes','full_matrix',{'duration_parameter':'shared_voltage_front','adc_batch':'binding','digital_tick':'binding','clock_id':'lv_core','comparison_cycles':1,'verify_columns_per_pass':16,'passes_per_plane':2,'full_refresh_of_front_each_pass':True},['adc_count','mux_channels','mux_fanin'],[ref(pointer='/service_modes/endpoint_verify'),ref(pointer='/mapping/verify_rule')],included=['input_step in complete front'],depends=['program_reset_set'])]
        c['unresolved']=[{'id':'pcm_voltage_sum','status':'retained_v3_service','reason':'Voltage-domain IM/clamp/8-WL transfer and q=0/1 settling are not generic conductance summation; mode-specific endpoint thresholds remain required.'}]
    elif index==7:
        vals=[('feram_sense',20,'ns','/paired_media_budgets_ns/reference/sense'),('polarization_hold',50,'ns','/paired_media_budgets_ns/reference/polarization_hold_per_phase'),('open_close',40,'ns','/paired_media_budgets_ns/reference/open_close_bias_total'),('memory_voltage',2.5,'V','/drive_resources/memory_voltage_V'),('BL_load',250,'fF','/drive_resources/BL_capacitance_fF'),('BL_rating',80,'uA','/drive_resources/BL_installed_rating_uA')]
        c['device']['primitives']=[primitive(a,b,u,[ref(pointer=p)],mode='read_restore_and_external_write') for a,b,u,p in vals]
        c['physical']['access_direction']=x['mapping']['logical_to_physical'];c['physical']['native_mapping']=x['mapping'];c['physical']['reference_storage_sites']=4096
        c['resources']['installed'].update({'restore_BL_drivers':4096,'external_BL_drivers':128,'read_restore_PL_domains':32,'mux_channels':4096,'mux_fanin':32,'operand_hold_banks':1,'added_operand_hold_bits':0,'BL_rating_uA':80})
        c['resources']['active']['resident'].update({'external_selected_rows':1,'target_bits':128,'polarization_phases':2,'full_load_transactions':1024});c['resources']['active']['streaming'].update({'read_restore_rows':32,'restored_bits_per_read':4096})
        c['services']=digital_read_stages(c,32,'feram_sense','check_feram.make_row',ref(pointer='/stage_coverage/read_includes'),existing_capture=True)
        c['services'][0]['call']['inputs'].update({'duration_parameters':['feram_sense','polarization_hold','open_close'],'restore_phases':1,'operand_capture_already_in_open_close':True,'no_extra_restore':True})
        c['services'][0]['included_stages']=['precharge/reference','WL/PL establish','sense/latch','existing operand capture','one polarization restore','line return/reset']
        c['services'] += [stage('external_load','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',1024,'transactions','full_matrix',{'digital_tick':'binding','clock_id':'lv_core','encoded_bits':128,'data_beats':1,'control_cycles':2,'first_data_in_command':True},['encoded_interface_bits'],[ref(pointer='/stage_coverage/write_includes')]),stage('external_polarization_write','resident','v3_native_service','check_feram.make_row / two target polarity holds and edges',1024,'physical_rows','full_matrix',{'duration_parameters':['open_close','polarization_hold'],'holds_per_row':2,'external_BLs':128,'logical_Byte':16,'memory_voltage':'qualification','BL_load':'qualification','BL_rating':'qualification'},['external_BL_drivers'],[ref(pointer='/mapping/plate_sequence'),ref(pointer='/stage_coverage/write_includes')],depends=['external_load'])]
        c['unresolved']=[{'id':'feram_restore','status':'retained_v3_service','reason':'HZO polarization/read-destruct/restore timing and 4096-BL plus32-PL supply are not generic capacitive or FeFET model behavior. PL total load/rating remains unqualified, not zero.'}]
    elif index==8:
        vals=[('program_complete',65,'ns','/profiles/1/program_complete_ns'),('common_read_overhead',86,'ns','/service_parameters/profile_common_overhead_ns/reference'),('mac_integration',1,'ns','/service_parameters/mac_integration_ns'),('refresh_integration',64,'ns','/service_parameters/refresh_integration_ns'),('refresh_period',400000,'ns','/refresh/period_ns'),('integration_capacitance',200,'fF','/refresh/integration_capacitance_fF_per_branch')]
        c['device']['primitives']=[primitive(a,b,u,[ref(pointer=p)],kind='opaque_complete_cycle' if a=='program_complete' else 'engineering_primitive',mode='current_program' if a=='program_complete' else 'mode_dependent_read') for a,b,u,p in vals]
        c['device']['primitives'][0]['included_stages']=['5ns coarse program','60ns fine current-feedback/self-calibration','no separate program verify']
        c['device']['mode_bias_load_endpoint']=x['service_modes']['early_release'];c['device']['release_policy']='early_release';c['device']['retained_endpoint_current_nA']=700
        c['physical']['access_direction']='Eight64x64 pseudo-differential pair tiles,one binary plane per tile;each pair stores(700,0)or(0,700)nA;two3T1C cells per bit.'
        c['resources']['installed'].update({'pair_write_drivers':128,'write_branches':256,'refresh_sign_decoders':128,'refresh_code_hold_bits':128,'full_matrix_shadow_bits':0,'integration_capacitance_fF_per_branch':200,'integration_total_pF':51.2,'program_original_BL_load_fF':50})
        c['resources']['active']['resident'].update({'logical_Byte':16,'pairs':128,'branches':256,'encoded_bits':256,'data_beats':2,'transactions':256})
        c['services']=analog_stages(c,32,'common_read_overhead',False,ref(pointer='/service_modes/early_release'))
        c['services'][0]['call']['inputs'].update({'duration_parameters':['common_read_overhead','mac_integration'],'integration_capacitance':'qualification','mode_release':'after1ns integration plus mandatory common overhead'})
        c['services'] += [stage('resident_load','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',256,'transactions','full_matrix',{'digital_tick':'binding','clock_id':'lv_core','encoded_bits':256,'data_beats':2,'control_cycles':2,'first_data_in_command':True},['encoded_interface_bits'],[ref(pointer='/write/encoded_load_bits')]),stage('current_program','resident','v3_native_service','check_gain_cell_edram.calc / complete feedback program',256,'pair_write_groups','full_matrix',{'duration_parameter':'program_complete','pairs_per_group':128,'branch_targets':256,'program_load_fF':50,'isolate_added_integrator':True},['pair_write_drivers','write_branches'],[ref(pointer='/write/load_isolation')],included=['current feedback and settling','no separate verify'],depends=['resident_load']),stage('refresh_read','maintenance','v3_native_service','check_gain_cell_edram.calc / same read path,64ns integration',256,'single_row_groups','refresh_period',{'period_parameter':'refresh_period','input_step':'binding','duration_parameters':['common_read_overhead','refresh_integration'],'adc_batch':'binding','integration_capacitance':'qualification','logical_payload_Byte':0},['adc_count','refresh_code_hold_bits'],[ref(pointer='/refresh'),ref(pointer='/service_modes/early_release/service_bindings/refresh_read')]),stage('refresh_decode_load_rewrite','maintenance','v3_native_service','check_gain_cell_edram.calc / sign decode,encoded load,feedback rewrite',256,'groups','refresh_period',{'digital_tick':'binding','clock_id':'lv_core','sign_decode_cycles':1,'encoded_bits':256,'data_beats':2,'front_control_cycles':2,'first_data_in_command':True,'duration_parameter':'program_complete','logical_payload_Byte':0},['refresh_sign_decoders','refresh_code_hold_bits','pair_write_drivers'],[ref(pointer='/refresh/decode_ticks'),ref('calculator',function='calc')],depends=['refresh_read'])]
        c['unresolved']=[{'id':'gc04_current_program_and_read','status':'retained_v3_service','reason':'GC-04 is silicon CMOS pseudo-differential3T1C current-feedback memory. MLP hybrid/2T1F and generic capacitance aliases cannot replace its program,1ns/64ns integration or maintenance.'}]
        c['implementation_plan']['maintenance']={'period_parameter':'refresh_period','busy':'sum actual256(read+decode+load+rewrite) group occupations','guard':'max(nonpreemptive evaluation group,ordinary write group)','availability':'1-(busy+guard)/period; reject <=0, no clamp','old_rho_tau_imported':False,'demand_write_refresh_credit':False}
    elif index==9:
        vals=[('binary_read',40,'ns','/profiles/1/complete_binary_read_ns'),('bias_transition',10,'ns','/profiles/1/bias_transition_ns'),('polarization_pulse',20,'ns','/resident/pulse_width_ns'),('post_pulse_guard',100,'ns','/resident/guard_after_final_pulse_ns'),('selected_gate_channel',2,'V','/resident/full_selected_gate_channel_V'),('bias_node_load',100,'fF','/engineering_driver_budget/maximum_effective_capacitance_per_driven_node_fF'),('node_current_rating',60,'uA','/engineering_driver_budget/installed_slew_current_uA_per_node')]
        c['device']['primitives']=[primitive(a,b,u,[ref(pointer=p)],kind='opaque_complete_slot' if a=='binary_read' else 'primitive_budget',mode='binary_read_or_polarization_write') for a,b,u,p in vals]
        c['device']['primitives'][0]['included_stages']=['row/layer/output selection','read bias/RC','binary sense/recovery']
        c['device']['primitives'][3]['included_stages']=['final bias return']
        c['physical']['access_direction']=x['mapping']['physical_address'];c['physical']['native_mapping']=x['mapping']
        c['resources']['installed'].update({'mux_channels':4096,'mux_fanin':8,'operand_hold_banks':1,'write_compare_lanes':16,'selected_write_targets':128,'selected_write_strips':8,'bias_nodes':288,'bias_current_rating_uA_per_node':60,'bias_supply_rating_mA':17.28})
        c['services']=digital_read_stages(c,32,'binary_read','check_fenor.recompute',ref(pointer='/engineering_read_budget'))
        c['services'] += [stage('resident_load','resident','neurosim_composed','Buffer::CalculateLatency; DFF::CalculateLatency',1024,'transactions','full_matrix',{'digital_tick':'binding','clock_id':'lv_core','encoded_bits':128,'data_beats':1,'control_cycles':2,'first_data_in_command':True},['encoded_interface_bits'],[ref(pointer='/resident/encoded_load_bits')]),stage('two_phase_write','resident','v3_native_service','check_fenor.write_service / opposite polarity masked strip writes',1024,'batches','full_matrix',{'duration_parameters':['bias_transition','polarization_pulse'],'bias_edges_before_final':3,'pulses':2,'selected_gate_channel':'qualification','bias_node_load':'qualification','node_current_rating':'qualification','selected_cells':128,'strips':8},['selected_write_targets','selected_write_strips','bias_nodes'],[ref(pointer='/resident/write_bias_scheme')],depends=['resident_load']),stage('post_pulse_guard','resident','v3_native_service','check_fenor.write_service / max(guard,final_return)',1024,'guards','full_matrix',{'duration_parameters':['post_pulse_guard','bias_transition'],'operation':'max','final_return_included':True},['external_update_domains'],[ref(pointer='/resident/guard_after_final_pulse_ns')],included=['final return; do not add fourth edge'],depends=['two_phase_write']),stage('terminal_verify','resident','v3_native_service','check_fenor.write_service / binary read then capture and compare',1024,'terminal_reads','full_matrix',{'duration_parameter':'binary_read','digital_tick':'binding','clock_id':'lv_core','capture_cycles':1,'compare_cycles':8,'sense_bits':128,'compare_lanes':16,'failure':'exception;no invented retry count'},['operand_hold_bits','write_compare_lanes'],[ref(pointer='/resident/verify_policy')],depends=['post_pulse_guard'])]
        c['unresolved']=[{'id':'vertical_and_fefet','status':'retained_v3_service','reason':'Generic FeFET enum does not reproduce strip/layer inhibit,opposite pulse phases,post-write observation or native digital read.'}]
    # Vector boundary capture/commit are separate from analog input/reset or native operand capture.
    streaming=[s for s in c['services'] if s['service_kind']=='streaming']
    capture=stage('input_capture','streaming','neurosim_native','DFF::Initialize; DFF::CalculateLatency',1,'cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','numRead':1,'numDff':c['logical']['K']*8},['input_register_bits'],[ref('shared','/resource_policy/input_capture_ticks')])
    commit=stage('output_commit','streaming','neurosim_native','DFF::Initialize; DFF::CalculateLatency',1,'cycles','vector',{'digital_tick':'binding','clock_id':'lv_core','numRead':1,'numDff':c['logical']['N']*c['logical']['output_bits']},['output_register_bits'],[ref('shared','/resource_policy/output_commit_ticks')],depends=[streaming[-1]['id']])
    for s in streaming:
        if not s['depends_on']:s['depends_on']=['input_capture']
    c['services'].insert(0,capture);c['services'].append(commit)
    scheduling(c,index)
    mux_channels=[128,None,4096,13824,128,4096,128,4096,128,4096]
    mux_fanin=[8,None,32,None,4,16,8,32,4,8]
    c['resources']['installed'].setdefault('mux_channels',mux_channels[index])
    c['resources']['installed'].setdefault('mux_fanin',mux_fanin[index])
    c['resources']['mux_scope']={'status':'selection_inventory_not_transistor_load_characterization','source_refs':[ref('results','/native_configuration')],'rule':'Ratios express selected outputs/local addresses; native row/layer/CIMSEL decoding is separate. No switch capacitance or RC assumed from fanin alone.'}
    if index==4:
        attempts=next(s for s in c['services'] if s['id']=='program_attempts')
        attempts['call']['inputs']['duration_parameters']=['local_setup','local_return']
        attempts['call']['inputs']['pulse_parameter_by_enclosing_axis']={'RESET_attempt':'reset_pulse','masked_SET_attempt':'set_pulse'}
        attempts['processing_range']={'scope':'one attempt within one16B transaction','pulse_select':'use the enclosing RESET_attempt or masked_SET_attempt loop; never apply both pulses in one attempt','verify_before_next_attempt':True,'rail_held_across_all_transactions':True}
    for s in c['services']:
        call=s['call'];ins=call['inputs']
        if 'data_beats' in ins:
            ins['front_cycles_formula']='control_cycles + data_beats - (1 if first_data_in_command else 0)'
            ins['front_reference_cycles']=ins.get('control_cycles',2)+ins['data_beats']-(1 if ins.get('first_data_in_command',False) else 0)
        if s['provider']=='v3_native_service' and ('digital_tick' in ins or 'adc_batch' in ins):
            s['provider']='neurosim_composed'
            call.setdefault('native_components',[{'provider':'v3_native_service','parameters':ins.get('duration_parameters',[ins.get('duration_parameter')]),'included_native_stages':s['included_stages']},{'provider':'neurosim_composed','bindings':[name for name in ('digital_tick','adc_batch') if name in ins],'status':'explicit external bound capability; native included stages are not repeated'}])
        if s['id']=='page_load' and 'encoded_bits' not in ins:ins['encoded_bits']=13824
    for s in c['services']:
        call=s['call'];call['count_owner']='stage.count is outer scheduling; per-primitive numRead=1; no implicit loop multiplication'
        if s['provider'].startswith('neurosim'):
            call['entrypoint']=call['entrypoint'].replace('Buffer::CalculateLatency; ','').replace('ShiftAdd::CalculateLatency','Adder::CalculateLatency').replace('AdderTree/ShiftAdd/DFF candidate signed-to-magnitude datapath','Adder::CalculateLatency; DFF::CalculateLatency; signed-magnitude control adapter').replace('DFF/Buffer plus signed-magnitude formatter; circuit realization unresolved','Adder::CalculateLatency; DFF::CalculateLatency; signed-magnitude page formatter adapter')
            call['inputs'].update({'primitive_numRead':1,'input_bit_loop_owner':'outer scheduler','weight_plane_loop_owner':'outer scheduler','output_load_F':None,'load_status':'requires_native_geometry_adapter','ShiftAdd_used':False})
            if s['id'] in ('reconstruct','digital_reconstruct','affine_merge_sign','digital_mac'):
                call['inputs']['existing_output_register_inventory_bits']=c['resources']['installed']['output_register_bits']
                call['inputs']['active_register_bits']=16*c['logical']['output_bits']
                call['inputs']['numDff']=16*c['logical']['output_bits']
                call['inputs']['register_allocation']='Reuse declared output/partial-sum containers; no new hidden hold bank or ShiftAdd register.'
                call['reference_schedule_count_only']=True
                call['component_occurrences_per_reference_cycle']=None
                call['microarchitecture_status']='Resolve which primitive operates on each reference schedule phase; do not multiply every listed component by total reference cycles.'
            if 'numDff' not in call['inputs'] and s['service_kind']=='resident':
                bits=call['inputs'].get('encoded_bits') or call['inputs'].get('staging_bits')
                if bits:call['inputs']['numDff']=bits;call['inputs']['register_allocation']='Reuse declared transaction/page/staging inventory for this local load unit; inspect resources.native_declared.'
            call['components']=[];call['outputs']=[]
            if 'AdderTree::' in call['entrypoint']:
                fanin=32 if s['id']=='digital_mac' else 4 if index==3 else 8
                call['components'].append({'module':'AdderTree','method':'CalculateLatency','numRead':1,'numUnitAdd':fanin,'input_word_bits':8 if s['id']=='digital_mac' else None,'input_word_bits_status':'INT8 leaves with explicit sign extension required' if s['id']=='digital_mac' else 'requires bit-shifted partial-sum leaf definition; do not reuse final output width as raw leaf width','numAdderTree':16,'capLoad_F':None,'clock_id':'lv_core'})
                call['outputs'].append({'field':'AdderTree.readLatency','unit':'cycles','clock_id':'lv_core','mode':'synchronous','conversion':'ceil(physical_delay_s * selected_clock_Hz), per primitive numRead=1','critical_path_measurement':'paired asynchronous CalculateLatency gives seconds; native load still required'})
            if 'Adder::' in call['entrypoint']:
                call['components'].append({'module':'Adder','method':'CalculateLatency','numRead':1,'numAdderBit':c['logical']['output_bits'],'numAdder':16,'capLoad_F':None})
                call['outputs'].append({'field':'Adder.readLatency','unit':'s','convert_to_ns_once':True})
            if 'DFF::' in call['entrypoint']:
                call['components'].append({'module':'DFF','method':'CalculateLatency','numRead':1,'numDff':call['inputs'].get('numDff'),'numDff_status':'specified' if 'numDff' in call['inputs'] else 'requires_stage_register_inventory','clock_id':'lv_core'})
                call['outputs'].append({'field':'DFF.readLatency','unit':'cycles','clock_id':'lv_core','mode':'synchronous','conversion':'numRead=1; actual period supplied by shared clock, not DFF timing closure'})
            if call['entrypoint'].startswith('SarADC'):
                call['outputs']=[{'field':'SarADC.readLatency','unit':'s','status':'native_primitive_total','convert_to_ns_once':True}]
            if not call['outputs']:
                call['outputs']=[{'field':'composed_duration','unit':'ns','status':'pending constituent instantiation; see native_components; convert seconds or cycles once before summation'}]
            call['aggregation_status']='Candidate primitives specify interface and ownership only. Existing v3 cycle count is reference schedule, not an executed NeuroSim replacement; combine sequential component occupancies after load/clock/count mapping is resolved.'
        else:
            call['outputs']=[{'field':'native_mode_duration','unit':'s','status':'retained_input_not_new_performance'}]
    c['implementation_plan']['no_double_counting']='Native opaque stages exclude replacement charges for their included stages. For constituent-mode stages, charge only listed primitives; calculator function is provenance, not a command to add its total again.'
    for s in c['services']:
        call=s['call'];ins=call['inputs']
        if not s['provider'].startswith('neurosim'):continue
        if 'native_components' in call:
            call['timing_role']='composed native occupation plus explicitly counted digital schedule/ADC binding; no opaque native stage splitting'
            continue
        if call['entrypoint'].startswith('SarADC'):
            call['timing_role']='one physical conversion; stage.count owns repetition';continue
        if s['id']=='page_load' and index==3:
            cycles={'by_schedule_page_kind':{'data':290,'reference':110},'formula':'2 control cycles + ceil(13824/effective_port_bits)'}
        elif 'front_reference_cycles' in ins:cycles={'value':ins['front_reference_cycles'],'source':'call.inputs.front_reference_cycles'}
        else:cycles={'value':1,'source':'one existing scheduled register-to-register tick per stage.count occurrence'}
        call['timing_role']='DFF_one_cycle_is_sole_digital_timer; combination_logic_only_checks_critical_path'
        call['timing_plan']={'clock_id':'lv_core','cycles_per_occurrence':cycles,'formula':'stage.count * cycles_per_occurrence * lv_core.actual_period_ns; apply schedule-dependent cycle factor before summing different page kinds','DFF_numRead':1,'DFF_role':'sole cycle timer; existing end-of-cycle register capture is within this tick','Adder_role':'critical_path_qualification_only','AdderTree_role':'physical asynchronous critical_path_qualification_only; synchronous ceil-cycles are NOT added','forbid_additive_combination_cycles':True,'actual_clock_rule':'max(5ns,all used register-to-register combinational/sense requirements); native case loads still require closure'}
        for comp in call.get('components',[]):
            comp['timing_role']='sole_cycle_timer' if comp['module']=='DFF' else 'critical_path_qualification_only'
            if comp['module']=='AdderTree':comp['qualification_mode']='asynchronous physical seconds; synchronous ceil-cycle return is not a second timer'
        for o in call.get('outputs',[]):
            o['timing_role']='sole_cycle_timer' if o['field'].startswith('DFF') else 'critical_path_qualification_only'
            if o['field'].startswith('AdderTree'):o.update(unit='s',mode='asynchronous_critical_path_qualification',conversion='physical seconds *1e9 once; not additional schedule cycles')
        call['timing_plan']['combinational_path_rule']='Sum serial logic delays on each register-to-register path (including reduction,sign/shift,accumulation); then take max across paths and target. Do not take max of individual serial gates.'
        call.pop('component_occurrences_per_reference_cycle',None)
        call['microarchitecture_status']='Fixed existing v3 digital tick schedule retained; combinational phase must fit the shared actual clock and does not add another cycle.'
        call['count_owner']='stage.count owns schedule occurrences; only DFF one-cycle timing, multiplied by explicit per-occurrence cycle factor; no additional Adder/AdderTree ceil-cycle summation'
        if s['id']=='input_magnitude_sign':
            ins.update(numDff=144,active_register_bits=144,register_allocation='16 lanes x9bits reused from36864bit input plus4608bit sign inventory')
            for comp in call.get('components',[]):
                if comp['module']=='DFF':comp.update(numDff=144,numDff_status='specified')
                if comp['module']=='Adder':comp['numAdderBit']=9
        if s['id']=='digital_mac':
            ins['arithmetic_widths']={'input_gate_bits':1,'signed_weight_leaf_bits':8,'term_count':32,'tree_result_bits':13,'accumulator_bits':c['logical']['output_bits'],'sign_extension':'explicit before/through reduction; input MSB coefficient negative','fixed_shifts':'wiring; input-bit shift/sign then existing output accumulator update'}
            call['timing_plan']['serial_paths']=[['input gating/sign extension','32-input tree','input-bit signed shift','output accumulator adder','existing output DFF setup']]
        if index in (0,4) and s['id'] in ('reconstruct','digital_reconstruct'):
            ins['arithmetic_widths']={'adc_nominal_bits':10,'weight_bits':8,'weighted_signed_leaf_bits':18,'leaf_width_formula':'adc_nominal_bits+(weight_bits-1)+1','fanin':8,'parallel_trees':16,'tree_result_bits':21,'accumulator_bits':23}
            ins['SAR_code_lifetime']='All128 converter codes remain in existing10bit SAR result state through both digital ticks; do not start another conversion; no added analog/digital hold bank.'
            ins['phase_plan']=[{'phase':1,'operation':'weighted signed plane reduction qualification','new_intermediate_register':False,'capture_policy':'keep source SAR codes unchanged; do not assume a free tree-result bank'},{'phase':2,'operation':'recompute weighted plane sum if needed, signed input-bit shift and accumulate into existing23bit output container','register':'existing output group','new_intermediate_register':False}]
            call['timing_plan']['serial_paths']=[['weighted8-plane tree','signed input-bit shift/sign','23bit accumulator adder','existing output DFF setup']]
            for comp in call.get('components',[]):
                if comp['module']=='AdderTree':comp.update(numUnitAdd=8,input_word_bits=18,input_word_bits_status='explicit conservative shifted signed code container',numAdderTree=16)
                if comp['module']=='Adder':comp['numAdderBit']=23
            c['resources']['installed']['existing_SAR_code_bits']=1280
            c['resources']['installed']['new_intermediate_hold_bits']=0
    electrical_modes(c,x,index)
    for service in c['services']:
        for output in service['call']['outputs']:
            if isinstance(output,dict) and output.get('unit') in ('s','ns'):
                if output.get('clock_id') is not None:
                    output['qualification_clock_id']=output['clock_id']
                output['clock_id']=None
    return c

def generate(repo,out,only=None):
    out.mkdir(parents=True,exist_ok=True)
    revision=Path(__file__).resolve().parents[1]/'interface_revision'
    clock_revision=runpy.run_path(str(revision/'clock_dependency.py'))['revise_case']
    digital_revision=runpy.run_path(str(revision/'digital_resources.py'))['revise_case']
    for i,cid in enumerate(CASES):
        if only and cid not in only:continue
        c,x,r=base(repo,cid,i);specify(c,x,r,i);add_bindings(c)
        c['contract_version']='3.0.0'
        clock_revision(c)
        digital_revision(c)
        for service in c['services']:
            service['service_timing']['blocks_resources']=list(service['resources'])
        used={}
        def walk(o):
            if isinstance(o,dict):
                if 'source_id' in o and 'function' in o:used.setdefault(o['source_id'],set()).add(o['function'])
                for v in o.values():walk(v)
            elif isinstance(o,list):
                for v in o:walk(v)
        walk(c)
        for sid,s in c['provenance']['sources'].items():
            if 'functions' in s:s['functions']={name:loc for name,loc in s['functions'].items() if name in used.get(sid,set())}
        dump(out/(cid+'.json'),c)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--only',nargs='*');a=p.parse_args();generate(a.repo.resolve(),a.out.resolve(),a.only)
