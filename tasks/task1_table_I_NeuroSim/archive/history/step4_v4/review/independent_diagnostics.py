#!/usr/bin/env python3
import json,math,sys
from pathlib import Path
run=Path(sys.argv[1]);here=Path(__file__).resolve().parent
cases=json.loads((run/'diagnostics.json').read_text())['case_results'];out=[]
def near(a,b):assert math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-18),(a,b)
for row in cases:
 cid=row['case_id'];sc=row['scenario'];r=json.loads((run/cid/sc/'resolved.json').read_text());ref=json.loads((run/cid/'reference/resolved.json').read_text());checks=[]
 if sc=='diagnostic_corrected300':
  assert r==json.loads((run/cid/'optimistic/resolved.json').read_text());checks=['Same corrected300K result before choosing350K warm point']
 elif sc=='diagnostic_driver55':
  near(r['mux_driver_n_m'],ref['mux_driver_n_m']/2);near(r['mux_driver_input_F'],ref['mux_driver_input_F']/2);assert r['mux_decoder_area_m2']<ref['mux_decoder_area_m2'];checks=['Driver physical width, preceding gate cap and area all respond']
 elif sc in ('diagnostic_wire2','diagnostic_wire125'):
  factor=2 if sc=='diagnostic_wire2' else 1.25;fields=('wire_resistance_ohm_per_m','rrow_ohm','rcol_ohm') if cid=='ns_sram_acim' else ('metal0_ohm_per_m','metal1_ohm_per_m','row_wire_ohm','col_wire_ohm')
  for field in fields:near(r[field],factor*ref[field])
  checks=['Requested wire change reaches actual metal and array resistance']
 elif sc=='diagnostic_pulse20ns':
  near(r['delta_s'],ref['delta_s']);near(r['resident_s']-ref['resident_s'],4608*10e-9);checks=['Pulse20ns causes exactly4608 additional10ns slots, read unchanged']
 elif sc=='diagnostic_attempt2':
  for field in ('write_pulses','write_transitions','verify_rows','verify_adc_rounds'):near(r[field],2*ref[field])
  for field in ('delta_s','write_data_capture_s','write_data_bus_s','area_total_m2'):near(r[field],ref[field])
  checks=['Retry demand doubles program/verify operations; one row load and fixed hardware retained']
 elif sc=='diagnostic_activity50':
  near(r['resident_s'],ref['resident_s']);assert r['native_read_other_s']<ref['native_read_other_s'];checks=['Read RC responds; full resident load unchanged']
 else:raise AssertionError(sc)
 out.append({'paired_id':row['paired_id'],'passed':True,'meaning':checks})
(here/'independent_diagnostics.json').write_text(json.dumps({'status':'pass','diagnostics':out,'interpretation':'Separate causal cases, never added to the nine main points'},indent=2)+'\n');print('Independent causal diagnostics passed')
