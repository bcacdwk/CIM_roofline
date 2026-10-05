#!/usr/bin/env python3
"""Independent V4 paired-scenario runner. No imports or reads from historical task results."""
import argparse
import csv
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
sys.dont_write_bytecode = True

CASES = ('ns_sram_acim', 'ns_rram_1t1r', 'ns_sram_dcim')
CODE_DIRS = ('configs', 'src', 'patches')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')


def command(argv, cwd, log):
    (cwd / 'tmp').mkdir(exist_ok=True)
    run = subprocess.run(list(map(str, argv)), cwd=cwd,
                         env=dict(os.environ, TMPDIR=str(cwd / 'tmp'), PYTHONDONTWRITEBYTECODE='1'),
                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log.write_text(run.stdout)
    if run.returncode:
        raise RuntimeError(f'{run.returncode}: {log}')
    return run.stdout


def parse(text):
    result = {}
    for line in text.splitlines():
        if '=' not in line:
            continue
        k, v = line.split('=', 1)
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', k):
            continue
        try:
            value = float(v)
        except ValueError:
            continue
        if not math.isfinite(value):
            raise ValueError(f'Nonfinite output: {k}={v}')
        result[k] = value
    if not result:
        raise ValueError('Empty model output')
    return result


def snapshot(own, out):
    dest = out / 'canonical'
    dest.mkdir()
    files = [own / 'run.py', own / 'INTERFACE.md']
    files += [p for d in CODE_DIRS for p in (own / d).rglob('*') if p.is_file()]
    for optional in ('check.py', 'numeric.py', 'plot.py', 'qualification.py'):
        if (own / optional).exists():
            files.append(own / optional)
    hashes = {}
    for f in sorted(files):
        if f.is_symlink() or f.stat().st_size > 1024 * 1024:
            raise ValueError(f'Invalid canonical source {f}')
        rel = f.relative_to(own)
        target = dest / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target)
        hashes[str(rel)] = digest(f)
    dump(out / 'snapshot_manifest.json', hashes)
    return dest


