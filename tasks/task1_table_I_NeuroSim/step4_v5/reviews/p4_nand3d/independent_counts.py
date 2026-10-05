"""Independent NAND organization/protocol/clock audit; no production aggregation."""
import json,math
from pathlib import Path
ROOT=Path(__file__).parent;B=Path('/Users/shine/neurosim/runs/step4-v5/p4');bind=json.loads((ROOT/'reviewed_hashes.json').read_text());T=500e-9
K,N=4608,240;blocks=(N//30)*4*2;pages=blocks*32*3;data_pages=blocks*30*3;refs=blocks*2*3;pageB=K*3//8
physical=blocks*32*3*(K*3);data=K*N*(4*2*3*3);reference=refs*pageB*8
assert physical==data+reference and blocks==64 and pages==6144
masks=4*2*4;reads=masks*30;calreads=2*4*3;coeff=64*4;packet_bits=16*3;packets=pageB*8//packet_bits
S_ticks=1+K//16+masks*(K//16)+reads*2+reads*2+reads+reads*(10+4)*(64//16)+reads*8+1+1
nonPE_ticks=1+(K*N)//16+pages*packets+pages*pageB+8*(pages+blocks)+calreads*2+calreads*3+(32+3)*(coeff//16)+1
S=S_ticks*T
# Independentbase4/sign/replicatedbit identity. Theseareencodingexpectedvalues,
# never usedtocorrectADC outputs.
errors=0
for x in range(-128,128):
 xd=[(abs(x)//(4**j))%4 for j in range(4)]
 for w in range(-128,128):
  ans=0
  for sign in [-1,1]:
   m=max(sign*w,0)
   for k in range(4):
    wd=(m//(4**k))%4;wb=[wd&1,wd>>1,wd>>1]
    for j,v in enumerate(xd):
     xb=[v&1,v>>1,v>>1]
     count=sum(a*b for a in xb for b in wb)
     ans+=(-1 if x<0 else 1)*sign*count*4**(j+k)
  errors+=(ans!=x*w)
assert errors==0
rows=[]
for short,name,prog,erase in [('opt','optimistic',.0003,.001),('ref','reference',.0003,.001),('pess','pessimistic',.0006,.0035)]:
 path=B/('case-nand3d-reviewer-nand-'+short+'-final-20261005');d=json.loads((path/'result.json').read_text());m=json.loads((path/'case_model.json').read_text());native=json.loads((path/'resolved_components.json').read_text());TR=nonPE_ticks*T+pages*prog+blocks*erase
 assert d['computational_snapshot_sha256']==bind['computational_snapshot_sha256'] and d['computational_hashes']==bind['computational_hashes']
 assert d['status']=='conditional' and math.isclose(d['single_latency_s'],S,rel_tol=1e-12) and math.isclose(d['resident_s'],TR,rel_tol=1e-12)
 assert native['sar']['native_ADC_count']==64 and native['logic']['resident_row_staging_bits']==K*9 and native['logic']['formatted_page_buffer_bits']==48 and native['logic']['output_hold_bits']==N*32
 f=m['diagnostics']['receiver'];gain=int(math.floor(f['gain_count_per_code']*65536+.5));offset=f['calibration_zero_code']
 assert gain<1<<24
 for code in range(1024):
  v=code-offset;word=v&2047;acc=0
  for bit in range(11):acc+=((word>>bit)&1)*(gain<<bit)*(-1 if bit==10 else 1)
  assert (acc+2048)>>12==(v*gain+2048)>>12 and -(1<<34)<=acc<(1<<34)
 assert next(s for s in f['samples'] if s['count']==1)['delta_code']==0
 assert m['diagnostics']['nominal_mapping']['code_perturbation_propagates']
 rows.append({k:d[k] for k in ['config_id','scenario','status','single_latency_s','resident_s','rho_MB_per_s','tau_MB_per_s','RI_star','U_star','component_bindings','run_directory']})
ct={'logical_shape':[K,N],'logical_matrix_bytes':K*N,'blocks':blocks,'physical_cells':physical,'data_cells':data,'reference_cells':reference,'cells_per_INT8_weight':72,'data_pages':data_pages,'reference_pages':refs,'all_pages':pages,'page_Byte':pageB,'physical_page_bytes':pages*pageB,'packets_per_page':packets,'formatter_packet_bits':packet_bits,'input_masks':masks,'stream_reads':reads,'calibration_reads':calreads,'gain_offset_pairs':coeff,'stream_500ns_cycles':S_ticks,'resident_nonPE_500ns_cycles':nonPE_ticks,'stream_s':S,'scalar_encoding_cases':65536,'encoding_errors':errors,'rawcode_integer_arithmetic_cases_per_scenario':1024}
out={'status':'PASS_dominant_counts_and_precision_scope','counts':ct,'points':rows,'reviewed_computational_snapshot_sha256':bind['computational_snapshot_sha256'],'operating_scope':'BoundedcalibratedanalogQ4,notexactINT8/ENOB. Isolatedstringcodezeroandbackgroundgainerrorsremainvisible;no payloadtruthfix in the actualcodepath.'};(ROOT/'independent_counts.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'status':out['status'],'sha':bind['computational_snapshot_sha256'],'counts':ct},indent=2))
