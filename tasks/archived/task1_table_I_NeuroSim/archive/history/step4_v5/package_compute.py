#!/usr/bin/env python3
"""Small explicit V5 computation package; no historical/final performance inputs."""
import argparse,hashlib,json,os,re,shutil,sys
from pathlib import Path
sys.dont_write_bytecode=True
CASES=('pcm','mram','nor2d','fenor3d','feram','gc04','nand3d')
COMMON=('INTERFACE.md','PROBE_API.md','run_nand.py','nand_native.py','v5.py','integrate.py','package_compute.py','run.py','service.py','run_components.py','component_aggregate.py','native_probe.py','threshold_probe.py','digital_probe.py','special_probe.py','gc_digital.py','functional_probe.py','digital_functional_probe.py','gc_functional_probe.py','provenance/dependencies.lock.json','provenance/upstream-notices.txt')
FORBIDDEN={'candidate_points.json','reference_snapshot.json','result.json','summary.json','summary.csv','probe_result.json','case_model.json','review.json'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cases',nargs='+',choices=CASES,required=True);p.add_argument('--run-id',required=True);p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))));a=p.parse_args()
 root=a.root.expanduser().absolute();out=root/'runs/step4-v5/packages'/a.run_id
 if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id) or any(x.is_symlink() for x in (out,*out.parents)) or any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe package path')
 files=[own/name for name in COMMON]+list((own/'src').glob('*.cpp'))+list((own/'patches').glob('*.patch'))
 for case in a.cases:
  folder=own/'cases'/case;source=json.loads((folder/'inputs.json').read_text());files.extend([folder/'inputs.json',folder/'case_adapter.py'])
  for name in source.get('adapter_files',[]):
   rel=Path(name)
   if rel.is_absolute() or '..' in rel.parts or rel.name in FORBIDDEN or rel.suffix not in ('.py','.json','.csv','.txt') or any(q in ('results','reports','review','reviews','legacy','replay') for q in rel.parts):raise ValueError('Non-computational adapter support '+case+'/'+name)
   files.append(folder/rel)
  files.extend(folder.glob('LICENSE*.txt'))
 files=sorted(set(files));out.mkdir(parents=True,exist_ok=False);manifest={}
 for f in files:
  if f.is_symlink() or f.stat().st_size>1024*1024:raise ValueError('Unsafe/large compute source '+str(f))
  rel=f.relative_to(own);dest=out/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(f,dest);manifest[str(rel)]={'sha256':digest(dest),'bytes':dest.stat().st_size}
 payload={'status':'compute_only','cases':a.cases,'files':manifest,'source_bytes':sum(x['bytes'] for x in manifest.values()),'upstream':'Exact locked worktrees via NEUROSIM_ROOT/worktrees.json; no upstream source duplicated into management','excluded':['all old performance files','candidate_points/reference_snapshot','reports/reviews/plots','legacy/replay','production binaries/cache'],'eligibility':'Package construction is not physical acceptance; final reviewer rebuilds from this package'}
 (out/'PACKAGE_MANIFEST.json').write_text(json.dumps(payload,indent=2)+'\n')
 (out/'README.compute.txt').write_text('Compute-only V5 package. Locked upstream worktrees are required at NEUROSIM_ROOT.\nRun from any cwd: python3 -B '+str(out/'v5.py')+' run --case '+a.cases[0]+' --scenario reference --run-id unique-review-id\nNo candidate/reference summaries, old performance, or producer binary is included.\n')
 print(json.dumps({'run_directory':str(out),'source_files':len(manifest),'source_bytes':payload['source_bytes'],'status':'compute_only_not_rebuilt'}))
if __name__=='__main__':main()
