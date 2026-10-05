"""Independent finalexecution/table/geometry audit. No productionimports."""
import argparse,collections,csv,hashlib,json,math,pathlib,re,xml.etree.ElementTree as ET
CASES={'pcm','mram','nor2d','fenor3d','feram','gc04','nand3d'}
SCENARIOS={'optimistic','reference','pessimistic'}

def read(p):return json.loads(pathlib.Path(p).read_text())
def sha(p):return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()
def close(a,b):return math.isclose(a,b,rel_tol=2e-10,abs_tol=1e-15)

def execution(manifest,summary,management):
 m=read(manifest);s=read(summary);root=pathlib.Path(management);pkg=pathlib.Path(m['package_path']);rs=s['results'];groups=collections.defaultdict(set)
 assert len(rs)==21 and len({r['config_id'] for r in rs})==21 and len({r['run_directory'] for r in rs})==21
 assert not s['execution_failures']
 assert sha(summary)==m['summary_sha256']
 assert sha(pkg/'PACKAGE_MANIFEST.json')==m['package_manifest_sha256']
 assert {r['case_id'] for r in rs}==CASES
 mr={x['config_id']:x for x in m['point_runs']};details=[];files_checked=set();native_dirs=[]
 for r in rs:
  groups[r['case_id']].add(r['scenario']);assert r['status']=='conditional' and not r['critical_failures']
  assert r['computational_snapshot_sha256']==m['case_computational_hashes'][r['case_id']]==mr[r['config_id']]['computational_snapshot_sha256']
  assert str(r['run_directory'])==mr[r['config_id']]['run_directory']
  rt=pathlib.Path(r['run_directory']);actual=read(rt/'result.json');assert actual['config_id']==r['config_id'] and actual['computational_snapshot_sha256']==r['computational_snapshot_sha256']
  cm=r['computational_hashes'];assert hashlib.sha256(json.dumps(cm,sort_keys=True).encode()).hexdigest()==r['computational_snapshot_sha256']
  for rel,h in cm.items():
   for base in (root,pkg,rt/'canonical'):
    f=base/rel;assert f.is_file() and not f.is_symlink();assert sha(f)==h;files_checked.add(str(f))
  bi=r['logical']['bytes_per_input'];bw=r['logical']['bytes_per_weight'];assert r['B_S_Byte']==r['K']*bi and r['B_R_Byte']==r['K']*r['N']*bw
  ds=r.get('delta_S_effective_s',r['delta_S_raw_s']);tr=r.get('resident_effective_interval_s',r['resident_s'])
  assert min(ds,tr,r['rho_MB_per_s'],r['tau_MB_per_s'])>0
  assert close(r['rho_MB_per_s'],r['B_S_Byte']/ds/1e6) and close(r['tau_MB_per_s'],r['B_R_Byte']/tr/1e6)
  assert close(r['RI_star'],r['rho_MB_per_s']/r['tau_MB_per_s']) and close(r['U_star'],tr/ds)
  assert close(r['U_star'],r['N']*bw/bi*r['RI_star'])
  if r['case_id']=='gc04':
   q=r['maintenance'];assert q['feasible'] and q['max_group_writeback_gap_s']<=q['retention_limit_s']
   assert ds>r['delta_S_raw_s'] and tr>r['resident_raw_s']
   assert close(r['single_latency_s'],q['single_admitted_stream_latency_s'])
  paths=[pathlib.Path(v['run_directory']) for v in r.get('component_bindings',{}).values()]
  if r.get('native_run_directory'):paths.append(pathlib.Path(r['native_run_directory']))
  for n in paths:
   assert (n/'source_manifest.json').is_file() and (n/'build.log').is_file()
   assert not n.is_symlink() and '/CloudStorage/' not in str(n)
   native_dirs.append(str(n))
  details.append({'config_id':r['config_id'],'case_id':r['case_id'],'scenario':r['scenario'],'computational_snapshot_sha256':r['computational_snapshot_sha256'],'rho_MB_per_s':r['rho_MB_per_s'],'tau_MB_per_s':r['tau_MB_per_s'],'rate_basis':'effectiveactualschedule' if r['case_id']=='gc04' else 'serialnonoverlap'})
 assert all(v==SCENARIOS for v in groups.values())
 assert len(set(native_dirs))==len(native_dirs)
 forbidden=[]
 for f in pkg.rglob('*'):
  assert not f.is_symlink()
  if f.is_file() and (f.name in {'result.json','summary.json','candidate_points.json','reference_snapshot.json','summary.csv'} or any(x in ('step4_v4','legacy','replay','results') for x in f.relative_to(pkg).parts)):forbidden.append(str(f))
 assert not forbidden
 return {'status':'PASS_final_execution_snapshot_only','formal_table_and_visual_review':'pendingfinalexport','point_count':21,'cases':7,'one_each_scenario_per_case':True,'unique_actual_native_build_directories':len(native_dirs),'file_hash_comparisons_unique_paths':len(files_checked),'exact_management_package_runtime_hash_binding':True,'old_results_or_replay_in_compute_package':False,'final_execution_failures':0,'initial_packaging_failures_retained':s['initial_packaging_failures'],'allrates_decimal_MB_s':True,'rho_tau_RI_U_independently_recomputed':True,'GC_effective_not_single_latency':True,'points':details,'manifest_sha256':sha(manifest),'summary_sha256':sha(summary)}


