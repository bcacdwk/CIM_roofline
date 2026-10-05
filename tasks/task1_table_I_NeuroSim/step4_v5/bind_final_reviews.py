#!/usr/bin/env python3
"""Bind actual final fresh runs to existing exact-hash independent fresh evidence."""
import argparse,hashlib,json,math
from pathlib import Path
REVIEWS={'pcm':'p1_pcm_hv','mram':'p1_mram','nor2d':'p2_nor2d','fenor3d':'p2_fenor3d','feram':'p3_feram','gc04':'p3_gc04','nand3d':'p4_nand3d'}

def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__);p.add_argument('--integration-dir',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--allow-pending',action='store_true');a=p.parse_args();summary=json.loads((a.integration_dir/'summary.json').read_text());qual=json.loads((own/'results/accepted_qualifications.json').read_text());bindings=[];pending=[]
 for r in summary['results']:
  path=own/'reviews'/REVIEWS[r['case_id']]/'review.json'
  if not path.exists():pending.append({'config_id':r['config_id'],'reason':'independent review pending'});continue
  review=json.loads(path.read_text());status=review.get('review_status',review.get('status',''))
  if not status.startswith('PASS') or review.get('open_blockers') or review.get('blocking_findings'):pending.append({'config_id':r['config_id'],'reason':'review not PASS/no blockers'});continue
  entries=review.get('fresh_runs',review.get('checks',[]));entry=next((x for x in entries if x.get('scenario')==r['scenario']),None)
  if entry is None:raise ValueError('No independent scenario record '+r['config_id'])
  where=entry.get('run_directory',entry.get('fresh_run',entry.get('run')));ind_path=Path(where);ind=json.loads((ind_path/'result.json').read_text())
  if ind_path.resolve()==Path(r['run_directory']).resolve():raise ValueError('Independent run reused producer directory')
  if ind['computational_snapshot_sha256']!=r['computational_snapshot_sha256'] or ind['computational_hashes']!=r['computational_hashes']:raise ValueError('Independent/final computation snapshot differs '+r['config_id'])
  differences={}
  for key in ('rho_MB_per_s','tau_MB_per_s','RI_star','U_star','single_latency_s','delta_S_raw_s','resident_s','resident_raw_s','delta_S_effective_s','resident_effective_interval_s'):
   if key in r:
    if not math.isclose(r[key],ind[key],rel_tol=1e-10,abs_tol=1e-15):raise ValueError('Final rate/time differs '+r['config_id']+':'+key)
    differences[key]=abs(r[key]-ind[key])
  native_final=[x['run_directory'] for x in r.get('component_bindings',{}).values()]+([r['native_run_directory']] if r.get('native_run_directory') else [])
  native_ind=[x['run_directory'] for x in ind.get('component_bindings',{}).values()]+([ind['native_run_directory']] if ind.get('native_run_directory') else [])
  if set(native_final)&set(native_ind):raise ValueError('Native source/build directory reused')
  if r['config_id'] not in qual or not qual[r['config_id']].get('accepted'):pending.append({'config_id':r['config_id'],'reason':'supervisor acceptance pending'});continue
  bindings.append({'config_id':r['config_id'],'case_id':r['case_id'],'scenario':r['scenario'],'computational_snapshot_sha256':r['computational_snapshot_sha256'],'final_run':r['run_directory'],'independent_run':str(ind_path),'independent_review':str(path.relative_to(own)),'review_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'review_status':status,'all_computational_files_equal':True,'new_source_build_directories_distinct':True,'rate_time_absolute_differences':differences,'original_independent_major_counts_retained':True,'supervisor_acceptance':qual[r['config_id']]})
 result={'status':'PASS_FINAL_HASH_BINDING' if not pending and len(bindings)==21 else 'PENDING','final_run_directory':str(a.integration_dir.resolve()),'final_summary_sha256':hashlib.sha256((a.integration_dir/'summary.json').read_bytes()).hexdigest(),'bound_points':len(bindings),'expected_points':21,'bindings':bindings,'pending':pending,'scope':'Production binding audit only; substantive independent reviews remain authored byA/B. Matching final hash reuses their actual fresh builds, not repair-preceding PASS.'}
 a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':result['status'],'bound_points':len(bindings),'pending':len(pending),'output':str(a.output)}))
 if pending and not a.allow_pending:raise SystemExit(1)
if __name__=='__main__':main()
