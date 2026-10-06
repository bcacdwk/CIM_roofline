"""Select and typeset accepted Task II results; no new workload analysis.

Writes the manuscript's single-column reuse table and full-width model table,
plus the exact selected records. Source Tasks and model files are read-only.
"""
from pathlib import Path
from fractions import Fraction
import csv
import importlib.util
import json
import sys
sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks/task2_table_II_workloads"
spec = importlib.util.spec_from_file_location("task2_readonly_formatter", TASK / "scripts/format_results.py")
fmt = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fmt)

def read_json(relative):
    return json.loads((TASK / relative).read_text())

def fraction(value):
    return Fraction(value["numerator"], value["denominator"]) if isinstance(value, dict) else Fraction(value)

def record(row):
    result = row["result"]
    if row["kind"] == "limit":
        assert row["U"] == result["Q_S"] == result["RI"] == "infinity"
        assert result["Q_R"] == row["N"] * row["K"]
        return {"case_id": row["case_id"], "kind": "limit", "Q_S": result["Q_S"],
                "Q_R": result["Q_R"], "RI_numerator": "", "RI_denominator": "",
                "display_RI": fmt.ri_decimal(result["RI"])}
    ri = fraction(result["RI"])
    assert ri == Fraction(result["Q_S"], result["Q_R"])
    return {"case_id": row["case_id"], "kind": "finite", "Q_S": result["Q_S"], "Q_R": result["Q_R"],
            "RI_numerator": ri.numerator, "RI_denominator": ri.denominator,
            "display_RI": fmt.ri_decimal(result["RI"])}

def save_records(name, rows):
    with (HERE / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def make_reuse_table():
    data = read_json("table_IIa/data/results.json")
    lookup = {(r["N"], r["K"], r["U"]): r for r in data["cases"]}
    shapes = [(128, 128), (1024, 1024), (4096, 4096), (1024, 4096), (4096, 1024)]
    us = [128, 1024, 16384, 131072, 1048576, "infinity"]
    lines = [
        "% Selected from Task II(a) data/results.json; exact values in selected_reuse.csv.",
        r"\begin{papertable}",
        r"\caption{Resident intensity after one complete weight load}",
        r"\label{tab:reuse-intensity}",
        r"\footnotesize\setlength{\tabcolsep}{2.5pt}\renewcommand{\arraystretch}{1.15}",
        r"\begin{tabularx}{\columnwidth}{@{}l*{6}{>{\centering\arraybackslash}X}@{}}",
        r"\toprule",
        r"Weight shape & \multicolumn{6}{c}{Reuse count $U$} \\",
        r"\cmidrule(l){2-7}",
        r"$N\times K$ & $128$ & $1\Kilo$ & $16\Kilo$ & $128\Kilo$ & $1\mathrm{M}$ & $\to\infty$ \\",
        r"\midrule",
    ]
    selected = []
    for n, k in shapes:
        rows = [lookup[n, k, u] for u in us]
        for row in rows:
            if row["kind"] == "finite":
                assert fraction(row["result"]["RI"]) == Fraction(row["U"], n)
        selected.extend(record(row) for row in rows)
        cells = [r"$\infty$" if row["kind"] == "limit" else fmt.ri_decimal(row["result"]["RI"]) for row in rows]
        lines.append(rf"${n}\times{k}$ & " + " & ".join(cells) + r" \\")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\par\smallskip\raggedright",
        r"One byte/element: $Q_S=UK$, $Q_R=NK$, $\RI=U/N$. As $U\to\infty$, the single load $Q_R=NK$ stays finite. Shapes are logical matrices, not hardware tiles. $1\Kilo=1024$, $1\mathrm{M}=1024^2$.",
        r"\end{papertable}",
    ]
    (HERE / "reuse_intensity.tex").write_text("\n".join(lines) + "\n")
    save_records("selected_reuse.csv", selected)
    return len(selected)

