#!/usr/bin/env python3
"""Render Table I and the final equal-scale log-log rho/tau map from reviewed results.

Run with: python -X utf8 path/to/build_figures.py
Only this directory is written. No source estimates are changed.
"""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
SOURCE = ANALYSIS / "data/ten_case_results.json"
OUT = HERE / "output"
DATA = HERE / "data"
INK = "#182838"
MUTED = "#657382"
GRID = "#e5eaf0"
ACCENT = "#245b78"
STRESS = "#a54d1d"
COLORS = ["#2d63ad", "#6e52a2", "#a37622", "#68737d", "#c54e55",
          "#178276", "#ca6b2b", "#338fa5", "#7b8736", "#ad5390"]
LABELS = ["SRAM ACIM", "SRAM DCIM", "2D NOR", "3D NAND", "RRAM",
          "MRAM", "PCM", r"HfO$_2$ FeRAM", "Gain-cell eDRAM", "3D FeFET"]
PLAIN_LABELS = ["SRAM ACIM", "SRAM DCIM", "2D NOR", "3D NAND", "RRAM",
                "MRAM", "PCM", "HfO2 FeRAM", "Gain-cell eDRAM", "3D FeFET"]
MODES = ["Binary charge-domain ACIM", "16-term digital reduction",
         "Binary sensing + digital reduction", "SLC integration; sustained rewrite",
         "32-term ACIM; 16 write lanes", "Complementary MTJ; digital path",
         "8-row ACIM; diagonal updates", "1T1C digital; read-code reuse",
         "Two-endpoint ACIM; refresh included", "2026 vertical AND; digital path"]
