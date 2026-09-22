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

def calc(profile,width=16,dedicated_read_ns=None,period_ns=None):
    p=next(p for p in X['profiles'] if p['id']==profile)
    v=S.C['propagation']['profile_values'][profile]; td=v['digital_tick']
    a={**S.R['acim'],'rows_per_group':X['mapping']['native_rows'],
       'evaluation_output_width':width,'adc_per_weight_plane':width}
    # The original 180 ns macro is only a scale anchor. Common TI and TA propagate.
    residual=p['dedicated_read_ns'] if dedicated_read_ns is None else dedicated_read_ns
    frontend=v['input_step']+residual+v['adc_batch']
    assert residual>=0
    ds,n,hold=S.acim_service(a,v,residual)
    encoded=width*X['mapping']['encoded_bits_per_weight']
    front,beats=S.front_ns(encoded,td,X['write']['first_data_in_command'])
    payload,dr,batches,_=S.direct_service(dict(logical_weights_completed=width,
        cells_per_weight=X['mapping']['cells_per_weight'],parallel_cells=16*width,
        encoded_load_bits=encoded,first_data_in_command=True,
        complete_physical_update_ns=p['program_complete_ns']),td)
    groups=math.ceil(S.L['resident_capacity_Byte']/payload)
    rf_read=frontend; rf_decode=X['refresh']['decode_ticks']*td
    rf_one=S.program_sequence_ns(rf_read+rf_decode+front,0,[dict(count=1,
         drive_program_ns=p['program_complete_ns'],verify_ns=0,recover_ns=0)])
    rf_total=groups*rf_one; period=X['refresh']['period_ns'] if period_ns is None else period_ns
    guard=max(frontend+math.ceil(width/a['digital_output_lanes'])*a['digital_ticks_per_reconstruction_round']*td,dr)
    slack=period-rf_total-guard
    alpha=slack/period
    feasible=alpha>0
    nominal=S.metrics(S.L['B_S_Byte'],payload,ds,dr)
    effective=(S.metrics(S.L['B_S_Byte'],payload,ds/alpha,dr/alpha) if feasible else
       dict(B_S_Byte=S.L['B_S_Byte'],B_R_Byte=payload,delta_S_ns=None,delta_R_ns=None,
            rho_Byte_per_s=None,tau_Byte_per_s=None,ridge=None))
    return dict(id=profile if width==16 else 'wide32',baseline_id=X['baseline_id'],mode=X['mode'],
       scenario_type=('resource_comparison' if width!=16 else
          'infeasible_stress' if not feasible else
          'refresh_critical_stress' if profile=='long' else
          'recommended_reference' if profile=='reference' else 'paired_engineering_scenario'),
       feasibility='feasible_under_stated_conditions' if feasible else 'infeasible_fixed_refresh_schedule',
       mapping='8 binary endpoint planes; pseudodifferential pairs; 64 rows/group',
       profile=profile,output_width=width,adc_count=width*8,pair_write_drivers=width*8,
       physical_cells=X['mapping']['physical_cells'],counts=n,write_batches=batches,
       data_beats=beats,encoded_load_bits=encoded,frontend_complete_ns=frontend,
       dedicated_read_ns=residual,frontend_coverage=['input_step','dedicated_integration','adc_batch'],
       write_front_ns=front,program_complete_ns=p['program_complete_ns'],
       nominal=nominal,refresh=dict(period_ns=period,groups=groups,scalar_pair_reads=groups*width*8,
          cells_rewritten=groups*width*16,group_read_ns=rf_read,group_decode_ns=rf_decode,
          group_load_control_ns=front,group_program_ns=p['program_complete_ns'],
          sign_decode_lanes=width*8,group_service_ns=rf_one,total_ns=rf_total,busy_fraction=rf_total/period,scheduling_guard_ns=guard,availability=alpha,
          total_reserved_fraction=(rf_total+guard)/period,workload_slack_ns=slack,
          availability_not_clipped=True,
          workload_payload_Byte=0),
       full_matrix_update=dict(logical_Byte=S.L['resident_capacity_Byte'],transactions=groups,
          raw_service_ns=groups*dr,average_service_with_reserved_refresh_ns=groups*dr/alpha if feasible else None),
       dominant='whole analog frontend in streaming; current settling in update; full-capacity read/decode/rewrite maintenance',
       provenance={'frontend':'engineering dedicated response plus actual shared TI/TA; GC-04 Fig10 whole 180 ns is scale anchor only',
          'program':'GC-04 pp9-10 measured 65 ns complete; 75 ns measured comparison used as long budget',
          'refresh_period':'GC-04 p10 limited +/-7 retention statistics; binary-margin-conditioned adaptation'},**effective)

