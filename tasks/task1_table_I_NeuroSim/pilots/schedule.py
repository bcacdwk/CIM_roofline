"""Serial resource-occupancy scheduler; physical events do not select clock."""
from collections import defaultdict
import math

def run(events,period,start_ns=0.,align=True):
    now=start_ns;trace=[];ledger={};wait_total=0.
    for e in events:
        kind=e['kind'];wait=0.;begin=now
        if kind in ['digital','boundary'] and align:
            margin=e.get('margin_ns',0.)
            edge=math.ceil((now+margin)/period-1e-10)*period
            wait=max(0.,edge-now);now+=wait;wait_total+=wait
        if kind=='physical':duration=e['ns'];raw=duration;unit='ns';clock=None
        elif kind=='digital':raw=e['cycles'];duration=raw*period;unit='cycles';clock='lv_core'
        elif kind=='boundary':duration=0.;raw=0.;unit='ns';clock=None
        else:raise ValueError(kind)
        assert math.isfinite(duration) and duration>=0 and e['resources'],e
        now+=duration;sid=e['id'];key=(sid,e['provider'],kind)
        row=ledger.setdefault(key,{'id':sid,'provider':e['provider'],'kind':kind,'count':0,'duration_ns':0.,'boundary_wait_ns':0.,'raw_values':set(),'resources':set(),'clock_id':clock,'unit':unit})
        row['count']+=1;row['duration_ns']+=duration;row['boundary_wait_ns']+=wait;row['raw_values'].add(raw);row['resources'].update(e['resources'])
        trace.append({**e,'start_ns':begin,'service_start_ns':begin+wait,'end_ns':now,'boundary_wait_ns':wait})
    stages=[]
    for row in ledger.values():
        raw_values=sorted(row.pop('raw_values'));resources=sorted(row.pop('resources'));row['resources']=resources
        stages.append({'stage_id':row['id'],'provider':row['provider'],'raw_returns':[{'value':x,'unit':row['unit'],'scope':'per event','clock_id':row['clock_id'],'status':'OK','reason':None} for x in raw_values],
         'latency_once_ns':row['duration_ns']/row['count'] if len(raw_values)==1 else None,'count':row['count'],'resource_occupancy_ns':row['duration_ns']+row['boundary_wait_ns'],'initiation_interval_ns':None,'initiation_interval_proof':None,'clock_id':row['clock_id'],'included_substages':[],'included_repetition_dimensions':[],'external_repetition_dimensions':['explicit serial event sequence'],'conversion_count':1,'status':'OK','reason':None,'timing_kind':'digital_step' if row['kind']=='digital' else 'service_duration','constraint_clock_id':None,'boundary_wait_ns':row['boundary_wait_ns'],'case_path_status':'native_budget_retained' if 'native' in row['provider'] or 'v3' in row['provider'] else 'actual_case_path_instantiated','resources':resources,'service_time_total_ns':row['duration_ns']})
    return {'latency_ns':now-start_ns,'boundary_wait_ns':wait_total,'stages':stages,'trace':trace,'end_ns':now}

def metrics(case,streaming,resident):
    l=case['logical'];s=streaming['latency_ns'];r=resident['latency_ns'];rho=1e9*l['B_S_Byte']/s;tau=1e9*l['B_R_Byte']/r
    return {'rho_Byte_per_s':rho,'tau_Byte_per_s':tau,'RI_star':rho/tau,'U_star':r/s,'status':'OK'}
