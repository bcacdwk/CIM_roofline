#!/usr/bin/env python3
"""Unified Step4 V5 run, batch and nominal-diagnostic entry; any working directory."""
import argparse,ast,json,os,subprocess,sys
from pathlib import Path
sys.dont_write_bytecode=True
CASES=('pcm','mram','nor2d','fenor3d','feram','gc04','nand3d')

def entry_for(case,own):
    adapter=own/'cases'/case/'case_adapter.py'
    if not adapter.is_file():raise ValueError('Case has no production adapter: '+case)
    names={n.name for n in ast.parse(adapter.read_text()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    if 'prepare_nand' in names:return 'run_nand.py'
    if 'prepare_components' in names:return 'run_components.py'
    if 'prepare' in names:return 'run.py'
    raise ValueError('No recognized case service interface: '+case)

def main():
    own=Path(__file__).resolve().parent
    if len(sys.argv)>1 and sys.argv[1] in ('compare','plots'):
        script=own/('compare_v4.py' if sys.argv[1]=='compare' else 'plot_overview.py')
        if not script.is_file():raise SystemExit('Post-processing author has not supplied '+script.name+' yet; computation entry is independent')
        interpreter=os.environ.get('NEUROSIM_PLOT_PYTHON','/opt/anaconda3/bin/python' if Path('/opt/anaconda3/bin/python').is_file() else sys.executable) if sys.argv[1]=='plots' else sys.executable
        raise SystemExit(subprocess.call([interpreter,'-B',str(script),*sys.argv[2:]]))
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    run=sub.add_parser('run');run.add_argument('--case',choices=CASES,required=True);run.add_argument('--scenario',choices=('optimistic','reference','pessimistic'),default='reference');run.add_argument('--run-id',required=True);run.add_argument('--root',type=Path)
    batch=sub.add_parser('all');batch.add_argument('--cases',choices=CASES,nargs='+',default=list(CASES));batch.add_argument('--scenarios',choices=('optimistic','reference','pessimistic'),nargs='+',default=['optimistic','reference','pessimistic']);batch.add_argument('--run-id',required=True);batch.add_argument('--workers',type=int,choices=(1,2),default=2);batch.add_argument('--root',type=Path)
    package=sub.add_parser('package');package.add_argument('--cases',choices=CASES,nargs='+',required=True);package.add_argument('--run-id',required=True);package.add_argument('--root',type=Path)
    export=sub.add_parser('export');export.add_argument('--integration-dir',type=Path,required=True);export.add_argument('--output-dir',type=Path,required=True);export.add_argument('--qualifications',type=Path)
    diag=sub.add_parser('diagnostics');diag.add_argument('--run-directory',type=Path,required=True)
    for name in ('compare','plots'):
        post=sub.add_parser(name);post.add_argument('args',nargs=argparse.REMAINDER)
    a=p.parse_args()
    if a.command in ('compare','plots'):
        script=own/('compare_v4.py' if a.command=='compare' else 'plot_overview.py')
        if not script.is_file():raise SystemExit('Post-processing author has not supplied '+script.name+' yet; computation entry is independent')
        raise SystemExit(subprocess.call([sys.executable,'-B',str(script),*a.args]))
    if a.command=='run':
        argv=[sys.executable,'-B',str(own/entry_for(a.case,own)),'--case',a.case,'--scenario',a.scenario,'--run-id',a.run_id]
        if a.root:argv+=['--root',str(a.root)]
        raise SystemExit(subprocess.call(argv,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')))
    if a.command=='export':
        argv=[sys.executable,'-B',str(own/'export_points.py'),'--integration-dir',str(a.integration_dir),'--output-dir',str(a.output_dir)]
        if a.qualifications:argv+=['--qualifications',str(a.qualifications)]
        raise SystemExit(subprocess.call(argv))
    if a.command=='package':
        argv=[sys.executable,'-B',str(own/'package_compute.py'),'--cases',*a.cases,'--run-id',a.run_id]
        if a.root:argv+=['--root',str(a.root)]
        raise SystemExit(subprocess.call(argv,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')))
    if a.command=='all':
        argv=[sys.executable,'-B',str(own/'integrate.py'),'--cases',*a.cases,'--scenarios',*a.scenarios,'--run-id',a.run_id,'--workers',str(a.workers)]
        if a.root:argv+=['--root',str(a.root)]
        raise SystemExit(subprocess.call(argv,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')))
    root=a.run_directory.expanduser().resolve();result=json.loads((root/'result.json').read_text());jobs=[]
    if result.get('native_run_directory'):jobs.append(('functional_probe.py',result['native_run_directory']))
    for b in result.get('component_bindings',{}).values():
        if b['kind']=='digital':jobs.append(('digital_functional_probe.py',b['run_directory']))
        if b['kind']=='gc_digital':jobs.append(('gc_functional_probe.py',b['run_directory']))
    if not jobs:raise ValueError('No nominal digital diagnostic applies; use case physical diagnostics')
    for script,path in jobs:
        subprocess.run([sys.executable,'-B',str(own/script),'--native-run',path],cwd=root,check=True,env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1'))
if __name__=='__main__':main()
