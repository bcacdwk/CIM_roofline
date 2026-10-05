#!/usr/bin/env python3
"""Independent literal UMEM equations, Brent circuit roots and adaptive DOP853.
No production adapter or aggregation import. Native values are circuit inputs.
"""
import json,math,hashlib
from pathlib import Path
import numpy as np
from scipy.optimize import brentq
from scipy.integrate import solve_ivp
ROOT=Path(__file__).parent
I=json.loads((ROOT/'package/cases/mram/inputs.json').read_text()); B=I['base_parameters']
P={k[5:]:v for k,v in B.items() if k.startswith('umem_')}
RUN=Path('/Users/shine/neurosim/runs/step4-v5/p1/case-mram-reviewer-mram-final-ref-20261005')
N=json.loads((RUN/'resolved.json').read_text())
VDD=N['actual_tech_vdd_V'];VT=N['actual_tech_vth_V'];OV=VDD-VT
RL=B['source_strap_resistivity_ohm_m']*B['rows']*B['cell_pitch_y_m']/(B['source_strap_width_m']*B['source_strap_thickness_m'])
RR=B['source_strap_resistivity_ohm_m']*N['array_row_m']/(B['source_strap_width_m']*B['source_strap_thickness_m'])
RW=N['array_col_res_ohm']+RL;C=N['sa_effective_node_cap_F']
IN=N['actual_tech_Ion_N_A_per_m'];IP=(N['write_mux_native_Ion_A']-IN*N['write_mux_width_N_m'])/N['write_mux_width_P_m']
BA=2*N['actual_access_Ion_at_native_bias_A']/OV**2
BN=2*IN*N['actual_mux_n_m']/OV**2;BP=2*IP*N['actual_mux_p_m']/OV**2
BWN=2*IN*N['write_mux_width_N_m']/OV**2;BWP=2*IP*N['write_mux_width_P_m']/OV**2

def upper(x,a,d):return (x+a-math.sqrt((x-a)**2+d*d))/2

def lower(x,a,d):return (x+a+math.sqrt((x-a)**2+d*d))/2

def R(v,z):
 s=lower(upper(z,1.,.001),-1.,.001);q=.5*(1+v/math.sqrt(v*v+.0001))
 rho=q*P['rhot_ohm_m']+(1-q)*P['rhot_r_ohm_m']; vv=q*P['v0_V']+(1-q)*P['v0_r_V'];xx=q*P['x0_m']+(1-q)*P['x0_r_m'];rs=q*P['rs_ohm']+(1-q)*P['rs_r_ohm']
 tmr=P['tmr0']/(1+(v/P['vr0_V'])**2);ratio=2*(1+tmr)/(2+(1+s)*tmr)
 return ratio*rho*P['tm_m']/P['area_m2']*math.exp(P['tm_m']/xx)/(1+(v/vv)**2)+rs*P['areanom_m2']/P['area_m2']/(1+(v/P['vs0_V'])**2)+P['minr_ohm']

def dz(z,current):
 cp=lower(current,0,1e-10)-5e-11;cn=current-cp;z0=lower(upper(z,1.,1e-3),-1.,1e-3)
 a=upper(z,.999,1e-3);b=lower(z,-.999,1e-3);vol=P['tf_m']*P['area_m2']/(P['tfnom_m']*P['areanom_m2'])
 return (-1-z)*(-1+a)*(.5*z0-cp/(P['ic0_A']*vol))/P['tau0_s']+(1-z)*(1+b)*(.5*z0-cn/(P['ic0_r_A']*vol))/P['tau0_s']

def mos(vds,vgs,beta):
 over=max(0,vgs-VT);vd=max(0,min(over,vds));return beta*(over*vd-vd*vd/2)

def inverse(i,vgs,beta):
 over=max(0,vgs-VT)
 if 2*i>beta*over*over:return math.inf
 return 2*i/beta/(over+math.sqrt(max(0,over*over-2*i/beta))) if i else 0.

def tg(hi,lo,bn,bp):
 if hi<=lo:return 0.
 return mos(hi-lo,VDD-lo,bn)+mos(hi-lo,hi,bp)

