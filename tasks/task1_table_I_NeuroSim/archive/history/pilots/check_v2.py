"""Targeted timing/schedule counterexamples, not implementation-mirroring counts."""
import copy, math
import timing

def run(case,plan,model):
    checks={}
    def reject(name,fn):
        try:fn()
        except (AssertionError,ValueError):checks[name]=True
        else:checks[name]=False
    p=copy.deepcopy(model['paths']);w=copy.deepcopy(model['reconstruction_window'])
    minimum=timing.qualify_paths(p,w)
    timing.select_period(p,w,model['actual_period_ns']);checks['chosen_period_meets_all_launch_capture_budgets']=True
    reject('period_below_true_timing_minimum_rejected',lambda:timing.select_period(copy.deepcopy(p),w,minimum*.9))
    if w is not None:
        for source in ['SAR_codes','input_bit','output_group','old_accumulator']:
            bad=copy.deepcopy(w);bad['source_stability'][source]=[1,2]
            reject('late_'+source+'_cannot_borrow_two_cycles',lambda bad=bad:timing.qualify_paths(copy.deepcopy(p),bad))
        bad=copy.deepcopy(w);bad['edge_updates']['1']=['phase_only','input_bit']
        reject('E1_select_update_rejected',lambda:timing.qualify_paths(copy.deepcopy(p),bad))
        bad=copy.deepcopy(w);bad['output_write_edges']=[1,2];bad['capture_enable_at_edge1']=True
        reject('E1_accumulator_capture_rejected',lambda:timing.qualify_paths(copy.deepcopy(p),bad))
        bad=copy.deepcopy(p);en=next(x for x in bad if x['id']=='capture_enable_path');en.update(launch_edge=0,capture_edge=2,available_cycles=2,single_cycle=False,path_class='held_reconstruction_data',stable_sources=['SAR_codes'])
        reject('capture_enable_cannot_be_divided_by_two',lambda:timing.qualify_paths(bad,w))
        bad=copy.deepcopy(p);ctl=next(x for x in bad if x['id']=='control_path');ctl.update(capture_edge=2,available_cycles=2,single_cycle=False,path_class='held_reconstruction_data',stable_sources=['input_bit'])
        reject('ordinary_control_cannot_be_divided_by_two',lambda:timing.qualify_paths(bad,w))
        bad=copy.deepcopy(plan);idx=next(i for i,e in enumerate(bad['streaming']) if e['id'] in ['reconstruct','digital_reconstruct']);bad['streaming'].insert(idx,{'id':'sar','kind':'physical','ns':model['sar_ns'],'resources':['SAR']})
        reject('no_new_conversion_during_held_codes',lambda:timing.validate_plan(bad,model))
        bad=copy.deepcopy(plan);rec=next(e for e in bad['streaming'] if e['id'] in ['reconstruct','digital_reconstruct']);rec['timing_window']['extra_register_bits']=23*16
        reject('undeclared_intermediate_bank_rejected',lambda:timing.validate_plan(bad,model))
        bad=copy.deepcopy(plan);rec=next(e for e in bad['streaming'] if e['id'] in ['reconstruct','digital_reconstruct']);rec['capture_offset_cycles']=[1]
        reject('early_capture_event_rejected',lambda:timing.validate_plan(bad,model))
        if case['case_id']=='01_sram_acim':
            for phase in [1,2]:
                bad=copy.deepcopy(plan);rec=next(e for e in bad['streaming'] if e['id']=='reconstruct' and e['context']['phase']==phase);rec['context']['captures_output']=(phase==1)
                reject('phase%d_capture_context_contradiction_rejected'%phase,lambda bad=bad:timing.validate_plan(bad,model))
        checks['compiled_graph_structural_arithmetic_executed']=model['raw_module_returns']['same_graph_arithmetic_fixtures']>0
    else:checks['DCIM_no_ADC_or_reconstruction_exception']=case['case_id']=='02_sram_dcim' and model['sar_ns'] is None
    assert all(checks.values()),checks
    return {'status':'PASS','checks':checks,'scope':'timing ownership and illegal schedules; old time/finite endpoint/numerical checks remain separate'}
