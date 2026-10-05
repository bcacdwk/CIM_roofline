#!/usr/bin/env python3
"""Deterministic MRAM branch of UMEM 1.0.1; series-access circuit adaptation.

UMEM copyright (c) 2026 Chien-Ting Tung, MIT; see LICENSE.umem.txt.
Source SHA 3cd6275284951b8033c9637bd8094ec05b716a4b.
Manual §6,7; umem.va lines 303–355. No thermal noise or WER prediction.
"""
import math

PARAMETERS={'tm_m':1e-9,'area_m2':49e-16,'areanom_m2':49e-16,'tf_m':5e-9,
 'tfnom_m':5e-9,'rhot_ohm_m':4.6e-3,'rhot_r_ohm_m':4.6e-3,
 'x0_m':5e-10,'x0_r_m':5e-10,'ic0_A':3.8e-5,'ic0_r_A':2.6e-5,
 'v0_V':1.5,'v0_r_V':2.0,'tmr0':1.13,'vr0_V':0.8,'tau0_s':1.8e-8,
 'rs_ohm':0.1,'rs_r_ohm':0.1,'vs0_V':0.5,'minr_ohm':0.001}

# Keep source's intentionally inverted names: smoothmax is an upper clamp,
# smoothmin is a lower clamp. Renaming without these semantics changes dynamics.
def smoothmax(x,upper,d):return 0.5*(x+upper-math.hypot(x-upper,d))
def smoothmin(x,lower,d):return 0.5*(x+lower+math.hypot(x-lower,d))
def state_clamp(s):return smoothmin(smoothmax(s,1.,1e-3),-1.,1e-3)

def resistance(v,s,p=PARAMETERS):
    t0=state_clamp(s)
    blend=0.5*(v/math.hypot(v,0.01)+1)
    x0=p['x0_m']*blend+p['x0_r_m']*(1-blend)
    v0=p['v0_V']*blend+p['v0_r_V']*(1-blend)
    rho=p['rhot_ohm_m']*blend+p['rhot_r_ohm_m']*(1-blend)
    rs=p['rs_ohm']*blend+p['rs_r_ohm']*(1-blend)
    tmr=p['tmr0']/(1+(v/p['vr0_V'])**2)
    ratio=2*(1+tmr)/(2+(1+t0)*tmr)
    return ratio*rho/p['area_m2']*p['tm_m']*math.exp(p['tm_m']/x0)/(1+(v/v0)**2)+rs/(1+(v/p['vs0_V'])**2)*p['areanom_m2']/p['area_m2']+p['minr_ohm']

def circuit(vport,s,raccess,p=PARAMETERS):
    if vport==0:return 0.,0.,0.
    lo,hi=min(0,vport),max(0,vport)
    for _ in range(34):
        vm=(lo+hi)/2
        residual=vm+vm/resistance(vm,s,p)*raccess-vport
        if residual>0:hi=vm
        else:lo=vm
    vm=(lo+hi)/2;i=vm/resistance(vm,s,p)
    return i,vm,vport-vm

def rhs(s,i,p=PARAMETERS):
    ip=smoothmin(i,0,1e-10)-5e-11;inn=i-ip
    t0=state_clamp(s);t1=smoothmax(s,0.999,1e-3);t2=smoothmin(s,-0.999,1e-3)
    volume_ratio=p['tf_m']*p['area_m2']/(p['tfnom_m']*p['areanom_m2'])
    return (-1-s)/p['tau0_s']*(-1+t1)*(0.5*t0-ip/(p['ic0_A']*volume_ratio))+(1-s)/p['tau0_s']*(1+t2)*(0.5*t0-inn/(p['ic0_r_A']*volume_ratio))

