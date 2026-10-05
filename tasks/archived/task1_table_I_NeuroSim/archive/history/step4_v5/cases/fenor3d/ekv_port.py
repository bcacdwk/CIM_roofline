"""Four-layer vertical AND compact port, not a parallel-RRAM surrogate.

EKV1995 Eq28,30,31 gives forward-minus-reverse current. Device-specific
normalization and Vt come from FENOR02; slope factor/read Vds/port-C remain
explicit engineering model choices. This code contains no source-paper text.
"""
import math,itertools,json,argparse,pathlib,hashlib

class Port:
    def __init__(self,n=1.5,T=300.):
        self.n=n;self.ut=1.380649e-23*T/1.602176634e-19
        self.vt={1:-1.05,0:-.38}
        self.ispec=1.
        self.ispec=200e-9/self.current(-.5,.1,0.,1)
    @staticmethod
    def f(x):
        y=x/2
        return (y+math.log1p(math.exp(-y)))**2 if y>0 else math.log1p(math.exp(y))**2
    def current(self,gate,drain,source,state,vt_shift=0.):
        vp=(gate-self.vt[state]-vt_shift)/self.n
        return self.ispec*(self.f((vp-source)/self.ut)-self.f((vp-drain)/self.ut))
    def stack_current(self,gate_selected,gate_off,drain,source,states,shifts=None):
        if shifts is None:shifts=[0.]*len(states)
        return sum(self.current(gate_selected if j==0 else gate_off,drain,source,s,d)
                   for j,(s,d) in enumerate(zip(states,shifts)))
    def extrema(self,layers,gate_off=-.9,drain=.1,vt_bound=.05):
        out=[]
        for selected in (0,1):
            vals=[]
            for bg in itertools.product((0,1),repeat=layers-1):
                states=(selected,)+bg
                for dvt in (-vt_bound,vt_bound):
                    current=self.stack_current(-.5,gate_off,drain,0.,states,[dvt]*layers)
                    vals.append((current,states,dvt))
            out.append({'selected':selected,'min_A':min(vals)[0],'max_A':max(vals)[0],
                        'min_pattern':min(vals)[1:],'max_pattern':max(vals)[1:]})
        return {'layers':layers,'off_gate_V':gate_off,'read_drain_V':drain,'vt_shift_bound_V':vt_bound,
                'states':out,'state_current_separation_A':out[1]['min_A']-out[0]['max_A']}


def diagnostic():
    p=Port();samples=[]
    for state in (0,1):
        for gate in (-1.1,-1.,-.9,-.5,0.):
            for vd in (0.,.025,.05,.1,.2,.5):
                samples.append({'state':state,'gate_V':gate,'drain_V':vd,'current_A':p.current(gate,vd,0.,state)})
    assert all(x['current_A']>=-1e-25 for x in samples)
    assert all(p.current(-.5,0,0,s)==0 for s in (0,1))
    # D/S reciprocity and positive conductance are physical checks, not fit claims.
    reciprocal=max(abs(p.current(-.5,.1,.02,s)+p.current(-.5,.02,.1,s)) for s in (0,1))
    slopes={str(s):(p.current(-.5,.10001,0,s)-p.current(-.5,.09999,0,s))/2e-5 for s in (0,1)}
    f4=p.extrema(4);f8=p.extrema(8)
    # Finite state/gate conditions. Vt shifts are sourced as <=50mV report, not
    # probability distribution or independent worst-corner material package.
    bad0=p.extrema(4,0.);strong_off=p.extrema(4,-1.1)
    eps0=8.8541878128e-12;eps_fe=25.;Ag=1e-15;tfe=6e-9
    Cgate=eps0*eps_fe*Ag/tfe
    return {'status':'compact_electrical_probe_only','model':'EKV1995_eq28_30_31_frozen_threshold_FET',
      'fit_point':{'state':1,'gate_V':-.5,'assumed_drain_V':.1,'current_A':200e-9,'source':'FENOR02 Fig3(d) current scale; source drain bias not reported'},
      'model_parameters':{'n':p.n,'n_role':'engineering slope factor, not measured extraction','Is_A':p.ispec,'Vt_low_V':p.vt[1],'Vt_high_V':p.vt[0]},
      'other_gate_state_checks':{'lowstate_gate_minus1_V_A':p.current(-1.,.1,0,1),'source_visual_lowstate_gate_minus1_approx_A':10e-9,
        'highstate_gate_minus05_A':p.current(-.5,.1,0,0),'source_visual_highstate_gate_minus05_approx_A':.3e-9,
        'qualification':'approximate figure comparisons, not pixel-fit confidence limits or independent Vds validation'},
      'physical_checks':{'DS_reciprocity_residual_A':reciprocal,'positive_small_signal_gds_S':slopes,'zero_Vds_current_A':0},
      'four_layer':f4,'eight_layer_same_bias_diagnostic':f8,'gate0_nonoff_negative':bad0,'gate_minus11_probe':strong_off,
      'geometry_C':{'gate_area_m2':Ag,'FE_thickness_m':tfe,'epsilon_r_engineering':eps_fe,'gate_background_C_F':Cgate,
                    'note':'dielectric background only; nonlinear switching charge and terminal partitions not extracted'},
      'instantaneous_read_field_bound':{'selected_gate_V':-.5,'unselected_gate_V':-.9,'BL_max_V':.1,'max_abs_gate_channel_V':1.,'write_full_V':2.,
        'note':'below half full-write amplitude is only a field check; repeated-read duration/retention still requires qualification'},
      'not_closed':['negative-gate driver/body/well/logic interface', 'physical nonlinear FE switching charge/driver load',
        'repeated negative-off read stress domain vs published pulsed halfselect','qualified data/reference sense and shared SL network at actual native loads'],
      'samples':samples}

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--out',required=True);args=a.parse_args();d=diagnostic()
    pathlib.Path(args.out).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'out':args.out,'four_layer_gap_A':d['four_layer']['state_current_separation_A'],'eight_layer_gap_A':d['eight_layer_same_bias_diagnostic']['state_current_separation_A'],'heldout':d['other_gate_state_checks']}))
