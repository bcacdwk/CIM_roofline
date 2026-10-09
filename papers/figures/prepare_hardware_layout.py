"""Compact two-panel Fig.3: accepted throughputs and native storage references.

Reads the accepted points and circle geometry. Keeps the original axis metrics,
colors, 30 point coordinates, pairings, circles, and equal log scale. The paper
viewport uses user-requested tighter limits. Writes only here.
The lower strip reads accepted footprint results and sorts density only.
The unmodified throughput vector source is retained as hardware_capacities.pdf.
"""
from pathlib import Path
import csv
import argparse
import hashlib
import os
import json
import math
import sys
sys.dont_write_bytecode = True
os.environ.setdefault("MPLCONFIGDIR", str(Path.home()/".cache/cim-roofline/matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import LogLocator, LogFormatterMathtext, NullLocator
from matplotlib.colors import to_rgb
import numpy as np
from figure_labels import TECHNOLOGY_LABELS

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--output-dir", type=Path, default=HERE)
args = parser.parse_args()
OUT = args.output_dir
OUT.mkdir(parents=True, exist_ok=True)
FOOTPRINT = HERE.parents[1] / "tasks/archived/task1_table_I_NeuroSim/analysis/12_footprint/results/footprint_results.json"
SOURCE = HERE.parents[1] / "tasks/task1_table_I_NVM/analysis/11_summary_figures/data"
meta = json.loads((SOURCE / "rho_tau_loglog_circles_validation.json").read_text())
with (SOURCE / "rho_tau_loglog_circles_points.csv").open(encoding="utf-8-sig") as f:
    rows = list(csv.DictReader(f))
ids = list(dict.fromkeys(r["case_id"] for r in rows))
colors = ["#2d63ad", "#6e52a2", "#a37622", "#68737d", "#c54e55",
          "#178276", "#ca6b2b", "#338fa5", "#7b8736", "#ad5390"]
labels = [TECHNOLOGY_LABELS[cid] for cid in ids]
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                     "pdf.fonttype": 42, "mathtext.fontset": "dejavusans",
                     "hatch.linewidth": .25})
# Keep 0.15 decades of breathing room beyond the outer x-axis decade ticks.
# The vertical viewport is exactly 10^0--10^3; do not squash the log geometry.
xlim, ylim = (10**-2.15, 10**4.15), (1.0, 1000.0)
sx, sy = [math.log10(b / a) for a, b in (xlim, ylim)]
fw = 7.16
left, right, top = .55, .55, .08
aw = fw - left - right
ah = aw * sy / sx
fh = 4.28
bottom = fh - top - ah
fig = plt.figure(figsize=(fw, fh))
ax = fig.add_axes([left/fw, bottom/fh, aw/fw, ah/fh])
ax.set(xscale="log", yscale="log", xlim=xlim, ylim=ylim)
ax.set_aspect("equal", adjustable="box")
ax.set_xlabel(r"Resident throughput $\tau$ [MB/s]", fontsize=8.5, labelpad=3, color="#000000")
ax.set_ylabel(r"Streaming throughput $\rho$ [MB/s]", fontsize=8.5, labelpad=3, color="#000000")
for axis in (ax.xaxis, ax.yaxis):
    axis.set_major_locator(LogLocator(base=10, numticks=12))
    axis.set_major_formatter(LogFormatterMathtext(base=10))
    axis.set_minor_locator(NullLocator())
