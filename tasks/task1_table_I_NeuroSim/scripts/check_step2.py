#!/usr/bin/env python3
"""Single Step 2 entry: immutable local snapshot, contracts, original C++ probes.

Only --export writes the small, explicit management artifact whitelist.
No package installation, Git mutation, v3 emit, or formal case performance run.
"""
import argparse
from collections import Counter
import csv
import datetime
import hashlib
import io
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
import traceback

sys.dont_write_bytecode = True
BASELINE = 'a5cf78bd1be755da8171a8b2d6189c4e7d80b6f0'
ROLES = ('read_timing', 'write_update', 'special', 'encoding_resources', 'interface_revision')
EXPECTED = {'01_sram_acim': (128,128), '02_sram_dcim': (128,16),
 '03_nor_2d': (128,128), '04_nand_3d': (4608,240), '05_rram': (128,64),
 '06_mram': (256,32), '07_pcm': (256,128), '08_feram_hfo2': (128,128),
 '09_gain_cell_edram': (64,64), '10_fenor_3d': (128,128)}

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False)+'\n')

def pointer(value, ref):
    assert ref == '' or ref.startswith('/'), ref
    for part in ref.split('/')[1:]:
        part = part.replace('~1','/').replace('~0','~')
        value = value[int(part)] if isinstance(value,list) else value[part]
    return value

def schema_check(value, spec, where='$'):
    """Validate the JSON Schema subset used by the two checked-in schemas."""
    if 'const' in spec: assert value == spec['const'], (where,'const',value)
    if 'enum' in spec: assert value in spec['enum'], (where,'enum',value)
    types = spec.get('type', [])
    if isinstance(types,str): types = [types]
    matches = {'object': isinstance(value,dict), 'array': isinstance(value,list),
        'string':isinstance(value,str), 'number': isinstance(value,(int,float)) and not isinstance(value,bool),
        'integer':isinstance(value,int) and not isinstance(value,bool),
        'boolean': isinstance(value,bool), 'null': value is None}
    if types: assert any(matches[t] for t in types), (where,types,type(value).__name__)
    if isinstance(value,(int,float)) and not isinstance(value,bool):
        assert math.isfinite(value), (where,'non-finite')
        if 'minimum' in spec: assert value >= spec['minimum'], (where,'minimum')
    if isinstance(value,dict):
        assert set(spec.get('required',[])) <= set(value), (where,'required',set(spec.get('required',[]))-set(value))
        for k,s in spec.get('properties',{}).items():
            if k in value: schema_check(value[k],s,where+'/'+k)
    if isinstance(value,list) and 'items' in spec:
        for i,x in enumerate(value): schema_check(x,spec['items'],where+'/'+str(i))

def objects(value):
    if isinstance(value,dict):
        yield value
        for x in value.values(): yield from objects(x)
    elif isinstance(value,list):
        for x in value: yield from objects(x)

def normalize_time(raw, clocks):
    """Single typed conversion usable by the forthcoming pilot driver wrapper."""
    assert raw.get('normalized') is not True and 'normalized_ns' not in raw and raw.get('conversion_count',0)==0, 'Time already normalized'
    if raw['status'] != 'OK':
        assert raw['value'] is None and raw.get('reason'), 'Missing is not zero'
        return None
    value=raw['value']; assert isinstance(value,(int,float)) and math.isfinite(value) and value>=0
    if raw['unit']=='cycles':
        assert raw.get('clock_id') in clocks, 'Cycles require a known clock_id'
        period=clocks[raw['clock_id']]['actual_period_ns']
        assert period is not None and period>0, 'Actual clock must be resolved'
        return value*period
    assert raw.get('clock_id') is None, 'Physical seconds are not cycles'
    if raw['unit']=='s': return value*1e9
    if raw['unit']=='ns': return value
    raise AssertionError('Not a time return: '+raw['unit'])