def final_tables(points_path,combined_path,v4_summary):
 data=read(points_path);combined=read(combined_path);points=data['points'];allpoints=combined['points']
 assert len(points)==21 and len(allpoints)==30
 assert len({r['config_id'] for r in allpoints})==30
 assert len({r['implementation_id'] for r in allpoints})==10
 assert len([r for r in allpoints if r['generation']=='V4'])==9
 assert all(r['accepted'] and r['plot_eligible'] for r in allpoints)
 assert {r['case_id'] for r in points}==CASES
 byid={r['config_id']:r for r in points}
 for r in allpoints:
  if r['generation']=='V5':
   assert r==byid[r['config_id']]
   assert r['review_binding']['computational_snapshot_sha256']==r['computational_snapshot_sha256']
   assert r['review_status'].startswith('PASS')
  bs=r['B_S_Byte'];br=r['B_R_Byte'];ds=r['effective_stream_interval_s'];tr=r['effective_resident_interval_s']
  assert close(r['rho_MB_per_s'],bs/ds/1e6) and close(r['tau_MB_per_s'],br/tr/1e6)
  assert close(r['RI_star'],r['rho_MB_per_s']/r['tau_MB_per_s']) and close(r['U_star'],tr/ds)
  assert r['precision_qualification'] and r['range_meaning'] and r['backend_locks']
  if r['case_id']=='gc04':
   assert r['rate_basis']=='long-term event schedule' and r['maintenance_summary']['feasible']
   assert r['effective_stream_interval_s']>r['single_stream_latency_s']
   assert r['effective_resident_interval_s']>r['raw_resident_service_s']
 old={r['paired_id']:r for r in read(v4_summary)['case_results']}
 for r in allpoints:
  if r['generation']=='V4':
   before=old[r['config_id']]
   for k in ('rho_MB_per_s','tau_MB_per_s','RI_star','U_star','K','N','B_S_Byte','B_R_Byte','status'):assert r[k]==before[k]
   assert r['temperature_K']==before['temperature_K']
 assert 'not same-chip PVT' in combined['range_layers']['V4']
 for path,key in ((points_path,'points'),(combined_path,'combined_points')):
  csvpath=pathlib.Path(path).with_suffix('.csv');rows=list(csv.DictReader(csvpath.open()));expected=read(path)['points']
  assert len(rows)==len(expected)
  lookup={r['config_id']:r for r in expected}
  for row in rows:
   target=lookup[row['config_id']]
   for field in ('rho_MB_per_s','tau_MB_per_s','RI_star','U_star'):assert close(float(row[field]),target[field])
 return {'status':'PASS_table_units_identity_pairing','V5_configs':21,'combined_configs':30,'classes':10,'V4_exact_original_values':True,'V5_review_hash_bound':True,'GC_effective_basis_separate_from_latency':True,'CSV_JSON_consistent':True,'V4_V5_range_semantics_explicit':True,'source_hashes':{'points':sha(points_path),'combined':sha(combined_path),'V4_summary':sha(v4_summary)}}

