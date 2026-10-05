#!/usr/bin/env python3
"""NAND case entry: fresh native periphery plus a visible nonlinear string/TIA model."""
import argparse,concurrent.futures,hashlib,importlib.util,json,os,re,shutil,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
from run import resolve_input
from service import aggregate,dump,digest

def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__);p.add_argument('--case',choices=('nand3d',),required=True);p.add_argument('--scenario',choices=('optimistic','reference','pessimistic'),default='reference');p.add_argument('--run-id',required=True);p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));a=p.parse_args();root=a.root.expanduser().absolute();out=root/'runs/step4-v5/p4'/('case-nand3d-'+a.run_id)
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id) or any(x.is_symlink() for x in (out,*out.parents)) or any(x in str(out) for x in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):raise ValueError('Unsafe runtime path')
 case=own/'cases/nand3d';resolved=resolve_input(case/'inputs.json',a.scenario);out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();canon=out/'canonical';canon.mkdir()
 files=[own/x for x in ('run_nand.py','nand_native.py','run.py','service.py','native_probe.py','src/nand_logic_probe.cpp','src/nand_sar_probe.cpp','patches/mlp_decoder_consistency.patch','provenance/dependencies.lock.json')]+[case/'inputs.json',case/'case_adapter.py']
 for name in resolved['input'].get('adapter_files',[]):
  rel=Path(name)
  if rel.is_absolute() or '..' in rel.parts or rel.suffix not in ('.py','.json','.csv','.txt') or rel.name in ('candidate_points.json','reference_snapshot.json','result.json','summary.json'):raise ValueError('Unsafe computation support')
  files.append(case/rel)
 hashes={}
 for f in set(files):
  if f.is_symlink() or f.stat().st_size>1024*1024:raise ValueError('Unsafe source file')
  rel=f.relative_to(own);target=canon/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,target);hashes[str(rel)]=digest(f)
 comp={k:v for k,v in hashes.items() if Path(k).suffix in ('.py','.cpp','.h','.patch','.json','.csv')};dump(out/'input.json',resolved);dump(out/'computational_manifest.json',comp);dump(out/'snapshot_manifest.json',hashes)
 adapterpath=canon/'cases/nand3d/case_adapter.py';sys.path.insert(0,str(adapterpath.parent));spec=importlib.util.spec_from_file_location('nand_case',adapterpath);adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter);request=adapter.prepare_nand(resolved);dump(out/'native_request.json',request)
 def build(kind):
  argv=[sys.executable,'-B',str(canon/'nand_native.py'),'--kind',kind,'--request',str(out/'native_request.json'),'--root',str(root),'--run-id',a.run_id];run=subprocess.run(argv,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(os.environ,TMPDIR=str(out/'tmp'),PYTHONDONTWRITEBYTECODE='1'));(out/(kind+'-execution.log')).write_text(run.stdout)
  if run.returncode:raise RuntimeError(kind+' native failed')
  meta=json.loads(run.stdout.splitlines()[-1]);path=Path(meta['run_directory']);return kind,json.loads((path/'resolved.json').read_text()),{'kind':'nand_'+kind,'run_directory':str(path),'source_manifest_sha256':digest(path/'source_manifest.json'),'request_sha256':digest(out/'native_request.json')}
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:parts=list(pool.map(build,('logic','sar')))
 raw={k:r for k,r,_ in parts};bindings={k:b for k,_,b in parts};model=adapter.evaluate(resolved,raw);model['physical_checks'].append({'id':'native_digital_clock','passed':bool(raw['logic']['digital_clock_budget_satisfied']),'critical':True,'evidence':{'required_period_s':raw['logic']['digital_halfcycle_min_period_s']}});result=aggregate(resolved,model)
 result.update(canonical_hashes=hashes,computational_hashes=comp,computational_snapshot_sha256=hashlib.sha256(json.dumps(comp,sort_keys=True).encode()).hexdigest(),component_bindings=bindings,run_directory=str(out))
 dump(out/'resolved_components.json',raw);dump(out/'case_model.json',model);dump(out/'resources.json',model['resources']);dump(out/'result.json',result);print(json.dumps({'status':result['status'],'review_state':result['review_state'],'case_id':'nand3d','run_directory':str(out)}))
if __name__=='__main__':main()
