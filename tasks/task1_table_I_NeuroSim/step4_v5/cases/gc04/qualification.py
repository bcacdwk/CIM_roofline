"""Finite GC04 charge/current, sampling and state checks for reference services.

Uses the native connected-node C and bias-R envelope; lumped charge integration
is followed by a separately charged worst-node RC settling guard. It is a compact
service-domain model, not a full transistor transient or ADC ENOB simulation.
"""
import math
from gc_model import Cell
from retention_probe import Leak

def qualify(p,f):
    cell=Cell(p['cell_temperature_K'],p['state_slope_factor'],p)
    C=f['total_connected_C_F'];Cd=f['ADC_node_C_F'];H=p['retention_limit_s'];Vdd=f['native_vdd_V'];Vth=f['native_vth_V']
    t=f['PWM_actual_short_s'];tr=f['PWM_actual_long_s']
    R=f['bank_MUX_effective_R_envelope_ohm'];Rrow=f['RWL_N_R_ohm']+p['rwl_wire_ohm']
    # Conservative full TG gate-charge budget counts each gate once, not an
    # invented confidence interval or a claim of perfect N/P cancellation.
    Qbound=(f['sample_TG_gate_n_F']+f['sample_TG_gate_p_F'])*Vdd
    iloff=f['native_Ioff_N_A_per_m']*f['sample_TG_width_n_m']+f['native_Ioff_P_A_per_m']*f['sample_TG_width_p_m']
    holdtime=1/p['clock_Hz']+f['native_ADC_s']+.5/p['clock_Hz']
    errbranch=Qbound/Cd+p['precharge_voltage_V']*p['precharge_error_fraction']+iloff*holdtime/Cd+p['precharge_voltage_V']*p['sampling_error_fraction']
    Cn=f['native_capIdealGate_F_per_m']*f['sample_TG_width_n_m'];Cp=f['native_capIdealGate_F_per_m']*f['sample_TG_width_p_m']
    Cgn=(f['native_capOverlap_F_per_m']+f['native_capFringe_F_per_m'])*f['sample_TG_width_n_m']
    Cgp=(f['native_capOverlap_F_per_m']+f['native_capFringe_F_per_m'])*f['sample_TG_width_p_m']
    def sample(v):
        # Nominal symmetric channel partition; complete native gate-charge
        # envelope above covers its uncertainty. Geometry is same onbothbranches.
        q=.5*(-Cn*max(Vdd-v-Vth,0)+Cp*max(v-Vth,0)+Vdd*(Cgp-Cgn))
        return v+q/Cd
    def code(v):
        return min((1<<p['adc_bits'])-1,max(0,int(math.floor(v/p['adc_reference_V']*(1<<p['adc_bits'])+.5))))
    cases=[]
    for name,nrow,positive,age,pulse in [('fresh_max',16,16,0,t),('aged_max',16,16,H,t),('aged_cancellation',16,8,H,t),('single_input',1,1,H,t),('refresh_positive',1,1,H,tr),('refresh_negative',1,0,H,tr)]:
        # One column represents16identicalphysicalcolumns;16×R accounts actual
        # sharedRWLcurrent. It is not16× throughput or a free isolated source.
        state=[[int(j<positive)] for j in range(nrow)]
        z=cell.integrate(state,age,pulse,C,Rrow*16,R,steps=80)
        vp=sample(z['positive_V'][0]);vn=sample(z['negative_V'][0]);qp,qn=code(vp),code(vn)
        z.update(name=name,age_s=age,sampled_positive_V=vp,sampled_negative_V=vn,positive_ADC_code=qp,negative_ADC_code=qn,difference_code=qn-qp,
          nominal_Q4_partial=(qn-qp)/16,expected_integer_for_error_only=2*positive-nrow,
          output_error=(qn-qp)/16-(2*positive-nrow),
          representation='ordinarypartialQ4' if not name.startswith('refresh') else 'refreshsignonly;longpulsehas16xgain')
        if name.startswith('refresh'):
            z['nominal_Q4_partial']=(qn-qp)/256
            z['output_error']=(qn-qp)/256-(2*positive-nrow)
        cases.append(z)
    # Alternative state-dependent leak family is a pressure check, not a second
    # measuredpopulation corner. Heldout400nA disagreement remainsinreport.
    pressure=Leak('off_access_subthreshold_plus_constant_sink')
    low0=cell.retained(False,0)['nominal_current_A'];ip=pressure.current(700e-9,H)-pressure.current(low0,H)
    # Bound current loss fromcommon-source andoutput slope ratherthanuseidealI/C.
    vsmax=16*p['cell_current_A']*Rrow
    gain=math.exp(-vsmax/cell.vslope)*(1+cell.lambda_eff*(p['current_valid_min_V']-.9))
    refresh_signal_lower=ip*gain*tr/C
    minV=min(z['minimum_cell_BL_V'] for z in cases)
    maxhold=max(z['sampled_positive_V'] for z in cases)+errbranch
    minhold=min(min(z['sampled_positive_V'],z['sampled_negative_V']) for z in cases)-errbranch
    write_current=2*p['adc_pair_lanes']*p['write_qualified_cap_F']*cell.vhigh/p['coarse_included_s']+p['adc_pair_lanes']*p['cell_current_A']
    checks=[{'id':'GC_cascode_headroom','passed':minV-vsmax>cell.cascode_headroom+4*cell.ut,'evidence':{'minimum_BL_V':minV,'source_bound_V':vsmax,'required_internal_and4UT_V':cell.cascode_headroom+4*cell.ut}},
      {'id':'GC_read_bias_domain','passed':minV>=p['current_valid_min_V'],'evidence':{'minimum_BL_V':minV,'model_min_V':p['current_valid_min_V']}},
      {'id':'GC_sampled_ADC_domain','passed':minhold>=0 and maxhold<=p['adc_reference_V'],'evidence':{'lower_V':minhold,'upper_V':maxhold,'branch_error_bound_V':errbranch}},
      {'id':'GC_refresh_sign_margin','passed':refresh_signal_lower>2*errbranch and cases[-2]['difference_code']>0 and cases[-1]['difference_code']<0,'evidence':{'pressure_signal_lower_V':refresh_signal_lower,'pair_error_bound_V':2*errbranch,'nominal_refresh_codes':[cases[-2]['difference_code'],cases[-1]['difference_code']]}},
      {'id':'GC_program_local_current','passed':write_current<=p['program_shared_supply_current_limit_A'],'evidence':{'coarse_plus_fine_current_bound_A':write_current,'declared_local_limit_A':p['program_shared_supply_current_limit_A']}},
      {'id':'GC_state_voltage_lifecycle','passed':0<=cell.retained(False,H)['node_V']<cell.retained(True,H)['node_V'] and cell.retained(True,0)['idle_node_V']<p['rwl_voltage_V'],'evidence':{'fresh_high':cell.retained(True,0),'aged_high':cell.retained(True,H),'aged_low':cell.retained(False,H)}}]
    return {'checks':checks,'cases':cases,'charge_sampling':{'perbranch_full_gate_charge_C':Qbound,'perbranch_error_bound_V':errbranch,'nominal_partition':.5,'hold_current_bound_A':iloff,'hold_time_bound_s':holdtime,'external_hold_F':p['external_hold_cap_F'],'ordinary_partial_error_bound_units':2*errbranch/(p['adc_reference_V']/(1<<p['adc_bits'])*16)},
      'retention_reference':{'kind':'state_dependent_voltage_relaxation','equilibrium_V':cell.leak_equilibrium_V,'tau_s':cell.leak_tau_s,'fit':'100/700nA sourceFF80C','heldout400nA_source_A':406e-9,'heldout400nA_model_A':Leak('ohmic_net_leak').current(400e-9,400e-6)},
      'scope':'Finiteuniform-column/active-row/current/chargechecks plusfullscalarencoding;nominalQ4approximate,notmeasuredENOBorall-cellholdingguarantee'}