def build(case, root, dest, own, cxx):
    dest.mkdir()
    src = dest / 'src'
    src.mkdir()
    (dest / 'tmp').mkdir()
    backend = case['backend']
    trees = json.loads((root / 'worktrees.json').read_text())
    tree = Path(trees[backend['branch']]).resolve()
    head = subprocess.check_output(['git', '-C', str(tree), 'rev-parse', 'HEAD'], text=True).strip()
    if head != backend['sha']:
        raise ValueError('Upstream SHA mismatch')
    names = subprocess.check_output(['git', '-C', str(tree), 'ls-tree', '-r', '--name-only', head, backend['core_path']], text=True).splitlines()
    upstream = {}
    for name in names:
        p = Path(name)
        if p.suffix not in ('.cpp', '.h') or str(p.parent) != backend['core_path']:
            continue
        data = subprocess.check_output(['git', '-C', str(tree), 'show', f'{head}:{name}'])
        local = tree / name
        if not local.is_file() or local.read_bytes() != data:
            raise ValueError(f'Missing or modified upstream: {local}')
        (src / p.name).write_bytes(data)
        upstream[p.name] = hashlib.sha256(data).hexdigest()
    params = case['resolved_parameters']
    declarations = []
    for key, value in sorted(params.items()):
        if not re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*', key) or isinstance(value, str):
            raise ValueError('Only named numeric/bool authoritative inputs allowed: ' + key)
        if isinstance(value, bool):
            dtype, literal = 'bool', str(value).lower()
        elif isinstance(value, int):
            dtype, literal = 'int', str(value)
        else:
            if not math.isfinite(value): raise ValueError('Nonfinite input')
            dtype, literal = 'double', format(value, '.17g')
        declarations.append(f'inline constexpr {dtype} {key} = {literal};')
    (src / 'request.h').write_text('#pragma once\nnamespace request {\n'+'\n'.join(declarations)+'\n}\n')
    specialized = dict(case.get('constructor_inputs', {}))
    for key, field in case.get('constructor_bindings', {}).items(): specialized[key] = params[field]
    for key, expression in case.get('constructor_derived', {}).items():
        if set(expression) == {'pow2'}: specialized[key] = 2 ** params[expression['pow2']]
        else: raise ValueError('Unknown constructor expression')
    original = (src / 'Param.cpp').read_text()
    modified = original
    for key, value in specialized.items():
        literal = str(value).lower() if isinstance(value, bool) else str(value)
        modified, n = re.subn(r'(?m)^(\s*' + re.escape(key) + r'\s*=\s*)[^;]+;', lambda m: m[1] + literal + ';', modified, count=1)
        if n != 1:
            raise ValueError(f'Constructor input missing: {key}')
    (src / 'Param.cpp').write_text(modified)
    (dest / 'constructor.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True), modified.splitlines(True), fromfile='a/Param.cpp', tofile='b/Param.cpp')))
    commands = []
    for name in case.get('patches', []):
        argv = ['patch', '-p1', '--batch', '-i', str(own / 'patches' / name)]
        command(argv, src, dest / ('patch-' + Path(name).stem + '.log'))
        commands.append(argv)
    for name in case.get('support_sources', []):
        shutil.copy2(own / 'src' / name, src / Path(name).name)
    shutil.copy2(own / 'src' / case['driver'], src / 'service.cpp')
    exclude = set(case.get('compile_exclude', ['main.cpp']))
    cpp = [str(p) for p in sorted(src.glob('*.cpp')) if p.name not in exclude]
    exe = dest / 'service'
    argv = [cxx, '-std=c++17', '-O2', '-fopenmp', '-Wno-unused-result', '-I', str(src), *cpp, '-o', str(exe)]
    command(argv, dest, dest / 'build.log')
    commands.append(argv)
    dump(dest / 'commands.json', commands)
    dump(dest / 'source_manifest.json', {'backend': backend, 'upstream_files': upstream,
          'constructor_inputs': specialized, 'authoritative_parameters': params, 'request_header_sha256': digest(src / 'request.h'),
          'patched_files': {p.name: digest(p) for p in sorted(src.iterdir()) if p.suffix in ('.cpp', '.h')},
          'executable_sha256': digest(exe), 'compiler_flags': argv[1:5]})
    return exe


def evaluate(case, raw):
    keys = case.get('result_keys', {})
    def get(name):
        return raw[keys.get(name, name)]
    k, n = int(get('logical_K')), int(get('logical_N'))
    latency, delta, resident = get('stream_latency_s'), get('delta_s'), get('resident_s')
    if min(k, n, latency, delta, resident) <= 0 or delta > latency * (1 + 1e-12):
        raise ValueError('Invalid service dimensions/times')
    rho, tau = k / delta, k * n / resident
    row = {'case_id': case['case_id'], 'scenario': case['scenario'], 'paired_id': case['case_id']+'__'+case['scenario'], 'status': case['status'], 'qualification': case['qualification'],
           'backend': case['backend']['branch'], 'backend_sha': case['backend']['sha'],
           'technode_nm': case['resolved_parameters']['technology_nm'], 'temperature_K': case['resolved_parameters']['temperature_K'], 'roadmap': case['process']['roadmap'],
           'K': k, 'N': n, 'input_bits': 8, 'weight_bits': 8,
           'physical_rows': get('physical_rows'), 'physical_cols': get('physical_cols'),
           'B_S_Byte': k, 'B_R_Byte': k * n,
           'single_latency_ns': latency * 1e9, 'delta_S_ns': delta * 1e9, 'T_R_ns': resident * 1e9,
           'rho_MB_per_s': rho / 1e6, 'tau_MB_per_s': tau / 1e6,
           'RI_star': rho / tau, 'U_star': resident / delta,
           'conditions': case.get('conditions', []), 'scope': 'finite paired engineering design scenario; native auto-sizing, not fixed-chip PVT', 'banks': raw.get('banks',1), 'physical_bank_rows': raw.get('bank_rows', get('physical_rows')), 'adc_count': raw.get('total_adc_count',raw.get('resolved_adc_count',0)), 'output_bits': raw.get('output_bits',25), 'fractional_output_bits': raw.get('fractional_output_bits',0)}
    assert math.isclose(row['U_star'], n * row['RI_star'], rel_tol=1e-12)
    return row


def resolved_case(base, scenario, scenarios, overrides=None):
    case = json.loads(json.dumps(base))
    unknown=(set(scenarios[scenario])|set(overrides or {}))-set(case['base_parameters'])
    if unknown: raise ValueError('Undeclared input overrides: '+str(sorted(unknown)))
    p = {**case['base_parameters'], **scenarios[scenario], **(overrides or {})}
    if not 300 <= p['temperature_K'] <= 400 or int(p['temperature_K']) != p['temperature_K']:
        raise ValueError('Temperature outside native integer 300..400 K table')
    if p['logical_K'] != 256 or p['logical_N'] != 31 or p['input_bits'] != 8 or p['weight_bits'] != 8:
        raise ValueError('This reference interface is fixed at 256x31 signed INT8')
    if p['clock_reservation_factor'] < 2:
        raise ValueError('Main/reference digital clock reserves at least half-cycle for capture/control')
    case['resolved_parameters'] = p
    case['scenario'] = scenario
    return case


def execute_case(case, root, dest, own, cxx):
    exe = build(case, root, dest, own, cxx)
    argv = [str(exe)]
    raw = parse(command(argv, dest, dest / 'main.log'))
    consumed = {}
    for key, field in case.get('consumption_checks', {}).items():
        requested, actual = case['resolved_parameters'][key], raw[field]
        ok = math.isclose(requested, actual, rel_tol=1e-12, abs_tol=1e-15)
        consumed[key] = {'requested': requested, 'actual': actual, 'field': field, 'matches': ok}
        if not ok: raise ValueError(f'Input not consumed: {key}: {requested} vs {actual}')
    dump(dest / 'input.json', case)
    dump(dest / 'resolved.json', raw)
    dump(dest / 'consumption.json', consumed)
    dump(dest / 'execution.json', {'argv': argv, 'returncode':0})
    row = evaluate(case, raw)
    dump(dest / 'result.json', row)
    return row


def worker(args, own, out, root):
    cases = CASES if args.case == 'all' else (args.case,)
    spec = json.loads((own / 'configs/scenarios.json').read_text())
    scenarios = spec['scenarios']
    selected = tuple(scenarios) if args.scenario == 'all' else (args.scenario,)
    rows = []
    diagnostic_rows = []
    for cid in cases:
        base = json.loads((own / 'configs' / (cid + '.json')).read_text())
        (out / cid).mkdir()
        for scenario in selected:
            case = resolved_case(base, scenario, scenarios)
            row = execute_case(case, root, out/cid/scenario, own, args.cxx)
            rows.append(row)
            print(f"{cid}/{scenario}: delta={row['delta_S_ns']:.6g} ns T_R={row['T_R_ns']:.6g} ns [{row['status']}]", flush=True)
        if args.diagnostics:
            for variant in base.get('diagnostics', []):
                case = resolved_case(base, variant['scenario'], scenarios, variant['overrides'])
                case['scenario'] = 'diagnostic_' + variant['id']
                case['diagnostic_purpose'] = variant['purpose']
                row = execute_case(case, root, out/cid/case['scenario'], own, args.cxx)
                diagnostic_rows.append(row)
    dump(out / 'summary.json', {'schema':'step4-v4.1','case_results':rows,'scenario_definition':spec})
    dump(out / 'diagnostics.json', {'case_results': diagnostic_rows})
    fields=[k for k in rows[0] if k not in ('conditions','qualification','scope')]
    with (out/'summary.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore');writer.writeheader();writer.writerows(rows)
    envelopes={}
    for cid in cases:
        group=[r for r in rows if r['case_id']==cid]
        envelopes[cid]={}
        for metric in ('delta_S_ns','T_R_ns','rho_MB_per_s','tau_MB_per_s','RI_star','U_star'):
            lo=min(group,key=lambda r:r[metric]);hi=max(group,key=lambda r:r[metric])
            envelopes[cid][metric]={'minimum':lo[metric],'minimum_paired_id':lo['paired_id'],'maximum':hi[metric],'maximum_paired_id':hi['paired_id'],'meaning':'sample extrema only, not mathematical bounds'}
    dump(out/'sample_extrema.json',envelopes)
    for optional in ('numeric.py','check.py','qualification.py'):
        if (own/optional).exists(): command([sys.executable,'-B',own/optional,out],out,out/(optional+'.log'))
    if args.plots and (own/'plot.py').exists():
        command([args.plot_python,'-B',own/'plot.py',out],out,out/'plot.log')
    print(out,flush=True)


def export(out, own):
    target = own / 'results' / out.name
    target.mkdir(parents=True, exist_ok=False)
    allowed = ['summary.json','summary.csv','snapshot_manifest.json','environment.json','diagnostics.json','sample_extrema.json','numeric.json','checks.json','qualification.json']
    for d in sorted(out.glob('ns_*/*')):
        if d.is_dir():
            allowed += [str((d/name).relative_to(out)) for name in ('input.json','resolved.json','result.json','source_manifest.json','consumption.json','execution.json')]
    for name in ('rho_tau_pairs.png','rho_tau_pairs.svg','rho_tau_circles.png','rho_tau_circles.svg','scenario_table.png','scenario_table.svg','plot_points.csv','plot_points.json','geometry.json'):
        allowed.append('figures/'+name)
    manifest = {}
    for rel in allowed:
        f = out / rel
        if not f.exists():
            continue
        if f.is_symlink() or f.stat().st_size > 1024 * 1024:
            raise ValueError('Export not compact: ' + str(f))
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
        manifest[rel] = {'bytes': f.stat().st_size, 'sha256': digest(f)}
    dump(target / 'export_manifest.json', manifest)
    print('Export: ' + str(target))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--case', choices=('all', *CASES), default='all')
    ap.add_argument('--scenario',choices=('all','optimistic','reference','pessimistic'),default='all')
    ap.add_argument('--plots',action='store_true')
    ap.add_argument('--plot-python',default=os.getenv('NEUROSIM_PLOT_PYTHON','/opt/anaconda3/bin/python'))
    ap.add_argument('--root', default=os.getenv('NEUROSIM_ROOT', str(Path.home() / 'neurosim')))
    ap.add_argument('--run-id', default='reference-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    ap.add_argument('--cxx', default=os.getenv('NEUROSIM_CXX', '/opt/homebrew/bin/g++-16'))
    ap.add_argument('--diagnostics', action='store_true')
    ap.add_argument('--export', action='store_true')
    ap.add_argument('--no-export', action='store_false', dest='export')
    ap.add_argument('--worker', help=argparse.SUPPRESS)
    args = ap.parse_args()
    own = Path(__file__).resolve().parent
    root = Path(args.root).expanduser().resolve()
    if any(x in str(root).lower() for x in ('onedrive', 'cloudstorage')) or root == own or own in root.parents:
        raise ValueError('Run root must be outside cloud storage and management directory')
    if args.worker:
        worker(args, own, Path(args.worker).resolve(), root)
        return
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.run_id) or args.run_id in ('.', '..'):
        raise ValueError('Unsafe run id')
    out = root / 'runs' / 'step4-v4' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / 'tmp').mkdir()
    local = snapshot(own, out)
    dump(out / 'environment.json', {'root': str(root), 'management_source': str(own),
         'run_dir': str(out), 'python': sys.version, 'compiler': subprocess.check_output([args.cxx, '--version'], text=True).splitlines()[0],
         'created_utc': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv,
         'repository_HEAD': subprocess.run(['git', '-C', str(own), 'rev-parse', 'HEAD'], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip() or None})
    argv = [sys.executable, '-B', str(local / 'run.py'), '--worker', str(out), '--root', str(root), '--case', args.case, '--scenario',args.scenario,'--cxx', args.cxx,'--plot-python',args.plot_python]
    if args.diagnostics:
        argv.append('--diagnostics')
    if args.plots:
        argv.append('--plots')
    result = subprocess.run(argv, cwd=out, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    if result.returncode:
        raise SystemExit(result.returncode)
    if args.export:
        export(out, own)


if __name__ == '__main__':
    main()
