#!/usr/bin/env python3
"""Nominal tiled operator graph diagnostic; physical array signals are checked separately."""
import argparse
import hashlib
import json
from pathlib import Path
import random
import sys
sys.dont_write_bytecode=True
import functional_probe as gates

def simulate(xs,w,lanes,held_rows,held_outputs,capture_bytes,omit_clear=False,omit_keep=False,omit_mask=False,initial=None):
 k,n=len(xs),len(w[0]);B=gates.WIDTH
 registers=[gates.bits(x & gates.MASK) for x in (initial or [12345*(i+1) for i in range(n)])]
 registers=[[b & int(omit_clear) for b in r] for r in registers]
 count={'weight_capture_beats':0,'input_row_captures':0,'parallel_mac_updates':0,'maximum_weight_hold_bits':held_rows*held_outputs*8}
 for r0 in range(0,k,held_rows):
  nr=min(held_rows,k-r0)
  for o0 in range(0,n,held_outputs):
   no=min(held_outputs,n-o0)
   # Only this physical tile is held. The immutable test matrix represents NVM cells.
   held=[0x5a]*(held_rows*held_outputs)
   incoming=[(w[r0+rr][o0+oo]&255) if rr<nr and oo<no else 0 for rr in range(held_rows) for oo in range(held_outputs)]
   for start in range(0,len(held),capture_bytes):
    held[start:start+capture_bytes]=incoming[start:start+capture_bytes];count['weight_capture_beats']+=1
   for rr in range(nr):
    count['input_row_captures']+=1;x=xs[r0+rr]&255
    for local0 in range(0,no,lanes):
     for bit in range(8):
      selected=[]
      for ll in range(min(lanes,no-local0)):
       col=o0+local0+ll;value=held[rr*held_outputs+local0+ll]
       extended=[(value>>i)&1 if i<8 else (value>>7)&1 for i in range(B)]
       shifted=[0]*bit+extended[:B-bit];inputbit=(x>>bit)&1
       masked=[z & (1 if omit_mask else inputbit) for z in shifted]
       add=gates.add_sub(registers[col],masked,0);sub=gates.add_sub(registers[col],masked,1)
       selected.append(gates.mux(int(bit==7),add,sub))
      # Actual result keep MUX leaves every unselected output group untouched.
      if omit_keep:
       for col in range(n):registers[col]=selected[col%len(selected)][:]
      else:
       for ll,value in enumerate(selected):registers[o0+local0+ll]=value
      count['parallel_mac_updates']+=1
 return [gates.signed(x) for x in registers],count

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-run',type=Path,required=True);a=p.parse_args()
 raw=json.loads((a.native_run/'resolved.json').read_text());v=json.loads((a.native_run/'input.json').read_text())['parameters']
 gates.WIDTH=v['accumulator_bits'];gates.MASK=(1<<gates.WIDTH)-1
 K,N,L=v['logical_K'],v['logical_N'],v['mac_lanes'];hr,ho=v['weight_hold_rows'],v['weight_hold_outputs'];capture=v['weight_capture_bits']//8
 if not capture or v['weight_capture_bits']%8:raise ValueError('This nominal diagnostic requires byte-aligned captures')
 rng=random.Random(20261005)
 fixtures={'zero':([0]*K,[[127]*N for _ in range(K)]),'extreme':([-128]*K,[[-128]*N for _ in range(K)]),
           'cancel':([127 if i%2 else -127 for i in range(K)],[[63]*N for _ in range(K)]),
           'group_boundary':([1]*K,[[j%7-3 for j in range(N)] for _ in range(K)]),
           'mixed':([rng.randrange(-128,128) for _ in range(K)],[[rng.randrange(-128,128) for _ in range(N)] for _ in range(K)])}
 tests={};counts=None
 for name,(x,w) in fixtures.items():
  got,counts=simulate(x,w,L,hr,ho,capture);expected=[sum(x[i]*w[i][j] for i in range(K)) for j in range(N)]
  tests[name]={'passes':got==expected,'output':got,'expected':expected}
 zero_x,zero_w=fixtures['zero'];x,w=fixtures['group_boundary']
 counters={'missing_mask_detected':simulate(zero_x,zero_w,L,hr,ho,capture,omit_mask=True)[0]!=tests['zero']['expected'],
           'missing_clear_detected':simulate(zero_x,zero_w,L,hr,ho,capture,omit_clear=True)[0]!=tests['zero']['expected']}
 if N>L:counters['missing_group_keep_detected']=simulate(x,w,L,hr,ho,capture,omit_keep=True)[0]!=tests['group_boundary']['expected']
 second,_=simulate(zero_x,zero_w,L,hr,ho,capture,initial=tests['mixed']['output']);tests['next_request']={'passes':second==tests['zero']['expected'],'output':second}
 checks={'held_capacity_matches':counts['maximum_weight_hold_bits']==raw['weight_hold_bits'],
         'mac_count_matches':counts['parallel_mac_updates']==K*N*8//L,
         'input_rows_reselected_per_output_tile':counts['input_row_captures']==K*((N+ho-1)//ho)}
 ok=all(x['passes'] for x in tests.values()) and all(counters.values()) and all(checks.values())
 result={'status':'PASS' if ok else 'FAIL','scope':'Boolean/ripple arithmetic, real limited tile hold and control ordering only; no analog precision claim','counts':counts,'checks':checks,'counterfactuals':counters,'tests':tests,'native_manifest_sha256':hashlib.sha256((a.native_run/'source_manifest.json').read_bytes()).hexdigest()}
 (a.native_run/'digital_functional_probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','counts','checks','counterfactuals')}))
 if not ok:raise SystemExit(1)
if __name__=='__main__':main()
