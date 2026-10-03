#!/usr/bin/env python3
"""Build native-configuration Table I and both equal-scale log-log plots.

All numerical values come from the unified full-precision data. Only this
summary directory is written; source models and their evidence remain upstream.
"""
from __future__ import annotations
import csv
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
sys.dont_write_bytecode = True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.patches import Rectangle

HERE = Path(__file__).resolve().parent
ANALYSIS = HERE.parent
SOURCE = ANALYSIS / "data/ten_case_results.json"
OUT, DATA = HERE / "output", HERE / "data"
INK, MUTED, GRID, ACCENT = "#182838", "#657382", "#e5eaf0", "#245b78"
COLORS = ["#2d63ad", "#6e52a2", "#a37622", "#68737d", "#c54e55",
          "#178276", "#ca6b2b", "#338fa5", "#7b8736", "#ad5390"]
LABELS = ["SRAM ACIM", "SRAM DCIM", "2D NOR", "3D NAND", "RRAM",
          "MRAM", "PCM", r"HfO$_2$ FeRAM", "Gain-cell eDRAM", "3D FeFET"]
PLAIN_LABELS = ["SRAM ACIM", "SRAM DCIM", "2D NOR", "3D NAND", "RRAM",
                "MRAM", "PCM", "HfO2 FeRAM", "Gain-cell eDRAM", "3D FeFET"]
PROFILES = ("short", "reference", "long")
PROFILE_LABELS = ("Optimistic / fast", "Typical", "Pessimistic / slow")
METRICS = ("rho", "tau", "RI_star")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10,
    "text.color": INK, "axes.labelcolor": INK, "xtick.color": MUTED,
    "ytick.color": MUTED, "axes.edgecolor": "#afbac5", "axes.titleweight": "bold",
    "mathtext.fontset": "dejavusans", "pdf.fonttype": 42, "ps.fonttype": 42,
    "svg.fonttype": "none", "savefig.facecolor": "white"})


