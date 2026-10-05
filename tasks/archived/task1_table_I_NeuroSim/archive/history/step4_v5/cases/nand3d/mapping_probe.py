"""Small logical/physical encoding and real fixed-point code diagnostics."""
import math,json,argparse
from pathlib import Path
from identifiability_probe import physical_product

def counts(p):
 K,N=p['logical_K'],p['logical_N'];physical=p['blocks']*p['wordlines']*p['ssl_count']*p['bitlines'];data=p['blocks']*p['data_wordlines']*p['ssl_count'];reference=p['blocks']*p['reference_wordlines']*p['ssl_count'];pages=data+reference
 return {'logical_bytes':K*N,'physical_cells':physical,'data_cells':K*N*72,'reference_cells':physical-K*N*72,'data_pages':data,'reference_pages':reference,'page_programs':pages,'block_erases':p['blocks'],'page_payload_bytes':p['page_bits']//8,'physical_page_bytes':pages*p['page_bits']//8,'stream_analog_reads':p['data_wordlines']*4*2*p['row_groups'],'calibration_analog_reads':2*p['row_groups']*3,'calibration_coefficients':p['adc_count']*p['row_groups'],'input_beats':K//p['lanes'],'resident_encoding_beats':K*N//p['lanes'],'packet_bits':p['lanes']*3,'packets_per_page':p['page_bits']//(p['lanes']*3),'calibrated_channels_per_read':p['adc_count'],'reconstruction_updates_per_read':8}

def diagnostic(p,gain,offset):
 values=[-128,-127,-64,-3,-1,0,1,2,3,63,64,127];errors=[]
 for x in values:
  for w in values:
   if physical_product(x,w)!=x*w:errors.append([x,w])
 def calibrate(code):
  coefficient=int(math.floor(gain*(1<<16)+.5));signed=code-offset;word=signed&2047;acc=0
  for bit in range(11):
   selected=((word>>bit)&1)*(coefficient<<bit);acc=acc-selected if bit==10 else acc+selected
  return (acc+2048)>>12
 codes=[0,1,int(offset),min(1023,int(offset)+1),1023];got=[calibrate(x) for x in codes]
 return {'status':'PASS' if not errors else 'FAIL','scalar_boundary_pairs':len(values)**2,'mapping_mismatches':errors,'zero_vector':physical_product(0,127)==0,'opposite_cancellation':physical_product(127,63)+physical_product(-127,63)==0,'isolated_boundary':physical_product(-128,-128)==16384,'fixed_point_input_codes':codes,'fixed_point_Q4_outputs':got,'code_perturbation_propagates':got[3]!=got[2],'runtime_formula':'11real serial add/sub updates;coefficientQ8.16;roundthenrightshift12;no exacttruth correction','scope':'nominal mapping/physical counts/fixed-point path, not analog precision or ENOB'}
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--run-directory',required=True,type=Path);a=parser.parse_args();r=json.loads((a.run_directory/'input.json').read_text());m=json.loads((a.run_directory/'case_model.json').read_text());out=diagnostic(r['resolved_parameters'],m['diagnostics']['receiver']['gain_count_per_code'],m['diagnostics']['receiver']['calibration_zero_code']);(a.run_directory/'nominal_mapping.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out))
