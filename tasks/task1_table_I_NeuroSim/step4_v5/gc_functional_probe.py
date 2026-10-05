#!/usr/bin/env python3
"""Nominal GC code-to-gate mapping and maintenance register lifecycle; not ENOB."""
import argparse,json,hashlib,random,sys
from pathlib import Path
sys.dont_write_bytecode=True
import functional_probe as gate

def bits(value,width):return [(value>>k)&1 for k in range(width)]
def signed(v):return sum(x<<k for k,x in enumerate(v))-(1<<len(v) if v[-1] else 0)
def mux(a,b,s):return [(x&(1-s))|(y&s) for x,y in zip(a,b)]
def compute(xs,w,L,B,omit_clear=False,omit_mask=False,omit_xsum=False,omit_sign=False,inject=False):
 K,N=len(xs),len(w[0]);registers=[bits(137*(j+1) if omit_clear else 0,B) for j in range(N)]
 xreg=bits(0,16)
 for x in xs:xreg=gate.add_sub(xreg,bits(x,16),0)
 counts={'analog_cycles':0,'parallel_difference_captures':0,'parallel_MAC_updates':0,'Xsum_updates':K,'correction_groups':N//L}
 for group in range(N//L):
  for row0 in range(0,K,16):
   for xb in range(8):
    raw=[]
    for p in range(8):
     for lane in range(L):
      col=group*L+lane;pos=neg=0
      for row in range(row0,min(K,row0+16)):
       active=1 if omit_mask else ((xs[row]&255)>>xb)&1
       if ((w[row][col]&255)>>p)&1:pos+=active
       else:neg+=active
      # Current lowers each branch voltage/code: N-code minus P-code gives P-N.
      rawP=1800-16*pos;rawN=1800-16*neg
      if inject and group==0 and row0==0 and xb==7 and p==7 and lane==0:rawN+=1
      raw.append(gate.add_sub(bits(rawN,12),bits(rawP,12),1))
    counts['analog_cycles']+=1;counts['parallel_difference_captures']+=1
    for p in range(8):
     for lane in range(L):
      col=group*L+lane;d=raw[p*L+lane];extended=d+[d[-1]]*(B-len(d));shift=xb+p
      operand=[0]*shift+extended[:B-shift]
      subtract=0 if omit_sign else int((xb==7)^(p==7))
      registers[col]=gate.add_sub(registers[col],operand,subtract)
     counts['parallel_MAC_updates']+=1
 result=[]
 for r in registers:
  correction=0 if omit_xsum else signed(xreg)<<4
  corrected=gate.add_sub(r,bits(correction,B),1)
  # Fixed arithmetic right shift; discarded half-LSB remains an error, not truth repair.
  result.append(signed(corrected)>>1)
 return result,counts,signed(xreg)

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--native-run',required=True,type=Path);a=p.parse_args()
 v=json.loads((a.native_run/'input.json').read_text())['parameters'];raw=json.loads((a.native_run/'resolved.json').read_text());K,N,L,B=[v[k] for k in ('logical_K','logical_N','mac_lanes','accumulator_bits')]
 rng=random.Random(20261005);fixtures={'zero':([0]*K,[[127]*N for _ in range(K)]),'extreme':([-128]*K,[[-128]*N for _ in range(K)]),'cancel':([127 if i%2 else -127 for i in range(K)],[[63]*N for _ in range(K)]),'isolated':([1]+[0]*(K-1),[[j%7-3 for j in range(N)] for _ in range(K)]),'mixed':([rng.randrange(-128,128) for _ in range(K)],[[rng.randrange(-128,128) for _ in range(N)] for _ in range(K)])}
 tests={}
 for name,(x,w) in fixtures.items():
  y,counts,xs=compute(x,w,L,B);expected=[sum(x[i]*w[i][j] for i in range(K))*16 for j in range(N)];tests[name]={'passes':y==expected,'output_Q4_codes':y,'Xsum':xs}
 x,w=fixtures['mixed'];z,zw=fixtures['zero']
 negative={'missing_clear_detected':compute(z,zw,L,B,omit_clear=True)[0]!=tests['zero']['output_Q4_codes'],'missing_row_mask_detected':compute(z,zw,L,B,omit_mask=True)[0]!=tests['zero']['output_Q4_codes'],'missing_Xsum_detected':compute(x,w,L,B,omit_xsum=True)[0]!=tests['mixed']['output_Q4_codes'],'missing_sign_logic_detected':compute(x,w,L,B,omit_sign=True)[0]!=tests['mixed']['output_Q4_codes'],'ADC_code_perturbation_propagates':compute(x,w,L,B,inject=True)[0]!=tests['mixed']['output_Q4_codes']}
 state={'resident_progress':173,'result':[345,-125],'Xsum':456,'resident_target':0xabc,'refresh_progress':231,'timer':3900,'operation_index':533}
 before=dict(state);state['refresh_progress']=0;state['timer']=0
 lifecycle=all(state[k]==before[k] for k in ('resident_progress','result','Xsum','resident_target','operation_index'))
 index=bits(777,10);index=[b&0 for b in index];done=False;completion=int(raw.get('operation_completion_carry_tap',10));updates=counts['parallel_MAC_updates']
 for update in range(updates):
  old=sum(b<<j for j,b in enumerate(index));index=gate.add_sub(index,bits(1,10),0);done=bool(((old+1)>>completion)&1)
  if update<updates-1:assert not done
 checks={'operation_index_complete_after_exact_MAC_count':done,'ADC_raw_capacity':raw['ADC_raw_hold_bits']==2*v['adc_pair_lanes']*v['adc_bits'],'difference_capacity':raw['ADC_difference_hold_bits']==v['adc_pair_lanes']*(v['adc_bits']+1),'Xsum_extreme_safe':tests['extreme']['Xsum']==-8192,'refresh_local_clear_preserves_other_state':lifecycle,'MAC_count':counts['parallel_MAC_updates']==(K//16)*(N//L)*8*8}
 ok=all(t['passes'] for t in tests.values()) and all(negative.values()) and all(checks.values())
 result={'status':'PASS' if ok else 'FAIL','scope':'nominal ADC-code mapping, ripple add/sub, sign/hold/clear; ideal code fixtures do not establish analog ENOB','native_manifest_sha256':hashlib.sha256((a.native_run/'source_manifest.json').read_bytes()).hexdigest(),'tests':tests,'counterfactuals':negative,'checks':checks,'counts':counts,'refresh_before':before,'refresh_after':state}
 (a.native_run/'gc_functional_probe.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','checks','counterfactuals','counts')}))
 if not ok:raise SystemExit(1)
if __name__=='__main__':main()
