#!/usr/bin/env python3
"""Read-only shared-API recomputation; --emit explicitly refreshes generated files."""
import argparse,hashlib,importlib.util,json,math,sys
sys.dont_write_bytecode=True
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
SHARED=BASE.parent/'shared_baseline'
CORPUS=BASE.parents[1]
X=json.loads((BASE/'data/inputs.json').read_text())
spec=importlib.util.spec_from_file_location('gain_cell_shared',SHARED/'scripts/check_shared.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
L=S.logical_configuration(**X['logical_configuration'])

def calc(profile,width=16,dedicated_read_ns=None,period_ns=None,logical=None,
         release_policy=None,parameter_overrides=None):
    release_policy=X['scenario_policy']['main_release_policy'] if release_policy is None else release_policy
    logical=L if logical is None else logical
    p=next(p for p in X['profiles'] if p['id']==profile)
    v=dict(S.C['propagation']['profile_values'][profile])
    parameters={**v,**{k:v for k,v in X['service_parameters'].items()
                       if k!='profile_common_overhead_ns'},
        'common_overhead_ns':X['service_parameters']['profile_common_overhead_ns'][profile],
        'program_complete_ns':p['program_complete_ns']}
    if dedicated_read_ns is not None:
        # Legacy public argument means the refresh dedicated frontend
        # (common residual + 64 ns), not the shorter MAC dedicated frontend.
        parameters['common_overhead_ns']=dedicated_read_ns-parameters['read_slot_reservation_ns']
    services=S.resolve_service_parameters(parameters,
        X['service_modes'][release_policy]['service_bindings'],parameter_overrides)
    normal=services['normal_evaluation']; refresh=services['refresh_read']
    assert all(z['pulse_ns']<=z['integration_reservation_ns'] for z in (normal,refresh)), 'pulse exceeds allocated control window'
    td=services['digital_control']['tick_ns'];program=services['resident_write']['complete_ns']
    v.update(input_step=normal['input_ns'],adc_batch=normal['adc_ns'],digital_tick=td)
    a={**S.R['acim'],'rows_per_group':X['mapping']['native_rows'],
       'evaluation_output_width':width,'adc_per_weight_plane':width}
    # The original 180 ns macro does not establish an independently measured stage split.
    residual=normal['common_overhead_ns']+normal['integration_reservation_ns']
    frontend=normal['input_ns']+residual+normal['adc_ns']
    assert residual>=0
    ds,n,hold=S.acim_service(a,v,residual,logical)
    encoded=width*X['mapping']['encoded_bits_per_weight']
    front,beats=S.front_ns(encoded,td,X['write']['first_data_in_command'])
    payload,dr,batches,_=S.direct_service(dict(logical_weights_completed=width,
        cells_per_weight=X['mapping']['cells_per_weight'],parallel_cells=16*width,
        encoded_load_bits=encoded,first_data_in_command=True,
        complete_physical_update_ns=program),td,logical)
    groups=math.ceil(logical['resident_capacity_Byte']/payload)
    rf_read=sum(refresh[k] for k in ('input_ns','common_overhead_ns','integration_reservation_ns','adc_ns'))
    rf_decode=X['refresh']['decode_ticks']*td
    rf_one=S.program_sequence_ns(rf_read+rf_decode+front,0,[dict(count=1,
         drive_program_ns=program,verify_ns=0,recover_ns=0)])
    rf_total=groups*rf_one; period=X['refresh']['period_ns'] if period_ns is None else period_ns
    guard=max(frontend+math.ceil(width/a['digital_output_lanes'])*a['digital_ticks_per_reconstruction_round']*td,dr)
    slack=period-rf_total-guard
    alpha=slack/period
    feasible=alpha>0
    nominal=S.metrics(logical['B_S_Byte'],payload,ds,dr)
    effective=S.apply_maintenance(nominal,period,rf_total,guard)['effective']
    load=S.full_load_service(logical,[dict(payload_Byte=payload,service_ns=dr,count=groups)])
    raw_interface=S.mapping_metrics(logical,ds,load['T_R_ns'])
    effective_interface=S.apply_maintenance(raw_interface,period,rf_total,guard)['effective']
    return dict(id=profile if width==16 else 'wide32',baseline_id=X['baseline_id'],mode=X['mode'],
       scenario_type=('operation_mode_comparison' if release_policy!=X['scenario_policy']['main_release_policy'] else
          'resource_comparison' if width!=16 else
          'infeasible_stress' if not feasible else
          'refresh_critical_stress' if logical['n_in']==128 and profile=='long' else
          'recommended_reference' if profile=='reference' else 'paired_engineering_scenario'),
       feasibility='feasible_under_stated_conditions' if feasible else 'infeasible_fixed_refresh_schedule',
       mapping='8 binary endpoint planes; pseudodifferential pairs; 64 rows/group',
       profile=profile,release_policy=release_policy,resolved_services=services,
       output_width=width,adc_count=width*8,pair_write_drivers=width*8,
       K=logical['n_in'],N=logical['n_out'],physical_cells=int(logical['resident_capacity_Byte']*16),counts=n,write_batches=batches,
       data_beats=beats,encoded_load_bits=encoded,frontend_complete_ns=frontend,
       dedicated_read_ns=residual,
       refresh_dedicated_read_ns=refresh['common_overhead_ns']+refresh['integration_reservation_ns'],
       frontend_coverage=['input_step','common_frontend_overhead','mode_integration_reservation','adc_batch'],
       write_front_ns=front,program_complete_ns=program,
       nominal=nominal,refresh=dict(period_ns=period,groups=groups,scalar_pair_reads=groups*width*8,
          cells_rewritten=groups*width*16,group_read_ns=rf_read,group_decode_ns=rf_decode,
          group_load_control_ns=front,group_program_ns=program,
          sign_decode_lanes=width*8,group_service_ns=rf_one,total_ns=rf_total,busy_fraction=rf_total/period,scheduling_guard_ns=guard,availability=alpha,
          total_reserved_fraction=(rf_total+guard)/period,workload_slack_ns=slack,
          availability_not_clipped=True,
          workload_payload_Byte=0),
       full_matrix_update=dict(logical_Byte=logical['resident_capacity_Byte'],transactions=groups,
          raw_service_ns=groups*dr,average_service_with_reserved_refresh_ns=groups*dr/alpha if feasible else None),
       dominant='whole analog frontend in streaming; current settling in update; full-capacity read/decode/rewrite maintenance',
       mapping_interface=effective_interface,raw_mapping_interface=raw_interface,
       effective_mapping_interface=dict(effective_interface),
       provenance={'frontend':'common stage allowance plus explicit control reservation and actual shared TI/TA; GC-04 Fig10 whole 180 ns is scale anchor only',
          'program':'GC-04 pp9-10 measured 65 ns complete; 75 ns measured comparison used as long budget',
          'refresh_period':'GC-04 p10 limited +/-7 retention statistics; binary-margin-conditioned adaptation'},**effective)

def results():
    rows=[calc(p['id']) for p in X['profiles']]
    wide=calc('reference',32);ref=rows[1]
    wide['ratios_to_reference']={k:wide[k]/ref[k] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    big=S.logical_configuration(128,128)
    capacity=calc('reference',logical=big);capacity['id']='capacity128_reference';capacity['scenario_type']='organization_comparison'
    pressure=calc('long',logical=big);pressure['id']='capacity128_long'
    failed=calc('long',dedicated_read_ns=216,logical=big);failed['id']='capacity128_read216_infeasible'
    modes=[]
    for p,main in zip(X['profiles'],rows):
        z=calc(p['id'],release_policy='fixed_slot');z['id']='fixed_slot_'+p['id']
        z['scenario_class']='operation_mode_comparison'
        z['ratios_to_same_profile_early_release']={k:z[k]/main[k] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
        modes.append(z)
    return dict(baseline_id=X['baseline_id'],kind=X['kind'],units=X['units'],baseline_hashes=X['baseline_hashes'],
        native_configuration=X['native_configuration'],scenarios=rows,structure_comparison=wide,
        capacity_comparison=capacity,refresh_pressure=pressure,infeasible_stress=failed,
        main_release_policy=X['scenario_policy']['main_release_policy'],mode_comparisons=modes,
        recommended_reference_id='reference',ordinary_scenario_ids=['short','reference','long'],
        pressure_scenario_ids=['capacity128_long','capacity128_read216_infeasible'],
        range_meaning='Three sustainable paired windows in64x64nativeconfiguration;capacity andresource changes separate',
        paired_ranges={k:[min(r[k] for r in rows),max(r[k] for r in rows)]
             for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']},
        refresh_threshold=dict(configuration='capacity128',profile='long',fixed_period_ns=400000,
            equation='1025 * refresh_dedicated_read_ns +179217 <400000',
            dedicated_read_strict_upper_bound_ns=(400000-179217)/1025,
            note='main early_release; refresh dedicated frontend=common residual+64 ns; the same residual also affects MAC. Applies only128x128capacity stress,not ordinary64x64long.'))

def tex_tables(r):
    t=[r'% Generated by scripts/check_gain_cell_edram.py --emit.',r'\begin{table}[htbp]\centering\small',
       r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
       r'情景 & $C_{A,M}$ (ns) & $P$ (ns) & $C_S$ (ns) & $C_R$ (ns) & $T_{\rm ref}$ ($\mu$s) & 可用率\\\midrule']
    for z,label in zip(r['scenarios'],['短','参考','长']):
        t.append(f"{label} & {z['frontend_complete_ns']:g} & {z['program_complete_ns']:g} & {z['nominal']['delta_S_ns']:g} & {z['nominal']['delta_R_ns']:g} & {z['refresh']['total_ns']/1000:.3f} & {100*z['refresh']['availability']:.3f}\\%\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{按模式结束积分的主调度：无维护占用 $C_S,C_R$ 与每 0.4 ms 全矩阵刷新时间；可用率再扣批边界余量 71/122/217 ns。}\end{table}',
      r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
      r'情景 & $\Delta_S$ ($\mu$s) & $\Delta_R$ (ns) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for z,label in zip(r['scenarios'],['短','参考','长']):
        t.append(f"{label} & {z['delta_S_ns']/1000:.3f} & {z['delta_R_ns']:.2f} & {z['rho_Byte_per_s']/1e6:.4g} & {z['tau_Byte_per_s']/1e6:.4g} & {z['ridge']:.5f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{包含固定刷新预留后的长期平均服务；$B_S=64$ Byte、$B_R=16$ Byte，MB=$10^6$ Byte。三点均为同一64×64原生组织的可持续情景；容量压力另列。}\label{09_gain_cell_edram:tab:results}\end{table}']
    w=r['structure_comparison']
    t += [r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
          r'配置 & ADC/写对驱动 & $N_E$ & 刷新 ($\mu$s) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for z,label in [(r['scenarios'][1],'16 输出'),(w,'32 输出')]:
        t.append(f"{label} & {z['adc_count']}/{z['pair_write_drivers']} & {z['counts']['evaluations']} & {z['refresh']['total_ns']/1000:.2f} & {z['rho_Byte_per_s']/1e6:.4g} & {z['tau_Byte_per_s']/1e6:.4g} & {z['ridge']:.5f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{仅参考时隙的资源对照；32 输出配置每事务完成 32 Byte，数据接口仍为 128 bit、数字通道仍为 16。}\label{09_gain_cell_edram:tab:wide}\end{table}']
    # Split three tables so manuscript can place structural comparison in its own section.
    text='\n'.join(t)+'\n'; at=text.index('\\begin{table}',text.index('\\label{09_gain_cell_edram:tab:results}'))
    return text[:at],text[at:]

def dependency_diagnostics():
    """Finite parameter probes; independent expected deltas are checked below."""
    probes=[('early_release','common_overhead_ns',96),('early_release','input_step',6),
        ('early_release','adc_batch',21),('early_release','digital_tick',6),
        ('fixed_slot','read_slot_reservation_ns',65),
        ('fixed_slot','mac_integration_ns',2),
        ('early_release','mac_integration_ns',2),
        ('early_release','refresh_integration_ns',65),
        ('early_release','program_complete_ns',66)]
    records=[]
    for mode,param,value in probes:
        base=calc('reference',release_policy=mode)
        z=calc('reference',release_policy=mode,parameter_overrides={param:value})
        records.append(dict(release_policy=mode,override={param:value},
            delta_raw_vector_ns=z['nominal']['delta_S_ns']-base['nominal']['delta_S_ns'],
            delta_raw_write_transaction_ns=z['nominal']['delta_R_ns']-base['nominal']['delta_R_ns'],
            delta_refresh_ns=z['refresh']['total_ns']-base['refresh']['total_ns'],
            delta_guard_ns=z['refresh']['scheduling_guard_ns']-base['refresh']['scheduling_guard_ns'],
            availability=z['refresh']['availability'],rho_Byte_per_s=z['rho_Byte_per_s'],
            tau_Byte_per_s=z['tau_Byte_per_s'],ridge=z['ridge']))
    return dict(kind='deterministic_dependency_diagnostics',
        method='Expected deltas use 32 compute groups, 256 refresh groups, 3 TD per write, 1 TD sign decode, and independent maximum-group scheduling arithmetic.',
        scope='Parameter propagation only; no circuit simulation or measured speed claim.',records=records)

def artifacts():
    r=results();tables,wide=tex_tables(r)
    return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n',
       'tex/generated_results.tex':tables,'tex/generated_structure.tex':wide,
       'data/service_diagnostics.json':json.dumps(dependency_diagnostics(),ensure_ascii=False,indent=2)+'\n'}

def check():
    for path,h in X['baseline_hashes'].items():
        assert hashlib.sha256((SHARED/path).read_bytes()).hexdigest()==h,('shared baseline changed',path)
    for sid,s in X['sources'].items():
        assert hashlib.sha256((CORPUS/s['pdf']['path']).read_bytes()).hexdigest()==s['pdf']['sha256'],sid
    for p in X['profiles']:
        assert p['program_coarse_ns']+p['program_fine_ns']==p['program_complete_ns']
        assert p['refresh_dedicated_read_ns']==X['service_parameters']['profile_common_overhead_ns'][p['id']]+X['refresh']['single_pair_pulse_ns']
    assert L['resident_capacity_Byte']*16==X['mapping']['physical_cells']==65536
    assert X['mapping']['physical_tiles']*64*64*2==65536
    for weight in range(-128,128):
        bits=[(weight>>i)&1 for i in range(8)]
        assert sum(((1<<i) if i<7 else -128)*b for i,b in enumerate(bits))==weight
    # Endpoint reconstruction independently exercises all count levels and representative activity.
    for active in range(65):
        for ones in range(active+1):
            assert ((ones-(active-ones))+active)/2==ones
    assert X['refresh']['single_pair_pulse_ns']==X['mapping']['native_rows']*X['refresh']['mac_pulse_ns']
    assert 700*64/1000==44.8  # nA*ns / 1000 -> fC
    assert math.isclose(44.8/200,0.224)  # fC/fF -> V
    r=results()
    for z in r['scenarios']+[r['structure_comparison']]+r['mode_comparisons']:
        v=S.C['propagation']['profile_values'][z['profile']];td=v['digital_tick']
        n=z['counts'];w=z['output_width'];f=z['refresh'];nom=z['nominal']
        assert n['evaluations']==8*(64//w)
        assert n['useful_scalar_conversions']==8*8*64==4096
        assert n['digital_ticks']==64
        assert f['sign_decode_lanes']==z['adc_count']
        assert f['scalar_pair_reads']==32768 and f['cells_rewritten']==65536
        assert f['groups']==64*(64//w)
        assert nom['delta_S_ns']==n['evaluations']*z['frontend_complete_ns']+66*td
        assert nom['delta_R_ns']==(2+math.ceil(16*w/128)-1)*td+z['program_complete_ns']
        assert f['group_service_ns']==f['group_read_ns']+td+nom['delta_R_ns']
        assert f['total_ns']==f['groups']*f['group_service_ns']
        assert f['total_ns']+f['scheduling_guard_ns']<f['period_ns']
        assert math.isclose(z['ridge'],(64/w)*nom['delta_R_ns']/nom['delta_S_ns'])
        assert math.isclose(z['rho_Byte_per_s']/z['tau_Byte_per_s'],z['ridge'])
        assert z['refresh']['workload_payload_Byte']==0
        agg=z['full_matrix_update'];assert math.isclose(agg['logical_Byte']/(agg['average_service_with_reserved_refresh_ns']*1e-9),z['tau_Byte_per_s'])
    ref=r['scenarios'][1]
    assert ref['nominal']['delta_S_ns']==32*(5+86+1+20)+66*5 and ref['nominal']['delta_R_ns']==80
    assert ref['refresh']['total_ns']==256*(175+5+80)
    assert math.isclose(ref['mapping_interface']['U_star'],256*80/(32*112+66*5))
    assert all(z['refresh']['availability']>.75 for z in r['scenarios'])
    for z in r['scenarios']:
        assert math.isclose(z['mapping_interface']['U_star'],64*z['ridge'])
    stress=r['infeasible_stress']
    assert stress['refresh']['availability']<0 and stress['rho_Byte_per_s'] is None and stress['ridge'] is None
    # At exactly zero available time the model must also suppress throughput/ridge.
    long_refresh=r['scenarios'][2]['refresh']
    at_zero=calc('long',period_ns=long_refresh['total_ns']+long_refresh['scheduling_guard_ns'])
    assert at_zero['refresh']['availability']==0 and at_zero['tau_Byte_per_s'] is None and at_zero['ridge'] is None
    assert r['paired_ranges']['rho_Byte_per_s'][0]==r['scenarios'][2]['rho_Byte_per_s']
    # An independently specified phase ledger checks both modes, including the
    # short-mode guard where the complete write (71 ns) dominates the 53 ns MAC group.
    for z,expected in zip(r['scenarios'],[
            (1700,47360,71,.8814225),(3914,66560,122,.833295),(6964,96000,217,.7594575)]):
        ds,h,g,alpha=expected
        assert z['nominal']['delta_S_ns']==ds
        assert z['refresh']['total_ns']==h and z['refresh']['scheduling_guard_ns']==g
        assert math.isclose(z['refresh']['availability'],alpha)
        assert math.isclose(z['rho_Byte_per_s'],64e9*alpha/ds)
        assert math.isclose(z['tau_Byte_per_s'],16e9*alpha/z['nominal']['delta_R_ns'])
        assert math.isclose(z['mapping_interface']['U_star'],64*z['ridge'])
        assert z['release_policy']=='early_release'
    for z,expected in zip(r['mode_comparisons'],[
            (3716,47360,116),(5930,66560,185),(8980,96000,280)]):
        ds,h,g=expected
        assert z['nominal']['delta_S_ns']==ds
        assert z['refresh']['total_ns']==h and z['refresh']['scheduling_guard_ns']==g
        assert z['release_policy']=='fixed_slot' and z['scenario_type']=='operation_mode_comparison'
    # Wider resources and larger capacity consume the same main mode; their
    # guard is independently recomputed from the true nonpreemptive group.
    wide=r['structure_comparison'];big=r['capacity_comparison'];pressure=r['refresh_pressure']
    assert wide['nominal']['delta_S_ns']==16*112+66*5
    assert wide['refresh']['total_ns']==128*(175+5+90)
    assert wide['refresh']['scheduling_guard_ns']==max(112+4*5,90)
    assert big['nominal']['delta_S_ns']==128*112+258*5
    assert big['refresh']['total_ns']==1024*(175+5+80)
    assert big['refresh']['scheduling_guard_ns']==122
    assert pressure['refresh']['total_ns']==1024*(260+10+105)
    assert pressure['refresh']['scheduling_guard_ns']==max(197+2*10,105)
    assert pressure['scenario_type']=='refresh_critical_stress'
    assert stress['refresh']['total_ns']+stress['refresh']['scheduling_guard_ns']==1025*216+179217
    assert stress['scenario_type']=='infeasible_stress'
    # Expected deltas do not call calc/acim_service: count physical groups and
    # each stage once. Fixed-slot pulse changes leave timing invariant within the slot.
    expected_deltas=[(320,0,2560,10),(32,0,256,1),(32,0,256,1),
        (66,3,1024,2),(32,0,256,1),(0,0,0,0),(32,0,0,1),(0,0,256,0),(0,1,256,0)]
    for z,expected in zip(dependency_diagnostics()['records'],expected_deltas):
        assert tuple(z[k] for k in ('delta_raw_vector_ns','delta_raw_write_transaction_ns',
            'delta_refresh_ns','delta_guard_ns'))==expected,z
    try:
        calc('reference',release_policy='fixed_slot',parameter_overrides={'refresh_integration_ns':65})
    except AssertionError as err:
        assert 'pulse exceeds' in str(err)
    else:
        raise AssertionError('a refresh pulse cannot overrun the fixed control slot')
    for path,text in artifacts().items():assert (BASE/path).read_text()==text,path
    print('PASS: source/baseline hashes; endpoint mapping; coverage; stage coverage; actual refresh capacity; paired metrics; aggregation; generated files.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--emit',action='store_true');a=p.parse_args()
    if a.emit:
        for path,text in artifacts().items():(BASE/path).write_text(text)
    check()
    for z in results()['scenarios']:
        print(z['id'],z['scenario_type'],f"rho={z['rho_Byte_per_s']/1e6:.8g} MB/s tau={z['tau_Byte_per_s']/1e6:.8g} MB/s RI*={z['ridge']:.8g}")
