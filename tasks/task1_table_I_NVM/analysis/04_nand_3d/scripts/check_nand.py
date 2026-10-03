#!/usr/bin/env python3
"""Native NAND service calculation; default read-only, --emit updates case artifacts."""
# result_card.tex is owned and checked by analysis/scripts/export_ten_cases.py.
import argparse, hashlib, importlib.util, json, math, sys, unittest
from pathlib import Path
sys.dont_write_bytecode=True
BASE=Path(__file__).resolve().parents[1]
TASK=BASE.parents[1]
SHARED=BASE.parent/'shared_baseline'
spec=importlib.util.spec_from_file_location('nand_shared',SHARED/'scripts/check_shared.py')
S=importlib.util.module_from_spec(spec);spec.loader.exec_module(S)
D=json.loads((BASE/'data/inputs.json').read_text())
M=D['mapping']; C=D['design_choices']; L=S.logical_configuration(M['K'],M['N'])
PORT={'physical_write_data_lanes':128,'control_ticks':2}

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def configuration():
    physical=M['bitlines_per_page']*M['wordlines_per_block']*M['ssl_per_block']*M['blocks_per_subarray']
    data_cells=M['bitlines_per_page']*M['data_wl_per_block']*M['ssl_per_block']*M['blocks_per_subarray']
    calibration_channels=M['blocks_per_subarray']*math.ceil(M['K']/M['rows_per_group'])
    return dict(**L,mode='SLC SGVC current-sum ACIM, base4 offset encoding, approximate INT8',
        logical_matrix_order='W[N,K]',logical_capacity_Byte=L['resident_capacity_Byte'],
        physical_capacity_bit=physical,physical_capacity_Byte=physical/8,physical_data_cells=data_cells,
        reference_cells=physical-data_cells,logical_weight_bits=L['resident_capacity_Byte']*8,
        physical_cells_per_INT8_weight=36,encoding_ratio_data_bits_to_logical_bits=4.5,
        storage_utilization_including_required_encoding=data_cells/physical,
        independent_logical_fraction_of_physical_bit_capacity=L['resident_capacity_Byte']*8/physical,
        input_copies=3,weight_SSL_code='LSB once,MSB twice',bitlines_per_page=13824,physical_page_Byte=1728,
        blocks=64,wordlines_per_block=32,SSL_per_block=3,data_WL=30,reference_WL=2,
        row_group_size=1152,row_groups=4,parallel_output_lanes=16,physical_weight_digit_groups=4,
        resources={'ADC_count':64,'ADC_nominal_bits':10,'ADC_effective_bits':8,'current_frontends':64,
            'current_full_scale_uA_per_frontend':25,'dense_nominal_current_uA_per_frontend':20.736,
            'dense_total_current_mA':64*20.736/1000,'native_SL_capacitance_pF_per_block':16,
            'added_feedback_capacitance_pF':0,'digital_output_channels':16,'affine_multipliers':64,
            'input_register_bits':L['input_register_bits'],'intermediate_accumulator_bits':480*30,'intermediate_container_bits':30,'signed_correction_channel_bits':16*30,'final_output_register_bits':L['output_register_bits'],
            'weight_sum_metadata_bits':480*21,'input_sum_register_bits':21,
            'calibration_gain_offset_register_bits':calibration_channels*24*2,
            'calibration_arithmetic_lanes':16,'write_data_port_bits':128,'page_buffer_bits':13824,
            'actual_write_domain':'one native page program domain with native page-buffer inhibit/verify',
            'physical_page_program_targets':13824,'external_update_domains':1},
        update_mode='sustained whole-matrix replace;64block erases+6144page programs',
        resident_publish='atomic whole matrix after page verify,calibration and metadata pass',
        metadata_lifecycle=C['metadata_lifecycle'],precision_contract=L.get('precision_contract','calibrated approximate sums;offset correction does not recover ADC quantization'))

