"""Step3 execution extension 2.0: explicit launch/capture and operating policy.

The frozen 3.0.0 input/output schema stays in use; these additional fields are
validated here rather than silently treating every path as a one-cycle path.
"""
import math
EXECUTION_VERSION='2.0.0'
DATA_SOURCES=('SAR_codes','input_bit','output_group','old_accumulator')
MULTICYCLE_PATHS={'reconstruct_path','bank_feedback_path','control_select_path'}

def reconstruction_window():
    return {'launch_edge':0,'capture_edge':2,'source_stability':{k:[0,2] for k in DATA_SOURCES},
            'edge_updates':{'0':['reconstruction_active'],'1':['phase_only'],'2':['selected_output_accumulator','next_batch_control']},
            'intermediate_capture':False,'extra_register_bits':0,'overlap':False,
            'phase_enable_launch_edge':1,'phase_enable_capture_edge':2,
            'capture_enable_at_edge1':False,'output_write_edges':[2],
            'hold_rule':'sources remain stable through E2 setup/hold; E2 updates affect next batch only; no combinational restart at E1',
            'implementation':'existing phase/controller bits; clock enable on existing output bank, no extra data register'}

def validate_window(window):
    assert window['launch_edge']==0 and window['capture_edge']==2
    assert window['phase_enable_launch_edge']==1 and window['phase_enable_capture_edge']==2
    assert window['intermediate_capture'] is False and window['extra_register_bits']==0
    assert window['overlap'] is False and window['capture_enable_at_edge1'] is False
    assert window['output_write_edges']==[2]
    assert window['edge_updates']['1']==['phase_only'], 'late data/select update destroys two-cycle window'
    for key in DATA_SOURCES:assert window['source_stability'][key]==[0,2],(key,'source not held')

def qualify_paths(paths,window=None):
    if window is not None:validate_window(window)
    minimum=0.
    for path in paths:
        assert path['constraint_clock_id']=='lv_core' and path['complete_serial_path']
        d=path['delay_ns'];assert math.isfinite(d) and d>0
        a=path['launch_edge'];b=path['capture_edge'];assert isinstance(a,int) and isinstance(b,int) and 0<=a<b
        cycles=b-a;assert path['single_cycle']==(cycles==1)
        assert path['available_cycles']==cycles and path['start_register'] and path['end_register']
        if cycles==2:
            assert window is not None and (a,b)==(0,2)
            assert path['id'] in MULTICYCLE_PATHS, 'unjustified multicycle exception'
            assert path['path_class']=='held_reconstruction_data'
            assert path['stable_sources'] and set(path['stable_sources'])<=set(DATA_SOURCES)
            for key in path['stable_sources']:assert window['source_stability'][key]==[0,2]
        else:
            assert cycles==1 and path['path_class']=='single_cycle_control_or_io'
        if path['id']=='capture_enable_path':assert (a,b)==(1,2),'enable cannot borrow prior cycle'
        path['required_period_ns']=d/cycles
        minimum=max(minimum,d/cycles)
    assert paths
    if window is not None:assert any(p['id']=='capture_enable_path' for p in paths)
    return minimum

def select_period(paths,window=None,requested=None,target=5.):
    minimum=qualify_paths(paths,window);floor=max(target,minimum)
    period=floor if requested is None else requested
    assert math.isfinite(period) and period>0
    assert period+1e-10>=minimum, 'illegal operating period below timing minimum'
    assert period+1e-10>=target, 'operating policy does not exceed target frequency'
    return {'timing_min_period_ns':minimum,'policy_min_period_ns':floor,
            'actual_period_ns':period,'target_period_ns':target,
            'selection_policy':'timing_floor' if requested is None else 'explicit_fixed_legal_period',
            'path_slack_ns':{p['id']:(p['capture_edge']-p['launch_edge'])*period-p['delay_ns'] for p in paths}}

def validate_plan(plan,model):
    window=model.get('reconstruction_window')
    if window is None:return
    validate_window(window);active=None;completed=0
    for e in plan['streaming']:
        if e['id']=='sar':
            assert active is None,'new conversion before prior accumulator capture'
            active={'context':{k:e.get('context',{}).get(k) for k in ['input_bit','row_group','output_group']},'cycles':0}
        if e['id'] in ['reconstruct','digital_reconstruct']:
            assert active is not None
            context={k:e.get('context',{}).get(k) for k in ['input_bit','row_group','output_group']}
            assert active['context']==context,'data/control selection changed during hold'
            assert e.get('timing_window')==window,'missing actual launch/capture annotation'
            assert not e.get('overlap',False)
            assert e['cycles']>0 and e['resources']
            assert e['launch_offset_cycle']==active['cycles'], 'phase launch does not match held interval'
            ending=active['cycles']+e['cycles']
            assert e['capture_offset_cycles']==([2] if ending==2 else []), 'early or missing accumulator capture'
            if 'captures_output' in e.get('context',{}):assert e['context']['captures_output']==(ending==2), 'capture context contradicts launch/capture schedule'
            assert any('SAR' in r or 'adc_count' in r for r in e['resources']),'unowned SAR result hold'
            active['cycles']+=e['cycles'];assert active['cycles']<=2
            if active['cycles']==2:completed+=1;active=None
        elif active is not None and e['id']!='sar':raise AssertionError('intervening operation inside reconstruction window')
    assert active is None and completed in [64,128]
