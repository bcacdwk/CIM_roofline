#!/usr/bin/env python3
"""One sourced SKY130 HV-port alternative. Not a complete PCM program guarantee.
SkyWater PDK Authors data/model parameters: Apache-2.0, see LICENSE.sky130.txt.
I-V comes from locked raw measurements; C bounds from separate TT model geometry.
"""
import argparse,bisect,json,math
from pathlib import Path

def interp(xs,ys,x):
    if not xs[0]-1e-12<=x<=xs[-1]+1e-12:raise ValueError('outside measured drain domain')
    j=min(max(1,bisect.bisect_left(xs,x)),len(xs)-1)
    return ys[j-1]+(ys[j]-ys[j-1])*(x-xs[j-1])/(xs[j]-xs[j-1])

class Port:
    def __init__(self,d):self.d=d
    def current(self,kind,gate,drain,body=0):
        # Gate values are deliberately rounded DOWN to a measured sweep to avoid
        # using convex interpolation as a falsely optimistic current bound.
        if gate<=0 or drain<=0:return 0.
        if not gate<=5 or not drain<=5:raise ValueError('measurement domain')
        g=math.floor(gate+1e-12)
        curves=self.d['raw_measured_N_curves' if kind=='N' else 'raw_measured_P_curves']
        row=next(q for q in curves if q['gate']==g and q['body']==body)
        return interp(row['V'],row['I'],drain)
    def caps(self,W,L,fingers=3):
        p=self.d['model_C'];diff=self.d['geometry']['diffusion_extension_m']
        cox=3.9*8.8541878128e-12/p['toxm_m']
        cg=cox*W*L+(p['cgso_F_per_m']+p['cgdo_F_per_m'])*W+p['cgbo_F_per_m']*L
        # Zero-bias junction values upper-bound reverse-biased junction capacitance.
        cd=p['cjs_F_per_m2']*W*diff+p['cjsws_F_per_m']*2*(W+fingers*diff)+p['cjswgs_F_per_m']*W+p['cgdo_F_per_m']*W
        return {'gate_upper_F':cg,'drain_upper_F':cd,'channel_and_diffusion_area_m2':W*(L+2*diff)}

def level_shift_probe(port,rail=5.,parallel_N=16):
    # Cross-coupled HV PMOS pair (7um/.5um), parallelHVNMOS pulldowns
    # (each20um/.5um) driven by complementary1V inputs. Tables are nominal
    # same-PDK measurements, not a measured joint silicon corner.
    nc=port.caps(20e-6,.5e-6);pc=port.caps(7e-6,.5e-6)
    C=parallel_N*nc['drain_upper_F']+pc['drain_upper_F']+2*pc['gate_upper_F']
    v=[rail,0.];h=.2e-12;t=0.;cross=None
    def f(v):
        a,b=v
        pa=port.current('P',max(0.,rail-b),max(0.,rail-a))
        pb=port.current('P',max(0.,rail-a),max(0.,rail-b))
        na=parallel_N*port.current('N',1.,max(0.,a))
        return [(pa-na)/C,pb/C]
    for j in range(250000):
        a=f(v);b=f([v[i]+h*a[i]/2 for i in range(2)]);c=f([v[i]+h*b[i]/2 for i in range(2)]);z=f([v[i]+h*c[i] for i in range(2)])
        nv=[v[i]+h*(a[i]+2*b[i]+2*c[i]+z[i])/6 for i in range(2)]
        if min(nv)<-1e-8 or max(nv)>rail+1e-8:raise ValueError('invalidcontrol integration')
        v=nv;t+=h
        if v[0]<.01*rail and v[1]>.99*rail:cross=t;break
    return {'rail_V':rail,'input_valid_V':1.,'NMOS_parallel_per_side':parallel_N,'PMOS_per_side':1,
      'control_node_upper_C_F':C,'input_gate_C_F_each':parallel_N*nc['gate_upper_F'],
      'switch_after_valid_complementary_inputs_s':cross,'end_nodes_V':v,'timestep_s':h,
      'scope':'Nominalphysicalcross-coupledport withmeasuredgate-floorI-V; beginsafterLVinputsarevalid;LVinputdrivernotincludedinthisnumber',
      'area_channel_plus_diffusion_m2':2*(parallel_N*nc['channel_and_diffusion_area_m2']+pc['channel_and_diffusion_area_m2'])}

