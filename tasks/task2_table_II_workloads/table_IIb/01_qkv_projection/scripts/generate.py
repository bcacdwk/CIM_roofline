#!/usr/bin/env python3
"""Recompute QKV one-load results. Read-only unless --emit is supplied."""
import argparse
import csv
import hashlib
import io
import json
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
TASK = HERE.parents[1]
import sys
sys.dont_write_bytecode = True
sys.path.insert(0, str(TASK / "scripts"))
from format_results import ri_decimal, count_label
CROSS = HERE.parent / "04_crosscheck"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def dumps(value):
    return json.dumps(value, ensure_ascii=False, indent=2) + "\n"


def exact(value):
    value = Fraction(value)
    return value.numerator if value.denominator == 1 else {
        "numerator": value.numerator, "denominator": value.denominator}


def display(value, tex=False):
    return ri_decimal(value, tex=tex)


def exact_text(value):
    if isinstance(value, dict):
        return f'{value["numerator"]}/{value["denominator"]}'
    return str(value)


def configuration(conventions):
    fixed = read(CROSS / "data/model_inputs.json")["models"]
    models = {m["id"]: m for m in read(TASK / "data/models.json")["models"]}
    source_paths = {
        "scripts/format_results.py": "display-only decimal rounding and K/M labels",
        "table_IIb/04_crosscheck/CONTRACT.zh.md": "QKV window and shared-stage input rule",
        "table_IIb/04_crosscheck/data/conventions.json": "schema, sweeps and exact values",
        "table_IIb/04_crosscheck/data/model_inputs.json": "six fixed model inputs",
        "table_IIa/data/config.json": "one complete weight load, U served vectors",
        "data/models.json": "identity, backbone, attention and precision",
        "data/sources.json": "official source URLs, revisions and hashes",
    }
    output_models = []
    for item in fixed:
        original = models[item["model_id"]]
        model = {k: item[k] for k in ["model_id", "display_name", "model_revision", "selected_layer"]}
        model["parameters"] = {k: item[k] for k in ["D", "H_q", "H_kv", "d_QK", "d_V", "D_g"]}
        model["parameters"].update({"N_Q": item["H_q"]*item["d_QK"], "N_G": item["D_g"],
                                    "N_K": item["H_kv"]*item["d_QK"], "N_V": item["H_kv"]*item["d_V"]})
        model["parameters"]["N_proj"] = sum(model["parameters"][f"N_{j}"] for j in ["Q", "G", "K", "V"])
        dtype = original["precision"]["checkpoint_declared_dtype"]
        model["context_notes"] = ["Selected layer is full/global causal GQA; layer index starts at 0.",
                                  f"Checkpoint declared dtype: {dtype}; counted logical elements use 1 Byte each.",
                                  "Native projection packing does not add duplicate logical Q/G/K/V weights."]
        if item["model_id"] == "mimo_v25_pro":
            model["context_notes"].append("Native checkpoint uses mixed FP8 E4M3; the declared default floating dtype does not describe every weight.")
        model["source_paths"] = []
        for key, locator in [("structure_card", "投影与 FFN 矩阵；层号从 0 起"),
                             ("raw_config", "hidden_size, num_attention_heads, num_key_value_heads, head_dim, v_head_dim/attn_output_gate"),
                             ("implementation", "Attention constructor and Q/G/K/V projection split")]:
            path = item["local_material"][key]
            source_paths[path] = locator
            model["source_paths"].append(path)
        output_models.append(model)
    return {
        "schema_version": conventions["schema_version"],
        "reference_id": conventions["reference_id"],
        "boundary": conventions["boundary"],
        "element_bytes": 1,
        "model_order": conventions["model_order"],
        "sweeps": {"qkv_projection": conventions["sweeps"]["qkv_projection"]},
        "window_rules": {"qkv_projection": {
            "initial_state": "所选 Q、可选 G、K、V 权重尚未装载，有效容量为 0 Byte。",
            "resident_write_rule": "全部所选投影权重完整写入一次，共 D*N_proj Byte；末态保留这些权重；U→∞ 时写入量仍为该有限值。",
            "streaming_input_rule": "同一阶段的 X[u,d] 由 Q、可选 G、K、V 共享，汇总只计一次，共 U*D Byte；U 是这次装载实际服务的向量总数。"
        }},
        "models": output_models,
        "sources": [{"path": p, "sha256": hashlib.sha256((TASK / p).read_bytes()).hexdigest(),
                     "locator": loc} for p, loc in source_paths.items()],
    }


