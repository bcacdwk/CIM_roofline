#!/usr/bin/env python3
import json,sys,hashlib
from pathlib import Path
here=Path(__file__).resolve().parent
run=Path(sys.argv[1]).resolve(); package=here/'only_v4'
records=[]
for f in sorted(here.glob('open_audit.*')):
 for line in f.read_text().splitlines():
  try:records.append(json.loads(line))
  except json.JSONDecodeError:raise AssertionError(f)
old_tokens=('step4_v3','step4_v2','/pilots/','legacy_replay','historical_replay','/results/step4/')
old=[r for r in records if any(t in json.dumps(r).lower() for t in old_tokens)]
assert not old,old
assert not (package/'results').exists()
assert not any(p.is_symlink() for p in package.rglob('*'))
builds=[]
for manifest in sorted(run.glob('ns_*/*/source_manifest.json')):
 d=json.loads(manifest.read_text());dest=manifest.parent
 commands=json.loads((dest/'commands.json').read_text()); compilers=[a for a in commands if '-std=c++17' in a]
 assert len(compilers)==1 and str(dest/'service')==compilers[0][-1]
 binary=dest/'service';assert binary.is_file()
 actual=hashlib.sha256(binary.read_bytes()).hexdigest();assert actual==d['executable_sha256']
 execution=json.loads((dest/'execution.json').read_text());assert execution['argv']==[str(binary)]
 assert all(str(dest/'src') in a for a in compilers[0] if a.endswith('.cpp'))
 builds.append({'case_scenario':str(dest.relative_to(run)),'executable':str(binary),'sha256':actual,'backend':d['backend'],'source_file_count':len(d['patched_files'])})
assert len([b for b in builds if '/diagnostic_' not in b['case_scenario']])==9
snapshot=json.loads((run/'snapshot_manifest.json').read_text())
for rel,digest in snapshot.items():assert hashlib.sha256((package/rel).read_bytes()).hexdigest()==digest
out={'status':'pass','run':str(run),'onlyV4_package':str(package),'package_has_no_results':True,'historical_read_or_subprocess_matches':old,'audit_event_count':len(records),'python_process_logs':len(list(here.glob('open_audit.*'))),'scope':'Python file-open/subprocess audit for launcher workers and postprocessing; compiler and service command provenance checked separately. Locked native upstream remains required source. Not an OS-wide syscall trace.','fresh_builds':builds,'canonical_snapshot_matches_onlyV4_package':True}
(here/'independent_dependencies.json').write_text(json.dumps(out,indent=2)+'\n');print('Independent source-package/build/read-dependency audit passed')