def scenario(profile):
    v=S.C['propagation']['profile_values'][profile];td=v['digital_tick']
    a={'input_bits_per_slice':2,'rows_per_group':1152,'weight_planes':4,'parallel_weight_planes':4,
       'evaluation_output_width':16,'adc_per_weight_plane':16,'digital_output_lanes':16,
       'digital_ticks_per_reconstruction_round':3,'hold_sample_slots':0,'hold_guarantee_ns':0,
       'hold_capture_ns_per_evaluation':0,'boundary_ticks':2}
    sl=C['sl_setup_budget_ns_by_profile'][profile];bl=D['reported_numeric']['bl_setup_ns'];wl=303
    # Native BL setup already covers input formation; do not add generic TI a second time.
    ds0,counts,_=S.acim_service(a,v,bl+sl-v['input_step'],L)
    input_sum_ticks=math.ceil(M['K']/C['input_sum_lanes'])
    correction_ticks=math.ceil(M['N']/16)*C['output_correction_ticks_per_group']
    ds=ds0+30*wl+(input_sum_ticks+correction_ticks)*td
    read_components={'WL_selection':30*wl,'BL_formation':counts['evaluations']*bl,
      'SL_establishment':counts['evaluations']*sl,'ADC_sample_convert':counts['adc_batches']*v['adc_batch'],
      'affine_merge_accumulate':counts['digital_ticks']*td,'input_offset_sum':input_sum_ticks*td,
      'final_signed_correction':correction_ticks*td,'capture_and_submit':2*td}
    assert math.isclose(sum(read_components.values()),ds)
    cal=C['calibration'];channels=64*cal['row_groups'];batches=math.ceil(channels/cal['arithmetic_lanes'])
    calticks=batches*(cal['division_ticks']+cal['other_ticks_per_channel_batch'])+cal['boundary_ticks']
    cal_reads=cal['samples_per_group']*cal['row_groups']
    calibration=cal['wordline_setups']*wl+cal_reads*(bl+sl+v['adc_batch'])+calticks*td
    program=C['program_full_budget_us_by_profile'][profile]*1000
    erase=C['erase_full_budget_ms_by_profile'][profile]*1e6
    # Each data WL:one canonical LSB page,one canonical MSB page,one MSB replica.
    # Input3x copies are already inside each physical1728B page. Payload allocation
    # is cost accounting;INT8 is only complete after all4 digit blocks are loaded.
    pages=[{'logical_payload_Byte':576,'encoded_load_bits':13824,'program_full_ns':program,'count':60},
           {'logical_payload_Byte':0,'encoded_load_bits':13824,'program_full_ns':program,'count':30},
           {'logical_payload_Byte':0,'encoded_load_bits':13824,'program_full_ns':program,'count':6}]
    block=S.native_block_service(pages,erase,td,PORT)
    # Popcount canonical (unreplicated)128bit groups, then shift/add into21bit sum.
    metadata_ticks=M['N']*8*math.ceil(M['K']/128)
    metadata_ns=metadata_ticks*td
    load=S.full_load_service(L,[{'payload_Byte':block['logical_payload_Byte'],'service_ns':block['T_R_ns'],'count':64},
       {'payload_Byte':0,'service_ns':metadata_ns},{'payload_Byte':0,'service_ns':calibration}])
    interface=S.mapping_metrics(L,ds,load['T_R_ns'])
    fpage,beats=S.front_ns(13824,td,False,PORT)
    write_components={'page_program_full':6144*program,'block_erase_full':64*erase,
      'encoded_page_load_and_control':6144*fpage,'weight_sum_metadata':metadata_ns,'calibration':calibration}
    assert math.isclose(sum(write_components.values()),load['T_R_ns'])
    append_TR=5760*(program+fpage)+metadata_ns+calibration
    append=S.mapping_metrics(L,ds,append_TR)
    return dict(id=profile,kind='paired_fixed_native_configuration',profile=profile,periphery_ns=v,
      read_counts=counts,read_service_components_ns=read_components,delta_S_ns=ds,
      wl_setup_count=30,BL_setup_includes_generic_input=True,sl_establishment_budget_ns=sl,
      current_full_scale_uA=25,dense_nominal_current_uA=20.736,program_budget_ns=program,erase_budget_ns=erase,
      calibration_counts={'analog_rounds':cal_reads,'channels':channels,'digital_ticks':calticks,'WL_setups':2},
      calibration_total_ns=calibration,metadata_generation_ticks=metadata_ticks,
      write_service_components_ns=write_components,page_data_beats=beats,block_service=block,
      full_load=load,mapping_interface=interface,rewrite=interface,
      append={'classification':'finite_preerased_burst_one_generation','precondition':'30dataWL erased and2referenceWL valid;all metadata/calibration regenerated','mapping_interface':append,**append},
      maintenance={'required_periodic_refresh':False,'raw':interface,'effective':dict(interface),'maintenance_payload_Byte':0},
      result_nature='conditional reference estimate from compatible native mapping and cross-implementation SLC P/E budget')