def compute(config):
    cases = []
    for model in config["models"]:
        p = model["parameters"]
        d = p["D"]
        widths = [("Q", p["H_q"] * p["d_QK"])]
        if p["D_g"]:
            widths.append(("G", p["D_g"]))
        widths.extend([("K", p["H_kv"] * p["d_QK"]),
                       ("V", p["H_kv"] * p["d_V"])])
        n_proj = sum(n for _, n in widths)
        for b in config["sweeps"]["qkv_projection"]["U"]:
            limit = b == "infinity"
            components = [{
                "id": name, "shape_N_K": [n, d], "state_copies": 1,
                "input_role": "shared_projection_input_X",
                "Q_S": "infinity" if limit else b * d,
                "Q_R": d * n,
                "RI": "infinity" if limit else exact(Fraction(b, n)),
                "resident_bytes_initial": 0, "resident_bytes_final": d * n,
            } for name, n in widths]
            cases.append({
                "case_id": f'{model["model_id"]}/qkv_projection/{b}',
                "model_id": model["model_id"], "model_revision": model["model_revision"],
                "selected_layer": model["selected_layer"], "workload": "qkv_projection",
                "kind": "limit" if limit else "finite", "U": b, "L": None,
                "parameters": dict(p),
                "window": dict(config["window_rules"]["qkv_projection"]),
                "result": {
                    "Q_S": "infinity" if limit else b * d,
                    "Q_R": d * n_proj,
                    "RI": "infinity" if limit else exact(Fraction(b, n_proj)),
                    "resident_bytes_initial": 0, "resident_bytes_final": d * n_proj,
                    "shared_input_bytes_removed": "infinity" if limit else (len(widths) - 1) * b * d,
                },
                "components": components,
            })
    return {"schema_version": config["schema_version"], "reference_id": config["reference_id"],
            "boundary": config["boundary"], "model_order": config["model_order"],
            "workload_ids": ["qkv_projection"], "cases": cases}


def csv_text(results, conventions):
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=conventions["csv_columns"], lineterminator="\n")
    writer.writeheader()
    for case in results["cases"]:
        for part in [{"id": "total", **case["result"]}] + case["components"]:
            row = {k: case[k] for k in ["case_id", "model_id", "model_revision", "selected_layer", "workload", "kind", "U", "L"]}
            row.update({"component": part["id"], "N": part.get("shape_N_K", ["", ""])[0],
                        "K": part.get("shape_N_K", ["", ""])[1], "state_copies": part.get("state_copies", ""),
                        "Q_S_Byte": part["Q_S"], "Q_R_Byte": part["Q_R"],
                        "RI_exact": "infinity" if part["RI"] == "infinity" else exact_text(part["RI"]),
                        "resident_initial_Byte": part["resident_bytes_initial"],
                        "resident_final_Byte": part["resident_bytes_final"],
                        "shared_input_removed_Byte": part.get("shared_input_bytes_removed", "")})
            writer.writerow(row)
    return stream.getvalue()


def table_models(config):
    lines = [r"\ModelTableSetup", r"\begin{tabularx}{\linewidth}{@{}p{0.32\linewidth}*{7}{>{\centering\arraybackslash}X}@{}}", r"\toprule",
             r"模型 & 层号 & $D$ & $N_Q$ & $N_G$ & $N_K$ & $N_V$ & $N_{\rm proj}$ \\", r"\midrule"]
    for m in config["models"]:
        p = m["parameters"]
        q, g, k, v = (p[f"N_{j}"] for j in ["Q", "G", "K", "V"])
        lines.append(" & ".join(map(str, [m["display_name"], m["selected_layer"], p["D"], q, g, k, v, q+g+k+v])) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabularx}"])
    return "\n".join(lines) + "\n"


