#!/usr/bin/env python3
"""Compare reviewer primary-source recomputation with production authority."""
import argparse,json,math,hashlib
from pathlib import Path
from independent_recompute import calculate

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--production',type=Path,required=True);p.add_argument('--output',type=Path,default=Path('comparison.json'));a=p.parse_args()
ind=calculate();prod=json.loads(a.production.read_text());by={r['case_id']:r for r in prod['main_rows']}
selected=[r for r in ind['source_rows'] if r['row_id'] not in ['nand_single_layer','nand_source_32']]
checks=[]
for r in selected:
 target=by[r['case_id']]
 for ik,pk in [('A_xy_um2','area_xy_um2'),('b_bit','independent_bits'),('F_mem_nm','F_mem_nm'),('a_bit_um2','a_bit_um2'),('D_Mbit_mm2','density_Mbit_mm2'),('alpha_Fmem2_per_bit','alpha_F_mem2_per_bit')]:
  assert math.isclose(r[ik],target[pk],rel_tol=1e-12),(r['case_id'],ik,r[ik],target[pk])
 checks.append(r['case_id'])
missing=['03_nor_2d','05_rram','07_pcm','08_feram_hfo2']
for cid in missing:
 for k in ['area_xy_um2','a_bit_um2','density_Mbit_mm2','alpha_F_mem2_per_bit']:assert by[cid][k] is None
 assert by[cid]['missing_reason']
for r in prod['diagnostic_rows']:
 name='nand_single_layer' if r['effective_layers']==1 else 'nand_source_32'
 own=next(q for q in ind['source_rows'] if q['row_id']==name)
 assert math.isclose(r['a_bit_um2'],own['a_bit_um2'],rel_tol=1e-12)
assert [r['case_id'] for r in prod['main_rows']]==sorted(by)
result={'status':'PASS','checked_quantified_cases':checks,'missing_cases_not_zero':missing,'production_sha256':sha(a.production),'independent_script_sha256':sha(Path(__file__).with_name('independent_recompute.py')),'arithmetic_checks':ind['checks'],'method':'Independent source-fact arithmetic first; production replay comparison second; production CSV never used as source.'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