def mos_circuit(vport,s,raccess,p=PARAMETERS,vdd=1.1,vth=0.5016636,rwire=0.,shared_return_ohm=0.,active_lanes=1,native_vdd=None,shared_background_wire_ohm=None):
    """3-terminal long-channel access adapter, native low-VDS R matched.

    BL/SL are 0 or abs(vport), gate native VDD. Reverse write includes source
    degeneration. rwire is a separate series resistance. No body-effect fit,
    no claimed BSIM accuracy or process-variation success probability.
    """
    swing=abs(vport);native_vdd=vdd if native_vdd is None else native_vdd;nom=native_vdd-vth
    if swing==0:return 0.,0.,0.
    if shared_return_ohm>0:
        # Self-consistent all-P load is the maximum current over the full state
        # domain. Holding this envelope throughout a pulse is conservative for
        # a mixed-state victim; it is not a probability or an extra memory copy.
        background_wire=rwire if shared_background_wire_ohm is None else shared_background_wire_ohm
        bg=mos_circuit(vport,1.001,raccess,p,vdd,vth,background_wire+active_lanes*shared_return_ohm,0.,1,native_vdd)[0]
        drop=active_lanes*abs(bg)*shared_return_ohm
        eff=vport-math.copysign(drop,vport)
        # Positive write/read return is lifted; negative source-drive loses rail
        # voltage while the device bottom/source remains referred to ground.
        gate=vdd-drop if vport>0 else vdd
        im,vm,vr=mos_circuit(eff,s,raccess,p,gate,vth,rwire,0.,1,native_vdd)
        return im,vm,vport-vm
    def mos(vds,vgs):
        ov=max(vgs-vth,0.)
        if ov==0 or vds<=0:return 0.
        z=min(vds,ov)
        return (ov*z-z*z/2)/(raccess*nom)
    lo,hi=0.,swing
    for _ in range(34):
        vm=(lo+hi)/2;iv=vm/resistance(vm if vport>0 else -vm,s,p)
        node=swing-vm-iv*rwire
        avail=mos(node,vdd) if vport>0 else mos(node,vdd-vm)
        if iv>avail:hi=vm
        else:lo=vm
    vm=(lo+hi)/2*(1 if vport>0 else -1)
    return vm/resistance(vm,s,p),vm,vport-vm

