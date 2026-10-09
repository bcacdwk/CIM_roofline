#!/usr/bin/env python3
import argparse,json,hashlib
from pathlib import Path
IDS=['01_sram_acim','02_sram_dcim','04_nand_3d','06_mram','09_gain_cell_edram','10_fenor_3d']
def h(x):return hashlib.sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--baseline-dir',type=Path,required=True);p.add_argument('--production-dir',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
bin=json.load(open(a.baseline_dir/'geometry_inputs.json'));pin=json.load(open(a.production_dir/'geometry_inputs.json'))
bout=json.load(open(a.baseline_dir/'footprint_results.json'));pout=json.load(open(a.production_dir/'results/footprint_results.json'))
bi={r['case_id']:r for r in bin['cases']};pi={r['case_id']:r for r in pin['cases']};bo={r['case_id']:r for r in bout['main_rows']};po={r['case_id']:r for r in pout['main_rows']}
rows=[]
for cid in IDS:
 assert bi[cid]==pi[cid],('original input row changed',cid)
 assert bo[cid]==po[cid],('original result row changed',cid)
 rows.append({'case_id':cid,'input_row_sha256':h(bi[cid]),'result_row_sha256':h(bo[cid]),'unchanged':True})
assert bout['diagnostic_rows']==pout['diagnostic_rows'],'NAND diagnostics changed'
a.output.write_text(json.dumps({'status':'PASS','six_rows':rows,'NAND_diagnostic_rows_unchanged':True},indent=2)+'\n');print('PASS: six complete input/result rows and NAND diagnostics unchanged')
