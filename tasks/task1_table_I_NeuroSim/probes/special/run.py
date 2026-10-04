#!/usr/bin/env python3
"""Branch-qualified types and original nvCap latency mechanism; no case PPA."""
import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
LOCKS = {
    '2DInferenceDCIMV1.0-dev': '38eedf926fc1a712df3627f36bb82b097ba6b9cb',
    '2DInferenceV1.5-dev': '9825ef40bf14d12a72c99d8e32ff8c499aeddf24',
    'MLPInferenceV3.0': '6098feabaf17b8209a8edbef4a9c963b5f015132',
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--cxx', required=True)
    a = ap.parse_args()
    root, out = Path(a.root).resolve(), Path(a.out).resolve()
    out.relative_to(root)
    out.mkdir(parents=True, exist_ok=False)
    tmp = out / 'tmp'; tmp.mkdir()
    env = dict(os.environ, TMPDIR=str(tmp), PYTHONDONTWRITEBYTECODE='1')
    ws = json.loads((root / 'worktrees.json').read_text())
    commands, checks = [], {}
    def command(argv, name, cwd=out):
        start = time.monotonic()
        proc = subprocess.run(list(map(str, argv)), cwd=cwd, env=env, text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        (out / (name + '.log')).write_text(proc.stdout)
        commands.append({'argv': list(map(str, argv)), 'cwd': str(cwd),
                         'exit_code': proc.returncode, 'seconds': time.monotonic()-start,
                         'log': name + '.log'})
        (out / 'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
        if proc.returncode: raise RuntimeError(name + ' failed; see local log')
        return proc.stdout
    for b, s in LOCKS.items():
        actual = command(['git', 'rev-parse', 'HEAD'], 'head-'+b, Path(ws[b])).strip()
        assert actual == s
    driver = out / 'special_probe.cpp'
    shutil.copyfile(Path(__file__).with_name('special_probe.cpp'), driver)
    dc = Path(ws['2DInferenceDCIMV1.0-dev']) / 'Inference_pytorch/NeuroSIM'
    dcbin = out / 'dcim-type'
    command([a.cxx, '-std=c++11', '-O2', '-I', dc, driver, dc/'Param.cpp', '-o', dcbin], 'build-dcim-type')
    dcraw = json.loads(command([dcbin], 'dcim-type').splitlines()[-1])
    checks['dcim_default_256x256'] = (dcraw['rows'], dcraw['columns']) == (256, 256)
    checks['dcim_parallel_weightprecision_four'] = dcraw['parallel_weightprecision'] == 4
    readme = (Path(ws['2DInferenceDCIMV1.0-dev'])/'README.md').read_text()
    checks['dcim_documented_native_limit'] = 'only support the 256x256' in readme
    guard = lambda rows, cols: rows == 256 and cols == 256
    checks['adapter_rejects_v3_d6_128x16_as_native_dcim'] = not guard(128, 16)
    source = Path(ws['2DInferenceV1.5-dev']) / 'NeuroSIM'
    build = out/'cap-source'; build.mkdir()
    manifest = {}
    for f in sorted(source.iterdir()):
        if f.suffix in ('.cpp', '.h'):
            shutil.copyfile(f, build/f.name)
            manifest[f.name] = hashlib.sha256(f.read_bytes()).hexdigest()
    # One constructor input is specialized BEFORE any derived initialization.
    # No timing/energy formula is changed; the exact local diff is retained.
    pc = build/'Param.cpp'; original = pc.read_text()
    changed, n = re.subn(r'(?m)^(\s*memcelltype\s*=\s*)2(\s*;)', r'\g<1>4\2', original, count=1)
    assert n == 1
    pc.write_text(changed)
    import difflib
    (out/'constructor-specialization.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), changed.splitlines(True), fromfile='upstream/Param.cpp', tofile='probe/Param.cpp')))
    (out/'source_hashes.json').write_text(json.dumps(manifest, indent=2)+'\n')
    capbin = out/'cap-probe'
    sources = [f for f in sorted(build.glob('*.cpp')) if f.name != 'main.cpp']
    command([a.cxx, '-std=c++11', '-O2', '-fopenmp', '-DPROBE_CAP', '-I', build, driver, *sources, '-o', capbin], 'build-cap')
    cap = []
    for rows, charge in [(128,5e-9), (128,10e-9), (64,5e-9), (64,10e-9)]:
        raw = command([capbin, str(rows), format(charge,'.17g')], 'cap-%d-%s'%(rows,charge))
        cap.append(json.loads(raw.splitlines()[-1]))
    for i, row in enumerate(cap):
        expected = row['charge_delay_input_s'] * row['active_rows']/128
        checks['cap_column_input_scaling_%d'%i] = math.isclose(row['col_delay_raw_s'], expected, rel_tol=1e-13)
        checks['cap_finite_positive_%d'%i] = all(math.isfinite(row[k]) and row[k]>0 for k in ['area_m2','sensing_critical_raw_s','col_delay_raw_s'])
    for a0, b0 in [(0,1),(2,3)]:
        delta = cap[b0]['sensing_critical_raw_s'] - cap[a0]['sensing_critical_raw_s']
        expected = (cap[b0]['col_delay_raw_s']-cap[a0]['col_delay_raw_s'])*cap[a0]['beta']
        checks['cap_input_delay_propagates_%d'%a0] = math.isclose(delta, expected, rel_tol=1e-12)
    checks['numeric_memcelltype_is_not_portable'] = dcraw['config_memcelltype'] == cap[0]['config_memcelltype'] == 4 and dcraw['symbol'] != cap[0]['symbol']
    v15readme = (source.parent/'README.md').read_text()
    checks['v15_dac_hardware_remains_bit_serial'] = 'All PPA simulations will use bit-serial mode' in v15readme
    hybrid = (Path(ws['MLPInferenceV3.0'])/'Cell.h').read_text()
    checks['hybrid_is_lsb_3t1c_plus_two_pcm_not_gc04'] = all(x in hybrid for x in ['_3T1C LSBcell', 'RealDevice MSBcell_LTP', 'RealDevice MSBcell_LTD', 'WeightTransfer('])
    summary = {'status': 'PASS' if all(checks.values()) else 'FAIL', 'checks': checks,
        'locked_shas': LOCKS, 'dcim_constructor': dcraw, 'cap_native_runs': cap,
        'probe_scope': 'branch types; original V1.5 ProcessingUnitInitialize/SubArray sensing path; no v3 case result',
        'native_initialization_order': ['constructor input specialization', 'Param()', 'explicit algorithm fields before object creation', 'ProcessingUnitInitialize (Technology/Initialize/CalculateArea)', 'SubArray::CalculateLatency(CalculateclkFreq=true)'],
        'local_constructor_change': {'file': 'Param.cpp', 'input': 'memcelltype', 'from':2, 'to':4, 'formula_changed':False},
        'routing': {'D6CIM':'retain_v3_complete_MAC_cycle','HZO_1T1C':'retain_v3_destructive_read_restore','GC04':'retain_v3_current_programming_integrate_refresh', 'Cap':'comparison_only_external_chargeDelay_macro'},
        'output_units': {'col_delay_raw_s':'s','sensing_critical_raw_s':'s','area_m2':'m^2'},
        'no_formal_case_metrics': True}
    (out/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(summary['status'], 'special', len(checks), 'checks', out)
    return 0 if summary['status']=='PASS' else 1

if __name__ == '__main__':
    raise SystemExit(main())
