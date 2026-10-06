"""Single-column Fig.4 from accepted Task III thresholds; layout changes only.

The original double-column vector remains in critical_reuse.pdf. Read-only
source data and style come from Task III; every output is inside papers/.
"""
from pathlib import Path
import csv
import importlib.util
import sys
sys.dont_write_bytecode = True

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.colors import to_rgba
from matplotlib.ticker import NullLocator
import numpy as np
from figure_labels import TECHNOLOGY_LABELS

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks/task3_matching_figures"
spec = importlib.util.spec_from_file_location("task3_readonly_style", TASK / "shared/style.py")
style = importlib.util.module_from_spec(spec)
spec.loader.exec_module(style)
with (TASK / "03_reuse_threshold/data/plotted_thresholds.csv").open() as f:
    rows = list(csv.DictReader(f))
typical = {r["case_id"]: r for r in rows if r["profile"] == "reference"}
order = sorted(typical, key=lambda cid: float(typical[cid]["U_star"]))
assert len(rows) == 30 and len(order) == 10

style.apply_style(7.5)
fig = plt.figure(figsize=(3.5, 2.55))
# A single label column; typical values sit beside the plotted scenario group.
left, right, bottom, top = .67, .05, .40, .26
ax = fig.add_axes([left/3.5, bottom/2.55, (3.5-left-right)/3.5,
                   (2.55-bottom-top)/2.55])
ax.set(xscale="log", xlim=(.72, 450000), ylim=(9.55, -.55))
for side in ("left", "top", "right"):
    ax.spines[side].set_visible(False)
ax.xaxis.set_minor_locator(NullLocator())
ax.set_xticks([1, 128, 1024, 131072])
ax.set_xticklabels(["1", "128", "1K", "128K"], fontsize=7.5)
ax.tick_params(axis="x", length=3, pad=3)
ax.tick_params(axis="y", length=0, pad=3)
ax.set_yticks(range(10))
labels = [TECHNOLOGY_LABELS[cid] for cid in order]
ax.set_yticklabels(labels, fontsize=6.5)
for tick, cid in zip(ax.get_yticklabels(), order):
    tick.set_color(style.COLORS[cid])
for u in (1, 128, 1024, 131072):
    # These are illustrative workload reuse counts, not universal ridges.
    ax.axvline(u, color="#c2c9cf", lw=.5, ls=(0, (3, 2)), zorder=0)
for y in range(10):
    ax.axhline(y, color=style.GRID, lw=.5, zorder=0)

value_anchors = []
plotted = []
for y, cid in enumerate(order):
    group = {r["profile"]: r for r in rows if r["case_id"] == cid}
    vals = [float(r["U_star"]) for r in group.values()]
    ax.plot([min(vals), max(vals)], [y, y], color=style.COLORS[cid], lw=1.1, zorder=2)
    for profile, dy, size, face in [
        ("short", -.22, 13, "white"),
        ("long", .22, 13, to_rgba(style.COLORS[cid], .28)),
        ("reference", 0, 23, style.COLORS[cid]),
    ]:
        x = float(group[profile]["U_star"])
        marker = ax.scatter(x, y+dy, s=size, marker=style.MARKERS[cid],
                            facecolors=face, edgecolors=style.COLORS[cid],
                            linewidths=.7, zorder=4)
        assert marker.get_offsets()[0, 0] == x
        plotted.append((cid, profile, x))
    v = float(group["reference"]["U_star"])
    text = f"{v:,.1f}" if v < 1000 else f"{v:,.0f}"
    value_anchors.append((y, vals, text, style.COLORS[cid]))

# Full-size, seven-point numeric labels replace the old right-hand value column.
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
bounds = ax.get_window_extent()
for label in ax.get_yticklabels():
    box = label.get_window_extent(renderer)
    assert box.x0 >= 0 and box.x1 < bounds.x0, label.get_text()
for y, vals, text, color in value_anchors:
    label = ax.annotate(text, (max(vals), y), xytext=(5, 0), textcoords="offset points",
                        ha="left", va="center", fontsize=7, color=color,
                        bbox=dict(facecolor="white", edgecolor="none", pad=.25), zorder=5)
    if label.get_window_extent(renderer).x1 > bounds.x1-1:
        label.xy = (min(vals), y)
        label.set_position((-5, 0))
        label.set_ha("right")
    box = label.get_window_extent(renderer)
    assert bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1)

handles = [
    Line2D([], [], ls="none", marker="o", ms=3.6, color=style.MUTED, mfc="white", label="Short"),
    Line2D([], [], ls="none", marker="o", ms=4.3, color=style.MUTED, mfc=style.MUTED, label="Typical"),
    Line2D([], [], ls="none", marker="o", ms=3.6, color=style.MUTED, mfc="#c7cdd2", label="Long"),
]
ax.legend(handles=handles, loc="lower left", bbox_to_anchor=(-.015, 1.015),
          ncol=3, frameon=False, fontsize=7, handletextpad=.35, columnspacing=.8,
          borderaxespad=0, handlelength=.8)
ax.set_xlabel(r"Critical reuse $U^*$ [vectors/load]", fontsize=7.5, labelpad=4)
ax.text(.985, .96,
        r"Native $W[N,K]$" + "\n" + r"$U^*=N\,\mathrm{RI}^*$" + "\n"
        + r"$U=128$: example",
        transform=ax.transAxes, ha="right", va="top", fontsize=6.5,
        linespacing=1.25, color=style.MUTED,
        bbox=dict(facecolor="white", edgecolor="none", pad=1.5), zorder=6)

assert len(plotted) == 30
for _, _, x in plotted:
    assert ax.get_xlim()[0] < x < ax.get_xlim()[1]
fig.savefig(HERE / "critical_reuse_single.pdf")
preview = HERE.parent / "build/critical_reuse_single.png"
preview.parent.mkdir(exist_ok=True)
fig.savefig(preview, dpi=240)
print("Single-column Fig.4: 3.5 x 2.55 in; all 30 original thresholds, paired scenarios, and colors retained.")
