#!/usr/bin/env python3
"""Reference-configuration log-log map; adapted directly from the NVM plot style."""
from __future__ import annotations
import csv
import json
import math
import sys
sys.dont_write_bytecode = True
import numpy as np
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullLocator
from build_figures import COLORS, DATA, LABELS, MUTED, OUT, fmt, normalize_svg, plt

INCHES_PER_DECADE = 2.6
MARKER_AREA, EXTREME_MARKER_AREA = 320, 56
STEM = "rho_tau_loglog"


def limits_for(groups, circles=None):
    log_points=np.array([np.log10([r["tau"],r["rho"]])
        for g in groups for r in (g.values() if circles else [g["reference"]])])
    low,high=log_points.min(axis=0),log_points.max(axis=0)
    for s in circles or []:
        center=np.array(s["center_log10"]);radius=s["radius_decades"]
        low=np.minimum(low,center-radius);high=np.maximum(high,center+radius)
    # Space for whole markers and readable labels, independent of rate magnitude.
    low=np.floor((low-np.array([.48,.60]))*4)/4
    high=np.ceil((high+np.array([.48,.40]))*4)/4
    return tuple(10.**np.array([low[0],high[0]])),tuple(10.**np.array([low[1],high[1]]))


def render_plot(rows, source_report, *, circle_specs=None, output_stem=STEM,
                 xlimits=None, ylimits=None):
    groups=[{"reference":r} for r in rows]
    OUT.mkdir(exist_ok=True);DATA.mkdir(exist_ok=True)
    auto_x,auto_y=limits_for(groups,circle_specs)
    xlimits=xlimits or auto_x;ylimits=ylimits or auto_y
    rows=[g["reference"] for g in groups]
    assert len(rows)==10
    sx,sy=[math.log10(b/a) for a,b in (xlimits,ylimits)]
    width,height=sx*INCHES_PER_DECADE,sy*INCHES_PER_DECADE
    left,bottom,right,top=1.05,1.40,.4,.9
    fw,fh=width+left+right,height+bottom+top
    fig=plt.figure(figsize=(fw,fh),facecolor="white")
    ax=fig.add_axes([left/fw,bottom/fh,width/fw,height/fh])
    ax.set(xscale="log",yscale="log",xlim=xlimits,ylim=ylimits)
    ax.set_aspect("equal",adjustable="box")
    for s in ax.spines.values():s.set_visible(True);s.set_color("#82909c");s.set_linewidth(1.1)
    ax.set_xlabel(r"Resident update capacity $\tau$ [MB/s]",fontsize=14,labelpad=12)
    ax.set_ylabel(r"Streaming input capacity $\rho$ [MB/s]",fontsize=14,labelpad=12)
    for a in (ax.xaxis,ax.yaxis):
        a.set_major_locator(LogLocator(base=10,numticks=12));a.set_major_formatter(LogFormatterMathtext(base=10));a.set_minor_locator(NullLocator())
    ax.tick_params(labelsize=12.5,length=4.5,pad=6);ax.grid(color="#e3e9ee",lw=.8,zorder=0)
    xx=np.geomspace(*xlimits,1000)
    ax.fill_between(xx,np.clip(xx,*ylimits),ylimits[1],color="#fbf8f3",zorder=0)
    ax.fill_between(xx,ylimits[0],np.clip(xx,*ylimits),color="#f3f8fb",zorder=0)
    for ratio in (.01,1,100):
        yy=ratio*xx;inside=(yy>=ylimits[0])&(yy<=ylimits[1])
        ax.plot(xx[inside],yy[inside],color="#28465e" if ratio==1 else "#718594",
            lw=3 if ratio==1 else 1.65,ls=(0,(7,4)) if ratio==1 else (0,(4,4)),zorder=2)
    for i,s in enumerate(circle_specs or []):
        center=np.array(s["center_log10"]);radius=s["radius_decades"]
        theta=np.linspace(0,2*np.pi,1441);xy=10**(center[:,None]+radius*np.array([np.cos(theta),np.sin(theta)]))
        ax.fill(xy[0],xy[1],color=COLORS[i],alpha=.065,edgecolor="none",zorder=1.1)
        ax.plot(xy[0],xy[1],color=COLORS[i],alpha=.83,lw=1.45,ls=(0,(5,3.2)),zorder=3)
    dots=[];connectors=[]
    if circle_specs:
        for i,g in enumerate(groups):
            for p in ("short","long"):
                r=g[p];ref=g["reference"]
                line,=ax.plot([ref["tau"],r["tau"]],[ref["rho"],r["rho"]],color=COLORS[i],lw=.9,alpha=.65,zorder=4)
                marker=ax.scatter(r["tau"],r["rho"],s=EXTREME_MARKER_AREA,c=COLORS[i],edgecolors="white",linewidths=.75,zorder=7)
                dots.append((marker,r,EXTREME_MARKER_AREA,.75));connectors.append((line,ref,r))
    for i,r in enumerate(rows):
        marker=ax.scatter(r["tau"],r["rho"],s=MARKER_AREA,c=COLORS[i],edgecolors="white",linewidths=1.25,zorder=6)
        dots.append((marker,r,MARKER_AREA,1.25))
    title="Typical streaming and resident capacity" if not circle_specs else "Paired streaming and resident capacity"
    fig.text(left/fw,(bottom+height+.48)/fh,title,fontsize=22,weight="bold")
    fig.text(left/fw,(bottom+height+.18)/fh,
        "Selected reference INT8 payloads  ·  RI* = ρ/τ" if not circle_specs else
        "Large dots: typical  ·  Small dots: fast / slow  ·  Lines join paired scenarios  ·  RI* = ρ/τ",fontsize=12,color=MUTED)
    fig.text(left/fw,.13/fh,"Native sizes and resources differ; these capacities do not rank equal-area or equal-work implementations.",fontsize=9.8,color=MUTED)
    if circle_specs:
        fig.text(left/fw,.35/fh,"Circles summarize finite sustainable scenarios; they are not confidence intervals or envelopes of feasible combinations.",fontsize=9.8,color=MUTED)
    fig.canvas.draw();renderer=fig.canvas.get_renderer();bounds=ax.get_window_extent()
    dot_geometry=[(ax.transData.transform((r["tau"],r["rho"])),(math.sqrt(area)+stroke)/2*fig.dpi/72) for _,r,area,stroke in dots]
    occupied=[];annotations=[];placements={}

    def valid(box,pad=4):
        box=box.padded(pad)
        if not (bounds.contains(box.x0,box.y0) and bounds.contains(box.x1,box.y1)):return False
        if any(box.overlaps(b) for b in occupied):return False
        for xy,rad in dot_geometry:
            distance=math.hypot(xy[0]-np.clip(xy[0],box.x0,box.x1),xy[1]-np.clip(xy[1],box.y0,box.y1))
            if distance<=rad+3:return False
        return True

    # Dense point neighborhoods are placed first. All choices move labels only.
    refxy=np.array([ax.transData.transform((r["tau"],r["rho"])) for r in rows])
    density=[sum(np.linalg.norm(x-refxy[i])<220 for x in refxy) for i in range(10)]
    order=sorted(range(10),key=lambda i:(-density[i],i))
    candidates=[(0,-18,"center","top"),(0,20,"center","bottom"),
                (20,0,"left","center"),(-20,0,"right","center")]
    for dist in (28,44,64,88,115):
        candidates += [(dx,dy,ha,va) for dx,ha in ((dist,"left"),(-dist,"right"))
                       for dy,va in ((-dist*.7,"top"),(dist*.7,"bottom"))]
        candidates += [(0,-dist-18,"center","top"),(0,dist+20,"center","bottom")]
    for i in order:
        r=rows[i];text=LABELS[i]+"\n"+r"$\mathrm{RI}^{*}="+fmt(r["RI_star"])+"$"
        label=ax.annotate(text,(r["tau"],r["rho"]),xytext=(0,-18),textcoords="offset points",
            fontsize=12,color=COLORS[i],weight="semibold",linespacing=1.35,zorder=8,
            bbox=dict(facecolor="white",edgecolor="none",alpha=.94,pad=.65))
        for dx,dy,ha,va in candidates:
            label.set_position((dx,dy));label.set_ha(ha);label.set_va(va)
            box=label.get_window_extent(renderer)
            if valid(box):
                occupied.append(box.padded(4));annotations.append(label)
                placements[r["case_id"]]={"offset_points":[dx,dy],"horizontal_alignment":ha,"vertical_alignment":va}
                break
        else:raise AssertionError("No collision-free label position: "+r["case_id"])
    # Reference-line labels are chosen from their visible segment after technology labels.
    guide_texts=[]
    for ratio in (1,100,.01):
        lo=max(math.log10(xlimits[0]),math.log10(ylimits[0]/ratio))+.18
        hi=min(math.log10(xlimits[1]),math.log10(ylimits[1]/ratio))-.6
        label_text=(r"$\rho=\tau\ (\mathrm{RI}^{*}=1)$" if ratio==1 else
                    r"$\mathrm{RI}^{*}=10^{"+str(int(math.log10(ratio)))+"}$")
        label=ax.text(1,1,label_text,rotation=45,rotation_mode="anchor",fontsize=13.5 if ratio==1 else 11.5,
            weight="bold",color="#28465e" if ratio==1 else "#637b8d",zorder=5,
            bbox=dict(facecolor="white",edgecolor="none",alpha=.92,pad=1))
        for t in np.linspace(hi,lo,60):
            label.set_position((10**t,ratio*10**t*1.13))
            box=label.get_window_extent(renderer)
            if valid(box):occupied.append(box.padded(4));guide_texts.append(label);break
        else:raise AssertionError("No collision-free guide-label position: "+str(ratio))
    fig.canvas.draw();renderer=fig.canvas.get_renderer()
    caption_boxes=[t.get_window_extent(renderer) for t in fig.texts]
    for i,box in enumerate(caption_boxes):
        assert not box.overlaps(ax.xaxis.label.get_window_extent(renderer)), "Caption overlaps x-axis label"
        for other in caption_boxes[i+1:]:assert not box.overlaps(other), "Figure-level text collision"
    assert math.isclose(bounds.width/sx,bounds.height/sy,rel_tol=1e-8)
    p0,p1=ax.transData.transform([[.1,.1],[1,1]])
    angle=math.degrees(math.atan2(p1[1]-p0[1],p1[0]-p0[0]));assert math.isclose(angle,45,abs_tol=1e-8)
    for (marker,r,_,_),(xy,rad) in zip(dots,dot_geometry):
        np.testing.assert_array_equal(marker.get_offsets().data[0],[r["tau"],r["rho"]])
        assert bounds.contains(xy[0]-rad,xy[1]-rad) and bounds.contains(xy[0]+rad,xy[1]+rad)
        assert math.isclose(r["RI_star"],r["rho"]/r["tau"],rel_tol=1e-12)
    all_labels=annotations+guide_texts
    for i,label in enumerate(all_labels):
        box=label.get_window_extent(renderer).padded(2)
        assert bounds.contains(box.x0,box.y0) and bounds.contains(box.x1,box.y1),label.get_text()
        for other in all_labels[i+1:]:assert not box.overlaps(other.get_window_extent(renderer).padded(2)),(label.get_text(),other.get_text())
        for xy,rad in dot_geometry:
            distance=math.hypot(xy[0]-np.clip(xy[0],box.x0,box.x1),xy[1]-np.clip(xy[1],box.y0,box.y1))
            assert distance>rad,"Label covers point: "+label.get_text()
    for line,ref,r in connectors:
        np.testing.assert_array_equal(line.get_xdata(),[ref["tau"],r["tau"]]);np.testing.assert_array_equal(line.get_ydata(),[ref["rho"],r["rho"]])
    for s in circle_specs or []:
        c=np.array(s["center_log10"]);rad=s["radius_decades"]
        display=ax.transData.transform(10**(c+rad*np.array([[1,0],[0,1],[-1,0],[0,-1]])))
        radii=np.linalg.norm(display-ax.transData.transform(10**c),axis=1)
        np.testing.assert_allclose(radii,radii[0],rtol=1e-12)
        assert all(bounds.contains(*p) for p in display),s["case_id"]
    for ext in ("png","pdf","svg"):
        fig.savefig(OUT/f"{output_stem}.{ext}",dpi=220,bbox_inches="tight",pad_inches=.14)
        if ext == "svg": normalize_svg(OUT/f"{output_stem}.{ext}")
    exported=[{"profile":p,**g[p]} for g in groups for p in ("short","reference","long")] if circle_specs else [{"profile":"reference",**r} for r in rows]
    fields=["profile","case_id","technology","K","N","rho","tau","RI_star","U_star","raw_delta_S_ns","raw_T_R_ns",
            "effective_delta_S_ns","effective_T_R_ns","availability","result_path","input_path"]
    with (DATA/f"{output_stem}_points.csv").open("w",encoding="utf-8-sig",newline="") as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows({k:r[k] for k in fields} for r in exported)
    report={"all_passed":True,"point_count":len(dots),"reference_point_count":10,
        "selection":"three sustainable fixed-resource paired scenarios" if circle_specs else "selected typical reference points",
        "x":{"metric":"tau","scale":"log10","limits":xlimits},"y":{"metric":"rho","scale":"log10","limits":ylimits},
        "dynamic_limits_from_data":True,"title":title,"plot_width_over_height":sx/sy,
        "inches_per_decade":INCHES_PER_DECADE,"equality_line_angle_degrees":angle,"same_scale_per_decade_verified":True,
        "all_points_and_labels_contained":True,"unmodified_coordinates_verified":True,
        "label_content":"Technology and RI_star = rho/tau; never workload RI", "label_offsets":placements,
        "no_label_leaders_verified":True,"no_overlapping_labels_or_label_dot_collisions":True,
        "guide_labels_included_in_collision_checks":True,"all_four_spines_visible":True,
        "marker_area_points_squared":MARKER_AREA,"source_checks_passed":source_report["all_passed"],
        "source_sha256":source_report["sha256"]["data/ten_case_results.json"],
        "native_configuration_note":"Selected different native sizes and resources; not equal-area or equal-work ranking"}
    if circle_specs:
        report.update({"extreme_point_count":20,"extreme_marker_area_points_squared":EXTREME_MARKER_AREA,
            "connector_count":len(connectors),"connector_origin":"typical point, not geometric center",
            "scenario_circles":circle_specs,
            "circle_geometry":"Projection of typical onto the perpendicular bisector of fast/slow in log10 space",
            "circle_display_checks":"All cardinal radii equal; entire circles and typical points contained",
            "circle_meaning":"Finite sustainable paired scenarios; not confidence intervals or a feasible-combination envelope"})
    (DATA/f"{output_stem}_validation.json").write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"PASS: {output_stem}; {len(dots)} unchanged points; equal log scale; all labels and dots collision-free.")
    return fig

if __name__=="__main__":
    from build_figures import main
    main()
