"""Finite-bandwidth hybrid SL receiver. Official LTC6268 parameters, explicit RC.
No legacy SL/WL total is used. No output is corrected using mathematical truth.
"""
import math,bisect,json
from pathlib import Path

def interp(xs,ys,x):
    if not xs[0]-1e-12<=x<=xs[-1]+1e-12:raise ValueError('SL left characterized string domain')
    i=min(max(1,bisect.bisect_left(xs,x)),len(xs)-1)
    return ys[i-1]+(ys[i]-ys[i-1])*(x-xs[i-1])/(xs[i]-xs[i-1])

class Receiver:
    def __init__(self,p,ports):self.p=p;self.ports=ports
    def current(self,v,count,active_slots,low_total,background='nominal',selected='data'):
        p=self.p;table=self.ports['tables'][selected+'_'+background];xs=self.ports['SL_grid_V'];total=p['bitlines']*p['ssl_count']
        on=interp(xs,table['active_on'],v);off=interp(xs,table['active_off'],v)
        ground_on=interp(xs,table['ground_on'],v);ground_off=interp(xs,table['ground_off'],v)
        low_ground=low_total-count;high_active=active_slots-count;high_ground=total-active_slots-low_ground
        if min(count,low_ground,high_active,high_ground)<0:raise ValueError('Inconsistent physical active/grounded state counts')
        return count*on+high_active*off+low_ground*ground_on+high_ground*ground_off
    def equilibrium(self,count,active_slots,low_total,background='nominal',selected='data'):
        p=self.p;A=p['amp_open_loop_gain'];Rf=p['feedback_R_ohm'];Vos=p['amp_offset_V'];lo,hi=self.ports['SL_grid_V'][0],self.ports['SL_grid_V'][-1]
        for _ in range(65):
            v=(lo+hi)/2;res=(A+1)*v-A*Vos-Rf*self.current(v,count,active_slots,low_total,background,selected)
            if res>0:hi=v
            else:lo=v
        v=(lo+hi)/2;vo=A*(Vos-v)
        vb=A/(1+A/2)*(p['buffer_bias_V']+p['buffer_offset_V']-vo/2)
        vn=(vo+vb)/2
        return [v,vo,vn,vb]
    def run(self,count,active_slots,low_total,background='nominal',selected='data',Cscale=1.):
        p=self.p;A=p['amp_open_loop_gain'];wt=2*math.pi*p['amp_GBW_Hz'];wp=wt/A
        Cf=p['feedback_C_F'];C=p['SL_cap_F']*Cscale+p['amp_common_C_F']+p['amp_differential_C_F']
        Cb=p['amp_common_C_F']+p['amp_differential_C_F'];Cfb=p['buffer_feedback_C_F'];R=p['feedback_R_ohm'];Rb=p['buffer_R_ohm']
        start=self.equilibrium(0,0,low_total,background,selected);target=self.equilibrium(count,active_slots,low_total,background,selected);z=start[:]
        dt=p['ode_step_s'];tol=p['adc_reference_V']/(2**p['adc_bits'])*p['settle_ADC_fraction'];t=0.;last_bad=0.;maxSL=abs(z[0]);peakI=0.;rail_ok=True
        def rhs(z):
            v,vo,vn,vb=z
            a=max(-p['amp_slew_down_V_s'],min(p['amp_slew_up_V_s'],wt*(p['amp_offset_V']-v)-wp*vo))
            b=max(-p['amp_slew_down_V_s'],min(p['amp_slew_up_V_s'],wt*(p['buffer_bias_V']+p['buffer_offset_V']-vn)-wp*vb))
            dv=(self.current(v,count,active_slots,low_total,background,selected)-(v-vo)/R+Cf*a)/(C+Cf)
            dn=((vo-vn)/Rb+(vb-vn)/Rb+Cfb*b)/(Cb+Cfb)
            return [dv,a,dn,b]
        # Fixed horizon is a convergence diagnostic; reported service is the last
        # threshold violation plus explicit hold, not this artificial horizon.
        steps=int(p['ode_horizon_s']/dt)
        for step in range(steps):
            a=rhs(z);b=rhs([z[i]+dt*a[i]/2 for i in range(4)]);c=rhs([z[i]+dt*b[i]/2 for i in range(4)]);d=rhs([z[i]+dt*c[i] for i in range(4)])
            z=[z[i]+dt*(a[i]+2*b[i]+2*c[i]+d[i])/6 for i in range(4)];t+=dt
            maxSL=max(maxSL,abs(z[0]));rail_ok &= -2.3<z[1]<2.3 and -2.3<z[3]<2.3
            peakI=max(peakI,abs(Cf*(a[1]-a[0])+(z[1]-z[0])/R+(z[1]-z[2])/Rb),abs(p['buffer_output_load_F']*a[3]+(z[3]-z[2])/Rb))
            if abs(z[3]-target[3])>tol or abs(z[0]-target[0])>p['SL_settle_tolerance_V']:last_bad=t
        code=lambda voltage:min(2**p['adc_bits']-1,max(0,math.floor(voltage/p['adc_reference_V']*2**p['adc_bits']+.5)))
        settled=abs(z[3]-target[3])<=tol and last_bad<t*.9
        return {'count':count,'background':background,'active_slots':active_slots,'low_total':low_total,'selected':selected,'Cscale':Cscale,'SL_steady_V':target[0],'TIA_steady_V':target[1],'ADC_steady_V':target[3],
                'ADC_code':code(target[3]),'baseline_code':code(start[3]),'delta_code':code(target[3])-code(start[3]),'settle_s':last_bad+dt,'settled':settled,'rail_valid':bool(rail_ok),'ADC_range_valid':0<target[3]<p['adc_reference_V'],'max_abs_SL_V':maxSL,'peak_amp_output_A':peakI,'end_error_V':z[3]-target[3]}

