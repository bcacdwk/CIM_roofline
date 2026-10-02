#!/usr/bin/env python3
"""Recompute the FFN stage-boundary records; default compares, --emit writes."""
import sys
sys.dont_write_bytecode = True
import argparse
import csv
import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASK = ROOT.parents[1]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(TASK / "scripts"))
from format_results import ri_decimal, count_label
COMMON = ROOT.parent / '04_crosscheck'
WORKLOAD = 'ffn_or_moe'


def read(path):
    return json.loads(path.read_text())


def exact(value):
    f = Fraction(value)
    return f.numerator if f.denominator == 1 else {'numerator': f.numerator, 'denominator': f.denominator}


def fraction_text(value):
    return str(value) if isinstance(value, int) else f"{value['numerator']}/{value['denominator']}"


def tex_fraction(value):
    return ri_decimal(value, tex=True)


def json_text(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + '\n'


def source(path, locator):
    return {'path': path, 'sha256': hashlib.sha256((TASK / path).read_bytes()).hexdigest(), 'locator': locator}


def create_config():
    conventions = read(COMMON / 'data/conventions.json')
    supplied = read(COMMON / 'data/model_inputs.json')['models']
    registry = {m['id']: m for m in read(TASK / 'data/models.json')['models']}
    source_registry = {s['id']: s for s in read(TASK / 'data/sources.json')}
    sources = [source(p, loc) for p, loc in [
        ('scripts/format_results.py', 'display-only decimal rounding and K/M labels'),
        ('table_IIa/README.md', '一次权重装载与实际服务向量 U'),
        ('table_IIa/tex/table_IIa.tex', 'RI=U/N 与等宽 1 Byte/element'),
        ('table_IIa/data/config.json', 'complete_weight_loads / U_definition / element_bytes'),
        ('table_IIb/04_crosscheck/CONTRACT.zh.md', 'FFN／MoE；共同边界、字段与正文顺序'),
        ('table_IIb/04_crosscheck/data/conventions.json', '共同 schema 与 FFN sweep'),
        ('table_IIb/04_crosscheck/data/model_inputs.json', '六模型 FFN 原生参数与固定层'),
        ('table_IIb/04_crosscheck/template/preamble.tex', '共同字体、字号、页边与表格样式'),
        ('table_IIb/04_crosscheck/template/report.zh.tex', '四节正文骨架'),
        ('data/models.json', 'models[*].identity / ffn / local_material'),
        ('data/sources.json', '原始来源 URL、revision 与 SHA-256'),
        ('../archived/task2_table_IIb_previous/02_ffn_moe/data/results.json', 'cases[*].result.operator / parts[*].operator / valid_resident_bytes，仅作回归')
    ]]
    models = []
    for m in supplied:
        native = registry[m['model_id']]
        loc = m['local_material']
        ev = [e for e in native['ffn']['evidence'] if 'intermediate_size' in e['locator'] or 'modeling_' in e['source_id']]
        config_source_id = next(s['id'] for s in source_registry.values() if s['local_path'] == loc['raw_config'])
        raw_prefix = 'text_config.' if 'text_config' in read(TASK / loc['raw_config']) else ''
        ev.insert(0, {'source_id': config_source_id, 'locator': raw_prefix + 'hidden_size'})
        relevant = {e['source_id'] for e in ev}
        for sid in sorted(relevant):
            rec = source_registry[sid]
            sources.append(source(rec['local_path'], '; '.join(e['locator'] for e in ev if e['source_id'] == sid)))
        sources.append(source(loc['structure_card'], '身份与选择；所选 FFN／单专家三矩阵'))
        sources.append(source(loc['raw_model_card'], '固定 checkpoint 的身份与结构说明'))
        config_impl = source_registry[loc['configuration_implementation_source_id']]
        sources.append(source(config_impl['local_path'], '所选 FFN 层型与配置字段定义'))
        models.append({
            'model_id': m['model_id'], 'display_name': m['display_name'],
            'model_revision': m['model_revision'], 'selected_layer': m['selected_layer'],
            'parameters': {'D': m['D'], 'F': m['F']},
            'context_notes': [m['ffn_kind'],
                              '原生存储：FP8 E4M3 mixed；默认浮点类型 BF16' if m['model_id'] == 'mimo_v25_pro' else '原生存储：BF16',
                              '原生存储类型仅作来源记录；计数统一为 1 Byte/element',
                              'implementation_revision=' + source_registry[loc['implementation_source_id']]['revision']],
            'source_paths': [loc['raw_config'], loc['structure_card'], loc['raw_model_card'],
                             loc['implementation'], config_impl['local_path']],
        })
    return {
        'schema_version': conventions['schema_version'], 'reference_id': conventions['reference_id'],
        'boundary': conventions['boundary'], 'element_bytes': conventions['element_bytes'],
        'model_order': conventions['model_order'], 'sweeps': {WORKLOAD: conventions['sweeps'][WORKLOAD]},
        'window_rules': {WORKLOAD: {
            'initial_state': '所选 Dense FFN 或一个路由专家的权重为空，初始有效容量为 0',
            'resident_write_rule': 'gate/up/down 三矩阵各完整装载一次，末态有效容量为 3DF Byte；不乘 top-k、专家数或层数',
            'streaming_input_rule': 'gate/up 在同一阶段共用 x，计 UD；down 的新输入 z 另计 UF；当前输出不直接计入 Q_S',
        }},
        'models': models, 'sources': sources,
    }


def create_results(config):
    cases = []
    for m in config['models']:
        D, F = m['parameters']['D'], m['parameters']['F']
        for U in config['sweeps'][WORKLOAD]['U']:
            components = []
            for role in ('gate', 'up', 'down'):
                N, K = (D, F) if role == 'down' else (F, D)
                components.append({
                    'id': role, 'shape_N_K': [N, K], 'state_copies': 1,
                    'input_role': 'x' if role != 'down' else 'z',
                    'Q_S': U * K, 'Q_R': N * K, 'RI': exact(Fraction(U, N)),
                    'resident_bytes_initial': 0, 'resident_bytes_final': N * K,
                })
            cases.append({
                'case_id': f"{m['model_id']}/{WORKLOAD}/{U}",
                'model_id': m['model_id'], 'model_revision': m['model_revision'],
                'selected_layer': m['selected_layer'], 'workload': WORKLOAD,
                'kind': 'finite', 'U': U, 'L': None,
                'parameters': {'D': D, 'F': F},
                'window': config['window_rules'][WORKLOAD].copy(),
                'result': {
                    'Q_S': U * (D + F), 'Q_R': 3 * D * F,
                    'RI': exact(Fraction(U * (D + F), 3 * D * F)),
                    'resident_bytes_initial': 0, 'resident_bytes_final': 3 * D * F,
                    'shared_input_bytes_removed': U * D,
                },
                'components': components,
            })
    return {k: config[k] for k in ('schema_version', 'reference_id', 'boundary', 'model_order')} | {'workload_ids': [WORKLOAD], 'cases': cases}


def create_csv(results):
    fields = read(COMMON / 'data/conventions.json')['csv_columns']
    stream = io.StringIO(newline='')
    writer = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
    writer.writeheader()
    for c in results['cases']:
        base = {k: c[k] for k in fields if k in c}
        for role, r in [('total', c['result'])] + [(p['id'], p) for p in c['components']]:
            row = base | {'component': role, 'Q_S_Byte': r['Q_S'], 'Q_R_Byte': r['Q_R'],
                          'RI_exact': fraction_text(r['RI']), 'resident_initial_Byte': r['resident_bytes_initial'],
                          'resident_final_Byte': r['resident_bytes_final']}
            if role == 'total':
                row['shared_input_removed_Byte'] = r['shared_input_bytes_removed']
            else:
                row.update(N=r['shape_N_K'][0], K=r['shape_N_K'][1], state_copies=r['state_copies'])
            writer.writerow(row)
    return stream.getvalue()


def create_tables(config, results):
    models = [r'\ModelTableSetup', r'\begin{tabularx}{\linewidth}{@{}p{0.32\linewidth}*{4}{>{\centering\arraybackslash}X}@{}}', r'\toprule',
              r'模型 & 所选对象 & 层号 & $D$ & $F$ \\', r'\midrule']
    rows = [r'\ResultTableSetup', r'\begin{tabularx}{\linewidth}{@{}p{0.32\linewidth}*{5}{>{\centering\arraybackslash}X}@{}}', r'\toprule',
            r'模型 & $U=1$ & $U=16$ & $U=128$ & $U=1\mathrm{K}$ & $U=16\mathrm{K}$ \\', r'\midrule']
    for m in config['models']:
        kind = 'Dense FFN' if m['context_notes'][0] == 'dense_swiglu' else '单路由专家'
        models.append(f"{m['display_name']} & {kind} & {m['selected_layer']} & {m['parameters']['D']} & {m['parameters']['F']} " + r'\\')
        vals = [tex_fraction(c['result']['RI']) for c in results['cases'] if c['model_id'] == m['model_id']]
        rows.append(m['display_name'] + ' & ' + ' & '.join('$' + v + '$' for v in vals) + r' \\')
    models += [r'\bottomrule', r'\end{tabularx}']
    rows += [r'\bottomrule', r'\end{tabularx}']
    return '\n'.join(models) + '\n', '\n'.join(rows) + '\n'


def create_preview(config, results):
    lines = ['# FFN／MoE 中文预览', '', '正文顺序与 PDF 一致；六模型、30 个有限工况。', '',
             '## 对象与公式', '',
             '每个窗口取一个 Dense FFN 或一个路由专家，gate/up/down 三矩阵完整装载一次，实际服务 U=1、16、128、1K、16K 个向量。所有计数角色取 1 Byte/element。', '',
             '`W_gate,W_up: F×D；W_down: D×F；X: U×D；Z=SiLU(XW_gateᵀ)⊙(XW_upᵀ)；Y=ZW_downᵀ`。', '',
             '矩阵阶段入口计数：gate/up 共用 X，只计 UD；down 接收新输入 Z，另计 UF。分项独立输入为 UD、UD、UF，汇总扣除 UD。', '',
             '**Q_S=U(D+F)，Q_R=3DF，RI=U(D+F)/(3DF)。** 窗口初始有效权重容量为 0，末态为 3DF Byte。U 是所选对象实际接收的向量数；不乘 top-k、专家总数、共享专家或层数。', '',
             '## 模型信息', '', '| 模型 | 所选对象 | 层号（零起点） | D | F |', '|---|---|---:|---:|---:|']
    for m in config['models']:
        kind = 'Dense FFN' if m['context_notes'][0] == 'dense_swiglu' else '单路由专家'
        lines.append(f"| {m['display_name']} | {kind} | {m['selected_layer']} | {m['parameters']['D']} | {m['parameters']['F']} |")
    lines += ['', '## 代入结果', '', '下表为小数 RI；1K=1024。RI≥1 保留一位小数，RI<1 保留三位有效数字。', '', '| 模型 | U=1 | U=16 | U=128 | U=1K | U=16K |', '|---|---:|---:|---:|---:|---:|']
    for m in config['models']:
        vals = [ri_decimal(c['result']['RI']) for c in results['cases'] if c['model_id'] == m['model_id']]
        lines.append('| ' + m['display_name'] + ' | ' + ' | '.join(vals) + ' |')
    lines += ['', '例：Qwen3.5-2B 在 U=1K 时，Q_S=1024×(2048+6144)=8,388,608 Byte，Q_R=3×2048×6144=37,748,736 Byte，RI≈0.222。', '',
              '## 结果说明', '',
              '同一模型的 Q_R 和末态有效权重容量固定，Q_S 与 RI 随 U 线性增长。U 是一次装载后累计服务的向量数（reuse count），包含首次使用；可跨 batch/请求累计。', '',
              '固定 U 时，RI=(U/3)(1/D+1/F)。本表的 Qwen3.6 单专家以 F=512 获得最高 RI，Ministral 的 D、F 组合对应最低 RI；模型名中的总参数标签不进入公式。', '',
              'Qwen3.5 与 MiMo 的 D、F 互换，D+F 与 DF 均相同，故 Q_S、Q_R、RI 和末态有效容量相同。二者的分项输入及共享扣除量不同；汇总相同符合本计数边界。', '',
              '专家的装载／替换策略可能改变 U；本表不从模型尺寸断言实际替换频率。固定来源、精确字节与独立复算见 [README](README.md) 及 [data](data/)。']
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--emit', action='store_true')
    args = parser.parse_args()
    config = create_config()
    results = create_results(config)
    models_tex, results_tex = create_tables(config, results)
    outputs = {'data/config.json': json_text(config), 'data/results.json': json_text(results),
               'data/results.csv': create_csv(results), 'tex/models.generated.tex': models_tex,
               'tex/results.generated.tex': results_tex, 'PREVIEW.zh.md': create_preview(config, results)}
    for rel, contents in outputs.items():
        path = ROOT / rel
        if args.emit:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(contents)
        elif not path.exists() or path.read_text() != contents:
            raise SystemExit(f'STALE: {rel}; run generate.py --emit')
    print(f"PASS: {'wrote' if args.emit else 'verified'} {len(outputs)} files; 30 finite cases, 90 components")


if __name__ == '__main__':
    main()