def svg_decades(path):
 ns={'s':'http://www.w3.org/2000/svg'};root=ET.parse(path).getroot();coords={}
 for axis,prefix,coordinate in ((1,'xtick_',0),(2,'ytick_',1)):
  parent=next(g for g in root.iter('{http://www.w3.org/2000/svg}g') if g.get('id')=='matplotlib.axis_'+str(axis))
  values=[]
  for tick in parent.findall('s:g',ns):
   if not tick.get('id','').startswith(prefix) or not tick.findall('.//s:text',ns):continue
   for elem in tick.findall('.//s:path',ns):
    d=elem.get('d','');match=re.match(r'M\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)\s+L\s+([-+0-9.eE]+)\s+([-+0-9.eE]+)',d)
    if match:
     x,y,x2,y2=map(float,match.groups())
     if (axis==1 and abs(x-x2)<1e-8 and abs(y-y2)>20) or (axis==2 and abs(y-y2)<1e-8 and abs(x-x2)>20):values.append((x,y)[coordinate]);break
  values=sorted(set(values));deltas=[b-a for a,b in zip(values,values[1:])]
  assert len(deltas)>=1
  assert max(deltas)-min(deltas)<1e-4
  coords[axis]=sum(deltas)/len(deltas)
 assert math.isclose(coords[1],coords[2],rel_tol=2e-6,abs_tol=1e-4)
 return {'SVG_major_grid_points_per_decade':[coords[1],coords[2]],'independent_equal_log_decades':True}

def geometry(geometry_path,points_path):
 g=read(geometry_path);points=read(points_path)['points'];byid={r['config_id']:r for r in points};group=collections.defaultdict(list)
 assert g['source_sha256']==sha(points_path) and not g['preview_only']
 for r in points:group[r['implementation_id']].append(r)
 results=[];folder=pathlib.Path(geometry_path).parent
 for fig in g['figures']:
  assert len(fig['points'])==len(points) and fig['eligible_points']==len(points)
  for q in fig['points']:
   original=byid[q['config_id']]
   assert q['rho_MB_per_s']==original['rho_MB_per_s'] and q['tau_MB_per_s']==original['tau_MB_per_s']
  lo,hi=fig['log10_limits']
  for c in fig['envelopes']:
   cx,cy=c['center_log10'];r=c['radius_decades']
   for point in group[c['implementation_id']]:
    distance=math.hypot(math.log10(point['tau_MB_per_s'])-cx,math.log10(point['rho_MB_per_s'])-cy)
    assert distance<=r+1e-10
   assert lo[0]<=cx-r+1e-12 and cx+r<=hi[0]+1e-12 and lo[1]<=cy-r+1e-12 and cy+r<=hi[1]+1e-12
   if c['case_id']=='fenor3d':assert r<=1e-12 and c['rule']=='minimum_enclosing_point'
  for ext,h in fig['outputs'].items():assert sha(folder/(fig['stem']+'.'+ext))==h
  vector=svg_decades(folder/(fig['stem']+'.svg'))
  results.append({'figure':fig['stem'],'point_coordinates_exact':True,'points':len(fig['points']),'all_reference_and_endpoint_centres_enclosed':True,'full_circle_boundaries_within_axes':True,'label_layout_penalties':[x['layout_penalty'] for x in fig['labels']],**vector})
 return {'status':'PASS_independent_geometry_SVG_checks','figures':results,'geometry_sha256':sha(geometry_path),'visual_PNG_review':'pendinghuman-modelview'}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--manifest');p.add_argument('--summary');p.add_argument('--management');p.add_argument('--points');p.add_argument('--combined');p.add_argument('--v4-summary');p.add_argument('--geometry',nargs='*');p.add_argument('--out',required=True);a=p.parse_args()
 d={}
 if a.manifest:d['execution']=execution(a.manifest,a.summary,a.management)
 if a.points and a.combined:d['tables']=final_tables(a.points,a.combined,a.v4_summary)
 if a.geometry:
  d['geometry']=[geometry(x,a.points if read(x)['figures'][0]['eligible_points']==21 else a.combined) for x in a.geometry]
 pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'out':a.out,'sections':list(d)}))
