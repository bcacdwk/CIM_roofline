#!/usr/bin/env python3
"""Rebuild and evaluate the CIM reference configurations and paired native-service scenarios in a fresh local run."""
import argparse, copy, csv, datetime, hashlib, importlib.util, json, math, os
from pathlib import Path
import shutil, subprocess, sys
sys.dont_write_bytecode = True
CASES = ['01_sram_acim', '02_sram_dcim', '03_nor_2d', '04_nand_3d', '05_rram', '06_mram', '07_pcm', '08_feram_hfo2', '09_gain_cell_edram', '10_fenor_3d']
ARRAY = {'01_sram_acim':'acim', '02_sram_dcim':'dcim', '05_rram':'rram'}
SHA = '8a88abf85844c0e1ba17cc771ea535fff6040456'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);sys.modules[name]=m;spec.loader.exec_module(m);return m
def parameters(case, shared):
    """Primitive inputs only: reference propagation budget plus normalized device seconds."""
    p=dict(json.loads((shared/'inputs/service_conditions.json').read_text())['reference'])
    for x in case['device']['primitives']:
        if x['normalized']['unit']=='s':p[x['id']]=x['normalized']['value']*1e9
    p.setdefault('binary_verify_sense_ns',p['adc_batch'])
    return p

def evaluate(own, out, root, cxx, cases, scenarios):
    shared=own/'analysis/shared';sys.path.insert(0,str(shared/'array_backend'))
    import timing
    array=module('array_backend',shared/'array_backend/backend.py')
    schedule=module('array_schedule',shared/'array_backend/schedule.py')
    checks=module('array_checks',shared/'array_backend/checks.py')
    peripheral=module('peripheral_backend',shared/'peripheral_backend/backend.py')
    engine=module('service_engine',shared/'peripheral_backend/engine.py')
    dump(out/'interface_checks.json',engine.checks())
    from scenarios import apply, validate_bindings
    rows=[]; reference_rows=[]; executors={}; build_records={}
    for cid,scenario in [(cid,scenario) for cid in cases for scenario in scenarios]:
        config=own/'analysis'/cid/'input.json';case,scenario_metadata=apply(config,scenario);p=parameters(case,shared)
        logical=case['logical'];assert logical['B_S_Byte']==logical['K']*logical['bytes_per_input'];assert logical['B_R_Byte']==logical['K']*logical['N']*logical['bytes_per_weight']
        work=(out/cid if scenarios==['reference'] else out/cid/scenario);work.mkdir(parents=True); is_array=cid in ARRAY
        folder=shared/('array_backend' if is_array else 'peripheral_backend')
        adapter=module('adapter_'+cid,folder/'adapters'/((ARRAY[cid] if is_array else 'nand' if cid=='04_nand_3d' else 'native')+'.py'))
        if cid not in executors:
            compile_case=json.loads(config.read_text());build_out=out/cid/'backend'
            executors[cid]=(array if is_array else peripheral).build(compile_case,root,build_out,cxx,folder)
            binary=build_out/('pilot' if is_array else 'step4-backend')
            build_records[cid]={'binary_sha256':sha(binary),'source_manifest_sha256':sha(build_out/'source_manifest.json'),'build_directory':str(build_out.relative_to(out)),'compiled_once_for_scenarios':scenarios,'native_service_values_change_compiled_dimensions':False}
        execute=executors[cid]
        b=execute(scenario,wire_um=10.,operating_period_ns=None,scenario_case=case)
        if scenarios!=['reference']:
            (work/'backend').mkdir()
            for name in ('source_manifest.json','constructor.patch'):shutil.copy2(out/cid/'backend'/name,work/'backend'/name)
        dump(work/'execution_build.json',build_records[cid])
        if scenario==scenarios[0] and scenario_metadata['excluded_candidates']:
            exclusions=[]
            for i,excluded in enumerate(scenario_metadata['excluded_candidates']):
                invalid=copy.deepcopy(case)
                primitive=next(x for x in invalid['device']['primitives'] if x['id']==excluded['parameter'])
                primitive['normalized']['value']=excluded['value']*{'ns':1e-9,'us':1e-6,'ms':1e-3}[excluded['unit']]
                try:execute('excluded_candidate_'+str(i),wire_um=10.,operating_period_ns=None,scenario_case=invalid)
                except AssertionError as exc:
                    assert 'preselection not established during native read' in str(exc)
                    exclusions.append({'candidate':excluded,'status':'REJECTED_BY_UNCHANGED_BACKEND_QUALIFICATION','reason':str(exc),'actual_pin_settle_ns':b['frame_preselection']['settle_to_existing_combinational_pins_ns'],'same_binary_sha256':build_records[cid]['binary_sha256']})
                else:raise AssertionError('excluded candidate unexpectedly accepted')
            dump(out/cid/'excluded_candidate_checks.json',{'status':'PASS','candidates':exclusions})
        binding_check=validate_bindings(case,p,b,scenario_metadata)
        plan=adapter.build(case,p,b);assert all(plan['checks'].values()),cid
        if is_array:
            timing.select_period(b['paths'],b.get('reconstruction_window'),b['actual_period_ns']);timing.validate_plan(plan,b)
            s=schedule.run(plan['streaming'],b['actual_period_ns']);r=schedule.run(plan['resident'],b['actual_period_ns'])
            second_s=schedule.run(plan['streaming'],b['actual_period_ns'],start_ns=s['end_ns']);second_r=schedule.run(plan['resident'],b['actual_period_ns'],start_ns=r['end_ns'])
            assert engine.close(second_s['latency_ns'],s['latency_ns']) and engine.close(second_r['latency_ns'],r['latency_ns'])
            metric=schedule.metrics(case,s,r)
            maintenance={'raw_stage_metrics':None,'effective_stage_metrics':None,'workload_write_Byte':0,'recompute_required':True}
            timing_check=checks.run(case,plan,b)
            if 'local_transaction' in plan:
                local=schedule.run(plan['local_transaction'],b['actual_period_ns']);isolated=schedule.run(plan['isolated_transaction'],b['actual_period_ns']);txn=local['latency_ns'];isolated_ns=isolated['latency_ns'];txn_interval=schedule.run(plan['local_transaction'],b['actual_period_ns'],start_ns=local['end_ns'])['latency_ns']
            else:txn=p['sram_write_cycle'];isolated_ns=None;txn_interval=math.ceil(txn/b['actual_period_ns']-1e-10)*b['actual_period_ns']
            services={'streaming':s,'resident':r}
            resident={'transaction_latency_ns':txn,'transaction_service_interval_ns':txn_interval,'isolated_transaction_with_rail_ns':isolated_ns,'T_R_ns':r['latency_ns'],'matrix_service_interval_ns':second_r['latency_ns'],'payload_Byte':logical['B_R_Byte'],'transaction_payload_Byte':16,'coverage_status':'complete_hybrid_conditional_native_services','normalized_missing_backend_write':{'value':None,'status':'NOT_IMPLEMENTED','reason':'locked V1.4 aggregate write disabled; no Training substitution'}}
            streaming={'latency_ns':s['latency_ns'],'delta_S_ns':s['latency_ns'],'initiation_interval_ns':second_s['latency_ns'],'proof':'strict serial vector schedule; all SAR/data resources retained until release; second vector simulated with same global phase'}
            clocks={'clock_id':'lv_core','target_period_ns':5.,'combinational_limit_ns':max(x['delay_ns'] for x in b['paths']),'timing_min_period_ns':b['timing_min_period_ns'],'policy_min_period_ns':b['policy_min_period_ns'],'selection_policy':b['selection_policy'],'actual_period_ns':b['actual_period_ns'],'closure_status':'modeled_complete_paths_under_declared_topology','constraining_paths':b['paths']}
        else:
            services,maintenance,metric=engine.evaluate(case,plan,b);s=services['streaming'];r=services['resident'];timing_check=engine.validate_timing(case,plan,b)
            for name in ('streaming','resident'):
                again=engine.run(plan[name],b['actual_period_ns'],start_ns=services[name]['end_ns']);assert engine.close(again['latency_ns'],services[name]['latency_ns'])
            events=plan['resident'] if logical['resident_transaction_Byte']==logical['B_R_Byte'] else plan.get('atomic_resident',plan['resident'][0]['steps'])
            txn=engine.run(events,b['actual_period_ns']);txn2=engine.run(events,b['actual_period_ns'],start_ns=txn['end_ns']);assert engine.close(txn2['latency_ns'],txn['latency_ns'])
            streaming={'latency_ns':s['latency_ns'],'delta_S_ns':s['latency_ns'],'initiation_interval_ns':s['latency_ns'],'effective_service_cost_ns':maintenance.get('effective_delta_S_ns',s['latency_ns']),'latency_context':'raw physical service without maintenance interruption; arrival-dependent maintenance waiting is not raw/availability','proof':'strict serial; two complete consecutive vectors; no overlap'}
            resident={'transaction_latency_ns':txn['latency_ns'],'T_R_ns':r['latency_ns'],'transaction_service_interval_ns':txn2['latency_ns'],'matrix_service_interval_ns':r['latency_ns'],'payload_Byte':logical['B_R_Byte'],'transaction_payload_Byte':logical['resident_transaction_Byte'],'effective_service_cost_ns':maintenance.get('effective_T_R_ns',r['latency_ns']),'coverage_status':'complete_hybrid_conditional_native_services','normalized_missing_backend_write':{'value':None,'status':'NOT_IMPLEMENTED','reason':'no compatible aggregate write model; complete native service plus explicit public control retained'}}
            clocks={'clock_id':'lv_core','target_period_ns':5.,'combinational_limit_ns':max(x['delay_ns'] for x in b['paths']),'timing_min_period_ns':b['timing_min_period_ns'],'actual_period_ns':b['actual_period_ns'],'selection_policy':b['selection_policy'],'closure_status':b.get('closure_status','modeled_paths_only_with_explicit_native_and_arithmetic_budget_exclusions'),'constraining_paths':b['paths']}
        resolved={'contract_version':'3.0.0','logical':logical,'physical':case['physical'],'resources':case['resources'],'native_parameters_ns':p,'backend':b,'adapter':plan['snapshot'],'source_provenance':case['provenance'],'schedule_policy':{'kind':'strict_serial_ordered_templates_no_overlap','edge_rule':'physical subsequences continuous; align at explicit digital consumer or boundary','maintenance':'raw request latency separated from long-term availability-adjusted service cost'}}
        if scenarios!=['reference']:resolved['scenario']=scenario_metadata
        dump(work/'resolved.json',resolved)
        result={'contract_version':'3.0.0','case_id':cid,'status':'OK' if maintenance.get('feasible',True) else 'FAILED','mode':'neurosim_device_service_reference','identity':{'backend_sha':SHA,'input_sha256':sha(config),'driver_sha256':sha(__file__)},'effective_config':{'resolved_snapshot':'resolved.json','resolved_sha256':sha(work/'resolved.json')},'derived_snapshot':{'actual_period_ns':b['actual_period_ns'],'module_returns':b['raw_module_returns'],'module_inventory':b['module_inventory'],'partial_area_scope':b['partial_area_scope']},'clocks':[clocks],'stages':[{**x,'service_kind':name} for name,value in services.items() for x in value['stages']],'streaming':streaming,'resident_load':resident,'maintenance':maintenance,'derived_metrics':metric,'checks':plan['checks']}
        if scenarios!=['reference']:result['scenario']={'id':scenario,'input_sha256':scenario_metadata['input_file_sha256']}
        if not is_array:result['coverage']=b['coverage'];result['derived_snapshot']['coverage']=b['coverage']
        dump(work/'result.json',result);dump(work/'timing_checks.json',timing_check);dump(work/'scenario_binding_checks.json',binding_check)
        for name,value in services.items():dump(work/(name+'_trace.json'),value['trace'])
        sources=[]
        for stage in result['stages']:
            raw=stage['raw_returns'][0];kind='digital' if stage['timing_kind']=='digital_step' else 'boundary' if raw['value']==0 and raw['unit']=='ns' else 'physical'
            sources.append({'stage_id':stage['stage_id'],'service_kind':stage['service_kind'],'provider':stage['provider'],'source_category':engine.source_category(stage['provider'],kind,stage['stage_id']),'operation_semantics':stage.get('operation_semantics','cycle' if kind=='digital' else 'capture_or_included_native_boundary' if kind=='boundary' else 'native_service'),'raw_service_total_ns':stage['resource_occupancy_ns']-stage['boundary_wait_ns'],'interface_edge_wait_ns':stage['boundary_wait_ns']})
        dump(work/'stage_sources.json',{'category_policy':'source/operation classification; no stage-count coverage percentage','stages':sources})
        row={'case_id':cid,**{k:logical[k] for k in ('K','N','B_S_Byte','B_R_Byte','bytes_per_input','bytes_per_weight')},'timing_min_period_ns':b['timing_min_period_ns'],'actual_period_ns':b['actual_period_ns'],'raw_delta_S_ns':s['latency_ns'],'raw_T_R_ns':r['latency_ns'],'effective_delta_S_ns':maintenance.get('effective_delta_S_ns',s['latency_ns']),'effective_T_R_ns':maintenance.get('effective_T_R_ns',r['latency_ns']),'availability':maintenance.get('availability',1.),**{k:v for k,v in metric.items() if k!='status'},'rho_MBps':metric['rho_Byte_per_s']/1e6,'tau_MBps':metric['tau_Byte_per_s']/1e6,'result_path':'analysis/'+cid+'/result.json','input_path':'analysis/'+cid+'/input.json'}
        assert math.isclose(row['rho_Byte_per_s'],logical['B_S_Byte']/row['effective_delta_S_ns']*1e9,rel_tol=1e-12)
        assert math.isclose(row['tau_Byte_per_s'],logical['B_R_Byte']/row['effective_T_R_ns']*1e9,rel_tol=1e-12)
        if scenario=='reference':reference_rows.append(dict(row))
        if scenarios!=['reference']:
            row.update(scenario=scenario,feasible=maintenance.get('feasible',True),scenario_parameters=scenario_metadata['parameters'],scenario_input_path='analysis/'+cid+'/scenarios.json',result_path='analysis/'+cid+'/scenarios/'+scenario+'/result.json')
        rows.append(row);print(json.dumps({'case_id':cid,'scenario':scenario,'status':result['status'],'rho_MBps':row['rho_MBps'],'tau_MBps':row['tau_MBps']}),flush=True)
    def export_table(name,document,entries):
        dump(out/(name+'.json'),{**document,'case_results':entries})
        with (out/(name+'.csv')).open('w') as f:
            w=csv.DictWriter(f,fieldnames=list(entries[0]));w.writeheader();w.writerows([{k:json.dumps(v,ensure_ascii=False,sort_keys=True) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in entries])
    typical={'schema_version':1,'title':'NeuroSim 与器件估计结合的 CIM 评估','configuration':'reference','units':{'time':'ns','rate':'Byte/s and decimal MB/s (1 MB = 1e6 Byte)'},'scope':'public compatible circuit modules plus literature-supported device/array services; conditional model coverage'}
    if scenarios==['reference']:export_table('ten_case_results',typical,rows)
    else:
        export_table('paired_scenario_results',{'schema_version':1,'title':'NeuroSim 与器件估计结合的 CIM 配对工程情景','scenario_order':scenarios,'scenario_semantics':'conditional paired native-service budgets at fixed hardware, not statistical/PVT bounds; SAR and digital timing are recomputed by the selected unchanged model','units':typical['units']},rows)
        if reference_rows:export_table('reference_results',typical,reference_rows)


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',default=os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim')));ap.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','g++-16'));ap.add_argument('--run-id',default='reference-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));ap.add_argument('--export',action='store_true',help='Export only business results to this package after a successful local run');ap.add_argument('--worker',help=argparse.SUPPRESS);ap.add_argument('--case',choices=['all',*CASES],default='all');ap.add_argument('--scenario',choices=['all','optimistic','reference','pessimistic'],default='reference');a=ap.parse_args()
    cases=CASES if a.case=='all' else [a.case];scenarios=['optimistic','reference','pessimistic'] if a.scenario=='all' else [a.scenario]
    if a.export and (a.case!='all' or a.scenario not in ('reference','all')):ap.error('--export requires all ten cases and either reference or all three scenarios; partial local runs never replace authoritative tables')
    own=Path(__file__).resolve().parents[2];root=Path(a.root).expanduser().resolve();assert not any(x in str(root).lower() for x in ('onedrive','icloud','mobile documents'));assert Path(a.run_id).name==a.run_id and a.run_id not in ('.','..')
    if a.worker:evaluate(own,Path(a.worker),root,a.cxx,cases,scenarios);return
    out=root/'runs/cim-reference'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    package=out/'package';files=list((own/'analysis/shared').rglob('*'))
    files += [own/'analysis'/cid/name for cid in cases for name in ('input.json','scenarios.json')]
    files += [own/'provenance/neurosim.lock.json']
    manifest={}
    for src in files:
        if not src.is_file() or '__pycache__' in src.parts:continue
        rel=src.relative_to(own);dst=package/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest[str(rel)]=sha(src)
    dump(out/'input_manifest.json',manifest)
    dump(out/'invocation.json',{'compiler':subprocess.check_output([a.cxx,'--version'],text=True).splitlines()[0],'python':sys.version,'locked_backend_sha':SHA,'argv':sys.argv,'case_count':len(cases),'scenarios':scenarios,'fresh_builds':len(cases),'scenario_executions':len(cases)*len(scenarios),'reproduction':'fresh source copy and compiler build per case; package contains no prior result'})
    cmd=[sys.executable,'-B',str(package/'analysis/shared/run_evaluation.py'),'--root',str(root),'--cxx',a.cxx,'--worker',str(out),'--case',a.case,'--scenario',a.scenario]
    with (out/'run.log').open('w') as log:
        p=subprocess.Popen(cmd,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for line in p.stdout:log.write(line);log.flush();print(line,end='',flush=True)
        if p.wait():raise SystemExit(p.returncode)
    if a.export:
        name='ten_case_results' if a.scenario=='reference' else 'paired_scenario_results'
        for suffix in ('.json','.csv'):
            dst=own/'analysis/data'/(name+suffix);dst.parent.mkdir(exist_ok=True);shutil.copy2(out/(name+suffix),dst)
        for cid in cases:
            for scenario in scenarios:
                source=out/cid if a.scenario=='reference' else out/cid/scenario
                target=own/'analysis'/cid if a.scenario=='reference' else own/'analysis'/cid/'scenarios'/scenario
                for rel in ('result.json','resolved.json','stage_sources.json','scenario_binding_checks.json','execution_build.json','backend/source_manifest.json','backend/constructor.patch'):
                    dst=target/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source/rel,dst)
            if (out/cid/'excluded_candidate_checks.json').exists():
                shutil.copy2(out/cid/'excluded_candidate_checks.json',own/'analysis'/cid/'excluded_candidate_checks.json')
    print(json.dumps({'status':'PASS','run':str(out),'exported':a.export}))
if __name__=='__main__':main()