def make_workload_table():
    data = read_json("table_IIb/04_crosscheck/data/results.json")
    models = {m["id"]: m for m in read_json("data/models.json")["models"]}
    lookup = {(r["model_id"], r["workload"], r["U"], r["L"]): r for r in data["cases"]}
    names = {
        "qwen35_2b": "Qwen3.5-2B",
        "ministral3_8b_2512": "Ministral 3 8B",
        "qwen36_35b_a3b": "Qwen3.6-35B-A3B",
        "hy3_295b": "Hy3 (295B)",
        "ling_1t": "Ling-1T (1000B)",
        "mimo_v25_pro": "MiMo-V2.5-Pro (1020B)",
    }
    for mid, expected in [("hy3_295b", 295), ("ling_1t", 1000), ("mimo_v25_pro", 1020)]:
        assert models[mid]["reported_parameters"]["total_billions"] == expected
    groups = [
        ("qkv_projection", "U", [1024, 131072, 1048576]),
        ("ffn_or_moe", "U", [16, 1024, 16384]),
        ("attention_prefill", "L", [1024, 8192, 65536]),
        ("attention_decode", "L", [1024, 8192, 65536]),
    ]
    lines = [
        "% Selected from Task II(b) 04_crosscheck/data/results.json; no O-projection values are implied.",
        r"\begin{paperwidetable}",
        r"\caption{Resident intensities of representative inference matrix stages}",
        r"\label{tab:workload-intensity}",
        r"\footnotesize\setlength{\tabcolsep}{1.6pt}\renewcommand{\arraystretch}{1.25}",
        r"\begin{tabularx}{\textwidth}{@{}p{0.20\textwidth}*{12}{>{\centering\arraybackslash}X}@{}}",
        r"\toprule",
        r"& \multicolumn{6}{c}{\textbf{Weight projections}} & \multicolumn{6}{c}{\textbf{Attention}} \\",
        r"\cmidrule(lr){2-7}\cmidrule(l){8-13}",
        r"& \multicolumn{3}{c}{QKV ($U$)} & \multicolumn{3}{c}{FFN/MoE ($U$)} & \multicolumn{3}{c}{Prefill ($L$)} & \multicolumn{3}{c}{Decode ($L$)} \\",
        r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(lr){8-10}\cmidrule(l){11-13}",
        r"Model & $1\Kilo$ & $128\Kilo$ & $1\mathrm{M}$ & $16$ & $1\Kilo$ & $16\Kilo$ & $1\Kilo$ & $8\Kilo$ & $64\Kilo$ & $1\Kilo$ & $8\Kilo$ & $64\Kilo$ \\",
        r"\midrule",
    ]
    selected = []
    for mid in data["model_order"]:
        rows = []
        for workload, variable, values in groups:
            for value in values:
                u, length = (value, None) if variable == "U" else (None, value)
                rows.append(lookup[mid, workload, u, length])
        assert len(rows) == 12
        selected.extend(record(row) for row in rows)
        lines.append(names[mid] + " & " + " & ".join(fmt.ri_decimal(row["result"]["RI"]) for row in rows) + r" \\")
    lines += [
        r"\bottomrule\end{tabularx}",
        r"\par\smallskip\raggedright",
        r"Entries are $\RI$; all roles use one byte/element. QKV includes any gate, excluding O. FFN/MoE counts one dense FFN or one routed expert. Prefill builds KV from empty; decode appends one token to a visible length $L$. $1\Kilo=1024$, $1\mathrm{M}=1024^2$. Ling-1T at $64\Kilo$ uses the fixed extension.",
        r"\end{paperwidetable}",
    ]
    (HERE / "workload_intensity.tex").write_text("\n".join(lines) + "\n")
    save_records("selected_workloads.csv", selected)
    return len(selected)

if __name__ == "__main__":
    a = make_reuse_table()
    b = make_workload_table()
    print(f"Selected {a} basic-reuse and {b} inference cases from accepted data; no new scenarios.")
