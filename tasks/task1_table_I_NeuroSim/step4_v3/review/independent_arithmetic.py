#!/usr/bin/env python3
"""Reviewer-only arithmetic and physical-map audit. No production imports."""
from fractions import Fraction
import hashlib,json,random
from pathlib import Path
K,N=256,31
truth=[]
for x in (0,1):
 for stored_q in (0,1):
  input_complement=1-x; stored_qbar=1-stored_q
  nor_output=int(not(input_complement or stored_qbar))
  assert nor_output==x*stored_q
  truth.append({'x':x,'stored_Q':stored_q,'input_INV':input_complement,'existing_Qbar':stored_qbar,'NOR_output':nor_output})
mins=[10**9]*3; maxs=[-10**9]*3
for x in range(-128,128):
 for w in range(-128,128):
  q=x%256; u=w+128; s=int(x<0)
  t=[q*u-128*q, q*u-128*q-256*s*u, q*u-128*q-256*s*u+32768*s]
  assert t[-1]==x*w
  for i,v in enumerate(t): mins[i]=min(mins[i],v);maxs[i]=max(maxs[i],v)
assert all(-(2**24)<=K*lo<=K*hi<2**24 for lo,hi in zip(mins,maxs))
gon=Fraction(1,13000); goff=Fraction(1,29000); lsb=(gon-goff)/2
halfup=lambda v:(2*v.numerator+v.denominator)//(2*v.denominator)
max_adc=0
for active in range(257):
 ref=halfup(active*goff/lsb)
 for ones in range(active+1):
  code=halfup((ones*gon+(active-ones)*goff)/lsb)
  assert code-ref==2*ones
  assert 0<=ref<=code<1024
  max_adc=max(max_adc,code)
rng=random.Random(20261004)
dense=[[((37*r+19*c)%256)-128 for c in range(N)] for r in range(K)]
cases={
 'zero':([0]*K,dense),
 'negative_min':([-128]*K,[[-128]*N for _ in range(K)]),
 'opposite_extremes':([-128]*K,[[127]*N for _ in range(K)]),
 'positive_max':([127]*K,[[127]*N for _ in range(K)]),
 'mixed':([rng.randrange(-128,128) for _ in range(K)],dense),
 'alternating_sign':([(-1)**r*127 for r in range(K)],[[127]*N for _ in range(K)]),
}
results={}
for name,(xs,ws) in cases.items():
 # DCIM exact nibble-tree reconstruction, using 64 independent 256-input trees.
 storage=[[((ws[r][j]+128) if j<N else 1) for j in range(32)] for r in range(K)]
 accum=[]
 for input_pass in ([x%256 for x in xs],[int(x<0) for x in xs]):
  sums=[0]*32
  for bit in range(8):
   trees=[sum(((storage[r][t//2]>>(4*(t%2)))&15)*((input_pass[r]>>bit)&1) for r in range(K)) for t in range(64)]
   for j in range(32): sums[j]+=(trees[2*j]+16*trees[2*j+1])*(2**bit)
  accum.append(sums)
 y=[accum[0][j]-128*accum[0][31]-256*accum[1][j]+32768*accum[1][31] for j in range(N)]
 assert y==[sum(xs[r]*ws[r][j] for r in range(K)) for j in range(N)]
 results[name]={'output_min':min(y),'output_max':max(y),'match':True}
sram=bytes(((dense[r][c//8]+128) if c//8<N else 1)>>(c%8)&1 for r in range(K) for c in range(256))
rram=bytes(((((dense[r][c//9]+128) if c//9<N else 1)>>(c%9))&1) if c%9<8 else 0 for r in range(K) for c in range(288))
assert len(sram)==65536 and len(rram)==73728
assert sum(sram)==sum(rram)
result={'DCIM_physical_NOR_truth_table':truth,'status':'PASS_ideal_arithmetic_and_mapping_only','exhaustive_signed_pairs':65536,'stage_aggregate_min':[K*x for x in mins],'stage_aggregate_max':[K*x for x in maxs],'all_active_ones_combinations':sum(a+1 for a in range(257)),'max_RRAM_ideal_ADC_code':max_adc,'matrix_vectors':results,'payload_Byte':K*N,'stream_Byte':K,'SRAM_bits':len(sram),'RRAM_cells':len(rram),'SRAM_reference_bits':2048,'RRAM_reference_cells':10240,'dense_target_SET_cells':sum(rram),'SRAM_map_sha256':hashlib.sha256(sram).hexdigest(),'RRAM_map_sha256':hashlib.sha256(rram).hexdigest(),'no_production_imports':True,'qualification':'Ideal code mapping with explicitly calibrated gain; not measured precision or analog accuracy.'}
Path(__file__).with_name('independent_arithmetic.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