def calculate():
    ss=[scenario(p) for p in ['short','reference','long']]
    return dict(schema_version='nand-3d-native-reference',native_configuration=configuration(),
      baseline_json_sha256=sha(SHARED/'data/shared_parameters.json'),baseline_script_sha256=sha(SHARED/'scripts/check_shared.py'),
      baseline_method_tex_sha256=sha(SHARED/'tex/02_estimation_method.tex'),
      main_scenarios=ss,main_paired_ranges={k:[min(x['mapping_interface'][k] for x in ss),max(x['mapping_interface'][k] for x in ss)] for k in ['rho_Byte_per_s','tau_Byte_per_s','RI_star','U_star']},
      numeric_estimation_complete=True,range_kind='paired service conditions with fixed native organization/resources;not a confidence interval',
      excluded_full_width_configuration={'active_items':4608,'nominal_current_uA':82.944,'fixed_frontend_full_scale_uA':25,'feasible':False,'reason':'Dense full input exceeds current range;does not enter three scenarios'},
      sources={k:{'pdf':s['pdf'],'actual_sha256':sha(TASK/s['pdf']['path'])} for k,s in D['sources'].items()},
      external_review_judgments=['Current-sense frontend budgets at original bias with25uA fixed range and16pF native SL','SGVC SLC full P/E absolute times inferred from same-manufacturer SLC product','Approximate quantization with signed offset cancellation and finite row-group calibration'])

def table(headers,rows,caption,widths=None):
    cols='l'+'r'*(len(headers)-1) if widths is None else widths
    return '\n'.join([r'\begin{table}[htbp]\centering\small',r'\begin{tabular}{@{}'+cols+r'@{}}\toprule',' & '.join(headers)+r'\\\midrule']+[' & '.join(row)+r'\\' for row in rows]+[r'\bottomrule\end{tabular}',r'\caption{'+caption+r'}\end{table}',''])

