#!/usr/bin/env python3
"""V5 case service from separate physical and digital native components."""
import argparse
import concurrent.futures
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True
from run import resolve_input,CASES
from service import dump,digest
from component_aggregate import aggregate
ENTRIES={
 'threshold':('threshold_probe.py','src/threshold_port_probe.cpp'),
 'digital':('digital_probe.py','src/digital_service_probe.cpp'),
 'gc_current':('special_probe.py','src/gc_current_probe.cpp'),
 'gc_digital':('gc_digital.py','src/gc_digital_probe.cpp'),
 'polarization':('special_probe.py','src/polarization_port_probe.cpp'),
 'current_sampling':('special_probe.py','src/current_sampling_probe.cpp')}

FORBIDDEN={'candidate_points.json','reference_snapshot.json','summary.json','summary.csv','result.json','probe_result.json','case_model.json'}

def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--case',choices=CASES,required=True);p.add_argument('--scenario',choices=('optimistic','reference','pessimistic'),default='reference');p.add_argument('--run-id',required=True)
 p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));a=p.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):p.error('Invalid run ID')
 root=a.root.expanduser().absolute();out=root/'runs/step4-v5/component-services'/('case-'+a.case+'-'+a.run_id)
 if any(q.is_symlink() for q in (out,*out.parents)) or any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe run path')
 case=own/'cases'/a.case;resolved=resolve_input(case/'inputs.json',a.scenario)
 out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();canon=out/'canonical';canon.mkdir()
 common=['run_components.py','component_aggregate.py','run.py','service.py','native_probe.py','provenance/dependencies.lock.json']
 files=[own/x for x in common]+[case/'inputs.json',case/'case_adapter.py']
 for name in resolved['input'].get('adapter_files',[]):
  rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts or rel.name in FORBIDDEN or any(x in ('results','reports','review','legacy','replay') for x in rel.parts) or rel.suffix not in ('.py','.json','.csv','.txt'):raise ValueError('Non-computational or unsafe adapter support '+name)
  files.append(case/rel)
 hashes={}
 for f in files:
  if f.is_symlink() or f.stat().st_size>1024*1024:raise ValueError('Unsafe canonical file '+str(f))
  rel=f.relative_to(own);dest=canon/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);hashes[str(rel)]=digest(f)
 if digest(canon/'cases'/a.case/'inputs.json')!=resolved['input_sha256']:raise ValueError('Input changed during snapshot')
 comp={k:v for k,v in hashes.items() if Path(k).suffix in ('.py','.cpp','.h','.patch','.json','.csv')}
 dump(out/'snapshot_manifest.json',hashes);dump(out/'computational_manifest.json',comp);dump(out/'input.json',resolved)
 adapterpath=canon/'cases'/a.case/'case_adapter.py';sys.path.insert(0,str(adapterpath.parent));spec=importlib.util.spec_from_file_location('v5_component_adapter',adapterpath);adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
 jobs=adapter.prepare_components(resolved)
 if not isinstance(jobs,dict) or not jobs:raise ValueError('Explicit physical component jobs required')
 def run(item):
  name,job=item
  if not re.fullmatch(r'[A-Za-z0-9_-]+',name) or job['kind'] not in ENTRIES:raise ValueError('Unknown component kind/name')
  req=out/(name+'-request.json');dump(req,job['request']);rid=a.case+'-'+a.run_id+'-'+name
  argv=[sys.executable,'-B',str(canon/ENTRIES[job['kind']][0]),'--request',str(req),'--root',str(root),'--run-id',rid]
  r=subprocess.run(argv,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(os.environ,TMPDIR=str(out/'tmp'),PYTHONDONTWRITEBYTECODE='1'))
  (out/(name+'-execution.log')).write_text(r.stdout)
  if r.returncode:raise RuntimeError(name+' native component failed; see log')
  meta=json.loads(r.stdout.splitlines()[-1]);path=Path(meta['run_directory']);raw=json.loads((path/'resolved.json').read_text())
  return name,raw,{'kind':job['kind'],'argv':argv,'run_directory':str(path),'source_manifest_sha256':digest(path/'source_manifest.json'),'request_sha256':digest(req)}
 def snapshot_jobs(selected):
  for name,job in selected.items():
   if job['kind'] not in ENTRIES:raise ValueError('Unknown component kind')
   for relative in ENTRIES[job['kind']]+(('patches/mlp_decoder_consistency.patch',) if job['kind'] in ('threshold','digital','gc_digital','polarization') else ()):
    f=own/relative;dest=canon/relative;dest.parent.mkdir(parents=True,exist_ok=True)
    if relative in hashes and hashes[relative]!=digest(f):raise ValueError('Shared component changed during one service build')
    shutil.copy2(f,dest);hashes[relative]=digest(f)
 snapshot_jobs(jobs)
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:completed=list(pool.map(run,jobs.items()))
 raw={name:values for name,values,_ in completed}
 if hasattr(adapter,'prepare_additional_components'):
  extra=adapter.prepare_additional_components(resolved,raw)
  if set(extra)&set(jobs):raise ValueError('Duplicate dependent component name')
  snapshot_jobs(extra)
  with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:completed+=list(pool.map(run,extra.items()))
 raw={name:values for name,values,_ in completed};bindings={name:binding for name,_,binding in completed}
 comp={k:v for k,v in hashes.items() if Path(k).suffix in ('.py','.cpp','.h','.patch','.json','.csv')}
 dump(out/'snapshot_manifest.json',hashes);dump(out/'computational_manifest.json',comp)
 model=adapter.evaluate(resolved,raw)
 for name,values,binding in completed:
  if binding['kind'] in ('digital','gc_digital'):model['physical_checks'].append({'id':'native_'+name+'_clock','passed':bool(values['digital_clock_budget_satisfied']),'critical':True,'evidence':{'required_s':values['digital_halfcycle_min_period_s']}})
  if binding['kind']=='threshold' and not values['native_gate_driver_compatible']:
   external=model.get('external_gate_port',{})
   stage_map={s['id']:s for s in model.get('stream_stages',[])+model.get('resident_stages',[])}
   qualified=bool(external.get('qualified') and external.get('source_ids') and external.get('domain') and external.get('stage_ids') and not(set(external.get('source_ids',[]))-set(resolved['input']['sources'])) and all(s in stage_map and stage_map[s]['source_class'] in ('adapter','external_primitive') for s in external.get('stage_ids',[])))
   model['physical_checks'].append({'id':'native_gate_replaced_by_explicit_port','passed':qualified,'critical':True,'evidence':external or 'Native gate incompatible; no qualified external port'})
 result=aggregate(resolved,model);result['canonical_hashes']=hashes;result['computational_hashes']=comp
 result['computational_snapshot_sha256']=hashlib.sha256(json.dumps(comp,sort_keys=True).encode()).hexdigest();result['runtime_input_sha256']=digest(out/'input.json');result['component_bindings']=bindings;result['run_directory']=str(out)
 dump(out/'resolved_components.json',raw);dump(out/'component_bindings.json',bindings);dump(out/'case_model.json',model);dump(out/'resources.json',model['resources']);dump(out/'result.json',result)
 print(json.dumps({'status':result['status'],'review_state':result['review_state'],'case_id':a.case,'run_directory':str(out)}))
if __name__=='__main__':main()