def results():
    rows=[calc(p['id']) for p in X['profiles']]
    wide=calc('reference',32); ref=rows[1]
    wide['ratios_to_reference']={k:wide[k]/ref[k] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    failed=calc('long',dedicated_read_ns=216)
    failed['id']='long_read216_infeasible'
    return dict(baseline_id=X['baseline_id'],kind=X['kind'],units=X['units'],baseline_hashes=X['baseline_hashes'],
                scenarios=rows,structure_comparison=wide,
                recommended_reference_id='reference',ordinary_scenario_ids=['short','reference'],
                pressure_scenario_ids=['long','long_read216_infeasible'],
                infeasible_stress=failed,
                range_meaning='Ordinary paired engineering scenarios only; long is refresh-critical stress, not a lower uncertainty bound.',
                paired_ranges={k:[min(r[k] for r in rows[:2]),max(r[k] for r in rows[:2])]
                      for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']},
                refresh_threshold=dict(profile='long',fixed_period_ns=400000,
                    equation='1025 * dedicated_read_ns + 179280 < 400000',
                    dedicated_read_strict_upper_bound_ns=(400000-179280)/1025,
                    margin_from_long_ns=(400000-179280)/1025-200,
                    note='Equality leaves zero workload availability; above it the schedule is infeasible. No throughput or finite ridge is exported at alpha <= 0.'))

def tex_tables(r):
    t=[r'% Generated by scripts/check_gain_cell_edram.py --emit.',r'\begin{table}[htbp]\centering\small',
       r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
       r'情景 & $C_A$ (ns) & $P$ (ns) & $C_S$ (ns) & $C_R$ (ns) & $T_{\rm ref}$ ($\mu$s) & 可用率\\\midrule']
    for z,label in zip(r['scenarios'],['短','参考','长：临界压力']):
        t.append(f"{label} & {z['frontend_complete_ns']:g} & {z['program_complete_ns']:g} & {z['nominal']['delta_S_ns']:g} & {z['nominal']['delta_R_ns']:g} & {z['refresh']['total_ns']/1000:.3f} & {100*z['refresh']['availability']:.3f}\\%\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{无维护时的占用 $C_S,C_R$ 与每 0.4 ms 全矩阵刷新时间；可用率再扣批边界余量 116/185/280 ns。}\end{table}',
      r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
      r'情景 & $\Delta_S$ ($\mu$s) & $\Delta_R$ (ns) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for z,label in zip(r['scenarios'],['短','参考','长：临界压力']):
        t.append(f"{label} & {z['delta_S_ns']/1000:.3f} & {z['delta_R_ns']:.2f} & {z['rho_Byte_per_s']/1e6:.4g} & {z['tau_Byte_per_s']/1e6:.4g} & {z['ridge']:.5f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{包含固定刷新预留后的长期平均服务；$B_S=128$ Byte、$B_R=16$ Byte，MB=$10^6$ Byte。普通情景只含短与参考，长点单列为压力情景。}\label{09_gain_cell_edram:tab:results}\end{table}']
    w=r['structure_comparison']
    t += [r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
          r'配置 & ADC/写对驱动 & $N_E$ & 刷新 ($\mu$s) & $\rho$ (MB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for z,label in [(r['scenarios'][1],'16 输出'),(w,'32 输出')]:
        t.append(f"{label} & {z['adc_count']}/{z['pair_write_drivers']} & {z['counts']['evaluations']} & {z['refresh']['total_ns']/1000:.2f} & {z['rho_Byte_per_s']/1e6:.4g} & {z['tau_Byte_per_s']/1e6:.4g} & {z['ridge']:.5f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{仅参考时隙的资源对照；32 输出配置每事务完成 32 Byte，数据接口仍为 128 bit、数字通道仍为 16。}\label{09_gain_cell_edram:tab:wide}\end{table}']
    # Split three tables so manuscript can place structural comparison in its own section.
    text='\n'.join(t)+'\n'; at=text.index('\\begin{table}',text.index('\\label{09_gain_cell_edram:tab:results}'))
    return text[:at],text[at:]

def artifacts():
    r=results();tables,wide=tex_tables(r)
    return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n',
       'tex/generated_results.tex':tables,'tex/generated_structure.tex':wide}

def check():
    for path,h in X['baseline_hashes'].items():
        assert hashlib.sha256((SHARED/path).read_bytes()).hexdigest()==h,('shared baseline changed',path)
    for sid,s in X['sources'].items():
        assert hashlib.sha256((CORPUS/s['pdf']['path']).read_bytes()).hexdigest()==s['pdf']['sha256'],sid
    for p in X['profiles']:
        assert p['program_coarse_ns']+p['program_fine_ns']==p['program_complete_ns']
        assert p['dedicated_read_ns']>=X['refresh']['single_pair_pulse_ns']
    assert S.L['resident_capacity_Byte']*16==X['mapping']['physical_cells']==262144
    assert X['mapping']['physical_tiles']*64*64*2==262144
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
    for z in r['scenarios']+[r['structure_comparison']]:
        v=S.C['propagation']['profile_values'][z['profile']];td=v['digital_tick']
        n=z['counts'];w=z['output_width'];f=z['refresh'];nom=z['nominal']
        assert n['evaluations']==8*2*(128//w)
        assert n['useful_scalar_conversions']==8*2*8*128==16384
        assert n['digital_ticks']==256
        assert f['sign_decode_lanes']==z['adc_count']
        assert f['scalar_pair_reads']==131072 and f['cells_rewritten']==262144
        assert f['groups']==128*(128//w)
        assert nom['delta_S_ns']==n['evaluations']*z['frontend_complete_ns']+258*td
        assert nom['delta_R_ns']==(2+math.ceil(16*w/128)-1)*td+z['program_complete_ns']
        assert f['group_service_ns']==z['frontend_complete_ns']+td+nom['delta_R_ns']
        assert f['total_ns']==f['groups']*f['group_service_ns']
        assert f['total_ns']+f['scheduling_guard_ns']<f['period_ns']
        assert math.isclose(z['ridge'],(128/w)*nom['delta_R_ns']/nom['delta_S_ns'])
        assert math.isclose(z['rho_Byte_per_s']/z['tau_Byte_per_s'],z['ridge'])
        assert z['refresh']['workload_payload_Byte']==0
        agg=z['full_matrix_update'];assert math.isclose(agg['logical_Byte']/(agg['average_service_with_reserved_refresh_ns']*1e-9),z['tau_Byte_per_s'])
    ref=r['scenarios'][1]
    assert ref['nominal']['delta_S_ns']==23690 and ref['nominal']['delta_R_ns']==80
    assert ref['refresh']['total_ns']==266240
    stress=r['infeasible_stress']
    assert stress['refresh']['availability']<0 and stress['rho_Byte_per_s'] is None and stress['ridge'] is None
    # At exactly zero available time the model must also suppress throughput/ridge.
    long_refresh=r['scenarios'][2]['refresh']
    at_zero=calc('long',period_ns=long_refresh['total_ns']+long_refresh['scheduling_guard_ns'])
    assert at_zero['refresh']['availability']==0 and at_zero['tau_Byte_per_s'] is None and at_zero['ridge'] is None
    assert r['paired_ranges']['rho_Byte_per_s'][0]==ref['rho_Byte_per_s']
    for path,text in artifacts().items():assert (BASE/path).read_text()==text,path
    print('PASS: source/baseline hashes; endpoint mapping; coverage; stage coverage; actual refresh capacity; paired metrics; aggregation; generated files.')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--emit',action='store_true');a=p.parse_args()
    if a.emit:
        for path,text in artifacts().items():(BASE/path).write_text(text)
    check()
    for z in results()['scenarios']:
        print(z['id'],z['scenario_type'],f"rho={z['rho_Byte_per_s']/1e6:.8g} MB/s tau={z['tau_Byte_per_s']/1e6:.8g} MB/s RI*={z['ridge']:.8g}")