def artifacts(result):
    ss=result['main_scenarios'];labels={'short':'乐观','reference':'典型','long':'悲观'}
    rows=[]
    for s in ss:
        r=s['mapping_interface'];rows.append([labels[s['id']],f"{r['delta_S_ns']/1000:.2f}",f"{r['T_R_ns']/1e9:.4f}",f"{r['rho_Byte_per_s']/1e6:.3g}",f"{r['tau_Byte_per_s']/1e6:.3g}",f"{r['RI_star']:.3g}",f"{r['U_star']:.3g}"])
    typ=ss[1]['mapping_interface']
    out={'data/results.json':json.dumps(result,ensure_ascii=False,indent=2)+'\n',
      'tex/generated_results.tex':table(['情景',r'$\Delta_S$($\mu$s)',r'$T_R$(s)',r'$\rho$(MB/s)',r'$\tau$(MB/s)',r'$\RI^*$',r'$U^*$'],rows,'原生 $K=4608,N=480$ 的固定配置成对结果。MB 为十进制；装载是完整矩阵持续替换。'),
      'tex/generated_budgets.tex':table(['情景',r'SL建立(ns)',r'完整页program($\mu$s)',r'完整块erase(ms)'],[[labels[s['id']],str(s['sl_establishment_budget_ns']),f"{s['program_budget_ns']/1000:g}",f"{s['erase_budget_ns']/1e6:g}"] for s in ss],'SL 是模型桥接预算；program/erase 是同厂异实现 SLC 完整操作锚点。短、典型共享典型 P/E，长端使用源表最大预算身份。'),
      'tex/generated_operations.tex':table(['完整操作','次数','有效逻辑payload'],[['数据页program','5760','2,211,840 Byte（全矩阵）'],['参考页program','384','0'],['块erase','64','0'],['输入向量求值','480轮','4608 Byte'],['校准参考读','12轮','0']],'编码复制和参考页占用物理资源，逻辑字节仅在完整状态就绪后提交。',widths='lrl'),
      'tex/generated_comparison.tex':table(['更新方式',r'$T_R$(s)',r'$\tau$(MB/s)',r'$\RI^*$'],[['持续完整替换',f"{typ['T_R_ns']/1e9:.4f}",f"{typ['tau_Byte_per_s']/1e6:.3g}",f"{typ['RI_star']:.3g}"],['预擦除有限一代',f"{ss[1]['append']['T_R_ns']/1e9:.4f}",f"{ss[1]['append']['tau_Byte_per_s']/1e6:.3g}",f"{ss[1]['append']['RI_star']:.3g}"]],'预擦除对照仅覆盖一个有限窗口，参考页预先存在；仍支付 metadata 和重新校准，不用于主表持续能力。'),
    }
    evidence=[r'\begingroup\small',r'\begin{longtable}{@{}>{\raggedright\arraybackslash}p{12mm}>{\raggedright\arraybackslash}p{29mm}>{\raggedright\arraybackslash}p{45mm}>{\raggedright\arraybackslash}p{62mm}@{}}\toprule ID & 原始证据 & 原值与定位 & 采用与边界\\\midrule\endhead']
    summaries=[
      ('E01','NAND-04','pp.2--3；13824 BL、32 WL、3 SSL；64块/subarray','四个两位权重块并行，30数据WL和2参考WL；K=4608，N=480。'),
      ('E02','NAND-05','pp.1--3，Fig.6；16层SGVC；2 nA均值、0.3 nA标准差','保留1 V选中栅压、0.2 V BL、4.5 V pass；不提高器件电流。'),
      ('E03','NAND-04','p.3 Table 1；WL303 ns、BL12 ns、SL530--750 ns；原生SL约16 pF','选530/640/750 ns为SL建立预算；640是工程内点；没有新增反馈积分电容。'),
      ('E04','NAND-05','pp.1--2；多bit读出约1微秒设计量级；应用最大电流25微安','固定前端量程25微安；1152项分组最大20.736微安；建立及零码响应需满足前端条件。'),
      ('E05','NAND-04/05','04 p.3；05 p.2；7位SAR及7--8位SA量化讨论','约8有效位为近似部分和；30位有符号中间通道、29位最终容器；不声称精确14位计数。'),
      ('E06','NAND-06','pp.5、25、31、43、58；SLC页program300/600微秒，块erase1/3.5毫秒','同厂异实现完整操作锚点；短/典型共用典型P/E，长端取源最大预算身份；不按页尺寸缩放。'),
      ('E07','NAND-05','p.2与Fig.12；一或两个已知码WL、除法器与推理校正','四行组各三次读、256对系数、16条校准通道；参考页及校准完整计时。'),
      ('E08','映射与公共方法','偏置码代数恒等式；INT8全值域检查','metadata是480个21位权重和；装载及每向量归约、30位最终校正均计资源与时间。'),
      ('E09','NAND-02','pp.1--3，Figs.15.1.2/5；verify与泵控制','完整program包含验证及恢复；不重复加verify，不取burst泵切换折扣。')]
    evidence += [' & '.join(row)+r'\\' for row in summaries]
    evidence += [r'\bottomrule\end{longtable}\endgroup',''];out['tex/generated_evidence.tex']='\n'.join(evidence)
    out['data/validation.json']=json.dumps({'method':'independent arithmetic and explicit encoder checks;no simulation','checks':['native capacities and encoding','all65536 signed INT8 encoder pairs','all data/reference pages and complete erase','headroom and group selection','independent typical time sum','TableII U* and finite-burst separation','source hashes and generated synchronization'],'expected_check_groups':7},ensure_ascii=False,indent=2)+'\n'
    return out

