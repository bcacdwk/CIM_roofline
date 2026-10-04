#!/usr/bin/env python3
"""Three reference pilots; snapshots/builds/logs stay in a new local directory.

From any cwd: python3 <task>/scripts/run_step3.py --case all --run-id <new>
--mode replay retains the original-time migration regression, no NeuroSim labels.
"""
import argparse, copy, csv, datetime, hashlib, importlib, json, math, os
from pathlib import Path
import shutil, subprocess, sys
sys.dont_write_bytecode=True
CASE={'01_sram_acim':'acim','02_sram_dcim':'dcim','05_rram':'rram'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',default=os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim')))
    ap.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','g++-16'));ap.add_argument('--case',choices=['all',*CASE],default='all')
    ap.add_argument('--run-id',default='pilot-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    ap.add_argument('--mode',choices=['pilot','replay'],default='pilot');ap.add_argument('--export',action='store_true');ap.add_argument('--no-export',action='store_true');ap.add_argument('--worker',help=argparse.SUPPRESS)
    a=ap.parse_args();own=Path(__file__).resolve().parents[1];root=Path(a.root).expanduser().resolve();root.mkdir(exist_ok=True)
    assert not any(x in str(root).lower() for x in ['onedrive','icloud','mobile documents'])
    assert Path(a.run_id).name==a.run_id and a.run_id not in ['.','..']
    cases=list(CASE) if a.case=='all' else [a.case]
    if not a.worker:
        repo=own.parents[1];out=root/'runs/step3'/a.run_id;out.mkdir(parents=True,exist_ok=False)
        snap=out/'snapshot';task=snap/'tasks/task1_table_I_NeuroSim';task.mkdir(parents=True)
        inputs=[]
        for directory in ['pilots','contracts']:
            for f in sorted((own/directory).rglob('*')):
                if f.is_file() and f.suffix in ['.py','.cpp','.json','.md','.csv']:
                    dest=task/f.relative_to(own);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
        for rel in ['scripts/run_step3.py','scripts/check_step2.py','probes/interface_revision/legacy_replay.py','provenance/neurosim.lock.json']:
            f=own/rel;dest=task/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
        for cid in cases:
            f=own/'configs/cases'/f'{cid}.json';dest=task/f.relative_to(own);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
            for source in json.loads(f.read_text())['provenance']['sources'].values():
                if not isinstance(source,dict) or 'path' not in source:continue
                src=repo/source['path'];assert sha(src)==source['sha256'],src
                dest=snap/source['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);inputs.append(src)
        manifest={str(f.relative_to(repo)):sha(f) for f in inputs}
        dump(out/'snapshot_manifest.json',manifest)
        initial={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=repo,text=True),'mode':a.mode,'selected_cases':cases,'compiler':subprocess.check_output([a.cxx,'--version'],text=True).splitlines()[0],'python':sys.version,'baseline':'e93cd8aec72d61d8a55c00c76453d58615ef5b67','device_baseline':'a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0'}
        dump(out/'invocation.json',initial)
        argv=[sys.executable,'-B',str(task/'scripts/run_step3.py'),'--root',str(root),'--cxx',a.cxx,'--case',a.case,'--run-id',a.run_id,'--mode',a.mode,'--worker',str(out)]
        completed=subprocess.run(argv,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/'run.log').write_text(completed.stdout)
        print(completed.stdout,end='')
        if completed.returncode:raise SystemExit(completed.returncode)
        if a.export and not a.no_export:
            export=own/'results/step3'/a.run_id;export.mkdir(parents=True,exist_ok=False)
            whitelist=['summary.json','summary.csv','snapshot_manifest.json','invocation.json']
            for cid in cases:
                whitelist += [cid+'/result.json',cid+'/resolved.json',cid+'/sensitivity.json',cid+'/backend/source_manifest.json',cid+'/backend/constructor.patch'] if a.mode=='pilot' else [cid+'/replay.json']
            for rel in whitelist:
                f=out/rel;assert f.stat().st_size<1_000_000,rel
                dest=export/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
            dump(own/'results/step3/latest.json',{'run_id':a.run_id,'mode':a.mode,'status':'PASS','summary':str((export/'summary.json').relative_to(own))})
        print(json.dumps({'run':str(out),'status':'PASS','mode':a.mode}));return
    out=Path(a.worker);repo=own.parents[1];sys.path.insert(0,str(own/'pilots'));sys.path.insert(0,str(own/'scripts'));sys.path.insert(0,str(own/'probes/interface_revision'))
    import backend,schedule,legacy_replay
    from check_step2 import schema_check
    rows=[]
    for cid in cases:
        config_path=own/'configs/cases'/f'{cid}.json';case=json.loads(config_path.read_text());schema_check(case,json.loads((own/'contracts/case.schema.json').read_text()))
        work=out/cid;work.mkdir();p=legacy_replay.parameters(case,repo)
        # Replay remains a separate calculation and mode. Final saved totals only enter comparison AFTER aggregation.
        replay=legacy_replay.aggregate(case,p)
        if a.mode=='replay':
            expected,source=legacy_replay.expected_reference(case,repo);assert all(math.isclose(replay[k],v,rel_tol=1e-12,abs_tol=1e-7) for k,v in expected.items())
            replay['comparison_source']=source;dump(work/'replay.json',replay);rows.append({'case_id':cid,'mode':'v3_original_time_replay','delta_S_ns':replay['raw_delta_S_ns'],'T_R_ns':replay['raw_T_R_ns']});continue
        execute=backend.build(case,root,work/'backend',a.cxx,own/'pilots');b=execute('reference')
        adapter=importlib.import_module('adapters.'+CASE[cid])
        def evaluate(par,model,align=True):
            plan=adapter.build(case,par,model);assert all(plan['checks'].values())
            return plan,schedule.run(plan['streaming'],model['actual_period_ns'],align=align),schedule.run(plan['resident'],model['actual_period_ns'],align=align)
        plan,s,r=evaluate(p,b);period=b['actual_period_ns']
        again=schedule.run(plan['streaming'],period,start_ns=s['end_ns']);assert math.isclose(again['latency_ns'],s['latency_ns'],rel_tol=1e-10)
        again_r=schedule.run(plan['resident'],period,start_ns=r['end_ns']);assert math.isclose(again_r['latency_ns'],r['latency_ns'],rel_tol=1e-10)
        dump(work/'streaming_trace.json',s['trace']);dump(work/'resident_trace.json',r['trace'])
        # Cause-isolating controls: same event model without edges at v3 clock, then real clock, then edges.
        old_clock=copy.deepcopy(b);old_clock['actual_period_ns']=5.
        _,sar_only_s,sar_only_r=evaluate(p,old_clock,False)
        _,clock_s,clock_r=evaluate(p,b,False)
        metric=schedule.metrics(case,s,r)
        expected,source=legacy_replay.expected_reference(case,repo)
        assert all(math.isclose(replay[k],v,rel_tol=1e-12,abs_tol=1e-7) for k,v in expected.items())
        comparison={'v3':{'delta_S_ns':replay['raw_delta_S_ns'],'T_R_ns':replay['raw_T_R_ns']},'source':source,'difference_ns':{'streaming':s['latency_ns']-replay['raw_delta_S_ns'],'resident':r['latency_ns']-replay['raw_T_R_ns']},'streaming_cause_ledger_ns':{'SAR_replacement_and_explicit_service_changes':sar_only_s['latency_ns']-replay['raw_delta_S_ns'],'digital_period_change':clock_s['latency_ns']-sar_only_s['latency_ns'],'consumer_boundary_wait':s['latency_ns']-clock_s['latency_ns']},'resident_cause_ledger_ns':{'native_and_explicit_service_changes':sar_only_r['latency_ns']-replay['raw_T_R_ns'],'digital_period_change':clock_r['latency_ns']-sar_only_r['latency_ns'],'consumer_boundary_wait':r['latency_ns']-clock_r['latency_ns']}}
        if 'local_transaction' in plan:
            local=schedule.run(plan['local_transaction'],period);isolated=schedule.run(plan['isolated_transaction'],period)
            txn=local['latency_ns'];isolated_ns=isolated['latency_ns'];txn_interval=schedule.run(plan['local_transaction'],period,start_ns=local['end_ns'])['latency_ns']
        else:txn=p['sram_write_cycle'];isolated_ns=None;txn_interval=math.ceil(txn/period-1e-10)*period
        resolved={'input_config_sha256':sha(config_path),'logical':case['logical'],'physical':case['physical'],'resources':case['resources'],'native_parameters_ns':p,'backend':b,'adapter':plan['snapshot'],'source_provenance':case['provenance'],'schedule_policy':{'mode':'strict_serial_no_overlap','physical_services':'continuous time; only next declared consumer aligns','digital_consumer':'combinational evaluation starts at eligible edge and captures at cycle end; modeled setup and clock Q are in complete path','native_write_port':'128bit data only on lv_core edge; native complete cycle includes data setup/capture','SAR_retention':'hold existing codes until both scheduled reconstruction ticks complete','boundary_ready_setup':'explicit setup margin only for capture-only matrix publication','steady_interval_proof':'two consecutive vector/matrix schedules at same global phase; no overlap; admission follows completed publish'}}
        dump(work/'resolved.json',resolved)
        result={'contract_version':'3.0.0','case_id':cid,'status':'OK','mode':'neurosim_native_hybrid_pilot','identity':{'backend_sha':backend.SHA,'input_sha256':sha(config_path),'patches':['backend/constructor.patch'],'driver_sha256':sha(__file__)},'effective_config':{'resolved_snapshot':'resolved.json','resolved_sha256':sha(work/'resolved.json')},'derived_snapshot':{'actual_period_ns':period,'module_returns':b['raw_module_returns'],'module_inventory':b['module_inventory'],'partial_area_scope':b['partial_area_scope']},'clocks':[{'clock_id':'lv_core','target_period_ns':5.,'combinational_limit_ns':max(x['delay_ns'] for x in b['paths']),'actual_period_ns':period,'closure_status':'modeled_complete_paths_under_declared_topology','constraining_paths':b['paths']}],
            'stages':[{**x,'service_kind':kind} for kind,service in [('streaming',s),('resident',r)] for x in service['stages']],
            'streaming':{'latency_ns':s['latency_ns'],'delta_S_ns':s['latency_ns'],'initiation_interval_ns':again['latency_ns'],'proof':'strict serial vector schedule; all SAR/data resources retained until release; second vector simulated with same global phase'},
            'resident_load':{'transaction_latency_ns':txn,'transaction_service_interval_ns':txn_interval,'isolated_transaction_with_rail_ns':isolated_ns,'T_R_ns':r['latency_ns'],'matrix_service_interval_ns':again_r['latency_ns'],'payload_Byte':case['logical']['B_R_Byte'],'transaction_payload_Byte':16,'coverage_status':'complete_hybrid_conditional_native_services','normalized_missing_backend_write':{'value':None,'status':'NOT_IMPLEMENTED','reason':'locked V1.4 aggregate write disabled; no Training substitution'}},
            'maintenance':{'raw_stage_metrics':None,'effective_stage_metrics':None,'workload_write_Byte':0,'recompute_required':True},'derived_metrics':metric,'comparison':comparison,'checks':plan['checks']}
        schema_check(result,json.loads((own/'contracts/output.schema.json').read_text()));dump(work/'result.json',result)
        sens=[]
        def record(label,par,model,expect_s=None,expect_r=None):
            _,xs,xr=evaluate(par,model);row={'id':label,'actual_period_ns':model['actual_period_ns'],'delta_S_ns':xs['latency_ns'],'T_R_ns':xr['latency_ns']}
            if expect_s is not None:assert math.isclose(xs['latency_ns'],expect_s,rel_tol=1e-10)
            if expect_r is not None:assert math.isclose(xr['latency_ns'],expect_r,rel_tol=1e-10)
            sens.append(row)
        if b['sar_ns'] is not None:
            slower=copy.deepcopy(b);slower['sar_ns']+=8;record('independent_SAR_duration_plus8ns_same10bit_resources',p,slower,expect_r=r['latency_ns'])
        write=copy.deepcopy(p);key='reset_pulse' if cid=='05_rram' else 'sram_write_cycle';write[key]+=125 if cid=='05_rram' else 2
        record('native_write_only_perturbation',write,b,expect_s=s['latency_ns'])
        if cid=='05_rram':
            window=copy.deepcopy(p);window['binary_verify_sense_ns']+=5;record('independent_window_plus5ns',window,b,expect_s=s['latency_ns'])
        else:
            slow=copy.deepcopy(p);slow['charge_front' if cid=='01_sram_acim' else 'native_mac_cycle']+=7
            record('native_compute_only_plus7ns',slow,b,expect_r=r['latency_ns'])
        for wire in [5.,20.]:record('model_local_wire_%gum'%wire,p,execute('wire_%g'%wire,wire_um=wire))
        dump(work/'sensitivity.json',{'status':'PASS','scope':'few named one-factor diagnostics; SAR duration perturbation is synthetic service dependency test, not new physical ADC precision','rows':sens})
        rows.append({'case_id':cid,'K':case['logical']['K'],'N':case['logical']['N'],'actual_period_ns':period,'delta_S_ns':s['latency_ns'],'T_R_ns':r['latency_ns'],**{k:v for k,v in metric.items() if k!='status'},'v3_delta_S_ns':replay['raw_delta_S_ns'],'v3_T_R_ns':replay['raw_T_R_ns']})
        print(json.dumps({'case_id':cid,'status':'PASS','delta_S_ns':s['latency_ns'],'T_R_ns':r['latency_ns'],'actual_period_ns':period}),flush=True)
    dump(out/'summary.json',{'status':'PASS','mode':a.mode,'case_results':rows,'reproduction':'fresh source copies and executable per case; no cached binary','scope':'three reference pilots only; source native services are conditional inputs'})
    with (out/'summary.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
if __name__=='__main__':main()
