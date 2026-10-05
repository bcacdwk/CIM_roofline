#!/usr/bin/env python3
"""Capability/reuse overlay; reads the frozen Task III interface only."""
from __future__ import annotations
import json
import math
import sys
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
from interface import load_data, classify
from style import CASE_ORDER, COLORS, MARKERS, LABELS, apply_style, save_figure


def circle(group):
    a, b, p = [np.log10([group[k]["tau_MB_per_s"], group[k]["sigma_MB_per_s"]])
               for k in ("short", "long", "reference")]
    m, d = (a+b)/2, b-a
    c = p - np.dot(p-m, d)/np.dot(d, d)*d
    radius = float(np.linalg.norm(a-c))
    assert math.isclose(radius, float(np.linalg.norm(b-c)), rel_tol=1e-12)
    assert np.linalg.norm(p-c) <= radius+1e-12
    return c, radius


def main():
    apply_style(8.4)
    data = load_data()
    groups = {case: {r["profile"]: r for r in data["hardware"] if r["case_id"] == case}
              for case in CASE_ORDER}
    # Equal displayed length per log decade: width / x span = height / y span.
    fig = plt.figure(figsize=(7.16, 4.35))
    xlog, ylog = (-2.7, 4.35), (1.72, 5.17)
    left, width = .096, .862
    height = width*7.16/(xlog[1]-xlog[0])*(ylog[1]-ylog[0])/4.35
    ax = fig.add_axes([left, .213, width, height])
    ax.set_xscale("log"); ax.set_yscale("log")
    ax.set_xlim(10**xlog[0],10**xlog[1]); ax.set_ylim(10**ylog[0],10**ylog[1])
    ax.grid(which="major", color="#e5eaf0", lw=.45)
    ax.tick_params(which="minor", length=2)
    ax.set_xlabel(r"Resident update capacity, $\tau$ (MB/s)", labelpad=5)
    ax.set_ylabel(r"Matrix-equivalent streaming capacity, $\sigma=N\rho$ (MB/s)", labelpad=4)
    xx=np.logspace(*xlog,1000)
    # One emphasized demand reference; no fixed background pretending to classify all U.
    styles = {1:(0,(1,2)),128:"-",1024:(0,(5,2)),131072:(0,(5,2,1,2))}
    for U in (1,128,1024,131072):
        ax.plot(xx,U*xx,color="#334c61" if U==128 else "#a2aab2",
                lw=1.2 if U==128 else .75, ls=styles[U], zorder=1)

    # Labels use empty whitespace; positions never alter hardware points.
    offsets = {
        "01_sram_acim":(8,-39), "02_sram_dcim":(2,36),
        "03_nor_2d":(-17,29), "04_nand_3d":(-5,-31),
        "05_rram":(-31,20), "06_mram":(-5,43),
        "07_pcm":(-24,-27), "08_feram_hfo2":(42,-2),
        "09_gain_cell_edram":(34,-28), "10_fenor_3d":(-60,10),
    }
    plotted=[]; circles=[]; text_artists=[]
    for case in CASE_ORDER:
        g=groups[case]; color=COLORS[case]; center,radius=circle(g)
        angle=np.linspace(0,2*np.pi,361)
        xy=10**(center[:,None]+radius*np.array([np.cos(angle),np.sin(angle)]))
        ax.fill(xy[0],xy[1],color=color,alpha=.055,zorder=1.2)
        ax.plot(xy[0],xy[1],color=color,alpha=.52,lw=.6,ls=(0,(4,2)),zorder=2)
        points=np.array([[g[p]["tau_MB_per_s"],g[p]["sigma_MB_per_s"]] for p in ("short","reference","long")])
        ax.plot(points[:,0],points[:,1],color=color,lw=.7,alpha=.7,zorder=3)
        for profile in ("short","long","reference"):
            r=g[profile]; is_ref=profile=="reference"
            ax.scatter(r["tau_MB_per_s"],r["sigma_MB_per_s"],marker=MARKERS[case],
                       s=40 if is_ref else 16, facecolor=color if is_ref else "white",
                       edgecolor="white" if is_ref else color,linewidth=.6 if is_ref else .8,zorder=5 if is_ref else 4)
            plotted.append({"case_id":case,"profile":profile,"K":r["K"],"N":r["N"],
                            "x_tau_MB_per_s":r["tau_MB_per_s"],"y_sigma_MB_per_s":r["sigma_MB_per_s"],
                            "rho_MB_per_s":r["rho_MB_per_s"],"U_star":r["U_star"],
                            "at_U128":classify(128,r["U_star"]),"source_mapping":r["source_mapping"]})
        p=g["reference"]; dx,dy=offsets[case]
        text_artists.append(ax.annotate(LABELS[case],xy=(p["tau_MB_per_s"],p["sigma_MB_per_s"]),
                    xytext=(dx,dy),textcoords="offset points",ha="center",va="center",
                    color=color,fontsize=8.05,weight="semibold",zorder=8,
                    arrowprops={"arrowstyle":"-","color":color,"lw":.45,"alpha":.7},
                    bbox={"facecolor":"white","edgecolor":"none","alpha":.92,"pad":.6}))
        assert xlog[0] < center[0]-radius and center[0]+radius < xlog[1]
        assert ylog[0] < center[1]-radius and center[1]+radius < ylog[1]
        circles.append({"case_id":case,"center_log10":center.tolist(),"radius_decades":radius,
                        "semantics":"finite paired scenario summary, not a feasible envelope"})

    # Inline labels on separated upper/lower stretches of each true balance line.
    line_labels=[(1,530,530,"U = 1"),(128,210,26880,"U = 128"),
                 (1024,18,18432,"U = 1K"),(131072,.19,24903.68,"U = 128K")]
    for U,x,y,label in line_labels:
        text_artists.append(ax.annotate(label,(x,y),xytext=(0,5),textcoords="offset points",rotation=45,
                    ha="center",va="bottom",color="#334c61" if U==128 else "#79838c",
                    fontsize=8,weight="semibold" if U==128 else "normal",
                    bbox={"facecolor":"white","edgecolor":"none","alpha":.9,"pad":.4},zorder=7))
    callout=ax.text(.023,.97,"For U = 128:\nAbove: resident-bound\nBelow: streaming-bound",transform=ax.transAxes,
                    fontsize=7.8,color="#334c61",linespacing=1.55,va="top")

    fig.text(.096,.958,"A | Native full-load reuse reference",fontsize=10.2,weight="semibold",color="#182838")
    fig.text(.096,.919,r"Each native matrix is loaded once; balance at $\sigma=U\tau$",fontsize=8.4,color="#657382")
    handles=[Line2D([0],[0],marker="o",color="none",markerfacecolor="#657382",markeredgecolor="white",markersize=6,label="Typical"),
             Line2D([0],[0],marker="o",color="none",markerfacecolor="white",markeredgecolor="#657382",markersize=4,label="Paired scenarios"),
             Line2D([0],[0],color="#657382",ls=(0,(4,2)),lw=.7,label="Finite-scenario circle")]
    fig.legend(handles=handles,loc="lower center",bbox_to_anchor=(.545,.071),ncol=3,frameon=False,
               fontsize=7.8,columnspacing=1.7,handlelength=1.8)
    fig.text(.096,.04,"U: served vectors per full load     1K = 1024     MB/s = 10⁶ Byte/s",fontsize=7.7,color="#657382")
    save_figure(fig,HERE/"figure")
    fig.canvas.draw()
    bbox=ax.get_window_extent()
    scale_x=bbox.width/(xlog[1]-xlog[0]); scale_y=bbox.height/(ylog[1]-ylog[0])
    assert math.isclose(scale_x,scale_y,rel_tol=1e-12)
    text_point_collisions=[]
    for t in text_artists:
        bb=t.get_bbox_patch().get_window_extent()
        for p in plotted:
            xy=ax.transData.transform((p["x_tau_MB_per_s"],p["y_sigma_MB_per_s"]))
            # Include the point's visible radius and 0.6 pt breathing room.
            radius=(math.sqrt(40 if p["profile"]=="reference" else 16)/2+.6)*fig.dpi/72
            if bb.x0-radius <= xy[0] <= bb.x1+radius and bb.y0-radius <= xy[1] <= bb.y1+radius:
                text_point_collisions.append([t.get_text(),p["case_id"],p["profile"]])
    assert not text_point_collisions, text_point_collisions
    callout_box=callout.get_window_extent()
    callout_collisions=[t.get_text() for t in text_artists
                        if callout_box.overlaps(t.get_bbox_patch().get_window_extent())]
    assert not callout_collisions, callout_collisions
    label_pair_collisions=[]
    for i,a in enumerate(text_artists):
        for b in text_artists[i+1:]:
            if a.get_bbox_patch().get_window_extent().overlaps(b.get_bbox_patch().get_window_extent()):
                label_pair_collisions.append([a.get_text(),b.get_text()])
    assert not label_pair_collisions, label_pair_collisions
    (HERE/"plotted_data.json").write_text(json.dumps({"shared_source":"../shared/data.json","points":plotted,"circles":circles,
                                                       "demand_U":[1,128,1024,131072]},indent=2)+"\n")
    (HERE/"validation.json").write_text(json.dumps({"status":"PASS","point_count":len(plotted),"all_circles_inside_axes":True,
                                                      "equal_pixels_per_decade":True,"pixels_per_decade":scale_x,
                                                      "label_boxes_vs_all_actual_markers":"PASS: no overlap including visible marker radius",
                                                      "callout_vs_all_label_boxes":"PASS: no overlap",
                                                      "all_label_pairs":"PASS: no bounding-box overlap",
                                                      "figure_inches":[7.16,4.35],"layout":"double-column",
                                                      "classification_uses":"30 actual paired scenario points only"},indent=2)+"\n")
    plt.close(fig)
    print("PASS: A saved PNG/PDF/SVG; 30 exact points, 10 bounded circles, equal log-decade display")


if __name__=="__main__":
    main()
