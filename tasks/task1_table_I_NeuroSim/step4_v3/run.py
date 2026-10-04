#!/usr/bin/env python3
"""Independent V3 runner. No imports or reads from historical task results."""
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
    for optional in ('check.py', 'numeric.py'):
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
    original = (src / 'Param.cpp').read_text()
    modified = original
    for key, value in case.get('constructor_inputs', {}).items():
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
          'constructor_inputs': case.get('constructor_inputs', {}),
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
    row = {'case_id': case['case_id'], 'status': case['status'],
           'backend': case['backend']['branch'], 'backend_sha': case['backend']['sha'],
           'technode_nm': case['process']['technode_nm'], 'roadmap': case['process']['roadmap'],
           'K': k, 'N': n, 'input_bits': 8, 'weight_bits': 8,
           'physical_rows': get('physical_rows'), 'physical_cols': get('physical_cols'),
           'B_S_Byte': k, 'B_R_Byte': k * n,
           'single_latency_ns': latency * 1e9, 'delta_S_ns': delta * 1e9, 'T_R_ns': resident * 1e9,
           'rho_MB_per_s': rho / 1e6, 'tau_MB_per_s': tau / 1e6,
           'RI_star': rho / tau, 'U_star': resident / delta,
           'conditions': case.get('conditions', [])}
    assert math.isclose(row['U_star'], n * row['RI_star'], rel_tol=1e-12)
    return row


def worker(args, own, out, root):
    cases = CASES if args.case == 'all' else (args.case,)
    rows = []
    for cid in cases:
        case = json.loads((own / 'configs' / (cid + '.json')).read_text())
        assert case['case_id'] == cid
        dest = out / cid
        exe = build(case, root, dest, own, args.cxx)
        argv = [str(exe), *map(str, case.get('arguments', []))]
        raw = parse(command(argv, dest, dest / 'main.log'))
        dump(dest / 'input.json', case)
        dump(dest / 'resolved.json', raw)
        row = evaluate(case, raw)
        dump(dest / 'result.json', row)
        runs = [{'label': 'main', 'argv': argv, 'result': 'resolved.json'}]
        diagnostics = {}
        if args.diagnostics:
            for variant in case.get('diagnostics', []):
                label = variant['label']
                argv = [str(exe), *map(str, variant['arguments'])]
                output = parse(command(argv, dest, dest / (label + '.log')))
                diagnostics[label] = {'changes': variant['changes'], 'raw': output}
                runs.append({'label': label, 'argv': argv})
        dump(dest / 'diagnostics.json', diagnostics)
        dump(dest / 'executions.json', runs)
        rows.append(row)
        print(f"{cid}: delta={row['delta_S_ns']:.6g} ns T_R={row['T_R_ns']:.6g} ns [{row['status']}]", flush=True)
    dump(out / 'summary.json', {'schema': 'step4-v3.1', 'case_results': rows})
    fields = [k for k in rows[0] if k != 'conditions']
    with (out / 'summary.csv').open('w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    if (own / 'numeric.py').exists():
        command([sys.executable, '-B', own / 'numeric.py', out], out, out / 'numeric.log')
    if (own / 'check.py').exists():
        command([sys.executable, '-B', own / 'check.py', out], out, out / 'checks.log')
    print(out, flush=True)


def export(out, own):
    target = own / 'results' / out.name
    target.mkdir(parents=True, exist_ok=False)
    allowed = ['summary.json', 'summary.csv', 'snapshot_manifest.json', 'environment.json', 'numeric.json', 'checks.json']
    for cid in CASES:
        allowed += [cid + '/' + name for name in ('input.json', 'resolved.json', 'result.json', 'source_manifest.json', 'diagnostics.json', 'executions.json')]
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
    out = root / 'runs' / 'step4-v3' / args.run_id
    out.mkdir(parents=True, exist_ok=False)
    (out / 'tmp').mkdir()
    local = snapshot(own, out)
    dump(out / 'environment.json', {'root': str(root), 'management_source': str(own),
         'run_dir': str(out), 'python': sys.version, 'compiler': subprocess.check_output([args.cxx, '--version'], text=True).splitlines()[0],
         'created_utc': datetime.now(timezone.utc).isoformat(), 'argv': sys.argv,
         'repository_HEAD': subprocess.run(['git', '-C', str(own), 'rev-parse', 'HEAD'], text=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL).stdout.strip() or None})
    argv = [sys.executable, '-B', str(local / 'run.py'), '--worker', str(out), '--root', str(root), '--case', args.case, '--cxx', args.cxx]
    if args.diagnostics:
        argv.append('--diagnostics')
    result = subprocess.run(argv, cwd=out, env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
    if result.returncode:
        raise SystemExit(result.returncode)
    if args.export:
        export(out, own)


if __name__ == '__main__':
    main()