def core(port,z,drop,bn,bp):
 sign=1 if port>0 else -1;v=abs(port)
 if v<=1e-16:return 0.,0.
 def residual(vm):
  current=vm/R(sign*vm,z)
  if sign>0:
   if bn+bp:
    va=inverse(current,VDD-drop,BA);bl=drop+va+vm+current*RW;available=tg(v,bl,bn,bp)
   else:available=mos(v-vm-current*RW-drop,VDD-drop,BA)
  else:
   if bn+bp:
    # In this voltage/current domain PMOS remains off at the low-side drop;
    # a root fallback independently handles any larger voltage.
    low=inverse(current,VDD,bn)
    if low>VT:
     low=brentq(lambda x:tg(x,0,bn,bp)-current,0,VDD,xtol=1e-14)
   else:low=0.
   source=low+current*RW+vm;available=mos(v-drop-source,VDD-source,BA)
  return current-available
 vm=brentq(residual,0,v,xtol=1e-14,rtol=1e-13)
 return sign*vm/R(sign*vm,z),sign*vm

def drop_root(v,lanes,bn,bp):
 return brentq(lambda d:d-lanes*RR*abs(core(v,1.001,d,bn,bp)[0]),0,abs(v),xtol=1e-14,rtol=1e-13)
DWP=drop_root(.6,32,BWN,BWP);DWN=drop_root(-.6,32,BWN,BWP);DR=drop_root(.15*1.01,64,0,0)

def integrate(initial,voltage,width,rtol=2e-10):
 drop=DWP if voltage>0 else DWN
 def fun(t,y):return [dz(y[0],core(voltage,y[0],drop,BWN,BWP)[0])]
 def crossing(t,y):return y[0]
 crossing.terminal=False
 sol=solve_ivp(fun,(0,width),[initial],method='DOP853',rtol=rtol,atol=rtol/10,max_step=4e-9,events=crossing,dense_output=True)
 assert sol.success
 states=sol.sol(np.linspace(0,width,1001))[0];vals=[core(voltage,x,drop,BWN,BWP) for x in states]
 return {'initial_state':initial,'port_V':voltage,'plateau_s':width,'final_state':float(sol.y[0,-1]),'crossing_s':float(sol.t_events[0][0]) if len(sol.t_events[0]) else None,'peak_current_A':max(abs(x[0]) for x in vals),'max_MTJ_V':max(abs(x[1]) for x in vals),'shared_drop_V':drop}

def ref_current(v):
 if v<=0:return 0.
 r=B['reference_resistance_ohm']+RL
 return brentq(lambda cur:cur-mos(v-cur*(r+32*RR),VDD-cur*32*RR,2*BN),0,v/r,xtol=1e-18,rtol=1e-13)

def read_check(states,time=1.23e-9):
 def data(initial_v,initial_z,drop):
  def f(t,y):
   cur=core(y[0],y[1],drop,BN,BP)[0];return [-cur/C,dz(y[1],cur)]
  sol=solve_ivp(f,(0,time),[initial_v,initial_z],method='DOP853',rtol=2e-11,atol=2e-13,max_step=5e-11);assert sol.success
  return list(map(float,sol.y[:,-1]))
 def reference(initial_v,duration):
  sol=solve_ivp(lambda t,y:[-ref_current(y[0])/C],(0,duration),[initial_v],method='DOP853',rtol=2e-11,atol=2e-13,max_step=5e-11);assert sol.success
  return float(sol.y[0,-1])
 p=data(.1515,states[0],DR);ap=data(.1485,states[1],0)
 early=reference(.1485,time+1e-10);late=reference(.1515,time-1e-10)
 return {'time_s':time,'P':[p[0],p[1]],'AP':[ap[0],ap[1]],'ref_early_low_V':early,'ref_late_high_V':late,'P_margin_V':early-p[0],'AP_margin_V':ap[0]-late,'required_V':.007,'passed':min(early-p[0],ap[0]-late)>=.007,'method':'Nonlinearinitialrefprechargeerror is integrated asinitialV, notscaledafterODE; Pmaxreturn/APzerodrop; Brent+DOP853'}