PROFILES = ("short", "reference", "long")
PROFILE_LABELS = ("Short budget", "Typical / reference", "Long budget")
METRICS = ("rho", "tau", "RI_star")

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.edgecolor": "#afbac5",
    "axes.titleweight": "bold", "axes.titlesize": 11.5,
    "mathtext.fontset": "dejavusans", "pdf.fonttype": 42,
    "ps.fonttype": 42, "svg.fonttype": "none", "savefig.facecolor": "white",
})


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def portable(value):
    """Normalize path separators only for comparing POSIX-generated metadata."""
    if isinstance(value, dict):
        return {k.replace("\\", "/"): portable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [portable(v) for v in value]
    if isinstance(value, str):
        return value.replace("\\", "/")
    return value


def profile_of(row):
    params = row["scenario_parameters"]
    for key in ("profile", "common_profile"):
        if params.get(key) in PROFILES:
            return params[key]
    if row["recommended"]:
        return "reference"
    for name in PROFILES:
        if name in row["scenario_id"].split("_"):
            return name
    # All remaining main result arrays explicitly use short/reference/long order.
    index = row["source_result"].split("/")[-1]
    if index.isdigit() and int(index) < 3:
        return PROFILES[int(index)]
    raise ValueError(f"Unrecognized primary profile: {row['source_result']}")


def load_and_validate():
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    adapter = import_file("reviewed_export_adapter", ANALYSIS / "scripts/export_ten_cases.py")
    fresh = adapter.normalized()
    assert portable(fresh) == portable(document), "Unified data differ from current native results"

    selected_types = {"recommended_reference", "paired_conditional"}
    rows = [r for r in document["results"] if r["scenario_type"] in selected_types
            or (r["case_id"] == "09_gain_cell_edram" and r["scenario_id"] == "long")]
    grouped = []
    for case in document["cases"]:
        group = {profile_of(r): r for r in rows if r["case_id"] == case["case_id"]}
        assert set(group) == set(PROFILES), (case["case_id"], group.keys())
        assert group["reference"]["recommended"]
        grouped.append(group)
    assert len(grouped) == 10 and len(rows) == 30

    for row in rows:
        file_name, pointer = row["source_result"].split("#/")
        native = json.loads((ANALYSIS / file_name).read_text(encoding="utf-8"))
        for token in pointer.split("/"):
            native = native[int(token)] if isinstance(native, list) else native[token]
        for metric, native_key, factor in [
            ("rho", "rho_Byte_per_s", 1e6),
            ("tau", "tau_Byte_per_s", 1e6), ("RI_star", "ridge", 1),
        ]:
            assert math.isclose(row[metric], native[native_key] / factor, rel_tol=1e-12)
        interval = row["effective_service_interval"] or row["raw_service_time"]
        assert math.isclose(row["rho"], row["B_S"] / interval["streaming_ns"] * 1e3, rel_tol=1e-12)
        assert math.isclose(row["tau"], row["B_R"] / interval["resident_ns"] * 1e3, rel_tol=1e-12)
        assert math.isclose(row["RI_star"], row["rho"] / row["tau"], rel_tol=1e-12)

    # Use the existing independent stage reconstruction without its Windows path-key issue.
    independent = import_file("reviewed_independent_check", ANALYSIS / "scripts/check_ten_cases.py")
    for group in grouped:
        row = group["reference"]
        s, r, br, availability, _ = independent.POINTS[row["case_id"]]
        expected = (128 / s * 1000 * availability, br / r * 1000 * availability,
                    128 / br * r / s)
        assert all(math.isclose(row[k], v, rel_tol=1e-11) for k, v in zip(METRICS, expected))

    assert grouped[8]["long"]["scenario_type"] == "pressure_near_refresh_saturation"
    assert math.isclose(grouped[8]["long"]["maintenance"]["availability"], .0393)
    assert all(r["rho"] is not None and r["tau"] > 0 for r in rows)
    paths = [SOURCE, ANALYSIS / "scripts/export_ten_cases.py",
             ANALYSIS / "scripts/check_ten_cases.py",
             ANALYSIS / "shared_baseline/data/shared_parameters.json"]
    for case in document["cases"]:
        folder = ANALYSIS / case["case_id"]
        paths.extend([folder / "data/results.json", folder / "tex" / (case["case_id"] + ".tex"),
                      folder / "tex/result_card.tex"])
    report = {
        "all_passed": True, "cases": 10, "paired_points_plus_stress": 30,
        "checks": ["Current unified export equals current native adapter after path normalization",
                   "All 30 points match native result pointers at full precision",
                   "Payload / service interval and rho / tau identities hold for all 30 points",
                   "Ten typical points match existing independent stage arithmetic",
                   "Gain-cell long remains a separately marked refresh stress scenario"],
        "platform_note": "Original checker uses POSIX path keys; original adapter serializes platform-specific paths. Source files were not changed.",
        "sha256": {p.relative_to(ANALYSIS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "display": {"rate_unit": "MB/s = 10^6 Byte/s", "significant_digits": 4,
                    "scatter_uses_unrounded_values": True, "axis_scales": "equal log10 scales in the final scatter",
                    "scatter_reference_point_count": 10,
                    "scatter_validation": "rho_tau_loglog_validation.json"},
    }
    return document, grouped, report


def fmt(value):
    """Four significant digits, no scientific notation; tiny rates remain visible."""
    if value == 0:
        return "0"
    decimals = max(0, 3 - math.floor(math.log10(abs(value))))
    return f"{value:,.{decimals}f}"


def save_figure(fig, stem):
    for extension in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{extension}", dpi=220, bbox_inches="tight", pad_inches=.16)


def make_table(groups):
    fig = plt.figure(figsize=(16.8, 8.3), facecolor="white")
    ax = fig.add_axes([.035, .20, .93, .64])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 12)
    ax.axis("off")
    fig.text(.035, .947, "TABLE I   |   Two service capacities across ten CIM technologies",
             fontsize=20, weight="bold")
    fig.text(.035, .898, r"28 nm CMOS reference periphery  ·  $128\times128$ INT8  ·  16 KiB resident state",
             fontsize=11.8, color=MUTED)

    name_width = .275
    column_width = (1 - name_width) / 9
    center = lambda j: name_width + (j + .5) * column_width
    group_x = [name_width + j * 3 * column_width for j in range(3)]
    for i in range(10):
        if i % 2 == 1:
            ax.add_patch(Rectangle((0, 9 - i), 1, 1, color="#f6f8fa", lw=0))
    ax.add_patch(Rectangle((group_x[1], 0), 3 * column_width, 12,
                           color="#e9f2f6", lw=0, zorder=1))
    ax.add_patch(Rectangle((group_x[2], 1), 3 * column_width, 1,
                           color="#fff2e7", lw=0, zorder=1))
    ax.plot([0, 1], [12, 12], color=INK, lw=1.8, clip_on=False)
    ax.plot([0, 1], [10, 10], color=INK, lw=1.1)
    ax.plot([0, 1], [0, 0], color=INK, lw=1.4, clip_on=False)
    ax.text(.014, 11.2, "Technology / reference mode", ha="left", va="center",
            fontsize=11.7, weight="bold")
    for i, label in enumerate(PROFILE_LABELS):
        ax.text(group_x[i] + 1.5 * column_width, 11.45, label,
                ha="center", va="center", fontsize=12.5, weight="bold",
                color=ACCENT if i == 1 else INK)
        ax.plot([group_x[i] + .008, group_x[i] + 3 * column_width - .008],
                [10.98, 10.98], color="#b8c8d3", lw=.8)
        for j, metric in enumerate((r"$\rho$", r"$\tau$", r"$\mathrm{RI}^{*}$")):
            unit = " [MB/s]" if j != 2 else " [–]"
            ax.text(center(i * 3 + j), 10.5, metric + unit, ha="center", va="center",
                    fontsize=11.3, color=ACCENT if i == 1 else MUTED)
    for i, group in enumerate(groups):
        y = 9.5 - i
        ax.add_patch(Rectangle((.001, y - .27), .0038, .54, color=COLORS[i], lw=0))
        ax.text(.014, y + .14, LABELS[i], ha="left", va="center", fontsize=12, weight="bold")
        ax.text(.014, y - .23, MODES[i], ha="left", va="center", fontsize=8.7, color=MUTED)
        for p, profile in enumerate(PROFILES):
            for j, metric in enumerate(METRICS):
                value = fmt(group[profile][metric])
                if i == 8 and p == 2:
                    value += "†"
                ax.text(center(p * 3 + j), y, value, ha="center", va="center", fontsize=11.7,
                        weight="bold" if p == 1 else "normal",
                        color=STRESS if i == 8 and p == 2 else (ACCENT if p == 1 else INK))
    fig.text(.035, .144, r"$\rho$: completed input-payload evaluation capacity.   $\tau$: resident-payload update capacity.   $\mathrm{RI}^{*}=\rho/\tau$: balance threshold.",
             fontsize=10.5)
    fig.text(.035, .109, "Short / typical / long are paired engineering budgets, not confidence bounds. Typical means the selected reference design, not a statistical median.",
             fontsize=9.7, color=MUTED)
    fig.text(.035, .076, "† Gain-cell long: refresh stress only (3.93% service availability); excluded from its ordinary conditional range. All gain-cell rates include periodic refresh.",
             fontsize=9.7, color=STRESS)
    fig.text(.035, .043, "NOR / NAND use complete 16 KiB rewrites; other cases use the declared local update groups. The ten cases include volatile SRAM and gain-cell eDRAM.",
             fontsize=9.5, color=MUTED)
    save_figure(fig, "table_I_three_scenarios")
    return fig


def export_data(document, groups):
    flat = []
    for i, group in enumerate(groups):
        for profile in PROFILES:
            r = group[profile]
            flat.append({"case_id": r["case_id"], "technology": PLAIN_LABELS[i],
                         "profile": profile, "scenario_type": r["scenario_type"],
                         "rho_MB_per_s": r["rho"], "tau_MB_per_s": r["tau"],
                         "RI_star": r["RI_star"], "B_S_Byte": r["B_S"], "B_R_Byte": r["B_R"],
                         "availability": r["maintenance"].get("availability", 1),
                         "mode": r["mode"], "update_pattern": r["update_pattern"],
                         "source_result": r["source_result"],
                         "source_ids": "; ".join(r["source_ids"])})
    with (DATA / "table_scenarios.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(flat[0]))
        writer.writeheader()
        writer.writerows(flat)
    (DATA / "table_scenarios.json").write_text(json.dumps(flat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md = ["# 十类 CIM 技术：三种成对情景", "",
          "ρ、τ 均为十进制 MB/s；RI* = ρ/τ，无量纲。典型即各案例选定的参考点，不是统计中位数。", "",
          "| 技术 | 短 ρ | 短 τ | 短 RI* | **典型 ρ** | **典型 τ** | **典型 RI*** | 长 ρ | 长 τ | 长 RI* |",
          "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for i, group in enumerate(groups):
        cells = [PLAIN_LABELS[i]]
        for profile in PROFILES:
            for key in METRICS:
                value = fmt(group[profile][key])
                if profile == "reference":
                    value = "**" + value + "**"
                if profile == "long" and i == 8:
                    value += "†"
                cells.append(value)
        md.append("| " + " | ".join(cells) + " |")
    md += ["", "† Gain-cell 长情景是刷新压力点，可用率 α=3.93%，不属于普通条件范围。参考点 α=33.39375%。",
           "", "三种情景保持读写成对；不表示误差棒、统计置信区间或所有实现的物理上下界。",
           "ρ 包含完成规定求值及输出所需服务，不能解释为单 cell 普通读取带宽。τ 采用各案例声明的完整更新形状。",
           "", "## 逐例模式和来源", ""]
    for i, case in enumerate(document["cases"]):
        cid = case["case_id"]
        md += [f"- [{PLAIN_LABELS[i]}](../../{cid}/tex/{cid}.tex)：{case['mode']}。更新：{case['update_pattern']}。"]
    (OUT / "table_I_three_scenarios.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    tex = [r"% Generated by build_figures.py; requires booktabs and graphicx.",
           r"\begin{table*}[t]", r"\centering\small", r"\setlength{\tabcolsep}{4pt}",
           r"\caption{Paired engineering scenarios for the ten CIM reference designs. Both service capacities are in decimal MB/s; $\mathrm{RI}^{*}=\rho/\tau$ is dimensionless.}",
           r"\label{tab:ten-cim-scenarios}", r"\resizebox{\textwidth}{!}{%",
           r"\begin{tabular}{@{}l rrr rrr rrr@{}}", r"\toprule",
           r"Technology & \multicolumn{3}{c}{Short budget} & \multicolumn{3}{c}{Typical / reference} & \multicolumn{3}{c}{Long budget}\\",
           r"\cmidrule(lr){2-4}\cmidrule(lr){5-7}\cmidrule(l){8-10}",
           r" & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$\\\midrule"]
    for i, group in enumerate(groups):
        label = LABELS[i].replace("3D FeFET", "3D vertical AND FeFET")
        cells = [label]
        for profile in PROFILES:
            for key in METRICS:
                value = fmt(group[profile][key])
                if profile == "reference":
                    value = r"\textbf{" + value + "}"
                if profile == "long" and i == 8:
                    value += r"$^{\dagger}$"
                cells.append(value)
        tex.append(" & ".join(cells) + r"\\")
    tex += [r"\bottomrule\end{tabular}}", r"\par\smallskip\begin{minipage}{\textwidth}\footnotesize",
            r"Short/typical/long are paired engineering budgets, not statistical bounds. Typical denotes the selected reference point. "
            r"$\dagger$ Gain-cell long is a separately classified refresh stress point ($\alpha=3.93\%$). "
            r"All gain-cell rates include periodic refresh. NOR/NAND use complete 16\,KiB rewrites; other rows use their declared local update groups. "
            r"The ten cases include volatile SRAM and gain-cell eDRAM. $\rho$ includes the complete prescribed evaluation, rather than bare memory reads.",
            r"\end{minipage}", r"\end{table*}"]
    (OUT / "table_I_three_scenarios.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    document, groups, report = load_and_validate()
    export_data(document, groups)
    table = make_table(groups)
    from build_loglog import render_final
    scatter = render_final(groups, report)
    with PdfPages(OUT / "review_figures.pdf", metadata={"Title": "Ten CIM cases: Table I and linear rho–tau map"}) as pdf:
        pdf.savefig(table, bbox_inches="tight", pad_inches=.16)
        pdf.savefig(scatter, bbox_inches="tight", pad_inches=.16)
    (DATA / "validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plt.close("all")
    print("PASS: 10 cases / 30 table scenarios / 10 reference points; native data, arithmetic, and paired-scenario semantics validated.")
    print(f"Figures: {OUT}")


if __name__ == "__main__":
    main()
