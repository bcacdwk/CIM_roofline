"""Apply sourced native-service scenarios to the same immutable case topology."""
import copy,hashlib,json,math
from pathlib import Path
SCENARIOS=['optimistic','reference','pessimistic']
FACTORS={'ns':1e-9,'us':1e-6,'ms':1e-3}
def apply(config_path,scenario):
    config_path=Path(config_path);case=json.loads(config_path.read_text());spec_path=config_path.with_name('scenarios.json');spec=json.loads(spec_path.read_text())
    assert spec['case_id']==case['case_id'] and scenario in SCENARIOS
    assert hashlib.sha256(config_path.read_bytes()).hexdigest()==spec['reference_input_sha256'],'scenario input no longer matches its reference case'
    primitives={p['id']:p for p in case['device']['primitives']};applied={}
    for row in spec['parameters']:
        name=row['parameter'];source=row['values'][scenario];ref=row['values']['reference'];p=primitives[name]
        assert p['normalized']['unit']=='s'
        assert math.isclose(p['normalized']['value'],ref['value']*FACTORS[ref['unit']],rel_tol=1e-12,abs_tol=0.)
        # Keep original reference bits; avoid re-serializing through nominal decimal units.
        if scenario!='reference':p['normalized']['value']=source['value']*FACTORS[source['unit']]
        applied[name]={'value_ns':p['normalized']['value']*1e9,'source_value':source['value'],'source_unit':source['unit'],'json_pointer':source['source_pointer'],'source_file_sha256':spec['source']['sha256'],'evidence_kind':row['evidence_kind'],'consumers':row['consumers']}
    metadata={'id':scenario,'input_file_sha256':hashlib.sha256(spec_path.read_bytes()).hexdigest(),'parameters':applied,'conditions':spec['conditions'],'excluded_candidates':spec['excluded_candidates']}
    return case,metadata

def validate_bindings(case,p,b,metadata):
    primitives={x['id']:x for x in case['device']['primitives']}
    for name,x in metadata['parameters'].items():
        assert p[name]==x['value_ns']==primitives[name]['normalized']['value']*1e9,(name,'adapter primitive mismatch')
    if 'native_device' in b:assert b['native_device']==case['device'], 'backend bound stale native device'
    native_leads={}
    # The backend names this audit according to the selected implementation interface.
    for value in b.values():
        if isinstance(value,dict) and 'available_native_lead_ns' in value:
            key=value['lead_source_parameter'];assert value['available_native_lead_ns']==p[key]
            native_leads[key]={'adapter_ns':p[key],'backend_native_lead_ns':value['available_native_lead_ns'],'backend_pin_settle_ns':value['settle_to_existing_combinational_pins_ns']}
            assert value['settle_to_existing_combinational_pins_ns']<=p[key]+1e-10
    return {'status':'PASS','same_scenario_case_supplied_to_backend_and_adapter':True,'native_lead_binding':native_leads,'parameter_values_ns':{k:v['value_ns'] for k,v in metadata['parameters'].items()},'resource_mapping_schedule_changed':False}
