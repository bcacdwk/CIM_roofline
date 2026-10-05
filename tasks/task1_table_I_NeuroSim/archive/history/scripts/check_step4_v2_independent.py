#!/usr/bin/env python3
"""Independent Step4 V2 arithmetic and semantic audit.

Expected service formulas do not import engine, adapters, replay, or original
calculators. The frozen engine is imported only as the subject of separate
edge/wrapper tests whose expected endpoints are computed here.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True

PILOTS = {'01_sram_acim','02_sram_dcim','05_rram'}
CHECKS = {}

def check(key, value):
    CHECKS[key] = bool(value)
    if not value:
        raise AssertionError(key)

def near(a,b):
    return math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-5)

def read(path):
    return json.loads(Path(path).read_text())

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def edge(t,p,setup=0.):
    q=(t+setup)/p
    if math.isclose(q,round(q),rel_tol=0.,abs_tol=1e-9): q=round(q)
    return math.ceil(q)*p

def pointer(obj, path):
    for key in path.split('/')[1:]:
        key=key.replace('~1','/').replace('~0','~')
        obj=obj[int(key)] if isinstance(obj,list) else obj[key]
    return obj

def expectations(cid,c,p,b):
    """Closed-form counts with actual consumer edge boundaries."""
    P=b['actual_period_ns']; M=b['boundary_setup_ns']; A=b.get('sar_ns')
    E=lambda t,setup=0.:edge(t,P,setup)
    H=G=0.; F=None
    if cid=='01_sram_acim':
        S=2*P+64*(E(p['charge_front']+A)+2*P)
        R=1024*E(p['sram_write_cycle'])
    elif cid=='02_sram_dcim':
        S=P+E(64*p['native_mac_cycle'])+P
        R=128*E(p['sram_write_cycle'])
    elif cid=='05_rram':
        S=2*P+128*(E(p['input_step']+p['cim_front']+A)+2*P)
        verify=p['input_step']+p['memory_verify_front']+p['binary_verify_sense_ns']
        reset=P+E(p['local_setup']+p['reset_pulse']+p['local_return']+verify)+P
        set_=P+E(p['local_setup']+p['set_pulse']+p['local_return']+verify)+P
        R=E(p['rail_setup'])+512*(2*P+2*reset+set_)+E(p['rail_exit'],M)
    elif cid=='03_nor_2d':
        S=2*P+32*(E(p['nor_read'],M)+8*P)
        R=4*(P+E(p['sector_erase'])+P+16*(18*P+E(p['page_program'],M)))
    elif cid=='06_mram':
        S=2*P+16*(E(p['ibmd_read'])+9*P)
        W=p['direction_write_slot']; B=p['ibmd_read']
        R=1024*(2*P+E(W)+P+E(W+B,M)+P+E(B,M)+P)
    elif cid=='07_pcm':
        V=p['shared_voltage_front']+A
        S=2*P+2048*(E(V)+2*P)
        write=3*p['drive_transition']+p['reset_pulse']+p['set_complete_pulse']
        R=1024*(3*P+8*(P+E(write+V)+P+E(V)+P))
    elif cid=='08_feram_hfo2':
        S=2*P+32*(E(p['feram_sense']+p['polarization_hold']+p['open_close'])+8*P)
        R=1024*(2*P+E(p['open_close']+2*p['polarization_hold'],M))
    elif cid=='09_gain_cell_edram':
        V=p['input_step']+p['common_read_overhead']+p['mac_integration']+A
        refresh=p['input_step']+p['common_read_overhead']+p['refresh_integration']+A
        atomS=E(V)+2*P
        atomR=3*P+E(p['program_complete'],M)
        S=2*P+32*atomS;R=256*atomR
        H=256*(E(refresh)+4*P+E(p['program_complete'],M))
        G=max(atomS,atomR); F=math.floor(p['refresh_period']/P)*P
    elif cid=='10_fenor_3d':
        S=2*P+32*(E(p['binary_read'],M)+8*P)
        native=3*p['bias_transition']+2*p['polarization_pulse']+max(p['post_pulse_guard'],p['bias_transition'])+p['binary_read']
        R=1024*(2*P+E(native,M)+8*P)
    elif cid=='04_nand_3d':
        X=p['bl_setup']+p['sl_setup']+A
        S=290*P+30*(E(p['wl_setup']+X)+4*P+31*(E(X)+4*P))
        pages=240*(288*P+24*(290*P+E(p['page_program'],M)))+384*(110*P+E(p['page_program'],M))
        calibration=2*E(p['wl_setup']+X,M)+10*E(X,M)+450*P
        R=E(64*p['block_erase'],M)+pages+calibration
    else:raise ValueError(cid)
    alpha=(F-H-G)/F if F is not None else 1.
    return dict(streaming_ns=S,resident_ns=R,maintenance_ns=H,guard_ns=G,frame_ns=F,availability=alpha)

def semantic_trace_check(cid,path,b):
    count=0; samples=[];P=b['actual_period_ns']
    def visit(nodes,multiplier=1):
        nonlocal count
        for i,node in enumerate(nodes):
            if 'repeat' in node:
                visit(node['examples'][0],multiplier*node['repeat'])
                continue
            if node.get('id')!='digital_reconstruct.phase1':continue
            prev,nxt=nodes[i-1],nodes[i+1]
            check(cid+'.held_pair_'+str(len(samples)),prev['id']=='sar' and nxt['id']=='digital_reconstruct.phase2')
            e0=node['service_start_ns'];e1=node['end_ns'];e2=nxt['end_ns']
            check(cid+'.edges_'+str(len(samples)),near(e1,e0+P) and near(e2,e0+2*P) and near(nxt['service_start_ns'],e1))
            check(cid+'.E0_alignment_'+str(len(samples)),near(e0,edge(prev['end_ns'],P)))
            check(cid+'.held_metadata_'+str(len(samples)),not node['accumulator_write'] and nxt['accumulator_write'] and not node['source_code_overwrite'] and not nxt['source_code_overwrite'])
            count+=multiplier;samples.append(dict(E0=e0,E1=e1,E2=e2,multiplicity=multiplier))
    visit(read(path))
    check(cid+'.held_batch_count',count==(2048 if cid=='07_pcm' else 32))
    return {'batches_checked':count,'representative_actual_edges':samples}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('run');ap.add_argument('--compare');args=ap.parse_args()
    run=Path(args.run).resolve();snap=run/'snapshot';task=snap/'tasks/task1_table_I_NeuroSim';report={}
    summary=read(run/'summary.json');check('fresh_run_PASS',summary['status']=='PASS')
    manifest=read(run/'snapshot_manifest.json')
    for rel,digest in manifest.items():check('snapshot_hash.'+rel,sha(snap/rel)==digest)
    for row in summary['case_results']:
        cid=row['case_id'];d=run/cid;c=read(task/'configs/cases'/f'{cid}.json');r=read(d/'resolved.json');result=read(d/'result.json');p=r['native_parameters_ns'];b=r['backend']
        build=d/'backend';bm=read(build/'source_manifest.json');commands=read(build/'commands.json')
        check(cid+'.fresh_compile_command',commands[0]['returncode']==0 and commands[0]['log']=='build.log' and 'g++' in commands[0]['argv'][0] and str(run) in ' '.join(commands[0]['argv']))
        check(cid+'.all_commands_successful',all(x['returncode']==0 for x in commands))
        check(cid+'.locked_backend',bm['backend_sha']=='8a88abf85844c0e1ba17cc771ea535fff6040456')
        check(cid+'.constructor_patch',sha(build/'constructor.patch')==bm['constructor_patch_sha256'])
        check(cid+'.request_header',sha(build/'src/request.h')==bm['request_header_sha256'])
        for filename,digest in bm['upstream_files'].items():
            if filename!='Param.cpp':check(cid+'.upstream_source.'+filename,sha(build/'src'/filename)==digest)
        for filename,digest in bm['adapter_headers'].items():check(cid+'.adapter_header.'+filename,sha(build/'src'/filename)==digest)
        if cid not in PILOTS:
            check(cid+'.actual_adapter_cpp',sha(build/'src/step4.cpp')==bm['adapter_sha256']==sha(task/'step4_v2/backend.cpp'))
            for filename in ('DFF.cpp','Adder.cpp','SarADC.cpp'):
                check(cid+'.MemCell_context_unread.'+filename,not re.findall(r'\bcell\s*\.\s*([A-Za-z_]\w*)',(build/'src'/filename).read_text()))
        # Validate source pointers and normalization, not just resolved outputs.
        unit={'ns':1e-9,'us':1e-6,'ms':1e-3,'s':1,'V':1,'uA':1e-6,'nA':1e-9,'fF':1e-15,'pF':1e-12,'ohm':1,'kohm':1e3}
        for primitive in c['device']['primitives']:
            original=primitive['original'];norm=primitive['normalized'];pid=primitive['id']
            if original['unit'] in unit:
                check(cid+'.primitive_normalized.'+pid,math.isclose(original['value']*unit[original['unit']],norm['value'],rel_tol=2e-12,abs_tol=1e-24))
            for ref in primitive['source_refs']:
                source=c['provenance']['sources'][ref['source_id']]
                native=pointer(read(snap/source['path']),ref['json_pointer'])
                if isinstance(native,dict) and 'binding' in native:
                    # RRAM's historical T_B=T_A capability policy is a source
                    # of the frozen20ns value, not a current shared-SAR route.
                    shared=read(snap/c['provenance']['sources']['shared']['path'])
                    native=shared['common_conditions']['propagation']['profile_values']['reference'][native['binding']]
                check(cid+'.primitive_source.'+pid,native==original['value'])
            if norm['unit']=='s':check(cid+'.primitive_resolved.'+pid,near(p[pid],norm['value']*1e9))
        expected=expectations(cid,c,p,b);S=result['streaming']['delta_S_ns'];R=result['resident_load']['T_R_ns']
        check(cid+'.independent_streaming',near(S,expected['streaming_ns']))
        check(cid+'.independent_resident',near(R,expected['resident_ns']))
        m=result['maintenance'];alpha=expected['availability']
        if cid=='09_gain_cell_edram':
            for key,actual in [('maintenance_ns',m['busy_ns']),('guard_ns',m['guard_ns']),('frame_ns',m['scheduled_frame_period_ns']),('availability',m['availability'])]:
                check(cid+'.independent_'+key,near(expected[key],actual))
            check(cid+'.retention_limit_not_changed',m['retention_limit_ns']==p['refresh_period']==400000)
            check(cid+'.integer_frame',near(m['scheduled_frame_period_ns']/b['actual_period_ns'],round(m['scheduled_frame_period_ns']/b['actual_period_ns'])))
            check(cid+'.actual_rewrite_proof',m['retention_schedule_proof']['physical_writeback_interval_max_ns']<=p['refresh_period'])
            check(cid+'.no_maintenance_payload',m['workload_write_Byte']==0)
        metrics=result['derived_metrics'];L=c['logical']
        expected_metrics={'rho_Byte_per_s':L['B_S_Byte']*1e9/S*alpha,'tau_Byte_per_s':L['B_R_Byte']*1e9/R*alpha,
                          'RI_star':L['B_S_Byte']*R/(L['B_R_Byte']*S),'U_star':R/S}
        for key,value in expected_metrics.items():check(cid+'.metric.'+key,near(metrics[key],value))
        check(cid+'.logical_payload',L['B_S_Byte']==L['K']*L['bytes_per_input'] and L['B_R_Byte']==L['K']*L['N']*L['bytes_per_weight'])
        if cid in PILOTS:
            check(cid+'.pilot_entire_result_unchanged',result==read(task/'results/step3_v2/integration-audited-v2'/cid/'result.json'))
        else:
            paths=b['paths'];P=b['actual_period_ns'];minimum=max(x['delay_ns']/x['available_cycles'] for x in paths)
            check(cid+'.derived_timing_minimum',near(minimum,b['timing_min_period_ns']))
            check(cid+'.clock_policy',near(P,math.ceil(max(5,minimum)*2-1e-10)/2))
            for path in paths:
                check(cid+'.valid_path_window.'+path['id'],path['capture_edge']-path['launch_edge']==path['available_cycles'] and path['delay_ns']<=path['available_cycles']*P+1e-9)
            check(cid+'.no_SubArray',not b['coverage']['SubArray_used'] and not b['coverage']['array_or_device_material_simulated'])
            check(cid+'.aggregate_write_is_null',b['coverage']['aggregate_write_return'] is None)
            check(cid+'.SAR_return',b['sar_ns'] is None if cid in ('03_nor_2d','06_mram','08_feram_hfo2','10_fenor_3d') else near(b['sar_ns'],11))
            if b.get('frame_preselection'):
                f=b['frame_preselection'];raw=b['raw_module_returns'];prefix='digital_mac_source_'
                classmax=max(v for k,v in raw.items() if k.startswith(prefix) and k.endswith('_full_s'))*1e9
                check(cid+'.source_envelopes_recombine',near(classmax,f['V1_all_sources_relaunched_delay_ns']))
                for name in f['early_sources']:
                    check(cid+'.early_pin_'+name,f['source_pin_settle_ns'][name]<=p[f['lead_source_parameter']]+1e-9)
                    check(cid+'.early_full_'+name,f['full_source_to_capture_delay_ns'][prefix+name+'_full_s']<=p[f['lead_source_parameter']]+P+1e-9)
                dynamic=max(raw[prefix+name+'_full_s'] for name in ('ibit','acc_data','weight'))*1e9
                check(cid+'.dynamic_one_cycle',near(dynamic,f['dynamic_complete_path_delay_ns']) and dynamic<=P+1e-9)
            if cid in ('07_pcm','09_gain_cell_edram'):
                data=next(x for x in paths if x['id'].startswith(('pcm_decode','gc_decode')))
                enable=next(x for x in paths if x['id']=='capture_enable_path')
                check(cid+'.data_E0_E2',data['launch_edge']==0 and data['capture_edge']==2 and data['available_cycles']==2)
                check(cid+'.enable_E1_E2',enable['launch_edge']==1 and enable['capture_edge']==2 and enable['available_cycles']==1)
                h=b['source_hold_window'];check(cid+'.E1_phase_only',h['edge_updates']['1']==['phase_only'] and h['no_new_intermediate_registers'] and not h['overlap'])
                expected['held_lifecycle']=semantic_trace_check(cid,d/'streaming_trace.json',b)
            for field in ('grouping_checks','numerical_checks','timing_checks'):
                data=read(d/(field+'.json'))
                check(cid+'.'+field,all(x.get('status')=='PASS' for x in data.values()) if field=='grouping_checks' else data['status']=='PASS')
        for source_row in read(d/'stage_sources.json')['stages']:
            check(cid+'.source_category.'+source_row['stage_id'],source_row['source_category'] in {'direct_neurosim_module','neurosim_gate_composition','retained_native_or_arithmetic_service','interface_and_schedule'})
            if source_row['provider'].startswith('retained_arithmetic'):
                check(cid+'.retained_not_circuit.'+source_row['stage_id'],source_row['source_category']=='retained_native_or_arithmetic_service')
        expected['metrics']=expected_metrics;report[cid]=expected
        if cid in ('03_nor_2d','04_nand_3d'):
            retained_PE=(64*p['page_program']+4*p['sector_erase']) if cid=='03_nor_2d' else (6144*p['page_program']+64*p['block_erase'])
            expected['retained_native_PE_fraction']=retained_PE/R
            expected['PE_interpretation']='High native P/E fraction explains old/new proximity; retained source budgets are not independently validated by NeuroSim.'
    # NAND stress values must come from explicit additional native budget work.
    nd=run/'04_nand_3d';stress=read(nd/'budget_sensitivity.json');base=stress['rows'][0];P=read(nd/'resolved.json')['backend']['actual_period_ns']
    for row in stress['rows']:
        f=row['factor'];check('NAND_budget_stream_'+str(f),near(row['delta_S_ns']-base['delta_S_ns'],960*(f-1)*P))
        check('NAND_budget_resident_'+str(f),near(row['T_R_ns']-base['T_R_ns'],448*(f-1)*P))
    # Independently computed edge endpoints test the production scheduler.
    spec=importlib.util.spec_from_file_location('frozen_engine_under_test',task/'step4_v2/engine.py');engine=importlib.util.module_from_spec(spec);spec.loader.exec_module(engine)
    examples=[]
    for finish in (9.7,9.75,9.8,9.99,10.,10.01):
        capture={'id':'capture','kind':'boundary','margin_ns':.25,'resources':['hold'],'provider':'explicit_capture'}
        cycle={'id':'cycle','kind':'digital','cycles':1,'resources':['output'],'provider':'neurosim_composed'}
        rc=engine.run([capture],10,start_ns=finish);rd=engine.run([cycle],10,start_ns=finish)
        check('edge_capture_'+str(finish),near(rc['end_ns'],edge(finish,10,.25)))
        check('edge_cycle_'+str(finish),near(rd['end_ns'],edge(finish,10)+10))
        check('wrapper_'+str(finish),near(engine.run([{'repeat':1,'axis':'transparent','steps':[capture]}],10,start_ns=finish)['end_ns'],rc['end_ns']))
        check('split_cycle_'+str(finish),near(engine.run([dict(cycle,cycles=2)],10,start_ns=finish)['end_ns'],engine.run([cycle,cycle],10,start_ns=finish)['end_ns']))
        examples.append(dict(physical_complete_ns=finish,capture_only_end_ns=rc['end_ns'],full_cycle_end_ns=rd['end_ns']))
    def rejected(label,fn):
        try:fn()
        except AssertionError:check(label,True)
        else:check(label,False)
    rejected('cycle_entry_setup_is_invalid',lambda:engine.run([dict(cycle,margin_ns=.25)],10))
    check('included_capture_exact_edge_no_repeat_setup',engine.run([dict(capture,margin_ns=0,operation_semantics='included_capture')],10,start_ns=10)['end_ns']==10)
    # Production adapter only creates the subject plan for state-machine
    # mutation tests. It supplies none of the independent expected formulas.
    spec=importlib.util.spec_from_file_location('frozen_adapter_under_test',task/'step4_v2/adapters/native.py');adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    for cid in ('07_pcm','09_gain_cell_edram'):
        cfg=read(task/'configs/cases'/f'{cid}.json');resolved=read(run/cid/'resolved.json');bb=resolved['backend'];pp=resolved['native_parameters_ns']
        plan=adapter.build(cfg,pp,bb)
        for label in ('write_acc_at_E1','overwrite_source_before_E2','new_SAR_before_E2'):
            bad=copy.deepcopy(plan);body=bad['streaming'][1]['steps'];idx=next(i for i,x in enumerate(body) if x.get('id')=='digital_reconstruct.phase1')
            if label=='write_acc_at_E1':body[idx]['accumulator_write']=True
            elif label=='overwrite_source_before_E2':body[idx]['source_code_overwrite']=True
            else:body.insert(idx+1,copy.deepcopy(next(x for x in body if x.get('id')=='sar')))
            rejected(cid+'.actual_lifecycle_reject.'+label,lambda:engine.validate_timing(cfg,bad,bb))
        if cid=='09_gain_cell_edram':
            F=math.floor(pp['refresh_period']/bb['actual_period_ns'])*bb['actual_period_ns'];completions=[]
            for frame in range(11):
                rr=engine.run(list(engine.event_stream(plan['maintenance'])),bb['actual_period_ns'],start_ns=frame*F)
                completions.append([x['end_ns'] for x in rr['trace'] if x.get('id')=='refresh_decode_load_rewrite.current_program'])
            ages=[y-x for first,second in zip(completions,completions[1:]) for x,y in zip(first,second)]
            check('GC_2560_physical_rewrite_intervals',len(ages)==2560 and all(near(x,F) and x<=pp['refresh_period'] for x in ages))
            report[cid]['independent_retention_trace']={'frames':11,'physical_interval_pairs':len(ages),'minimum_ns':min(ages),'maximum_ns':max(ages),'limit_ns':pp['refresh_period']}
            for limit in (1,30000):
                badp=dict(pp,refresh_period=limit);_,maintenance,mm=engine.evaluate(cfg,adapter.build(cfg,badp,bb),bb)
                check('GC_infeasible_'+str(limit),not maintenance['feasible'] and mm['status']=='INFEASIBLE' and mm['rho_Byte_per_s'] is None)
                check('GC_no_clipped_alpha_'+str(limit),maintenance['availability'] is None if limit==1 else maintenance['availability']<0)
    # Compare independent builds after every formula has been assessed.
    comparison={}
    if args.compare:
        master=Path(args.compare)
        def normalize(x):
            if isinstance(x,str):return x.replace(str(run),'<RUN>').replace(str(master),'<RUN>')
            if isinstance(x,list):return [normalize(v) for v in x]
            if isinstance(x,dict):return {k:normalize(v) for k,v in x.items()}
            return x
        for row in summary['case_results']:
            cid=row['case_id'];names=['result.json','resolved.json','replay.json','stage_sources.json']
            if cid not in PILOTS:names+=['timing_checks.json','grouping_checks.json','numerical_checks.json','sensitivity.json','budget_sensitivity.json','v1_v2_comparison.json']
            for name in names:
                equal=normalize(read(run/cid/name))==normalize(read(master/cid/name));check('independent_build_equal.'+cid+'.'+name,equal);comparison[cid+'/'+name]=equal
        check('summary_rows_equal',summary['case_results']==read(master/'summary.json')['case_results'])
    payload={'status':'PASS','checks_count':len(CHECKS),'checks':CHECKS,'independent_formulas':report,'edge_examples':examples,'independent_build_comparison':comparison,
             'source_policy':'Expected formulas use frozen primitives/counts and actual module returns; no production calculator supplies expected services.',
             'reviewer_disclosure':'Reviewer authored six native adapters in V1. No V2 production design or edits; all audit writes local.'}
    (run/'review_independent.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':'PASS','checks':len(CHECKS),'output':str(run/'review_independent.json')}))

if __name__=='__main__':main()
