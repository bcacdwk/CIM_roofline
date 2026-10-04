#!/usr/bin/env python3
"""Step 2 revision: honest digital coverage and typed physical write resources.

The generator calls revise_case AFTER its original schedule/bindings. No native
time, clock ownership, schedule count, or v3 input is modified here.
"""
import copy
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
V14 = '8a88abf85844c0e1ba17cc771ea535fff6040456'


def quantity(value, unit, meaning, source_pointer=None, status=None):
    return {'value': value, 'unit': unit, 'meaning': meaning,
            'status': status or ('specified' if value is not None else 'not_reported'),
            'source_refs': ([{'source_id': 'results', 'json_pointer': source_pointer}]
                            if source_pointer else [])}


def _write_semantics(c):
    i=int(c['case_id'][:2])-1
    # Drivers/outputs and storage targets are independently specified, never inferred.
    electrical=[128,128,None,None,128,128,32,128,256,288][i]
    heads=[128,128,None,None,128,128,32,128,128,None][i]
    targets=[128,128,2048,13824,128,64,32,128,128,128][i]
    target_unit='complementary_pair' if i in (5,8) else 'storage_cell'
    target_scope='native_page' if i in (2,3) else 'selected_batch'
    encoded_factor=2 if i in (5,8) else 1
    native=c['resources']['native_declared']
    ptr='/native_configuration/resources/'
    electrical_key=['write_drivers','write_drivers',None,None,'write_driver_count',
                    'write_driver_lanes','IDAC_count','external_target_BL_drivers',
                    'write_branches','driven_bias_nodes'][i]
    target_key=['write_drivers','write_drivers','page_buffer_bits','physical_page_program_targets',
                'write_driver_count',None,'IDAC_count','external_target_BL_drivers',
                'write_pair_drivers','parallel_write_cells'][i]
    head_unit='pair_programmer' if i==8 else 'program_channel'
    payload=c['logical']['resident_transaction_Byte']
    sem={
      'electrical_drive_outputs':quantity(electrical,'electrical_output',
          'Biased/current-driven electrical outputs; not a programming target count.',ptr+electrical_key if electrical_key else None),
      'program_driver_channels':quantity(heads,head_unit,
          'Explicit independent drive channels when reported; page-engine or distributed bias outputs do not establish this count.',
          ptr+electrical_key if electrical_key and i not in (8,9) else ptr+'write_pair_drivers' if i==8 else None),
      'selected_storage_targets':quantity(targets,target_unit,
          'Addressed storage targets per '+target_scope+'; phase and plane organization remain explicit.',ptr+target_key if target_key else None),
      'target_scope':target_scope,
      'logical_bits_per_target':quantity(1,'logical_bit/'+target_unit,'One binary state/pair before INT8 plane and NAND encoding expansion.'),
      'physical_cells_per_target':quantity(encoded_factor,'storage_cell/'+target_unit,'Complementary storage branches per addressed target.'),
      'logical_payload_per_transaction':quantity(payload,'Byte','Workload payload for an indivisible resident transaction; not bias outputs or port beats.'),
      'encoded_bits_per_load_unit':quantity(c['resources']['active']['resident']['encoded_bits_per_load_unit'],'encoded_bit','Encoded bits in one native page for NOR/NAND; otherwise one resident transaction.'),
      'load_unit_scope':'native_page' if i in (2,3) else 'resident_transaction',
      'data_port_width':quantity(128,'bit/beat','External encoded port width; not physical program parallelism.'),
      'update_domains':quantity(1,'update_domain','One native independently scheduled update domain.'),
      'full_matrix_transactions':quantity(c['logical']['B_R_Byte']//payload,'transaction','B_R_Byte / logical_payload_per_transaction, exact integer division.'),
      'program_parallelism_source':'selected_storage_targets plus explicitly reported channels, phases and planes; never electrical_drive_outputs or data_port_width',
      'transaction_count_rule':'B_R_Byte / logical_payload_per_transaction; reject nonintegral division',
      'program_batches_per_transaction':None,
      'program_batch_count_rule':'program_batches_per_load_unit * load_units_per_transaction; batch is a native selection/program-service target group, not an internal pulse/head count; phase/retry services remain separately scheduled.',
      'phase_semantics':'Preserve service-specific pulses/retries; a target is not a pulse count.'}
    if i==2:
        sem['logical_bits_per_target']['meaning']='One binary NOR cell; one 2048-bit native page carries 256 workload Byte.'
        sem['page_payload']=quantity(256,'Byte/page','Native NOR page, 64 pages in complete resident rewrite.')
        sem['page_count']=quantity(64,'page','16384 Byte / 256 Byte per native page.')
    if i==3:
        sem['logical_bits_per_target']['value']=None
        sem['logical_bits_per_target']['status']='encoded_layout_not_one_to_one'
        sem['logical_bits_per_target']['meaning']='NAND base-4/SLC split-sign, digit duplication, input copies and reference pages forbid one-cell-to-one-payload conversion.'
        sem['page_count']=quantity(6144,'page','5760 data + 384 reference pages; each page selects 13824 storage cells.')
        sem['data_page_port']=quantity(48,'encoded_bit/beat','Actual useful data page formatter rate, distinct from nominal 128-bit port.')
        sem['reference_page_port']=quantity(128,'encoded_bit/beat','Reference page formatter rate.')
        sem['phase_semantics']='Native page program engine owns internal concurrency; selected page targets are not simultaneous internal program heads.'
    if i==5:
        sem['selected_storage_targets']['source_refs']=[{'source_id':'inputs','json_pointer':'/mapping/selected_pairs_per_write_group'}]
        sem['phase_targets']=[quantity(128,'MTJ','Phase 1 addresses both MTJs of each of 64 pairs.'),quantity(64,'MTJ','Phase 2 selects one MTJ of each pair.')]
        sem['phase_semantics']='64 pairs = 64 logical weight bits = 128 installed MTJ states = 8 workload Byte; phases address 128 then 64 MTJs.'
    if i==8:
        sem['phase_targets']=[quantity(128,'complementary_pair','One current-program group.'),quantity(256,'storage_branch','Two current-feedback branches per pair, 128 logical bits.')]
        sem['phase_semantics']='128 pair programmers service 256 electrical branches = 128 binary bits = 16 Byte; 256 encoded bits take two 128-bit beats.'
    if i==9:
        sem['phase_semantics']='288 bias outputs supply strip/layer inhibit/selection for 128 selected cells across 8 strips; two opposite-polarity phases do not create 288 independent targets.'
        sem['bias_node_count']=quantity(288,'bias_node','Electrical selection/bias network including unselected/inhibited nodes.',ptr+'driven_bias_nodes')
        sem['selected_strips']=quantity(8,'strip','Physical selected strips.',ptr+'parallel_write_strips')
    if i==7:
        sem['internal_restore_targets']=quantity(4096,'storage_cell','Internal read/restore cells; contributes zero external workload Byte.',ptr+'internal_restore_BL_drivers')
    if i==2:
        sem['load_units_per_transaction']=payload*8//targets
        sem['program_batches_per_load_unit']=1
    elif i==3:
        sem['load_units_per_transaction']=(c['physical']['data_storage_sites']+c['physical']['reference_storage_sites'])//targets
        sem['program_batches_per_load_unit']=1
    else:
        sem['load_units_per_transaction']=1
        sem['program_batches_per_load_unit']=sem['encoded_bits_per_load_unit']['value']//(targets*encoded_factor)
    sem['program_batches_per_transaction']=sem['load_units_per_transaction']*sem['program_batches_per_load_unit']
    return sem


def _operation_plan(c,s):
    sid=s['id'];i=int(c['case_id'][:2])-1
    p={'operations':[], 'scheduled_cycles':{'source':'existing v3 count and nested schedule; this plan adds no cycle or register'},
       'register_boundaries':[], 'reusable_modules':[], 'uncovered_logic':[],
       'timing_evidence':'v3 scheduled budget retained until actual case register paths and loads are instantiated',
       'instantiation_required':[], 'case_timing_validated':False}
    if sid in ('input_capture','output_commit','operand_capture','attempt_done','polarity_turn'):
        p.update(operations=['existing register capture/control state update'],register_boundaries=['declared input/output/operand/mask/target register, selected by call.inputs'],reusable_modules=['DFF'],instantiation_required=['actual destination fanout and setup/clock-domain boundary; DFF cycle count alone is not closure'])
    elif sid=='digital_mac':
        p.update(operations=['1-bit input gate over signed INT8 weight leaves','32-input signed reduction','input-bit constant shift and MSB sign handling','accumulate into existing output container'],
          register_boundaries=['4096-bit held operand tile and input register -> reduction/shift/sign/accumulate -> existing output/partial-sum register'],
          reusable_modules=['AdderTree for a compatible tree-only carry approximation','Adder for output accumulator','DFF for existing capture'],
          uncovered_logic=['gating and sign-extension fanout/load','fixed-shift wiring load and negative-MSB control','full serial tree-to-accumulator path including setup'],
          instantiation_required=['retain one native scheduled tick per input slice; instantiate this complete serial path before setting actual digital clock; no new interstage register'])
        p['scheduled_cycles'].update(per_tile=8,per_input_slice=1)
    elif sid=='native_mac':
        p.update(operations=['D6CIM input gating','native 16-term HCA/BFA reduction','signed shift/control','local output accumulation'],register_boundaries=['native D6CIM complete-MAC cycle boundary; internal partition not replaced'],uncovered_logic=['generic DCIM 256x256 tree is not a replacement for D6CIM HCA/BFA'],timing_evidence='retained complete v3 native MAC cycle including all listed operations',instantiation_required=['only an explicitly separate future architecture study may replace the native MAC cycle'])
    elif sid in ('reconstruct','digital_reconstruct'):
        p.update(operations=['signed, weighted eight-plane SAR code reconstruction','input-bit signed shift','output accumulator update'],reusable_modules=['AdderTree for compatible weighted reduction','Adder for existing output accumulation','DFF for existing output capture'],uncovered_logic=['actual code source drive and fanout','sign/shift/wiring load','serial reduction-to-accumulator timing and setup'],instantiation_required=['instantiate phase-two full serial path; prove source code lifetime for both ticks using declared state only'])
        p['scheduled_cycles'].update(per_conversion_batch=2,phase_1='source codes retained; no free tree-result register',phase_2='recompute reduction if needed; signed shift and accumulate')
        p['register_boundaries']=['existing SAR result state -> weighted tree/sign/accumulator -> existing output register; no new intermediate bank']
        if i not in (0,4):
            p['register_boundaries']=['existing declared SAR/code state -> reconstruction/accumulator -> existing output containers; retention topology requires instantiation']
            p['uncovered_logic'].append('PCM/GC native code lifetime and release/refresh arbitration are pending; no extra hold resource allocated')
    elif sid=='affine_merge_sign':
        p.update(operations=['10-bit SAR code times unsigned Q8.16 gain plus signed Q12.12 offset; rounding to count','four base-4 weighted count merge','positive-minus-negative weight polarity subtraction','signed input-phase shift and output accumulation'],
          register_boundaries=['tick1: SAR/coefficient state -> 64x14-bit affine-count register','tick2: affine-count register -> 16x20-bit magnitude-sum register','tick3: magnitude registers -> 8x21-bit polarity-difference register','tick4: polarity-difference plus existing accumulator -> 240x29-bit output/accumulator inventory'],
          reusable_modules=['AdderTree: merge-only candidate subject to shifted leaf definition','Adder: offset/subtraction/accumulation constituent','DFF: already declared stage registers'],
          uncovered_logic=['fixed-point affine multiplier with round/saturation path','loaded base-4 merge with shifted operands','subtraction/sign control and accumulator serial paths'],
          instantiation_required=['retain four v3 digital tick budgets; do not claim multiplier delay from AdderTree','map each actual register path with existing stage inventory before any replacement'])
        p['scheduled_cycles'].update(per_conversion_round=4)
    elif sid=='load_calibration':
        p.update(operations=['capture zero/full/half-reference ADC samples','gain/offset subtraction and 24-step division per channel batch','fixed-point coefficient round/store','half-input residual arithmetic/threshold check and final publish'],
          register_boundaries=['existing ADC code state and calibration arithmetic working state -> 12288-bit gain/offset registers; working register allocation still pending','16 arithmetic channels, 16 batches; 24 division + 4 other ticks/batch plus 2 boundary ticks'],
          reusable_modules=['SarADC for shared conversions','Adder for subtract/add constituents','DFF for declared coefficient storage'],uncovered_logic=['divider recurrence, working register inventory, rounding and residual compare path'],instantiation_required=['retain 450 v3 arithmetic ticks and native analog/ADC constituents; do not interpret an Adder/DFF list as a complete divider'],timing_evidence='v3 complete calibration arithmetic schedule budget plus separately identified shared front/ADC service')
        p['scheduled_cycles'].update(arithmetic_ticks=450,formula='16*(24+4)+2')
    elif sid in ('input_magnitude_sign','resident_encode'):
        p.update(operations=['two-complement signed INT8 -> 8-bit magnitude plus sign, including -128','lane selection and page/input formatter routing'],register_boundaries=['existing input/sign register inventory' if sid=='input_magnitude_sign' else 'declared 4608x9-bit one-row staging and native page buffer'],reusable_modules=['Adder for conditional negate only','DFF for declared storage'],uncovered_logic=['conditional complement/select','formatter fanout and actual combinational path'],instantiation_required=['preserve 16 lanes and scheduled 288 ticks per input vector/output row; qualify negate/formatter using actual load'])
    elif sid=='endpoint_verify' and i==6:
        p.update(operations=['native voltage frontend and shared SAR conversion','digital endpoint-code threshold comparison','existing mask/done capture'],register_boundaries=['SAR result -> threshold compare -> existing mask/done state'],reusable_modules=['SarADC for conversion','DFF for existing capture','Adder-based difference only if exact compare circuit is explicitly instantiated'],uncovered_logic=['digital threshold comparator/sign/exceptions path and actual loads'],instantiation_required=['retain one v3 comparison tick for each of two fresh passes; do not model analog window sense with digital Comparator'],timing_evidence='native mode front + shared ADC candidate + retained v3 digital comparison budget')
    elif sid=='refresh_decode_load_rewrite':
        p.update(operations=['decode signed fresh differential ADC code into binary endpoint','use existing 128-bit refresh code hold','format complementary 256 encoded bits and load two port beats','native current-feedback rewrite'],register_boundaries=['fresh ADC -> 128 refresh sign decoders/code hold -> existing pair-program interface; no full-matrix shadow'],reusable_modules=['DFF for existing sign-code/port capture'],uncovered_logic=['sign-decision threshold and gating path','complement formatter and target control load'],instantiation_required=['preserve one decode tick and existing load/control count; actual refresh arbitration and release timing remain pending'],timing_evidence='v3 decode/load budget and complete native rewrite; read/ADC remains shared by explicit dependency')
    elif sid=='terminal_verify':
        p.update(operations=['retained native state sense','capture absolute physical state','compare expected encoded state and reduce pass/fail'],register_boundaries=['native sense result -> existing verify state latch/operand hold -> completion state'],reusable_modules=['DFF for existing capture','Adder/logic only after exact comparator/reduction topology selection'],uncovered_logic=['digital compare and pass/fail reduction, fanout and setup'],instantiation_required=['preserve existing branch/capture/compare counts; instantiate exact absolute-state comparator path before replacing budget'])
    elif 'digital_tick' in s['call']['inputs'] or s['call'].get('components'):
        p.update(operations=['explicit declared encoded load/control/selection steps; native analog portions stay complete'],register_boundaries=['declared transaction/page/mask/code registers only; see resources and call.inputs'],reusable_modules=['DFF for capture only'],uncovered_logic=['control decode, selection/enable and wiring load'],instantiation_required=['bind each counted digital control step to its existing source/destination register; retain v3 control tick budget meanwhile'])
    else:
        p.update(operations=['complete native physical service or independent analog primitive'],register_boundaries=['service launch/completion boundary; no internal digital register invented'],timing_evidence='retained native physical budget or separately probed primitive; no digital path closure claimed')
    return p


def revise_case(c):
    sem=_write_semantics(c);c['resources']['write_semantics']=sem
    c['resources']['installed'].pop('real_write_driver_count',None)
    c['resources']['active']['resident'].pop('physical_write_driver_count',None)
    for s in c['services']:
        s['resources']=['write_semantics.program_driver_channels' if x in ('real_write_driver_count','physical_write_driver_count') else x for x in s['resources']]
        p=_operation_plan(c,s);s['call']['operation_plan']=p
        s['call']['case_timing_validation']='pending' if p['instantiation_required'] else 'native_budget_retained'
        components=s['call'].get('components',[])
        for component in components:
            component['coverage_limit']='callable constituent; actual case load and full register path not validated'
            if component['module']=='AdderTree':
                component['latency_model_scope']='V1.4 tree-specific first-width then 2-bit carry-arrival approximation; not a model for multiplier/divider or arbitrary serial arithmetic'
        native=(s['provider']=='v3_native_service')
        hybrid=bool(s['call'].get('native_components')) or (bool(p['uncovered_logic']) and bool(p['reusable_modules']))
        s['coverage']={
          'kind':'native_service' if native else 'hybrid_stage' if hybrid else 'native_module',
          'routing_status':'route_defined',
          'native_module_probe_status':'native_module_probe_run' if s['provider'].startswith('neurosim') and any(m in json.dumps(s['call']) for m in ('AdderTree','SarADC','DFF')) else 'not_applicable',
          'case_path_status':'case_path_pending' if p['instantiation_required'] and not native else 'native_budget_retained',
          'dominant_timing_provider':('v3_native_complete_service' if native else 'v3_native_services_plus_pending_primitive_or_control_replacement' if s['call'].get('native_components') else 'neurosim_SAR_primitive_pending_case_instantiation' if s['id']=='sar' else 'v3_scheduled_digital_budget_until_case_path_instantiation'),
          'whole_arithmetic_path_validated':False,
          'note':'A module mechanism probe does not validate this case path. No unimplemented combinational operation has zero time.'}
        if s['id'] in ('affine_merge_sign','load_calibration'):
            s['coverage']['kind']='hybrid_stage'
            s['coverage']['case_path_status']='native_budget_retained'
            s['coverage']['dominant_timing_provider']='v3_arithmetic_schedule_budget; shared front/ADC separately identified'
            s['call']['entrypoint']=('v3 four-tick affine/merge/subtract/accumulate schedule; AdderTree/Adder/DFF are constituent candidates only' if s['id']=='affine_merge_sign' else 'v3 calibration arithmetic schedule plus native frontend and shared SarADC candidate')
        if p['instantiation_required'] and not native:
            s['call']['microarchitecture_status']='route_defined; retain native budget until all listed register paths and case loads are instantiated; mechanism probes do not qualify full arithmetic'
    c['implementation_plan']['digital_path_policy']='Four distinct states: route_defined; native_module_probe_run (mechanism only); case_path_pending (no case closure); native_budget_retained. No path is qualified by an AdderTree/Adder/DFF component list.'
    return c


def validate_resource_case(c):
    """Typed quantities used in capacity/concurrency/count math, not pointer-only checks."""
    i=int(c['case_id'][:2])-1; r=c['resources'];w=r['write_semantics'];l=c['logical']
    expected_targets=[128,128,2048,13824,128,64,32,128,128,128][i]
    expected_unit='complementary_pair' if i in (5,8) else 'storage_cell'
    expected_units={
      'electrical_drive_outputs':'electrical_output',
      'program_driver_channels':'pair_programmer' if i==8 else 'program_channel',
      'selected_storage_targets':expected_unit,
      'logical_bits_per_target':'logical_bit/'+expected_unit,
      'physical_cells_per_target':'storage_cell/'+expected_unit,
      'logical_payload_per_transaction':'Byte',
      'encoded_bits_per_load_unit':'encoded_bit',
      'data_port_width':'bit/beat','update_domains':'update_domain',
      'full_matrix_transactions':'transaction'}
    if i==2:expected_units.update(page_payload='Byte/page',page_count='page')
    if i==3:expected_units.update(page_count='page',data_page_port='encoded_bit/beat',reference_page_port='encoded_bit/beat')
    if i==7:expected_units['internal_restore_targets']='storage_cell'
    if i==9:expected_units.update(bias_node_count='bias_node',selected_strips='strip')
    for name,unit in expected_units.items():
        item=w[name];assert item['unit']==unit,name+' unit mismatch'
        allow_null=(name=='electrical_drive_outputs' and i in (2,3)) or (name=='program_driver_channels' and i in (2,3,9)) or (name=='logical_bits_per_target' and i==3)
        if allow_null:assert item['value'] is None,name+' must retain unknown/encoded-layout status'
        else:assert type(item['value']) is int and item['value']>0,name+' must be a positive integer count'
    for key in ('K','N','B_R_Byte','bytes_per_weight','resident_transaction_Byte'):
        assert type(l[key]) is int and l[key]>0,'logical '+key+' must be positive integer'
    for key in ('effective_capacity_Byte','data_storage_sites','cells_per_INT8_weight'):
        assert type(c['physical'][key]) is int and c['physical'][key]>0,'physical '+key+' must be positive integer'
    q=w['selected_storage_targets']
    assert q['value']==expected_targets and q['unit']==expected_unit,'selected target count/unit mismatch; electrical outputs and ports cannot substitute'
    assert w['electrical_drive_outputs']['value']==[128,128,None,None,128,128,32,128,256,288][i]
    assert w['electrical_drive_outputs']['unit']=='electrical_output'
    assert w['program_driver_channels']['value']==[128,128,None,None,128,128,32,128,128,None][i]
    assert w['logical_bits_per_target']['value']==(None if i==3 else 1)
    assert w['physical_cells_per_target']['value']==(2 if i in (5,8) else 1)
    payload=w['logical_payload_per_transaction']['value']
    assert payload==l['resident_transaction_Byte']==[16,16,16384,1105920,16,8,32,16,16,16][i]
    assert l['B_R_Byte']%payload==0 and w['full_matrix_transactions']['value']==l['B_R_Byte']//payload
    assert w['full_matrix_transactions']['unit']=='transaction' and w['update_domains']['value']==1
    assert w['data_port_width']==dict(w['data_port_width'],value=128,unit='bit/beat')
    assert w['target_scope']==('native_page' if i in (2,3) else 'selected_batch')
    assert w['load_unit_scope']==('native_page' if i in (2,3) else 'resident_transaction')
    encoded=w['encoded_bits_per_load_unit']['value']
    assert encoded==r['active']['resident']['encoded_bits_per_load_unit']==[128,128,2048,13824,128,128,256,128,256,128][i]
    assert 'encoded_bits_per_transaction' not in w,'ambiguous page/transaction field retired'
    assert c['physical']['effective_capacity_Byte']==l['K']*l['N']*l['bytes_per_weight']
    assert c['physical']['data_storage_sites']==l['K']*l['N']*c['physical']['cells_per_INT8_weight']
    if i not in (2,3):
        planes=8 if i==6 else 1
        assert q['value']*planes==payload*8,'physical targets and serial planes do not cover transaction payload'
        physical_per_batch=q['value']*w['physical_cells_per_target']['value']
        assert encoded==payload*8*w['physical_cells_per_target']['value']
        assert encoded%physical_per_batch==0
        batches=encoded//physical_per_batch
        assert batches==planes,'target groups must match actual serial planes, not pulse count'
    if i==2:
        assert w['page_count']['value']*w['page_payload']['value']==l['B_R_Byte']
        assert w['page_payload']['value']==256 and w['page_count']['value']==64
        assert q['value']==encoded==w['page_payload']['value']*8
        assert payload*8%q['value']==0
        batches=payload*8//q['value']
    if i==3:
        assert w['page_count']['value']==5760+384 and q['value']==13824
        assert 5760*13824==c['physical']['data_storage_sites']
        assert 384*13824==c['physical']['reference_storage_sites']
        assert 13824//w['data_page_port']['value']==288 and 13824//w['reference_page_port']['value']==108
        assert w['data_page_port']['value']==48 and w['reference_page_port']['value']==128
        assert w['program_driver_channels']['value'] is None
        cells=c['physical']['data_storage_sites']+c['physical']['reference_storage_sites']
        assert type(c['physical']['reference_storage_sites']) is int and cells%q['value']==0
        batches=cells//q['value']
        assert batches==w['page_count']['value']
    assert type(w['program_batches_per_transaction']) is int and w['program_batches_per_transaction']==batches,'program batch count must follow selected target groups and encoding/planes/pages'
    load_units=batches if i in (2,3) else 1
    per_load_batch=1 if i in (2,3) else batches
    assert type(w['load_units_per_transaction']) is int and w['load_units_per_transaction']==load_units,'load units must include every native data/reference page or one local transaction'
    assert type(w['program_batches_per_load_unit']) is int and w['program_batches_per_load_unit']==per_load_batch,'load-unit batching must follow targets and encoded cells'
    assert w['program_batches_per_transaction']==w['load_units_per_transaction']*w['program_batches_per_load_unit']
    if i in (5,8):
        assert q['value']*2==encoded
        expected_phase_units=['MTJ','MTJ'] if i==5 else ['complementary_pair','storage_branch']
        assert len(w['phase_targets'])==2
        for phase,unit in zip(w['phase_targets'],expected_phase_units):
            assert phase['unit']==unit and type(phase['value']) is int and phase['value']>0,'phase target unit/integer mismatch'
    if i==5:
        assert [x['value'] for x in w['phase_targets']]==[q['value']*2,q['value']]
        assert max(x['value'] for x in w['phase_targets'])<=w['program_driver_channels']['value']
        assert c['physical']['data_storage_sites']==l['K']*l['N']*8*2
    if i==8:
        assert [x['value'] for x in w['phase_targets']]==[q['value'],q['value']*2]
        assert w['program_driver_channels']['value']==q['value']
    if i==7:assert w['internal_restore_targets']['value']==4096
    if i==9:assert w['bias_node_count']['value']==288 and w['selected_strips']['value']==8 and payload==16
    assert 'real_write_driver_count' not in r['installed'] and 'physical_write_driver_count' not in r['active']['resident']
    return True


def run_checks(cases, policy=None):
    if isinstance(cases,dict):cases=list(cases.values())
    checks=[]
    def ck(name,ok,detail=None):checks.append({'name':name,'status':'PASS' if ok else 'FAIL','detail':detail})
    for c in cases:
        try:validate_resource_case(c);ok=True;err=None
        except (AssertionError,KeyError,TypeError,ZeroDivisionError) as exc:ok=False;err=str(exc)
        ck(c['case_id']+' typed capacity/target/transaction invariants',ok,err)
        for s in c['services']:
            p=s['call'].get('operation_plan',{});cov=s.get('coverage',{})
            ck(c['case_id']+'/'+s['id']+' operation and evidence boundary',bool(p.get('operations')) and bool(p.get('register_boundaries')) and cov.get('whole_arithmetic_path_validated') is False)
            if p.get('uncovered_logic'):
                ck(c['case_id']+'/'+s['id']+' missing logic retained or pending',bool(p.get('timing_evidence')) and cov['case_path_status'] in ('case_path_pending','native_budget_retained'))
        # Adversarial substitutions must fail even if a source pointer is valid.
        for bad_kind in ('electrical_outputs','port_width','target_unit','payload_unit'):
            bad=copy.deepcopy(c);w=bad['resources']['write_semantics']
            if bad_kind=='electrical_outputs':
                value=w['electrical_drive_outputs']['value']
                if value==w['selected_storage_targets']['value'] or value is None:continue
                w['selected_storage_targets']['value']=value
            elif bad_kind=='port_width':
                value=w['data_port_width']['value']
                if value==w['selected_storage_targets']['value']:continue
                w['selected_storage_targets']['value']=value
            elif bad_kind=='target_unit':w['selected_storage_targets']['unit']='electrical_output'
            else:w['logical_payload_per_transaction']['unit']='bit'
            try:validate_resource_case(bad);rejected=False
            except (AssertionError,KeyError,TypeError,ZeroDivisionError):rejected=True
            ck(c['case_id']+' rejects '+bad_kind+' as capacity/concurrency quantity',rejected)
        # Every physical quantity participating in count arithmetic is unit-checked.
        # These include reviewer-found counterexamples where the numeric value was
        # correct but a programmer, complementary factor, or encoded bit was mislabeled.
        quantities=[name for name,q in c['resources']['write_semantics'].items()
                    if isinstance(q,dict) and 'unit' in q and 'value' in q]
        for name in quantities:
            bad=copy.deepcopy(c)
            bad['resources']['write_semantics'][name]['unit']='Byte' if name in ('physical_cells_per_target','encoded_bits_per_load_unit') else 'bit/beat' if name in ('program_driver_channels','update_domains') else 'invalid_count_unit'
            try:validate_resource_case(bad);rejected=False
            except (AssertionError,KeyError,TypeError,ZeroDivisionError):rejected=True
            ck(c['case_id']+' rejects '+name+' incorrect unit',rejected)
        for name in ('program_batches_per_transaction','program_batches_per_load_unit','load_units_per_transaction'):
            bad=copy.deepcopy(c);bad['resources']['write_semantics'][name]=13
            try:validate_resource_case(bad);rejected=False
            except (AssertionError,KeyError,TypeError,ZeroDivisionError):rejected=True
            ck(c['case_id']+' rejects inconsistent '+name,rejected)
        for name in ('selected_storage_targets','logical_payload_per_transaction','encoded_bits_per_load_unit','physical_cells_per_target','update_domains'):
            bad=copy.deepcopy(c);q=bad['resources']['write_semantics'][name];q['value']=float(q['value'])
            try:validate_resource_case(bad);rejected=False
            except (AssertionError,KeyError,TypeError,ZeroDivisionError):rejected=True
            ck(c['case_id']+' rejects noninteger '+name,rejected)
        if 'phase_targets' in c['resources']['write_semantics']:
            for index in range(2):
                bad=copy.deepcopy(c);bad['resources']['write_semantics']['phase_targets'][index]['unit']='bit/beat'
                try:validate_resource_case(bad);rejected=False
                except (AssertionError,KeyError,TypeError,ZeroDivisionError):rejected=True
                ck(c['case_id']+' rejects phase target '+str(index)+' port unit',rejected)
    byid={c['case_id']:c for c in cases}
    nand=byid.get('04_nand_3d')
    if nand:
        stages={s['id']:s for s in nand['services']}
        ck('NAND affine multiplier and divider not certified by 32-input tree',all(stages[x]['coverage']['case_path_status']=='native_budget_retained' and stages[x]['call']['operation_plan']['uncovered_logic'] for x in ('affine_merge_sign','load_calibration')))
        ck('NAND stage register inventories preserved',[nand['resources']['native_declared'][x] for x in ('affine_count_stage_register_bits','magnitude_sum_stage_register_bits','polarity_difference_stage_register_bits')]==[896,320,168])
    for cid in ('01_sram_acim','05_rram'):
        c=byid.get(cid)
        if c:
            stage=next(s for s in c['services'] if s['id'] in ('reconstruct','digital_reconstruct'))
            ck(cid+' two ticks no new intermediate register',stage['call']['operation_plan']['scheduled_cycles']['per_conversion_batch']==2 and c['resources']['installed']['new_intermediate_hold_bits']==0 and c['resources']['installed']['existing_SAR_code_bits']==1280)
    return {'status':'PASS' if all(x['status']=='PASS' for x in checks) else 'FAIL','checks':checks,
      'observations':['No whole-case digital critical path was newly certified. Native budgets remain for missing multiplier/divider/compare/control logic.','Typed resource tests use concrete target/phase/page/payload arithmetic and reject electrical-output or interface substitutions.']}


def run_native(root,out,cxx):
    root=Path(root).expanduser().resolve();out=Path(out).resolve();own=Path(__file__).resolve().parent
    if root not in out.parents or any(s in str(root).lower() for s in ('onedrive','icloud','mobile documents')):raise ValueError('native probe output must be under nonsynchronized local root')
    if out.exists() and any(out.iterdir()):raise ValueError('native probe output must be new')
    out.mkdir(parents=True,exist_ok=True);src=out/'src';src.mkdir();tmp=out/'tmp';tmp.mkdir()
    tree=Path(json.loads((root/'worktrees.json').read_text())['2DInferenceV1.4'])
    if subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()!=V14:raise ValueError('locked SHA mismatch')
    core=tree/'Inference_pytorch/NeuroSIM';hashes={}
    for f in sorted(core.iterdir()):
        if f.suffix in ('.cpp','.h'):
            shutil.copy2(f,src/f.name);hashes[f.name]=hashlib.sha256(f.read_bytes()).hexdigest()
    shutil.copy2(own/'addertree_probe.cpp',src/'revision_addertree_probe.cpp')
    shutil.copy2(__file__,out/'digital_resources.py');shutil.copy2(own/'addertree_probe.cpp',out/'addertree_probe.cpp')
    commands=[];env=dict(os.environ,TMPDIR=str(tmp))
    def run(argv,name):
        r=subprocess.run(argv,cwd=out,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/(name+'.log')).write_text(r.stdout);commands.append({'argv':list(map(str,argv)),'cwd':str(out),'returncode':r.returncode,'log':name+'.log'})
        (out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
        if r.returncode:raise RuntimeError(name+' failed; see '+str(out))
        return r.stdout
    exe=out/'addertree_probe';cpp=[str(p) for p in sorted(src.glob('*.cpp')) if p.name!='main.cpp']
    run([str(cxx),'-std=c++11','-O2','-fopenmp','-w','-I',str(src)]+cpp+['-o',str(exe)],'build')
    raw=run([str(exe)],'run');records=[];checks=[]
    for line in raw.splitlines():
        if line.count(',')!=8:continue
        v=list(map(float,line.split(',')));f,b,d,cap,tree_d,first,two,model,serial=v
        records.append(dict(zip(('fanin','input_bits','depth','capLoad_F','native_tree_s','first_adder_s','two_bit_adder_s','native_model_sum_s','arbitrary_serial_fullwidth_sum_s'),v)))
        checks.append({'name':f'AdderTree {int(f)}x{int(b)} matches first-width plus later 2-bit model','status':'PASS' if math.isclose(tree_d,first+(d-1)*two,rel_tol=1e-12) and math.isclose(tree_d,model,rel_tol=1e-12) and 0<tree_d<serial else 'FAIL'})
    checks.append({'name':'six finite positive load-sensitive native model records','status':'PASS' if len(records)==6 and all(math.isfinite(v) and v>0 for r in records for v in r.values()) else 'FAIL'})
    summary={'status':'PASS' if all(c['status']=='PASS' for c in checks) else 'FAIL','checks':checks,'records':records,'backend_sha':V14,'source_modified':False,'upstream_source_sha256':hashes,'probe_sha256':hashlib.sha256((own/'addertree_probe.cpp').read_bytes()).hexdigest(),
      'interpretation':'Confirms a specific tree carry-arrival approximation implemented by V1.4. Full-width serial sum is a different boundary/arrival assumption, not a correctness oracle. Neither result validates NAND affine multiply/divide or arbitrary logic chained after a tree.'}
    (out/'summary.json').write_text(json.dumps(summary,indent=2,allow_nan=False)+'\n')
    return summary