def import_file(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def portable(value):
    if isinstance(value, dict):
        return {k.replace("\\", "/"): portable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [portable(v) for v in value]
    return value.replace("\\", "/") if isinstance(value, str) else value


def profile_of(row):
    profile = row["scenario_profile"]
    assert profile in PROFILES
    return profile


def load_and_validate():
    document = json.loads(SOURCE.read_text(encoding="utf-8"))
    adapter = import_file("reviewed_export_adapter", ANALYSIS / "scripts/export_ten_cases.py")
    assert portable(adapter.normalized()) == portable(document), "Stale unified data"
    rows = [r for r in document["results"]
            if r["scenario_type"] in {"recommended_reference", "paired_conditional"}]
    groups = []
    for case in document["cases"]:
        selected = [r for r in rows if r["case_id"] == case["case_id"]]
        group = {profile_of(r): r for r in selected}
        assert len(selected) == 3 and set(group) == set(PROFILES)
        assert group["reference"]["recommended"]
        groups.append(group)
    assert len(groups) == 10 and len(rows) == 30
    for row in rows:
        name, pointer = row["source_mapping"].split("#/")
        native = json.loads((ANALYSIS / name).read_text(encoding="utf-8"))
        for token in pointer.split("/"):
            native = native[int(token)] if isinstance(native, list) else native[token]
        for metric, key, factor in [("rho", "rho_Byte_per_s", 1e6),
                                    ("tau", "tau_Byte_per_s", 1e6), ("RI_star", "RI_star", 1)]:
            assert math.isclose(row[metric], native[key] / factor, rel_tol=1e-12)
        s = row["effective_service_interval"]["streaming_ns"]
        r = row["effective_service_interval"]["resident_ns"]
        assert row["B_S"] == row["K"] * row["b_S"]
        assert row["B_R"] == row["K"] * row["N"] * row["b_R"]
        assert math.isclose(row["rho"], row["B_S"] / s * 1e3, rel_tol=1e-12)
        assert math.isclose(row["tau"], row["B_R"] / r * 1e3, rel_tol=1e-12)
        assert math.isclose(row["RI_star"], row["rho"] / row["tau"], rel_tol=1e-12)
        assert math.isclose(row["U_star"], r / s, rel_tol=1e-12)
        assert math.isclose(row["U_star"], row["N"]*row["b_R"]/row["b_S"]*row["RI_star"], rel_tol=1e-12)
        assert row["rho"] > 0 and row["tau"] > 0 and not row["feasibility"].startswith("infeasible")
    independent = import_file("reviewed_independent_check", ANALYSIS / "scripts/check_ten_cases.py")
    independent.run()  # Reconstruct stages from case inputs; does not write or import calculators.
    paths = [SOURCE, ANALYSIS / "scripts/export_ten_cases.py", ANALYSIS / "scripts/check_ten_cases.py",
             ANALYSIS / "shared_baseline/data/shared_parameters.json"]
    for case in document["cases"]:
        for suffix in ("inputs", "results"):
            paths.append(ANALYSIS / case["case_id"] / "data" / (suffix + ".json"))
    report = {"all_passed": True, "cases": 10, "paired_sustainable_points": 30,
        "checks": ["Unified export equals current native adapter",
                   "Thirty points match native mapping interfaces at full precision",
                   "Native payload, complete service, RI_star and U_star identities hold",
                   "Independent input-derived stage and geometry checker passes for ten cases and thirty scenarios",
                   "Only fixed-resource sustainable paired scenarios selected"],
        "sha256": {p.relative_to(ANALYSIS).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
        "display": {"rate_unit": "MB/s = 10^6 Byte/s", "significant_digits": 2,
                    "scatter_uses_unrounded_values": True, "axis_scales": "equal log10 scales",
                    "native_configurations_not_equal_area_or_equal_work": True}}
    return document, groups, report


def fmt(value):
    """Two significant digits for reading; full precision stays in JSON/CSV."""
    if value == 0:
        return "0"
    rounded = float(f"{value:.2g}")
    decimals = max(0, 1 - math.floor(math.log10(abs(rounded))))
    return f"{rounded:,.{decimals}f}"


def config_label(row):
    """Compact configuration from native metadata, never an assumed macro size."""
    shape = f"{row['K']}×{row['N']}"
    pattern = row["update_pattern"].lower()
    if "page" in pattern:
        mode = "block/page replace" if "block" in pattern else "sector/page overwrite"
    else:
        n = row["transaction_service"]["B_R_Byte"]
        mode = f"{n:g} B " + ("row stripes" if "strip" in pattern else "groups")
        if "isolated_request_ns" in row["transaction_service"]:
            mode = f"{row['B_R']/1024:g} KiB epoch; " + mode
    return shape + " · " + mode


def normalize_svg(path):
    """Preserve XML geometry while writing deterministic LF-only text lines."""
    path.write_text("\n".join(line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()) + "\n", encoding="utf-8")


def save_figure(fig, stem):
    for ext in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{ext}", dpi=220, bbox_inches="tight", pad_inches=.16)
        if ext == "svg": normalize_svg(OUT / f"{stem}.{ext}")


def make_table(groups):
    fig = plt.figure(figsize=(17.4, 8.3), facecolor="white")
    ax = fig.add_axes([.035, .20, .93, .64]); ax.set(xlim=(0, 1), ylim=(0, 12)); ax.axis("off")
    fig.text(.035, .947, "TABLE I   |   Two service capacities across ten CIM technologies", fontsize=20, weight="bold")
    fig.text(.035, .898, "INT8 logical payloads  ·  Selected native configurations  ·  Sustained complete-matrix loading", fontsize=11.8, color=MUTED)
    name_width = .29; cw = (1-name_width)/9
    center = lambda j: name_width + (j+.5)*cw
    gx = [name_width+j*3*cw for j in range(3)]
    for i in range(10):
        if i%2: ax.add_patch(Rectangle((0,9-i),1,1,color="#f6f8fa",lw=0))
    ax.add_patch(Rectangle((gx[1],0),3*cw,12,color="#e9f2f6",lw=0,zorder=1))
    for y,lw in [(12,1.8),(10,1.1),(0,1.4)]: ax.plot([0,1],[y,y],color=INK,lw=lw,clip_on=False)
    ax.text(.014,11.2,"Technology / native K × N / update",ha="left",va="center",fontsize=11.5,weight="bold")
    for i,label in enumerate(PROFILE_LABELS):
        ax.text(gx[i]+1.5*cw,11.45,label,ha="center",va="center",fontsize=12.2,weight="bold",color=ACCENT if i==1 else INK)
        ax.plot([gx[i]+.008,gx[i]+3*cw-.008],[10.98,10.98],color="#b8c8d3",lw=.8)
        for j,m in enumerate((r"$\rho$",r"$\tau$",r"$\mathrm{RI}^{*}$")):
            ax.text(center(i*3+j),10.5,m+(" [MB/s]" if j<2 else " [-]"),ha="center",va="center",fontsize=11.3,color=ACCENT if i==1 else MUTED)
    for i,g in enumerate(groups):
        y=9.5-i
        ax.add_patch(Rectangle((.001,y-.27),.0038,.54,color=COLORS[i],lw=0))
        ax.text(.014,y+.14,LABELS[i],ha="left",va="center",fontsize=12,weight="bold")
        ax.text(.014,y-.23,config_label(g["reference"]),ha="left",va="center",fontsize=9.4,color=MUTED)
        for p,profile in enumerate(PROFILES):
            for j,metric in enumerate(METRICS):
                ax.text(center(p*3+j),y,fmt(g[profile][metric]),ha="center",va="center",fontsize=11.7,weight="bold" if p==1 else "normal",color=ACCENT if p==1 else INK)
    notes = [
        (r"$\rho$: complete input-vector evaluation capacity.   $\tau$: full resident-matrix loading capacity.   $\mathrm{RI}^{*}=\rho/\tau$.",10.5,INK),
        ("Fast / typical / slow are paired, sustainable conditions in one configuration; resource expansions and refresh stress points are excluded.",9.7,MUTED),
        ("K × N counts input and output elements. Group labels describe local update shape; reported τ includes all groups and required full-load overhead.",9.7,MUTED),
        ("Gain-cell rates include refresh. NOR / NAND include erase. Native configurations differ in resources and size; this is not an equal-area or equal-work ranking.",9.5,MUTED)]
    for y,(s,fs,c) in zip((.144,.109,.076,.043),notes): fig.text(.035,y,s,fontsize=fs,color=c)
    save_figure(fig,"table_I_three_scenarios")
    return fig


def export_data(document, groups):
    flat=[]
    for i,g in enumerate(groups):
        for p in PROFILES:
            r=g[p]; m=r["maintenance"]
            flat.append({"case_id":r["case_id"],"technology":PLAIN_LABELS[i],"profile":p,
                "scenario_type":r["scenario_type"],"K":r["K"],"N":r["N"],"configuration":config_label(r),
                "rho_MB_per_s":r["rho"],"tau_MB_per_s":r["tau"],"RI_star":r["RI_star"],"U_star":r["U_star"],
                "B_S_Byte":r["B_S"],"B_R_Byte":r["B_R"],"delta_S_ns":r["delta_S_ns"],"T_R_ns":r["T_R_ns"],
                "availability":m.get("availability",1) if isinstance(m,dict) else 1,
                "mode":r["mode"],"update_pattern":r["update_pattern"],"source_mapping":r["source_mapping"],
                "source_result":r["source_result"],"source_ids":"; ".join(r["source_ids"])})
    with (DATA/"table_scenarios.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(flat[0]),lineterminator="\n"); w.writeheader();w.writerows(flat)
    (DATA/"table_scenarios.json").write_text(json.dumps(flat,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    md=["# 十类 CIM 技术：三种成对情景","","ρ、τ 单位为十进制 MB/s。RI* = ρ/τ；INT8 下 U* = N·RI*。K×N 为输入×输出逻辑元素数。典型为选定原生参考配置。","",
        "| 技术 | 原生 K×N / 更新组织 | 乐观 ρ | 乐观 τ | 乐观 RI* | **典型 ρ** | **典型 τ** | **典型 RI*** | 悲观 ρ | 悲观 τ | 悲观 RI* |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for i,g in enumerate(groups):
        cells=[PLAIN_LABELS[i],config_label(g["reference"])]
        for p in PROFILES:
            cells += [("**"+fmt(g[p][k])+"**") if p=="reference" else fmt(g[p][k]) for k in METRICS]
        md.append("| "+" | ".join(cells)+" |")
    md += ["","三种情景是相同组织和资源下的可持续成对条件，不是独立读写极值、统计区间或资源扩展对照。",
           "τ 使用完整矩阵有效逻辑容量与完整装载服务时间；局部更新分组不改变分子边界。NOR/NAND 包含持续擦写，Gain-cell 包含周期刷新。",
           "不同原生配置的能力不表示等面积或相同计算量的性能排名。完整资源和更新形状在统一机器数据中保留。",
           "","## 逐例模式和来源",""]
    for i,c in enumerate(document["cases"]):
        cid=c["case_id"]
        md += [f"- [{PLAIN_LABELS[i]}](../../{cid}/tex/{cid}.tex)：{c['mode']}。更新：{c['update_pattern']}。"]
    (OUT/"table_I_three_scenarios.md").write_text("\n".join(md)+"\n",encoding="utf-8")
    tex=[r"% Generated by build_figures.py; requires booktabs and graphicx.",r"\begin{table*}[t]",r"\centering\small",r"\setlength{\tabcolsep}{4pt}",
        r"\caption{Paired sustainable scenarios for selected native INT8 CIM configurations. Both capacities use decimal MB/s; $\mathrm{RI}^{*}=\rho/\tau$.}",
        r"\label{tab:ten-cim-scenarios}",r"\resizebox{\textwidth}{!}{%",r"\begin{tabular}{@{}ll rrr rrr rrr@{}}",r"\toprule",
        r"Technology & Native $K\!\times\!N$ / update & \multicolumn{3}{c}{Optimistic / fast} & \multicolumn{3}{c}{Typical} & \multicolumn{3}{c}{Pessimistic / slow}\\",
        r"\cmidrule(lr){3-5}\cmidrule(lr){6-8}\cmidrule(l){9-11}",
        r" & & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$ & $\rho$ & $\tau$ & $\mathrm{RI}^{*}$\\\midrule"]
    for i,g in enumerate(groups):
        cfg=config_label(g["reference"]).replace("×",r"$\times$").replace(" · ","; ")
        cells=[LABELS[i],cfg]
        for p in PROFILES:
            cells += [(r"\textbf{"+fmt(g[p][k])+"}") if p=="reference" else fmt(g[p][k]) for k in METRICS]
        tex.append(" & ".join(cells)+r"\\")
    tex += [r"\bottomrule\end{tabular}}",r"\par\smallskip\begin{minipage}{\textwidth}\footnotesize",
        r"$K$ and $N$ count input and output elements. Local group shapes are shown; $\tau$ uses the entire logical matrix and all required loading overhead. "
        r"Fast/typical/slow retain one resource configuration. NOR/NAND include erase; gain-cell rates include refresh. "
        r"Resource-expansion and maintenance-stress contrasts are excluded. Native resources and sizes differ, so the table is not an equal-area or equal-work ranking. "
        r"For the matched INT8 matrix, $U^{*}=N\mathrm{RI}^{*}$; this relation requires matching full-load and full-vector boundaries.",
        r"\end{minipage}",r"\end{table*}"]
    (OUT/"table_I_three_scenarios.tex").write_text("\n".join(tex)+"\n",encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=True);DATA.mkdir(exist_ok=True)
    document,groups,report=load_and_validate()
    export_data(document,groups);table=make_table(groups)
    from build_loglog import render_final
    from build_loglog_circles import circle_for
    scatter=render_final(groups,report)
    circles=render_final(groups,report,circle_specs=[circle_for(g) for g in groups],output_stem="rho_tau_loglog_circles")
    with PdfPages(OUT/"review_figures.pdf",metadata={"Title":"Table I and native-configuration rho-tau maps"}) as pdf:
        for fig in (table,scatter,circles):pdf.savefig(fig,bbox_inches="tight",pad_inches=.16)
    (DATA/"validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    plt.close("all")
    print("PASS: 10 native configurations / 30 sustainable scenarios / full-load and Table II identities / independent stage checks.")
    print(f"Figures: {OUT}")

if __name__=="__main__":main()
