import hashlib,json,shutil
from pathlib import Path
base=Path('/Users/shine/neurosim/runs/consolidation-20261005/integration');task=Path.cwd()/'tasks/task1_table_I_NeuroSim';cur=base/'current';manifest=json.loads((base/'migration_before.json').read_text())
files={p.relative_to(task).as_posix() for p in task.rglob('*') if p.is_file()}
assert files=={r['original_path'] for r in manifest['files']},'task tree changed after inventory'
for r in manifest['files']:assert hashlib.sha256((task/r['original_path']).read_bytes()).hexdigest()==r['sha256'],r['original_path']
archive=task/'archive';history=archive/'history';history.mkdir(parents=True,exist_ok=False)
for p in list(task.iterdir()):
 if p.name!='archive':shutil.move(str(p),history/p.name)
for p in cur.iterdir():
 if p.is_dir():shutil.copytree(p,task/p.name)
 else:shutil.copy2(p,task/p.name)
(archive/'migration_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
maint=archive/'maintenance/consolidation-20261005';maint.mkdir(parents=True)
for p in (base/'integration_regression.json',base/'compare.py',base/'migrate.py',base/'prepare.py',base/'write_navigation.py'):
 shutil.copy2(p,maint/p.name)
review=base.parent/'reviewer'
for name in ('independent_reproduction.json','baseline_consistency.json','implementation_diff.patch','isolated_package_manifest.json'):
 shutil.copy2(review/name,maint/name)
for r in manifest['files']:assert hashlib.sha256((task/r['archive_path']).read_bytes()).hexdigest()==r['sha256'],r['original_path']
report={'status':'PASS','original_file_count':len(manifest['files']),'all_original_bytes_preserved':True,'original_total_bytes':sum(r['size'] for r in manifest['files']),'original_head':manifest['head'],'managed_root':str(task),'local_backup':str(base/'before')}
(maint/'migration_verification.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(report,ensure_ascii=False))
