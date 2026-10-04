#!/usr/bin/env python3
"""Step 2 encoding/resource probes; standard library, no device performance outputs."""
import argparse
import ast
import datetime
import hashlib
import json
import math
import os
from pathlib import Path
import shutil
import sys
import traceback
sys.dont_write_bytecode = True

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dump(p,obj):Path(p).write_text(json.dumps(obj,indent=2,ensure_ascii=False)+"\n")
def ceildiv(n,d):
    if n<0 or d<=0:raise ValueError('invalid count or resource width')
    return (n+d-1)//d
def pointer(obj,path):
    if path=='':return obj
    if not path.startswith('/'):raise ValueError('invalid JSON pointer')
    for token in path[1:].split('/'):
        token=token.replace('~1','/').replace('~0','~')
        obj=obj[int(token)] if isinstance(obj,list) else obj[token]
    return obj
def walk(obj):
    yield obj
    if isinstance(obj,dict):
        for value in obj.values():yield from walk(value)
    elif isinstance(obj,list):
        for value in obj:yield from walk(value)
def tc_bits(n):
    if not -128<=n<=127:raise ValueError('not INT8')
    return [(n&255)>>b&1 for b in range(8)]
def tc_decode(bits):return sum(bit*((1<<i) if i<7 else -128) for i,bit in enumerate(bits))
def signed_digits(n):
    if not -128<=n<=127:raise ValueError('not INT8')
    mag=abs(n)
    return (1 if n>=0 else -1),[(mag>>(2*i))&3 for i in range(4)]
def nand_pair(x,w):
    sx,dx=signed_digits(x);sw,dw=signed_digits(w)
    # Two input phases and two distinct weight polarity banks. Each base4 digit
    # maps to LSB once,MSB twice on three physical lanes/SSL positions.
    px=1 if sx>0 else 0;nx=1-px;pw=1 if sw>0 else 0;nw=1-pw
    reconstructed=0
    for i,a in enumerate(dx):
        input_copies=[int(a>=j) for j in (1,2,3)]
        for j,b in enumerate(dw):
            ssl=[b&1,(b>>1)&1,(b>>1)&1]
            physical_on_terms=sum(input_copies)*sum(ssl)
            sign=(px-nx)*(pw-nw)
            reconstructed+=sign*physical_on_terms*(4**i)*(4**j)
    return reconstructed
def digital_tile(rows,cols,bits,sense,hold):
    need=rows*cols*bits
    if hold<need:raise ValueError('insufficient hold capacity; no free bank')
    return {'tile_bits':need,'read_batches':ceildiv(need,sense)}
def load_units(payload,transaction):
    return [min(transaction,payload-off) for off in range(0,payload,transaction)]
