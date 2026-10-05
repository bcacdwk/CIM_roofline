#!/usr/bin/env python3
"""Clock/dependency, coverage/resource, native approximation and v3-time replay."""
import argparse
import json
import os
from pathlib import Path
import runpy
import sys
sys.dont_write_bytecode=True

def dump(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',required=True);ap.add_argument('--out',required=True);ap.add_argument('--cxx',required=True)
    a=ap.parse_args();root=Path(a.root).resolve();out=Path(a.out).resolve();out.relative_to(root)
    out.mkdir(parents=True,exist_ok=False)
    own=Path(__file__).resolve().parent;management=own.parents[1]
    repo=Path(os.environ.get('NEUROSIM_REPO_ROOT',str(management.parent.parent))).resolve()
    cases=[json.loads(f.read_text()) for f in sorted((management/'configs/cases').glob('*.json'))]
    policy=json.loads((management/'contracts/parameter_policy.json').read_text())
    clock=runpy.run_path(str(own/'clock_dependency.py'))
    digital=runpy.run_path(str(own/'digital_resources.py'))
    replay=runpy.run_path(str(own/'legacy_replay.py'))
    outputs={}
    outputs['clock_dependency']=clock['run_checks'](cases,policy)
    outputs['digital_resources']=digital['run_checks'](cases,policy)
    outputs['addertree_model']=digital['run_native'](root,out/'addertree-model',a.cxx)
    outputs['legacy_replay']=replay['run_checks'](cases,repo)
    assertion_rows=[]
    for name,data in outputs.items():
        dump(out/(name+'.json'),data)
        checks=data['checks']
        if isinstance(checks,dict):
            assertion_rows.extend({'group':name,'name':key,'status':'PASS' if val else 'FAIL'} for key,val in checks.items())
        else:
            assertion_rows.extend({'group':name,'name':row.get('name',row.get('id')),'status':row['status']} for row in checks)
    dump(out/'assertions.json',assertion_rows)
    commands=json.loads((out/'addertree-model/commands.json').read_text())
    commands.append({'argv':[sys.executable,str(own/'legacy_replay.py')],
        'invocation':'in-process run_checks(cases,repo); saved v3 results comparison occurs after independent aggregation',
        'cwd':str(out),'returncode':0 if outputs['legacy_replay']['status']=='PASS' else 1})
    dump(out/'commands.json',commands)
    summary={'contract_version':'3.0.0','status':'PASS' if all(x['status']=='PASS' for x in outputs.values()) else 'FAIL',
      'group_status':{name:data['status'] for name,data in outputs.items()},
      'assertions':len(assertion_rows),'passed':sum(x['status']=='PASS' for x in assertion_rows),
      'original_time_replay_cases':10,'native_case_timing_qualified':False,
      'new_ten_case_performance':False,'new_clock_alignment_used_in_legacy_replay':False}
    dump(out/'summary.json',summary)
    print(summary['status'],'interface_revision',summary['passed'],'/',summary['assertions'],out)
    return 0 if summary['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
