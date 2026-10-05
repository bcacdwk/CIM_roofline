#!/usr/bin/env python3
"""Generate small electrical port characterization from the series EKV model."""
import json,hashlib
from pathlib import Path
from string_probe import String

def build():
    p=String();grid=[-.008+j*.00025 for j in range(81)];tables={}
    for selected,row in [('data',15),('reference',30)]:
        for bg in ('nominal','low_pass','high_pass'):
            background=[j%2 if bg=='nominal' else int(bg=='high_pass') for j in range(32)];curves={}
            for name,vbl,state in [('active_on',.2,0),('active_off',.2,1),('ground_on',0.,0),('ground_off',0.,1)]:
                states=background[:];states[row]=state;curves[name]=[p.solve(32,row,states,1.,vbl,v)['current_A'] for v in grid]
            tables[selected+'_'+bg]=curves
    return {'status':'electrical_characterization_not_performance_result','model_sha256':hashlib.sha256(Path(__file__).with_name('string_probe.py').read_bytes()).hexdigest(),'parameters':{'layers':32,'Is_A':p.ispec,'n':p.n,'low_Vt_V':p.low,'high_Vt_V':p.high,'selected_gate_V':1.,'pass_gate_V':4.5,'active_BL_V':.2,'inactive_BL_V':0.,'temperature_K':300},'SL_grid_V':grid,'tables':tables,'source':'EKV1995 Eq28/30/31;16-layer2nA calibration and32-layer unchanged-parameter extension; not old latency fit'}
if __name__=='__main__':
    p=Path(__file__).with_name('string_ports.json');d=build();p.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'file':str(p),'bytes':p.stat().st_size,'electrical_curves':len(d['tables'])*4}))
