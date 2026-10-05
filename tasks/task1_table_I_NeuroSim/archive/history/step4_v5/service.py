"""V5 API v1: explicit serial services assembled from native and compact stages.
No legacy result import or device-specific physical constants live here.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True

KINDS=('native_circuit','adapter','external_primitive','service_policy')
def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def stage_total(stages, sources):
    if not isinstance(stages,list) or not stages:raise ValueError('Empty service stage list')
    total=0.;seen=set()
    for stage in stages:
        for key in ('id','duration_s','count','source_class','source_ids','resources','includes','excludes'):
            if key not in stage:raise ValueError('Missing stage field '+key)
        if stage['id'] in seen:raise ValueError('Duplicate stage ID in service')
        seen.add(stage['id'])
        duration=stage['duration_s'];count=stage['count']
        if isinstance(duration,bool) or not isinstance(duration,(int,float)) or not math.isfinite(duration) or duration<0:raise ValueError('Invalid stage duration')
        if isinstance(count,bool) or not isinstance(count,int) or count<=0:raise ValueError('Invalid stage multiplicity')
        if stage['source_class'] not in KINDS or not stage['source_ids'] or set(stage['source_ids'])-set(sources):raise ValueError('Invalid stage provenance')
        if not stage['resources'] or not stage['includes'] or not stage['excludes']:raise ValueError('Missing stage resource/coverage explanation')
        if duration==0 and not stage.get('zero_reason'):raise ValueError('Zero stage requires explanation')
        if stage['source_class']=='native_circuit':
            if stage.get('native_return_unit') not in ('seconds','cycles'):raise ValueError('Native stage unit missing')
            if 'included_internal_clock_phases' not in stage:raise ValueError('Native included clock phases missing')
            if stage['native_return_unit']=='cycles' and (not stage.get('conversion_clock_id') or stage.get('conversion_clock_Hz',0)<=0):raise ValueError('Native cycle conversion missing')
        total+=duration*count
    return total

def aggregate(resolved, model):
    source=resolved['input'];logical=source['logical'];status=model['status']
    if status not in ('valid','conditional','infeasible','blocked'):raise ValueError('Unknown case status')
    checks=model['physical_checks']
    if not isinstance(checks,list) or not checks:raise ValueError('Case requires explicit physical checks')
    for c in checks:
        if not isinstance(c.get('passed'),bool) or not c.get('id') or not c.get('evidence'):raise ValueError('Malformed physical check')
    failed=[x['id'] for x in checks if x.get('critical',True) and not x['passed']]
    if failed:status='infeasible'
    if model.get('program_outcome')=='failed':status='infeasible'
    if status in ('valid','conditional') and model.get('program_outcome')!='success':raise ValueError('Successful resident endpoint not established')
    if status=='conditional' and not model.get('conditions'):raise ValueError('Conditional result needs conditions')
    stream=stage_total(model['stream_stages'],source['sources']) if model.get('stream_stages') else None
    resident=stage_total(model['resident_stages'],source['sources']) if model.get('resident_stages') else None
    result={'case_id':source['case_id'],'implementation_id':source['implementation_id'],
            'config_id':resolved['config_id'],'scenario':resolved['scenario'],'status':status,
            'qualification':model['qualification'],'conditions':model.get('conditions',[]),
            'critical_failures':failed,'review_state':'not_reviewed','K':logical['K'],'N':logical['N'],
            'logical':logical,'identity':source['identity'],'resources':model['resources'],
            'range_meaning':source['scenarios'][resolved['scenario']]['meaning'],
            'single_latency_s':stream,'delta_S_raw_s':stream,'resident_s':resident,
            'B_S_Byte':logical['K']*logical['bytes_per_input'],
            'B_R_Byte':logical['K']*logical['N']*logical['bytes_per_weight'],
            'maintenance_basis':'none declared for this nonvolatile serial service',
            'formal_eligibility':False}
    if status in ('valid','conditional'):
        if stream is None or resident is None or min(stream,resident)<=0:raise ValueError('Incomplete positive service')
        if model.get('scheduling')!='serial_nonoverlap':raise ValueError('API v1 only implements explicit serial nonoverlap')
        rho=result['B_S_Byte']/stream;tau=result['B_R_Byte']/resident
        result.update(rho_MB_per_s=rho/1e6,tau_MB_per_s=tau/1e6,RI_star=rho/tau,U_star=resident/stream)
        assert math.isclose(result['U_star'],logical['N']*logical['bytes_per_weight']/logical['bytes_per_input']*result['RI_star'],rel_tol=1e-12)
    return result

def run_case(args, own, resolve_input):
    root=args.root.expanduser().absolute();out=root/'runs/step4-v5/p1'/('case-'+args.case+'-'+args.run_id)
    for path in (out,*out.parents):
        if path.is_symlink():raise ValueError('Symlink in runtime path '+str(path))
    root=root.resolve();out=out.resolve()
    if root not in out.parents or any(token in str(out) for token in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):raise ValueError('Runtime must be outside synchronized storage')
    case_dir=own/'cases'/args.case
    resolved=resolve_input(case_dir/'inputs.json',args.scenario)
    out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();canonical=out/'canonical';canonical.mkdir()
    # Small exact source package, with no history/results. Do not snapshot arbitrary case directories.
    files=[own/'run.py',own/'service.py',own/'native_probe.py',own/'functional_probe.py',own/'INTERFACE.md',own/'PROBE_API.md',
           own/'provenance/dependencies.lock.json',own/'src/native_binary_probe.cpp',
           own/'patches/mlp_binary_column_load.patch',own/'patches/mlp_decoder_consistency.patch',own/'patches/mlp_single_row_mux_and_write_target.patch',case_dir/'inputs.json',case_dir/'case_adapter.py']
    adapter_files=json.loads((case_dir/'inputs.json').read_text()).get('adapter_files',[])
    for name in adapter_files:
        rel=Path(name)
        if rel.is_absolute() or '..' in rel.parts or rel.suffix not in ('.py','.json','.csv','.txt'):raise ValueError('Unsafe adapter support path')
        files.append(case_dir/rel)
    hashes={}
    for f in files:
        if f.is_symlink() or f.stat().st_size>1024*1024:raise ValueError('Invalid canonical source '+str(f))
        rel=f.relative_to(own);target=canonical/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);hashes[str(rel)]=digest(f)
    computational={name:value for name,value in hashes.items() if Path(name).suffix in ('.py','.cpp','.h','.patch','.json','.csv')}
    dump(out/'snapshot_manifest.json',hashes);dump(out/'computational_manifest.json',computational);dump(out/'input.json',resolved)
    adapter_path=canonical/'cases'/args.case/'case_adapter.py'
    sys.path.insert(0,str(adapter_path.parent))
    spec=importlib.util.spec_from_file_location('v5_case_adapter',adapter_path);adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    request=adapter.prepare(resolved)
    if request.get('point_eligibility')!='probe_only':raise ValueError('Native request must retain probe-only identity; full service qualified separately')
    dump(out/'native_request.json',request)
    native_id='service-'+args.case+'-'+args.run_id
    argv=[sys.executable,'-B',str(canonical/'native_probe.py'),'--root',str(root),'--run-id',native_id,'--request',str(out/'native_request.json')]
    native=subprocess.run(argv,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(os.environ,TMPDIR=str(out/'tmp'),PYTHONDONTWRITEBYTECODE='1'))
    (out/'native-build-run.log').write_text(native.stdout)
    if native.returncode:raise RuntimeError('Native backend failed; see '+str(out/'native-build-run.log'))
    native_out=root/'runs/step4-v5/p1'/('integrator-'+native_id)
    raw=json.loads((native_out/'resolved.json').read_text())
    if args.scenario=='reference':
        check=subprocess.run([sys.executable,'-B',str(canonical/'functional_probe.py'),'--native-run',str(native_out)],cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/'functional_check.log').write_text(check.stdout)
        if check.returncode:raise RuntimeError('Nominal gate/hold diagnostic failed')
    model=adapter.evaluate(resolved,raw)
    for field in ('digital_clock_budget_satisfied','precharge_bias_feasible','write_mux_current_compliance','reference_enable_load_match_feasible'):
        model['physical_checks'].append({'id':'common_'+field,'passed':bool(raw[field]),'critical':True,'evidence':'native resolved field '+field})
    result=aggregate(resolved,model)
    result['canonical_hashes']=hashes;result['computational_hashes']=computational;result['computational_snapshot_sha256']=hashlib.sha256(json.dumps(computational,sort_keys=True).encode()).hexdigest();result['native_source_manifest_sha256']=digest(native_out/'source_manifest.json')
    result['run_directory']=str(out);result['native_run_directory']=str(native_out)
    dump(out/'resolved.json',raw);dump(out/'case_model.json',model);dump(out/'resources.json',model['resources']);dump(out/'result.json',result)
    dump(out/'execution.json',{'native_argv':argv,'native_exit_code':native.returncode,'adapter_path':str(adapter_path)})
    print(json.dumps({'status':result['status'],'review_state':result['review_state'],'case_id':args.case,'run_directory':str(out)}))
