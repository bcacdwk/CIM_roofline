#!/usr/bin/env python3
"""PCM local state/mapping/physics adapter. No unqualified Roofline service export."""
import math

def byte_bits(value):
    if not -128 <= value <= 127: raise ValueError("not signed INT8")
    return [(value & 255) >> b & 1 for b in range(8)]

def serial_mac(inputs, weights, accumulator_bits=25):
    """Actual bit-select/add/sub sequence; each row's fetched bits remain held."""
    if len(inputs) != len(weights) or not weights: raise ValueError("shape")
    n=len(weights[0]); acc=[0]*n; mask=(1<<accumulator_bits)-1
    for x,row in zip(inputs,weights):
        if len(row)!=n: raise ValueError("ragged")
        decoded=[sum(bit*((1<<b) if b<7 else -128) for b,bit in enumerate(byte_bits(w))) for w in row]
        for b,enabled in enumerate(byte_bits(x)):
            if enabled:
                for j,w in enumerate(decoded):
                    value=acc[j]+w*((1<<b) if b<7 else -128)
                    if not -(1<<(accumulator_bits-1)) <= value < (1<<(accumulator_bits-1)): raise OverflowError("physical accumulator")
                    u=value&mask;acc[j]=u-(1<<accumulator_bits) if u&(1<<(accumulator_bits-1)) else u
    return acc