def output_contract_tests(management):
    clocks={'lv_core':{'actual_period_ns':100}}
    checks={}
    checks['slow_clock_four_cycles_400ns']=normalize_time({'status':'OK','value':4,'unit':'cycles','clock_id':'lv_core'},clocks)==400
    checks['physical_seconds_once']=math.isclose(normalize_time({'status':'OK','value':11e-9,'unit':'s','clock_id':None},clocks),11)
    checks['missing_write_is_null']=normalize_time({'status':'NOT_IMPLEMENTED','value':None,'unit':'s','clock_id':None,'reason':'V1.4 aggregate write code inactive'},clocks) is None
    for name,raw in {
      'reject_zero_missing':{'status':'NOT_IMPLEMENTED','value':0,'unit':'s','reason':'inactive'},
      'reject_cycles_without_clock':{'status':'OK','value':2,'unit':'cycles','clock_id':None},
      'reject_seconds_as_cycles':{'status':'OK','value':1e-9,'unit':'s','clock_id':'lv_core'},
      'reject_repeated_conversion':{'status':'OK','value':2,'unit':'ns','clock_id':None,'normalized':True},
      'reject_nonfinite':{'status':'OK','value':float('nan'),'unit':'s','clock_id':None}}.items():
        try: normalize_time(raw,clocks)
        except (AssertionError,KeyError): checks[name]=True
        else: checks[name]=False
    schema=json.loads((management/'contracts/output.schema.json').read_text())
    example={'contract_version':'3.0.0','case_id':'synthetic_contract_check','status':'NOT_IMPLEMENTED',
      'identity':{'backend_sha':'8a88abf85844c0e1ba17cc771ea535fff6040456','input_sha256':'0'*64,'patches':[],'driver_sha256':'0'*64},
      'effective_config':{},'derived_snapshot':{},'clocks':[], 'stages':[],
      'resident_load':{'transaction_latency_ns':None,'T_R_ns':None,'payload_Byte':0,'coverage_status':'NOT_IMPLEMENTED'},
      'maintenance':{'raw_stage_metrics':None,'effective_stage_metrics':None,'workload_write_Byte':0,'recompute_required':True},
      'derived_metrics':{'rho_Byte_per_s':None,'tau_Byte_per_s':None,'RI_star':None,'U_star':None,'status':'NOT_EVALUATED'}}
    schema_check(example,schema);checks['output_schema_accepts_explicit_missing']=True
    assert all(checks.values()),checks
    return {'status':'PASS','checks':checks,'formal_case_output_generated':False}

