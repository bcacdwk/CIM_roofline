#!/usr/bin/env python3
"""Recompute SRAM ACIM from shared API. Default read-only; --emit refreshes results/TeX."""
import argparse,hashlib,importlib.util,json,math,random,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
B=Path(__file__).resolve().parents[1]; SH=B.parent/'shared_baseline'; C=B.parents[1]
spec=importlib.util.spec_from_file_location('shared',SH/'scripts/check_shared.py'); S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
D=json.loads((B/'data/inputs.json').read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def block(t,count=1):return S.program_sequence_ns(0,0,[dict(count=count,drive_program_ns=t,verify_ns=0,recover_ns=0)])
def calculate(profile,tf,tm,parallel=None):
 v=S.C['propagation']['profile_values'][profile]; a={**S.R['acim'],**D['acim_overrides']}
 residual=tf-v['input_step']; assert residual>=0
 ds,n,hold=S.acim_service(a,v,residual)
 x={**D['update_geometry'],'complete_physical_update_ns':tm}
 if parallel is not None:x['parallel_cells']=parallel
 br,uncollapsed,batches,beats=S.direct_service(x,v['digital_tick'])
 front,_=S.front_ns(x['encoded_load_bits'],v['digital_tick'],x['first_data_in_command'])
 dr=block(tm,batches)
 stages=dict(streaming=[dict(stage='reset_input_array_frontend',count=n['evaluations'],each_ns=tf,total_ns=n['evaluations']*tf),dict(stage='complete_SAR_batch',count=n['adc_batches'],each_ns=v['adc_batch'],total_ns=n['adc_batches']*v['adc_batch']),dict(stage='digital_reconstruction',count=n['digital_ticks'],each_ns=v['digital_tick'],total_ns=n['digital_ticks']*v['digital_tick']),dict(stage='input_capture_output_commit',count=a['boundary_ticks'],each_ns=v['digital_tick'],total_ns=a['boundary_ticks']*v['digital_tick'])],resident=[dict(stage='complete_synchronous_ordinary_write',count=batches,each_ns=tm,total_ns=dr)],replaced_shared_front_ns=front,uncollapsed_direct_template_ns=uncollapsed,extra_write_handshake_ns=0)
 return dict(common_profile=profile,mode='binary_charge_domain_approximate_BPBS',mapping_id='8_planes_128x128_R0',counts=n,frontend_complete_ns=tf,engineering_read_residual_ns=residual,common_times_ns=v,complete_memory_cycle_ns=tm,write_batches=batches,write_data_beats=beats,parallel_write_cells=x['parallel_cells'],hold_extra_ns=hold,stage_coverage=stages,streaming_dominant=max(stages['streaming'],key=lambda x:x['total_ns'])['stage'],resident_dominant='ordinary synchronous write',sources=['E01','E02','E04','E06','E07','E09','E10'],**S.metrics(S.L['B_S_Byte'],br,ds,dr))
def compute():
 rows=[dict(id=x['id'],label=x['label'],**calculate(x['common_profile'],x['frontend_complete_ns'],x['complete_memory_cycle_ns'])) for x in D['scenarios']]
 r=rows[1]; sens=[]
 for tf in D['sensitivities']['frontend_at_reference_ns']:
  q=calculate('reference',tf,r['complete_memory_cycle_ns']);sens.append(dict(id=f'frontend_{tf}',kind='frontend_at_fixed_reference_periphery',rho_ratio_to_reference=q['rho_Byte_per_s']/r['rho_Byte_per_s'],**q))
 q=calculate('reference',r['frontend_complete_ns'],r['complete_memory_cycle_ns'],D['sensitivities']['write_resource_parallel_cells']);sens.append(dict(id='64_write_drivers',kind='actual_write_resource_comparison',**q))
 ranges={k:[min(x[k] for x in rows),max(x[k] for x in rows)] for k in ['delta_S_ns','delta_R_ns','rho_Byte_per_s','tau_Byte_per_s','ridge']}
 ranges['independent_endpoint_ridge_envelope']=[ranges['rho_Byte_per_s'][0]/ranges['tau_Byte_per_s'][1],ranges['rho_Byte_per_s'][1]/ranges['tau_Byte_per_s'][0]]
 return dict(analysis_id=D['analysis_id'],baseline_id=S.D['baseline_id'],status='conditional_reference_estimate_not_measured_paired_chip',units=dict(payload='Byte',time='ns',throughput='Byte/s',ridge='dimensionless'),baseline_files_actual={f:sha(SH/f) for f in D['baseline_files']},mapping=D['device_state_and_mapping'],scenarios=rows,sensitivities=sens,ranges=ranges,whole_matrix_updates=[dict(profile=r['id'],logical_payload_Byte=S.L['resident_capacity_Byte'],transactions=S.L['resident_capacity_Byte']//r['B_R_Byte'],delta_R_ns=(S.L['resident_capacity_Byte']//r['B_R_Byte'])*r['delta_R_ns'],tau_Byte_per_s=r['tau_Byte_per_s']) for r in rows])
def table(rows,sens=False):
 if not sens:
  head=r'情景 & $T_F$ & $T_A$ & $T_D$ & $\Delta_S$ & $\Delta_R$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$';cols='lrrrrrrrr'
  body=[f"{r['label']} & {r['frontend_complete_ns']:g} & {r['common_times_ns']['adc_batch']:g} & {r['common_times_ns']['digital_tick']:g} & {r['delta_S_ns']:g} & {r['delta_R_ns']:g} & {r['rho_Byte_per_s']/1e9:.4g} & {r['tau_Byte_per_s']/1e9:.4g} & {r['ridge']:.5f}"+r'\\' for r in rows]
  caption='成对工程情景。所有时间为ns，吞吐为十进制GB/s；有效逻辑粒度固定为$B_S=128$ Byte、$B_R=16$ Byte。'
 else:
  head=r'条件 & $\Delta_S$ (ns) & $\Delta_R$ (ns) & $\rho$ (GB/s) & $\tau$ (GB/s) & $\mathrm{RI}^{*}$';cols='lrrrrr';body=[]
  for r in rows:
   label=(f"前端 {r['frontend_complete_ns']:g} ns" if r['kind'].startswith('frontend') else '64个实际写驱动')
   body.append(f"{label} & {r['delta_S_ns']:g} & {r['delta_R_ns']:g} & {r['rho_Byte_per_s']/1e9:.4g} & {r['tau_Byte_per_s']/1e9:.4g} & {r['ridge']:.5f}"+r'\\')
  caption='固定共同参考外围的敏感性。前三行仅改前端预算；末行保持20ns前端，但写驱动减半、两个完整同步写槽完成同一16Byte事务。'
 return '\n'.join([r'% Generated; do not edit.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}'+cols+r'@{}}\toprule',head+r'\\\midrule',*body,r'\bottomrule\end{tabular}',r'\caption{'+caption+r'}\end{table}'])+'\n'
def evidence():
 a=['# SRAM ACIM 证据表','','页码均为本地PDF页序，原值与工程采用值分开。由 inputs.json 生成；解释及手算见 method_review.zh.md。','','|编号/来源/定位|原值与单位|条件与性质|采用及桥接|','|---|---|---|---|']
 for e in D['raw_evidence']:a.append('| '+' | '.join([f"{e['id']} / {e['source_id']} / {e['locator']}",e['parameter']+'：'+e['original_value']+' ['+e['unit']+']',e['conditions']+'；'+e['kind'],e['adopted']+'；'+e['conversion_reason']])+' |')
 return '\n'.join(a)+'\n'
def generated():
 r=compute();return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','tex/generated_results.tex':table(r['scenarios']),'tex/generated_sensitivity.tex':table(r['sensitivities'],True),'notes/evidence.zh.md':evidence()}
class Checks(unittest.TestCase):
 def test_shared_and_source_hashes(self):
  for f,h in D['baseline_files'].items():self.assertEqual(sha(SH/f),h,f)
  self.assertEqual(sha(C/'source_manifest.json'),D['source_manifest_sha256'])
  for sid,x in D['sources'].items():self.assertEqual(sha(C/x['pdf']['path']),x['pdf']['sha256'],sid)
 def test_mapping_capacity_and_write_resources(self):
  m=D['device_state_and_mapping'];w=D['write_resources'];g=D['update_geometry']
  self.assertEqual(m['weight_planes']*m['physical_rows_per_plane']*m['physical_columns_per_plane'],S.L['resident_capacity_Byte']*8)
  self.assertEqual(w['write_driver_pairs_per_plane']*w['active_planes'],g['parallel_cells'])
  self.assertEqual(g['logical_weights_completed']*m['cells_per_weight'],g['encoded_load_bits'])
  self.assertEqual(m['independent_service_units'],1);self.assertEqual(m['write_domains'],1)
 def test_exact_logical_coverage(self):
  n=S.acim_counts(S.R['acim']);seen=set()
  for bit in range(8):
   for group in range(8):
    for weight in range(8):
     for out in range(group*16,(group+1)*16):
      key=(bit,weight,out);self.assertNotIn(key,seen);seen.add(key)
  self.assertEqual(len(seen),n['useful_scalar_conversions']);self.assertEqual(len(seen),8192)
  self.assertEqual(n['evaluations'],64);self.assertEqual(n['adc_batches'],64);self.assertEqual(n['digital_ticks'],128)
 def test_signed_reconstruction_contract(self):
  rng=random.Random(7);c=[1,2,4,8,16,32,64,-128]
  for mode in ['random','extreme']:
   x=[rng.randrange(-128,128) for _ in range(128)] if mode=='random' else [-128]*128
   for o in range(8):
    w=[rng.randrange(-128,128) for _ in range(128)] if mode=='random' else [-128 if o%2==0 else 127]*128
    exact=sum(a*b for a,b in zip(x,w));recon=sum(c[u]*c[k]*sum(((a&255)>>u&1)*((b&255)>>k&1) for a,b in zip(x,w)) for u in range(8) for k in range(8))
    self.assertEqual(exact,recon);self.assertLess(abs(exact),2**23)
 def test_stage_coverage_and_hand_arithmetic(self):
  rr=compute()['scenarios'];expected=[1540,3210,7700]
  for r,ds in zip(rr,expected):
   self.assertEqual(r['delta_S_ns'],ds);self.assertEqual(sum(x['total_ns'] for x in r['stage_coverage']['streaming']),ds)
   self.assertEqual(sum(x['total_ns'] for x in r['stage_coverage']['resident']),r['delta_R_ns'])
   self.assertEqual(r['frontend_complete_ns'],r['common_times_ns']['input_step']+r['engineering_read_residual_ns'])
   self.assertEqual(r['delta_R_ns'],r['complete_memory_cycle_ns']);self.assertEqual(r['hold_extra_ns'],0)
   self.assertEqual(r['stage_coverage']['uncollapsed_direct_template_ns']-r['stage_coverage']['replaced_shared_front_ns'],r['delta_R_ns'])
   self.assertAlmostEqual(r['ridge'],8*r['delta_R_ns']/ds)
  r=rr[1];self.assertAlmostEqual(r['rho_Byte_per_s']/1e9,128/3210);self.assertAlmostEqual(r['tau_Byte_per_s']/1e9,3.2)
 def test_sensitivities_and_aggregation(self):
  r=compute();ss=r['sensitivities'];self.assertEqual([x['delta_S_ns'] for x in ss],[2570,3210,5130,3210]);self.assertEqual(ss[-1]['write_batches'],2);self.assertEqual(ss[-1]['delta_R_ns'],10)
  for x in r['whole_matrix_updates']:
   self.assertEqual(x['transactions'],1024);self.assertAlmostEqual(x['logical_payload_Byte']/(x['delta_R_ns']*1e-9),x['tau_Byte_per_s'])
 def test_generated_readonly_contract(self):
  for f,s in generated().items():self.assertEqual((B/f).read_text(),s,f)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--emit',action='store_true');args=p.parse_args()
 if args.emit:
  for f,s in generated().items():(B/f).write_text(s)
 result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks));raise SystemExit(not result.wasSuccessful())