def diagnostics(p,ports):
    receiver=Receiver(p,ports);n=p['rows_per_group']*9
    total=p['bitlines']*p['ssl_count']
    cases=[(n,n,total,'nominal','reference',1.),(0,n,0,'nominal','reference',1.),(n//2,n//2,total,'nominal','reference',1.),
      (n,n,total//2,'nominal','data',1.),(1,3,3,'nominal','data',1.),(1024,n,total//2,'nominal','data',1.),(1024,n,1024,'nominal','data',1.),
      (n,n,total//2,'low_pass','data',1.),(n,n,total//2,'high_pass','data',1.),(n,n,total//2,'nominal','data',2.)]
    samples=[receiver.run(*args) for args in cases]
    full=samples[0]['ADC_code'];zero=samples[0]['baseline_code'];span=full-zero
    if span<=0:raise ValueError('Invalid calibration span')
    for s in samples:s['count_from_fixed_reference']=s['delta_code']*n/span;s['count_error_for_diagnostic_only']=s['count_from_fixed_reference']-s['count']
    return {'status':'finite_hybrid_receiver_model_reference','samples':samples,'calibration_zero_code':zero,'calibration_full_code':full,'gain_count_per_code':n/span,'maximum_settle_s':max(s['settle_s'] for s in samples if s['Cscale']==1.),'double_C_settle_s':samples[-1]['settle_s'],
      'valid':all(s['settled'] and s['rail_valid'] and s['ADC_range_valid'] and s['peak_amp_output_A']<.01 for s in samples),'amplifiers':128,'static_power_typ_W':128*p['amp_Iq_A']*5.,
      'precision':'10bit nominal code only; sparse counts may quantize to zero, pass-background gain residuals retained; not exactINT8/ENOB/noise distribution',
      'independent_load_check':'2xSLcap point not used for DC calibration','equations':'actual all-string terminal I(VSL), Csl/Cin/Cf KCL, finiteA0/GBW/slew forTIA and explicit inverting offsetbuffer'}