def table_results(config, results):
    lines = [r"\ResultTableSetup", r"\begin{tabularx}{\linewidth}{@{}p{0.32\linewidth}*{5}{>{\centering\arraybackslash}X}@{}}", r"\toprule",
             r"模型 & $U=1$ & $U=1\mathrm{K}$ & $U=128\mathrm{K}$ & $U=1\mathrm{M}$ & $U\to\infty$ \\", r"\midrule"]
    for m in config["models"]:
        cases = [c for c in results["cases"] if c["model_id"] == m["model_id"]]
        lines.append(m["display_name"] + " & " + " & ".join("$" + display(c["result"]["RI"], True) + "$" for c in cases) + r" \\")
    lines.extend([r"\bottomrule", r"\end{tabularx}"])
    return "\n".join(lines) + "\n"


def preview(config, results):
    lines = ["# QKV 投影的输入复用与 RI", "", "## 对象与公式", "", "固定一层完整／全局 GQA；Q、可选 G、K、V 权重完整装载一次，累计服务 U 个向量（复用次数 reuse count，包含首次使用，可跨多个 batch/请求）。每元素 1 Byte，同阶段输入共享一次。", "",
             "Q_S = UD；Q_R = D N_proj；RI = U/N_proj。N_proj = H_q d_QK + D_g + H_kv(d_QK+d_V)。", "",
             "## 模型信息", "",
             "| 模型 | 层号（0 起） | D | Q/G/K/V 输出宽度 | N_proj |", "|---|---:|---:|---|---:|"]
    for m in config["models"]:
        c = next(c for c in results["cases"] if c["model_id"] == m["model_id"])
        widths = "/".join(str(c["parameters"].get(f"N_{p}", 0)) for p in ["Q", "G", "K", "V"])
        lines.append(f'| {m["display_name"]} | {m["selected_layer"]} | {m["parameters"]["D"]} | {widths} | {c["parameters"]["N_proj"]} |')
    lines += ["", "## 代入结果", "", "1K=1024，1M=1024²。RI≥1 保留一位小数，RI<1 保留三位有效数字；精确值见机器数据。", "", "| 模型 | U=1 | U=1K | U=128K | U=1M | U→∞ |", "|---|---:|---:|---:|---:|---:|"]
    for m in config["models"]:
        ri = [display(c["result"]["RI"]) for c in results["cases"] if c["model_id"] == m["model_id"]]
        lines.append("| " + m["display_name"] + " | " + " | ".join(ri) + " |")
    lines += ["", "## 结果说明", "", "无穷列为复用极限：Q_S 与 RI 无界增长，Q_R 仍为有限的一次权重写入量。Hy3 与 Ling 的 N_proj 均为 10240，因此各档 RI 相同；D 的差别会改变绝对输入和权重字节。", "", "中文正文及一条完整数字代入见 [PDF](output/report.zh.pdf)。精确字节、分项、窗口和来源见 data/；本预览由 generate.py 生成。", ""]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--emit", action="store_true")
    args = parser.parse_args()
    conventions = read(CROSS / "data/conventions.json")
    config = configuration(conventions)
    results = compute(config)
    outputs = {"data/config.json": dumps(config), "data/results.json": dumps(results),
               "data/results.csv": csv_text(results, conventions),
               "tex/models.generated.tex": table_models(config),
               "tex/results.generated.tex": table_results(config, results),
               "PREVIEW.zh.md": preview(config, results)}
    for name, content in outputs.items():
        path = HERE / name
        if args.emit:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            raise SystemExit(f"STALE: {path}; use --emit to refresh")
    print("PASS: 24 finite cases + 6 symbolic limits; generated artifacts " + ("written" if args.emit else "match"))


if __name__ == "__main__":
    main()
