#!/usr/bin/env python3
"""Reference-design NAND estimates, composed through the unchanged shared API.

--emit refreshes this case's results and tables. Source measurements, engineering
budgets and charge-derived timings remain distinct in inputs.json. No shared
files or source PDFs are written. A passed arithmetic check is not a silicon test.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
CORPUS=BASE.parents[1]
SHARED=BASE.parent/'shared_baseline'
X=json.loads((BASE/'data/inputs.json').read_text())
M=X['mapping']; D=X['design_choices']; E=X['reported_numeric']
spec=importlib.util.spec_from_file_location('shared_nand_api',SHARED/'scripts/check_shared.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def geometry(copies):
    blocks=M['subarrays']*M['blocks_per_subarray']
    data_pages=blocks*M['output_wl_groups']
    return dict(copies=copies,blocks=blocks,subarrays=M['subarrays'],physical_page_bits=M['bitlines_per_page'],
        physical_page_Byte=M['bitlines_per_page']//8,physical_pages_per_block=M['wordlines_per_block']*M['ssl_per_block'],
        useful_data_pages_per_block=M['output_wl_groups'],calibration_pages_per_block=M['calibration_wl_per_block'],
        data_pages_per_matrix=data_pages,calibration_pages_per_matrix=blocks*M['calibration_wl_per_block'],
        logical_matrix_Byte=S.L['resident_capacity_Byte'],logical_bit_payload_per_data_page_Byte=S.L['resident_capacity_Byte']/data_pages,
        physical_data_target_cells=data_pages*M['logical_inputs']*copies,
        active_bitlines_per_page=M['logical_inputs']*copies,
        encoded_data_Byte=data_pages*M['bitlines_per_page']//8,
        physical_array_cells=blocks*M['bitlines_per_page']*M['wordlines_per_block']*M['ssl_per_block'],
        adc_count=S.R['acim']['parallel_weight_planes']*S.R['acim']['adc_per_weight_plane'],
        added_integration_capacitance_pF=D['integration']['frontends']*D['integration']['feedback_capacitance_pF_per_channel'],
        maximum_sum_current_nA=E['cell_on_current_nA']*M['logical_inputs']*copies,
        required_fullscale_drive_uA_per_channel=E['cell_on_current_nA']*M['logical_inputs']*copies/1000,
        total_fullscale_signal_current_mA=E['cell_on_current_nA']*M['logical_inputs']*copies*D['integration']['frontends']/1e6,
        required_integrator_slew_V_per_us=D['integration']['useful_output_swing_V']/(integration_ns(copies)/1000),
        useful_count_LSB_current_nA=E['cell_on_current_nA']*copies,
        iid_sigma_in_count_LSB=E['cell_on_sigma_nA']*math.sqrt(M['logical_inputs']*copies)/(E['cell_on_current_nA']*copies))


def integration_ns(copies):
    # Physical input derivation, not a replacement of the shared service formulas.
    a=D['integration']
    q_coulomb=a['feedback_capacitance_pF_per_channel']*1e-12*a['useful_output_swing_V']
    current_ampere=M['logical_inputs']*copies*E['cell_on_current_nA']*1e-9
    return q_coulomb/current_ampere*1e9


def cal_counts():
    c=D['calibration'];n=math.ceil(D['integration']['frontends']/c['coefficient_channels'])
    ticks=n*(c['subtract_ticks']+c['division_steps']+c['store_ticks']+c['validation_ticks_per_batch'])+c['boundary_ticks']
    return dict(sample_rounds=c['sample_rounds'],wl_setups=c['wl_setups'],coefficient_batches=n,digital_ticks=ticks,
        coefficients=D['integration']['frontends'],division_steps=c['division_steps'])


def calibration_ns(v,media_ns):
    n=cal_counts()
    steps=[dict(count=n['wl_setups'],drive_program_ns=E['wl_setup_ns'],verify_ns=0,recover_ns=0),
        dict(count=n['sample_rounds'],drive_program_ns=v['input_step']+media_ns+v['adc_batch'],verify_ns=0,recover_ns=0),
        dict(count=n['digital_ticks'],drive_program_ns=v['digital_tick'],verify_ns=0,recover_ns=0)]
    return S.program_sequence_ns(0,0,steps)


def resident(v,mode,program_ns,erase_ns,cal_ns,g):
    data_pages=g['data_pages_per_matrix']
    cal_pages=g['calibration_pages_per_matrix'] if mode=='rewrite' else 0
    pages=data_pages+cal_pages
    erase_count=g['blocks'] if mode=='rewrite' else 0
    front,beats=S.front_ns(g['physical_page_bits'],v['digital_tick'],False)
    # In hardware each load is followed by its program. The sum below aggregates
    # these serial front stages; it does not require an all-pages input buffer.
    steps=[dict(count=pages,drive_program_ns=program_ns,verify_ns=0,recover_ns=0),
           dict(count=1,drive_program_ns=cal_ns,verify_ns=0,recover_ns=0)]
    dr=S.program_sequence_ns(pages*front,erase_count*erase_ns,steps)
    return dr,dict(data_pages=data_pages,calibration_pages=cal_pages,program_cycles=pages,erase_cycles=erase_count,
        data_beats_per_page=beats,front_ns_per_page=front,front_total_ns=pages*front,
        complete_program_total_ns=pages*program_ns,complete_erase_total_ns=erase_count*erase_ns,
        calibration_total_ns=cal_ns,physical_loaded_Byte=pages*g['physical_page_Byte'])


def scenario(profile,copies,kind):
    v=S.C['propagation']['profile_values'][profile];g=geometry(copies)
    sl=D['sl_setup_budget_ns_by_profile'][profile]
    tint=integration_ns(copies)
    media=E['bl_setup_ns']+sl+tint+sl
    cfg={**S.R['acim'],'digital_ticks_per_reconstruction_round':S.R['acim']['digital_ticks_per_reconstruction_round']+D['digital_correction_ticks_per_round']}
    ds0,counts,_=S.acim_service(cfg,v,media)
    ds=S.program_sequence_ns(ds0,0,[dict(count=M['output_wl_groups'],drive_program_ns=E['wl_setup_ns'],verify_ns=0,recover_ns=0)])
    c=calibration_ns(v,media)
    p=D['program_full_budget_ms_by_profile'][profile]*1e6
    e=D['erase_full_budget_ms_by_profile'][profile]*1e6
    result=dict(id=f'c{copies}_{profile}',kind=kind,profile=profile,copies=copies,geometry=g,periphery_ns=v,
        read_counts=counts,wl_setup_count=M['output_wl_groups'],integration_ns_per_evaluation=tint,
        read_service_components_ns=dict(wl=M['output_wl_groups']*E['wl_setup_ns'],input=counts['evaluations']*v['input_step'],
            bl=counts['evaluations']*E['bl_setup_ns'],sl_setup=counts['evaluations']*sl,
            integration=counts['evaluations']*tint,recovery=counts['evaluations']*sl,
            adc=counts['adc_batches']*v['adc_batch'],digital=counts['digital_ticks']*v['digital_tick'],boundary=2*v['digital_tick']),
        media_ns_per_evaluation=media,program_budget_ns=p,erase_budget_ns=e,calibration_counts=cal_counts(),calibration_total_ns=c,
        delta_S_ns=ds,result_nature='finite reference estimate with explicit resources and accepted-operation budgets; not measured device bounds')
    for mode in ['append','rewrite']:
        dr,ops=resident(v,mode,p,e,c,g)
        result[mode]={**S.metrics(S.L['B_S_Byte'],g['logical_matrix_Byte'],ds,dr),'operations':ops}
    return result


def recompute():
    rows=[scenario(p,M['main_input_copies'],'main') for p in ['short','reference','long']]
    comp=scenario('reference',M['comparison_input_copies'],'organization_comparison')
    ref=rows[1]
    comp['relative_to_main_reference']={k:comp['rewrite'][k]/ref['rewrite'][k] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    ranges={}
    for mode in ['append','rewrite']:
        ranges[mode]={k:[min(r[mode][k] for r in rows),max(r[mode][k] for r in rows)] for k in ['rho_Byte_per_s','tau_Byte_per_s','ridge']}
    return dict(schema_version='nand-3d-results-2',baseline_json_sha256=sha(SHARED/'data/shared_parameters.json'),
        baseline_script_sha256=sha(SHARED/'scripts/check_shared.py'),baseline_method_tex_sha256=sha(SHARED/'tex/02_estimation_method.tex'),
        main_scenarios=rows,organization_comparison=comp,main_paired_ranges=ranges,
        numeric_estimation_complete=True,range_kind='paired reference-design budgets, not statistical confidence intervals or universal SLC bounds')


def esc(x):
    for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('_',r'\_\allowbreak{}'),('#',r'\#')]:x=x.replace(a,b)
    return x.replace('μ',r'$\mu$').replace('×',r'$\times$').replace('~',r'$\sim$').replace('≈',r'$\approx$').replace('–','--')


def budget_table(r):
    t=[r'% Generated from inputs/results.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
       r'情景 & 建立/恢复各(ns) & $T_{int}$ ($\mu$s) & $P$ (ms) & $E$ (ms) & $C$ ($\mu$s)\\\midrule']
    for x in r['main_scenarios']:
        t.append(f"{dict(short='短预算',reference='参考',long='长预算')[x['profile']]} & {D['sl_setup_budget_ns_by_profile'][x['profile']]} & {x['integration_ns_per_evaluation']/1000:g} & {x['program_budget_ns']/1e6:g} & {x['erase_budget_ns']/1e6:g} & {x['calibration_total_ns']/1000:.3f}\\\\")
    return '\n'.join(t+[r'\bottomrule\end{tabular}',r'\caption{主情景的选定预算及推导校准时间。$P/E$是完整操作预算；$T_{int}$由电荷守恒导出，$C$由三次参考读和固定数字序列导出。}',r'\label{tab:budget}\end{table}',''])


def result_table(r):
    t=[r'% Generated from results.json.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrrr@{}}\toprule',
       r'情景 & $\Delta_S$ (ms) & $\rho$ & $\tau_{app}$ & $\RI^*_{app}$ & $\tau_{rw}$ & $\RI^*_{rw}$\\\midrule']
    for x in r['main_scenarios']:
        a,w=x['append'],x['rewrite']
        t.append(f"{dict(short='短预算',reference='参考',long='长预算')[x['profile']]} & {x['delta_S_ns']/1e6:.4f} & {w['rho_Byte_per_s']/1e3:.4g} & {a['tau_Byte_per_s']/1e3:.4g} & {a['ridge']:.4g} & {w['tau_Byte_per_s']/1e3:.4g} & {w['ridge']:.4g}\\\\")
    return '\n'.join(t+[r'\bottomrule\end{tabular}',r'\caption{有限主情景结果；三个吞吐列单位均为kB/s（$10^3$ Byte/s）。append只针对已有预擦除数据页和已编程参考页的窗口；两种写入均重新校准。}',r'\label{tab:results}\end{table}',''])


def operation_table(r):
    ref=r['main_scenarios'][1]
    t=[r'% Generated from results.json.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrr@{}}\toprule',r'参考事务 & 数据/参考页 & program次数 & erase次数 & $\Delta_R$ (s)\\\midrule']
    for mode,label in [('append','预擦除append'),('rewrite','同地址持续重写')]:
        z=ref[mode];n=z['operations']
        t.append(f"{label} & {n['data_pages']}/{n['calibration_pages']} & {n['program_cycles']} & {n['erase_cycles']} & {z['delta_R_ns']/1e9:.6f}\\\\")
    return '\n'.join(t+[r'\bottomrule\end{tabular}',r'\caption{整矩阵服务操作计数与参考时间。两行都完成$B_R=16384$ Byte；每页完整装入108拍加两拍控制，串行单更新域。}',r'\label{tab:operations}\end{table}',''])


def comparison_table(r):
    t=[r'% Generated from results.json.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrrr@{}}\toprule',r'参考外围/写预算 & $T_{int}$ ($\mu$s) & $\rho$ (kB/s) & $\tau_{rw}$ (kB/s) & $\RI^*_{rw}$ & $\sigma$/LSB\\\midrule']
    for x in [r['main_scenarios'][1],r['organization_comparison']]:
        z=x['rewrite'];t.append(f"$c={x['copies']}$ & {x['integration_ns_per_evaluation']/1000:.4g} & {z['rho_Byte_per_s']/1e3:.5g} & {z['tau_Byte_per_s']/1e3:.5g} & {z['ridge']:.5g} & {x['geometry']['iid_sigma_in_count_LSB']:.4g}\\\\")
    return '\n'.join(t+[r'\bottomrule\end{tabular}',r'\caption{唯一组织对照：同一前端、字节、完整写预算和校准规则，仅复制数变化。随机误差列为独立同分布满量程估计；二者逻辑格式相同，最终误差能力不相等。}',r'\label{tab:comparison}\end{table}',''])


def evidence_md():
    t=['# 原始量到参考预算的桥接','', 'PDF定位为本地1基页序；工程选择与原文值分列。','', '| ID | 来源/定位 | 原值、单位与条件 | 采用与桥接理由 |','|---|---|---|---|']
    for x in X['raw_evidence']:t.append(f"| {x['id']} | {x['source']} · {x['locator']} | {x['raw']}；{x['condition']} | {x['adoption']} |")
    return '\n'.join(t)+'\n'


def evidence_tex():
    t=[r'% Generated from raw_evidence in inputs.json.',r'\begingroup\footnotesize\setstretch{1.0}',r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{27mm}>{\raggedright\arraybackslash}p{59mm}>{\raggedright\arraybackslash}p{70mm}@{}}',
       r'\caption{原始量、采用预算与换算理由。}\label{tab:evidence}\\',r'\toprule 来源/定位 & 原值与条件 & 采用及桥接\\\midrule\endfirsthead',r'\toprule 来源/定位 & 原值与条件 & 采用及桥接\\\midrule\endhead']
    for x in X['raw_evidence']:
        t.append(' & '.join(esc(a) for a in [('公共基线：参数JSON与R0' if x['source']=='shared_baseline' else x['source']+' '+x['locator']),x['raw']+'。'+x['condition'],x['adoption']])+r'\\')
    return '\n'.join(t+[r'\bottomrule\end{longtable}\endgroup',''])


def generated():
    r=recompute()
    return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n',
        'tex/generated_budgets.tex':budget_table(r),'tex/generated_results.tex':result_table(r),
        'tex/generated_operations.tex':operation_table(r),'tex/generated_comparison.tex':comparison_table(r),
        'tex/generated_evidence.tex':evidence_tex(),'notes/parameter_evidence.md':evidence_md()}


class Checks(unittest.TestCase):
    def test_unchanged_shared_api_and_source_hashes(self):
        for key,path in [('json_sha256','data/shared_parameters.json'),('script_sha256','scripts/check_shared.py'),('method_tex_sha256','tex/02_estimation_method.tex')]:
            self.assertEqual(X['baseline'][key],sha(SHARED/path))
        for s in X['sources'].values():self.assertEqual(s['actual_sha256'],sha(CORPUS/s['pdf']['path']))
    def test_native_mapping_and_complete_INT8_transaction(self):
        for copies in [1,108]:
            g=geometry(copies)
            self.assertEqual(g['blocks'],128);self.assertEqual(g['data_pages_per_matrix'],1024)
            self.assertEqual(g['calibration_pages_per_matrix'],256)
            self.assertEqual(g['physical_data_target_cells']/copies,16384*8)
            self.assertLessEqual(g['active_bitlines_per_page'],g['physical_page_bits'])
            self.assertEqual(g['encoded_data_Byte'],1769472)
            self.assertEqual(g['useful_data_pages_per_block'],8)
            self.assertEqual(g['physical_pages_per_block'],96)
    def test_charge_derived_time_and_physical_resources(self):
        self.assertAlmostEqual(integration_ns(1),25000)
        self.assertAlmostEqual(integration_ns(108)*108,integration_ns(1))
        self.assertEqual(geometry(1)['added_integration_capacitance_pF'],2048)
        self.assertEqual(D['correction_parallel_multipliers'],128)
        self.assertAlmostEqual(geometry(108)['required_integrator_slew_V_per_us'],1.728)
        self.assertAlmostEqual(geometry(108)['total_fullscale_signal_current_mA'],3.538944)
    def test_separate_WL_evaluation_and_correction_counts(self):
        for x in recompute()['main_scenarios']:
            n=x['read_counts'];self.assertEqual([n['evaluations'],n['adc_batches'],n['digital_ticks']],[64,64,192])
            self.assertEqual(n['useful_scalar_conversions'],8192)
            self.assertAlmostEqual(sum(x['read_service_components_ns'].values()),x['delta_S_ns'])
            self.assertEqual(x['wl_setup_count'],8)
    def test_calibration_is_finite_and_always_charged(self):
        self.assertEqual(cal_counts()['digital_ticks'],226)
        for x in recompute()['main_scenarios']:
            v=x['periphery_ns'];oracle=2*303+3*(v['input_step']+x['media_ns_per_evaluation']+v['adc_batch'])+226*v['digital_tick']
            self.assertAlmostEqual(x['calibration_total_ns'],oracle)
            for mode in ['append','rewrite']:self.assertEqual(x[mode]['operations']['calibration_total_ns'],oracle)
    def test_complete_program_erase_and_native_loading(self):
        for x in recompute()['main_scenarios']:
            for mode,pages,erases in [('append',1024,0),('rewrite',1280,128)]:
                z=x[mode];n=z['operations']
                self.assertEqual(n['data_beats_per_page'],108)
                self.assertEqual(n['program_cycles'],pages);self.assertEqual(n['erase_cycles'],erases)
                oracle=pages*(110*x['periphery_ns']['digital_tick']+x['program_budget_ns'])+erases*x['erase_budget_ns']+x['calibration_total_ns']
                self.assertAlmostEqual(z['delta_R_ns'],oracle)
                self.assertAlmostEqual(z['ridge'],(128/16384)*(z['delta_R_ns']/x['delta_S_ns']))
                self.assertGreater(z['tau_Byte_per_s'],0)
    def test_single_fair_organization_comparison(self):
        r=recompute();a=r['main_scenarios'][1];b=r['organization_comparison']
        for key in ['program_budget_ns','erase_budget_ns','periphery_ns','calibration_counts']:self.assertEqual(a[key],b[key])
        for key in ['program_cycles','erase_cycles','physical_loaded_Byte']:self.assertEqual(a['rewrite']['operations'][key],b['rewrite']['operations'][key])
        self.assertEqual(M['program_domains'],1)
    def test_generated_files_current(self):
        for name,content in generated().items():self.assertEqual((BASE/name).read_text(),content,name)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--emit',action='store_true');args=parser.parse_args()
    if args.emit:
        for name,content in generated().items():(BASE/name).write_text(content)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Checks))
    sys.exit(not result.wasSuccessful())
