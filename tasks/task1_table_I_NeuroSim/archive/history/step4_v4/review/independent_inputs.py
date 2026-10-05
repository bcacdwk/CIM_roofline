#!/usr/bin/env python3
"""Reviewer checks request/constructor/native field chain and unsupported override rejection."""
import importlib.util,json,sys,math,hashlib,re
from pathlib import Path
here=Path(__file__).resolve().parent;package=here/'only_v4';run=Path(sys.argv[1]).resolve()
spec=importlib.util.spec_from_file_location('v4_authority_under_test',package/'run.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
scenarios=json.loads((package/'configs/scenarios.json').read_text())['scenarios'];results={}
for config in sorted((package/'configs').glob('ns_*.json')):
 base=json.loads(config.read_text());cid=base['case_id'];rejects=[]
 for change in ({'unknown_reviewer_field':1},{'logical_K':128},{'logical_N':32},{'input_bits':4},{'temperature_K':299},{'temperature_K':401},{'temperature_K':350.5},{'clock_reservation_factor':1}):
  try:module.resolved_case(base,'reference',scenarios,change)
  except ValueError:rejects.append(change)
  else:raise AssertionError(('unsupported_override_accepted',cid,change))
 raw=[];inputs=[];header_checks=[]
 for sc in ('optimistic','reference','pessimistic'):
  d=run/cid/sc;r=json.loads((d/'resolved.json').read_text());p=json.loads((d/'input.json').read_text())['resolved_parameters'];inputs.append(p);raw.append(r)
  header=(d/'src/request.h').read_text();ctor=(d/'src/Param.cpp').read_text()
  assert ('temperature_K = '+str(p['temperature_K'])+';') in header
  assert re.search(r'\btemp\s*=\s*'+str(p['temperature_K'])+r'\s*;',ctor)
  assert r.get('temperature_K',r.get('temperature_k'))==p['temperature_K']
  header_checks.append({'scenario':sc,'temperature_K':p['temperature_K'],'request_header_sha256':hashlib.sha256(header.encode()).hexdigest(),'constructor_sha256':hashlib.sha256(ctor.encode()).hexdigest()})
 frozen=[{k:v for k,v in p.items() if k!='temperature_K'} for p in inputs];assert frozen[0]==frozen[1]==frozen[2]
 wire='metal0_ohm_per_m' if cid=='ns_sram_dcim' else 'wire_resistance_ohm_per_m'
 for index,factor in ((1,1.2255),(2,1.451)):assert math.isclose(raw[index][wire]/raw[0][wire],factor,rel_tol=1e-12)
 size_fields=('wl_tg_n_m','wl_tg_p_m') if cid=='ns_sram_dcim' else ('wl_tg_n_m','wl_tg_p_m','mux_tg_n_m','mux_tg_p_m') if cid=='ns_sram_acim' else ('access_width_f','mux_width_n_m','mux_width_p_m')
 sizes={field:[r[field] for r in raw] for field in size_fields};assert any(len(set(values))>1 for values in sizes.values())
 results[cid]={'rejected_unsupported_overrides':rejects,'source_and_actual_temperature_chain':header_checks,'only_temperature_changes_in_main_request':True,'wire_ratios':[r[wire]/raw[0][wire] for r in raw],'native_resized_fields':sizes,'interpretation':'Fixed architecture design scenarios; these native sizes do not represent one fixed chip PVT sweep.'}
(here/'independent_inputs.json').write_text(json.dumps({'status':'pass','cases':results},indent=2)+'\n');print('Independent request / constructor / native-thermal sizing audit passed')
