#!/usr/bin/env python3
"""RRAM native matrix/full-load service; shared APIs, default read-only."""
# result_card.tex is owned and checked by analysis/scripts/export_ten_cases.py.
import argparse,hashlib,importlib.util,json,math,sys,unittest
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[1];CORPUS=BASE.parents[1];SHARED=BASE.parent/'shared_baseline'
X=json.loads((BASE/'data/inputs.json').read_text());A=X['adopted_inputs'];C=X['configuration']
spec=importlib.util.spec_from_file_location('rram_shared',SHARED/'scripts/check_shared.py');S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
L=S.logical_configuration(C['logical_K'],C['logical_N']);PORT={'physical_write_data_lanes':128,'control_ticks':2}
LABEL={'short':'乐观','reference':'典型','long':'悲观'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def service_parameters(profile,parameter_overrides=None):
    values={**S.C['propagation']['profile_values'][profile],
      'cim_frontend_ns':A['front_end_settle_ns']['value']+A['additional_frontend_ns']['value'],
      'verify_frontend_ns':A['binary_verify_frontend_ns']['value'],
      'local_setup_ns':A['high_voltage_setup_ns_per_attempt']['by_profile'][profile],
      'local_return_ns':A['high_voltage_return_recover_ns_per_attempt']['by_profile'][profile],
      'set_pulse_ns':A['program_pulse_ns']['SET'],'reset_pulse_ns':A['program_pulse_ns']['RESET'],
      'rail_setup_ns':A['rail_lifecycle_ns']['setup'],'rail_exit_ns':A['rail_lifecycle_ns']['exit']}
    bindings={m['mode_id']:m['parameter_bindings'] for m in X['service_modes']}
    return S.resolve_service_parameters(values,bindings,parameter_overrides)

def write_service(profile,parallel=128,attempt_profile=None,transition_ns=None,parameter_overrides=None):
    modes=service_parameters(profile,parameter_overrides);u=modes['resident_update'];b=modes['endpoint_verify']
    td=u['digital_ns'];front,beats=S.front_ns(128,td,True,PORT)
    setup=u['setup_ns'] if transition_ns is None else transition_ns
    recover=u['return_ns'] if transition_ns is None else transition_ns
    nb=128//parallel;assert parallel in [16,128]
    verify=b['input_ns']+b['frontend_ns']+b['sense_ns']
    phases=[];steps=[]
    for phase in ['RESET','SET']:
        n=A['group_attempt_scenarios'][attempt_profile or profile][phase];count=nb*n
        phases.append(dict(phase=phase,batches=nb,attempts_per_batch=n,attempt_slots=count,
          pulse_total_ns=count*u[phase.lower()+'_pulse_ns'],local_transition_total_ns=count*(setup+recover),
          verify_read_total_ns=count*verify,control_total_ns=count*(td+b['digital_ns'])))
        steps.append(dict(count=count,drive_program_ns=setup+u[phase.lower()+'_pulse_ns']+td,
                          verify_ns=verify+b['digital_ns'],recover_ns=recover))
    local=S.program_sequence_ns(front,0,steps)
    rail=u['rail_setup_ns']+u['rail_exit_ns']
    load=S.full_load_service(L,[{'payload_Byte':16,'service_ns':local,'count':512},{'payload_Byte':0,'service_ns':rail}])
    details=dict(parallel_cells=parallel,local_transaction_Byte=16,local_transaction_ns=local,data_beats=beats,
      local_front_ns=front,phase_details=phases,local_transition_ns_each=setup if setup==recover else None,
      local_setup_ns=setup,local_return_ns=recover,verify_read_ns=verify,
      rail_setup_ns=u['rail_setup_ns'],rail_exit_ns=u['rail_exit_ns'],
      rail_lifecycle='regulatedprogramrail held throughout fullmatrix;local switching on everyattempt',
      peak_array_current_budget_mA=parallel*.3,binary_comparators=parallel*2,full_load=load,
      isolated_16B_request_ns=local+rail,success_condition='allactivecells meetbinarywindow withindeclaredattempts;failedfullmatrix is not published')
    return load['T_R_ns'],details

def native_configuration():
    return dict(**L,logical_capacity_Byte=8192,physical_capacity_bit=65536,physical_capacity_Byte=8192,
      physical_data_cells=65536,encoding='8binarybitplanes,no differential duplication;allm=1',
      mode='WH-2T1R32-item ACIM with native CIMSEL time selection',physical_native_macros=8,
      physical_macro_shape=[64,128],subarrays_per_macro=4,subarray_shape=[64,32],
      update_mode='single-domain sustained whole8192B matrix load;512local16B groups',
      resources={'ADC_count':128,'ADC_per_plane':16,'digital_output_channels':16,'active_input_terms':32,
       'write_driver_count':128,'binary_window_comparators':256,'program_current_rating_uA_per_lane':300,
       'total_program_current_rating_mA':38.4,'switched_capacitance_limit_pF_per_lane':1,
       'program_voltage_rating_V':1.8,'encoded_buffer_bits':128,'mask_done_bits':128,
       'input_register_bits':1024,'output_register_bits':64*23,'write_interface_bits':128,
       'external_update_domains':1,'shared_TBL_policy':'retain native4subarrays per macro;CIMSEL time-selects;no freeTBL isolation'},
      precision_contract='calibrated approximate bit-plane sums;INT8 final23bit container')

def calculate(parameter_overrides=None):
    cfg={**S.R['acim'],**C['acim_overrides']};rows=[]
    for p,v in S.C['propagation']['profile_values'].items():
        modes=service_parameters(p,parameter_overrides);e=modes['normal_evaluation']
        read_v={'input_step':e['input_ns'],'adc_batch':e['conversion_ns'],'digital_tick':e['digital_ns']}
        ds,counts,hold=S.acim_service(cfg,read_v,e['frontend_ns'],L)
        tr,wd=write_service(p,parameter_overrides=parameter_overrides);mi=S.mapping_metrics(L,ds,tr)
        rows.append(dict(profile=p,scenario_class=X['scenario_classification']['main'],
          periphery_ns=read_v,resolved_service_parameters=modes,counts=counts,hold_extra_ns=hold,write_details=wd,
          mapping_interface=mi,maintenance={'raw':mi,'effective':dict(mi),'maintenance_payload_Byte':0},**mi))
    ds=rows[1]['delta_S_ns'];com=[]
    for parallel in [128,16]:
        tr,wd=write_service('reference',parallel,parameter_overrides=parameter_overrides)
        com.append(dict(label=f'W{parallel}',scenario_class='reference' if parallel==128 else 'resource_comparison',write_details=wd,**S.mapping_metrics(L,ds,tr)))
    attempts=[]
    for p in ['short','reference','long']:
        tr,wd=write_service('reference',attempt_profile=p,parameter_overrides=parameter_overrides)
        attempts.append(dict(attempt_profile=p,scenario_class=X['scenario_classification']['attempt_sensitivity'],attempts=A['group_attempt_scenarios'][p],write_details=wd,**S.mapping_metrics(L,ds,tr)))
    transition=[]
    for g in [50,100,1000]:
        tr,wd=write_service('reference',transition_ns=g,parameter_overrides=parameter_overrides)
        transition.append(dict(local_transition_ns_each=g,scenario_class=X['scenario_classification']['transition_sensitivity'],write_details=wd,**S.mapping_metrics(L,ds,tr)))
    return dict(schema_version='rram-native-reference',native_configuration=native_configuration(),
      baseline_json_sha256=digest(SHARED/'data/shared_parameters.json'),baseline_script_sha256=digest(SHARED/'scripts/check_shared.py'),
      input_sha256=digest(BASE/'data/inputs.json'),numerical_media_write_point_available=True,
      service_modes=X['service_modes'],range_semantics=X['range_semantics'],
      scenarios=rows,paired_ranges={m:[min(r[m] for r in rows),max(r[m] for r in rows)] for m in ['rho_Byte_per_s','tau_Byte_per_s','RI_star']},
      comparisons_at_reference=com,attempt_sensitivity=attempts,local_transition_sensitivity=transition,
      dominant_parameters={'read':'32active/CIMSEL groups plus sharedADC/digital slots','write':'full1us RESET/SET waveforms,attemptcounts,128realdrivers andlocalbias switching'},
      sources={k:s['pdf'] for k,s in X.get('sources',{}).items()} if isinstance(X.get('sources'),dict) else {},
      external_review=['cross-stack1usprogramwaveforms andbinaryacceptancewindows','dedicated128driver/38.4mA supply and<=1pF local switchload','finite local50/100/250ns transitionbudgets andnormalattemptcompletion'])

def tab(headers,rows,caption):
    return '\n'.join([r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}l'+'r'*(len(headers)-1)+r'@{}}\toprule',' & '.join(headers)+r'\\\midrule']+[' & '.join(t)+r'\\' for t in rows]+[r'\bottomrule\end{tabular}',r'\caption{'+caption+r'}\end{table}',''])
def generate(r):
    rows=[]
    for s in r['scenarios']:
        k=A['group_attempt_scenarios'][s['profile']];rows.append([LABEL[s['profile']],f"{k['RESET']}/{k['SET']}",f"{s['delta_S_ns']/1000:.3f}",f"{s['T_R_ns']/1e6:.4f}",f"{s['rho_Byte_per_s']/1e6:.3g}",f"{s['tau_Byte_per_s']/1e6:.3g}",f"{s['RI_star']:.3g}"])
    out={'data/results.json':json.dumps(r,ensure_ascii=False,indent=2)+'\n','tex/generated_read.tex':tab(['情景',r'$K_R/K_S$',r'$\Delta_S$($\mu$s)',r'$T_R$(ms)',r'$\rho$(MB/s)',r'$\tau$(MB/s)',r'$\RI^*$'],rows,'原生 $K=128,N=64$，完整8192 Byte装载含一次写rail起退；固定128驱动、256比较器。三情景为声明次数内完成的条件选点，不是统计快慢界。')}
    br=[]
    for s in r['scenarios']:
        wd=s['write_details'];ps=wd['phase_details']
        vals=[512*sum(q[k] for q in ps)/1000 for k in ['pulse_total_ns','local_transition_total_ns','verify_read_total_ns','control_total_ns']]
        vals[-1]+=(512*wd['local_front_ns']+wd['rail_setup_ns']+wd['rail_exit_ns'])/1000
        br.append([LABEL[s['profile']]]+[f'{a:.3g}' for a in vals]+[f"{s['T_R_ns']/1000:.3g}"])
    out['tex/generated_write_breakdown.tex']=tab(['情景','脉冲','局部切换','新读验','控制/rail',r'总计($\mu$s)'],br,'全矩阵更新占用分解，时间均为微秒。rail仅在整矩阵边界起退，局部切换每次尝试都保留。')
    out['tex/generated_comparison.tex']=tab(['资源',r'额定电流(mA)',r'$T_R$(ms)',r'$\tau$(MB/s)',r'$\RI^*$'],[[s['label'],f"{s['write_details']['peak_array_current_budget_mA']:g}",f"{s['T_R_ns']/1e6:.4f}",f"{s['tau_Byte_per_s']/1e6:.3g}",f"{s['RI_star']:.3g}"] for s in r['comparisons_at_reference']],'W16缩资源对照将驱动与窗口比较器同比减少；同一脉冲/局部切换及完整rail生命周期，读侧不变。')
    out['tex/generated_attempts.tex']=tab([r'$K_R/K_S$',r'$T_R$(ms)',r'$\tau$(MB/s)',r'$\RI^*$'],[[f"{s['attempts']['RESET']}/{s['attempts']['SET']}",f"{s['T_R_ns']/1e6:.4f}",f"{s['tau_Byte_per_s']/1e6:.3g}",f"{s['RI_star']:.3g}"] for s in r['attempt_sensitivity']],'固定参考外围与100 ns局部切换，仅改变尝试次数；不解释为概率分布或材料最坏值。')
    typical=r['scenarios'][1]
    ev=[r'\begingroup\footnotesize\begin{longtable}{@{}>{\raggedright\arraybackslash}p{22mm}>{\raggedright\arraybackslash}p{59mm}>{\raggedright\arraybackslash}p{70mm}@{}}\toprule 来源 & 原始证据 & 采用与限制\\\midrule\endhead']
    evidence=[('RRAM-05','p.3 Figs.3--4：64行128列、四个64×32子阵列共享TBL；独立memory BL/SL写路径','每位平面保留完整原宏；四个32项输入组由CIMSEL分时。128驱动为明确新增资源，不能从原DIN接口推出。'),('RRAM-05','pp.4--7：典型LRS10千欧/HRS100千欧；32项m=1求和；PH0为5 ns','LRS8--12千欧、HRS至少70千欧为参考窗，非计算充分界。CIM与memory前端分别设参；共同时隙政策联动两路。'),('RRAM-01','p.10：1微秒SET/RESET；外部DAC/ADC受限的1--10微秒读回','跨stack波形预算：原目标最高30/40微西门子，本LRS窗83--125微西门子，未证明同脉宽可达本窗。'),('RRAM-03/06','03 p.5：二态多数名义条件完成，少量追加；06 pp.1--2：双组mask/done及超时','仅支持一次及追加写验的类别；2/1为RESET增加一次裕量的条件选点，无实测次数分布。保留完整RESET。'),('公共方法与选择','128个实际目标、300微安每lane、256比较器、每lane局部切换负载不大于1 pF','最大1.8 V与8千欧量级给225微安；剩余75微安对1.8 pC约24 ns。50/100/250 ns是有限切换预算，不是实测转换延时。')]
    ev += [' & '.join(q)+r'\\' for q in evidence]+[r'\bottomrule\end{longtable}\endgroup',''];out['tex/generated_evidence.tex']='\n'.join(ev)
    md=['# RRAM 参数证据','','原始PDF是证据，输入JSON保留原值与采用参数。局部切换和rail生命周期分开。','']
    for e in X['reported_evidence']:md += [f"## {e['id']} — {e['source_id']}",'',e['locator'],'','原值：'+e['original'],'','条件：'+e['condition'],'','采用：'+e['adoption'],'']
    out['notes/parameter_evidence.zh.md']='\n'.join(md)
    return out

class Check(unittest.TestCase):
    def test_mode_dependencies_independent(self):
        # Expected slopes count 128 evaluation rounds and 512 full-load groups,
        # with three attempt slots at reference; no production timing helper is used.
        base_ds=128*(5+5+20+2*5)+2*5
        base_tr=512*(2*5+3*(1000+100+100+5+5+20+2*5))+2000
        expected={
          'cim_frontend_ns':(5,128,0),
          'verify_frontend_ns':(5,0,512*3),
          'adc_batch':(20,128,512*3),
          'input_step':(5,128,512*3),
          'digital_tick':(5,128*2+2,512*(2+3*2)),
          'local_setup_ns':(100,0,512*3),
          'local_return_ns':(100,0,512*3),
          'reset_pulse_ns':(1000,0,512*2),
          'set_pulse_ns':(1000,0,512),
          'rail_setup_ns':(1000,0,1),
          'rail_exit_ns':(1000,0,1)}
        for name,(value,dds,dtr) in expected.items():
            with self.subTest(parameter=name):
                s=calculate({name:value+1})['scenarios'][1]
                self.assertEqual(s['delta_S_ns'],base_ds+dds)
                self.assertEqual(s['T_R_ns'],base_tr+dtr)
                self.assertAlmostEqual(s['rho_Byte_per_s'],128e9/(base_ds+dds))
                self.assertAlmostEqual(s['tau_Byte_per_s'],8192e9/(base_tr+dtr))
                self.assertAlmostEqual(s['U_star'],(base_tr+dtr)/(base_ds+dds))
        with self.assertRaises(AssertionError):service_parameters('reference',{'unknown_frontend':1})
        modes=service_parameters('reference',{'adc_batch':21})
        self.assertEqual(modes['normal_evaluation']['conversion_ns'],21)
        self.assertEqual(modes['endpoint_verify']['sense_ns'],21)

    def test_input_frontends_are_consumed(self):
        # Mutate the actual input slots, not only resolver overrides.
        old_read=A['front_end_settle_ns']['value'];old_verify=A['binary_verify_frontend_ns']['value']
        try:
            A['front_end_settle_ns']['value']=old_read+2
            A['binary_verify_frontend_ns']['value']=old_verify+3
            s=calculate()['scenarios'][1]
            self.assertEqual(s['delta_S_ns'],5130+128*2)
            self.assertEqual(s['T_R_ns'],1911760+512*3*3)
        finally:
            A['front_end_settle_ns']['value']=old_read
            A['binary_verify_frontend_ns']['value']=old_verify

    def test_native_and_update_selection(self):
        self.assertEqual(8*64*128,65536);self.assertEqual(8*64*128/8,8192)
        positions=[]
        for out in range(64):
            for group in range(4):
                for half in range(2):
                    cols=[group*32+g*16+half*8+k for g in range(2) for k in range(8)]
                    positions.extend((out,c) for c in cols)
        self.assertEqual(len(positions),8192);self.assertEqual(len(set(positions)),8192)
    def test_independent_typical(self):
        s=calculate()['scenarios'][1]
        self.assertEqual(s['delta_S_ns'],128*(5+5+20+2*5)+2*5)
        local=10+3*(1000+100+100+5+5+20+5+5)
        tr=512*local+2000
        self.assertEqual(local,3730);self.assertEqual(tr,1911760);self.assertEqual(s['T_R_ns'],tr)
        self.assertAlmostEqual(s['tau_Byte_per_s'],8192/(1911760e-9))
        self.assertEqual(s['write_details']['binary_comparators'],256)
    def test_boundaries_payload_and_interfaces(self):
        for s in calculate()['scenarios']:
            self.assertEqual(s['B_R_Byte'],8192);self.assertEqual(s['B_S_Byte'],128)
            self.assertAlmostEqual(s['U_star'],64*s['RI_star']);self.assertEqual(s['write_details']['data_beats'],1)
            wd=s['write_details'];terms=wd['local_front_ns']+sum(q[k] for q in wd['phase_details'] for k in ['pulse_total_ns','local_transition_total_ns','verify_read_total_ns','control_total_ns'])
            self.assertEqual(terms,wd['local_transaction_ns']);self.assertEqual(s['T_R_ns'],512*terms+2000)
    def test_fixed_resources_and_sensitivity(self):
        r=calculate();a,b=r['comparisons_at_reference'];self.assertGreater(a['tau_Byte_per_s'],b['tau_Byte_per_s'])
        self.assertEqual([q['write_details']['parallel_cells'] for q in r['scenarios']],[128]*3)
        self.assertEqual(len({q['delta_S_ns'] for q in r['attempt_sensitivity']}),1)
        self.assertLess(r['local_transition_sensitivity'][0]['T_R_ns'],r['local_transition_sensitivity'][-1]['T_R_ns'])
        self.assertEqual(1.8/8000*1e6,225);self.assertAlmostEqual(1e-12*1.8/(75e-6)*1e9,24)
    def test_sources(self):
        p=json.loads((BASE/'data/provenance.json').read_text())
        for q in p['corpus_sources']:self.assertEqual(digest(CORPUS/q['path']),q['sha256'])
    def test_generated(self):
        for p,t in generate(calculate()).items():self.assertEqual((BASE/p).read_text(),t,p)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--emit',action='store_true');a=ap.parse_args();r=calculate()
    if a.emit:
        for p,t in generate(r).items():(BASE/p).write_text(t)
    ok=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Check)).wasSuccessful()
    for q in r['scenarios']:print(q['profile'],q['delta_S_ns'],q['T_R_ns'],q['rho_Byte_per_s']/1e6,q['tau_Byte_per_s']/1e6,q['RI_star'])
    raise SystemExit(0 if ok else 1)
