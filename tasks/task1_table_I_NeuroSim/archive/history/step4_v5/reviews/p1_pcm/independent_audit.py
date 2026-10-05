#!/usr/bin/env python3
"""Independent PCM read/blocked-boundary audit; imports no production aggregator/model."""
import json,math,hashlib,argparse,itertools
from pathlib import Path

def mm(A,B):return [[sum(x*y for x,y in zip(row,col)) for col in zip(*B)] for row in A]
def mv(A,v):return [sum(x*y for x,y in zip(row,v)) for row in A]
def expm(A,t):
    z=len(A);norm=max(sum(abs(x*t) for x in row) for row in A);scale=max(0,math.ceil(math.log2(max(norm/.2,1))))
    X=[[x*t/2**scale for x in row] for row in A];E=[[float(i==j) for j in range(z)] for i in range(z)];term=[row[:] for row in E]
    for k in range(1,35):
        term=[[v/k for v in row] for row in mm(term,X)];E=[[E[i][j]+term[i][j] for j in range(z)] for i in range(z)]
    for _ in range(scale):E=mm(E,E)
    return E

def circuit_A(R,C,counts,sourceR,mask=None):
    g=[counts[i]/R[i] if mask is None or mask[i] else 0 for i in range(4)];den=1/sourceR+sum(g)
    G=[[(-g[i]*g[j]/den)+(g[i] if i==j else 0) for j in range(4)] for i in range(4)]
    return [[-G[i][j]/(counts[i]*C[i]) for j in range(4)] for i in range(4)]