class Check(unittest.TestCase):
    def test_native_payload(self):
        n=configuration();self.assertEqual(n['physical_capacity_bit'],84934656);self.assertEqual(n['physical_data_cells'],79626240)
        self.assertEqual(n['logical_capacity_Byte'],2211840);self.assertEqual(n['reference_cells'],5308416)
        self.assertEqual(n['physical_cells_per_INT8_weight']*4608*480,n['physical_data_cells']);self.assertEqual(L['output_container_bits'],29);self.assertLess(4608*255*255,2**29);self.assertGreater(4608*255*255,2**28);self.assertEqual(n['resources']['intermediate_accumulator_bits'],14400)
    def test_signed_encoder(self):
        # Product of physical3-fold digit codes, independent of service implementation.
        for x in range(-128,128):
            for w in range(-128,128):
                xp=x+128;wp=w+128;z=0
                for a in range(4):
                    xd=(xp>>(2*a))&3;xb=[xd&1,(xd>>1)&1,(xd>>1)&1]
                    for b in range(4):
                        wd=(wp>>(2*b))&3;wb=[wd&1,(wd>>1)&1,(wd>>1)&1]
                        z+=sum(i*j for i in xb for j in wb)*(4**(a+b))
                self.assertEqual(z-128*xp-128*wp+16384,x*w)
    def test_mapping_selection_and_headroom(self):
        # Four BL groups partition4608 independent terms;duplicates never create new weights.
        visits=[i for g in range(4) for i in range(g*1152,(g+1)*1152)]
        self.assertEqual(visits,list(range(4608)));self.assertEqual(len({(j//16,j%16) for j in range(480)}),480)
        self.assertEqual(1152*3*3*2/1000,20.736);self.assertLess(20.736,25);self.assertGreater(4608*9*2/1000,25)
    def test_independent_typical(self):
        x=scenario('reference');r=x['mapping_interface']
        self.assertEqual(x['read_counts']['evaluations'],480);self.assertEqual(x['read_counts']['useful_scalar_conversions'],30720)
        self.assertEqual(r['delta_S_ns'],30*303+480*(12+640+20+15)+(288+60+2)*5)
        cal=2*303+12*(12+640+20)+450*5
        tr=6144*(300000+110*5)+64*1000000+480*8*36*5+cal
        self.assertEqual(r['T_R_ns'],tr);self.assertAlmostEqual(r['rho_Byte_per_s'],4608/(340600e-9))
        self.assertAlmostEqual(r['tau_Byte_per_s'],2211840/(tr*1e-9))
    def test_full_load_and_two_table_interface(self):
        for s in calculate()['main_scenarios']:
            r=s['mapping_interface'];self.assertEqual(s['block_service']['physical_pages'],96)
            self.assertEqual(s['full_load']['logical_payload_Byte'],4608*480)
            self.assertAlmostEqual(r['U_star'],480*r['RI_star']);self.assertEqual(r['B_R_Byte'],2211840)
            self.assertAlmostEqual(r['average_update_ns_per_16KiB'],r['T_R_ns']*16384/2211840)
            self.assertEqual(s['maintenance']['raw'],s['maintenance']['effective'])
            self.assertLess(s['append']['T_R_ns'],r['T_R_ns'])
    def test_sources(self):
        for s in D['sources'].values():self.assertEqual(sha(TASK/s['pdf']['path']),s['pdf']['sha256'])
    def test_synchronized(self):
        for p,t in artifacts(calculate()).items():self.assertEqual((BASE/p).read_text(),t,p)

if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('--emit',action='store_true');args=ap.parse_args()
    result=calculate()
    if args.emit:
        for p,t in artifacts(result).items():(BASE/p).write_text(t)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Check);ok=unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()
    if ok:
        for s in result['main_scenarios']:
            r=s['mapping_interface'];print(s['id'],{k:r[k] for k in ['delta_S_ns','T_R_ns','rho_Byte_per_s','tau_Byte_per_s','RI_star','U_star']})
    raise SystemExit(0 if ok else 1)
