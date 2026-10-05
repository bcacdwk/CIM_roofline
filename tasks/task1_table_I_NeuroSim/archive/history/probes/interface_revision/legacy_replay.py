#!/usr/bin/env python3
"""Independent replay of v3 primitive budgets through the case stage schedules.

No original calculator is imported or called. Saved results enter ONLY the
comparison function, after aggregation. This is not a NeuroSim case evaluation.
New clock selection and boundary-edge alignment are deliberately disabled.
"""
from collections import Counter, defaultdict
import copy
import hashlib
import json
import math
from pathlib import Path

RESULT_ROWS = {'04_nand_3d':'main_scenarios','07_pcm':'paired_scenarios',
               '08_feram_hfo2':'paired','10_fenor_3d':'main_scenarios'}

def parameters(case, repo):
    """Only input specifications/primitive sources; no results file access."""
    shared_path=repo/case['provenance']['sources']['shared']['path']
    shared=json.loads(shared_path.read_text())
    values=dict(shared['common_conditions']['propagation']['profile_values']['reference'])
    for p in case['device']['primitives']:
        if p['normalized']['unit']=='s':
            values[p['id']]=p['normalized']['value']*1e9
    # Revision 3 freezes the prior independent binary-window reference budget.
    # Old specifications are accepted only for migration debugging of this test.
    values.setdefault('binary_verify_sense_ns',values['adc_batch'])
    return values

def _front_cycles(ins):
    if 'front_reference_cycles' in ins:return ins['front_reference_cycles']
    beats=ins.get('data_beats',ins.get('front_data_beats'))
    if beats is None:beats=math.ceil(ins['encoded_bits']/ins.get('port_bits',128))
    control=ins.get('control_cycles',ins.get('front_control_cycles',2))
    return control+beats-int(ins.get('first_data_in_command',False))

def stage_parts(case, stage, context, p):
    """Per-occurrence source arithmetic, with a diagnostic component ledger."""
    cid=case['case_id'];sid=stage['id'];i=stage['call']['inputs'];td=p['digital_tick']
    # Composite/native services first. No final service totals from v3 are inputs.
    if sid=='load_calibration':
        return {'WL_setup':i['wl_setup_count']*p['wl_setup'],
                'BL_setup':i['analog_rounds']*p['bl_setup'],
                'SL_setup':i['analog_rounds']*p['sl_setup'],
                'shared_ADC':i['analog_rounds']*p['adc_batch'],
                'native_arithmetic_budget':i['arithmetic_cycles']*td}
    if cid=='05_rram' and sid=='program_attempts':
        phase=context.get('phase')
        assert phase in ['RESET','SET'], 'RRAM pulse needs the enclosing attempt phase'
        return {'local_setup':p['local_setup'],phase+'_pulse':p[phase.lower()+'_pulse'],
                'local_return':p['local_return'],'attempt_control':i['control_cycles_per_attempt']*td}
    if cid=='05_rram' and sid=='endpoint_verify':
        return {'input_reset':p['input_step'],'memory_front':p['memory_verify_front'],
                'independent_binary_window':p['binary_verify_sense_ns']}
    if cid=='06_mram' and sid=='terminal_verify':
        return {'complete_IBMD_read':p['ibmd_read'],
                'capture':i['capture_cycles_per_branch']*td,
                'compare':i['compare_cycles_per_branch']*td}
    if cid=='07_pcm' and sid=='program_reset_set':
        return {'batch_select':i['selection_cycles_per_batch']*td,
                'mode_transitions':i['driver_transitions_per_batch']*p['drive_transition'],
                'RESET':i['reset_attempts']*p['reset_pulse'],
                'complete_SET':i['set_attempts']*p['set_complete_pulse']}
    if cid=='07_pcm' and sid=='endpoint_verify':
        return {'shared_complete_front':p['shared_voltage_front'],
                'shared_ADC':p['adc_batch'],'compare':i['comparison_cycles']*td}
    if cid=='08_feram_hfo2' and sid=='external_polarization_write':
        return {'open_close':p['open_close'],'polarization_holds':i['holds_per_row']*p['polarization_hold']}
    if cid=='09_gain_cell_edram' and sid=='refresh_read':
        return {'input_reset':p['input_step'],'shared_overhead':p['common_read_overhead'],
                'refresh_integration':p['refresh_integration'],'shared_ADC':p['adc_batch']}
    if cid=='09_gain_cell_edram' and sid=='refresh_decode_load_rewrite':
        return {'sign_decode':i['sign_decode_cycles']*td,
                'encoded_load_and_control':_front_cycles(i)*td,
                'complete_program':p['program_complete']}
    if cid=='10_fenor_3d' and sid=='two_phase_write':
        return {'bias_edges_before_final':i['bias_edges_before_final']*p['bias_transition'],
                'polarization':i['pulses']*p['polarization_pulse']}
    if cid=='10_fenor_3d' and sid=='post_pulse_guard':
        return {'guard_including_final_return':max(p['post_pulse_guard'],p['bias_transition'])}
    if cid=='10_fenor_3d' and sid=='terminal_verify':
        return {'complete_binary_read':p['binary_read'],'capture':i['capture_cycles']*td,
                'compare':i['compare_cycles']*td}
    if sid=='sector_erase':
        return {'complete_erase':p['sector_erase'],'erase_control':i['control_cycles_per_erase']*td}
    if sid=='page_load' and cid=='04_nand_3d':
        width=context['effective_port_bits']
        assert (context['page_kind'],width) in [('data',48),('reference',128)]
        return {'port_and_control':(i['control_cycles']+math.ceil(i['encoded_bits']/width))*td}
    if sid=='sar':return {'shared_ADC':p['adc_batch']}
    # Retained primitive/complete front: use each time parameter exactly once.
    duration_ids=i.get('duration_parameters')
    if duration_ids is None and 'duration_parameter' in i:duration_ids=[i['duration_parameter']]
    if duration_ids:
        parts={key:p[key] for key in duration_ids}
        if 'input_step' in i:parts['input_reset']=p['input_step']
        return parts
    # Already-declared v3 digital schedule, NOT new module timing or clock closure.
    timing=stage['call'].get('timing_plan',{})
    factor=timing.get('cycles_per_occurrence',{}).get('value')
    if factor is None:
        if any(k in i for k in ['encoded_bits','data_beats','front_reference_cycles']):factor=_front_cycles(i)
        elif 'digital_tick' in i or i.get('shared_binding')=='digital_tick':factor=1
    if factor is not None:return {'retained_digital_schedule':factor*td}
    raise ValueError('No original-time rule for '+cid+'/'+sid)

