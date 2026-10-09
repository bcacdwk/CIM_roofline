#!/usr/bin/env python3
import argparse,json,math,hashlib
from pathlib import Path
from independent_recompute import calculate
p=argparse.ArgumentParser();p.add_argument('--production',type=Path,required=True);p.add_argument('--model-input',type=Path,default=Path(__file__).resolve().parents[1]/'model_inputs.json');p.add_argument('--output',type=Path,default=Path('comparison.json'));a=p.parse_args()
ind=calculate(json.load(open(a.model_input)));prod=json.load(open(a.production));by={r['case_id']:r for r in prod['main_rows']}
for r in ind['source_rows']:
 for ik,pk in [('A_xy_um2','area_xy_um2'),('b_bit','independent_bits'),('F_mem_nm','F_mem_nm'),('a_bit_um2','a_bit_um2'),('D_Mbit_mm2','density_Mbit_mm2'),('alpha_Fmem2_per_bit','alpha_F_mem2_per_bit')]:
  assert math.isclose(r[ik],by[r['case_id']][pk],rel_tol=2e-12,abs_tol=1e-14),(r['case_id'],ik)
assert len(by)==10 and all(r['density_Mbit_mm2']>0 for r in prod['main_rows'])
for r in prod['diagnostic_rows']:
 exp=ind['NAND_algebraic_rows']['a1_um2' if r['effective_layers']==1 else 'a32_um2'];assert math.isclose(r['a_bit_um2'],exp,rel_tol=1e-12)
result={'status':'PASS','checked_cases':list(by),'all_ten_finite_positive':True,'NAND_diagnostics_match':True,'production_sha256':hashlib.sha256(a.production.read_bytes()).hexdigest(),'method':'Independent source/model arithmetic; original six additionally protected by full-row snapshot comparison'}
a.output.write_text(json.dumps(result,indent=2)+'\n');print('PASS: all ten production rows and NAND diagnostics')
