"""Paper-size typography for the accepted Task I plot; no service recalculation.

Reads the accepted points and circle geometry. Keeps the original axis metrics,
colors, 30 point coordinates, pairings, circles, and equal log scale. The paper
viewport uses user-requested tighter limits. Writes only here.
The unmodified vector source is retained as hardware_capacities.pdf.
"""
from pathlib import Path
import csv
import json
import math
import sys
sys.dont_write_bytecode = True
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext, NullLocator
import numpy as np
from figure_labels import TECHNOLOGY_LABELS

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parents[1] / "tasks/task1_table_I_NVM/analysis/11_summary_figures/data"
meta = json.loads((SOURCE / "rho_tau_loglog_circles_validation.json").read_text())
with (SOURCE / "rho_tau_loglog_circles_points.csv").open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
ids = list(dict.fromkeys(r["case_id"] for r in rows))
colors = ["#2d63ad", "#6e52a2", "#a37622", "#68737d", "#c54e55",
          "#178276", "#ca6b2b", "#338fa5", "#7b8736", "#ad5390"]
labels = [TECHNOLOGY_LABELS[cid] for cid in ids]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "pdf.fonttype": 42, "mathtext.fontset": "dejavusans"})
# Keep 0.15 decades of breathing room beyond the outer x-axis decade ticks.
# The vertical viewport is exactly 10^0--10^3; do not squash the log geometry.
xlim, ylim = (10**-2.15, 10**4.15), (1.0, 1000.0)
sx, sy = [math.log10(b / a) for a, b in (xlim, ylim)]
fw = 7.16
left, bottom, right, top = .58, .43, .10, .12
aw = fw - left - right
ah = aw * sy / sx
fh = ah + bottom + top
fig = plt.figure(figsize=(fw, fh))
ax = fig.add_axes([left/fw, bottom/fh, aw/fw, ah/fh])
ax.set(xscale="log", yscale="log", xlim=xlim, ylim=ylim)
ax.set_aspect("equal", adjustable="box")
ax.set_xlabel(r"Resident throughput $\tau$ [MB/s]", fontsize=8.5, labelpad=3)
ax.set_ylabel(r"Streaming throughput $\rho$ [MB/s]", fontsize=8.5, labelpad=3)
for axis in (ax.xaxis, ax.yaxis):
    axis.set_major_locator(LogLocator(base=10, numticks=12))
    axis.set_major_formatter(LogFormatterMathtext(base=10))
    axis.set_minor_locator(NullLocator())
ax.tick_params(labelsize=7.5, length=3, pad=2, colors="#657382")
for spine in ax.spines.values():
    spine.set_color("#82909c")
    spine.set_linewidth(.6)
ax.grid(color="#e3e9ee", linewidth=.5)
xx = np.geomspace(*xlim, 1000)
ax.fill_between(xx, np.clip(xx, *ylim), ylim[1], color="#fbf8f3", zorder=0)
ax.fill_between(xx, ylim[0], np.clip(xx, *ylim), color="#f3f8fb", zorder=0)
for ratio in (.01, 1, 100):
    yy = ratio * xx
    valid = (yy >= ylim[0]) & (yy <= ylim[1])
    ax.plot(xx[valid], yy[valid], color="#28465e" if ratio == 1 else "#718594",
            lw=1 if ratio == 1 else .6, ls=(0, (5, 4)), zorder=2)
dots = []
for i, cid in enumerate(ids):
    group = {r["profile"]: r for r in rows if r["case_id"] == cid}
    ref = group["reference"]
    circle = next(s for s in meta["scenario_circles"] if s["case_id"] == cid)
    theta = np.linspace(0, 2*np.pi, 1441)
    xy = 10 ** (np.array(circle["center_log10"])[:, None]
               + circle["radius_decades"] * np.array([np.cos(theta), np.sin(theta)]))
    ax.fill(*xy, color=colors[i], alpha=.065, zorder=1)
    ax.plot(*xy, color=colors[i], alpha=.83, lw=.7, ls=(0, (5, 3.2)), zorder=3)
    for profile, row in group.items():
        x, y = float(row["tau"]), float(row["rho"])
        if profile != "reference":
            ax.plot([float(ref["tau"]), x], [float(ref["rho"]), y],
                    color=colors[i], alpha=.65, lw=.55, zorder=4)
        assert xlim[0] <= x <= xlim[1] and ylim[0] <= y <= ylim[1]
        point = ax.scatter(x, y, s=35 if profile == "reference" else 10,
                           c=colors[i], edgecolors="white", linewidths=.5,
                           clip_on=False, zorder=6)
        assert np.array_equal(point.get_offsets().data[0], [x, y])
        dots.append((x, y))

