import copy,hashlib,importlib.util,json,math,random,sys
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).parent; RUNS=Path('/Users/shine/neurosim/runs/step4-v5/p1')
AUDIT=json.loads((ROOT/'independent_audit.json').read_text());HASH=json.loads((ROOT/'reviewed_hashes.json').read_text())['canonical_hashes']
checks=[];points=[];max_state_error=0.;max_cross_error=0.
for short,name in [('opt','optimistic'),('ref','reference'),('pess','pessimistic')]:
 r=RUNS/('case-mram-reviewer-mram-final-'+short+'-20261005');d=json.loads((r/'result.json').read_text());prod=json.loads((RUNS/('case-mram-mram-sidebound-final-'+short+'-20261005')/'result.json').read_text())
 assert d['canonical_hashes']==HASH==prod['canonical_hashes']
 for key in ['rho_MB_per_s','tau_MB_per_s','RI_star','U_star','single_latency_s','resident_s']:
  assert math.isclose(d[key],prod[key],rel_tol=1e-13)
 expected=next(q for q in AUDIT['count_audit']['points'] if q['scenario']==name)
 for key in ['rho_MB_per_s','tau_MB_per_s','RI_star','U_star']:assert math.isclose(d[key],expected[key],rel_tol=1e-13)
 md=json.loads((r/'case_model.json').read_text())
 for p in md['diagnostics']['write_pulses']:
  a=next(q for q in AUDIT['pulses'] if q['initial_state']==p['initial_state'] and q['port_V']==p['port_voltage_V'] and q['plateau_s']==p['plateau_s'])
  max_state_error=max(max_state_error,abs(a['final_state']-p['final_state']))
  if a['crossing_s'] is not None:max_cross_error=max(max_cross_error,abs(a['crossing_s']-p['crossing_s']))
 points.append({k:d[k] for k in ['config_id','scenario','status','rho_MB_per_s','tau_MB_per_s','RI_star','U_star','single_latency_s','resident_s','computational_snapshot_sha256','native_source_manifest_sha256','run_directory','native_run_directory']})
assert max_state_error<1e-8 and max_cross_error<1.1e-10
# Full 64-output hardware layout, two groups of 4 outputs within each of eight banks.
rng=random.Random(9026);x=[rng.randrange(-128,128) for _ in range(64)];w=[[rng.randrange(-128,128) for _ in range(64)] for _ in range(64)]
def scheduled(xs,weights,initial):
 acc=[0 for _ in initial] # actual clear is independently bound by fresh native functional probe
 for row in range(64):
  for group in range(2):
   holds={(bank,lane):weights[row][bank*8+group*4+lane] for bank in range(8) for lane in range(4)}
   for bit in range(8):
    xb=((xs[row]&255)>>bit)&1
    for bank in range(8):
     for lane in range(4):
      col=bank*8+group*4+lane;term=xb*(holds[(bank,lane)]<<bit);acc[col]+=term*(-1 if bit==7 else 1)
      assert -(1<<24)<=acc[col]<(1<<24)
 return acc
vectors={'mixed':(x,w),'zeros':([0]*64,[[127]*64 for _ in range(64)]),'negative_extreme':([-128]*64,[[-128]*64 for _ in range(64)]),'cancellation':([127,-127]*32,[[127]*64 for _ in range(64)]),'bank_and_group_boundary':([1]+[0]*63,[[j-32 for j in range(64)] for _ in range(64)])}
vector_report={}
prior=[99999]*64
for name,(xs,ws) in vectors.items():
 got=scheduled(xs,ws,prior);expected=[sum(xs[i]*ws[i][j] for i in range(64)) for j in range(64)];assert got==expected;vector_report[name]={'passed':True,'min':min(got),'max':max(got)};prior=got
# Import producer only as system under test for failed service; never for expected timing.
def module(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
r=RUNS/'case-mram-reviewer-mram-final-ref-20261005';inp=json.loads((r/'input.json').read_text());native=json.loads((r/'resolved.json').read_text())
probe=copy.deepcopy(inp);probe['resolved_parameters']['program_plateau_s']=40e-9
adapter=module('uut_case',ROOT/'package/cases/mram/case_adapter.py');service=module('uut_service',ROOT/'package/service.py')
failed=adapter.evaluate(probe,native);result=service.aggregate(probe,failed)
assert failed['program_outcome']=='failed' and result['status']=='infeasible'
assert all(k not in result for k in ['rho_MB_per_s','tau_MB_per_s','RI_star','U_star'])
functional=json.loads((Path(points[1]['native_run_directory'])/'functional_probe.json').read_text());assert functional['status']=='PASS'
report={'status':'PASS','points':points,'exact_final_source_hashes':HASH,'max_final_state_difference':max_state_error,'max_crossing_time_difference_s':max_cross_error,'full64output_vectors':vector_report,'clear_and_nominal_gate_counterfactuals':functional['counterfactuals'],'failed40ns_pulse':{'program_outcome':failed['program_outcome'],'aggregate_status':result['status'],'critical_failures':result['critical_failures'],'no_completed_rates':True,'scope':'samefreshnativegeometry;onlypulsewidthcounterfactual;notformalpoint'},'conditions':'Independentreviewpermitsonlydeclaredconditionalmodelscope;notWER,noise/offsetcertification,foundrytransistororSTA.'}
(ROOT/'verification_supplement.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['points','exact_final_source_hashes']},indent=2))
