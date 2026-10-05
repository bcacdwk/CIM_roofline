#!/usr/bin/env python3
"""Fresh bounded-concurrency case/scenario integration; local outputs only."""
import argparse
import concurrent.futures
import csv
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
sys.dont_write_bytecode=True
from v5 import entry_for
CASES=('pcm','mram','nor2d','fenor3d','feram','gc04','nand3d')
SCENARIOS=('optimistic','reference','pessimistic')

def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def main():
    own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases',nargs='+',choices=CASES,default=['pcm','mram']);p.add_argument('--scenarios',nargs='+',choices=SCENARIOS,default=list(SCENARIOS))
    p.add_argument('--run-id',required=True);p.add_argument('--workers',type=int,choices=(1,2),default=2)
    p.add_argument('--root',type=Path,default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))))
    a=p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+',a.run_id):p.error('Invalid run ID')
    root=a.root.expanduser().absolute();out=root/'runs/step4-v5/integration'/a.run_id
    if any(x.is_symlink() for x in (out,*out.parents)) or any(t in str(out) for t in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):p.error('Unsafe runtime path')
    case_records=[];pairs=[]
    for case in a.cases:
        folder=own/'cases'/case
        missing=[name for name in ('inputs.json','case_adapter.py') if not (folder/name).is_file()]
        if missing:
            case_records.append({'case_id':case,'status':'implementation_not_ready','reason':'missing '+','.join(missing),'formal_point':False});continue
        source=json.loads((folder/'inputs.json').read_text())
        available=[scenario for scenario in a.scenarios if scenario in source.get('scenarios',{})]
        if len(available)!=len(a.scenarios):case_records.append({'case_id':case,'status':'range_not_ready','missing_scenarios':list(set(a.scenarios)-set(available)),'formal_point':False})
        pairs.extend((case,scenario) for scenario in available)
    out.mkdir(parents=True,exist_ok=False);(out/'tmp').mkdir();shutil.copy2(__file__,out/'integrate.py');shutil.copy2(own/'v5.py',out/'v5.py')
    def run(pair):
        case,scenario=pair;rid=a.run_id+'-'+scenario
        argv=[sys.executable,'-B',str(own/entry_for(case,own)),'--case',case,'--scenario',scenario,'--run-id',rid,'--root',str(root)]
        result=subprocess.run(argv,cwd=out,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,env=dict(os.environ,TMPDIR=str(out/'tmp'),PYTHONDONTWRITEBYTECODE='1'))
        (out/(case+'-'+scenario+'.log')).write_text(result.stdout)
        path=root/('runs/step4-v5/component-services' if entry_for(case,own)=='run_components.py' else 'runs/step4-v5/p4' if entry_for(case,own)=='run_nand.py' else 'runs/step4-v5/p1')/('case-'+case+'-'+rid)
        return {'case_id':case,'scenario':scenario,'argv':argv,'exit_code':result.returncode,'run_path':str(path),'result':json.loads((path/'result.json').read_text()) if result.returncode==0 and (path/'result.json').exists() else None}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as pool:runs=list(pool.map(run,pairs))
    dump(out/'execution.json',runs)
    failures=[{k:r[k] for k in ('case_id','scenario','exit_code','run_path')} for r in runs if r['exit_code'] or r['result'] is None]
    rows=[r['result'] for r in runs if r['result'] is not None]
    shared={};case_inputs={};case_packages={}
    for row in rows:
        comp=row['computational_hashes']
        for name,value in comp.items():
            if not name.startswith('cases/'):shared.setdefault(name,set()).add(value)
        source_id=comp['cases/'+row['case_id']+'/inputs.json'];case_inputs.setdefault(row['case_id'],set()).add(source_id)
        case_package={k:v for k,v in comp.items() if k.startswith('cases/'+row['case_id']+'/')}
        case_packages.setdefault(row['case_id'],set()).add(json.dumps(case_package,sort_keys=True))
        if 'rho_MB_per_s' in row:
            assert math.isclose(row['U_star'],row.get('resident_effective_interval_s',row['resident_s'])/row.get('delta_S_effective_s',row['delta_S_raw_s']),rel_tol=1e-12)
            assert math.isclose(row['RI_star'],row['rho_MB_per_s']/row['tau_MB_per_s'],rel_tol=1e-12)
    if any(len(values)!=1 for values in shared.values()) or any(len(x)!=1 for x in case_inputs.values()) or any(len(x)!=1 for x in case_packages.values()):raise RuntimeError('Source/input changed during integration; mixed snapshot rejected')
    summary={'run_id':a.run_id,'review_state':'not_reviewed','computed_pairs':len(rows),'expected_pairs':len(a.cases)*len(a.scenarios),'scheduled_pairs':len(pairs),'all_requested_configurations_executed':len(rows)==len(a.cases)*len(a.scenarios) and not failures,
             'normal_candidates':sum(r['status'] in ('valid','conditional') for r in rows),'formal_accepted_points':0,
             'execution_failures':failures,'case_records':case_records,'shared_computational_hashes':{k:next(iter(values)) for k,values in shared.items()},'case_input_hashes':{k:next(iter(v)) for k,v in case_inputs.items()},'results':rows}
    dump(out/'summary.json',summary)
    fields=('case_id','implementation_id','config_id','scenario','status','review_state','K','N','single_latency_s','delta_S_raw_s','resident_s','B_S_Byte','B_R_Byte','rho_MB_per_s','tau_MB_per_s','RI_star','U_star','computational_snapshot_sha256')
    with (out/'summary.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
    dump(out/'integration_manifest.json',{'integrator_script_sha256':hashlib.sha256((out/'integrate.py').read_bytes()).hexdigest(),'summary_sha256':hashlib.sha256((out/'summary.json').read_bytes()).hexdigest(),'row_source_paths':[r['run_path'] for r in runs],'exported_to_management':False})
    print(json.dumps({'run_directory':str(out),'computed_pairs':len(rows),'normal_candidates':summary['normal_candidates'],'formal_accepted_points':0,'execution_failures':len(failures),'case_records':case_records}))
    if failures:raise SystemExit(1)
if __name__=='__main__':main()