def pulse(initial,vport,duration,raccess=1000.,dt=5e-11,edge=1e-9,record=False,p=PARAMETERS,mos=None):
    """Whole trapezoid: duration is plateau; explicit rise/fall are additional."""
    total=duration+2*edge;steps=math.ceil(total/dt);h=total/steps;s=initial
    energy=0.;imax=0.;vmax=0.;cross=None;trace=[]
    def voltage(t):
        if edge==0:return vport
        return vport*max(0,min(1,t/edge,(total-t)/edge))
    def branch(v,y):
        return circuit(v,y,raccess,p) if mos is None else (mos(v,y) if callable(mos) else mos_circuit(v,y,raccess,p,**mos))
    def f(t,y):return rhs(y,branch(voltage(t),y)[0],p)
    for n in range(steps):
        t=n*h;i,vm,vr=branch(voltage(t),s)
        energy+=abs(voltage(t)*i)*h;imax=max(imax,abs(i));vmax=max(vmax,abs(vm))
        if record and (n%max(1,steps//150)==0):trace.append([t,s,i,vm,vr])
        k1=f(t,s);k2=f(t+h/2,s+h*k1/2);k3=f(t+h/2,s+h*k2/2);k4=f(t+h,s+h*k3)
        sn=s+h*(k1+2*k2+2*k3+k4)/6
        if not math.isfinite(sn) or abs(sn)>1.01:raise ValueError('Invalid state integration')
        if cross is None and s*sn<0:cross=t+h
        s=sn
    return {'initial_state':initial,'final_state':s,'port_voltage_V':vport,'plateau_s':duration,'edge_each_s':edge,'waveform_s':total,'crossing_s':cross,'max_current_A':imax,'max_MTJ_voltage_V':vmax,'driver_energy_J':energy,'access_ohm':raccess,'trace_columns':['t_s','s','I_A','V_MTJ_V','V_access_V'],'trace':trace,'model':'UMEM1.0.1 deterministic,no stochastic/thermal BER'}

class BiasPort:
    """Native-Ion/width/Vth-anchored three-terminal access and complementary TG.

    beta=2*Ion/(VDD-Vth)^2 is a declared saturation-anchor compact extension.
    CACTI effective Ron sizes the actual native transistor but is NOT treated as
    its small-VDS resistance. Body effect/velocity saturation are not calibrated.
    The column TG is at BL: high-side for positive current, low-side for negative.
    BL/SL remain 0..abs(port); gate rails are0/nativeVDD. Return is an explicit
    shared rail. A strongest-state background provides a conservative current
    context over the stated |raw_state|<=1.001 domain, not a probability bound.
    """
    def __init__(self,p,vdd,vth,beta_access,beta_tg_n,beta_tg_p,wire_ohm,return_ohm=0.,active_lanes=1,background_wire_ohm=None,background_has_tg=True,background_voltage_limit=None):
        self.p=p;self.vdd=vdd;self.vth=vth;self.ba=beta_access;self.bn=beta_tg_n;self.bp=beta_tg_p
        self.wire=wire_ohm;self.ret=return_ohm;self.count=active_lanes
        self.bgwire=wire_ohm if background_wire_ohm is None else background_wire_ohm
        self.bgtg=background_has_tg;self.bgV=background_voltage_limit;self.cache={};self.max_drop=0.
    def mos(self,vds,vgs,beta):
        over=max(vgs-self.vth,0.);z=max(0,min(vds,over))
        return beta*(over*z-z*z/2)
    def inv_mos(self,i,vgs,beta):
        over=max(vgs-self.vth,0.)
        if beta<=0 or i>.5*beta*over*over:return math.inf
        return over-math.sqrt(max(0,over*over-2*i/beta))
    def tg(self,hi,lo):
        if hi<=lo:return 0.
        return self.mos(hi-lo,self.vdd-lo,self.bn)+self.mos(hi-lo,hi,self.bp)
    def low_tg_drop(self,i):
        if self.bn+self.bp==0:return 0.
        q=self.inv_mos(i,self.vdd,self.bn)
        if q<self.vth:return q # PMOS off, exact inverse of the NMOS branch
        lo,hi=0.,self.vdd
        for _ in range(28):
            mid=(lo+hi)/2
            if self.tg(mid,0)<i:lo=mid
            else:hi=mid
        return (lo+hi)/2
    def core(self,port,s,drop,wire,with_tg):
        swing=abs(port)
        if swing<=0:return 0.,0.,0.
        lo,hi=0.,swing
        for _ in range(30):
            vm=(lo+hi)/2;iv=vm/resistance(vm if port>0 else -vm,s,self.p)
            if port>0:
                if with_tg:
                    vd=self.inv_mos(iv,self.vdd-drop,self.ba)
                    bl=drop+vd+vm+iv*wire
                    available=self.tg(swing,bl)
                else:
                    vd=swing-vm-iv*wire-drop
                    available=self.mos(vd,self.vdd-drop,self.ba)
            else:
                bl=(self.low_tg_drop(iv) if with_tg else 0.)+iv*wire
                source=bl+vm;vd=swing-drop-source
                available=self.mos(vd,self.vdd-source,self.ba)
            if iv>available:hi=vm
            else:lo=vm
        vm=(lo+hi)/2*(1 if port>0 else -1)
        return vm/resistance(vm,s,self.p),vm,port-vm
    def __call__(self,port,s):
        if port==0:return 0.,0.,0.
        if self.ret:
            key=port if self.bgV is None else math.copysign(self.bgV,port)
            if key not in self.cache:
                drop=0.
                for _ in range(9):
                    ib=self.core(key,1.001,drop,self.bgwire,self.bgtg)[0]
                    drop=self.count*abs(ib)*self.ret
                self.cache[key]=drop;self.max_drop=max(self.max_drop,drop)
            drop=self.cache[key]
        else:drop=0.
        return self.core(port,s,drop,self.wire,self.bn+self.bp>0)
    def resistive_reference_current(self,voltage,resistor,Rn0,branches,return_R):
        """Fixed resistor plus actual N-only isolation; reference quietreturn KCL."""
        # Native N-only TG width doubles, so its Ion anchor is reconstructed by
        # the caller and exposed as beta_ref rather than native effective Ron.
        beta_ref=Rn0;lo,hi=0.,voltage/max(resistor,1e-30)
        for _ in range(30):
            i=(lo+hi)/2;vs=i*branches*return_R
            vd=voltage-i*resistor-vs
            actual=self.mos(vd,self.vdd-vs,beta_ref)
            if i>actual:hi=i
            else:lo=i
        return (lo+hi)/2
