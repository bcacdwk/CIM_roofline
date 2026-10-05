#!/usr/bin/env python3
"""P0 identifiability witnesses; no service prediction or accepted device corners."""
import json, math, argparse
from pathlib import Path

def code3(d):
    return [d & 1, (d >> 1) & 1, (d >> 1) & 1]

def physical_product(x, w):
    answer = 0
    for pol in [-1, 1]:
        wm = max(pol*w, 0)
        for k in range(4):
            weight = code3((wm >> (2*k)) & 3)
            for j in range(4):
                inp = code3((abs(x) >> (2*j)) & 3)
                count = sum(a*b for a in inp for b in weight)
                answer += (-1 if x < 0 else 1)*pol*count*4**(j+k)
    return answer

def run():
    mismatch = [(x,w) for x in range(-128,128) for w in range(-128,128) if physical_product(x,w)!=x*w]
    cells = 13824*32*3*64
    # These two output-conductance/feedback choices fit the same reported DC point.
    # They are algebraic witnesses of non-identifiability, NOT selected model values.
    witnesses=[]
    for label,lam,G in [('A',0,0.002),('B',0.5,0.020)]:
        i0=2e-9; n=1152*9; c=16e-12
        gds=i0*lam
        eff=G+n*gds
        witnesses.append({'witness':label,'I_at_VDS_0p2_A':i0,'gds_S':gds,'assumed_feedback_G_S':G,'VSL_steady_V':n*i0/eff,'single_pole_time_to_1_over_1024_s':math.log(1024)*c/eff,'qualification':'arbitrary positive witness, not a device scenario; no performance eligibility'})
    return {'status':'identifiability_gap_demonstrated_not_service','physical_scalar_pairs_checked':65536,'mapping_mismatches':len(mismatch),'physical_cells':cells,'reference_cells':13824*2*3*64,'data_cells':cells-13824*2*3*64,'logical_K_N':[4608,240],'cells_per_INT8_weight':72,'page_programs':64*32*3,'block_erases':64,'data_pages':64*30*3,'reference_pages':64*2*3,'max_group_current_A':1152*9*2e-9,'nominal_ADC_LSB_in_unit_currents':25e-6/(1024*2e-9),'V_over_I_is_ohm':0.2/2e-9,'witnesses':witnesses,'missing':['dI/dVDS vs selected/pass state and SL compliance','WL/BL/SSL/GSL capacitance and resistance network','source sense feedback topology/gain/bandwidth','same-topology independent load/state/geometry point'],'published_service_points':0}
if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',required=True);p=Path(a.parse_args().out).resolve()
    if 'CloudStorage' in str(p): raise SystemExit('probe output must stay outside sync tree')
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(run(),indent=2)+'\n');print(p)