def run(runpath,out):
    r=json.loads((runpath/'input.json').read_text());p=r['resolved_parameters'];n=json.loads((runpath/'resolved.json').read_text());m=json.loads((runpath/'case_model.json').read_text());result=json.loads((runpath/'result.json').read_text());checks=[]
    def ck(k,good,evidence):checks.append({'id':k,'passed':bool(good),'evidence':evidence})
    K=r['input']['logical']['K'];N=r['input']['logical']['N'];S=int(n['native_sa_count']);U=p['cols']-S
    counts={'logical_bytes':K*N,'physical_bits':8*K*N,'RESET_batches':math.ceil(8*K*N/(p['cols']//p['write_mux'])),'SET_slots':math.ceil(8*K*N/(p['cols']//p['write_mux'])),'read_groups':K*math.ceil(8*N/S),'positive_updates':7*K*math.ceil(8*N/S),'sign_updates':K*math.ceil(8*N/S)}
    ck('independent_mapping_counts',counts=={'logical_bytes':2048,'physical_bits':16384,'RESET_batches':1024,'SET_slots':1024,'read_groups':256,'positive_updates':1792,'sign_updates':256},counts)
    localR=p['source_metal_resistivity_ohm_m']*p['rows']*p['cell_pitch_y_m']/(p['source_column_width_m']*p['source_column_thickness_m'])
    sourceR=p['source_metal_resistivity_ohm_m']*(p['cols']+S)*p['cell_pitch_x_m']/(p['source_bus_width_m']*p['source_bus_thickness_m'])
    Ccouple=8.8541878128e-12*p['source_dielectric_relative_permittivity']*p['source_column_width_m']*p['rows']*p['cell_pitch_y_m']/p['source_BL_spacing_m']+p['source_fringe_F_per_m']*p['rows']*p['cell_pitch_y_m']
    C=n['sa_effective_node_cap_F'];Cu=n['array_BL_cap_F']+Ccouple+n['write_off_drain_added_to_read_F']+(n['native_sa_input_cap_F']-n['array_BL_cap_F'])/(p['read_mux']+1)
    common=p['access_resistance_ohm']+n['array_col_res_ohm']+n['actual_mux_res_ohm']+localR
    Rref=p['reference_resistance_ohm']+n['array_col_res_ohm']+localR+n['reference_switch_R_ohm'];physical_counts=[1,S-1,S,U];cap=[C,C,C*p['reference_cap_ratio'],Cu]
    t=m['reference_network']['develop_s'];samples=[]
    for state,cellR in [('on',p['on_accept_max_ohm']),('off',p['off_accept_min_ohm'])]:
      for other,hidden,history,skew in itertools.product([p['on_accept_min_ohm'],p['off_accept_max_ohm']],[p['on_accept_min_ohm'],p['off_accept_max_ohm']],[0.,p['unselected_BL_initial_max_V']],[-p['enable_skew_limit_s'],0.,p['enable_skew_limit_s']]):
        R=[cellR+common,other+common,Rref,hidden+p['access_resistance_ohm']+n['array_col_res_ohm']+localR]
        initial=[p['read_voltage_V']]*3+[history]
        if skew!=0:
          mask=[False,False,True,False] if skew<0 else [True,True,False,True]
          initial=mv(expm(circuit_A(R,cap,physical_counts,sourceR,mask),abs(skew)),initial)
        A=circuit_A(R,cap,physical_counts,sourceR);v=mv(expm(A,t),initial);dv=mv(A,v)
        g=[physical_counts[i]/R[i] for i in range(4)];vs=sum(g[i]*v[i] for i in range(4))/(1/sourceR+sum(g))
        kcl=sum(g[i]*(v[i]-vs) for i in range(4))-vs/sourceR
        edot=sum(physical_counts[i]*cap[i]*v[i]*dv[i] for i in range(4));loss=sum(physical_counts[i]*(v[i]-vs)**2/R[i] for i in range(4))+vs*vs/sourceR
        margin=v[2]-v[0] if state=='on' else v[0]-v[2]
        samples.append({'state':state,'otherR':other,'hiddenR':hidden,'historyV':history,'skew_s':skew,'margin_V':margin,'KCL_residual_A':kcl,'energy_balance_residual_W':edot+loss,'energy_decay_W':edot,'voltages':v})
    goal=p['sense_threshold_V']+p['sense_error_budget_V'];minimum=min(x['margin_V'] for x in samples)
    ck('independent_matrix_exponential_RC',len(samples)==48 and minimum>=goal-1e-9,{'contexts':48,'minimum_margin_V':minimum,'goal_V':goal,'producer_minimum_V':m['reference_network']['min_margin_V'],'time_s':t,'method':'Reducednodalconductancematrix,scaling/squaringexponential;noimportofRK4producer'})
    ck('charge_power_KCL',max(abs(x['KCL_residual_A']) for x in samples)<1e-12 and max(abs(x['energy_balance_residual_W']) for x in samples)<1e-12 and max(x['energy_decay_W'] for x in samples)<=0,{'max_KCL_A':max(abs(x['KCL_residual_A']) for x in samples),'max_energy_error_W':max(abs(x['energy_balance_residual_W']) for x in samples)})
    T=1/p['clock_Hz'];pre=n['sa_precharge_per_group_s']+max(T,n['precharge_external_RC_s']*max(1,p['reference_cap_ratio'])+n['precharge_control_s'])
    front=n['WL_address_setup_s']+n['group_select_s']+n['native_mux_s']+pre+n['precharge_control_s']+max(n['WL_enable_edge_only_s'],n['reference_isolation_edge_s'])+t+T+max(n['WL_release_s'],n['reference_isolation_edge_s'])
    operand=n['group_select_s']+max(n['weight_group_select_s']+n['extra_shift_select_s']+n['extra_shifted_weight_mux_s']+n['data_zero_mask_s'],n['input_bit_select_s']+n['data_zero_mask_s'],n['extra_accumulator_feedback_mux_s'])
    tail=n['add_sub_result_select_s']+n['accumulator_keep_s'];add=max(T,operand+n['extra_25bit_adder_s']+tail+n['signed_capture_s']);sub=max(T,operand+n['signed_correction_s']+tail+n['signed_capture_s'])
    delta=math.ceil(K*8/p['input_port_bits'])*max(T,n['input_ingress_select_s']+n['input_capture_s'])+max(T,n['state_clear_s'])+K*max(T,n['input_row_select_s']+n['input_row_capture_s'])+counts['read_groups']*(front+max(T,n['weight_keep_s']+n['weight_hold_capture_s']))+counts['positive_updates']*add+counts['sign_updates']*sub
    ck('independent_complete_read_count',abs(delta-result['delta_S_raw_s'])<1e-15,{'independent_delta_s':delta,'reported_delta_s':result['delta_S_raw_s'],'conditional_read_rho_MB_s':K/delta/1e6})
    ck('physical_clear_and_hold',n['state_clear_bits']>=N*25 and n['state_clear_gates']>=2*n['state_clear_bits'] and n['state_clear_s']>0 and min(add,sub)>=T,{'clear_bits':n['state_clear_bits'],'clear_gates':n['state_clear_gates'],'MACfullperiod_s':T})
    ck('resident_block_correctly_suppressed',result['status']=='blocked' and m['program_outcome']=='blocked' and m['resident_stages']==[] and result['resident_s'] is None and 'tau_MB_per_s' not in result,{'blocked_stage':m['blocked_stage'],'no_rho_tau_pair':True})
    audit={'review_status':'partial_read_model_verified_resident_blocked' if all(x['passed'] for x in checks) else 'changes_requested','scope':'Read/control/countingonly;notfullPCMserviceorindependentfoundryvalidation','role_disclosure':'MRAMauthor;noPCMproduction;sharedinterfaceissuesraisedbutsharedcodeownedbyintegrator','fresh_run':str(runpath),'input_sha256':r['input_sha256'],'computational_manifest':json.loads((runpath/'computational_manifest.json').read_text()),'checks':checks,'conditions':m['conditions'],'exact_missing_resident_port':m['blocked_stage'],'RC_samples':samples,'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    out.write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'status':audit['review_status'],'checks_failed':[x['id'] for x in checks if not x['passed']],'rho_read':K/delta/1e6,'min_margin':minimum}))
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--run',type=Path,required=True);a.add_argument('--out',type=Path,required=True);args=a.parse_args()
 if 'CloudStorage' in str(args.out.resolve()):raise SystemExit('Detailedauditmuststaylocal')
 run(args.run,args.out)
