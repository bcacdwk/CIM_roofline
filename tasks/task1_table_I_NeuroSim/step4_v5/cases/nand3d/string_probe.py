"""Mechanism probe: finite-bias series MOS string using EKV Eq28/30/31.

This tries a sourced compact equation before declaring a parameter gap. It does
not fit any legacy WL/BL/SL time and is not an accepted SGVC service reference.
"""
import math,json,argparse,pathlib
UT=1.380649e-23*300/1.602176634e-19

def F(x):
    z=x/2
    return (z+math.log1p(math.exp(-z)))**2 if z>0 else math.log1p(math.exp(z))**2

def invF(y):
    if y<=0:return -1e6
    z=math.sqrt(y)
    return 2*(z+math.log1p(-math.exp(-z))) if z>1 else 2*math.log(math.expm1(z))

class String:
    def __init__(self,n=3.,low=-.8,high=1.7):
        self.n=n;self.low=low;self.high=high;self.ispec=1.
        z=self.solve(16,0,[j%2 for j in range(16)],1.,.2,0.)
        self.ispec=2e-9/z['current_A']
    def solve(self,layers,selected,states,vg,vbl,vsl,vpass=4.5,selector_gate=4.5):
        if vbl < vsl:
            z=self.solve(layers,layers-1-selected,list(reversed(states)),vg,vsl,vbl,vpass,selector_gate)
            return {**z,"current_A":-z["current_A"],"node_V":list(reversed(z["node_V"]))}
        # Two selectors and every unselected storage FET are actual series edges.
        # States are0=lowVT and1=highVT. Reference fit pattern is50% data occupancy.
        vps=[(selector_gate-.5)/self.n]+[((vg if j==selected else vpass)-(self.high if s else self.low))/self.n for j,s in enumerate(states)]+[(selector_gate-.5)/self.n]
        def endpoints(current):
            node=vsl;nodes=[node]
            for vp in vps:
                forward=F((vp-node)/UT)
                remain=forward-current/self.ispec
                if remain<=0:return float('inf'),nodes
                node=vp-UT*invF(remain);nodes.append(node)
            return node,nodes
        lo=0.;hi=min(self.ispec*F((vp-vsl)/UT) for vp in vps)
        for _ in range(70):
            mid=(lo+hi)/2
            if endpoints(mid)[0]>vbl:hi=mid
            else:lo=mid
        current=(lo+hi)/2;end,nodes=endpoints(current)
        return {'current_A':current,'node_V':nodes,'KVL_error_V':end-vbl,'series_devices':len(vps)}

def diagnostic():
    p=String();samples=[]
    for layers in (8,16,32):
        for state in (0,1):
            for vbl in (.05,.1,.2,.3):
                for vsl in (0.,.01,.03):
                    pattern=[j%2 for j in range(layers)];pattern[layers//2]=state
                    r=p.solve(layers,layers//2,pattern,1.,vbl,vsl)
                    samples.append({'layers':layers,'state':state,'VBL_V':vbl,'VSL_V':vsl,**r})
    curves={}
    for state in (0,1):
        pattern=[j%2 for j in range(16)];pattern[8]=state
        curves[str(state)]=[{'gate_V':vg,'current_A':p.solve(16,8,pattern,vg,.2,0.)['current_A']} for vg in (-1.5,-1.,-.5,0.,1.,2.,3.,4.,5.)]
    patterns=[]
    for bg in (0,1):
        pat=[bg]*16;pat[8]=0
        patterns.append({'background_state':bg,**p.solve(16,8,pat,1.,.2,0.)})
    # A measured Id-Vg plateau constrains the pass-limited mechanism, independent
    # of the2nA normalization point, though not a gds/dynamic validation.
    on=curves['0'];ratio=on[-1]['current_A']/next(x['current_A'] for x in on if x['gate_V']==1.)
    return {'status':'second_route_electrical_probe_not_service','fit':'16layer,50percentpattern,Vg1,VBL.2,Vpass4.5 ->2nA',
      'parameters':{'Is_A':p.ispec,'n_engineering_curve_shape':p.n,'low_Vt_engineering_V':p.low,'high_Vt_engineering_V':p.high},
      'series_mechanism':'one selected andlayers-1 pass memory FETs +GSL+SSL;common current solves every internal node',
      'plateau_gate1_to5_ratio':ratio,'curves':curves,'background_pattern_checks':patterns,'samples':samples,
      'qualifications':['Vt locations and n approximate engineering shape parameters; sourceFig6 does not uniquely extract them.',
      '2nA is a calibration current; the measured Vg plateau andoff limit are separate local checks.',
      'This tries a series field-effect network. It does not assert missing SGVC IdVds and capacitive transients are verified.',
      '32layers is a model extension; all cellparameters fixed from16layer fit, no renormalization to force2nA.',
      'No sharedSL amplifier,HVpassdriver,portC orcompleteP/E closure here. Noformalrho/tau.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();d=diagnostic();pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'out':a.out,'plateau_ratio':d['plateau_gate1_to5_ratio'],'parameters':d['parameters']}))
