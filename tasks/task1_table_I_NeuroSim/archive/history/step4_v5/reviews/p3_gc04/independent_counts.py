"""Independent integer-clock/encoding/resource audit; no production scheduler import."""
import json,math
from pathlib import Path
ROOT=Path(__file__).parent;period=.2e-6
# K64,N16,16active rows,8planes,physicalcomplementarypair,32physicalrows/half.
counts={'physical_cells':64*16*8*2,'physical_arrays':8*2,'SAR_single_ended':16*8*2,'pair_subtractors':16*8,'external_hold_F':16*8*2*4e-12,'analog_groups':(64//16)*8,'MAC_updates':(64//16)*8*8,'Xsum_updates':64,'refresh_groups':64,'input_beats':64//16}
stream_ticks=1+4+64+32*(4+3+1)+256+1
resident_ticks=1+64*(1+2+1);refresh_ticks=64*(4+7+1+1+2+1)
assert stream_ticks==582 and resident_ticks==257 and refresh_ticks==1024
# Complementarybit identity independently enumerated, not calling gc_model.
mismatch=0
for x in range(-128,128):
 for w in range(-128,128):
  signed_sum=0
  for b in range(8):
   d=x*(2*((w&255)>>b&1)-1);signed_sum+=d*((1<<b) if b<7 else -128)
  mismatch+=((signed_sum-x)//2 != x*w)
assert mismatch==0

def events(H):
 # Ticksareintegers: initialgroupwritebackagesstaggeredfromactualpriorcycle.
 progress=0;clock=0;completed=0;seen={};last=[-(H-1)+(j+1)*16 for j in range(64)];maxage=0;first=None
 for epoch in range(10000):
  if progress in seen:
   oldtime,oldcount=seen[progress]
   if completed>oldcount:
    interval=(clock-oldtime)/(completed-oldcount);break
  else:seen[progress]=(clock,completed)
  start=clock;deadline=start+H-1
  for group in range(64):
   clock=start+(group+1)*16;maxage=max(maxage,clock-last[group]);last[group]=clock
  while clock+4+(1 if progress==0 else 0)<=deadline:
   clock+=4+(1 if progress==0 else 0)
   maxage=max(maxage,clock-last[progress]);last[progress]=clock;progress+=1
   if progress==64:
    progress=0;completed+=1
    if first is None:first=clock-refresh_ticks
  clock+=1 # physicalnonpreemptibleguard
 else:raise AssertionError('noeventrecurrence')
 assert maxage<=H
 n=(H-refresh_ticks-1)//stream_ticks;assert n==1
 Sint=refresh_ticks+n*stream_ticks+1
 return {'retention_ticks':H,'stream_requests_per_refresh':n,'effective_stream_interval_s':Sint*period/n,'resident_interval_s':interval*period,'first_resident_s':first*period,'max_group_age_s':maxage*period,'rho_MB_s':64/(Sint*period/n)/1e6,'tau_MB_s':1024/(interval*period)/1e6,'repeat_elapsed_ticks':clock-oldtime,'repeat_payloads':completed-oldcount}
rows=[]
for name,H in [('optimistic',2000),('reference',1750),('pessimistic',1650)]:
 q=events(H);q['scenario']=name;rows.append(q)
 # Producercomparedonlyaftertheindependentexpectedvaluesareformed.
 f=Path('/Users/shine/neurosim/runs/step4-v5/component-services')/('case-gc04-reviewer-gc04-'+{'optimistic':'opt','reference':'ref','pessimistic':'pess'}[name]+'-final-20261005')
 d=json.loads((f/'result.json').read_text());assert d['status']=='conditional'
 assert math.isclose(d['rho_MB_per_s'],q['rho_MB_s'],rel_tol=1e-10);assert math.isclose(d['tau_MB_per_s'],q['tau_MB_s'],rel_tol=1e-10)
 assert math.isclose(d['delta_S_raw_s'],stream_ticks*period,rel_tol=1e-12)
 assert math.isclose(d['resident_raw_s'],resident_ticks*period,rel_tol=1e-12)
 native=json.loads((f/'resolved_components.json').read_text());assert native['frontend']['ADC_lanes']==256
 assert native['frontend']['program_connected_load_F']<=50e-15*(1+1e-10)
 assert native['digital']['refresh_deadline_bits']>=11 and native['digital']['resident_progress_bits']>=7
 assert counts['physical_cells']==d['resources']['physical_cells']
# Counterexample: positiveavailabilitydoesnotadmitonenonpreemptiblefullrequest.
assert (1500-refresh_ticks-1)>0 and (1500-refresh_ticks-1)<stream_ticks
out={'status':'PASS_main_mechanism_counts','no_production_aggregator_or_scheduler_for_expected_values':True,'resource_count':counts,'raw_stream_s':stream_ticks*period,'raw_resident_s':resident_ticks*period,'refresh_work_s':refresh_ticks*period,'scalar_encoding_cases':256*256,'scalar_encoding_mismatches':mismatch,'initial_phase':'Priorwritebacksare-(H-guard)+(group+1)*q,not allzeroage; refreshedinphysicalorder','points':rows,'300us_counterexample_positive_fraction_but_no_stream':True,'qualification':'Conditional353Kretention/leakmodelandanalogQ4;notexactINT8orall-cellretentionguarantee;physicalsinglelatencydistinctfromlongterminterval'}
(ROOT/'independent_counts.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
