"""Fresh locked-source builds and typed two-pass primitive execution."""
import difflib, hashlib, json, math, os, re, shutil, subprocess
from pathlib import Path
SHA='8a88abf85844c0e1ba17cc771ea535fff6040456'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def build(case,root,out,cxx,own):
    out.mkdir(parents=True); src=out/'src';src.mkdir();(out/'tmp').mkdir()
    tree=Path(json.loads((root/'worktrees.json').read_text())['2DInferenceV1.4'])
    assert subprocess.check_output(['git','-C',str(tree),'rev-parse','HEAD'],text=True).strip()==SHA
    core=tree/'Inference_pytorch/NeuroSIM'; hashes={}
    for f in sorted(core.iterdir()):
        if f.suffix in ['.cpp','.h']:
            # Compare shared source to locked Git blob: a dirty worktree cannot silently enter the run.
            blob=subprocess.check_output(['git','-C',str(tree),'show',SHA+':Inference_pytorch/NeuroSIM/'+f.name])
            assert hashlib.sha256(blob).hexdigest()==sha(f),('dirty upstream',f.name)
            hashes[f.name]=sha(f);shutil.copy2(f,src/f.name)
    cid=case['case_id'];rram=cid=='05_rram';adc=case['resources']['installed']['adc_count']
    original=(src/'Param.cpp').read_text();text=original
    primaries={'technode':22,'temp':300,'deviceroadmap':2,'memcelltype':2 if rram else 1,'numRowSubArray':64 if rram else 128,'numColSubArray':128}
    for key,value in primaries.items():
        text,n=re.subn(r'(?m)^(\s*'+key+r'\s*=\s*)[^;]+;',lambda m:m[1]+str(value)+';',text,count=1);assert n==1,key
    (src/'Param.cpp').write_text(text)
    patch=''.join(difflib.unified_diff(original.splitlines(True),text.splitlines(True),fromfile='a/Param.cpp',tofile='b/Param.cpp'))
    (out/'constructor.patch').write_text(patch)
    dims={'ACTIVE_TERMS':case['resources']['active']['streaming']['input_terms_per_group'],'ADC_COUNT':adc,'INPUT_BITS':case['resources']['installed']['input_register_bits'],'OUTPUT_BITS':case['resources']['installed']['output_register_bits'],'IS_RRAM':int(rram),'NATIVE_NODE':0,'NATIVE_READ_V':0,'NATIVE_RON':0,'NATIVE_ROFF':0,'NATIVE_READ_NS':0}
    # Native electrical fields are unused by these primitives; unknown is null in the resolved snapshot, never inferred from Param defaults.
    (src/'request.h').write_text('\n'.join('#define %s %s'%x for x in dims.items())+'\n')
    shutil.copy2(own/'backend.cpp',src/'pilot.cpp')
    cmds=[]
    def command(argv,label):
        result=subprocess.run(argv,cwd=out,env=dict(os.environ,TMPDIR=str(out/'tmp')),text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (out/(label+'.log')).write_text(result.stdout)
        cmds.append({'argv':list(map(str,argv)),'returncode':result.returncode,'log':label+'.log'});dump(out/'commands.json',cmds)
        if result.returncode:raise RuntimeError(str(out/(label+'.log')))
        return result.stdout
    exe=out/'pilot'
    cpp=[str(p) for p in sorted(src.glob('*.cpp')) if p.name!='main.cpp']
    command([cxx,'-std=c++11','-O2','-fopenmp','-w','-I',str(src),*cpp,'-o',str(exe)],'build')
    dump(out/'source_manifest.json',{'backend_sha':SHA,'upstream_files':hashes,'constructor_inputs':primaries,'constructor_patch_sha256':sha(out/'constructor.patch'),'request_header_sha256':sha(src/'request.h'),'adapter_sha256':sha(own/'backend.cpp')})
    def execute(label,wire_um=10.,bits=10):
        def run(hz,suffix):
            result={}
            for line in command([str(exe),str(hz),str(wire_um),str(bits)],label+suffix).splitlines():
                if '=' in line:
                    k,v=line.split('=',1)
                    try:result[k]=float(v)
                    except ValueError:pass
            assert result and all(math.isfinite(x) for x in result.values())
            return result
        raw=run(2e8,'-physical');limit=max(v*1e9 for k,v in raw.items() if k.endswith('_path_s'));period=max(5.,limit)
        final=run(1e9/period,'-count');assert final['dff_cycle']==final['output_cycle']==final['controller_cycle']==1
        assert abs(final['clkFreq_hz']*period-1e9)<1e-4
        paths=[]
        for k,v in final.items():
            if k.endswith('_path_s'):
                paths.append({'id':k[:-2],'delay_ns':v*1e9,'start_register':'held_SAR_code_and_output_accumulator' if k.startswith('reconstruct') else 'existing_data_or_controller_state','end_register':'existing_output_group' if k.startswith('reconstruct') else 'existing_data_or_controller_state','constraint_clock_id':'lv_core','single_cycle':True,'complete_serial_path':True,'actual_load':{'wire_per_logic_segment_um':wire_um,'wire_cap_F':final['wire_cap_F'],'destination_DFF_data_cap_F':final['dff_data_cap_F']},'path_status':'actual_case_path_instantiated_under_declared_gate_topology'})
        result={'sar_ns':final.get('sar_s',0)*1e9 if adc else None,'actual_period_ns':period,'boundary_setup_ns':final['setup_s']*1e9,'dff_cycle':final['dff_cycle'],'paths':paths,'raw_module_returns':final,'adc_bits':bits,'wire_um':wire_um,'constructor_inputs':primaries,'native_electrical_fields_used_by_primitives':False,'native_device':case['device'],'module_inventory':{'input_DFF':dims['INPUT_BITS'],'output_DFF':dims['OUTPUT_BITS'],'controller_state_DFF':32,'encoded_DFF':128 if rram else 0,'mask_DFF':128 if rram else 0,'SAR':adc,'arithmetic_lanes':16 if adc else 0,'extra_payload_or_code_registers':0},'engineering_conditions':{'local_wire_um':wire_um,'wire_capacitance_fF_per_um':0.2,'wire_resistance_provider':'locked Param 22nm wire model','register_boundary_model':'clock-Q and setup each represented by two loaded inverters; explicit engineering envelope, not DFF library characterization','logic_topology':'full-width unregistered ripple reduction; actual NAND2 input capacitance; <=4-way balanced inverter control distribution; bank feedback, sign/shift select and accumulator clear are separate paths','normalization':'fixed nominal power-of-two code mapping; physical calibration not modeled','gate_load_table':{'gate_chain_internal':'3 NAND2 inputs','tree_level0_to1':'4 next Adder NAND inputs including sign extension','tree_level1_to2':'4 next Adder NAND inputs','tree_result_to_shift':'8 NAND2 inputs including sign distribution','bank_feedback':'2 accumulator NAND inputs','control_distribution':'max4 INV inputs per branch; last max4 NAND2 inputs','clear_distribution_sinks':dims['OUTPUT_BITS'],'sign_select_distribution_sinks':368,'mask_control_sinks':128}},'partial_area_scope':'Only called SAR/DFF/Adder modules. Excludes formula-composed mux/control gates, native arrays/frontends/writes and routing. Diagnostic AdderTree excluded; NOT macro PPA.'}
        dump(out/(label+'.json'),result);return result
    return execute
