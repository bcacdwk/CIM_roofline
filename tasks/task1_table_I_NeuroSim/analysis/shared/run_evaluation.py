#!/usr/bin/env python3
"""Rebuild and evaluate the ten reference CIM configurations in a fresh local run."""
import argparse, csv, datetime, hashlib, importlib.util, json, math, os
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

def evaluate(own, out, root, cxx):
    shared=own/'analysis/shared';sys.path.insert(0,str(shared/'array_backend'))
    import timing
    array=module('array_backend',shared/'array_backend/backend.py')
    schedule=module('array_schedule',shared/'array_backend/schedule.py')
    checks=module('array_checks',shared/'array_backend/checks.py')
    peripheral=module('peripheral_backend',shared/'peripheral_backend/backend.py')
    engine=module('service_engine',shared/'peripheral_backend/engine.py')
    dump(out/'interface_checks.json',engine.checks())
    rows=[]
    for cid in CASES:
        config=own/'analysis'/cid/'input.json';case=json.loads(config.read_text());p=parameters(case,shared)
        logical=case['logical'];assert logical['B_S_Byte']==logical['K']*logical['bytes_per_input'];assert logical['B_R_Byte']==logical['K']*logical['N']*logical['bytes_per_weight']
        work=out/cid;work.mkdir(); is_array=cid in ARRAY
        folder=shared/('array_backend' if is_array else 'peripheral_backend')
        adapter=module('adapter_'+cid,folder/'adapters'/((ARRAY[cid] if is_array else 'nand' if cid=='04_nand_3d' else 'native')+'.py'))
        execute=(array if is_array else peripheral).build(case,root,work/'backend',cxx,folder)
        b=execute('reference',wire_um=10.,operating_period_ns=None)
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
        dump(work/'resolved.json',resolved)
        result={'contract_version':'3.0.0','case_id':cid,'status':'OK' if maintenance.get('feasible',True) else 'FAILED','mode':'neurosim_device_service_reference','identity':{'backend_sha':SHA,'input_sha256':sha(config),'driver_sha256':sha(__file__)},'effective_config':{'resolved_snapshot':'resolved.json','resolved_sha256':sha(work/'resolved.json')},'derived_snapshot':{'actual_period_ns':b['actual_period_ns'],'module_returns':b['raw_module_returns'],'module_inventory':b['module_inventory'],'partial_area_scope':b['partial_area_scope']},'clocks':[clocks],'stages':[{**x,'service_kind':name} for name,value in services.items() for x in value['stages']],'streaming':streaming,'resident_load':resident,'maintenance':maintenance,'derived_metrics':metric,'checks':plan['checks']}
        if not is_array:result['coverage']=b['coverage'];result['derived_snapshot']['coverage']=b['coverage']
        dump(work/'result.json',result);dump(work/'timing_checks.json',timing_check)
        for name,value in services.items():dump(work/(name+'_trace.json'),value['trace'])
        sources=[]
        for stage in result['stages']:
            raw=stage['raw_returns'][0];kind='digital' if stage['timing_kind']=='digital_step' else 'boundary' if raw['value']==0 and raw['unit']=='ns' else 'physical'
            sources.append({'stage_id':stage['stage_id'],'service_kind':stage['service_kind'],'provider':stage['provider'],'source_category':engine.source_category(stage['provider'],kind,stage['stage_id']),'operation_semantics':stage.get('operation_semantics','cycle' if kind=='digital' else 'capture_or_included_native_boundary' if kind=='boundary' else 'native_service'),'raw_service_total_ns':stage['resource_occupancy_ns']-stage['boundary_wait_ns'],'interface_edge_wait_ns':stage['boundary_wait_ns']})
        dump(work/'stage_sources.json',{'category_policy':'source/operation classification; no stage-count coverage percentage','stages':sources})
        row={'case_id':cid,**{k:logical[k] for k in ('K','N','B_S_Byte','B_R_Byte','bytes_per_input','bytes_per_weight')},'timing_min_period_ns':b['timing_min_period_ns'],'actual_period_ns':b['actual_period_ns'],'raw_delta_S_ns':s['latency_ns'],'raw_T_R_ns':r['latency_ns'],'effective_delta_S_ns':maintenance.get('effective_delta_S_ns',s['latency_ns']),'effective_T_R_ns':maintenance.get('effective_T_R_ns',r['latency_ns']),'availability':maintenance.get('availability',1.),**{k:v for k,v in metric.items() if k!='status'},'rho_MBps':metric['rho_Byte_per_s']/1e6,'tau_MBps':metric['tau_Byte_per_s']/1e6,'result_path':'analysis/'+cid+'/result.json','input_path':'analysis/'+cid+'/input.json'}
        assert math.isclose(row['rho_Byte_per_s'],logical['B_S_Byte']/row['effective_delta_S_ns']*1e9,rel_tol=1e-12)
        assert math.isclose(row['tau_Byte_per_s'],logical['B_R_Byte']/row['effective_T_R_ns']*1e9,rel_tol=1e-12)
        rows.append(row);print(json.dumps({'case_id':cid,'status':result['status'],'rho_MBps':row['rho_MBps'],'tau_MBps':row['tau_MBps']}),flush=True)
    dump(out/'ten_case_results.json',{'schema_version':1,'title':'NeuroSim 与器件估计结合的 CIM 评估','configuration':'reference','units':{'time':'ns','rate':'Byte/s and decimal MB/s (1 MB = 1e6 Byte)'},'scope':'public compatible circuit modules plus literature-supported device/array services; conditional model coverage','case_results':rows})
    with (out/'ten_case_results.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',default=os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim')));ap.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','g++-16'));ap.add_argument('--run-id',default='reference-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'));ap.add_argument('--export',action='store_true',help='Export only business results to this package after a successful local run');ap.add_argument('--worker',help=argparse.SUPPRESS);a=ap.parse_args()
    own=Path(__file__).resolve().parents[2];root=Path(a.root).expanduser().resolve();assert not any(x in str(root).lower() for x in ('onedrive','icloud','mobile documents'));assert Path(a.run_id).name==a.run_id and a.run_id not in ('.','..')
    if a.worker:evaluate(own,Path(a.worker),root,a.cxx);return
    out=root/'runs/cim-reference'/a.run_id;out.mkdir(parents=True,exist_ok=False)
    package=out/'package';files=list((own/'analysis/shared').rglob('*'))
    files += [own/'analysis'/cid/'input.json' for cid in CASES]
    files += [own/'provenance/neurosim.lock.json']
    manifest={}
    for src in files:
        if not src.is_file() or '__pycache__' in src.parts:continue
        rel=src.relative_to(own);dst=package/rel;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst);manifest[str(rel)]=sha(src)
    dump(out/'input_manifest.json',manifest)
    dump(out/'invocation.json',{'compiler':subprocess.check_output([a.cxx,'--version'],text=True).splitlines()[0],'python':sys.version,'locked_backend_sha':SHA,'argv':sys.argv,'case_count':10,'reproduction':'fresh source copy and compiler build per case; package contains no prior result'})
    cmd=[sys.executable,'-B',str(package/'analysis/shared/run_evaluation.py'),'--root',str(root),'--cxx',a.cxx,'--worker',str(out)]
    with (out/'run.log').open('w') as log:
        p=subprocess.Popen(cmd,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        for line in p.stdout:log.write(line);log.flush();print(line,end='',flush=True)
        if p.wait():raise SystemExit(p.returncode)
    if a.export:
        for name in ('ten_case_results.json','ten_case_results.csv'):
            dst=own/'analysis/data'/name;dst.parent.mkdir(exist_ok=True);shutil.copy2(out/name,dst)
        for cid in CASES:
            for name in ('result.json','resolved.json','stage_sources.json','backend/source_manifest.json','backend/constructor.patch'):
                dst=own/'analysis'/cid/name;dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(out/cid/name,dst)
    print(json.dumps({'status':'PASS','run':str(out),'exported':a.export}))
if __name__=='__main__':main()
