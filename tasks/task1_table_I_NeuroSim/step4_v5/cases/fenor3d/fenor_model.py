"""Finite vertical-AND current/state + sourced HV compact-port reference.
No inherited complete read slot; layer load/leak and physical bias enter here.
"""
import math,json,pathlib
from ekv_port import Port

def hvdata():return json.loads(pathlib.Path(__file__).with_name('hv_table.json').read_text())

def cap_port(W,L,p):
    eps0=8.8541878128e-12;cox=3.9*eps0/p['toxm_m'];ext=1e-6
    return {'gate_F':cox*W*L+(p['cgso_F_per_m']+p['cgdo_F_per_m'])*W,
      'drain_F':p['cjs_F_per_m2']*W*ext+p['cjsws_F_per_m']*2*(W+3*ext)+p['cjswgs_F_per_m']*W+p['cgdo_F_per_m']*W,
      'active_geometry_m2':W*(L+2*ext)}

def ports(p):
    h=hvdata();n=cap_port(20e-6,.5e-6,h['model_C']);pp=cap_port(7e-6,.5e-6,h['model_C_P']);m=Port(p['channel_slope_factor'],p['temperature_K']);m.vt={1:p['low_state_Vt_V'],0:p['high_state_Vt_V']};m.ispec=1.;m.ispec=p['calibration_current_A']/m.current(p['calibration_gate_V'],p['calibration_drain_V'],0.,1)
    gateA=p['channel_width_m']*p['channel_length_m'];cg=8.8541878128e-12*p['FE_relative_permittivity']*gateA/p['FE_thickness_m']
    # One read isolation HVNMOS/BL, counted at both its physical terminals.
    Cbl=2*n['drain_F']+p['layers']*.1*cg+p['extra_sense_cap_F']+p['wire_cap_per_m']*p['layers']*p['layer_pitch_m']
    Cgate=p['physical_cols']*cg
    Csl=p['wire_cap_per_m']*p['physical_cols']*p['column_pitch_m']
    SLlocal=p['metal_rho_ohm_m']*p['physical_cols']*p['column_pitch_m']/(p['SL_width_m']*p['SL_thickness_m'])
    SLglobal=p['metal_rho_ohm_m']*p['lateral_lanes']*p['row_pitch_m']/(p['SL_width_m']*p['SL_thickness_m'])
    vshift=p['state_window_shift_V'];loShift=-vshift;hiShift=vshift
    def branch(states,v):return sum(m.current(p['selected_gate_V'] if j==0 else p['unselected_gate_V'],v,0,s,loShift if s else hiShift) for j,s in enumerate(states))
    high=branch([1]+[0]*(p['layers']-1),.2);low=branch([0]+[1]*(p['layers']-1),.2)
    readR=.05/h['N_read_lower_curve']['I'][1]
    driveI=min(h['N_drive_curve']['I'][2],h['P_drive_curve']['I'][2])
    # Gate translation/isolated wells are a finite characterized-port condition,
    # not a claim the positive5Vlevel-shifter is a full negative-rail design.
    gatecharge=Cgate*2+p['physical_cols']*cg*p['threshold_window_V']
    hv_settle=p['HV_control_allowance_s']+gatecharge/driveI
    return {'gate_C_each_WL_F':Cgate,'BL_C_F':Cbl,'SL_C_F':Csl,'cell_gate_C_F':cg,'SL_local_R_ohm':SLlocal,'SL_global_R_ohm':SLglobal,
      'HV_read_R_ohm':readR,'HV_drive_current_lower_A':driveI,'HV_gate_transition_s':hv_settle,
      'HV_N':n,'HV_P':pp,'read_high_A':high,'read_low_A':low,'device_model':m}


def sense(p,native):
    port=ports(p);m=port['device_model'];C=native['native_sense_node_cap_F']+p['follower_extra_cap_F'];Vdd=native['actual_native_gate_rail_V'];vth=native['native_vth_V']+p['follower_body_allowance_V']
    W=p['follower_width_F']*p['technology_nm']*1e-9
    beta=2*W*native['native_Ion_N_A_per_m']/(Vdd-native['native_vth_V'])**2/p['follower_length_ratio']
    vg=p['follower_gate_V'];Rref=p['reference_resistance_ohm']+native['reference_TG_R_n_native_ohm']*(Vdd-native['native_vth_V'])/(Vdd-.23-native['native_vth_V']);T=p['read_pulse_s'];h=T/1000
    port['HV_read_R_ohm']+=native['actual_mux_target_ohm']
    # All32lateralunits have128simultaneousbranches; sourcedreturnmetal hasrealIR.
    Iupper=port['read_high_A']+port['read_low_A']
    source_bound=Iupper*p['physical_cols']*(port['SL_local_R_ohm']+p['lateral_lanes']*port['SL_global_R_ohm'])
    shift=p['state_window_shift_V'];vlo=-shift;vhi=shift
    def F(v):return .5*beta*max(0.,vg-v-vth)**2
    def cur(v,state,offstate,source):
        x=max(0.,v)
        for _ in range(3):
            I=sum(m.current(p['selected_gate_V'] if j==0 else p['unselected_gate_V'],x,source,state if j==0 else offstate,vlo if (state if j==0 else offstate) else vhi) for j in range(p['layers']))
            x=max(source,v-I*port['HV_read_R_ohm'])
        return max(0.,I)
    results=[]
    for state,back,sv in [(1,0,source_bound),(0,1,0.)]:
        v=p['reset_residual_V'] if state else 0.;r=0. if state else p['reset_residual_V'];cross=None;wrong=0.
        for step in range(1000):
            # Both branches startparked0. Theirpositivebiasfollowers create
            # state-dependentvoltages. Referencehasitsownquietreturn.
            a=(F(v)-cur(v,state,back,sv))/C;b=(F(r)-r/Rref)/C
            v2=v+h*a;r2=r+h*b
            a2=(F(v2)-cur(v2,state,back,sv))/C;b2=(F(r2)-r2/Rref)/C
            v+=h*(a+a2)/2;r+=h*(b+b2)/2
            margin=(r-v) if state else (v-r);wrong=min(wrong,margin)
            if cross is None and margin>=p['sense_threshold_V']+p['sense_error_budget_V']:cross=(step+1)*h
        results.append({'state':state,'background':back,'source_bound_V':sv,'data_V':v,'reference_V':r,'margin_V':margin,'first_cross_s':cross,'wrong_polarity_V':wrong})
    return {'feasible':all(z['first_cross_s'] is not None and z['margin_V']>=p['sense_threshold_V']+p['sense_error_budget_V'] for z in results),
      'C_each_node_F':C,'beta_A_per_V2':beta,'nativeW_m':W,'length_ratio':p['follower_length_ratio'],'effective_vth_V':vth,
      'follower_bias_V':vg,'no_load_voltage_V':vg-vth,'source_return_bound_V':source_bound,'read_pulse_s':T,'results':results,
      'read_domain_field_bound_V':abs(p['unselected_gate_V'])+max(vg-vth,0.),
      'HV_control_s':port['HV_gate_transition_s'],'driver_current_lower_A':port['HV_drive_current_lower_A'],
      'sense_scope':'Finiteactive-source-followerbinaryport,nominalMOSIon/W/Vth+bodyallowance,longchannelW/L scaling;noPDKsignoff;nativeVSAabstractthresholdlatchafterfinitephysicaldevelopment'}