def validate_cases(management, repo):
    schema = json.loads((management/'contracts/case.schema.json').read_text())
    cases = [json.loads(p.read_text()) for p in sorted((management/'configs/cases').glob('*.json'))]
    assert {x['case_id'] for x in cases} == set(EXPECTED), 'ten exact case IDs required'
    checked_sources, details, source_cache = {}, [], {}
    for case in cases:
        schema_check(case,schema)
        cid = case['case_id']; l = case['logical']; phys=case['physical']
        assert (l['K'],l['N']) == EXPECTED[cid], cid
        assert l['input_bits']==l['weight_bits']==8 and l['bytes_per_input']==l['bytes_per_weight']==1, cid
        assert l['B_S_Byte']==l['K'] and l['B_R_Byte']==l['K']*l['N'], cid
        assert l['output_bits'] >= 16+math.ceil(math.log2(l['K'])), cid
        assert phys['effective_capacity_Byte']==l['B_R_Byte'], cid
        assert case['periphery']['clock']['actual_period_ns'] is None, 'Step 2 not evaluated'
        assert not any(k in case for k in ['rho','tau','T_R','RI_star','performance']), cid
        sources = case['provenance']['sources']; ref_count=0
        for sid,source in sources.items():
            if not isinstance(source,dict) or 'path' not in source: continue
            path = repo/source['path']; path.resolve().relative_to(repo.resolve())
            assert path.is_file() and sha(path)==source['sha256'], (cid,sid,'source hash')
            if 'baseline_sha' in source:
                assert source['baseline_sha']==BASELINE
                cachekey=(source['path'],BASELINE)
                if cachekey not in source_cache:
                    blob=subprocess.check_output(['git','show',BASELINE+':'+source['path']],cwd=repo)
                    source_cache[cachekey]=hashlib.sha256(blob).hexdigest()
                assert source_cache[cachekey]==source['sha256'], (cid,sid,'baseline drift')
            checked_sources[source['path']]=source['sha256']
        for ref in objects(case):
            if 'source_id' in ref and ('json_pointer' in ref or 'function' in ref):
                src=sources[ref['source_id']]; path=repo/src['path']
                if 'json_pointer' in ref: pointer(json.loads(path.read_text()),ref['json_pointer'])
                if 'function' in ref:
                    assert ('def '+ref['function']+'(') in path.read_text() or ref['function'] in path.read_text(), (cid,ref)
                ref_count+=1
        stages=case['services']; ids={s['id'] for s in stages}
        assert len(ids)==len(stages) and stages, cid
        completed=set()
        for _ in stages:
            for s in stages:
                assert set(s['depends_on'])<=ids, (cid,s['id'],'unknown dependency')
                if set(s['depends_on'])<=completed: completed.add(s['id'])
        assert completed==ids, (cid,'cycle')
        for s in stages:
            count=s['count']
            if 'value' in count: assert isinstance(count['value'],(int,float)) and count['value']>=0, (cid,s['id'])
            assert s['call']['entrypoint'] and s['call']['inputs'] and s['call']['outputs'], (cid,s['id'],'empty call')
            assert not s['overlap']['allowed'] or s['overlap'].get('reason'), (cid,s['id'],'unproven overlap')
            for returned in s['call']['outputs']:
                if not isinstance(returned,dict): continue
                if returned.get('unit') in ['s','ns']:
                    assert returned.get('clock_id') is None, (cid,s['id'],'physical time must not carry conversion clock_id')
                elif returned.get('unit')=='cycles':
                    assert returned.get('clock_id')==case['periphery']['clock']['clock_id'], (cid,s['id'],'cycle clock not bound')
        for binding in case['parameter_bindings']:
            assert set(binding.get('consumers',[]))<=ids, (cid,binding['id'],'unknown consumer')
        if cid=='06_mram':
            direction=next(s for s in stages if s['id']=='direction_write')
            assert direction['provider']=='v3_native_service', 'MRAM complete direction slot is opaque'
            assert 'digital_tick' not in direction['call']['inputs'], 'MRAM turn/verify already own control ticks'
            tick=next(b for b in case['parameter_bindings'] if b['id']=='digital_tick')
            assert 'direction_write' not in tick['consumers']
            assert {'polarity_turn','terminal_verify'}<=set(tick['consumers'])
        def expand(nodes,multiplier=1):
            totals=Counter()
            for node in nodes:
                if 'stage_id' in node:
                    assert node['stage_id'] in ids and isinstance(node['count'],int) and node['count']>=0
                    totals[node['stage_id']]+=multiplier*node['count']
                else:
                    assert isinstance(node['repeat'],int) and node['repeat']>0 and node.get('axis')
                    totals.update(expand(node['steps'],multiplier*node['repeat']))
            return totals
        scheduled=Counter()
        for kind in ['streaming','resident','maintenance']:
            section=case['service_schedules'][kind]
            scheduled.update(expand(section['steps']))
        assert dict(scheduled)=={s['id']:s['count']['value'] for s in stages}, (cid,'schedule count mismatch',dict(scheduled))
        inst=case['resources']['installed']
        assert inst['input_register_bits']>=l['K']*8 and inst['output_register_bits']>=l['N']*l['output_bits'], cid
        assert inst['external_update_domains']==1, cid
        if cid in ['02_sram_dcim','03_nor_2d','06_mram','08_feram_hfo2','10_fenor_3d']:
            assert inst['adc_count']==0, (cid,'unexpected ADC')
        details.append({'case_id':cid,'status':'PASS','K':l['K'],'N':l['N'],
            'B_S_Byte':l['B_S_Byte'],'B_R_Byte':l['B_R_Byte'],
            'stage_count':len(stages),'resolved_source_refs':ref_count})
    # Independent counting identity, no ten-case timing estimates.
    B_S,B_R,ds,tr=7,35,13,91
    rho,tau=B_S/ds,B_R/tr
    assert math.isclose(tr/ds,5*(rho/tau))
    return cases, {'status':'PASS','cases':details,'source_hashes':checked_sources,
                   'identity_test':'synthetic B_S=7, B_R=35, ds=13, tr=91; U*=N*RI*',
                   'new_ten_case_performance':'NOT_RUN'}

def render(cases):
    text=io.StringIO(); writer=csv.writer(text,lineterminator='\n')
    writer.writerow(['case_id','K','N','stage_id','service_kind','provider','coverage_kind','dominant_timing_provider','case_path_status','entrypoint','count','included_stages','source_refs'])
    md=['| 案例 | 逻辑 K×N | 原生模块入口（非案例闭合） | 混合/候选阶段 | 保留原生完整服务 |','|---|---:|---|---|---|']
    for c in cases:
        native=[]; mixed=[]; kept=[]
        for s in c['services']:
            cv=s['coverage']
            writer.writerow([c['case_id'],c['logical']['K'],c['logical']['N'],s['id'],s['service_kind'],s['provider'],cv['kind'],cv['dominant_timing_provider'],cv['case_path_status'],s['call']['entrypoint'],json.dumps(s['count'],ensure_ascii=False),'; '.join(s['included_stages']),json.dumps(s['source_refs'],ensure_ascii=False)])
            bucket=kept if cv['kind']=='native_service' else mixed if cv['kind']=='hybrid_stage' else native
            bucket.append(s['id']+('〔原算术预算〕' if s['id'] in ['affine_merge_sign','load_calibration'] else ''))
        md.append('| '+c['case_id']+' | '+str(c['logical']['K'])+'×'+str(c['logical']['N'])+' | '+', '.join(native)+' | '+', '.join(mixed)+' | '+', '.join(kept)+' |')
    return text.getvalue(),'\n'.join(md)+'\n'