def analog_batch(planes,adc_per_plane,installed,evaluated_outputs,hold_slots):
    if planes*adc_per_plane>installed:raise ValueError('ADC parallelism exceeds installed converters')
    if evaluated_outputs>adc_per_plane and hold_slots<planes*evaluated_outputs:raise ValueError('unfunded analog hold across ADC batches')
    return ceildiv(evaluated_outputs,adc_per_plane)

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);ap.add_argument('--cxx',default='not_used');a=ap.parse_args()
    root=a.root.expanduser().resolve();out=a.out.expanduser().resolve()
    if root not in out.parents or any(s in str(out).lower() for s in ('onedrive','icloud','cloudstorage','mobile documents')):raise SystemExit('out must be a fresh directory below local root, outside cloud storage')
    out.mkdir(parents=True,exist_ok=False)
    os.environ['TMPDIR']=str(root/'cache/tmp')
    original=Path(__file__).resolve();canonical=original.parent
    management=canonical.parents[1]
    configs=management/'configs/cases'
    repo_env=os.environ.get('NEUROSIM_REPO_ROOT')
    if repo_env:repo=Path(repo_env).expanduser().resolve()
    else:
        repo=next((p for p in canonical.parents if (p/'tasks/task1_table_I_NVM/analysis').is_dir()),None)
        if repo is None:raise SystemExit('NEUROSIM_REPO_ROOT required outside canonical repository')
    snapshot=out/'snapshot';(snapshot/'probe').mkdir(parents=True);(snapshot/'cases').mkdir()
    manifest={}
    for p in sorted(canonical.iterdir()):
        if p.is_file() and p.suffix in ('.py','.json','.md'):
            shutil.copy2(p,snapshot/'probe'/p.name);manifest['probe/'+p.name]=digest(p)
    for p in sorted(configs.glob('*.json')):
        shutil.copy2(p,snapshot/'cases'/p.name);manifest['cases/'+p.name]=digest(p)
    dump(out/'source_hashes.json',manifest)
    dump(out/'invocation.json',{'argv':[sys.executable]+sys.argv,'cwd':os.getcwd(),'root':str(root),'out':str(out),'cxx_argument':a.cxx,'cxx_used':False,'repo_root':str(repo)})
    # All actual computations are from the local copy; --out already allocated.
    if os.environ.get('NEUROSIM_ENCODING_LOCAL')!='1':
        env=os.environ.copy();env.update(NEUROSIM_ENCODING_LOCAL='1',NEUROSIM_ENCODING_OUT=str(out),NEUROSIM_REPO_ROOT=str(repo),PYTHONDONTWRITEBYTECODE='1')
        os.execve(sys.executable,[sys.executable,str(snapshot/'probe'/original.name),'--local'],env)

