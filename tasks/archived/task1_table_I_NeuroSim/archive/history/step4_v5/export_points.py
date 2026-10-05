#!/usr/bin/env python3
"""Export a small, unit-explicit point table from actual V5 runs; no simulation."""
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--integration-dir',type=Path,required=True);p.add_argument('--output-dir',type=Path,required=True);p.add_argument('--qualifications',type=Path);a=p.parse_args()
 source=a.integration_dir.resolve();summary=json.loads((source/'summary.json').read_text());q=json.loads(a.qualifications.read_text()) if a.qualifications else {};out=a.output_dir.absolute()
 if out.exists():raise ValueError('Export destination already exists; preserve prior snapshot')
 if any(x.is_symlink() for x in (out,*out.parents)):raise ValueError('Symlink in export path')
 points=[]
 for r in summary['results']:
  runtime=Path(r['run_directory']);inp=json.loads((runtime/'input.json').read_text());model=json.loads((runtime/'case_model.json').read_text());params=inp['resolved_parameters'];identity=inp['input']['identity'];maintenance=r.get('maintenance')
  rates=r.get('rho_MB_per_s') is not None and r.get('tau_MB_per_s') is not None
  if rates:
   assert math.isclose(r['RI_star'],r['rho_MB_per_s']/r['tau_MB_per_s'],rel_tol=1e-10)
   assert math.isclose(r['U_star'],r['N']*r['logical']['bytes_per_weight']/r['logical']['bytes_per_input']*r['RI_star'],rel_tol=1e-10)
  qualification=q.get(r['config_id'],{})
  bound=qualification.get('computational_snapshot_sha256')==r.get('computational_snapshot_sha256')
  accepted=bool(bound and qualification.get('accepted') is True and qualification.get('review_status','').startswith('PASS'))
  resources={k:v for k,v in r['resources'].items() if not (k.startswith('native') and isinstance(v,dict))}
  native_paths=[Path(x['run_directory']) for x in r.get('component_bindings',{}).values()]
  if r.get('native_run_directory'):native_paths.append(Path(r['native_run_directory']))
  locks={}
  for path in native_paths:
   backend=json.loads((path/'source_manifest.json').read_text())['backend'];locks[backend['branch']]=backend['sha']
  delta=r.get('delta_S_effective_s',r.get('delta_S_raw_s'));resident_effective=r.get('resident_effective_interval_s',r.get('resident_s'))
  point={'generation':'V5','case_id':r['case_id'],'implementation_id':r['implementation_id'],'config_id':r['config_id'],'scenario':r['scenario'],
   'status':r['status'],'review_status':qualification.get('review_status',r['review_state']),'accepted':accepted,'plot_eligible':accepted and rates and r['status'] in ('valid','conditional'),
   'K':r['K'],'N':r['N'],'bytes_per_input':r['logical']['bytes_per_input'],'bytes_per_weight':r['logical']['bytes_per_weight'],'B_S_Byte':r['B_S_Byte'],'B_R_Byte':r['B_R_Byte'],
   'precision_qualification':r['logical']['output_qualification'],'implementation_identity':identity,'backend_plan':inp['input']['backend_plan'],'backend_locks':locks,
   'technology_nm':params.get('technology_nm'),'temperature_K':params.get('temperature_K'),'range_meaning':r['range_meaning'],
   'single_stream_latency_s':r.get('single_latency_s'),'raw_stream_interval_s':r.get('delta_S_raw_s'),'effective_stream_interval_s':delta,
   'single_resident_latency_s':r.get('single_resident_latency_s',r.get('resident_s')),'raw_resident_service_s':r.get('resident_raw_s',r.get('resident_s')),'effective_resident_interval_s':resident_effective,
   'rate_basis':'long-term event schedule' if maintenance else 'serial nonoverlap, no periodic maintenance',
   'rho_MB_per_s':r.get('rho_MB_per_s'),'tau_MB_per_s':r.get('tau_MB_per_s'),'RI_star':r.get('RI_star'),'U_star':r.get('U_star'),
   'raw_rho_MB_per_s':r.get('raw_rho_MB_per_s',r.get('rho_MB_per_s')),'raw_tau_MB_per_s':r.get('raw_tau_MB_per_s',r.get('tau_MB_per_s')),
   'model_source_classes':sorted({s['source_class'] for s in model.get('stream_stages',[])+model.get('resident_stages',[])}),'main_resources':resources,'qualification':r['qualification'],'conditions':r.get('conditions',[]),'critical_failures':r.get('critical_failures',[]),
   'maintenance_summary':None if maintenance is None else {k:maintenance.get(k) for k in ('basis','feasible','schedule_policy','max_group_writeback_gap_s','retention_limit_s')},
   'computational_snapshot_sha256':r.get('computational_snapshot_sha256'),'run_directory':str(runtime),'review_binding':qualification if bound else None}
  points.append(point)
 out.mkdir(parents=True,exist_ok=False)
 dataset={'units':{'rates':'decimal MB/s = 1e6 logical Byte/s','times':'s','payload':'logical Byte'},'scope':'V5 finite paired scenarios; circles summarize samples, not confidence or all achievable combinations','source_summary_sha256':hashlib.sha256((source/'summary.json').read_bytes()).hexdigest(),'points':points,'case_records':summary.get('case_records',[]),'execution_failures':summary.get('execution_failures',[]),'paired_numeric_points':sum(x['rho_MB_per_s'] is not None and x['tau_MB_per_s'] is not None for x in points),'plot_eligible_points':sum(x['plot_eligible'] for x in points)}
 (out/'points.json').write_text(json.dumps(dataset,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
 fields=['generation','case_id','implementation_id','config_id','scenario','status','review_status','accepted','plot_eligible','K','N','precision_qualification','technology_nm','temperature_K','backend_locks','B_S_Byte','B_R_Byte','single_stream_latency_s','raw_stream_interval_s','effective_stream_interval_s','single_resident_latency_s','raw_resident_service_s','effective_resident_interval_s','rate_basis','rho_MB_per_s','tau_MB_per_s','RI_star','U_star','raw_rho_MB_per_s','raw_tau_MB_per_s','range_meaning','model_source_classes','main_resources','conditions','computational_snapshot_sha256']
 with (out/'points.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader()
  for point in points:w.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in point.items()})
 print(json.dumps({'output_directory':str(out),'numeric_pairs':dataset['paired_numeric_points'],'plot_eligible_points':dataset['plot_eligible_points'],'bytes':sum(f.stat().st_size for f in out.iterdir())}))
if __name__=='__main__':main()
