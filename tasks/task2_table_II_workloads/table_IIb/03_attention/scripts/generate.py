#!/usr/bin/env python3
"""Exact native-dimension closed forms; --emit is the only write mode."""
import argparse
import csv
import hashlib
import io
import json
import sys
from fractions import Fraction
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parents[1]
TASK = HERE.parents[1]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(TASK / "scripts"))
from format_results import ri_decimal, count_label
COMMON = HERE.parent / "04_crosscheck"
WORKLOADS = ["attention_prefill", "attention_decode"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def exact(value):
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else {
        "numerator": value.numerator, "denominator": value.denominator}


def fraction(value):
    return Fraction(value["numerator"], value["denominator"]) if isinstance(value, dict) else Fraction(value)


def compact(value):
    return str(fraction(value))


def tex_exact(value):
    return ri_decimal(value, tex=True)


def dump(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def parameters(model):
    return {**{key: model[key] for key in ("H_q", "H_kv", "d_QK", "d_V")},
            "g": model["H_q"] // model["H_kv"]}


def window_rules():
    return {
        "attention_prefill": {
            "initial_state": "单序列、所选完整因果 GQA 层，初始 KV 为空。",
            "resident_write_rule": "由空状态建到 L；每个 KV head 的每个 K/V 元素仅写入一次。",
            "streaming_input_rule": "对因果前缀 i=1..L，分别计 QK 的 d_QK 维 query 与 AV 的 i 维系数；各 query head 分别计入。",
        },
        "attention_decode": {
            "initial_state": "单序列、所选完整因果 GQA 层，已有 L-1 个 token 的 KV。",
            "resident_write_rule": "每个 KV head 追加一个 token 的 K/V；最终可见长度 L。",
            "streaming_input_rule": "各 query head 分别计本次 QK 的 d_QK 维 query 与 AV 的 L 维系数。",
        },
    }


def context_notes(model, native_model):
    notes = [
        "零起点所选层为完整/global 因果 GQA；单序列，每个 KV head 一份唯一逻辑 K/V。",
        f"固定配置 max_position_embeddings={model['context']['config_max_position_embeddings']}。",
        f"原生声明 dtype={native_model['precision']['checkpoint_declared_dtype']}；本表所有计量角色统一为 1 Byte/element。",
    ]
    if model["model_id"] == "ling_1t":
        notes.append("L=65536（64K）沿用既定的官方 YaRN 条件：factor=4、original_max_position_embeddings=32768、type=yarn，并设 --max-model-len 131072；原始配置保持不变。")
    elif model["model_id"] == "ministral3_8b_2512":
        notes.append("沿用固定配置内 YaRN factor=16、original=16384 及 llama_4_scaling_beta=0.1 的位置相关 query 缩放。")
    elif model["model_id"] == "mimo_v25_pro":
        notes.append("原生 d_QK=192、d_V=128；Value 在 KV 写入前乘 0.612，不改变元素数；所选 global 层无 attention sink。原生产物为 FP8 E4M3 mixed，dtype 声明仅作来源记录。")
    if model["model_id"] in ("qwen35_2b", "qwen36_35b_a3b"):
        notes.append("Q 旁 output gate 作用于 Attention 输出，不形成额外 query head 或 KV 状态。")
    return notes


def create_config(conventions, models):
    registry = read(TASK / "data/sources.json")
    source_by_path = {s["local_path"]: s for s in registry}
    native_models = {m["id"]: m for m in read(TASK / "data/models.json")["models"]}
    paths = {
        "scripts/format_results.py": "display-only decimal rounding and K/M labels",
        "data/models.json": "six fixed model identities, native attention dimensions and context conditions",
        "data/sources.json": "fixed URLs, revisions and SHA-256 source registry",
        "table_IIa/data/config.json": "one-byte operator-input reference and RI=Q_S/Q_R",
        "table_IIb/04_crosscheck/CONTRACT.zh.md": "Attention formulas, windows, native dimensions, output organization",
        "table_IIb/04_crosscheck/data/conventions.json": "common machine interface and exact value schema",
        "table_IIb/04_crosscheck/data/model_inputs.json": "fixed model order, revisions, selected layers and dimensions",
        "table_IIb/04_crosscheck/template/preamble.tex": "shared typography, full-width model/result table setup and decimal RI style",
        "../archived/task2_table_IIb_previous/03_attention/data/results.json": "operator demands and effective capacities, migration regression only",
    }
    records = []
    for model in models:
        material = model["local_material"]
        model_paths = [material[k] for k in ("structure_card", "raw_config", "raw_model_card", "implementation")]
        for path in model_paths:
            if path.endswith("STRUCTURE.zh.md"):
                locator = "身份与选择、关键结构、KV 与工况入口"
            elif path.endswith("config.json"):
                locator = "native num_attention_heads/num_key_value_heads/head_dim[/v_head_dim], layer type and context keys"
            elif path.endswith("README.md"):
                locator = "context support; Ling official YaRN recipe lines 238-250 when applicable"
            else:
                locator = "Attention constructor/forward: query dimensions, KV cache update, GQA sharing and matrix inputs"
            paths[path] = locator
        records.append({
            "model_id": model["model_id"], "display_name": model["display_name"],
            "model_revision": model["model_revision"], "selected_layer": model["selected_layer"],
            "parameters": parameters(model), "context_notes": context_notes(model, native_models[model["model_id"]]),
            "source_paths": model_paths,
        })
    sources = []
    for path, locator in paths.items():
        digest = hashlib.sha256((TASK / path).read_bytes()).hexdigest()
        if path in source_by_path:
            assert digest == source_by_path[path]["sha256"], path
        sources.append({"path": path, "sha256": digest, "locator": locator})
    return {
        "schema_version": conventions["schema_version"], "reference_id": conventions["reference_id"],
        "boundary": conventions["boundary"], "element_bytes": conventions["element_bytes"],
        "model_order": conventions["model_order"],
        "sweeps": {w: conventions["sweeps"][w] for w in WORKLOADS},
        "window_rules": window_rules(), "models": records, "sources": sources,
    }


def calculate(model, workload, length, rules):
    """Closed-form production count, using the complete native head dimensions."""
    p = parameters(model)
    hq, hkv, dq, dv = (p[k] for k in ("H_q", "H_kv", "d_QK", "d_V"))
    prefill = workload == "attention_prefill"
    appended = length if prefill else 1
    initial = 0 if prefill else length - 1
    prefix_sum = length * (length + 1) // 2 if prefill else length
    qk_s, av_s = hq * appended * dq, hq * prefix_sum
    qk_r, av_r = hkv * appended * dq, hkv * appended * dv
    components = []
    for name, shape, role, s, r, width in [
        ("QK", [length, dq], "各 query head 的 query；每个有效 query 输入 d_QK 元素。", qk_s, qk_r, dq),
        ("AV", [dv, length], "各 query head 的 softmax 后系数；因果前缀 i 输入 i 元素。", av_s, av_r, dv),
    ]:
        components.append({
            "id": name, "shape_N_K": shape, "state_copies": hkv, "input_role": role,
            "Q_S": s, "Q_R": r, "RI": exact(Fraction(s, r)),
            "resident_bytes_initial": initial * hkv * width,
            "resident_bytes_final": length * hkv * width,
        })
    s = hq * (appended * dq + prefix_sum)
    r = appended * hkv * (dq + dv)
    return {
        "case_id": f"{model['model_id']}/{workload}/{length}",
        "model_id": model["model_id"], "model_revision": model["model_revision"],
        "selected_layer": model["selected_layer"], "workload": workload, "kind": "finite",
        "U": None, "L": length, "parameters": p, "window": rules[workload],
        "result": {"Q_S": s, "Q_R": r, "RI": exact(Fraction(s, r)),
                   "resident_bytes_initial": initial * hkv * (dq + dv),
                   "resident_bytes_final": length * hkv * (dq + dv),
                   "shared_input_bytes_removed": 0},
        "components": components,
    }


def make_csv(conventions, results):
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=conventions["csv_columns"], lineterminator="\n")
    writer.writeheader()
    for case in results["cases"]:
        prefix = {k: case[k] for k in ("case_id", "model_id", "model_revision", "selected_layer", "workload", "kind", "U", "L")}
        for component, demand in [("total", case["result"])] + [(c["id"], c) for c in case["components"]]:
            row = {**prefix, "component": component, "Q_S_Byte": demand["Q_S"],
                   "Q_R_Byte": demand["Q_R"], "RI_exact": compact(demand["RI"]),
                   "resident_initial_Byte": demand["resident_bytes_initial"],
                   "resident_final_Byte": demand["resident_bytes_final"]}
            if component == "total":
                row["shared_input_removed_Byte"] = demand["shared_input_bytes_removed"]
            else:
                row.update(N=demand["shape_N_K"][0], K=demand["shape_N_K"][1], state_copies=demand["state_copies"])
            writer.writerow(row)
    return buffer.getvalue()


def models_tex(models):
    lines = [r"\ModelTableSetup", r"\begin{tabularx}{\linewidth}{@{}p{0.32\linewidth}*{6}{>{\centering\arraybackslash}X}@{}}", r"\toprule",
             r"模型 & 所选层 & $H_q$ & $H_{\rm kv}$ & $g$ & $d_{\rm QK}$ & $d_V$\\", r"\midrule"]
    for model in models:
        p = parameters(model)
        lines.append(model["display_name"] + " & " + " & ".join(str(v) for v in [model["selected_layer"], p["H_q"], p["H_kv"], p["g"], p["d_QK"], p["d_V"]]) + r"\\")
    return "\n".join(lines + [r"\bottomrule", r"\end{tabularx}"]) + "\n"


def result_tables(models, results):
    by_id = {c["case_id"]: c for c in results["cases"]}
    lines = []
    preview = ["# Attention：中文结果预览", "", "## 对象与公式", "",
               "单序列、所选完整/global 因果 GQA；所有计量角色取 1 Byte/element。H_q 为 query 头数，H_kv 为 KV 头数，g=H_q/H_kv；d_QK 与 d_V 为原生头维，L 为本次追加后可见长度。每个 KV head 保存一份唯一逻辑 K/V。", "",
               "Prefill：空 KV → L。Q_S = H_q[L d_QK + L(L+1)/2]，Q_R = L H_kv(d_QK+d_V)，RI = g[d_QK+(L+1)/2]/(d_QK+d_V)。", "",
               "Decode：已有 L−1 追加一个 → L。Q_S = H_q(d_QK+L)，Q_R = H_kv(d_QK+d_V)，RI = g(d_QK+L)/(d_QK+d_V)。", "",
               "QK 的 query 与 AV 的 softmax 后系数分别计入各矩阵阶段，输出不另加。最终有效 KV 容量均为 L H_kv(d_QK+d_V) Byte；Prefill 初始容量为 0，Decode 初始容量为 (L−1)H_kv(d_QK+d_V) Byte。因果三角和仅表示算法有效范围。", "",
               "## 模型信息", "", "六模型均取固定版本中的完整/global GQA 层，层号从 0 起。", "",
               "| 模型 | 所选层 | H_q | H_kv | g | d_QK | d_V |", "|---|---:|---:|---:|---:|---:|---:|"]
    for model in models:
        p = parameters(model)
        preview.append("| " + model["display_name"] + " | " + " | ".join(str(v) for v in [model["selected_layer"], p["H_q"], p["H_kv"], p["g"], p["d_QK"], p["d_V"]]) + " |")
    preview += ["", "各模型保留原有上下文设置。Ling-1T 的 L=65536（64K）沿用既定的官方 YaRN factor=4、original_max_position_embeddings=32768、type=yarn，并设置 --max-model-len 131072。MiMo 保留原生 d_QK=192、d_V=128，Value 写入前乘 0.612，所选全局层无 sink。", "",
                "## 代入结果", "", "两表均以模型为行、追加后可见长度 L 为列，单元格为小数 RI；1K=1024，RI≥1 保留一位小数。", ""]
    for workload, name, window in [(WORKLOADS[0], "预填充（Prefill）", "空 KV 建到 $L$"), (WORKLOADS[1], "单步解码（Decode）", "已有 $L-1$，追加一个")]:
        if lines:
            lines.append(r"\par\bigskip")
        lines += [rf"\textbf{{{name}的 $\RI$：{window}}}\par\smallskip",
                  r"\ResultTableSetup",
                  r"\begin{tabularx}{\linewidth}{@{}p{0.32\linewidth}*{3}{>{\centering\arraybackslash}X}@{}}",
                  r"\toprule", r"模型 & $L=1\mathrm{K}$ & $L=8\mathrm{K}$ & $L=64\mathrm{K}$\\", r"\midrule"]
        preview += ["### " + name, "", "| 模型 | L=1K | L=8K | L=64K |", "|---|---:|---:|---:|"]
        for model in models:
            values = [by_id[f"{model['model_id']}/{workload}/{length}"]["result"]["RI"] for length in (1024, 8192, 65536)]
            lines.append(model["display_name"] + " & " + " & ".join("$" + tex_exact(v) + "$" for v in values) + r"\\")
            preview.append("| " + model["display_name"] + " | " + " | ".join(ri_decimal(v) for v in values) + " |")
        lines += [r"\bottomrule", r"\end{tabularx}"]
        preview.append("")
    preview += ["例如，Qwen3.5-2B 在 Prefill、L=1K 时，Q_S=8[1024×256+1024×1025/2]=6,295,552 Byte，Q_R=1024×2×(256+256)=1,048,576 Byte，RI≈6.0。", "",
                "## 结果说明", "",
                "固定头维时，RI 随 g 成比例增长。两个 Qwen 模型的头维相同，Qwen3.6 的 g 加倍，RI 也加倍。", "",
                "RI 均随 L 线性增长；写入窗口则不同：Prefill 从空 KV 建到 L，Decode 只追加一个 token。", "",
                "Hy3 与 Ling 的头结构相同，RI 相同；MiMo 直接使用原生 192/128 头维。", "",
                "固定模型来源、精确字节及复算记录见本目录 README 与 data/；数学入口为 Table II(a)。", ""]
    return "\n".join(lines) + "\n", "\n".join(preview)


def artifacts():
    conventions = read(COMMON / "data/conventions.json")
    models = read(COMMON / "data/model_inputs.json")["models"]
    config = create_config(conventions, models)
    cases = [calculate(model, workload, length, config["window_rules"])
             for model in models for workload in WORKLOADS for length in config["sweeps"][workload]["L"]]
    results = {"schema_version": conventions["schema_version"], "reference_id": conventions["reference_id"],
               "boundary": conventions["boundary"], "model_order": conventions["model_order"],
               "workload_ids": WORKLOADS, "cases": cases}
    tables, preview = result_tables(models, results)
    return {"data/config.json": dump(config), "data/results.json": dump(results),
            "data/results.csv": make_csv(conventions, results), "tex/models.generated.tex": models_tex(models),
            "tex/results.generated.tex": tables, "PREVIEW.zh.md": preview}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    outputs = artifacts()
    for relative, expected in outputs.items():
        target = HERE / relative
        if args.emit:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(expected, encoding="utf-8")
        elif not target.exists() or target.read_text(encoding="utf-8") != expected:
            raise SystemExit(f"STALE: {relative}; run generate.py --emit explicitly")
    print(f"PASS: {len(outputs)} generated artifacts; 36 exact finite cases" + (" emitted" if args.emit else " compared read-only"))


if __name__ == "__main__":
    main()
