"""Visible geometric port and rated read-bias driver compact estimates."""
import math,json
from pathlib import Path

def ports(p):
    epsilon=8.8541878128e-12*p['dielectric_epsilon_r'];sheet=p['block_length_m']*p['block_width_m']
    # Two adjacent plane loads plus actual channel-gate surface; dimensions are
    # explicit model choices, not capacitance fitted from the old303ns slot.
    wl=2*epsilon*sheet/p['WL_spacing_m']+p['bitlines']*p['ssl_count']*epsilon*(2*p['channel_width_m']*p['gate_height_m'])/p['gate_EOT_m']
    bl=p['BL_length_m']*p['wire_cap_F_m']+p['blocks']*p['ssl_count']*p['terminal_drain_cap_F']
    wlr=p['WL_sheet_ohm_square']*p['block_length_m']/p['block_width_m'];blr=p['metal_resistivity_ohm_m']*p['BL_length_m']/(p['BL_width_m']*p['BL_thickness_m'])
    h=json.loads(Path(__file__).with_name('hv_driver_characterization.json').read_text());n=h['devices']['N'];q=h['devices']['P'];load=wl+n['drain_F']+q['drain_F']
    def charge(swing,device):
        last=p['bias_relative_error']*swing;first=min(.05,swing)
        return load*max(0,swing-first)/device['I_at_50mV_A']+load*device['low_field_R_ohm']*math.log(first/last)
    up=charge(p['pass_voltage_V'],q);down=charge(p['pass_voltage_V'],n)
    # Local level translation is a retained nominal component budget from the
    # measured-I/C cross-coupled port; its original low-voltage input is loaded
    # by the actual native address path, and output switching is charged above.
    setup=p['level_translate_s']+max(up,down)+-math.log(p['bias_relative_error'])*wlr*load/2
    count=p['blocks']*(p['wordlines']+p['ssl_count']+1)
    return {'WL_cap_F':wl,'BL_cap_F':bl,'WL_wire_ohm':wlr,'BL_wire_ohm':blr,'read_bias_setup_s':setup,'read_bias_release_s':p['level_translate_s']+down,'HV_control_channels':count,'HV_read_driver_FETs':2*count,'HV_driver_gate_load_F_each':n['gate_F']+q['gate_F'],
      'HV_read_port_active_area_lower_m2':count*(n['channel_diffusion_area_m2']+q['channel_diffusion_area_m2']),'native_LV_level_input_F':p['HV_level_input_F'],
      'scope':'SKY130read-bias ports <=4.5V only. CompletePEengine separately owns HV isolation/pump/bias recovery; no20V claim for5Vswitches.'}

def channel_settling(p):
    """Finite internal channel-C allowance from EKV differential conductances.
    Both terminal ends are stiff compared with megohm channel sections. Trace of
    the passive minimum-conductance ladder inverse bounds its slowest pole;
    this is a visible conservative local surrogate, not V/I or full TCAD.
    """
    from string_probe import String,UT
    model=String();cap=8.8541878128e-12*p['dielectric_epsilon_r']*(2*p['channel_width_m']*p['gate_height_m'])/p['gate_EOT_m']
    def slope(x):
        z=x/2;soft=z+math.log1p(math.exp(-z)) if z>0 else math.log1p(math.exp(z));sig=1/(1+math.exp(-z)) if z>0 else math.exp(z)/(1+math.exp(z));return soft*sig
    records=[]
    for row in (0,15,30,31):
        for background in (0,1):
            for state in (0,1):
                states=[background]*32;states[row]=state;r=model.solve(32,row,states,1.,.2,p['amp_offset_V']);nodes=r['node_V']
                vps=[(4.5-.5)/3]+[((1. if i==row else 4.5)-(model.high if s else model.low))/3 for i,s in enumerate(states)]+[(4.5-.5)/3]
                resistances=[]
                for i,vp in enumerate(vps):
                    gs=model.ispec/UT*slope((vp-nodes[i])/UT);gd=model.ispec/UT*slope((vp-nodes[i+1])/UT);resistances.append(1/min(gs,gd))
                left=[];z=0
                for resistance in resistances:z+=resistance;left.append(z)
                right=[0.]*len(resistances);z=0
                for i in range(len(resistances)-1,-1,-1):z+=resistances[i];right[i]=z
                tau=sum(cap/(1/left[i]+1/right[i+1]) for i in range(len(resistances)-1))
                records.append({'selected':row,'pass_background':background,'state':state,'tau_trace_s':tau})
    maximum=max(x['tau_trace_s'] for x in records)
    return {'internal_node_cap_F':cap,'differential_RC_trace_max_s':maximum,'settle_allowance_s':-math.log(.001)*maximum,'method':'minimum(g_source,g_drain) of actualEKVoperatingnodes;grounded-endRCinverse trace;0.1percent finite allowance','scope':'explicitgeometry/local-linear surrogate;notlegacy total timing or all-nonlinear siliconbound','limiting_case':max(records,key=lambda x:x['tau_trace_s'])}