def full_cover_counts(k,n,write_lanes=16,sense_lanes=64):
    bits_per_row=8*n
    return {"logical_payload_bytes":k*n,"physical_data_bits":k*bits_per_row,
            "physical_rows":k,"reset_batches":k*math.ceil(bits_per_row/write_lanes),
            "set_reserved_batches":k*math.ceil(bits_per_row/write_lanes),
            "verify_row_reads":k,"verify_sense_groups":k*math.ceil(bits_per_row/sense_lanes),
            "serial_add_groups":k*8*math.ceil(n/(sense_lanes//8)),
            "operand_hold_bits":bits_per_row,"output_hold_bits":n*25,
            "scope":"RESET full row by actual write lanes; SET target-one mask in reserved equal slots; verify every physical bit before row commit. No data-equality skip."}

def accept_programmed_row(target_bits, final_resistances, on_max_ohm, off_min_ohm):
    """Offline characterized-window diagnostic; NOT implemented single-threshold hardware verify."""
    if len(target_bits)!=len(final_resistances):raise ValueError("coverage")
    failures=[]
    for i,(b,r) in enumerate(zip(target_bits,final_resistances)):
        if b not in (0,1) or not math.isfinite(r) or r<=0:raise ValueError("state")
        if (b==1 and r>on_max_ohm) or (b==0 and r<off_min_ohm):failures.append(i)
    return {"status":"success" if not failures else "failed_attempt_budget","failed_bits":failures,
            "payload_committed":not failures,"attempt_limit":1,"yield_claim":None}

def reference_signal_bound(r_on,r_off,cap_F,voltage_V,threshold_V):
    """Independent two passive exponential branches, best possible middle reference.
    Any fixed reference gives min distance <= half full separation; this is an
    upper bound even before reference circuit mismatch and extra capacitance.
    """
    if not 0<r_on<r_off or cap_F<=0 or voltage_V<=0:raise ValueError("domain")
    peak_s=cap_F*math.log(r_off/r_on)/(1/r_on-1/r_off)
    separation=voltage_V*(math.exp(-peak_s/(r_off*cap_F))-math.exp(-peak_s/(r_on*cap_F)))
    return {"time_at_full_separation_peak_s":peak_s,"full_state_separation_V":separation,
            "best_middle_reference_margin_upper_bound_V":separation/2,
            "required_sense_difference_V":threshold_V,
            "single_cell_middle_reference_possible":separation/2>threshold_V,
            "qualification":"Necessary bound only; passing does not implement a reference, certify noise, read disturbance, or analog timing."}


def verify_binary_readback(target_bits, sensed_bits):
    if len(target_bits)!=len(sensed_bits):raise ValueError("unverified physical bits")
    bad=[i for i,(a,b) in enumerate(zip(target_bits,sensed_bits)) if a!=b]
    return {"status":"success" if not bad else "failed_attempt_budget", "failed_bits":bad,
            "payload_committed":not bad,"attempt_limit":1,
            "measures_resistance_acceptance_window":False}

def passive_reference_develop(r_on_max,r_off_min,r_ref,cap_data,cap_ref,voltage,required_margin):
    """Earliest common sampling time resolving both endpoint classes against a real R/C branch."""
    if not 0<r_on_max<r_ref<r_off_min: return {"feasible":False,"reason":"reference resistance outside accepted endpoints"}
    def signals(t):
        on=voltage*math.exp(-t/(r_on_max*cap_data))
        off=voltage*math.exp(-t/(r_off_min*cap_data))
        ref=voltage*math.exp(-t/(r_ref*cap_ref))
        return ref-on,off-ref
    t0=min(r_on_max*cap_data,r_ref*cap_ref,r_off_min*cap_data)*1e-7
    last=0.;peak=0.;best=0.
    for i in range(2400):
        tm=t0*math.exp(i*math.log(1e9)/2399)
        ds=signals(tm);margin=min(ds)
        if margin>peak:peak=margin;best=tm
        if margin>=required_margin:
            lo,hi=last,tm
            for _ in range(90):
                mid=(lo+hi)/2
                if min(signals(mid))>=required_margin:hi=mid
                else:lo=mid
            ds=signals(hi)
            return {"feasible":True,"develop_s":hi,"on_side_margin_V":ds[0],"off_side_margin_V":ds[1],
                    "reference_resistance_total_ohm":r_ref,"data_total_cap_F":cap_data,"reference_total_cap_F":cap_ref}
        last=tm
    return {"feasible":False,"reason":"no common state/reference sensing aperture","best_margin_V":peak,"best_time_s":best}

def nominal_full_cover_lifecycle(k,n,write_lanes=16,fault=None):
    """Conditional state-machine enumeration, not a materials switching simulator.
    It realizes the declared accepted programming outcome and tests actual coverage,
    grouped write resources and readback failure behavior. No whole-matrix shadow.
    """
    reset_batches=set();set_batches=set();verified=0;committed=0
    for row in range(k):
        target=[((row*37+col*17+11)>>((row+col)%5))&1 for col in range(8*n)]
        state=[1-b for b in target] # maximally different old row; no equality skip
        for start in range(0,8*n,write_lanes):
            reset_batches.add((row,start//write_lanes))
            for col in range(start,min(start+write_lanes,8*n)):state[col]=0
        for start in range(0,8*n,write_lanes):
            set_batches.add((row,start//write_lanes))
            for col in range(start,min(start+write_lanes,8*n)):
                if target[col]:state[col]=1
        if fault and fault[0]==row:state[fault[1]]^=1
        result=verify_binary_readback(target,state);verified+=len(state)
        if not result['payload_committed']:
            return dict(status='failed_attempt_budget',payload_Byte=0,failed_row=row,failed_bits=result['failed_bits'],verified_bits=verified,
             reset_batches=len(reset_batches),set_reserved_batches=len(set_batches),committed_rows_before_failure=committed,
             model_scope='Nominal accepted-state transitions with explicit injected fault; no stochastic switching prediction')
        committed+=1
    return dict(status='success',payload_Byte=k*n,verified_bits=verified,reset_batches=len(reset_batches),
      set_reserved_batches=len(set_batches),committed_rows=committed,max_row_target_hold_bits=8*n,
      model_scope='Nominal accepted-state transitions only; binary readback does not certify resistance windows')

def source_grid(parameters):
    p=parameters;rho=p['source_metal_resistivity_ohm_m'];length=p['rows']*p['cell_pitch_y_m']
    sense=p['cols']//p['read_mux'];branches=p['cols']+sense
    width=branches*p['cell_pitch_x_m'] # includes explicit reference peripheral columns
    local_R=rho*length/(p['source_column_width_m']*p['source_column_thickness_m'])
    bus_R=rho*width/(p['source_bus_width_m']*p['source_bus_thickness_m'])
    cap=8.8541878128e-12*p['source_dielectric_relative_permittivity']*p['source_column_width_m']*length/p['source_BL_spacing_m']+p['source_fringe_F_per_m']*length
    return dict(local_source_R_ohm=local_R,shared_source_R_ohm=bus_R,source_BL_coupling_F=cap,
      source_column_count=branches,source_column_length_m=length,source_bus_length_m=width,
      write_peak_A=(p['cols']//p['write_mux'])*p['reset_current_A'],
      write_source_drop_V=(p['cols']//p['write_mux'])*p['reset_current_A']*bus_R+p['reset_current_A']*local_R,
      rejected_native_thin_row_drop_V=(p['cols']//p['write_mux'])*p['reset_current_A']*(p['cols']*p['cell_pitch_x_m']*p['wire_ohm_per_m']),
      metal_area_m2=branches*p['source_column_width_m']*length+p['source_bus_width_m']*width,
      geometry_scope='Readsourcegroundgrid shared acrossdataandreference;sourceBLcoupling parallelplate+fringe estimate, not a fittedreadlatency')

def coupled_reference_develop(p,n,grid,reference_switch_R):
    """Four-node shared-source RC: sensed victim/other sensed/reference/unsensed BL.
    All physical WL cells can conduct; absence of an SA does not delete a column.
    Finite extreme-history/load/skew cases are model qualifications, not distributions.
    """
    common=p['access_resistance_ohm']+n['array_col_res_ohm']+n['actual_mux_res_ohm']+grid['local_source_R_ohm']
    C=n['sa_effective_node_cap_F'];Cr=C*p['reference_cap_ratio'];S=int(n['native_sa_count']);U=p['cols']-S
    mux_drain=(n['native_sa_input_cap_F']-n['array_BL_cap_F'])/(p['read_mux']+1)
    Cu=n['array_BL_cap_F']+grid['source_BL_coupling_F']+n['write_off_drain_added_to_read_F']+mux_drain
    Ru_par=p['access_resistance_ohm']+n['array_col_res_ohm']+grid['local_source_R_ohm']
    Rref=p['reference_resistance_ohm']+n['array_col_res_ohm']+grid['local_source_R_ohm']+reference_switch_R
    Rs=grid['shared_source_R_ohm'];goal=p['sense_threshold_V']+p['sense_error_budget_V']
    ages=[-p['enable_skew_limit_s'],0.,p['enable_skew_limit_s']];contexts=[]
    def initial(x,age):
        v=[p['read_voltage_V']]*3+[x['unsensed_initial_V']]
        if age<0:
            v[2]*=math.exp(age/((Rref+S*Rs)*Cr));return v
        # Matrix exponential series for the short data-before-reference interval.
        # Reference is isolated; all128 data cells, includingunsensed columns, are active.
        g=[x['counts'][i]/x['R'][i] if i!=2 else 0. for i in range(4)]
        den=1/Rs+sum(g)
        A=[[0.]*4 for _ in range(4)]
        for i in (0,1,3):
            for j in range(4):A[i][j]=g[j]/(den*x['R'][i]*x['C'][i])
            A[i][i]-=1/(x['R'][i]*x['C'][i])
        answer=v[:];term=v[:]
        for order in range(1,31):
            term=[age/order*sum(A[i][j]*term[j] for j in range(4)) for i in range(4)]
            answer=[answer[i]+term[i] for i in range(4)]
        return answer
    for cls,target in [('on',p['on_accept_max_ohm']),('off',p['off_accept_min_ohm'])]:
        for other in [p['on_accept_min_ohm'],p['off_accept_max_ohm']]:
            for ur in [p['on_accept_min_ohm'],p['off_accept_max_ohm']]:
                for uv in (0.,p['unselected_BL_initial_max_V']):
                    for age in ages:
                        x={'cls':cls,'R':[target+common,other+common,Rref,ur+Ru_par],
                           'C':[C,C,Cr,Cu],'counts':[1,S-1,S,U],'unsensed_initial_V':uv,'data_pre_age_s':age}
                        x['v']=initial(x,age);contexts.append(x)
    dt=min(min(x['R'][i]*x['C'][i] for i in range(4)) for x in contexts)/4000
    voltage_bound=max(p['read_voltage_V'],p['unselected_BL_initial_max_V'])
    maxsource=max(voltage_bound*sum(x['counts'][i]/x['R'][i] for i in range(4))/(1/Rs+sum(x['counts'][i]/x['R'][i] for i in range(4))) for x in contexts)
    def rhs(x,v):
        den=1/Rs+sum(x['counts'][i]/x['R'][i] for i in range(4))
        vs=sum(v[i]*x['counts'][i]/x['R'][i] for i in range(4))/den
        return [-(v[i]-vs)/(x['R'][i]*x['C'][i]) for i in range(4)]
    tm=0.
    for step in range(120000):
        margins=[]
        for x in contexts:
            v=x['v'];a=rhs(x,v);b=rhs(x,[v[i]+dt*a[i]/2 for i in range(4)])
            c=rhs(x,[v[i]+dt*b[i]/2 for i in range(4)]);d=rhs(x,[v[i]+dt*c[i] for i in range(4)])
            x['v']=[v[i]+dt*(a[i]+2*b[i]+2*c[i]+d[i])/6 for i in range(4)]
            margins.append(x['v'][2]-x['v'][0] if x['cls']=='on' else x['v'][0]-x['v'][2])
        tm+=dt
        if min(margins)>=goal:
            return dict(feasible=True,develop_s=tm,integration_dt_s=dt,min_margin_V=min(margins),context_margins_V=margins,
              finite_context_count=len(contexts),max_shared_source_drop_V=maxsource,source_drop_kind='all-physical-nodesatvoltagebound conservativeupperbound',
              data_pre_discharge_ages_s=ages,reference_resistance_total_ohm=Rref,data_total_cap_F=C,reference_total_cap_F=Cr,
              unsensed_physical_columns=U,unsensed_column_cap_F=Cu,unsensed_initial_range_V=[0.,p['unselected_BL_initial_max_V']],
              model='Four-nodecoupledpassiveRC withallWL-activatedcolumns,unsensedhistoryextremes,referenceisolation andfiniteenableskew;notastatisticalenvelope')
    return dict(feasible=False,reason='Noqualifiedcommonaperture',integration_dt_s=dt,max_shared_source_drop_V=maxsource)
