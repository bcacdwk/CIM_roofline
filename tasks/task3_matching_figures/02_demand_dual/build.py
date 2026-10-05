#!/usr/bin/env python3
"""Candidate B: two logical QKV demand planes and mapped native tile references.

Reads only ../shared. Writes only this candidate directory. No Task I/II
builder is imported or executed. Final plotted quantities are recorded in JSON.
"""
from __future__ import annotations
import json
import hashlib
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from interface import load_data, classify, qkv_mapping, mapped_hardware, mapped_workloads
from style import COLORS, LABELS, MARKERS, INK, MUTED, GRID, apply_style, save_figure, format_u, DOUBLE_COLUMN_IN
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator

MODELS = ("qwen35_2b", "mimo_v25_pro")
HARDWARE = ("01_sram_acim", "10_fenor_3d", "03_nor_2d")
U_VALUES = (1, 1024, 131072, 1048576)


def byte_label(x):
    for scale, suffix in ((2**30, "GiB"), (2**20, "MiB"), (2**10, "KiB")):
        if x >= scale:
            return f"{x / scale:g} {suffix}"
    return f"{x:g} B"


def axes_style(ax):
    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_xlim(2**20, 2**30)
    ax.set_ylim(2**10, 2**34)
    xticks = [2**20, 2**24, 2**28, 2**30]
    yticks = [2**10, 2**14, 2**18, 2**22, 2**26, 2**30, 2**34]
    ax.xaxis.set_major_locator(FixedLocator(xticks))
    ax.xaxis.set_major_formatter(FixedFormatter([byte_label(v) for v in xticks]))
    ax.yaxis.set_major_locator(FixedLocator(yticks))
    ax.yaxis.set_major_formatter(FixedFormatter([byte_label(v) for v in yticks]))
    ax.xaxis.set_minor_locator(NullLocator())
    ax.yaxis.set_minor_locator(NullLocator())
    ax.grid(which="major", color=GRID, linewidth=0.55)
    ax.set_axisbelow(True)
    ax.tick_params(length=2.5, pad=3)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.set_xlabel(r"Resident load $Q_R$ (Byte)", labelpad=6)
    ax.get_xticklabels()[-1].set_horizontalalignment("right")