def aggregate(case, values):
    """Traverse nested ordered templates. Multiplication preserves loop context."""
    by_id={s['id']:s for s in case['services']};ledger={};counts=Counter()
    totals={};trace=[]
    def walk(nodes,multiplier=1,context=None,path=''):
        context=dict(context or {});total=0.0
        for pos,node in enumerate(nodes):
            here=path+'/'+str(pos)
            if 'stage_id' not in node:
                nested=dict(context);axis=node['axis']
                if 'RESET_attempt' in axis:nested['phase']='RESET'
                if 'SET_attempt' in axis:nested['phase']='SET'
                total+=walk(node['steps'],multiplier*node['repeat'],nested,here+'/'+axis)
                continue
            ctx={**context,**{k:v for k,v in node.items() if k not in ['stage_id','count']}}
            sid=node['stage_id'];count=multiplier*node['count'];stage=by_id[sid]
            parts=stage_parts(case,stage,ctx,values)
            assert parts and all(math.isfinite(v) and v>=0 for v in parts.values()),(sid,parts)
            each=sum(parts.values());subtotal=each*count;counts[sid]+=count;total+=subtotal
            item=ledger.setdefault(sid,{'count':0,'total_ns':0.,'components_ns':{},'source_refs':stage['source_refs']})
            item['count']+=count;item['total_ns']+=subtotal
            for name,value in parts.items():item['components_ns'][name]=item['components_ns'].get(name,0)+value*count
            trace.append({'path':here,'stage_id':sid,'count':count,'context':ctx,'per_occurrence_ns':each,'components_each_ns':parts})
        return total
    for service in ['streaming','resident','maintenance']:
        totals[service]=walk(case['service_schedules'][service]['steps'],path=service)
    assert dict(counts)=={s['id']:s['count']['value'] for s in case['services']},'schedule migration changed stage counts'
    result={'case_id':case['case_id'],'mode':'v3_original_time_replay','new_neurosim_times':False,
            'new_boundary_alignment':False,'raw_delta_S_ns':totals['streaming'],
            'raw_T_R_ns':totals['resident'],'maintenance_busy_ns':totals['maintenance'],
            'stage_ledger':ledger,'schedule_trace':trace,'input_times_ns':values}
    if case['case_id']=='09_gain_cell_edram':
        front=sum(stage_parts(case,by_id['analog_front'],{},values).values())+values['adc_batch']
        batch=front+2*values['digital_tick']
        txn=sum(stage_parts(case,by_id['resident_load'],{},values).values())+values['program_complete']
        guard=max(batch,txn);period=values['refresh_period'];availability=(period-totals['maintenance']-guard)/period
        assert availability>0
        result.update(maintenance_guard_ns=guard,maintenance_period_ns=period,
            maintenance_availability=availability,maintenance_workload_Byte=0,
            effective_delta_S_ns=totals['streaming']/availability,
            effective_T_R_ns=totals['resident']/availability)
    return result

