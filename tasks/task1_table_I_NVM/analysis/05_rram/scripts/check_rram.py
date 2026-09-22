#!/usr/bin/env python3
"""Finite RRAM reference budgets; all time/throughput templates are imported shared APIs."""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE.parents[1]
SHARED = BASE.parent / 'shared_baseline'
X = json.loads((BASE/'data/inputs.json').read_text())
PROV = json.loads((BASE/'data/provenance.json').read_text())
spec=importlib.util.spec_from_file_location('rram_shared_api',SHARED/'scripts/check_shared.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
A=X['adopted_inputs'];C=X['configuration']
LABEL={'short':'短预算','reference':'参考','long':'长预算'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def physical_batches():
    # One selected output WL in each plane; G0 columns 0..15, G1 columns 16..31.
    # Transaction covers input indices 0..7 and 16..23, two INT8 weights per batch.
    return [[dict(payload_element=8*g+k,input_column=16*g+k,weight_plane=w,group=g,output_WL=0)
             for g in range(2) for w in range(8)] for k in range(8)]

def write_service(name,parallel_cells=16,verify_mode='binary'):
    v=S.C['propagation']['profile_values'][name]
    front,beats=S.front_ns(C['encoded_load_bits'],v['digital_tick'],True)
    assert 128%parallel_cells==0
    nb=128//parallel_cells
    verify_read=(v['input_step']+A['binary_verify_frontend_ns']['value']+A['binary_sense_slot_ns'][name] if verify_mode=='binary'
                 else v['input_step']+A['front_end_settle_ns']['value']+v['adc_batch'])
    address_ticks=A['address_and_pulse_control_ticks_per_attempt']['value']
    done_ticks=A['verify_group_done_commit_ticks_per_attempt']['value']
    guard_pre=A['high_voltage_setup_ns_per_attempt']['value']
    guard_post=A['high_voltage_return_recover_ns_per_attempt']['value']
    stages=[];terms=[]
    for phase in ['RESET','SET']:
        k=A['group_attempt_scenarios'][name][phase]
        count=nb*k
        step=dict(count=count,
                  drive_program_ns=guard_pre+A['program_pulse_ns'][phase]+address_ticks*v['digital_tick'],
                  recover_ns=guard_post,
                  verify_ns=verify_read+done_ticks*v['digital_tick'])
        stages.append(step)
        terms.append(dict(phase=phase,batches=nb,attempts_per_batch=k,attempt_slots=count,
            allocated_voltage_sequence_V=[round(A['program_voltages']['initial_'+phase+'_V']+j*A['program_voltages']['increment_on_same_polarity_retry_V'],3) for j in range(k)],
            pulse_total_ns=count*A['program_pulse_ns'][phase],
            HV_guard_total_ns=count*(guard_pre+guard_post),
            verify_read_total_ns=count*verify_read,
            local_control_total_ns=count*(address_ticks+done_ticks)*v['digital_tick'],
            mask='all 128 cells' if phase=='RESET' else 'only desired LRS bits; disabled lanes draw no program current; budget keeps the phase slot'))
    dr=S.program_sequence_ns(front,0,stages)
    details=dict(parallel_cells=parallel_cells,verify_mode=verify_mode,front_ns=front,data_beats=beats,
                 verify_read_ns_per_attempt=verify_read,
                 local_read_components_ns=dict(input_select=v['input_step'],frontend=5,sense_sample_latch=v['adc_batch']),
                 window_decision_in_sense_slot=True,group_done_mask_commit_ns=done_ticks*v['digital_tick'],
                 phase_details=terms,shared_template_steps=stages,
                 one_control_domain=True,success_condition='all target cells pass before final slot; retry tail beyond scenario is outside this case, never counted as successful payload')
    return dr,details

def calculate():
    cfg={**S.R['acim'],**C['acim_overrides']};rows=[]
    for name,v in S.C['propagation']['profile_values'].items():
        ds,n,hold=S.acim_service(cfg,v,A['front_end_settle_ns']['value'])
        dr,wd=write_service(name)
        rows.append(dict(profile=name,periphery_ns=v,counts=n,hold_extra_ns=hold,write_details=wd,
                         **S.metrics(S.L['B_S_Byte'],16,ds,dr)))
    v=S.C['propagation']['profile_values']['reference'];ds=S.acim_service(cfg,v,5)[0]
    comparisons=[]
    for label,p,mode in [('B32-W16 binary',16,'binary'),('B32-W1 binary',1,'binary'),('B32-W1 SAR',1,'sar')]:
        dr,wd=write_service('reference',p,mode)
        row=dict(label=label,write_details=wd,**S.metrics(128,16,ds,dr))
        row['peak_array_current_budget_mA']=p*C['write_resources']['current_compliance_uA_per_lane']/1000
        comparisons.append(row)
    h=[]
    for ha in [0,5]:
        d=S.acim_service(cfg,v,5+ha)[0];dr,_=write_service('reference')
        h.append(dict(h_A_ns=ha,meaning='additional front-end engineering budget; main binary verify is decoupled',**S.metrics(128,16,d,dr)))
    ranges={m:[min(r[m] for r in rows),max(r[m] for r in rows)] for m in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    return dict(schema_version='rram-reference-results-2.0',status=X['status'],
        baseline_json_sha256=digest(SHARED/'data/shared_parameters.json'),
        baseline_script_sha256=digest(SHARED/'scripts/check_shared.py'),input_sha256=digest(BASE/'data/inputs.json'),
        numerical_media_write_point_available=True,
        claim='finite engineering service budgets conditional on the selected windows being reached within the stated group-attempt counts; not measured confidence intervals or universal technology bounds',
        geometry=dict(logical_payload_elements=16,physical_cells=128,program_batches=physical_batches(),
            columns_in_this_transaction=list(range(8))+list(range(16,24)),
            complementary_transaction_columns=list(range(8,16))+list(range(24,32))),
        scenarios=rows,paired_ranges=ranges,
        independent_endpoint_ridge_envelope=[ranges['rho_Byte_per_s'][0]/ranges['tau_Byte_per_s'][1],ranges['rho_Byte_per_s'][1]/ranges['tau_Byte_per_s'][0]],
        comparisons_at_reference= comparisons,frontend_sensitivity=h)

def esc(s):
    for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('_',r'\_'),('#',r'\#')]:s=s.replace(a,b)
    return s.replace('µ',r'$\mu$').replace('×',r'$\times$').replace('Ω',r'$\Omega$').replace('−','-').replace('–','--').replace('≥',r'$\geq$').replace('≤',r'$\leq$')

def generate(r):
    t=[r'% Generated from inputs JSON via shared API.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',r'情景 & $K_R/K_S$ & $\Delta_S$ (\,$\mu$s) & $\Delta_R$ (\,$\mu$s) & $\rho$ (GB/s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for row in r['scenarios']:
        k=A['group_attempt_scenarios'][row['profile']]
        t.append(f"{LABEL[row['profile']]} & {k['RESET']}/{k['SET']} & {row['delta_S_ns']/1000:.3f} & {row['delta_R_ns']/1000:.3f} & {row['rho_Byte_per_s']/1e9:.5f} & {row['tau_Byte_per_s']/1e6:.5f} & {row['ridge']:.3f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{同一 B32-W16 参考组织的有限成对服务预算。$B_S=128$ Byte，$B_R=16$ Byte；GB、MB 均为十进制。组内所有活动 cell 在所列尝试次数内达窗是情景完成条件，次数不是实测尾部上界。}\label{tab:main}\end{table}']
    br=[r'% Generated detailed occupancy.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',r'情景 & 脉冲时隙 & HV建立/恢复预留 & binary选通/感测 & 控制/提交 & 合计\\\midrule']
    for row in r['scenarios']:
        ps=row['write_details']['phase_details'];vals=[sum(q[k] for q in ps)/1000 for k in ['pulse_total_ns','HV_guard_total_ns','verify_read_total_ns']]
        ctrl=(row['write_details']['front_ns']+sum(q['local_control_total_ns'] for q in ps))/1000
        br.append(f"{LABEL[row['profile']]} & {vals[0]:g} & {vals[1]:g} & {vals[2]:g} & {ctrl:.3f} & {row['delta_R_ns']/1000:.3f}\\\\")
    br += [r'\bottomrule\end{tabular}',r'\caption{完整 resident 占用分解，单位均为 $\mu$s。脉冲列按并行批预留时隙计，1 $\mu$s脉宽借自原文实际波形；HV前后各1 $\mu$s是工程余量，binary列含输入选通、5 ns建立以及10/20/50 ns完整sense时隙；该预算非本地SA实测内在延时。}\label{tab:breakdown}\end{table}']
    co=[r'% Generated one controlled comparison.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',r'参考点组织 & 活动写lane & verify读回 (ns) & $\Delta_R$ (\,$\mu$s) & $\tau$ (MB/s) & $\RI^*$\\\midrule']
    for row in r['comparisons_at_reference']:
        d=row['write_details']
        co.append(f"{esc(row['label'])} & {d['parallel_cells']} & {d['verify_read_ns_per_attempt']:g} & {row['delta_R_ns']/1000:.3f} & {row['tau_Byte_per_s']/1e6:.6f} & {row['ridge']:.3f}\\\\")
    co += [r'\bottomrule\end{tabular}',r'\caption{同一两阶段程序、脉冲、HV预留、成功窗和 $K_R/K_S=2/1$，仅改变活动并行度或校验通路。三行读侧相同，$\Delta_S=10.25\,\mu$s；W1仅启用已配置硬件中的一个lane，SAR复用原CIM转换器。}\label{tab:comparison}\end{table}']
    ev=[r'% Generated evidence table.',r'\begingroup\footnotesize',r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{16mm}>{\raggedright\arraybackslash}p{50mm}>{\raggedright\arraybackslash}p{42mm}>{\raggedright\arraybackslash}p{48mm}@{}}',r'\caption{原始证据与工程选择分列。页码为本地PDF页序。}\label{tab:evidence}\\',r'\toprule ID/来源 & 原值、单位、条件 & 定位 & 采用/换算及限制\\\midrule\endfirsthead',r'\toprule ID/来源 & 原值、单位、条件 & 定位 & 采用/换算及限制\\\midrule\endhead']
    md=['# RRAM 参数证据表','','原值、跨实现操作锚点与工程选择分开；从 `data/inputs.json` 生成。','','| ID/来源 | 原值与单位 | 条件与定位 | 采用/换算理由 |','|---|---|---|---|']
    for e in X['reported_evidence']:
        sid=e['source_id'] if e['source_id']!='shared_baseline' else '共享基线'
        locator=e['locator'] if e['id']!='E11' else '输入JSON：采用参数、写资源'
        ev.append(f"{esc(e['id'])}\\newline {esc(sid)} & {esc(e['original'])}\\newline {esc(e['condition'])} & {esc(locator)} & {esc(e['adoption'])}\\\\")
        md.append(f"| {e['id']} / {e['source_id']} | {e['original']} | {e['condition']}；{e['locator']} | {e['adoption']} |")
    ev += [r'\bottomrule\end{longtable}\endgroup']
    readme=(BASE/'README.md').read_text()
    begin='<!-- BEGIN GENERATED RESULTS -->';end='<!-- END GENERATED RESULTS -->'
    before,rest=readme.split(begin,1);_,after=rest.split(end,1)
    mt=['| 成对情景 | ΔS (µs) | ΔR (µs) | ρ (GB/s) | τ (MB/s) | RI* |','|---|---:|---:|---:|---:|---:|']
    for row in r['scenarios']:
        mt.append(f"| {LABEL[row['profile']]} | {row['delta_S_ns']/1000:.3f} | {row['delta_R_ns']/1000:.3f} | {row['rho_Byte_per_s']/1e9:.5f} | {row['tau_Byte_per_s']/1e6:.5f} | {row['ridge']:.3f} |")
    new_readme=before+begin+'\n'+'\n'.join(mt)+'\n'+end+after
    return {'README.md':new_readme,'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','tex/generated_read.tex':'\n'.join(t)+'\n','tex/generated_write_breakdown.tex':'\n'.join(br)+'\n','tex/generated_comparison.tex':'\n'.join(co)+'\n','tex/generated_evidence.tex':'\n'.join(ev)+'\n','notes/parameter_evidence.zh.md':'\n'.join(md)+'\n'}

def check(r):
    assert digest(SHARED/'data/shared_parameters.json')==X['baseline']['json_sha256']
    assert digest(SHARED/'scripts/check_shared.py')==X['baseline']['script_sha256']
    for s in PROV['corpus_sources']+PROV['read_files']:assert digest(CORPUS/s['path'])==s['sha256'],s['path']
    batches=physical_batches();flat=[c for row in batches for c in row]
    assert len(flat)==128 and len({(c['weight_plane'],c['input_column'],c['output_WL']) for c in flat})==128
    for j in range(16):assert sorted(c['weight_plane'] for c in flat if c['payload_element']==j)==list(range(8))
    assert all(len(row)==16 and len({(c['group'],c['weight_plane']) for c in row})==16 for row in batches)
    assert 128*4*2*16==S.L['resident_capacity_Byte']==16384
    assert C['write_resources']['binary_comparators_total']==2*C['parallel_program_cells']==32
    assert math.isclose(C['write_resources']['peak_array_current_budget_mA'],16*300/1000)
    for row in r['scenarios']:
        n=row['counts'];d=row['write_details']
        assert (n['evaluations'],n['adc_batches'],n['digital_ticks'])==(256,256,512)
        assert (row['B_S_Byte'],row['B_R_Byte'],d['data_beats'])==(128,16,1)
        assert row['tau_Byte_per_s']>0 and math.isfinite(row['ridge'])
        ps=d['phase_details'];assert [s['phase'] for s in ps]==['RESET','SET']
        assert all(s['batches']==8 for s in ps)
        components=d['front_ns']+sum(s[k] for s in ps for k in ['pulse_total_ns','HV_guard_total_ns','verify_read_total_ns','local_control_total_ns'])
        assert components==row['delta_R_ns']
        # Independent aggregation through shared direct_service using a full paired batch block.
        full=(row['delta_R_ns']-d['front_ns'])/8
        br,dr,nb,_=S.direct_service(dict(logical_weights_completed=16,cells_per_weight=8,parallel_cells=16,encoded_load_bits=128,first_data_in_command=True,complete_physical_update_ns=full),row['periphery_ns']['digital_tick'])
        assert br==16 and nb==8 and dr==row['delta_R_ns']
    a,b,c=r['comparisons_at_reference']
    assert math.isclose(b['delta_R_ns']-10,16*(a['delta_R_ns']-10))
    assert a['delta_R_ns']<c['delta_R_ns']==b['delta_R_ns']
    assert all(A['binary_sense_slot_ns'][n]==v['adc_batch'] for n,v in S.C['propagation']['profile_values'].items())
    assert len({x['delta_S_ns'] for x in [a,b,c]})==1
    assert math.isclose(S.seconds(1,'us'),S.seconds(1000,'ns'))
    print('PASS: shared/source hashes; 8-plane/two-group geometry; 128cell/16Byte coverage; RESET/SET and retry masks; full-cycle aggregation; finite metrics; controlled comparisons.')

def main():
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');args=p.parse_args()
    r=calculate();check(r)
    for name,txt in generate(r).items():
        if args.emit:(BASE/name).write_text(txt)
        else:assert (BASE/name).read_text()==txt,f'stale generated {name}'
    print('PASS: generated files match inputs/results.')
    for row in r['scenarios']:print(row['profile'],row['delta_S_ns'],row['delta_R_ns'],row['tau_Byte_per_s'],row['ridge'])
    for row in r['comparisons_at_reference']:print(row['label'],row['delta_R_ns'],row['tau_Byte_per_s'],row['ridge'])
if __name__=='__main__':main()
