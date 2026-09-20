#!/usr/bin/env python3
"""Read-only recomputation; --emit explicitly refreshes result JSON and TeX."""
import argparse, hashlib, importlib.util, json, math, sys
from pathlib import Path
sys.dont_write_bytecode = True
BASE=Path(__file__).resolve().parents[1]
SHARED=BASE.parent/'shared_baseline'
CORPUS=BASE.parents[1]
spec=importlib.util.spec_from_file_location('shared_api',SHARED/'scripts/check_shared.py')
api=importlib.util.module_from_spec(spec); spec.loader.exec_module(api)
X=json.loads((BASE/'data/inputs.json').read_text())
L=api.L; R=api.R
M=X['mapping']; P=X['program']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()

def geometry(heads=32):
    n=L['n_in']; cols=L['n_out']; per=M['logical_weights_per_transaction']
    width=cols//M['writeheads']
    all_seen=set(); examples=[]; transactions=[]
    # The two subsets used with 16 heads are indexed by the ADC mux parity.
    for d in range(n):
        for s in range(width):
            coords=[((width*h+s+d)%n,width*h+s) for h in range(per)]
            assert len({r for r,c in coords})==per
            assert len({c for r,c in coords})==per
            for cell in coords:
                assert cell not in all_seen; all_seen.add(cell)
            transactions.append({'diagonal':d,'column_slot':s,'logical_weights':len(coords)})
            if d==0 and s==0:
                for plane in range(R['acim']['weight_planes']):
                    groups=[coords] if heads==32 else [coords[k::2] for k in range(2)]
                    for group in groups:
                        verify=[group[k::2] for k in range(2)] if heads==32 else [group]
                        assert all(len(v)==R['acim']['adc_per_weight_plane'] for v in verify)
                        assert all(len({c//M['verify_adc_group_width'] for r,c in v})==len(v) for v in verify)
                        examples.append({'plane':plane,'cells':[list(t) for t in group], 'verify_passes':[[list(t) for t in v] for v in verify]})
    assert len(all_seen)==n*cols==L['resident_capacity_Byte']/L['b_R']
    assert len(transactions)*per==n*cols
    return {'logical_transaction_count':len(transactions),'physical_cell_count':len(all_seen)*M['physical_cells_per_weight'],
            'full_coverage_unique_weights':len(all_seen),'transaction_inventory':transactions,'example_transaction_batches':examples}

def compute(profile,heads=32,set_ns=None,weak_verify=False):
    v=api.C['propagation']['profile_values'][profile]; x=X['profiles'][profile]
    cfg={**R['acim'],'rows_per_group':M['rows_per_group']}
    front_read=x['read_front_including_TI_ns']
    assert front_read>=v['input_step']
    ds,counts,hold=api.acim_service(cfg,v,front_read-v['input_step'])
    assert hold==0
    weights=M['logical_weights_per_transaction']; planes=cfg['weight_planes']
    geom=geometry(heads); batches=geom['example_transaction_batches']
    nv=sum(len(b['verify_passes']) for b in batches)
    np=len(batches)
    encoded=weights*M['physical_cells_per_weight']
    front,beats=api.front_ns(encoded,v['digital_tick'],True)
    s=P['set_total_budget_ns'] if set_ns is None else set_ns
    pulse=P['reset_pulse_ns']+s
    verify_front=(P['verify_precharge_ns']+P['verify_low_current_read_ns']) if weak_verify else front_read
    verify=verify_front+v['adc_batch']+v['digital_tick']
    g=x['drive_transition_ns']
    steps=[dict(count=1,drive_program_ns=v['digital_tick']+3*g+pulse,
                verify_ns=len(b['verify_passes'])*verify,recover_ns=0) for b in batches]
    dr=api.program_sequence_ns(front,0,steps)
    result=api.metrics(L['B_S_Byte'],weights*L['b_R'],ds,dr)
    result.update(profile=profile,mode=X['mode'],baseline_id=api.D['baseline_id'],writeheads=heads,verify_mode='weak_signal_analog_front' if weak_verify else 'same_front_binary_endpoint',
                  read_counts=counts,program_batches=np,verify_passes=nv,encoded_load_bits=encoded,data_beats=beats,
                  physical_cells_updated=encoded,
                  read_stages_ns={'front_including_TI':counts['evaluations']*front_read,'ADC':counts['adc_batches']*v['adc_batch'],
                                  'digital_decode_reconstruct':counts['digital_ticks']*v['digital_tick'],'boundary':cfg['boundary_ticks']*v['digital_tick']},
                  write_stages_ns={'interface':front,'batch_select':np*v['digital_tick'],'current_driver_transitions':3*np*g,
                                   'RESET_pulses':np*P['reset_pulse_ns'],'SET_pulses':np*s,
                                   'verify_front':nv*verify_front,
                                   'verify_ADC':nv*v['adc_batch'],'verify_endpoint_compare':nv*v['digital_tick']},
                  shared_profile_ns=v,read_front_total_ns=front_read,read_media_API_ns=front_read-v['input_step'],
                  transaction_pattern=M['transaction_pattern'],dominant_read='16 row groups,1024 serial front/ADC/decode rounds',
                  dominant_write='SET+RESET pulses' if not weak_verify else '16 repeated768ns weak-signal read-front blocks',
                  successful_service_condition=P['normal_service_condition'])
    assert math.isclose(sum(result['read_stages_ns'].values()),ds)
    assert math.isclose(sum(result['write_stages_ns'].values()),dr)
    assert result['B_R_Byte']==32 and result['B_S_Byte']==128
    assert np*heads==encoded and nv==16 and counts['evaluations']==1024
    assert counts['useful_scalar_conversions']==131072
    assert math.isclose(result['ridge'],4*dr/ds)
    transactions=geom['logical_transaction_count']
    result['matrix_reload']={'B_R_Byte':transactions*result['B_R_Byte'],'delta_R_ns':transactions*dr,'transactions':transactions,
                            'tau_Byte_per_s':transactions*result['B_R_Byte']/api.seconds(transactions*dr,'ns')}
    assert math.isclose(result['matrix_reload']['tau_Byte_per_s'],result['tau_Byte_per_s'])
    return result

def results():
    manifest={s['source_id']:s for s in json.loads((CORPUS/'source_manifest.json').read_text())['sources']}
    sources={}
    for key in X['sources']:
        s=manifest[key]; actual=digest(CORPUS/s['pdf']['path']); assert actual==s['pdf']['sha256']
        sources[key]={'title':s['title'],'pdf':s['pdf'],'doi':s['doi']}
    pairs=[compute(p) for p in ['short','reference','long']]
    # Independent literal hand arithmetic only for the reference arithmetic audit.
    ref=pairs[1]
    weak=compute('reference',weak_verify=True)
    assert weak['delta_R_ns']-ref['delta_R_ns']==16*(768-20)==11968
    assert weak['delta_S_ns']==ref['delta_S_ns']
    assert ref['delta_S_ns']==1024*(20+20+2*5)+2*5==51210
    assert ref['delta_R_ns']==3*5+8*(5+3*20+125+300+2*(20+20+5))==4655
    bounds={k:[min(s[k] for s in pairs),max(s[k] for s in pairs)] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    return dict(case_id=X['case_id'],baseline_id=api.D['baseline_id'],inputs_sha256=digest(BASE/'data/inputs.json'),mode=X['mode'],units={'time':'ns','payload':'Byte','rates':'Byte/s','ridge':'dimensionless'},
                shared_sha256={str(p.relative_to(SHARED)):digest(p) for p in [SHARED/'data/shared_parameters.json',SHARED/'scripts/check_shared.py']},
                sources=sources,paired_scenarios=pairs,paired_ranges=bounds,
                independent_endpoint_outer_envelope=[bounds['rho_Byte_per_s'][0]/bounds['tau_Byte_per_s'][1],bounds['rho_Byte_per_s'][1]/bounds['tau_Byte_per_s'][0]],
                verify_organization_comparison=compute('reference',weak_verify=True),set_total250ns_sensitivity=compute('reference',32,250),mapping=geometry())

def table(r):
    t=[r'% Generated by scripts/check_pcm.py --emit.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
       r'情景 & $\Delta_S$ ($\mu$s) & $\Delta_R$ ($\mu$s) & $\rho$ (GB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for label,row in zip(['短','参考','长'],r['paired_scenarios']):
        t.append(f"{label} & {row['delta_S_ns']/1000:.3f} & {row['delta_R_ns']/1000:.3f} & {row['rho_Byte_per_s']/1e9:.6f} & {row['tau_Byte_per_s']/1e6:.3f} & {row['ridge']:.4f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{二进制 PCM 的成对服务预算；GB/MB 为十进制单位，时间小数用于复算。}\label{tab:results}\end{table}']
    return '\n'.join(t)+'\n'

def stages(r):
    row=r['paired_scenarios'][1]
    labels={'interface':'命令、数据装入及提交','batch_select':'八批选通/模式控制','current_driver_transitions':'三段专用驱动转换','RESET_pulses':'RESET 脉冲','SET_pulses':'SET 平台及尾沿','verify_front':'二状态重新建立/读出','verify_ADC':'替代 SAR 转换','verify_endpoint_compare':'终态比较'}
    t=[r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrr@{}}\toprule',r'参考点 resident 占用 & ns & 占比 (\%)\\\midrule']
    for k,v in row['write_stages_ns'].items(): t.append(f"{labels[k]} & {v:g} & {100*v/row['delta_R_ns']:.2f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{完整写服务分解。接口与内部读验不增加逻辑写入字节。}\label{tab:write}\end{table}']
    return '\n'.join(t)+'\n'

def main():
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument('--emit',action='store_true'); args=parser.parse_args()
    r=results(); files={'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','tex/generated_results.tex':table(r),'tex/generated_write.tex':stages(r)}
    for p,text in files.items():
        if args.emit: (BASE/p).write_text(text)
        else: assert (BASE/p).read_text()==text, f'{p} stale; run --emit explicitly'
    print('PCM OK: shared API/hashes, source hashes, full diagonal coverage, program/verify ADC routing, stage coverage, paired metrics, matrix aggregation.')
    for s in r['paired_scenarios']: print(s['profile'],s['delta_S_ns'],s['delta_R_ns'],s['rho_Byte_per_s']/1e9,s['tau_Byte_per_s']/1e6,s['ridge'])
    print('weak verify:',r['verify_organization_comparison']['delta_R_ns'],r['verify_organization_comparison']['ridge'])
    print('SET total250ns:',r['set_total250ns_sensitivity']['delta_R_ns'])
if __name__=='__main__': main()