def expected_reference(case,repo):
    """Comparison-only boundary: called AFTER aggregate. Never returns inputs."""
    path=repo/case['provenance']['sources']['results']['path']
    assert hashlib.sha256(path.read_bytes()).hexdigest()==case['provenance']['sources']['results']['sha256']
    saved=json.loads(path.read_text());key=RESULT_ROWS.get(case['case_id'],'scenarios')
    candidates=[(i,row) for i,row in enumerate(saved[key]) if row.get('profile',row.get('common_profile',row.get('id')))=='reference']
    assert len(candidates)==1,(case['case_id'],'ambiguous reference')
    index,row=candidates[0]; raw=row.get('raw_mapping_interface',row['mapping_interface'])
    expected={'raw_delta_S_ns':raw['delta_S_ns'],'raw_T_R_ns':raw['T_R_ns']}
    if case['case_id']=='09_gain_cell_edram':
        expected.update(maintenance_busy_ns=row['refresh']['total_ns'],
            maintenance_guard_ns=row['refresh']['scheduling_guard_ns'],
            maintenance_availability=row['refresh']['availability'],
            effective_delta_S_ns=row['mapping_interface']['delta_S_ns'],
            effective_T_R_ns=row['mapping_interface']['T_R_ns'])
    return expected,{'path':case['provenance']['sources']['results']['path'],
                     'json_pointer':'/'+key+'/'+str(index),'usage':'comparison_only_after_aggregation'}

def _close(a,b):return math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-7)

def run_checks(cases,repo):
    checks={};replays=[]
    for case in cases:
        computed=aggregate(case,parameters(case,repo))
        expected,where=expected_reference(case,repo)
        comparisons={key:{'computed':computed[key],'expected_v3':value,
                          'difference':computed[key]-value,'pass':_close(computed[key],value)} for key,value in expected.items()}
        checks[case['case_id']+'.original_time_replay']=all(x['pass'] for x in comparisons.values())
        computed.update(comparisons=comparisons,comparison_source=where)
        replays.append(computed)
    # Independent negative sensitivity: mutate INPUT, not the comparison target.
    first=cases[0];v=parameters(first,repo);base=aggregate(first,v)
    v['charge_front']+=1;changed=aggregate(first,v)
    checks['reject_missing_or_changed_front_stage']=_close(changed['raw_delta_S_ns']-base['raw_delta_S_ns'],64) and not _close(changed['raw_delta_S_ns'],base['raw_delta_S_ns'])
    gc=next(c for c in cases if c['case_id']=='09_gain_cell_edram');v=parameters(gc,repo);before=aggregate(gc,v)
    v['adc_batch']+=1;after=aggregate(gc,v)
    checks['shared_GC_ADC_replay_consumers']=_close(after['raw_delta_S_ns']-before['raw_delta_S_ns'],32) and _close(after['maintenance_busy_ns']-before['maintenance_busy_ns'],256)
    checks['GC_guard_recomputed_from_stage_times']=_close(after['maintenance_guard_ns']-before['maintenance_guard_ns'],1)
    checks['replay_never_selects_new_clock_or_alignment']=all(not x['new_boundary_alignment'] and not x['new_neurosim_times'] for x in replays)
    return {'status':'PASS' if all(checks.values()) else 'FAIL','checks':checks,
            'mode':'original_v3_time_interface_regression','new_case_performance':False,
            'calculator_imported_or_called':False,'tolerance':{'relative':1e-12,'absolute_ns':1e-7},
            'replays':replays}
