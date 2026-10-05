#!/usr/bin/env python3
"""Analytic one-route scaling at real native hardware/reuse reference states."""
from __future__ import annotations
import hashlib
import json
import math
import sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from interface import get_hardware, bound_MB_per_s, classify, native_demand
from style import apply_style, save_figure, COLORS, LABELS, MARKERS, INK, MUTED, GRID, DOUBLE_COLUMN_IN, format_u
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
import numpy as np

CASES = (("05_rram", 128), ("06_mram", 128), ("06_mram", 1024))


def main():
    apply_style(8)
    fig, axs = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN_IN, 4.15), sharex=True, sharey=True)
    fig.subplots_adjust(left=.076, right=.988, bottom=.35, top=.78, wspace=.17)
    fig.text(.076, .975, "E | Improve the route that limits the bound", fontsize=11, weight="semibold", va="top")
    fig.text(.076, .905, "Analytic capability scaling at three native full-load service states", fontsize=8, color=MUTED)
    plot = {"candidate": "E", "figure_size_in": [DOUBLE_COLUMN_IN, 4.15],
            "formula": "gain(a,b) = min(a*rho,b*tau*U/N)/min(rho,tau*U/N)",
            "factor_range": [1,16], "factor_semantics": "analytic capability multiplier; not equal engineering cost",
            "shared_data_sha256": hashlib.sha256((HERE.parent / "shared/data.json").read_bytes()).hexdigest(),
            "cases": []}
    base_factors = np.geomspace(1, 16, 257)
    for i, (ax, (case_id, U)) in enumerate(zip(axs, CASES)):
        h = get_hardware(case_id)
        base = bound_MB_per_s(h, U)
        status = classify(U, h["U_star"])
        exact_knee = max(h["U_star"]/U, U/h["U_star"])
        factors = np.unique(np.r_[base_factors, 2.0, exact_knee])
        stream_gain = np.array([bound_MB_per_s(h, U, streaming_factor=float(f))/base for f in factors])
        resident_gain = np.array([bound_MB_per_s(h, U, resident_factor=float(f))/base for f in factors])
        limit = h["U_star"]/U if status == "resident-bound" else U/h["U_star"]
        assert limit >= 1
        assert math.isclose(bound_MB_per_s(h, U, streaming_factor=1), base, rel_tol=1e-12)
        assert math.isclose(bound_MB_per_s(h, U, resident_factor=1), base, rel_tol=1e-12)
        for f, s, r in zip(factors, stream_gain, resident_gain):
            expected_s = 1.0 if status == "resident-bound" else min(float(f), limit)
            expected_r = min(float(f), limit) if status == "resident-bound" else 1.0
            assert math.isclose(float(s), expected_s, rel_tol=1e-12)
            assert math.isclose(float(r), expected_r, rel_tol=1e-12)
        ax.set_xscale("log", base=2)
        ax.set_xlim(.95, 17)
        ax.set_ylim(.78, 8.5)
        ax.xaxis.set_major_locator(FixedLocator([1,2,4,8,16]))
        ax.xaxis.set_major_formatter(FixedFormatter(["1×","2×","4×","8×","16×"]))
        ax.xaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_major_locator(FixedLocator([1,2,4,6,8]))
        ax.yaxis.set_major_formatter(FixedFormatter(["1×","2×","4×","6×","8×"]))
        ax.grid(axis="y", color=GRID, linewidth=.55)
        ax.set_axisbelow(True)
        ax.tick_params(length=2.5, pad=3)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        title = f"({chr(97+i)}) {LABELS[case_id]}, U={format_u(U)}"
        ax.set_title(title, loc="left", pad=20, fontsize=8.5)
        subtitle = ("Resident-bound" if i == 0 else ("Near balance (resident-bound)" if i == 1 else "Streaming-bound"))
        ax.text(0, 1.056, subtitle, transform=ax.transAxes, fontsize=7.2, color=MUTED, va="bottom")
        ax.axvline(2, color="#bcc5ce", linestyle=(0,(1,2)), linewidth=.8, zorder=1)
        # Solid = streaming route; dashed = resident route. Hue is the medium.
        ax.plot(factors, stream_gain, color=COLORS[case_id], linewidth=1.6, zorder=3)
        ax.plot(factors, resident_gain, color=COLORS[case_id], linewidth=1.6, linestyle=(0,(4,2)), zorder=4)
        sg2 = bound_MB_per_s(h, U, streaming_factor=2)/base
        rg2 = bound_MB_per_s(h, U, resident_factor=2)/base
        ax.plot(2, sg2, marker=MARKERS[case_id], color=COLORS[case_id], markeredgecolor="white", markeredgewidth=.45, markersize=5.8, linestyle="none", zorder=6)
        ax.plot(2, rg2, marker=MARKERS[case_id], color=COLORS[case_id], markerfacecolor="white", markersize=5.8, linestyle="none", zorder=7)
        if i == 0:
            ax.annotate(f"Resident gain caps at {limit:.2f}×", xy=(limit, limit), xytext=(1.18,4.8),
                        fontsize=7.1, color=INK, arrowprops={"arrowstyle":"-", "color":MUTED,"lw":.7})
        elif i == 1:
            ax.annotate(f"Resident gain caps at {limit:.2f}×", xy=(2,limit), xytext=(1.12,3.3),
                        fontsize=7.1, color=INK, arrowprops={"arrowstyle":"-", "color":MUTED,"lw":.7})
        else:
            ax.annotate(f"Gain cap: {limit:.2f}×", xy=(limit,limit), xytext=(1.13,8.03),
                        fontsize=7.1, color=INK, arrowprops={"arrowstyle":"-", "color":MUTED,"lw":.7})
        ax.set_xlabel("Capability multiplier", labelpad=5)
        panel_center = (ax.get_position().x0 + ax.get_position().x1) / 2
        fig.text(panel_center, .219, f"2× streaming → {sg2:.2f}× gain", fontsize=7.1, color=INK, ha="center")
        fig.text(panel_center, .182, f"2× resident → {rg2:.2f}× gain", fontsize=7.1, color=INK, ha="center")
        plot["cases"].append({"hardware_case_id":case_id, "profile":"reference", "U":U,
            "native_demand":native_demand(h,U), "hardware":h,
            "baseline_bound_MB_per_s":base, "baseline_bottleneck":status,
            "bottleneck_route_capability_multiplier_at_balance":limit,
            "gain_ceiling_for_improving_bottleneck_route":limit,
            "gain_at_2x":{"streaming_only":sg2,"resident_only":rg2},
            "factor":factors.tolist(),"streaming_only_gain":stream_gain.tolist(),"resident_only_gain":resident_gain.tolist()})
    axs[0].set_ylabel("Gain in two-route upper bound", labelpad=5)
    handles = [Line2D([0],[0],color=INK,linewidth=1.6,label=r"Streaming only: $\rho \to f\rho$"),
               Line2D([0],[0],color=INK,linewidth=1.6,linestyle=(0,(4,2)),label=r"Resident only: $\tau \to f\tau$")]
    fig.legend(handles=handles, loc="lower center", bbox_to_anchor=(.55,.083), ncol=2, frameon=False,
               fontsize=7.7, columnspacing=2.3, handlelength=2.7)
    fig.text(.55,.023,"Single-route upper-bound gains; capability factors do not represent equal cost",ha="center",fontsize=7.3,color=MUTED)
    save_figure(fig,HERE/"output/figure")
    plt.close(fig)
    (HERE/"plotted_data.json").write_text(json.dumps(plot,ensure_ascii=False,indent=2)+"\n")
    validation={"status":"pass","analytic_curve_values_checked":sum(2*len(c["factor"]) for c in plot["cases"]),
                "baseline_value_checks":len(CASES)*2,
                "cases":[{k:v for k,v in c.items() if k not in ["hardware","factor","streaming_only_gain","resident_only_gain"]} for c in plot["cases"]],
                "visual_review":"supervisor_reviewed", "figure_size_in": [DOUBLE_COLUMN_IN, 4.15]}
    (HERE/"validation.json").write_text(json.dumps(validation,ensure_ascii=False,indent=2)+"\n")
    print("PASS: 3 real reference states, exact analytic curves; PNG/PDF/SVG saved.")


if __name__ == "__main__": main()
