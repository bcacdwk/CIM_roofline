#!/usr/bin/env python3
"""Reviewer-only recomputation from primitive returns and audited operation counts.
No imports of production run.py, evaluate(), check.py, or numeric.py.
"""
import json,math,sys,hashlib
from pathlib import Path
run=Path(sys.argv[1]); checks=[]
def eq(label,a,b):
 assert math.isclose(a,b,rel_tol=2e-12,abs_tol=1e-20),(label,a,b)
 checks.append({'check':label,'actual':a,'independent_expected':b})
def check_case(cid,d,args):
 P=d['clock_period_s'];K=int(d['physical_rows']);cols=int(d['physical_cols']);n=cols//(9 if 'rram' in cid else 8)-1
 assert P>0 and K>0 and n>0
 eq(cid+' installed selector control bits',d['input_selector_control_bits'],5)
 assert d['input_selector_control_area_m2']>0
 assert all(isinstance(v,(int,float)) and math.isfinite(v) for v in d.values())
 if cid=='ns_sram_acim':
  mux=args[2];wc=args[3];ab=args[7];b=K*math.ceil(cols/wc)
  eq('ACIM installed ADC lanes',d['resolved_adc_count'],cols/mux)
  eq('ACIM ADC levels',d['resolved_adc_levels'],2**ab)
  eq('ACIM weight accumulator lanes',d['weight_shift_units'],cols/mux)
  eq('ACIM input accumulator lanes',d['input_shift_units'],cols/mux)
  eq('ACIM write batch count',d['write_batches'],b)
  eq('ACIM native SAR groups',d['adc_s'],mux*(ab+1)*1e-9)
  m=d['mux_s']+d['muxdecoder_s']
  nativebit=max(d['wl_read_s'],m/mux)+(mux-1)*m/mux+d['precharge_read_s']+d['col_s']+d['adc_s']+d['weight_shift_s']+d['input_shift_s']
  eq('ACIM per-bit native components',d['read_per_bit_s'],nativebit)
  eq('ACIM unsigned rounds',d['native_unsigned_8bit_s'],8*nativebit)
  stream=2*8*nativebit+13*P+16*d['input_select_comb_s']
  resident=d['wl_write_s']+d['precharge_write_s']+d['write_driver_s']+(d['native_write_cell_flip_all_s'] if 'native_write_cell_flip_all_s' in d else d['write_all_s']-d['wl_write_s']-d['precharge_write_s']-d['write_driver_s'])+b*(P/2+d['write_encode_inv_s'])+d['precharge_read_s']/mux
  eq('ACIM correction registers',d['correction_s'],3*P)
  eq('ACIM period from installed datapath',P,2*(d['correction_adder_s']+d['correction_inv_s']+d['correction_broadcast_s']))
 elif cid=='ns_rram_1t1r':
  b=K*math.ceil(cols/d['write_batch_cols']);mux=9;ab=d['adc_bits']
  eq('RRAM physical coverage',d['physical_cells'],K*cols)
  for key,value in [('write_batches_per_direction',b),('write_pulses',2*b),('write_transitions',4*b),('verify_rows',2*K),('resident_input_beats',b),('verify_adc_rounds',2*K*9),('verify_comparator_count',64)]:eq('RRAM '+key,d[key],value)
  eq('RRAM SAR groups for eight planes',d['native_read_adc_s'],8*9*(ab+1)*1e-9)
  col=0.2*9*d['cap_col_f']*(d['r_off_ohm']+d['res_row_ohm']+d['res_col_ohm'])/max(1,K*d['read_activity'])
  rowmux=max(d['wl_logic_s']+P/2,d['mux_logic_s'])+8*d['mux_logic_s']
  eq('RRAM first selection overlap plus eight later groups and column RC',d['native_read_other_s'],8*(rowmux+col))
  native=d['native_read_adc_s']+d['native_read_accum_s']+d['native_read_other_s']
  eq('RRAM native component total',d['native_read_8bit_s'],native)
  baseline=8*(8*(d['baseline_combinational_s']+P/2)+P/2)
  eq('RRAM 64 data subtracts and 8 ref captures',d['hrs_subtract_s'],baseline)
  unsigned=native+baseline+d['read_levelshift_s']
  eq('RRAM unsigned service',d['unsigned_8bit_service_s'],unsigned)
  stream=2*unsigned+12.5*P+16*d['input_selector_comb_s']
  verify=d['verify_total_s'];eq('RRAM verify rows total',verify,2*K*d['verify_one_row_s'])
  resident=d['write_pulse_s']+2*d['write_enable_s']+d['write_levelshift_s']+d['write_data_capture_s']+verify
  eq('RRAM release uses same installed path',d['write_release_s'],d['write_enable_s'])
  eq('RRAM derived period',P,2*d['max_combinational_s'])
 else:
  groups=d['write_groups_parallel'];b=K*4/groups
  eq('DCIM NOR input complement enabled',d['input_complement_for_NOR'],1)
  assert d['input_polarity_inv_s']>0 and d['write_cell_node_cap_f']>d['native_product_NOR_input_cap_f']>0
  eq('DCIM serialized complemented input path',d['input_select_comb_s'],d['input_select_decoder_s']+d['input_mux_s']+d['input_polarity_inv_s'])
  eq('DCIM writer columns per group',d['native_write_driver_columns_per_group'],64)
  eq('DCIM total bit capacity',d['physical_bits'],256*256)
  eq('DCIM nibble tree count',d['native_tree_count'],256/4)
  eq('DCIM native unsigned pipeline cycles',d['native_unsigned_cycles'],9)
  eq('DCIM native core seconds',d['native_bit_core_s'],d['native_tree_s']+d['native_nor_s']+d['native_wl_s'])
  eq('DCIM native capture in cycles',d['dff_capture_return_cycles'],1)
  eq('DCIM 64bit group write batches',d['write_beats'],b)
  eq('DCIM write port',d['write_port_bits'],64*groups)
  analog=2*d['write_decoder_one_edge_s']+d['write_precharge_s']+d['write_driver_s']+d['write_cell_flip_s']+d['write_encode_s']
  eq('DCIM write analog path',d['write_analog_s'],analog)
  writebeat=(1+math.ceil(analog/P))*P
  eq('DCIM capture plus rounded busy interval',d['write_beat_s'],writebeat)
  eq('DCIM derived period',P,2*max(d['native_bit_core_s'],d['native_shiftadd_comb_s'],d['nibble_merge_s'],d['correction_comb_s'],d['input_select_comb_s']))
  stream=(1+2*(1+9+1)+3)*P;resident=b*writebeat
  assert d['merge_direct_operand_capture']==1
 actualstream=d.get('stream_latency_s',d.get('stream_single_s'))
 eq(cid+' complete stream reconstruction',actualstream,stream)
 eq(cid+' complete interval',d['delta_s'],stream)
 eq(cid+' resident reconstruction',d['resident_s'],resident)
 return {'case':cid,'K':K,'N':n,'B_S_Byte':K,'B_R_Byte':K*n,'delta_S_ns':stream*1e9,'T_R_ns':resident*1e9,'rho_MB_per_s':K/stream/1e6,'tau_MB_per_s':K*n/resident/1e6,'RI_star':resident/(n*stream),'U_star':resident/stream}
rows=[]
for cid in ('ns_sram_acim','ns_rram_1t1r','ns_sram_dcim'):
 cfg=json.loads((run/cid/'input.json').read_text());raw=json.loads((run/cid/'resolved.json').read_text())
 rows.append(check_case(cid,raw,cfg.get('arguments',[])))
 diagnostic=json.loads((run/cid/'diagnostics.json').read_text())
 for v in cfg['diagnostics']:check_case(cid,diagnostic[v['label']]['raw'],v['arguments'])
 reported=json.loads((run/cid/'result.json').read_text())
 for key in ('K','N','B_S_Byte','B_R_Byte','delta_S_ns','T_R_ns','rho_MB_per_s','tau_MB_per_s','RI_star','U_star'):eq(cid+' exported '+key,reported[key],rows[-1][key])
result={'status':'PASS','producer_evaluate_used':False,'run':str(run),'independent_main_results':rows,'assertion_count':len(checks),'checks':checks}
(run/'reviewer_service_checks.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'assertion_count':len(checks),'independent_main_results':rows},indent=2))
