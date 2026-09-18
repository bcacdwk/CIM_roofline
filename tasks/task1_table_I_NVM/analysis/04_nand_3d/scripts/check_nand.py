#!/usr/bin/env python3
"""NAND mapping and conditional coefficients via the shared calculation API.

Default verifies; --emit writes only this case's JSON/TeX/Markdown derivatives.
P, E and C remain unknown. Unit-basis calls derive algebraic coefficients only;
no synthetic device time is exposed as a real NAND scenario.
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

BASE = Path(__file__).resolve().parents[1]
CORPUS = BASE.parents[1]
X = json.loads((BASE/'data/inputs.json').read_text())
SHARED = BASE.parent/'shared_baseline'
spec = importlib.util.spec_from_file_location('shared_nand_calculation_api', SHARED/'scripts/check_shared.py')
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
M = X['mapping']
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def geometry():
    blocks = M['subarrays']*M['blocks_per_subarray']
    data_pages = blocks*M['output_wl_groups']
    return dict(blocks=blocks, subarrays=M['subarrays'], physical_page_bits=M['bitlines_per_page'],
                physical_page_Byte=M['bitlines_per_page']//8,
                physical_pages_per_block=M['wordlines_per_block']*M['ssl_per_block'],
                useful_data_pages_per_block=M['output_wl_groups'],
                data_pages_per_matrix=data_pages,
                logical_matrix_Byte=S.L['resident_capacity_Byte'],
                logical_bit_payload_per_data_page_Byte=S.L['resident_capacity_Byte']/data_pages,
                encoded_data_Byte=data_pages*M['bitlines_per_page']//8,
                physical_array_cells=blocks*M['bitlines_per_page']*M['wordlines_per_block']*M['ssl_per_block'],
                weight_bit_cell_copies=M['input_copies'],
                physical_data_cells=data_pages*M['bitlines_per_page'],
                adc_count=S.R['acim']['parallel_weight_planes']*S.R['acim']['adc_per_weight_plane'],
                maximum_sum_current_uA=2*M['bitlines_per_page']/1000,
                useful_count_LSB_current_nA=2*M['input_copies'],
                iid_cell_variation_sigma_in_count_LSB=0.3*math.sqrt(M['bitlines_per_page'])/(2*M['input_copies']))


def resident_ns(v, mode, program_us, erase_us, calibration_us, qcal=1):
    g=geometry()
    pages=g['data_pages_per_matrix']+(qcal*g['blocks'] if mode=='rewrite' else 0)
    front, beats=S.front_ns(g['physical_page_bits'],v['digital_tick'],False)
    steps=[dict(count=pages, drive_program_ns=program_us*1000,verify_ns=0,recover_ns=0)]
    # P is a full program block, so program-internal verify must not be charged twice.
    ns=S.program_sequence_ns(pages*front,calibration_us*1000,steps,
           erase=(g['blocks']*erase_us*1000 if mode=='rewrite' else 0),pages_per_erase=1)
    return ns,dict(program_cycles=pages,data_pages=g['data_pages_per_matrix'],
        calibration_pages=pages-g['data_pages_per_matrix'],erase_cycles=(g['blocks'] if mode=='rewrite' else 0),
        data_beats_per_page=beats,front_ns_per_page=front,front_total_ns=pages*front)


def recompute():
    g=geometry(); rows=[]
    for profile in ['short','reference','long']:
        v=S.C['propagation']['profile_values'][profile]
        sl=X['read']['sl_setup_ns_by_profile'][profile]
        ds0,counts,hold=S.acim_service(S.R['acim'],v,X['read']['bl_setup_ns']+sl)
        wl_count=M['output_wl_groups']
        # Compose the media-specific WL control blocks using the shared sequence API.
        ds=S.program_sequence_ns(ds0,0,[dict(count=wl_count,drive_program_ns=X['read']['wl_setup_ns'],verify_ns=0,recover_ns=0)])
        # metrics called with a positive unit time only to obtain the defined streaming rate.
        rho=S.metrics(S.L['B_S_Byte'],g['logical_matrix_Byte'],ds,1)['rho_Byte_per_s']
        variants=[]
        for mode,qcal in [('append',0),('rewrite',1),('rewrite',2)]:
            f,detail=resident_ns(v,mode,0,0,0,qcal)
            # Finite unit basis extracts exact linear coefficients, not device assumptions.
            cp=(resident_ns(v,mode,1,0,0,qcal)[0]-f)/1000
            ce=(resident_ns(v,mode,0,1,0,qcal)[0]-f)/1000
            cc=(resident_ns(v,mode,0,0,1,qcal)[0]-f)/1000
            ratio=S.L['B_S_Byte']/g['logical_matrix_Byte']
            co=dict(front_us=f/1000,P_us_coefficient=cp,E_us_coefficient=ce,C_us_coefficient=cc)
            variants.append(dict(mode=mode,calibration_wl_per_block=qcal,operation_counts=detail,
                delta_R_us_coefficients=co,ridge_coefficients=dict(constant=ratio*f/ds,
                    P_us=ratio*cp*1000/ds,E_us=ratio*ce*1000/ds,C_us=ratio*cc*1000/ds),
                P_us_at_ridge_1_given_E_C_zero=((ds/ratio-f)/1000)/cp,
                E_us_at_ridge_1_given_P_C_zero=(((ds/ratio-f)/1000)/ce if ce else None),
                tau_Byte_per_s=None,ridge=None,status='unknown absolute SLC program/erase/calibration; coefficients only'))
        rows.append(dict(profile=profile,periphery_ns=v,sl_setup_ns=sl,counts=counts,
            wl_setup_count=wl_count,wl_setup_total_ns=wl_count*X['read']['wl_setup_ns'],
            delta_S_ns=ds,rho_Byte_per_s=rho,extra_media_ns_per_evaluation_coefficient=counts['evaluations'],
            read_result_kind='conditional engineering estimate; not measured SLC macro result',resident=variants))
    return dict(schema_version='nand-3d-results-1',baseline_json_sha256=sha(SHARED/'data/shared_parameters.json'),
        baseline_script_sha256=sha(SHARED/'scripts/check_shared.py'),baseline_method_tex_sha256=sha(SHARED/'tex/02_estimation_method.tex'),geometry=g,scenarios=rows,
        conditional_rho_MB_per_s_range=[min(r['rho_Byte_per_s'] for r in rows)/1e6,max(r['rho_Byte_per_s'] for r in rows)/1e6],
        no_finite_supported_numeric_tau_ridge_range=True)


def latex_escape(x):
    for a,b in [('\\',r'\textbackslash{}'),('&',r'\&'),('%',r'\%'),('_',r'\_\allowbreak{}'),('#',r'\#')]: x=x.replace(a,b)
    return x.replace('μ',r'$\mu$').replace('×',r'$\times$').replace('~',r'$\sim$').replace('–','--')


def read_table(r):
    t=[r'% Generated by scripts/check_nand.py --emit.',r'\begin{table}[htbp]\centering\small',
       r'\begin{tabular}{@{}lrrrrr@{}}\toprule',
       r'情景 & $t_{SL}$ (ns) & $\Delta_S$ ($\mu$s) & $\rho$ (MB/s) & $F_{app}$ ($\mu$s) & $F_{rw,1}$ ($\mu$s)\\\midrule']
    labels=dict(short='短时隙',reference='参考',long='长时隙')
    for x in r['scenarios']:
        f=[a['delta_R_us_coefficients']['front_us'] for a in x['resident']]
        t.append(f"{labels[x['profile']]} & {x['sl_setup_ns']:g} & {x['delta_S_ns']/1000:.3f} & {x['rho_Byte_per_s']/1e6:.4g} & {f[0]:g} & {f[1]:g}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{条件读侧结果与整矩阵写数据装入/控制开销。$F_{app}$ 为1024数据页；$F_{rw,1}$ 为1024数据页加128校准页。MB 为$10^6$ Byte。SL中点640 ns为插值；不是新增实测点。}',r'\label{tab:read}\end{table}']
    return '\n'.join(t)+'\n'


def coeff_table(r):
    x=next(q for q in r['scenarios'] if q['profile']=='reference')
    t=[r'% Generated by scripts/check_nand.py --emit.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrrl@{}}\toprule',r'事务 & program页数 & erase块数 & $F$ ($\mu$s) & $\Delta_R$ ($\mu$s)\\\midrule']
    names=['预擦除append','重写，1校准WL','重写，2校准WL']
    for label,z in zip(names,x['resident']):
        d=z['delta_R_us_coefficients'];n=z['operation_counts']
        e=(f"+{d['E_us_coefficient']:g}E" if d['E_us_coefficient'] else '')
        t.append(f"{label} & {n['program_cycles']} & {n['erase_cycles']} & {d['front_us']:g} & ${d['front_us']:g}+{d['P_us_coefficient']:g}P{e}+C$\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{参考外围下的完整事务系数。每行$B_R=16384$ Byte；$P,E,C$均以$\mu$s计，分别为完整SLC-CIM页program、块erase、整事务额外校准时间。三者未被本地证据定值。}',r'\label{tab:coeff}\end{table}']
    return '\n'.join(t)+'\n'


def threshold_table(r):
    t=[r'% Generated by scripts/check_nand.py --emit.',r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}lrrr@{}}\toprule',r'外围情景 & append的$P$阈值 & 重写1校准WL的$P$阈值 & 重写1校准WL的$E$截距\\\midrule']
    for x in r['scenarios']:
        a,w=x['resident'][:2]
        t.append(f"{dict(short='短时隙',reference='参考',long='长时隙')[x['profile']]} & {a['P_us_at_ridge_1_given_E_C_zero']:.3f} & {w['P_us_at_ridge_1_given_E_C_zero']:.3f} & {w['E_us_at_ridge_1_given_P_C_zero']:.3f}\\\\")
    t += [r'\bottomrule\end{tabular}',r'\caption{由$\RI^*=1$反推的时间预算（$\mu$s）。$P$阈值设$E=C=0$；$E$截距设$P=C=0$。零值只用于求直线截距，不是物理情景或器件时间。}',r'\label{tab:threshold}\end{table}']
    return '\n'.join(t)+'\n'


def evidence_md():
    t=['# 参数与证据定位','', '原值、采用选择和不采用理由独立记录；PDF页为本地1基页序。','', '| ID | 来源/定位 | 原值、单位与条件 | 采用与换算 |','|---|---|---|---|']
    for x in X['raw_evidence']:t.append(f"| {x['id']} | {x['source']} · {x['locator']} | {x['raw']}；{x['condition']} | {x['adoption']} |")
    return '\n'.join(t)+'\n'


def evidence_tex():
    t=[r'% Generated from raw_evidence in inputs.json.',r'\begingroup\footnotesize',r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{25mm}>{\raggedright\arraybackslash}p{61mm}>{\raggedright\arraybackslash}p{70mm}@{}}',r'\caption{紧凑证据表：原值与本分析采用方式。PDF定位为本地页序。}\\',r'\toprule 来源/定位 & 原值与条件 & 采用、换算及限制\\\midrule\endfirsthead',r'\toprule 来源/定位 & 原值与条件 & 采用、换算及限制\\\midrule\endhead']
    for x in X['raw_evidence']:
        t.append(' & '.join(latex_escape(a) for a in [('公共基线：参数JSON与R0' if x['source']=='shared_baseline' else x['source']+' '+x['locator']),x['raw']+'。'+x['condition'],x['adoption']])+r'\\')
    return '\n'.join(t+[r'\bottomrule\end{longtable}\endgroup',''])


def generated():
    r=recompute()
    return {'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','tex/generated_read.tex':read_table(r),
        'tex/generated_coefficients.tex':coeff_table(r),'tex/generated_thresholds.tex':threshold_table(r),
        'tex/generated_evidence.tex':evidence_tex(),'notes/parameter_evidence.md':evidence_md()}


class Checks(unittest.TestCase):
    def test_baseline_hash_and_sources(self):
        self.assertEqual(X['baseline']['json_sha256'],sha(SHARED/'data/shared_parameters.json'))
        self.assertEqual(X['baseline']['script_sha256'],sha(SHARED/'scripts/check_shared.py'))
        self.assertEqual(X['baseline']['method_tex_sha256'],sha(SHARED/'tex/02_estimation_method.tex'))
        for source in X['sources'].values():
            self.assertEqual(source['actual_sha256'],sha(CORPUS/source['pdf']['path']))
            self.assertEqual(source['actual_sha256'],source['pdf']['sha256'])
    def test_native_geometry_and_logical_coverage(self):
        g=geometry()
        self.assertEqual(M['logical_inputs']*M['input_copies'],M['bitlines_per_page'])
        self.assertEqual(g['blocks'],M['weight_bit_planes']*M['outputs_per_wl_group'])
        self.assertEqual(M['outputs_per_wl_group']*M['output_wl_groups'],128)
        self.assertEqual(g['physical_data_cells']//M['input_copies'],g['logical_matrix_Byte']*8)
        self.assertEqual(g['data_pages_per_matrix'],1024)
        self.assertEqual(g['useful_data_pages_per_block'],8)
        self.assertEqual(g['physical_pages_per_block'],96)
        self.assertLess(M['output_wl_groups']+2,M['wordlines_per_block'])
    def test_complete_transactions_and_single_domain(self):
        v=S.C['propagation']['profile_values']['reference']
        # Independent algebra only as a test oracle; production calculation imports shared templates.
        for mode,q,pages in [('append',0,1024),('rewrite',1,1152),('rewrite',2,1280)]:
            ns,d=resident_ns(v,mode,13,21,7,q)
            erase=128*21000 if mode=='rewrite' else 0
            self.assertEqual(ns,pages*(110*5+13000)+erase+7000)
            self.assertEqual(d['data_beats_per_page'],108)
        self.assertEqual(M['program_domains'],1)
    def test_read_counts_wl_and_boundaries(self):
        for x in recompute()['scenarios']:
            n=x['counts'];v=x['periphery_ns']
            self.assertEqual([n['evaluations'],n['adc_batches'],n['digital_ticks']],[64,64,128])
            self.assertEqual(n['useful_scalar_conversions'],8192)
            self.assertEqual(x['delta_S_ns'],64*(v['input_step']+12+x['sl_setup_ns']+v['adc_batch']+2*v['digital_tick'])+2*v['digital_tick']+8*303)
    def test_missing_data_not_fabricated(self):
        self.assertIsNone(X['resident']['program_full_us'])
        self.assertIsNone(X['resident']['erase_full_us'])
        for x in recompute()['scenarios']:
            for r in x['resident']:
                self.assertIsNone(r['tau_Byte_per_s']);self.assertIsNone(r['ridge'])
                co=r['delta_R_us_coefficients'];coeff=r['ridge_coefficients']
                dr=co['front_us']+co['P_us_coefficient']*17+co['E_us_coefficient']*23+7
                expected=S.metrics(128,16384,x['delta_S_ns'],dr*1000)['ridge']
                self.assertAlmostEqual(expected,coeff['constant']+coeff['P_us']*17+coeff['E_us']*23+coeff['C_us']*7)
    def test_generated_files_are_current(self):
        for name,content in generated().items():self.assertEqual((BASE/name).read_text(),content,name)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--emit',action='store_true');a=p.parse_args()
    if a.emit:
        for name,content in generated().items():(BASE/name).write_text(content)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Checks)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(not result.wasSuccessful())