def main():
    apply_style(font_size=8)
    data = load_data()
    fig, axs = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN_IN, 4.3), sharex=True, sharey=True)
    fig.subplots_adjust(left=0.100, right=0.981, bottom=0.28, top=0.800, wspace=0.14)
    fig.text(0.1, 0.976, "B | QKV demand and native-tile balance", fontsize=11, weight="semibold", va="top")
    fig.text(0.1, 0.910, "Logical traffic; each 128 × 128 tile loaded once, serves U vectors", fontsize=8, color=MUTED)
    plotted = {
        "candidate": "B", "figure_size_in": [DOUBLE_COLUMN_IN, 4.3],
        "shared_data_sha256": hashlib.sha256((HERE.parent / "shared/data.json").read_bytes()).hexdigest(),
        "axes": {"x": "logical Q_R Byte", "y": "logical Q_S Byte", "scales": "log2; common limits"},
        "boundary": "sequential complete-native-tile component service; QKV logical operator-stage demand",
        "formula": "Q_S=RI_star_effective*Q_R; RI_star_effective=RI_star/m_N=U_star/N_proj",
        "workloads": [], "rays": [], "classifications": [],
    }
    checks = []
    xline = np.geomspace(2**20, 2**30, 240)
    for panel_index, (ax, model) in enumerate(zip(axs, MODELS)):
        axes_style(ax)
        mapping = qkv_mapping(model)
        workloads = sorted(mapped_workloads(model), key=lambda x: x["U"])
        assert tuple(w["U"] for w in workloads) == U_VALUES
        ax.set_title(f"({chr(97 + panel_index)}) {mapping['model_label']}", loc="left", pad=14)
        ax.text(0.0, 1.017, f"D={mapping['D']:,}; N$_{{proj}}$={mapping['N_proj']:,}; load={byte_label(mapping['model_Q_R_Byte'])}",
                transform=ax.transAxes, fontsize=7.3, color=MUTED, va="bottom")
        qr = mapping["model_Q_R_Byte"]
        ys = [w["Q_S_Byte"] for w in workloads]
        ax.plot([qr, qr], [ys[0], ys[-1]], color=INK, linewidth=1.25, zorder=4)
        for h in HARDWARE:
            ray = mapped_hardware(model, h)
            ax.plot(xline, ray["RI_star_effective"] * xline, color=COLORS[h], linewidth=1.25, alpha=.9, zorder=2)
            # A symbol on the reference ray encodes medium identity. It is an
            # analytic point on the ray, not an extra hardware scenario.
            marker_x = 2**25 if h == "01_sram_acim" else 2**21.6
            marker_y = ray["RI_star_effective"] * marker_x
            if 2**10 < marker_y < 2**34:
                ax.plot(marker_x, marker_y, marker=MARKERS[h], markersize=5.5,
                        markeredgecolor=COLORS[h], markerfacecolor="white", linestyle="none", zorder=3)
            plotted["rays"].append({"model_id": model, "m_N": mapping["m_N"], **ray})
            assert math.isclose(ray["RI_star_effective"], ray["U_star"] / mapping["N_proj"], rel_tol=1e-12)
            assert math.isclose(ray["T_R_all_tiles_ns"] / ray["streaming_ns_per_model_vector"], ray["U_star"], rel_tol=1e-12)
            for ratio in (1 - 1e-8, 1, 1 + 1e-8):
                u = ray["U_star"] * ratio
                expected = "balanced" if ratio == 1 else ("resident-bound" if ratio < 1 else "streaming-bound")
                assert classify(u, ray["U_star"]) == expected
                checks.append({"model_id": model, "hardware": h, "threshold_multiplier": ratio, "classification": expected})
        for w in workloads:
            ax.scatter(w["Q_R_Byte"], w["Q_S_Byte"], s=22, marker="o", color=INK, edgecolor="white", linewidth=.55, zorder=6)
            # Labels sit beside the exact points; the point coordinates do not move.
            offset_y = 0
            ax.annotate(f"U={format_u(w['U'])}", xy=(w["Q_R_Byte"], w["Q_S_Byte"]),
                        xytext=(7, offset_y), textcoords="offset points", fontsize=7.6,
                        va="center", color=INK,
                        bbox={"facecolor": "white", "edgecolor": "none", "pad": .5, "alpha": .92}, zorder=7)
            plotted["workloads"].append(w)
            assert w["Q_R_Byte"] == mapping["D"] * mapping["N_proj"]
            assert w["Q_S_Byte"] == w["U"] * mapping["D"]
            assert w["native_accumulated_Q_S_Byte"] == mapping["m_N"] * w["Q_S_Byte"]
            for h in HARDWARE:
                ray = mapped_hardware(model, h)
                ratio_demand = w["Q_S_Byte"] / (ray["RI_star_effective"] * w["Q_R_Byte"])
                ratio_time = (w["U"] * ray["streaming_ns_per_model_vector"]) / ray["T_R_all_tiles_ns"]
                assert math.isclose(ratio_demand, w["U"] / ray["U_star"], rel_tol=1e-12)
                assert math.isclose(ratio_time, ratio_demand, rel_tol=1e-12)
                status = classify(w["U"], ray["U_star"])
                assert status == ("streaming-bound" if ratio_demand > 1 else "resident-bound")
                plotted["classifications"].append({
                    "workload_case_id": w["case_id"], "hardware_case_id": h,
                    "profile": "reference", "U": w["U"], "U_star": ray["U_star"],
                    "demand_above_ray_factor": ratio_demand, "component_T_S_over_T_R": ratio_time,
                    "bottleneck": status,
                })
    axs[0].set_ylabel(r"Cumulative streaming input $Q_S$ (Byte)", labelpad=7)
    handles = []
    for h in HARDWARE:
        row = mapped_hardware(MODELS[0], h)
        u = row["U_star"]
        u_text = f"{u:.2f}" if u < 10 else (f"{u:.1f}" if u < 1000 else f"{u / 1024:.1f}K")
        handles.append(Line2D([0], [0], color=COLORS[h], marker=MARKERS[h],
                              markerfacecolor="white", markersize=5, linewidth=1.3,
                              label=LABELS[h] + r" ($U^*=" + u_text + r"$)"))
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.55, .109), ncol=3,
               frameon=False, columnspacing=1.6, handlelength=2.1, handletextpad=.5, fontsize=7.6)
    fig.text(.55, .083, "Typical hardware references • ray: Q$_S$ = RI*$_{eff}$ Q$_R$", ha="center", fontsize=7.4, color=MUTED)
    fig.text(.55, .041, "Above each ray: streaming-bound   |   Below each ray: resident-bound", ha="center", fontsize=7.8, color=INK)
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for ax in axs:
        for tick in ax.get_xticklabels():
            box = tick.get_window_extent(renderer)
            assert box.x0 >= 0 and box.x1 <= fig.bbox.width
    save_figure(fig, HERE / "output/figure")
    plt.close(fig)
    (HERE / "plotted_data.json").write_text(json.dumps(plotted, indent=2, ensure_ascii=False) + "\n")
    validation = {
        "status": "pass", "workload_points": len(plotted["workloads"]),
        "mapped_hardware_rays": len(plotted["rays"]),
        "cross_plane_and_component_time_checks": len(plotted["classifications"]),
        "threshold_neighborhood_checks": checks,
        "model_Q_R_ratio": qkv_mapping(MODELS[1])["model_Q_R_Byte"] / qkv_mapping(MODELS[0])["model_Q_R_Byte"],
        "model_Q_S_ratio_at_same_U": qkv_mapping(MODELS[1])["D"] / qkv_mapping(MODELS[0])["D"],
        "effective_ray_slope_ratio_Qwen_over_MiMo": qkv_mapping(MODELS[1])["m_N"] / qkv_mapping(MODELS[0])["m_N"],
        "x_tick_bboxes_inside_figure": True, "visual_review": "supervisor_reviewed", "figure_size_in": [DOUBLE_COLUMN_IN, 4.3],
    }
    (HERE / "validation.json").write_text(json.dumps(validation, indent=2, ensure_ascii=False) + "\n")
    print("PASS: 8 exact QKV demand points, 6 mapped rays, 24 cross-plane/time classifications; PNG/PDF/SVG saved.")


if __name__ == "__main__":
    main()
