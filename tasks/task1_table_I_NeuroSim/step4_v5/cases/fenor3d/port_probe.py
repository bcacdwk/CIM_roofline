#!/usr/bin/env python3
"""P2 topology/port identifiability probe, not a FeFET service prediction.

Measured/visual source: FENOR-02 Figs3/5/9/11. Drain-voltage normalization and
shape parameters below are engineering witnesses because manuscript omits Vds.
"""
import math,json,argparse,itertools
from pathlib import Path

def id_vg(g,state):
    # Two finite gate-controlled branches, anchored only to visual Fig3(d)
    # read current scale atVg=-.5V. Slopes are engineering witnesses, not extracted.
    at_read=(200e-9 if state else .3e-9)
    return max(.02e-9,min(10e-6,at_read*math.exp((g+.5)/.10)))

def current(g,vds,state,vsat):
    # Both laws agree at chosen0.1V normalization but differ elsewhere.
    return id_vg(g,state)*(-math.expm1(-max(vds,0)/vsat))/(-math.expm1(-.1/vsat))

def four_layer(k,states,selected_gate=-.5,off_gate=-1.1,vds=.1,vsat=.02):
    branch=[current(selected_gate if l==k else off_gate,vds,states[l],vsat) for l in range(4)]
    return {'selected_A':branch[k],'unselected_sum_A':sum(branch)-branch[k],'total_A':sum(branch),'branch_A':branch}

def run():
    read=[]
    for selected in [0,1]:
        vals=[four_layer(0,[selected,*bits]) for bits in itertools.product([0,1],repeat=3)]
        read.append({'selected_state':selected,'min_total_A':min(v['total_A'] for v in vals),'max_total_A':max(v['total_A'] for v in vals),'max_unselected_A':max(v['unselected_sum_A'] for v in vals)})
    no_layer_select=four_layer(0,[0,1,1,1],off_gate=-.5)
    full_erase_off_voltage=-2. # This tempting ordinary-MOS offbias is inadmissible.
    halfselect=[]
    for sign in [-1,1]:
        vw=2.;wsel=sign*2*vw/3;wother=sign*vw/3;btarget=-sign*vw/3;binhibit=sign*vw/3
        halfselect.append({'sign':sign,'target_gate_channel_V':wsel-btarget,'selected_layer_inhibited_col_V':wsel-binhibit,'unselected_layer_target_col_V':wother-btarget,'unselected_layer_inhibited_col_V':wother-binhibit,'adjacent_WL_V':wsel-wother})
    witness=[]
    for vs in [.02,.2]:
        vals=[{'Vds_V':v,'current_A':current(-.5,v,1,vs)} for v in [.01,.05,.1,.2]]
        h=1e-5;gd=(current(-.5,.1+h,1,vs)-current(-.5,.1-h,1,vs))/(2*h)
        witness.append({'drain_shape_V':vs,'at_selected_normalization':vals,'gds_at0p1V_S':gd})
    addresses={(i%32,i//32,(o//16)*8+b,o%16) for i in range(128) for o in range(128) for b in range(8)}
    return {'status':'probe_only','formal_point':False,'source':'FENOR-02p2Fig3/5,p3Fig9/11;no old readslot/ADC/NeuroSim nativeclaim','source_missing':'Vds for reported IdVg,portC/table,qualifiednegative driver','assumed_probe_conditions':{'read_Vds_V':.1,'selected_gate_V':-.5,'unselected_gate_V':-1.1,'normalized_ON_A_visual_approx':200e-9,'normalized_OFF_A_visual_approx':.3e-9,'gate_slope_V_engineering':.1},'four_layer_all_unselected_states':read,'bad_all_layers_read_selected':no_layer_select,'inadmissible_ordinary_off_bias':{'off_gate_V':full_erase_off_voltage,'reason':'−2V is full ERS pulse amplitude;cannot silently use as harmless persistentoffgate'},'read_gate_channel_stress_max_V':1.2,'two_thirds_write_stress_V':4/3,'halfselect_biases':halfselect,'logical_mapping_unique':len(addresses)==131072,'physical_cells':len(addresses),'parallel_operands':32,'layers_are_capacity_not_parallel_operands':True,'drain_shape_identifiability_witnesses':witness,'conclusion':'SharedBL four-layerselection andunselectedleakageare explicit. Same gate/read-currentpoint leavesgds/dynamics unidentified;no rho/tau produced. Negativeoffbiasmustavoidfullerase;do nothide underordinaryMOSgate0or−2V.'}
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--out',type=Path,required=True);out=a.parse_args().out.resolve()
 if 'CloudStorage' in str(out):raise SystemExit('Runtimeoutputmustbeoutsidecloud')
 out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(run(),indent=2)+'\n');print(out)
