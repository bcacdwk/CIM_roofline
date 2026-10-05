"""Shared-SL capacitor KCL including grounded inactive BL string return paths.

Tests a real passive-SL alternative, not an assumed feedback gain. No service
point is emitted. Source16pF load is a parameter, not an inherited total delay.
"""
from string_probe import String
import math,json,argparse,pathlib

def run():
    p=String();layers=16;idx=8;bg=[j%2 for j in range(layers)];bg[idx]=0
    high=bg.copy();high[idx]=1
    grids={}
    step=.1/100
    for name,vbl,pattern in [('active_on',.2,bg),('active_off',.2,high),('ground_on',0.,bg),('ground_off',0.,high)]:
        grids[name]=[p.solve(layers,idx,pattern,1.,vbl,j*step)['current_A'] for j in range(101)]
    def iv(name,v):
        x=max(0.,min(100.,v/step));a=min(99,int(x));f=x-a
        return grids[name][a]*(1-f)+grids[name][a+1]*f
    C=16e-12;nmax=1152*9;ntotal=13824*3;time=40e-9
    def integrate(n,C,background_on):
        z=0.;dt=time/400;charge=0
        def rhs(v):return n*iv('active_on',v)+(nmax-n)*iv('active_off',v)+(ntotal-nmax)*iv('ground_on' if background_on else 'ground_off',v)
        for _ in range(400):
            a=rhs(z);b=rhs(z+dt*a/C);q=.5*(a+b)*dt;charge+=q;z+=q/C
        return {'SL_V':z,'charge_C':charge,'charge_identity_residual_C':charge-C*z,'net_current_final_A':rhs(z),'active_strings':n,'grounded_background_lowVT':background_on,'C_F':C,'integration_s':time}
    full=integrate(nmax,C,True)['SL_V'];adc_full_V=25e-6*time/C;refcode=round(full/adc_full_V*1023);samples=[]
    for Ctest in (8e-12,16e-12,32e-12):
        for n in (0,1,16,128,1024,nmax):
            for b in (False,True):
                z=integrate(n,Ctest,b);z['code_10bit_full_reference']=min(1023,max(0,round(z['SL_V']/adc_full_V*1023)));z['nominal_reconstructed_string_count']=z['code_10bit_full_reference']*nmax/refcode;z['actual_count_for_error_only']=n;samples.append(z)
    isolated=[z for z in samples if z['active_strings']==1 and z['C_F']==C]
    zero=[z for z in samples if z['active_strings']==0 and z['C_F']==C]
    half=[z for z in samples if z['active_strings']==1024 and z['C_F']==C]
    return {'status':'sharedSL_passive_alternative_mechanism_probe_only','source_C_F':C,'physical_strings_per_block':ntotal,'maximum_active_input_group_strings':nmax,
       'integration_time_s':time,'time_role':'finite engineering integration probe, not publishedWL/BL/SL total',
       'fullscale_reference_V':full,'ADC_full_range_V':adc_full_V,'full_reference_code':refcode,'isolated_cases':isolated,'zero_weight_cases':zero,'background_pattern_cases':half,'samples':samples,
       'findings':['InactiveBL=0 strings withlowselectedVT sink current whenSL rises; all41472physicalstrings cannot be omitted.',
       'A passiveSL cap produces input/weight-background-dependent gain. Two referencepages do not remove every loading pattern.',
       'The native10bit coarse range cannot resolve everyisolated2nA operand evenatnominal calibration; do notcallINT8exact.',
       'A qualified activeSL clamp/current-sense topology withactualports/gm/C/rails is still needed to preserve the intended source-current summation domain.',
       'Noold530-750nsor303nsreadslot used. Noformalrho/tau.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args();d=run();pathlib.Path(a.out).write_text(json.dumps(d,indent=2)+'\n')
    print(json.dumps({'out':a.out,'fullscale_V':d['fullscale_reference_V'],'isolated_codes':[x['code_10bit_full_reference'] for x in d['isolated_cases']],'1024codes_by_background':[x['code_10bit_full_reference'] for x in d['background_pattern_cases']]}))