def evaluate(data,native):
    port=Port(data);nc=port.caps(20e-6,.5e-6);rail=5.;hot=4.5;limit=.2;group=16
    # This is a fixedengineeringcompliance choice, NOT TiSbTe measured voltage.
    grid_R=.8448;local_R=1.408
    peak_device=port.current('N',rail,hot,0.)
    ground_bound=peak_device*(group*grid_R+local_R)
    assert rail-ground_bound>=4 and ground_bound<limit and ground_bound<=2.5
    C=native['sa_effective_node_cap_F']+3*nc['drain_upper_F']
    # Use lower measuredVGS4V/body-2.5V, andworstsourcebounce throughout:
    # actualVGS>=4,body>=-2.5 bythecheckabove. This gives a conservative
    # discharge integral while gate is valid; no ideal zero-time clamp.
    steps=20000;dv=(hot-limit)/steps;delay=0.
    for j in range(steps):
        v=limit+(j+.5)*dv
        current=port.current('N',4.,v-ground_bound,-2.5)
        if current<=0:raise ValueError('no return current')
        delay+=C*dv/current
    control=level_shift_probe(port)
    on_R=.05/port.current('N',4.,.05,-2.5)
    lvpark_R=native['precharge_branch_R_ohm'] # conservativeexisting8F NMOSlowrailR
    lower_node_C=native['sa_effective_node_cap_F']+nc['drain_upper_F']
    feedthrough_bound=nc['drain_upper_F']/lower_node_C*hot
    park_s=lvpark_R*lower_node_C*math.log(max(feedthrough_bound,1e-3)/1e-3)
    return {'status':'sourced_hv_component_probe_only','complete_PCM_resident_qualified':False,
      'rated_domains_checked':True,'fixed_engine_compliance_upper_V':hot,'gate_supply_V':rail,
      'geometry':data['geometry'],'caps':nc,'nominal_read_isolator_R_upper_ohm':on_R,
      'off_leakage_measured_abs_bound_A':data['raw_off_current_absolute_upper_A']['N'],
      'off_isolation':{'hot_V':hot,'gate_V':0.,'low_node_park_V':0.,'bounds':'VDS<=4.5,VGS=0,VBS=0withinpublishedHVdomain;negativeinstrumentcurrentnotclaimedastargetperformance',
       'pessimistic_full_drain_cap_feedthrough_V':feedthrough_bound,'native_low_domain_limit_V':native['actual_tech_vdd_V'],
       'LVpark_devices_required':128,'LVpark_R_ohm':lvpark_R,'LVpark_settle_to_1mV_s':park_s,
       'LVpark_steady_leak_error_V':lvpark_R*data['raw_off_current_absolute_upper_A']['N']},
      'return':{'simultaneous_clamps':group,'all_column_groups':8,'peak_current_device_A':peak_device,'peak_current_group_A':group*peak_device,
        'ground_drop_upper_V':ground_bound,'initial_upper_V':hot,'residual_target_V':limit,'load_upper_F':C,'discharge_after_gate_valid_s':delay,
        'method':'C integral dV/I; conservative measuredgate/body sweeps andworstsourcebounce; allWLoff so residualcapenergyreturnsoutsidePCM'},
      'level_translation':control,
      'resources_required':{'HVread_isolation_FETs':128,'HVreturn_clamp_FETs':128,'HVprogram_outputs_or_selectors':128,'active_program_sources':16,
         'LVparking_FETs':128,'LV_HV_control_channels_candidate':26,'technology_identity':'separateSKY130HV20um/.5um ports, not scaled45nmdevices'},
      'remaining_before_formal_service':['IntegrateLVdriverandHVoutputbufferloading/commands, realmodeFSMandgatevalidtiming intoeachwrite/return/readstage.',
       'RelocateeveryLV1Vswitch outofhotdomain; authoritativecompleteporttopology/readC andprogramcurrentpathmustreplaceoldcandidate.',
       'Source-equivalentTiSbTe terminalpulse delivery/currenttail under4.5VcomplianceandactualaddedC remainsunverified jointcondition; no coldR extrapolation.',
       'All128columnsmustreturnbeforefirstverify; preventthermalreheatingduringcharge-removal byWL/isolation/controlsequence.',
       'I-V samples+TTcap are nominalmixed evidence; no processcorner/noise/thermal/silicon guarantee.'],
      'not_used_for_rho_tau':True}

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--native',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    if a.out.exists():raise ValueError('no overwrite')
    data=json.loads(Path(__file__).with_name('hv_data.json').read_text());n=json.loads(a.native.read_text())
    out=evaluate(data,n);a.out.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'status':out['status'],'return':out['return'],'level_translation':out['level_translation'],'read_R_upper_ohm':out['nominal_read_isolator_R_upper_ohm'],'caps':out['caps']}))
