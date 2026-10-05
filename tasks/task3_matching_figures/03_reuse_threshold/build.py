#!/usr/bin/env python3
"""Candidate C: full-native-load critical reuse, without changing source data."""
import sys
sys.dont_write_bytecode = True
import csv
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib import colors as mcolors
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
from interface import load_data, classify
from style import (apply_style, save_figure, COLORS, LABELS, MARKERS, INK,
                   MUTED, GRID, DOUBLE_COLUMN_IN, U_VALUES, U_LABELS)


def main():
    data = load_data()
    rows = data["hardware"]
    typical = {r["case_id"]: r for r in rows if r["profile"] == "reference"}
    order = sorted(typical, key=lambda cid: typical[cid]["U_star"])
    apply_style(8)
    fig, ax = plt.subplots(figsize=(DOUBLE_COLUMN_IN, 4.05))
    fig.subplots_adjust(left=.205, right=.875, bottom=.235, top=.81)
    ax.set_xscale("log")
    ax.set_xlim(.7, 1048576)
    ax.set_ylim(-.65, len(order)-.35)
    ax.invert_yaxis()
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.tick_params(axis="y", length=0, pad=8)
    ax.tick_params(axis="x", which="minor", length=0)
    ax.set_xticks([1, 10, 128, 1024, 16384, 131072, 1048576])
    ax.set_xticklabels(["1", "10", "128", "1K", "16K", "128K", "1M"])
    ax.set_yticks(range(len(order)))
    ax.set_yticklabels([LABELS[cid] for cid in order])
    for lab, cid in zip(ax.get_yticklabels(), order):
        lab.set_color(COLORS[cid])
    for u in U_VALUES:
        ax.axvline(u, color="#647583" if u == 128 else "#bdc5cc",
                   lw=1.05 if u == 128 else .65, ls=(0,(3,2)), zorder=0)
    for y in range(len(order)):
        ax.axhline(y, color=GRID, lw=.55, zorder=0)
    for cid in order:
        y = order.index(cid)
        rr = {r["profile"]: r for r in rows if r["case_id"] == cid}
        vals = [r["U_star"] for r in rr.values()]
        ax.plot([min(vals), max(vals)], [y,y], color=COLORS[cid], lw=1.4, zorder=2)
        # A small categorical row offset makes coincident true U* values visible.
        for profile, dy, size, face in [
            ("short", -.13, 25, "white"),
            ("long", .13, 25, mcolors.to_rgba(COLORS[cid], .32)),
            ("reference", 0, 43, COLORS[cid]),
        ]:
            ax.scatter([rr[profile]["U_star"]], [y+dy], s=size,
                       marker=MARKERS[cid], facecolors=face,
                       edgecolors=COLORS[cid], linewidths=.8, zorder=4)
        v=typical[cid]["U_star"]
        text=f"{v:,.1f}" if v<1000 else f"{v:,.0f}"
        ax.text(1.025, y, text, transform=ax.get_yaxis_transform(), va="center",
                ha="left", fontsize=7.6, color=COLORS[cid])
    ax.text(1.025, 1.035, "Typical $U^*$", transform=ax.transAxes,
            ha="left", va="bottom", fontsize=7.4, color=MUTED)
    ax.set_xlabel(r"Critical reuse $U^*=T_R/\Delta_S$ (vectors / full native load)", labelpad=6)
    fig.text(.025, .96, "C  |  Reuse needed to balance one full load", fontsize=10,
             weight="semibold", ha="left", va="top")
    fig.text(.205, .893, r"$U<U^*$: resident-bound    •    $U>U^*$: streaming-bound",
             fontsize=7.7, ha="left")
    handles=[Line2D([],[], color=MUTED, marker="o", ls="none", ms=4,
                    mfc="white", label="Short-time pair"),
             Line2D([],[], color=MUTED, marker="o", ls="none", ms=5,
                    mfc=MUTED, label="Typical pair"),
             Line2D([],[], color=MUTED, marker="o", ls="none", ms=4,
                    mfc="#c7cdd2", label="Long-time pair")]
    ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-.008, 1.028),
              ncol=3, frameon=False, handletextpad=.4, columnspacing=1.4,
              borderaxespad=0, fontsize=7)
    fig.text(.205,.066,"Dashed lines: Table II(a) reuse references  U = 1, 128, 1K, 128K", fontsize=7.3,
             color=MUTED, ha="left")
    fig.text(.205,.027,"MRAM at U = 128: short / typical / long = resident / resident / streaming", fontsize=7.2,
             color=INK, ha="left")
    save_figure(fig, HERE / "output" / "figure")
    plt.close(fig)

    out=[]
    for cid in order:
        for r in rows:
            if r["case_id"] != cid: continue
            record = {k:r[k] for k in ["case_id","label","profile","K","N","U_star","RI_star",
                                        "rho_MB_per_s","tau_MB_per_s","delta_S_ns","T_R_ns",
                                        "source_result","central_source"]}
            record.update({f"at_U_{u}":classify(u,r["U_star"]) for u in U_VALUES})
            out.append(record)
    (HERE / "data").mkdir(exist_ok=True)
    with (HERE / "data" / "plotted_thresholds.csv").open("w", newline="") as f:
        writer=csv.DictWriter(f,fieldnames=list(out[0])); writer.writeheader(); writer.writerows(out)
    mram=[r for r in out if r["case_id"]=="06_mram"]
    check={"shared_interface":"../shared/data.json", "formula":"U_star = T_R / delta_S = N * rho / tau",
           "reference_U":[1,128,1024,131072],"same_native_shape_scope":data["boundary"],
           "MRAM_U128":[{"profile":r["profile"],"U_star":r["U_star"],
                          "U_over_U_star":128/r["U_star"],"classification":r["at_U_128"]} for r in mram],
           "max_formula_relative_error":max(abs(r["U_star"]-r["T_R_ns"]/r["delta_S_ns"])/r["U_star"] for r in out),
           "figure_inches":[DOUBLE_COLUMN_IN,4.05],"threshold_row_order":order}
    (HERE / "data" / "validation.json").write_text(json.dumps(check,indent=2)+"\n")

if __name__ == "__main__":
    main()
