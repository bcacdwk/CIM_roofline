#!/usr/bin/env python3
"""Read-only historical comparison after V5 computation. Never imported by runners."""
import argparse,csv,hashlib,json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
NAMES={'ns_sram_acim':'sram_acim','ns_sram_dcim':'sram_dcim','ns_rram_1t1r':'rram'}
SCENARIOS=('optimistic','reference','pessimistic')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write_json(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
def rows_csv(path,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with path.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=keys);w.writeheader()
  for row in rows:w.writerow({k:json.dumps(v,ensure_ascii=False,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in row.items()})
def historical(v4):
 run=v4/'results/reference-v4-20261005';source=run/'summary.json';reviewpath=v4/'reports/review.json';summary=json.loads(source.read_text());review=json.loads(reviewpath.read_text());qualification=run/'qualification.json'
 if review['status']!='PASS_WITH_EXPLICIT_MODEL_CONDITIONS' or review.get('blocking_findings'):raise ValueError('Unexpected historical V4 qualification')
 old=summary['case_results'];ids={(r['case_id'],r['scenario']) for r in old}
 if ids!={(c,s) for c in NAMES for s in SCENARIOS} or len(old)!=9:raise ValueError('Expected exactly original V4 nine points')
 points=[]
 for r in old:
  reviewed=next(x for x in review['case_results'] if x['paired_id']==r['paired_id'])
  for k in ('rho_MB_per_s','tau_MB_per_s','RI_star','U_star','delta_S_ns','T_R_ns'):
   if reviewed[k]!=r[k]:raise ValueError('Historical summary/review mismatch '+r['paired_id'])
  ds=r['delta_S_ns']*1e-9;tr=r['T_R_ns']*1e-9
  for value,expected in ((r['rho_MB_per_s'],r['B_S_Byte']/ds/1e6),(r['tau_MB_per_s'],r['B_R_Byte']/tr/1e6),(r['RI_star'],r['rho_MB_per_s']/r['tau_MB_per_s']),(r['U_star'],tr/ds)):
   if not math.isclose(value,expected,rel_tol=1e-10):raise ValueError('V4 payload/unit inconsistency')
  origin=r['case_id'];cid=NAMES[origin];precision=('29-bit signed Q4 approximate; finite analog residuals, not exact INT8' if cid=='rram' else '25-bit nominal arithmetic; SRAM multi-row analog transfer conditional, not ENOB' if cid=='sram_acim' else '25-bit nominal exact digital mapping; no STA/silicon signoff')
  resources={k:r[k] for k in ('banks','physical_rows','physical_cols','physical_bank_rows','adc_count','output_bits','fractional_output_bits') if k in r}
  resources['logical_shape']=[r['K'],r['N']]
  conditions=list(dict.fromkeys(r['conditions']+review['qualification_conditions'].get(origin,[])+review['qualification_conditions']['common']))
  points.append({'generation':'V4','case_id':cid,'historical_case_id':origin,'implementation_id':'V4_'+origin,'config_id':r['paired_id'],'scenario':r['scenario'],'status':r['status'],'review_status':review['status'],'accepted':True,'plot_eligible':True,
   'K':r['K'],'N':r['N'],'bytes_per_input':1,'bytes_per_weight':1,'B_S_Byte':r['B_S_Byte'],'B_R_Byte':r['B_R_Byte'],'precision_qualification':precision,
   'implementation_identity':{'hardware':origin,'qualification':r['qualification'],'historical_identity_preserved':True},'backend_locks':{r['backend']:r['backend_sha']},'technology_nm':r['technode_nm'],'temperature_K':r['temperature_K'],
   'range_meaning':summary['scenario_definition']['interpretation']+'; '+summary['scenario_definition']['reference_meaning'],
   'single_stream_latency_s':r['single_latency_ns']*1e-9,'raw_stream_interval_s':ds,'effective_stream_interval_s':ds,'single_resident_latency_s':tr,'raw_resident_service_s':tr,'effective_resident_interval_s':tr,
   'rate_basis':'serial nonoverlap; historical V4, no periodic maintenance','rho_MB_per_s':r['rho_MB_per_s'],'tau_MB_per_s':r['tau_MB_per_s'],'RI_star':r['RI_star'],'U_star':r['U_star'],'raw_rho_MB_per_s':r['rho_MB_per_s'],'raw_tau_MB_per_s':r['tau_MB_per_s'],
   'model_source_classes':['native_circuit','adapter','external_primitive','service_policy'],'main_resources':resources,'qualification':r['qualification'],'conditions':conditions,'maintenance_summary':None,
   'computational_snapshot_sha256':None,'historical_result_sha256':sha(run/origin/r['scenario']/'result.json'),'historical_native_manifest_sha256':sha(run/origin/r['scenario']/'source_manifest.json'),'review_binding':{'read_only_historical_review':str(reviewpath),'review_sha256':sha(reviewpath)},'run_directory':str(run/origin/r['scenario'])})
 return points,{'V4_summary':{'path':str(source),'sha256':sha(source)},'V4_review':{'path':str(reviewpath),'sha256':sha(reviewpath)},'V4_qualification':{'path':str(qualification),'sha256':sha(qualification)}}
def legacy_background(path,out,current):
 data=json.loads(path.read_text());rows=[]
 category={'01':'sram_acim','02':'sram_dcim','03':'nor2d','04':'nand3d','05':'rram','06':'mram','07':'pcm','08':'feram','09':'gc04','10':'fenor3d'}
 for r in data['results']:
  if not r.get('recommended'):continue
  native=r['native_configuration'];matches=[x for x in current if x['case_id']==category[r['case_id'][:2]] and x['scenario']=='reference'];new=matches[0] if matches else None
  rows.append({'generation':'old_NVM_background_only','case_id':r['case_id'],'technology':r['technology'],'K':r['K'],'N':r['N'],'mode':r['mode'],'rho_MB_per_s':r['rho'],'tau_MB_per_s':r['tau'],'RI_star':r['RI_star'],'U_star':r['U_star'],'single_stream_ns':r['raw_service_time']['streaming_ns'],'effective_stream_ns':r['effective_service_interval']['streaming_ns'],'effective_resident_ns':r['effective_service_interval']['resident_ns'],'native_configuration':native,'service_record':{k:v for k,v in r.items() if any(x in k.lower() for x in ('rho','tau','ridge','eligib','status','service','load'))},'new_reference':None if new is None else {k:new.get(k) for k in ('generation','implementation_id','config_id','K','N','status','accepted','precision_qualification','implementation_identity','rho_MB_per_s','tau_MB_per_s','RI_star','U_star','rate_basis')},'qualification':'Historical architecture/precision/range differ; no uniform tool-correction ratio and no input to V5 computation'})
 write_json(out/'legacy_background.json',{'source':str(path),'sha256':sha(path),'scope':'separate optional historical context only','records':rows});rows_csv(out/'legacy_background.csv',rows)
def main():
 own=Path(__file__).resolve().parent;p=argparse.ArgumentParser(description=__doc__);p.add_argument('--v5-points',required=True,type=Path);p.add_argument('--output-dir',required=True,type=Path);p.add_argument('--v4-root',type=Path,default=own.parent/'step4_v4');p.add_argument('--legacy-background',type=Path);a=p.parse_args()
 out=a.output_dir.absolute()
 if out.exists() or any(x.is_symlink() for x in (out,*out.parents)):raise ValueError('New non-symlink comparison directory required')
 dataset=json.loads(a.v5_points.read_text());current=dataset['points']
 if any(r.get('generation')!='V5' for r in current):raise ValueError('Expected V5-only point table')
 prior,sources=historical(a.v4_root.resolve());combined=current+prior
 if len({r['config_id'] for r in combined})!=len(combined):raise ValueError('Duplicate config ID')
 out.mkdir(parents=True,exist_ok=False);sources['V5_points']={'path':str(a.v5_points.resolve()),'sha256':sha(a.v5_points)}
 result={'units':dataset['units'],'scope':'Read-only V4 nine points + current V5 paired points; different range/precision/architecture semantics remain explicit','range_layers':{'V4':'300/350/400K, fixed architecture with native resizing; not same-chip PVT','V5':'case-specific finite device/protocol/operating scenarios; GC long-term event-scheduled rates'},'sources':sources,'points':combined,'case_records':dataset.get('case_records',[]),'execution_failures':dataset.get('execution_failures',[]),'plot_eligible_points':sum(r.get('plot_eligible',False) for r in combined)}
 write_json(out/'combined_points.json',result);rows_csv(out/'combined_points.csv',combined)
 if a.legacy_background:legacy_background(a.legacy_background.resolve(),out,combined)
 write_json(out/'comparison_provenance.json',{'sources':sources,'original_V4_values_recomputed':False,'original_V4_identity_or_qualification_changed':False,'V4_in_compute_dependencies':False,'legacy_background_separate':bool(a.legacy_background),'script_sha256':sha(Path(__file__))})
 print(json.dumps({'output_directory':str(out),'V4_historical_points':len(prior),'V5_points':len(current),'plot_eligible_points':result['plot_eligible_points']}))
if __name__=='__main__':main()
