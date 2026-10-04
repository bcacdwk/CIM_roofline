"""Reviewer-only independent audit; does not import production calculation code."""
import sys,json,math,hashlib,pathlib
root=pathlib.Path(sys.argv[1]);repo=root/'snapshot';task=repo/'tasks/task1_table_I_NeuroSim'
summary=json.loads((root/'summary.json').read_text());rows=[]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def pointer(o,p):
 for part in p.strip('/').split('/'):
  part=part.replace('~1','/').replace('~0','~');o=o[int(part)] if isinstance(o,list) else o[part]
 return o
for row in summary['case_results']:
 cid=row['case_id'];c=json.loads((task/'configs/cases'/f'{cid}.json').read_text());result=json.loads((root/cid/'result.json').read_text());resolved=json.loads((root/cid/'resolved.json').read_text())
 checks={};sources={}
 for k,x in c['provenance']['sources'].items():
  if isinstance(x,dict) and 'path' in x:
   sources[k]=json.loads((repo/x['path']).read_text()) if x['path'].endswith('.json') else None
   checks['source_hash_'+k]=sha(repo/x['path'])==x['sha256']
 units={'ns':1e-9,'us':1e-6,'ms':1e-3,'nA':1e-9,'uA':1e-6,'pF':1e-12,'fF':1e-15,'V':1,'A':1,'s':1,'F':1}
 for q in c['device']['primitives']:
  for ref in q['source_refs']:
   value=pointer(sources[ref['source_id']],ref['json_pointer'])
   if isinstance(value,(int,float)):
    checks['primitive_source_'+q['id']]=math.isclose(value,q['original']['value'],rel_tol=1e-12,abs_tol=1e-12)
  checks['primitive_units_'+q['id']]=math.isclose(q['normalized']['value'],q['original']['value']*units[q['original']['unit']],rel_tol=1e-12,abs_tol=1e-20)
 l=c['logical'];P=result['clocks'][0]['actual_period_ns'];S=result['streaming']['delta_S_ns'];R=result['resident_load']['T_R_ns'];alpha=result['maintenance'].get('availability',1.)
 checks['logical_payload']=l['B_S_Byte']==l['K']*l['bytes_per_input'] and l['B_R_Byte']==l['K']*l['N']*l['bytes_per_weight']
 expected={'rho_Byte_per_s':l['B_S_Byte']*1e9/S*alpha,'tau_Byte_per_s':l['B_R_Byte']*1e9/R*alpha,'RI_star':l['B_S_Byte']/l['B_R_Byte']*R/S,'U_star':R/S}
 for k,v in expected.items():checks['metric_'+k]=math.isclose(result['derived_metrics'][k],v,rel_tol=2e-12)
 checks['same_policy_RI_U']=math.isclose(expected['U_star'],expected['RI_star']*l['B_R_Byte']/l['B_S_Byte'],rel_tol=1e-12)
 vals={}
 if cid not in {'01_sram_acim','02_sram_dcim','05_rram'}:
  b=resolved['backend'];M=b['boundary_setup_ns'];adc=b['sar_ns'];ceil=lambda n:math.ceil(n/P-1e-10)
  checks['single_cycle_only']=all(p['available_cycles']==1 and p['single_cycle'] for p in b['paths'])
  checks['legal_policy']=P==math.ceil(max(5.,max(p['delay_ns'] for p in b['paths']))*2-1e-10)/2
  manifest=json.loads((root/cid/'backend/source_manifest.json').read_text())
  checks['backend_version']=manifest['backend_sha']=='8a88abf85844c0e1ba17cc771ea535fff6040456'
  checks['unused_cell_context']=all(not x['MemCell_field_reads_in_complete_cpp'] for x in manifest['MemCell_use_audit'].values())
  checks['no_subarray']=b['coverage']['SubArray_used'] is False and b['coverage']['array_or_device_material_simulated'] is False
  checks['raw_aggregate_write_null']=result['resident_load']['normalized_missing_backend_write']['value'] is None
  checks['actual_module_execution']=b['raw_module_returns']['same_graph_arithmetic_fixtures']>0
  if cid=='03_nor_2d':
   ss=(2+32*(ceil(120+M)+9))*P;rr=4*(2+ceil(45000000+M)+16*(18+ceil(400000+M)))*P
  elif cid=='04_nand_3d':
   ss=(290+30*(ceil(303+652+adc+M)+4+31*(ceil(652+adc+M)+4)))*P
   rr=(ceil(64000000+M)+240*(288+24*(290+ceil(300000+M)))+384*(110+ceil(300000+M))+2*ceil(303+652+adc+M)+10*ceil(652+adc+M)+450)*P
   checks['NAND_capacity_and_pages']=c['physical']['physical_capacity_bit']==13824*32*3*64==84934656 and c['resources']['active']['resident']['data_pages']==5760 and c['resources']['active']['resident']['reference_pages']==384
   checks['NAND_arithmetic_remains_unverified']=not b['coverage']['full_arithmetic_paths'] and len(b['coverage']['retained_unverified_arithmetic'])==2
  elif cid=='06_mram':
   ss=(2+16*(ceil(5+M)+9))*P;rr=1024*(7+ceil(30+M)+ceil(35+M)+ceil(5+M))*P
  elif cid=='07_pcm':
   ss=(2+2048*(ceil(20+adc+M)+2))*P;rr=1024*(3+8*(3+ceil(485+20+adc+M)+ceil(20+adc+M)))*P
   checks['PCM_mode_pair_SAR']=sum(s['count'] for s in result['stages'] if s['provider']=='neurosim_native' and s['service_kind']=='resident')==16384
  elif cid=='08_feram_hfo2':
   ss=(2+32*(ceil(110)+8))*P;rr=1024*(2+ceil(140+M))*P
   checks['FeRAM_no_extra_capture']=all(s['stage_id']!='operand_capture' for s in result['stages'])
   dr=sources['inputs']['drive_resources'];demand=dr['BL_capacitance_fF']*dr['memory_voltage_V']/dr['edge_each_ns']['reference']
   checks['FeRAM_native_BL_rating_only']=demand<=dr['BL_installed_rating_uA'] and math.isclose(demand*dr['restore_BL_drivers']/1000,128.)
   checks['FeRAM_PL_gap_preserved']='unvalidated' in resolved['adapter']['qualification_gap']
  elif cid=='09_gain_cell_edram':
   batch=(ceil(92+adc+M)+2)*P;tx=(3+ceil(65+M))*P;ss=2*P+32*batch;rr=256*tx
   busy=256*(ceil(155+adc+M)+4+ceil(65+M))*P;guard=max(batch,tx);a=(400000-busy-guard)/400000
   checks['GC_maintenance']=math.isclose(result['maintenance']['busy_ns'],busy,rel_tol=1e-12) and math.isclose(result['maintenance']['guard_ns'],guard,rel_tol=1e-12)
   checks['GC_feasible_actual_schedule']=busy+guard<400000 and math.isclose(alpha,a,rel_tol=1e-12)
   checks['GC_payload_zero']=result['maintenance']['workload_write_Byte']==0
   checks['GC_mean_not_physical']=math.isclose(result['streaming']['effective_service_cost_ns'],S/alpha,rel_tol=1e-12) and math.isclose(result['resident_load']['effective_service_cost_ns'],R/alpha,rel_tol=1e-12)
   vals.update(independent_busy_ns=busy,independent_guard_ns=guard,independent_alpha=a)
  elif cid=='10_fenor_3d':
   ss=(2+32*(ceil(40+M)+9))*P;rr=1024*(11+ceil(210+M))*P
   dr=sources['inputs']['engineering_driver_budget'];demand=dr['maximum_effective_capacitance_per_driven_node_fF']*dr['worst_swing_V']/10
   checks['FeNOR_native_driver_rating']=demand<=dr['installed_slew_current_uA_per_node'] and demand*288/1000<=dr['installed_supply_current_mA'] and dr['installed_nodes']==288
   vals['independent_native_node_current_uA']=demand
  checks['independent_ordered_formula_S']=math.isclose(ss,S,rel_tol=2e-12,abs_tol=3e-5)
  checks['independent_ordered_formula_R']=math.isclose(rr,R,rel_tol=2e-12,abs_tol=3e-5)
  vals.update(independent_S_ns=ss,independent_R_ns=rr,period_ns=P,setup_ns=M)
 else:
  accepted=json.loads((task/'results/step3_v2/integration-audited-v2'/cid/'result.json').read_text())
  checks['pilot_full_accepted_result_identical']=result==accepted
 rows.append(dict(case_id=cid,status='PASS' if all(checks.values()) else 'FAIL',checks=checks,independent_metrics=expected,**vals))
manifest=json.loads((root/'snapshot_manifest.json').read_text());snapshot_checks={p:sha(repo/p)==s for p,s in manifest.items()}
out={'status':'PASS' if all(r['status']=='PASS' for r in rows) and all(snapshot_checks.values()) else 'FAIL','method':'Reviewer-only direct formulas and source pointers; no import of engine, adapters, legacy_replay or native calculators','run':str(root),'case_checks':rows,'snapshot_hash_checks':snapshot_checks,'snapshot_file_count':len(manifest)}
(root/'review_independent.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':out['status'],'failures':{r['case_id']:[k for k,v in r['checks'].items() if not v] for r in rows if r['status']!='PASS'},'snapshot_files':len(manifest)},ensure_ascii=False))
