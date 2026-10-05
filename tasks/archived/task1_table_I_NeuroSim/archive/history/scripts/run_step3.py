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
def b_clock(b):return {k:b[k] for k in ['timing_min_period_ns','actual_period_ns','selection_policy']}

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--root',default=os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim')))
    ap.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX','g++-16'));ap.add_argument('--case',choices=['all',*CASE],default='all')
    ap.add_argument('--run-id',default='pilot-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    ap.add_argument('--revision',choices=['v1','v2'],default='v2');ap.add_argument('--period-ns',type=float);ap.add_argument('--wire-um',type=float,default=10.)
    ap.add_argument('--mode',choices=['pilot','replay'],default='pilot');ap.add_argument('--export',action='store_true');ap.add_argument('--no-export',action='store_true');ap.add_argument('--worker',help=argparse.SUPPRESS)
    a=ap.parse_args();own=Path(__file__).resolve().parents[1];root=Path(a.root).expanduser().resolve();root.mkdir(exist_ok=True)
    assert not any(x in str(root).lower() for x in ['onedrive','icloud','mobile documents'])
    assert Path(a.run_id).name==a.run_id and a.run_id not in ['.','..']
    cases=list(CASE) if a.case=='all' else [a.case]
    if not a.worker:
        repo=own.parents[1];out=root/('runs/step3-v2' if a.revision=='v2' else 'runs/step3-v1-replay')/a.run_id;out.mkdir(parents=True,exist_ok=False)
        snap=out/'snapshot';task=snap/'tasks/task1_table_I_NeuroSim';task.mkdir(parents=True)
        inputs=[]
        for directory in ['pilots','contracts']:
            for f in sorted((own/directory).rglob('*')):
                if f.is_file() and f.suffix in ['.py','.cpp','.h','.json','.md','.csv']:
                    dest=task/f.relative_to(own);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
        for rel in ['scripts/run_step3.py','scripts/check_step2.py','probes/interface_revision/legacy_replay.py','provenance/neurosim.lock.json']:
            f=own/rel;dest=task/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
        for cid in cases:
            f=own/'configs/cases'/f'{cid}.json';dest=task/f.relative_to(own);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
            for source in json.loads(f.read_text())['provenance']['sources'].values():
                if not isinstance(source,dict) or 'path' not in source:continue
                src=repo/source['path'];assert sha(src)==source['sha256'],src
                dest=snap/source['path'];dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dest);inputs.append(src)
        for cid in cases:
            for name in ['result.json','resolved.json','sensitivity.json']:
                f=own/'results/step3/integration-final-20261004'/cid/name
                dest=task/f.relative_to(own);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);inputs.append(f)
        manifest={str(f.relative_to(repo)):sha(f) for f in inputs}
        dump(out/'snapshot_manifest.json',manifest)
        initial={'head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip(),'status':subprocess.check_output(['git','status','--short'],cwd=repo,text=True),'mode':a.mode,'selected_cases':cases,'compiler':subprocess.check_output([a.cxx,'--version'],text=True).splitlines()[0],'python':sys.version,'baseline':'88448197c570b113f6002524aaacd1bd8865ca86','execution_revision':a.revision,'requested_period_ns':a.period_ns,'wire_um':a.wire_um,'device_baseline':'a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0'}
        dump(out/'invocation.json',initial)
        argv=[sys.executable,'-B',str(task/'scripts/run_step3.py'),'--root',str(root),'--cxx',a.cxx,'--case',a.case,'--run-id',a.run_id,'--mode',a.mode,'--worker',str(out),'--revision',a.revision,'--wire-um',str(a.wire_um)]
        if a.period_ns is not None:argv+=['--period-ns',str(a.period_ns)]
        completed=subprocess.run(argv,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT);(out/'run.log').write_text(completed.stdout)
        print(completed.stdout,end='')
        if completed.returncode:raise SystemExit(completed.returncode)
        if a.export and not a.no_export:
            export=own/('results/step3_v2' if a.revision=='v2' else 'results/step3_v1_replay')/a.run_id;export.mkdir(parents=True,exist_ok=False)
            whitelist=['summary.json','summary.csv','snapshot_manifest.json','invocation.json']
            for cid in cases:
                whitelist += [cid+'/result.json',cid+'/resolved.json',cid+'/sensitivity.json',cid+'/operating_points.json',cid+'/timing_checks.json',cid+'/backend/source_manifest.json',cid+'/backend/constructor.patch'] if a.mode=='pilot' else [cid+'/replay.json']
            for rel in whitelist:
                f=out/rel;assert f.stat().st_size<1_000_000,rel
                dest=export/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest)
            dump(export.parent/'latest.json',{'run_id':a.run_id,'mode':a.mode,'status':'PASS','summary':str((export/'summary.json').relative_to(own))})
        print(json.dumps({'run':str(out),'status':'PASS','mode':a.mode}));return
    out=Path(a.worker);repo=own.parents[1];sys.path.insert(0,str(own/'pilots'));sys.path.insert(0,str(own/'scripts'));sys.path.insert(0,str(own/'probes/interface_revision'))
    import backend,schedule,legacy_replay,timing,check_v2
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
        execute=backend.build(case,root,work/'backend',a.cxx,own/'pilots',revision=a.revision);b=execute('reference',wire_um=a.wire_um,operating_period_ns=a.period_ns)
        adapter=importlib.import_module('adapters.'+CASE[cid])
        def evaluate(par,model,align=True):
            plan=adapter.build(case,par,model);assert all(plan['checks'].values())
            if align:
                timing.select_period(model['paths'],model.get('reconstruction_window'),model['actual_period_ns'])
                timing.validate_plan(plan,model)
            return plan,schedule.run(plan['streaming'],model['actual_period_ns'],align=align),schedule.run(plan['resident'],model['actual_period_ns'],align=align)
        plan,s,r=evaluate(p,b);period=b['actual_period_ns']
        timing_checks=check_v2.run(case,plan,b) if a.revision=='v2' else {'status':'PASS','scope':'V1 single-cycle comparison, no V2 multicycle checks'}
        dump(work/'timing_checks.json',timing_checks)
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
        old=json.loads((own/'results/step3/integration-final-20261004'/cid/'result.json').read_text())
        comparison['V1']={'delta_S_ns':old['streaming']['delta_S_ns'],'T_R_ns':old['resident_load']['T_R_ns'],
            'source':'88448197:results/step3/integration-final-20261004/'+cid+'/result.json','usage':'comparison_only_after_new_aggregation'}
        comparison['V1_to_current_difference_ns']={'streaming':s['latency_ns']-old['streaming']['delta_S_ns'],'resident':r['latency_ns']-old['resident_load']['T_R_ns']}
        if 'local_transaction' in plan:
            local=schedule.run(plan['local_transaction'],period);isolated=schedule.run(plan['isolated_transaction'],period)
            txn=local['latency_ns'];isolated_ns=isolated['latency_ns'];txn_interval=schedule.run(plan['local_transaction'],period,start_ns=local['end_ns'])['latency_ns']
        else:txn=p['sram_write_cycle'];isolated_ns=None;txn_interval=math.ceil(txn/period-1e-10)*period
        resolved={'execution_extension':json.loads((own/'contracts/step3_timing_extension.json').read_text()) if a.revision=='v2' else {'applicable':False,'mode':'V1 conservative single-cycle rebuild; frozen original source retained'},'input_config_sha256':sha(config_path),'logical':case['logical'],'physical':case['physical'],'resources':case['resources'],'native_parameters_ns':p,'backend':b,'adapter':plan['snapshot'],'source_provenance':case['provenance'],'schedule_policy':{'mode':'strict_serial_no_overlap','physical_services':'continuous time; only next declared consumer aligns','execution_extension':'2.0.0' if a.revision=='v2' else 'V1 single-cycle timing' ,'digital_consumer':('ordinary operations capture after1cycle; held reconstruction propagates continuously E0toE2; only phase changes atE1; capture-enable path remains1cycle' if a.revision=='v2' else 'V1 two scheduled ticks with conservative full single-cycle path qualification; no V2 multicycle timing exception'),'native_write_port':'128bit data only on lv_core edge; native complete cycle includes data setup/capture','SAR_retention':'hold existing codes until both scheduled reconstruction ticks complete','boundary_ready_setup':'explicit setup margin only for capture-only matrix publication','steady_interval_proof':'two consecutive vector/matrix schedules at same global phase; no overlap; admission follows completed publish'}}
        dump(work/'resolved.json',resolved)
        result={'contract_version':'3.0.0','case_id':cid,'status':'OK','mode':'neurosim_native_hybrid_pilot','execution_revision':a.revision,'identity':{'backend_sha':backend.SHA,'input_sha256':sha(config_path),'patches':['backend/constructor.patch'],'driver_sha256':sha(__file__)},'effective_config':{'resolved_snapshot':'resolved.json','resolved_sha256':sha(work/'resolved.json')},'derived_snapshot':{'actual_period_ns':period,'module_returns':b['raw_module_returns'],'module_inventory':b['module_inventory'],'partial_area_scope':b['partial_area_scope']},'clocks':[{'clock_id':'lv_core','target_period_ns':5.,'combinational_limit_ns':max(x['delay_ns'] for x in b['paths']),'timing_min_period_ns':b['timing_min_period_ns'],'policy_min_period_ns':b['policy_min_period_ns'],'selection_policy':b['selection_policy'],'actual_period_ns':period,'closure_status':'modeled_complete_paths_under_declared_topology','constraining_paths':b['paths']}],
            'stages':[{**x,'service_kind':kind} for kind,service in [('streaming',s),('resident',r)] for x in service['stages']],
            'streaming':{'latency_ns':s['latency_ns'],'delta_S_ns':s['latency_ns'],'initiation_interval_ns':again['latency_ns'],'proof':'strict serial vector schedule; all SAR/data resources retained until release; second vector simulated with same global phase'},
            'resident_load':{'transaction_latency_ns':txn,'transaction_service_interval_ns':txn_interval,'isolated_transaction_with_rail_ns':isolated_ns,'T_R_ns':r['latency_ns'],'matrix_service_interval_ns':again_r['latency_ns'],'payload_Byte':case['logical']['B_R_Byte'],'transaction_payload_Byte':16,'coverage_status':'complete_hybrid_conditional_native_services','normalized_missing_backend_write':{'value':None,'status':'NOT_IMPLEMENTED','reason':'locked V1.4 aggregate write disabled; no Training substitution'}},
            'maintenance':{'raw_stage_metrics':None,'effective_stage_metrics':None,'workload_write_Byte':0,'recompute_required':True},'derived_metrics':metric,'comparison':comparison,'checks':plan['checks']}
        schema_check(result,json.loads((own/'contracts/output.schema.json').read_text()));dump(work/'result.json',result)
        sens=[];points=[]
        def record(label,par,model,expect_s=None,expect_r=None):
            _,xs,xr=evaluate(par,model);row={'id':label,'timing_min_period_ns':model['timing_min_period_ns'],'actual_period_ns':model['actual_period_ns'],'selection_policy':model['selection_policy'],'delta_S_ns':xs['latency_ns'],'T_R_ns':xr['latency_ns'],**schedule.metrics(case,xs,xr)}
            for events,computed in [(adapter.build(case,par,model)['streaming'],xs),(adapter.build(case,par,model)['resident'],xr)]:
                second=schedule.run(events,model['actual_period_ns'],start_ns=computed['end_ns'])
                assert math.isclose(second['latency_ns'],computed['latency_ns'],rel_tol=1e-10)
            if expect_s is not None:assert math.isclose(xs['latency_ns'],expect_s,rel_tol=1e-10)
            if expect_r is not None:assert math.isclose(xr['latency_ns'],expect_r,rel_tol=1e-10)
            sens.append(row);return row
        if b['sar_ns'] is not None:
            slower=copy.deepcopy(b);slower['sar_ns']+=8;record('independent_SAR_duration_plus8ns_same10bit_resources',p,slower,expect_r=r['latency_ns'])
        write=copy.deepcopy(p);key='reset_pulse' if cid=='05_rram' else 'sram_write_cycle';write[key]+=125 if cid=='05_rram' else 2
        record('native_write_only_perturbation',write,b,expect_s=s['latency_ns'])
        if cid=='05_rram':
            window=copy.deepcopy(p);window['binary_verify_sense_ns']+=5;record('independent_window_plus5ns',window,b,expect_s=s['latency_ns'])
        else:
            slow=copy.deepcopy(p);slow['charge_front' if cid=='01_sram_acim' else 'native_mac_cycle']+=7
            record('native_compute_only_plus7ns',slow,b,expect_r=r['latency_ns'])
        points.append({'id':'main',**b_clock(b),'delta_S_ns':s['latency_ns'],'T_R_ns':r['latency_ns'],**metric})
        alternatives=sorted(set([math.ceil(period*4-1e-9)/4+.25,math.ceil(period*2-1e-9)/2+.5]))
        for chosen in alternatives:
            label='fixed_period_%g_ns'%chosen;model=execute(label,wire_um=a.wire_um,operating_period_ns=chosen)
            points.append(record(label,p,model))
        for wire in [5.,20.]:
            model=execute('wire_%g_floor'%wire,wire_um=wire,policy='timing_floor');record('wire_%g_timing_floor_policy'%wire,p,model)
            if period+1e-10>=model['policy_min_period_ns']:
                model=execute('wire_%g_same_clock'%wire,wire_um=wire,operating_period_ns=period)
                record('wire_%g_same_main_clock'%wire,p,model)
            else:sens.append({'id':'wire_%g_same_main_clock'%wire,'status':'REJECTED_ILLEGAL_PERIOD','timing_min_period_ns':model['timing_min_period_ns'],'requested_period_ns':period})
        dump(work/'operating_points.json',{'status':'PASS','policy':('main keeps nominal5ns if legal, otherwise rounds up to0.5ns; alternatives are named whole-device points, no mixed rho/tau optima' if a.revision=='v2' else 'V1 main exact max(5ns,full single-cycle paths), unless explicit legal override; no V2 multicycle exception'),'points':points})
        dump(work/'sensitivity.json',{'status':'PASS','scope':'few named one-factor diagnostics; SAR duration perturbation is synthetic service dependency test, not new physical ADC precision','rows':sens})
        rows.append({'case_id':cid,'timing_min_period_ns':b['timing_min_period_ns'],'operating_policy':b['selection_policy'],'K':case['logical']['K'],'N':case['logical']['N'],'actual_period_ns':period,'delta_S_ns':s['latency_ns'],'T_R_ns':r['latency_ns'],**{k:v for k,v in metric.items() if k!='status'},'v3_delta_S_ns':replay['raw_delta_S_ns'],'v3_T_R_ns':replay['raw_T_R_ns']})
        print(json.dumps({'case_id':cid,'status':'PASS','timing_min_period_ns':b['timing_min_period_ns'],'delta_S_ns':s['latency_ns'],'T_R_ns':r['latency_ns'],'actual_period_ns':period}),flush=True)
    dump(out/'summary.json',{'status':'PASS','mode':a.mode,'case_results':rows,'reproduction':'fresh source copies and executable per case; no cached binary','scope':'three reference pilots only; source native services are conditional inputs','execution_revision':a.revision})
    with (out/'summary.csv').open('w') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
if __name__=='__main__':main()
