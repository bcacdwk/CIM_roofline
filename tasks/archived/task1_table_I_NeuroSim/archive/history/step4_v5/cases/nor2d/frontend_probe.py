#!/usr/bin/env python3
"""NOR-04 curve-based three-terminal probe, not complete NOR service prediction."""
import bisect,json,math
from pathlib import Path

def current(vgs,vds,state,table):
    xs=[r['gate_V'] for r in table['samples']]
    if not xs[0]<=vgs<=xs[-1] or not 0<=vds<=1:raise ValueError('Outside characterized/conditional compact domain')
    j=min(max(1,bisect.bisect_left(xs,vgs)),len(xs)-1);a,b=table['samples'][j-1:j+1]
    key='erased_current_A' if state=='erased' else 'programmed_current_bound_A'
    f=(vgs-a['gate_V'])/(b['gate_V']-a['gate_V'])
    i1=math.exp(math.log(a[key])*(1-f)+math.log(b[key])*f)
    # Finite-VDS subthreshold saturation extension; source Fig3 provides VT=26mV.
    # Only VDS=1V is a measured transfer. This extension is a transistor-physics model.
    return i1*(-math.expm1(-vds/.026))/(-math.expm1(-1/.026))

def evaluate(table):
    out=[]
    for gate in (1.1,1.2,1.3):
        on=current(gate,1.,'erased',table);off=current(gate,1.,'programmed',table)
        out.append({'gate_V':gate,'source_V':0.,'drain_read_V':1.,'on_A':on,'off_upper_A':off,
         'read_state_ratio_lower':on/off,'saturation_change_to_VDS0p8_relative':1-current(gate,.8,'erased',table)/on,
         'read_point_Ron_ohm_diagnostic_only':1/on,
         'off_row_leak_upper_A_127rows':127*table['floor_A']})
    return {'status':'probe_only','formal_service_points':0,'source_curve':'transfer_samples.json','working_points':out,
     'model_coverage':'Measured IDS-VGS atVDS1V; finiteVDS subthreshold drainfactor is explicit compact extension, not measured transient or RRAM programming.',
     'port_candidates':{'terminals':['gate','drain','source','storedfloatinggatecharge'],'drain_domain_V':[.8,1.],
       'control_gate_domain_V':[1.1,1.3],'wordline_capacitance':'pendinggeometry/EOT engineeringinput; notdeducedfrom100/120/130nsaccess',
       'bitline_capacitance':'pendingdrain/wire/externalreference mapping','state_update':'opaquecompletepage/sectorP/E; noR-basedupdate'},
     'limitations':['Setupfloor is anoffcurrent upperbound; no statistics inferred.','Unselectedgate0 is belowextractedtableminimum. The127-rowleakbound is a conservative source-floor assumption, tobechecked with actualselection.','No rho/tau, no complete write, no native peripheral run yet.']}

if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 root=Path(__file__).resolve().parent;t=json.loads((root/'transfer_samples.json').read_text())
 if a.out.exists():raise ValueError('no overwrite')
 a.out.write_text(json.dumps(evaluate(t),ensure_ascii=False,indent=2)+'\n')
 print(json.dumps({'status':'probe_only','output':str(a.out)}))