def counts():
 cells={(bank,row,col) for bank in range(8) for row in range(64) for col in range(64)};written=set();batches=0
 for bank in range(8):
  for row in range(64):
   for group in range(2):
    actual={(bank,row,col) for col in range(group*32,(group+1)*32)};assert not actual&written;written|=actual;batches+=1
 assert cells==written
 stream=4+1+64+128*(3+1+8)+1
 rows=[]
 for scenario,perpol in [('optimistic',6),('reference',11),('pessimistic',21)]:
  resident=1+batches*(1+1+2+2*perpol+3+1+1)+1
  rows.append({'scenario':scenario,'stream_cycles':stream,'resident_cycles':resident,'delta_S_s':stream*1e-7,'T_R_s':resident*1e-7,'rho_MB_per_s':64/(stream*1e-7)/1e6,'tau_MB_per_s':4096/(resident*1e-7)/1e6,'RI_star':resident/stream/64,'U_star':resident/stream})
 return {'cells':len(cells),'program_batches':batches,'payload_Byte':len(cells)//8,'stream_tiles':128,'updates':1024,'points':rows,'derivation':'fulladdressenumeration;32lanesglobalwrite;8banksparallelread;4ingressbeats;fullcyclehold/clear/MAC/compare;roundedpulse0and1separately'}

if __name__=='__main__':
 source=Path('/Users/shine/neurosim/runs/step4-v5/p1/mram-model-20261005/umem/1.0.1/code/umem.va');sha=hashlib.sha256(source.read_bytes()).hexdigest();assert sha=='07cec8af359e97c37ee711177b2e5c4dc63baf8ce422c12571089947de363523'
 out={'source_sha256':sha,'method':'LiteralVA303-355/macros independently rewritten; BrentKCL+Brentsharedreturn+DOP853; no productionmodule import','native_calibration':{'VDD':VDD,'Vth':VT,'beta_access':BA,'beta_read_N':BN,'beta_write_N':BWN,'native_effective_R_to_Ion_ratio':B['access_resistance_ohm']*N['actual_access_Ion_at_native_bias_A']/VDD},'drop_roots_V':{'write_positive':DWP,'write_negative':DWN,'read_max':DR},'count_audit':counts(),'pulses':[],'read_checks':[]}
 for name,width in [('optimistic',500e-9),('reference',1e-6),('pessimistic',2e-6)]:
  pts=[integrate(initial,voltage,width) for voltage in [.6,-.6] for initial in [-1.,1.]]
  out['pulses'].extend(pts)
  states=(min(q['final_state'] for q in pts if q['port_V']<0),max(q['final_state'] for q in pts if q['port_V']>0))
  rd=read_check(states);rd['scenario']=name;out['read_checks'].append(rd)
 # Another solve accuracy and worst allowed raw-state initial endpoint.
 out['convergence']=[integrate(1.,.6,500e-9,2e-12),integrate(-1.,-.6,500e-9,2e-12)]
 out['raw_endpoint_probes']=[integrate(1.001,.6,500e-9),integrate(-1.001,-.6,500e-9)]
 # Sufficient finite-slew construction fits reserved control clock; does not add spin acceleration.
 rmax=1/min(BWN*max(VDD-x-VT,0)+BWP*max(x-VT,0) for x in np.linspace(0,.6,10001))
 rc=(rmax+RW+32*RR)*N['write_total_connected_cap_F'];dc=max(q['peak_current_A'] for q in out['pulses'])
 ramp=N['write_total_connected_cap_F']*.6/(.01/32-dc);settle=math.log(1000)*rc
 wait=100e-9-2*max(1e-9,settle,N['write_column_driver_one_edge_s'])
 out['return_and_edge_certificate']={'Rmax_ohm':rmax,'connected_C_F':N['write_total_connected_cap_F'],'minimum_slew_for_10mA_s':ramp,'RC99p9_s':settle,'sufficient_slew_plus_settle_s':ramp+settle,'minimum_zero_bias_clock_wait_s':wait,'max_BL_after_zero_wait_V':.6*math.exp(-wait/rc),'read_rail_V':.15,'scope':'Fixed0Vcommandduringclockalignment;chargedBLhasTG/wirereturnpath;nominalcompactmodelandstablelocalrailcondition;notSTAorPDNsignoff'}
 assert all(x['passed'] for x in out['read_checks'])
 assert all(q['final_state']*(-1 if q['port_V']>0 else 1)>.98 for q in out['pulses']+out['raw_endpoint_probes'])
 (ROOT/'independent_audit.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'read_checks':out['read_checks'],'roots':out['drop_roots_V'],'return':out['return_and_edge_certificate'],'count_audit':out['count_audit']},indent=2))
