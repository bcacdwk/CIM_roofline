#!/usr/bin/env python3
"""V5 input validation and API-v1 case service entry."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import sys
sys.dont_write_bytecode = True

CASES = ('pcm', 'mram', 'nor2d', 'fenor3d', 'feram', 'gc04', 'nand3d')
SOURCE_KINDS = ('native_circuit', 'adapter', 'external_primitive', 'service_policy')

def resolve_input(path, scenario):
    source = json.loads(Path(path).read_text())
    required = {'schema_version','case_id','implementation_id','identity','logical','base_parameters','parameter_metadata','scenarios','sources','service_policy','backend_plan'}
    missing = required - source.keys()
    if missing:
        raise ValueError('Missing input fields: ' + ', '.join(sorted(missing)))
    if source['schema_version'] != '5.0.0' or source['case_id'] not in CASES:
        raise ValueError('Unsupported version or case identity')
    def meaningful(value):
        return isinstance(value, (str, list, dict)) and bool(value)
    for section in ('identity', 'service_policy', 'backend_plan'):
        if not isinstance(source[section], dict) or not source[section]:
            raise ValueError('Empty descriptive input section: ' + section)
    if not meaningful(source['implementation_id']):
        raise ValueError('Missing implementation identity')
    policy_keys = ('initial_state','input_port','write_port','output_endpoint','resident_endpoint',
                   'request_overlap','arbitration','retry','maintenance','supply_startup')
    for key in policy_keys:
        if key not in source['service_policy'] or not meaningful(source['service_policy'][key]):
            raise ValueError('Missing explicit service policy: ' + key)
    logical = source['logical']
    if not isinstance(logical.get('signed'), bool) or not meaningful(logical.get('output_qualification')):
        raise ValueError('Missing signed operand and output precision qualification')
    for key in ('K','N','input_bits','weight_bits'):
        value = logical[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError('Invalid logical integer: ' + key)
    for key in ('bytes_per_input','bytes_per_weight'):
        if isinstance(logical[key], bool) or not isinstance(logical[key], (int,float)) or not math.isfinite(logical[key]) or logical[key] <= 0:
            raise ValueError('Invalid logical payload: ' + key)
    base = source['base_parameters']
    metadata = source['parameter_metadata']
    if set(metadata) != set(base):
        raise ValueError('Every authoritative parameter must have exactly one metadata entry')
    for sid, item in source['sources'].items():
        if item['kind'] not in SOURCE_KINDS:
            raise ValueError('Unknown source class: ' + sid)
        for key in ('locator','evidence_type','applicability','exclusions'):
            if not meaningful(item.get(key)):
                raise ValueError('Missing source ' + key + ': ' + sid)
        if not meaningful(item.get('path')) and not meaningful(item.get('url')):
            raise ValueError('Missing source path/URL: ' + sid)
        if item['kind'] == 'external_primitive':
            for key in ('includes','excludes','domain'):
                if not meaningful(item.get(key)):
                    raise ValueError('Missing external primitive coverage/domain: ' + sid + ':' + key)
    selected = source['scenarios'][scenario]
    for key in ('meaning','evidence'):
        if not meaningful(selected.get(key)):
            raise ValueError('Missing scenario ' + key)
    overrides = selected['overrides']
    if set(overrides) - set(base):
        raise ValueError('Undeclared scenario override')
    parameters = dict(base, **overrides)
    for key, value in parameters.items():
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key):
            raise ValueError('Invalid parameter identifier: ' + key)
        if not isinstance(value, (int, float, bool)) or not math.isfinite(value):
            raise ValueError('Only finite numeric/bool parameters accepted: ' + key)
        meta = metadata[key]
        if not meta.get('unit') or not meta.get('source_ids') or not meaningful(meta.get('applicability')) or meta.get('role') not in ('physical_evidence','architecture_choice','external_primitive','operating_condition'):
            raise ValueError('Missing unit/source identity: ' + key)
        if set(meta['source_ids']) - set(source['sources']):
            raise ValueError('Unknown parameter source: ' + key)
        if value < meta.get('min', -math.inf) or value > meta.get('max', math.inf):
            raise ValueError('Parameter outside declared domain: ' + key)
    return {'input':source, 'scenario':scenario, 'resolved_parameters':parameters,
            'config_id':source['implementation_id'] + '__' + scenario,
            'qualification':'input syntax/domain checked only; not circuit/physical validation',
            'input_sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--validate-input', type=Path)
    p.add_argument('--case', choices=CASES)
    p.add_argument('--scenario', default='reference', choices=('reference','optimistic','pessimistic'))
    p.add_argument('--root', type=Path, default=Path(os.environ.get('NEUROSIM_ROOT',str(Path.home()/'neurosim'))))
    p.add_argument('--run-id', required=True)
    a = p.parse_args()
    if not re.fullmatch(r'[A-Za-z0-9_-]+', a.run_id):
        p.error('run-id must contain only letters, digits, underscore or dash')
    def reject_symlink_chain(path):
        for part in (path, *path.parents):
            if part.is_symlink():
                p.error('Runtime path chain contains symlink: ' + str(part))
    root_input = a.root.expanduser().absolute()
    reject_symlink_chain(root_input)
    root = root_input.resolve()
    if any(token in str(root) for token in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):
        p.error('Runtime root must be outside synchronized storage')
    if a.case:
        if a.validate_input:p.error('Use either case service or standalone input validation')
        import service
        return service.run_case(a, Path(__file__).resolve().parent, resolve_input)
    if not a.validate_input:p.error('A case or --validate-input is required')
    resolved = resolve_input(a.validate_input.resolve(), a.scenario)
    out = root/'runs'/'step4-v5'/'p0'/('input-'+a.run_id)
    reject_symlink_chain(out)
    final_out = out.resolve()
    if root not in final_out.parents or any(token in str(final_out) for token in ('/CloudStorage/','/OneDrive','/Dropbox/','/Mobile Documents/')):
        p.error('Unsafe resolved run destination')
    out.mkdir(parents=True, exist_ok=False)
    shutil.copy2(a.validate_input, out/'input.json')
    shutil.copy2(Path(__file__), out/'run.py')
    (out/'input_validation.json').write_text(json.dumps(resolved,ensure_ascii=False,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'status':'input_checked_only','run_directory':str(out),'config_id':resolved['config_id']}))

if __name__ == '__main__':
    main()