# Only labels move. The accepted point coordinates and circle geometry do not.
fig.canvas.draw()
renderer = fig.canvas.get_renderer()
bounds = ax.get_window_extent()
occupied = []
dot_pixels = [ax.transData.transform(p) for p in dots]
def free(box):
    box = box.padded(2)
    if not (bounds.contains(box.x0, box.y0) and bounds.contains(box.x1, box.y1)):
        return False
    if any(box.overlaps(b) for b in occupied):
        return False
    return all(math.hypot(x-np.clip(x, box.x0, box.x1), y-np.clip(y, box.y0, box.y1)) > 5
               for x, y in dot_pixels)

for i in [9, 7, 8, 5, 0, 1, 2, 3, 4, 6]:
    row = next(r for r in rows if r["case_id"] == ids[i] and r["profile"] == "reference")
    value = format(float(format(float(row["RI_star"]), ".2g")), "g")
    label = labels[i] + "\n" + r"$\mathrm{SI}^{*}=" + value + "$"
    a = ax.annotate(label, (float(row["tau"]), float(row["rho"])), xytext=(0, 0), textcoords="offset points",
                    fontsize=7.5, color=colors[i], weight="medium", linespacing=1.05,
                    bbox=dict(facecolor="white", edgecolor="none", alpha=.94, pad=.45), zorder=8)
    candidates = []
    for distance in (8, 14, 22, 32, 45):
        candidates += [(0, -distance, "center", "top"), (0, distance, "center", "bottom"),
                       (distance, 0, "left", "center"), (-distance, 0, "right", "center")]
        candidates += [(dx, dy, ha, va) for dx, ha in ((distance, "left"), (-distance, "right"))
                       for dy, va in ((distance*.7, "bottom"), (-distance*.7, "top"))]
    for dx, dy, ha, va in candidates:
        a.set_position((dx, dy)); a.set_ha(ha); a.set_va(va)
        box = a.get_window_extent(renderer)
        if free(box):
            occupied.append(box.padded(2)); break
    else:
        raise RuntimeError("No label placement: " + row["case_id"])
for ratio in (1, 100, .01):
    text = r"$\rho=\tau\ (\mathrm{SI}^{*}=1)$" if ratio == 1 else r"$\mathrm{SI}^{*}=10^{"+str(int(math.log10(ratio)))+"}$"
    a = ax.text(1, 1, text, fontsize=7.5, color="#637b8d", rotation=45,
                rotation_mode="anchor", bbox=dict(facecolor="white", edgecolor="none", alpha=.92, pad=.4), zorder=5)
    lo = max(math.log10(xlim[0]), math.log10(ylim[0]/ratio)) + .05
    hi = min(math.log10(xlim[1]), math.log10(ylim[1]/ratio)) - .15
    candidates = [(t, shift) for shift in (1.14, 1.4, .8, .65)
                  for t in np.linspace(hi, lo, 150)]
    for t, shift in candidates:
        a.set_position((10**t, ratio*10**t*shift))
        box = a.get_window_extent(renderer)
        if free(box):
            occupied.append(box.padded(2)); break
    else:
        raise RuntimeError(f"No guide-label placement for RI*={ratio}")
assert len(dots) == 30
assert math.isclose(bounds.width/sx, bounds.height/sy, rel_tol=1e-8)
fig.savefig(HERE / "hardware_capacities_paper.pdf")
fig.savefig(HERE / "hardware_capacities_paper.png", dpi=180)
print(f"30 original points retained; x={xlim}, y={ylim}; original circles/colors, equal log scale; height={fh:.3f} in.")