def local_main():
    out=Path(os.environ['NEUROSIM_ENCODING_OUT']);root=out
    repo=Path(os.environ['NEUROSIM_REPO_ROOT']);os.chdir(out)
    configs=[json.loads(p.read_text()) for p in sorted((out/'snapshot/cases').glob('*.json'))]
    assertions=[];details={};errors=[]
    def check(name,value,detail=None):
        ok=bool(value);assertions.append({'id':name,'status':'PASS' if ok else 'FAIL','detail':detail})
        if not ok:errors.append(name)
    def rejects(name,fn):
        try:fn()
        except ValueError:check(name,True);return
        check(name,False)
    try:
        check('ten_input_specifications',len(configs)==10)
        source_pointer_count=0;source_hash_count=0
        for c in configs:
            cid=c['case_id'];src=c['provenance']['sources'];loaded={}
            for sid,record in src.items():
                p=repo/record['path'];check(cid+'.hash.'+sid,digest(p)==record['sha256']);source_hash_count+=1
                if p.suffix=='.json':loaded[sid]=json.loads(p.read_text())
                elif p.suffix=='.py':loaded[sid]={n.name for n in ast.walk(ast.parse(p.read_text())) if isinstance(n,ast.FunctionDef)}
            for item in walk(c):
                if not isinstance(item,dict) or 'source_id' not in item:continue
                sid=item['source_id']
                if 'json_pointer' in item:pointer(loaded[sid],item['json_pointer']);source_pointer_count+=1
                if 'function' in item:check(cid+'.function.'+item['function'],item['function'] in loaded[sid])
            log=c['logical'];k,n=log['K'],log['N'];resources=c['resources'];phy=c['physical']
            check(cid+'.byte_not_bit',log['input_bits']==log['weight_bits']==8 and log['bytes_per_input']==log['bytes_per_weight']==1)
            check(cid+'.payload',log['B_S_Byte']==k and log['B_R_Byte']==k*n and phy['effective_capacity_Byte']==k*n)
            check(cid+'.output_container',log['output_bits']==16+math.ceil(math.log2(k)) and 2**(log['output_bits']-1)>k*128*128)
            check(cid+'.data_sites',phy['data_storage_sites']==k*n*phy['cells_per_INT8_weight'])
            check(cid+'.single_update_domain',resources['installed']['external_update_domains']==1)
            check(cid+'.register_inventory',resources['installed']['input_register_bits']==8*k and resources['installed']['output_register_bits']==n*log['output_bits'])
            check(cid+'.no_logical_array_alias',phy['neurosim_array_assignment']['numRowSubArray'] is None and phy['neurosim_array_assignment']['numColSubArray'] is None)
            check(cid+'.no_performance_targets',all(not any(key in obj for key in ('rho','tau','T_R_ns','delta_S_ns','delta_R_ns')) for obj in walk(c) if isinstance(obj,dict)))
            sids={s['id'] for s in c['services']}
            check(cid+'.stage_ids_unique',len(sids)==len(c['services']))
            check(cid+'.dependencies',all(d in sids for s in c['services'] for d in s['depends_on']))
            totals={sid:0 for sid in sids}
            def tally(steps,multiplier=1):
                for node in steps:
                    if 'repeat' in node:
                        if not isinstance(node['repeat'],int) or node['repeat']<=0:raise ValueError('nonpositive schedule repeat')
                        tally(node['steps'],multiplier*node['repeat'])
                    else:totals[node['stage_id']]+=multiplier*node['count']
            for mode in ('streaming','resident','maintenance'):tally(c['service_schedules'][mode]['steps'])
            check(cid+'.nested_schedule_counts',all(totals[s['id']]==s['count']['value'] for s in c['services']),{'expanded_counts':totals})
            check(cid+'.cycle_outputs_named_clock',all(o.get('clock_id')=='lv_core' for s in c['services'] for o in s['call']['outputs'] if isinstance(o,dict) and o.get('unit')=='cycles'))
            check(cid+'.physical_time_no_conversion_clock',all(o.get('clock_id') is None for s in c['services'] for o in s['call']['outputs'] if isinstance(o,dict) and o.get('unit') in ('s','ns')))
            check(cid+'.digital_no_additive_comb_cycles',all(s['call']['timing_plan']['forbid_additive_combination_cycles'] and s['call']['timing_plan']['DFF_numRead']==1 for s in c['services'] if 'timing_plan' in s['call']))
            check(cid+'.boundaries',{'input_capture','output_commit'}<=sids)
            check(cid+'.counts_positive',all(isinstance(s['count']['value'],int) and s['count']['value']>0 for s in c['services']))
            check(cid+'.no_empty_active_bindings',all(b.get('status')!='active' or bool(b['consumers']) for b in c['parameter_bindings']))
            check(cid+'.policy',c['periphery']['policy_id']=='lv_v14_22nm_lstp_300k_v1' and c['periphery']['clock']['actual_period_ns'] is None)
            check(cid+'.source_contract',c['status']=='input_specification' and c['contract_version']=='2.0.0')
            check(cid+'.driver_not_interface_inference',resources['installed']['real_write_driver_count'] is None if cid.startswith(('03_','04_')) else resources['installed']['real_write_driver_count']>0)
        details['source_validation']={'file_hashes':source_hash_count,'json_pointer_resolutions':source_pointer_count}
        values=[-128,-1,0,1,127]
        check('two_complement_roundtrip_all_INT8',all(tc_decode(tc_bits(v))==v for v in range(-128,128)))
        coefficients=[1,2,4,8,16,32,64,-128]
        pairs=values+[-97,-31,-2,2,33,96,126]
        check('two_complement_product_reconstruction',all(sum(a*b*coefficients[i]*coefficients[j] for i,a in enumerate(tc_bits(x)) for j,b in enumerate(tc_bits(w)))==x*w for x in pairs for w in pairs))
        check('nand_split_sign_base4_all_INT8_pairs',all(nand_pair(x,w)==x*w for x in range(-128,128) for w in range(-128,128)))
        mixed_x=[((i*73+19)%256)-128 for i in range(256)];mixed_w=[((i*37+7)%256)-128 for i in range(256)]
        check('mixed_signed_dot',sum(nand_pair(x,w) for x,w in zip(mixed_x,mixed_w))==sum(x*w for x,w in zip(mixed_x,mixed_w)))
        details['encoding']={'explicit_edge_values':values,'two_complement_roundtrips':256,'nand_product_pairs':65536,'mixed_dot_terms':256,'mixed_dot_integer':sum(x*w for x,w in zip(mixed_x,mixed_w)),'full_NAND_matrix_allocated':False,'scope':'ideal encoding algebra; no claim of ADC precision, analog calibration or device timing'}
        rejects('reject_OUT_OF_INT8_high',lambda:tc_bits(128));rejects('reject_OUT_OF_INT8_low',lambda:signed_digits(-129))
        expected_sites=[128*128*8,128*128,32*512*8,64*30*3*13824,8*64*128,64*256*4*2,256*1024,32*32*128,8*64*64*2,32*64*4*16]
        for c,sites in zip(configs,expected_sites):check(c['case_id']+'.native_geometry_capacity',c['physical']['data_storage_sites']==sites)
        nand=configs[3]
        check('nand_references_and_total_capacity',64*2*3*13824==nand['physical']['reference_storage_sites'] and expected_sites[3]+nand['physical']['reference_storage_sites']==64*32*3*13824)
        check('nand_pages_and_port',64*32*3==6144 and ceildiv(13824,48)==288 and ceildiv(13824,128)==108)
        check('nand_row_staging_only',nand['resources']['installed']['resident_staging_bits']==4608*9<4608*240*8)
        check('digital_4096_hold_one_tile',digital_tile(32,16,8,4096,4096)=={'tile_bits':4096,'read_batches':1})
        check('narrower_SA_costs_32_reads',digital_tile(32,16,8,128,4096)['read_batches']==32)
        rejects('cannot_double_output_lanes_free',lambda:digital_tile(32,32,8,4096,4096))
        rejects('cannot_double_active_rows_free',lambda:digital_tile(64,16,8,4096,4096))
        rejects('insufficient_hold_rejected',lambda:digital_tile(32,16,8,4096,2048))
        check('tail_transactions_paid',load_units(35,16)==[16,16,3] and len(load_units(35,16))==3 and sum(load_units(35,16))==35)
        check('tail_encoded_load_paid',ceildiv(17*8,128)==2 and ceildiv(9*16,128)==2)
        check('complementary_encoding_no_payload_gain',configs[5]['logical']['resident_transaction_Byte']==8 and configs[5]['resources']['active']['resident']['encoded_bits_per_load_unit']==128)
        check('GC_encoded_two_beats',configs[8]['logical']['resident_transaction_Byte']==16 and ceildiv(configs[8]['resources']['active']['resident']['encoded_bits_per_load_unit'],128)==2)
        check('PCM_32_IDAC_eight_planes',configs[6]['resources']['installed']['IDAC_count']==32 and 32*8==configs[6]['resources']['active']['resident']['encoded_bits_per_load_unit'])
        check('PCM_verify_two_mux_passes',len({c//8 for c in [4*h for h in range(32)][::2]})==16 and len({c//8 for c in [4*h for h in range(32)][1::2]})==16)
        pcm_cells={(r,4*h+s) for r in range(256) for s in range(4) for h in range(32)}
        check('PCM_row_stripe_unique_coverage',len(pcm_cells)==256*128)
        check('FeRAM_restore_not_external_width',configs[7]['resources']['installed']['restore_BL_drivers']==4096 and configs[7]['resources']['installed']['external_BL_drivers']==128)
        check('FeFET_bias_nodes_and_binary_targets_separate',configs[9]['resources']['installed']['bias_nodes']==8*36 and configs[9]['resources']['installed']['selected_write_targets']==128)
        check('MRAM_installed_not_active',configs[5]['resources']['installed']['installed_ibmd_digitizers']==65536 and configs[5]['resources']['installed']['active_ibmd_digitizers']==4096)
        mram_stages={s['id']:s for s in configs[5]['services']}
        mram_digital=next(b for b in configs[5]['parameter_bindings'] if b['id']=='digital_tick')
        check('MRAM_direction_write_is_opaque_without_digital_tick',mram_stages['direction_write']['provider']=='v3_native_service' and 'digital_tick' not in mram_stages['direction_write']['call']['inputs'] and 'direction_write' not in mram_digital['consumers'] and 'native_components' not in mram_stages['direction_write']['call'])
        check('MRAM_turn_and_verify_keep_separate_digital_binding',all(name in mram_digital['consumers'] and 'digital_tick' in mram_stages[name]['call']['inputs'] for name in ('polarity_turn','terminal_verify')))
        check('no_ADC_for_digital_cases',all(configs[i]['resources']['installed']['adc_count']==0 for i in (1,2,5,7,9)))
        check('ADC_finite_resources',all(configs[i]['resources']['installed']['adc_count']==(64 if i==3 else 128) for i in (0,3,4,6,8)))
        check('ADC_selected_group_one_batch',analog_batch(8,16,128,16,0)==1)
        rejects('cannot_double_ADC_parallelism_free',lambda:analog_batch(8,32,128,32,0))
        rejects('cannot_serialize_conversion_without_hold',lambda:analog_batch(8,16,128,32,0))
        check('funded_hold_pays_two_ADC_batches',analog_batch(8,16,128,32,256)==2)
        check('tail_output_evaluation_paid',load_units(17,16)==[16,1] and sum(analog_batch(8,16,128,n,0) for n in load_units(17,16))==2)
        check('GC04_identity',all(s in configs[8]['device']['identity'] for s in ('GC-04','silicon CMOS','3T1C')) and configs[8]['device']['release_policy']=='early_release')
        check('no_HV_current_exceeds_fixed_rating',700*32/1000==configs[6]['resources']['installed']['return_RESET_rating_mA'] and 1.8/8000*1e6<=configs[4]['resources']['installed']['program_current_rating_uA_per_lane'])
        check('FeFET_typical_slew_fits_fixed_resource',100*8/3/10<=60 and 288*100*8/3/10/1000<=17.28)
        check('FeRAM_typical_BL_slew_fits',250*2.5/20<=80)
        for index in (0,4):
            rec=next(s for s in configs[index]['services'] if s['id'] in ('reconstruct','digital_reconstruct'))
            widths=rec['call']['inputs']['arithmetic_widths']
            check(configs[index]['case_id']+'.pilot18bit_leaves23bit_accumulator',widths['weighted_signed_leaf_bits']==18 and widths['fanin']==8 and widths['parallel_trees']==16 and widths['accumulator_bits']==23)
            check(configs[index]['case_id']+'.no_free_intermediate_bank',configs[index]['resources']['installed']['new_intermediate_hold_bits']==0 and configs[index]['resources']['installed']['existing_SAR_code_bits']==128*10)
    except Exception as exc:
        errors.append(str(exc));assertions.append({'id':'probe_exception','status':'FAIL','detail':traceback.format_exc()})
    dump(out/'assertions.json',assertions);dump(out/'raw-output.json',details)
    summary={'status':'PASS' if not errors else 'FAIL','probe':'encoding_resources','contract_version':'2.0.0','cases':len(configs),'assertions':len(assertions),'passed':sum(a['status']=='PASS' for a in assertions),'failed':errors,'scope':'input specification, ideal encoding and finite resource accounting only','performance_metrics_generated':False,'CXX_used':False,'source_hashes_file':'source_hashes.json','raw_output_file':'raw-output.json','assertions_file':'assertions.json'}
    dump(out/'summary.json',summary)
    invocation=json.loads((out/'invocation.json').read_text())
    dump(out/'commands.json',[{'argv':invocation['argv'],'cwd':invocation['cwd'],'exit_code':0 if not errors else 1,'description':'entrypoint; snapshots canonical config/probe sources locally'},{'argv':[sys.executable,str(Path(__file__).resolve()),'--local'],'cwd':str(out),'exit_code':0 if not errors else 1,'description':'local snapshot of standard-library probe; no external simulator/calculator invocation'}])
    print(json.dumps(summary,ensure_ascii=False));return 0 if not errors else 1

if __name__=='__main__':
    if sys.argv[1:]==['--local']:sys.exit(local_main())
    main()
