"""Fresh locked-source builds and typed two-pass primitive execution."""
import difflib, hashlib, json, math, os, re, shutil, subprocess
from pathlib import Path
import timing
SHA='8a88abf85844c0e1ba17cc771ea535fff6040456'

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False)+'\n')

def build(case,root,out,cxx,own):
    revision="v2"  # Selected source interface; historical alternatives are not installed.
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
    adapter_source=own/'backend.cpp'
    shutil.copy2(adapter_source,src/'pilot.cpp')
    for header in own.glob('*.h'):shutil.copy2(header,src/header.name)
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
    dump(out/'source_manifest.json',{'backend_sha':SHA,'upstream_files':hashes,'constructor_inputs':primaries,'constructor_patch_sha256':sha(out/'constructor.patch'),'request_header_sha256':sha(src/'request.h'),'adapter_file':adapter_source.name,'adapter_sha256':sha(adapter_source),'adapter_headers':{h.name:sha(h) for h in own.glob('*.h')}})
    def execute(label,wire_um=10.,bits=10,operating_period_ns=None,policy="nominal_target", scenario_case=None):
        active_case = case if scenario_case is None else scenario_case
        # Native service budgets do not alter the compiled topology.  Every
        # execution explicitly binds its own primitive values for qualification.
        assert active_case['case_id'] == case['case_id']
        for key in ('logical', 'physical', 'resources', 'services', 'service_schedules'):
            assert active_case[key] == case[key], ('scenario changed compiled organization', key)
        assert active_case['device']['identity'] == case['device']['identity']

        def run(hz,suffix):
            result={}
            for line in command([str(exe),str(hz),str(wire_um),str(bits)],label+suffix).splitlines():
                if '=' in line:
                    k,v=line.split('=',1)
                    try:result[k]=float(v)
                    except ValueError:pass
            assert result and all(math.isfinite(x) for x in result.values())
            return result
        raw=run(2e8,'-physical')
        window=timing.reconstruction_window() if adc and revision=='v2' else None
        paths=[]
        for k,v in raw.items():
            if not k.endswith('_path_s'):continue
            name=k[:-2];multi=window is not None and name in timing.MULTICYCLE_PATHS
            launch=1 if name=='capture_enable_path' else 0;capture=2 if multi or launch==1 else 1
            paths.append({'id':name,'delay_ns':v*1e9,
                'start_register':'held_SAR_code_ibit_group_and_old_accumulator' if multi else 'existing_data_or_controller_state',
                'end_register':'existing_selected_output_accumulator' if multi or name=='capture_enable_path' else 'existing_data_or_controller_state',
                'constraint_clock_id':'lv_core','single_cycle':capture-launch==1,'launch_edge':launch,'capture_edge':capture,
                'available_cycles':capture-launch,'path_class':'held_reconstruction_data' if multi else 'single_cycle_control_or_io',
                'stable_sources':list(timing.DATA_SOURCES) if multi else [],'complete_serial_path':True,
                'actual_load':{'wire_per_logic_segment_um':wire_um,'wire_cap_F':raw['wire_cap_F'],'destination_DFF_data_cap_F':raw['dff_data_cap_F']},
                'path_status':'formula_based_bit_arrival_envelope' if multi else 'actual_case_gate_topology_under_engineering_conditions'})
        minimum=timing.qualify_paths(paths,window)
        if operating_period_ns is None:
            floor=max(5.,minimum)
            selected=floor if revision=='v1' or policy=='timing_floor' else math.ceil(floor*2-1e-10)/2
            choice='v1_auto_minimum' if revision=='v1' else ('timing_floor_diagnostic' if policy=='timing_floor' else 'target_5ns_else_upward_0.5ns_grid')
        else:selected=operating_period_ns;choice='explicit_fixed_legal_operating_point'
        clock=timing.select_period(paths,window,selected);clock['selection_policy']=choice
        final=run(1e9/selected,'-count');assert final['dff_cycle']==final['output_cycle']==final['controller_cycle']==1
        assert abs(final['clkFreq_hz']*selected-1e9)<1e-4
        for k,v in raw.items():
            if k.endswith('_path_s'):assert math.isclose(v,final[k],rel_tol=1e-12)
        result={'execution_revision':timing.EXECUTION_VERSION,'datapath_revision':revision,
            'sar_ns':final.get('sar_s',0)*1e9 if adc else None,**clock,
            'boundary_setup_ns':final['setup_s']*1e9,'dff_cycle':final['dff_cycle'],'paths':paths,
            'reconstruction_window':window,'raw_module_returns':final,'adc_bits':bits,'wire_um':wire_um,
            'constructor_inputs':primaries,'native_electrical_fields_used_by_primitives':False,'native_device':active_case['device'],
            'module_inventory':{'input_DFF':dims['INPUT_BITS'],'output_DFF':dims['OUTPUT_BITS'],'controller_state_DFF':32,
                'encoded_DFF':128 if rram else 0,'mask_DFF':128 if rram else 0,'SAR':adc,'arithmetic_lanes':16 if adc else 0,
                'extra_payload_or_code_registers':0,'weighted_tree_installed_bits':[9,9,9,9,11,11,15] if revision=='v2' and adc else None,
                'accumulator_bits':23,'FA_bitcell_count_per_arithmetic_lane':96 if revision=='v2' and adc else (194 if adc else 0)},
            'engineering_conditions':{'local_wire_um':wire_um,'wire_capacitance_fF_per_um':0.2,
                'wire_resistance_provider':'locked Param 22nm wire model',
                'register_boundary_model':'clock-Q and setup use two loaded inverters; existing V1 engineering approximation, not library STA',
                'arithmetic_timing':('exact bit wiring of fixed weighted tree; public Adder NAND sizing/capacitances and formula; per-bit Pareto arrival/slew propagation; same DAG evaluated numerically' if revision=='v2' else 'V1 full-width scalar Adder sums, single-cycle'),
                'source_loads':('count-code output drivers loaded from actual graph fanout; ibit uses bounded4fanout distribution across16 lanes; old accumulator and held group select both traverse bank mux' if revision=='v2' else 'V1 explicit fixed fanout and full-width scalar Adder load assumptions; see immutable backend_v1.cpp'),
                'capture_control':('phase updates at E1; decoder and active16x23 output-enable distribution plus destination mux/setup require one cycle' if revision=='v2' else 'V1 conservative full single-cycle path qualification during two scheduled ticks; no new multicycle exception'),
                'normalized_bits':6 if rram else 8,'shared_installed_partial_sum_bits':15 if revision=='v2' else 21,
                'RRAM_upper_count_bits':('hard zero under q>>4; same installed arithmetic widths; constant outputs have no timed arrival, but all installed NAND cells and input pin loads are retained' if revision=='v2' else 'V1 overwide18bit leaves do not prune constant cones'),
                'normalization':'q>>2 or q>>4 fixed bit wires; nominal transfer condition unchanged',
                'scope':'structural gate arrival envelope; no path sensitization, extracted layout, or silicon precision claim'},
            'partial_area_scope':'Only initialized SAR/DFF/Adder module area; formula mux/control gates, native arrays/frontends/writes/routing excluded. No DAG gate area added again. NOT macro PPA.'}
        dump(out/(label+'.json'),result);return result
    return execute