def source_map(management,cases):
    return {'contract_version':'3.0.0','device_baseline_sha':BASELINE,
      'upstream_lock':'neurosim.lock.json',
      'probe_maps':{role:json.loads((management/'probes'/role/'source_map.json').read_text()) for role in ROLES},
      'case_inputs':{c['case_id']:c['provenance'] for c in cases}}

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--root',default=os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim')))
    ap.add_argument('--run-id',default=os.environ.get('NEUROSIM_RUN_ID'))
    ap.add_argument('--cxx',default=os.environ.get('NEUROSIM_CXX'))
    ap.add_argument('--validate-only',action='store_true')
    ap.add_argument('--export',action='store_true')
    ap.add_argument('--no-export',action='store_true')
    a=ap.parse_args(); assert not(a.export and a.no_export)
    management=Path(__file__).resolve().parents[1];repo=management.parent.parent
    root=Path(a.root).expanduser().resolve()
    assert root.is_dir() and (root/'worktrees.json').is_file(), 'Reuse Step 1 local root'
    assert not any(t in str(root).lower() for t in ['onedrive','icloud','cloudstorage','mobile documents']), 'Cloud/symlink runtime root rejected'
    assert not root.is_relative_to(repo), 'Runtime root must be outside repository'
    runid=a.run_id or 'step2-'+datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'-'+str(os.getpid())
    assert runid and Path(runid).name==runid and runid not in ['.','..']
    out=root/'runs/step2'/runid;out.mkdir(parents=True,exist_ok=False)
    snapshot=out/'snapshot';snapshot.mkdir()
    command_log=[]
    try:
        hashes={}
        selected=[]
        for base in ['probes','configs/cases','contracts']:
            selected.extend(p for p in (management/base).rglob('*') if p.is_file() and p.suffix in ['.py','.cpp','.h','.json','.md'])
        selected.append(Path(__file__).resolve())
        for f in selected:
            assert not f.is_symlink(); rel=f.relative_to(management);dest=snapshot/rel
            dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);hashes[str(rel)]=sha(dest)
        write_json(out/'snapshot_hashes.json',hashes)
        lock=json.loads((management/'provenance/neurosim.lock.json').read_text())
        ws=json.loads((root/'worktrees.json').read_text()); worktrees={}
        for b in lock['snapshots']:
            path=Path(ws[b['branch']]).resolve();path.relative_to(root)
            head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()
            status=subprocess.check_output(['git','status','--porcelain=v1'],cwd=path,text=True).strip()
            assert head==b['locked_sha'] and not status, (b['branch'],'source drift')
            worktrees[b['branch']]={'sha':head,'clean':True}
        cases,validation=validate_cases(snapshot,repo)
        write_json(out/'configuration_checks.json',validation)
        write_json(out/'output_contract_checks.json',output_contract_tests(snapshot))
        coverage,md=render(cases);(out/'coverage.csv').write_text(coverage);(out/'coverage.md').write_text(md)
        if (management/'contracts/coverage.csv').exists():
            assert (management/'contracts/coverage.csv').read_text()==coverage or a.export, 'Stale generated coverage; regenerate explicitly with --export'
        provenance=source_map(snapshot,cases)
        write_json(out/'step2_source_map.json',provenance)
        cxx=a.cxx or json.loads((management/'provenance/environment.json').read_text())['tools']['cxx']['path']
        tmp=out/'tmp';tmp.mkdir()
        env=dict(os.environ,TMPDIR=str(tmp),PYTHONDONTWRITEBYTECODE='1',NEUROSIM_REPO_ROOT=str(repo),NEUROSIM_MANAGEMENT=str(management))
        summaries={}
        if not a.validate_only:
            for role in ROLES:
                cmd=[sys.executable,str(snapshot/'probes'/role/'run.py'),'--root',str(root),'--out',str(out/role),'--cxx',cxx]
                with (out/(role+'.runner.log')).open('w') as log:
                    proc=subprocess.run(cmd,cwd=out,env=env,stdout=log,stderr=subprocess.STDOUT)
                command_log.append({'role':role,'argv':cmd,'cwd':str(out),'exit_code':proc.returncode,'log':role+'.runner.log'})
                write_json(out/'commands.json',command_log)
                assert proc.returncode==0,(role,'runner failed')
                summaries[role]=json.loads((out/role/'summary.json').read_text())
                assert summaries[role]['status']=='PASS',(role,'assertions failed')
        # Scope and archival checks after native runs.
        for branch,record in worktrees.items():
            path=Path(ws[branch])
            assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=path,text=True).strip()==record['sha']
            assert not subprocess.check_output(['git','status','--porcelain=v1'],cwd=path,text=True).strip(), (branch,'probe changed upstream')
        initial=json.loads((management/'provenance/step2_repository.initial.json').read_text())
        preserved={name:sha(management/name)==digest for name,digest in initial['initial_management_hashes'].items() if name not in initial['allowed_modified_existing']}
        assert all(preserved.values()),'Archived Step 1 artifact changed'
        revision=json.loads((management/'provenance/step2_revision.initial.json').read_text())
        protected={name:digest for name,digest in revision['initial_hashes'].items()
                   if (name.startswith('results/') and name!='results/step2/latest.json')
                   or name in ['reports/step2_review.json','provenance/step2_delivery.json']}
        assert all(sha(management/name)==digest for name,digest in protected.items()),'Prior Step 2 evidence changed'
        status=subprocess.check_output(['git','diff','--name-only'],cwd=repo,text=True).splitlines()
        assert all(p.startswith('tasks/task1_table_I_NeuroSim/') or p=='.DS_Store' for p in status),status
        assert not subprocess.check_output(['git','diff','--cached','--name-only'],cwd=repo,text=True).strip()
        for f in management.rglob('*'):
            assert not f.is_symlink(),('management symlink',str(f))
            if f.is_dir(): assert f.name not in ['.git','__pycache__','node_modules'],str(f)
            elif f.is_file():
                assert f.suffix not in ['.o','.so','.dylib','.a','.pyc','.zip','.gz'],str(f)
                assert b'\x00' not in f.read_bytes(),('unexpected binary',str(f))
        summary={'contract_version':'3.0.0','status':'PASS','run_id':runid,
          'configuration_status':'PASS','probes_status':'NOT_RUN' if a.validate_only else 'PASS',
          'probe_statuses':{role:s['status'] for role,s in summaries.items()},
          'worktrees':worktrees,'step1_archives_unchanged':all(preserved.values()),
          'prior_step2_results_unchanged':True,'revision_base':revision['review_base'],
          'root_ds_store_matches_initial':sha(repo/'.DS_Store')==initial['root_ds_store_sha256'],
          'root_ds_store_sha256':sha(repo/'.DS_Store'),'git_index_empty':True,
          'case_count':len(cases),'new_ten_case_performance':'NOT_RUN','compiler':cxx}
        write_json(out/'summary.json',summary)
        if a.export:
            assert not a.validate_only,'Export requires all probes'
            dst=management/'results/step2'/runid;dst.mkdir(parents=True,exist_ok=False)
            for name in ['summary.json','configuration_checks.json','output_contract_checks.json','snapshot_hashes.json','commands.json','coverage.csv','coverage.md']:
                shutil.copyfile(out/name,dst/name)
            for role in ROLES:
                sub=dst/role;sub.mkdir()
                for name in ['summary.json','commands.json','assertions.json','raw-output.json','manifest.json','source_hashes.json','clock_dependency.json','digital_resources.json','addertree_model.json','legacy_replay.json']:
                    f=out/role/name
                    if f.is_file():
                        assert f.stat().st_size<262144
                        shutil.copyfile(f,sub/name)
            write_json(management/'results/step2/latest.json',{'run_id':runid,'status':'PASS'})
            shutil.copyfile(out/'step2_source_map.json',management/'provenance/step2_source_map.json')
            (management/'contracts/coverage.csv').write_text(coverage)
        print('PASS Step 2',runid,'cases='+str(len(cases)),'probes='+summary['probes_status'],out)
        return 0
    except Exception as exc:
        write_json(out/'failure.json',{'status':'FAIL','error':str(exc),'traceback':traceback.format_exc()})
        print('FAIL Step 2',runid,str(exc),'local evidence:',out,file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
