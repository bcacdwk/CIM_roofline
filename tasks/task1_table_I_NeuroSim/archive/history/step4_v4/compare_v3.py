#!/usr/bin/env python3
"""Post-result historical comparison only. Never imported by the V4 model runner."""
import json,csv,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
run=Path(sys.argv[1]).resolve()
old=Path(sys.argv[2]).resolve()
now=json.loads((run/'summary.json').read_text())['case_results'];before=json.loads(old.read_text())['case_results']
rows=[]
classes={'ns_sram_acim':['decoder load/series/wire consistency corrections','fixed public driver110 design choice','single external input capture with retained input bank'], 'ns_rram_1t1r':['segmented16-bank architecture and512ADCs','explicit directional transport/endpoint/staging/global reduction','Q4 approximate format and gain/verify derivation','native settling/verification state/neutral return corrections'], 'ns_sram_dcim':['decoder predecessor/odd-fanout/series and select-wire corrections','actual Metal0/1 thermal propagation','50%-cycle budget and26/512cycle policy retained']}
for oldr in before:
 cid=oldr['case_id'];cold=next(x for x in now if x['case_id']==cid and x['scenario']=='optimistic');ref=next(x for x in now if x['case_id']==cid and x['scenario']=='reference')
 r={'case_id':cid,'V3_source':str(old),'V4_300_paired_id':cold['paired_id'],'V4_350_paired_id':ref['paired_id'],'changes_at_300K':classes[cid]}
 for metric in ['delta_S_ns','T_R_ns','rho_MB_per_s','tau_MB_per_s','RI_star','U_star']:
  v=oldr[metric];r['V3_'+metric]=v;r['V4_300_'+metric]=cold[metric];r['V4_reference_'+metric]=ref[metric]
  r['revision_at_300_delta_'+metric]=cold[metric]-v;r['warm_input_delta_'+metric]=ref[metric]-cold[metric]
  assert math.isclose(r['revision_at_300_delta_'+metric]+r['warm_input_delta_'+metric],ref[metric]-v,rel_tol=1e-12,abs_tol=1e-10)
 rows.append(r)
(run/'comparison_v3.json').write_text(json.dumps({'role':'Independent post-result background comparison; not an evaluation input or fitting target','accounting':'All interacting model/architecture/policy revisions counted once at300K; warm operating input350K shown separately; not a causal per-patch attribution','rows':rows},indent=2)+'\n')
fields=[k for k in rows[0] if k not in ('changes_at_300K','V3_source')]
with (run/'comparison_v3.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
print('Historical comparison produced after all V4 results.')
