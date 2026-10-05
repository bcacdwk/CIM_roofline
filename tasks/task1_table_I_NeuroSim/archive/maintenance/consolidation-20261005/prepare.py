import ast,hashlib,json,shutil
from pathlib import Path
base=Path('/Users/shine/neurosim/runs/consolidation-20261005/integration'); old=base/'before'; cur=base/'current'; shared=cur/'analysis/shared'
shared.mkdir(parents=True,exist_ok=True)
def dump(p,x): p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
records=[]
def cp(src,dst):
 dst.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(src,dst); records.append({'original_path':str(src.relative_to(old)),'current_path':str(dst.relative_to(cur)),'original_sha256':sha(src),'current_sha256':sha(dst)})
for group,target,files in [('pilots','array_backend',['backend.py','backend.cpp','paths_dag.h','schedule.py','timing.py','check_v2.py','adapters/acim.py','adapters/dcim.py','adapters/rram.py']),('step4_v2','peripheral_backend',['backend.py','backend.cpp','step4_dag.h','engine.py','adapters/native.py','adapters/nand.py'])]:
 for name in files:
  dest=shared/target/('checks.py' if name=='check_v2.py' else name);cp(old/group/name,dest)
# Keep the selected callable algorithms only; numerical regressions which consume historical diagnostics are archived.
for name,marker in [('native.py','def _vectors('),('nand.py','def _half_up(')]:
 p=shared/'peripheral_backend/adapters'/name;s=p.read_text();p.write_text(s[:s.index(marker)])
# Freeze the selected branch, retaining all numerical operations. No alternate implementation is carried.
p=shared/'array_backend/backend.py';s=p.read_text();s=s.replace('def build(case,root,out,cxx,own,revision="v2"):', 'def build(case,root,out,cxx,own):\n    revision="v2"  # Selected source interface; historical alternatives are not installed.')
s=s.replace("adapter_source=own/('backend_v1.cpp' if revision=='v1' else 'backend.cpp')","adapter_source=own/'backend.cpp'")
p.write_text(s)
case_sources={}; repo=Path.cwd()
for p in sorted((old/'configs/cases').glob('*.json')):
 cid=p.stem;x=json.loads(p.read_text()); srcs=x['provenance']['sources'];case_sources[cid]={'config_original_path':'configs/cases/'+p.name,'config_original_sha256':sha(p),'sources':srcs}
 # The self-contained case input keeps the historical literature/source metadata as provenance, never an executable dependency.
 x['provenance']={'source_record':'provenance/input_sources.json#'+cid,'profile':'reference','sources':{'inputs':{'path':'analysis/'+cid+'/source_inputs.json','sha256':srcs['inputs']['sha256']}}}
 dump(cur/'analysis'/cid/'input.json',x)
 src=repo/srcs['inputs']['path']; assert sha(src)==srcs['inputs']['sha256']; cp(src if src.is_relative_to(old) else old/'configs/cases'/p.name,cur/'analysis'/cid/'unused') if False else None
 shutil.copy2(src,cur/'analysis'/cid/'source_inputs.json')
shared_source=repo/case_sources['01_sram_acim']['sources']['shared']['path'];d=json.loads(shared_source.read_text());values=d['common_conditions']['propagation']['profile_values']['reference']
dump(shared/'inputs/service_conditions.json',{'units':'ns for durations; source retains names','reference':values,'source':{'original_path':str(shared_source.relative_to(repo)),'sha256':sha(shared_source),'json_pointer':'/common_conditions/propagation/profile_values/reference'}})
cp(old/'provenance/neurosim.lock.json',cur/'provenance/neurosim.lock.json')
dump(cur/'provenance/input_sources.json',case_sources)
for r in records:r['current_sha256']=sha(cur/r['current_path'])
dump(cur/'provenance/code_sources.json',{'selected_commit':'b7795fd5acc8f5f3816d1022111330fc569b6853','integration_head':'8d75481fbf0d9005c5285ff4b4fecdb9f7d6a5e6','files':records,'changes':'Path packaging, selected backend entry point, and removal of non-runtime historical numerical-comparison functions. Computation adapters, scheduler and timing arithmetic retained.'})
print('current prepared',cur)