ax.tick_params(labelsize=7.5, length=3, pad=2, colors="#000000")
for side, spine in ax.spines.items():
    spine.set_color("#000000" if side in ("left", "bottom") else "#82909c")
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
    a = ax.text(1, 1, text, fontsize=7.0, color="#637b8d", rotation=45,
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
# Independent native binary cell/tile references, sorted only by absolute density.
from matplotlib.patches import Patch
footprint = json.loads(FOOTPRINT.read_text())["main_rows"]
assert len(footprint) == 10 and {r["case_id"] for r in footprint} == set(ids)
footprint = sorted(footprint, key=lambda r: -r["density_Mbit_mm2"])
color_by_id = dict(zip(ids, colors))
short_labels = TECHNOLOGY_LABELS
bar_bottom, bar_height = .15, .70
bar_width = aw - .04  # Reserve space for the enlarged right-axis title.
axd = fig.add_axes([left/fw, bar_bottom/fh, bar_width/fw, bar_height/fh])
axa = axd.twinx()
axd.set_yscale("log"); axa.set_yscale("log")
axd.set_ylim(1e-2, 1e5); axa.set_ylim(1e-2, 1e4)
axd.set_yticks([1e-2, 1e1, 1e4]); axa.set_yticks([1e-2, 1e1, 1e4])
for axis in (axd.yaxis, axa.yaxis):
    axis.set_major_formatter(LogFormatterMathtext(base=10))
    axis.set_minor_locator(NullLocator())
axd.set_ylabel("Density ↑\n[Mbit/mm²]", fontsize=7.5, labelpad=1)
axa.set_ylabel("Footprint ↓\n"+r"[$F_{\mathrm{mem}}^2$/bit]", fontsize=7.5, labelpad=1)
x = np.arange(10); bw=.32; pair_gap=.06
for i,r in enumerate(footprint):
    color=color_by_id[r["case_id"]]
    light_color=tuple(.52*channel+.48 for channel in to_rgb(color))
    axd.bar(i-(bw+pair_gap)/2, r["density_Mbit_mm2"]-1e-2, bottom=1e-2, width=bw,
            color=color, edgecolor="none", linewidth=0, zorder=3)
    axa.bar(i+(bw+pair_gap)/2, r["alpha_F_mem2_per_bit"]-1e-2, bottom=1e-2, width=bw,
            facecolor=light_color, edgecolor=color, hatch="------", linewidth=0, zorder=4)
axd.set_xlim(-.6,9.6)
axd.set_xticks(x,[short_labels[r["case_id"]] for r in footprint],fontsize=7.5)
axd.tick_params(axis="x",length=0,pad=2)
for a in (axd,axa):
    a.tick_params(axis="y",labelsize=7.5,length=2,pad=1,colors="#000000")
    for label in a.get_yticklabels():
        label.set_fontweight("normal")
        label.set_color("#000000")
    for sp in a.spines.values(): sp.set_color("#82909c"); sp.set_linewidth(.5)
    a.spines["top"].set_visible(False)
axd.set_axisbelow(True); axd.grid(axis="y",color="#e3e9ee",linewidth=.4)
axd.legend(handles=[Patch(facecolor="#657382",edgecolor="none",label="D: left axis"),
                    Patch(facecolor="#afb8c0",edgecolor="#657382",hatch="------",linewidth=0,label="α: right axis")],
           loc="upper right",bbox_to_anchor=(.995,1.25),ncol=2,frameon=False,
           fontsize=6.0,handlelength=1.4,columnspacing=.9,borderaxespad=0,handletextpad=.4)
ax.text(.01,.985,"(a)",transform=ax.transAxes,ha="left",va="top",fontsize=8,weight="bold")
axd.text(.01,1.01,"(b)",transform=axd.transAxes,ha="left",va="bottom",fontsize=7,weight="bold",
         bbox=dict(facecolor="white",edgecolor="none",pad=.2),zorder=7)
fig.canvas.draw()
assert math.isclose(ax.get_window_extent().width/sx,ax.get_window_extent().height/sy,rel_tol=1e-8)
validation={"throughput_point_count":len(dots),"throughput_points":dots,"circle_geometry":meta["scenario_circles"],
    "xlim":xlim,"ylim":ylim,"equal_log_scale":True,"figure_inches":[fw,fh],"upper_axes_inches":[left,bottom,aw,ah],
    "storage_axes_inches":[left,bar_bottom,bar_width,bar_height],"storage_order":[r["case_id"] for r in footprint],
    "storage_labels":[short_labels[r["case_id"]] for r in footprint],
    "storage_bar_style":{"density":"solid device color","footprint":"light tint with fine horizontal rules","hatch":"------","hatch_linewidth_pt":.25,"within_pair_gap":pair_gap},
    "storage_y_tick_style":{"color":"#000000","weight":"normal","font_size_pt":7.5},
    "storage_values":[{"case_id":r["case_id"],"density":r["density_Mbit_mm2"],"alpha":r["alpha_F_mem2_per_bit"],"color":color_by_id[r["case_id"]]} for r in footprint],
    "source_sha256":{str(f.relative_to(HERE.parents[1])):hashlib.sha256(f.read_bytes()).hexdigest() for f in [SOURCE/"rho_tau_loglog_circles_points.csv",SOURCE/"rho_tau_loglog_circles_validation.json",FOOTPRINT]}}
for ext in ("pdf","png","svg"):
    fig.savefig(OUT/("hardware_capacities_paper."+ext),dpi=220)
(OUT/"hardware_capacities_layout_checks.json").write_text(json.dumps(validation,indent=2)+"\n")
print(f"30 original points retained; 20 native-storage bars; equal log scale; size={fw} x {fh} in.")
