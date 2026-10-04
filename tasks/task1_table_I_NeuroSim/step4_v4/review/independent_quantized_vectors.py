#!/usr/bin/env python3
"""Independent ladder collapse, nominal quantizer and direct bit-significance reconstruction."""
from pathlib import Path
import json,math,sys,functools,hashlib
here=Path(__file__).resolve().parent;run=Path(sys.argv[1]);reported=json.loads((run/'qualification.json').read_text())['paired_results'];out={}
for sc in ('optimistic','reference','pessimistic'):
 raw=json.loads((run/'ns_rram_1t1r'/sc/'resolved.json').read_text());line=raw['res_col_ohm'];term=raw['mux_res_tg_ohm'];v=raw['read_voltage_v'];gain=raw['nominal_adc_gain_codes_per_A'];ron=raw['r_on_ohm'];roff=raw['r_off_ohm']
 @functools.lru_cache(None)
 def code(mask,active):
  downstream=math.inf
  for j in range(15,-1,-1):
   g=(1/(ron if mask>>j&1 else roff)) if active>>j&1 else 0
   if math.isfinite(downstream):g+=1/(line/16+downstream)
   downstream=1/g if g else math.inf
  current=v/(term+line/16+downstream) if math.isfinite(downstream) else 0
  return math.floor(current*gain+.5)
 dense=[[((r*37+j*19)%256)-128 for j in range(31)] for r in range(256)]
 patterns={'zero_input':([0]*256,dense),'zero_weights':([((r*53)%256)-128 for r in range(256)],[[0]*31 for _ in range(256)]),'full_positive':([127]*256,[[127]*31 for _ in range(256)]),'negative_extremes':([-128]*256,[[-128]*31 for _ in range(256)]),'signed_cancel':([127 if r%2 else -127 for r in range(256)],[[127]*31 for _ in range(256)]),'mixed':([((r*53)%256)-128 for r in range(256)],dense)}
 result={}
 for name,(x,w) in patterns.items():
  passes=[]
  for phase in (0,1):
   acc=[0]*32
   for bank in range(16):
    q=[(x[16*bank+i]%256) if phase==0 else int(x[16*bank+i]<0) for i in range(16)]
    for plane in range(8):
     active=sum(((a>>plane)&1)<<j for j,a in enumerate(q));ref=code(0,active)
     for lane in range(32):
      for weight_bit in range(8):
       state=sum((((w[16*bank+j][lane]+128) if lane<31 else 1)>>weight_bit&1)<<j for j in range(16))
       acc[lane]+=(code(state,active)-ref)*(2**(plane+weight_bit))
   passes.append(acc)
  a,b=passes;c,d=a[31],b[31];actual=[(a[j]-128*c-256*b[j]+32768*d)/16 for j in range(31)];exact=[sum(x[i]*w[i][j] for i in range(256)) for j in range(31)];errors=[av-ev for av,ev in zip(actual,exact)]
  metric={'max_abs_output_error':max(map(abs,errors)),'zero_exact_output_max_abs_residual':max((abs(av) for av,ev in zip(actual,exact) if ev==0),default=0),'max_relative_error_nonzero_only':max((abs((av-ev)/ev) for av,ev in zip(actual,exact) if ev),default=None)}
  official=reported['ns_rram_1t1r__'+sc]['quantized_Q4_mapped_vectors'][name]
  for key,value in metric.items():assert value==official[key],(sc,name,key,value,official[key])
  result[name]=metric
 out[sc]={'temperature_K':raw['temperature_K'],'vectors':result,'comparison':'exactly matches independent fresh-run finite qualification metrics'}
(here/'independent_quantized_vectors.json').write_text(json.dumps({'status':'pass','method':'Recursive circuit collapse plus direct powers-of-two bit significance; no production solver/mapping import','limitation':'Finite vectors under ideal stiff-rail linear ladder and deterministic ADC; not ENOB/accuracy certification','results':out,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},indent=2)+'\n')
print('Independent quantized physical-vector diagnostics match, including nonzero cancellation residuals')
