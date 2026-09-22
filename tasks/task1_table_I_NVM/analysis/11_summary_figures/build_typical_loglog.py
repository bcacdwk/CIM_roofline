#!/usr/bin/env python3
"""One square log-log rho/tau plane containing only the ten reference points.

Run with python -X utf8 build_typical_loglog.py. Writes only new log-log outputs.
"""
from __future__ import annotations

import csv
import json
import math
import sys

sys.dont_write_bytecode = True

from build_figures import (COLORS, DATA, INK, LABELS, MUTED, OUT, SOURCE,
                           load_and_validate, plt)
import numpy as np
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullLocator


def main():
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    _, groups, source_validation = load_and_validate()
    rows = [g["reference"] for g in groups]
    assert len(rows) == 10 and len({r["case_id"] for r in rows}) == 10
    assert all(r["recommended"] and r["rho"] > 0 and r["tau"] > 0 for r in rows)

    fig = plt.figure(figsize=(10.6, 11.0), facecolor="white")
    ax = fig.add_axes([.115, .175, .815, .7854])
    # Identical log ranges and equal transformed-axis scale make all constant-ratio
    # lines 45 degrees. No point is moved to separate coincident-looking markers.
    low, high = 1e-3, 1e4
    ax.set(xscale="log", yscale="log", xlim=(low, high), ylim=(low, high))
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(r"Resident update capacity $\tau$ [MB/s]", fontsize=12.3, labelpad=12)
    ax.set_ylabel(r"Input evaluation capacity $\rho$ [MB/s]", fontsize=12.3, labelpad=12)
    ax.spines[["top", "right"]].set_visible(False)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(LogLocator(base=10, numticks=9))
        axis.set_major_formatter(LogFormatterMathtext(base=10))
        axis.set_minor_locator(NullLocator())
    ax.tick_params(labelsize=11, length=4, pad=5)
    ax.grid(which="major", color="#e3e9ee", lw=.75, zorder=0)

    xx = np.geomspace(low, high, 500)
    ax.fill_between(xx, xx, high, color="#fbf8f3", zorder=0)
    ax.fill_between(xx, low, xx, color="#f3f8fb", zorder=0)
    ax.plot(xx, xx, color="#4b657b", lw=1.6, ls=(0, (5, 4)), zorder=2)
    for ratio in (.01, 100):
        yy = xx * ratio
        visible = (yy >= low) & (yy <= high)
        ax.plot(xx[visible], yy[visible], color="#c5cfd8", lw=.9,
                ls=(0, (3, 5)), zorder=1)

    ax.text(.005, 1600, r"$\rho>\tau$" + "\n" + r"$\mathrm{RI}^{*}>1$",
            fontsize=13, color="#947041", ha="left", va="center", linespacing=1.6)
    ax.text(2600, .007, r"$\rho<\tau$" + "\n" + r"$\mathrm{RI}^{*}<1$",
            fontsize=13, color="#4a7795", ha="right", va="center", linespacing=1.6)
    ax.text(175, 230, r"$\rho=\tau$  ($\mathrm{RI}^{*}=1$)", rotation=45,
            rotation_mode="anchor", color="#4b657b", fontsize=10.6,
            bbox=dict(facecolor="#fbf8f3", edgecolor="none", pad=2))
    ax.text(.0033, .48, r"$\mathrm{RI}^{*}=10^{2}$", rotation=45,
            rotation_mode="anchor", color="#98a6b2", fontsize=9.2)
    ax.text(.45, .0068, r"$\mathrm{RI}^{*}=10^{-2}$", rotation=45,
            rotation_mode="anchor", color="#98a6b2", fontsize=9.2)

    label_positions = [
        (600, 14),       # SRAM ACIM
        (470, 150),      # SRAM DCIM
        (.012, 1.7),     # NOR
        (.006, .12),     # NAND
        (.045, 36),      # RRAM
        (17, 165),       # MRAM
        (.8, .6),        # PCM
        (170, 5.8),      # FeRAM
        (70, .27),       # Gain-cell
        (1.1, 30),       # FeFET
    ]
    plotted_artists = []
    for i, (row, position) in enumerate(zip(rows, label_positions)):
        artist = ax.scatter(row["tau"], row["rho"], s=66, marker="o", c=COLORS[i],
                            edgecolors="white", linewidths=.95, zorder=6)
        plotted_artists.append(artist)
        text = LABELS[i] + "\n" + r"$\mathrm{RI}^{*}=" + f"{row['RI_star']:.3g}" + "$"
        ax.annotate(text, (row["tau"], row["rho"]), xytext=position, textcoords="data",
                    ha="left", va="center", fontsize=11, color=COLORS[i],
                    linespacing=1.4, weight="medium", zorder=8,
                    arrowprops=dict(arrowstyle="-", lw=.85, color=COLORS[i],
                                    shrinkA=4, shrinkB=5),
                    bbox=dict(boxstyle="round,pad=.16", fc="white", ec="none", alpha=.94))

    # Keep the title outside the axes while preserving a square plotting area.
    ax.set_title("Typical CIM designs in the ρ–τ plane", fontsize=19,
                 weight="bold", loc="left", pad=42)
    ax.text(0, 1.027, "10 reference points  ·  logarithmic axes  ·  28 nm CMOS reference periphery",
            transform=ax.transAxes, fontsize=10.5, color=MUTED, va="bottom")
    fig.text(.115, .090, r"$\mathrm{RI}^{*}=\rho/\tau$. Parallel dashed lines show constant capacity ratios; the bold line marks equal capacity.",
             fontsize=9.5, color=MUTED)
    fig.text(.115, .060, r"$\rho$ includes the complete prescribed evaluation; $\tau$ uses each design's declared update groups.  MB/s = $10^6$ Byte/s.",
             fontsize=9.2, color=MUTED)
    fig.text(.115, .031, "Gain-cell includes refresh.  3D FeFET denotes the 2026 vertical AND design.  Values are paired reference estimates.",
             fontsize=9.2, color=MUTED)

    fig.canvas.draw()
    pixel_box = ax.get_window_extent()
    assert math.isclose(pixel_box.width, pixel_box.height, rel_tol=1e-8)
    p0, p1 = ax.transData.transform([[.1, .1], [1, 1]])
    assert math.isclose(p1[0] - p0[0], p1[1] - p0[1], rel_tol=1e-8)
    assert len(plotted_artists) == 10
    for artist, row in zip(plotted_artists, rows):
        np.testing.assert_array_equal(artist.get_offsets().data[0], [row["tau"], row["rho"]])

    stem = "rho_tau_typical_loglog"
    for extension in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{extension}", dpi=250, bbox_inches="tight", pad_inches=.18)
    plt.close(fig)

    with (DATA / f"{stem}_points.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        fields = ["case_id", "technology", "rho", "tau", "RI_star", "source_result"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in rows)
    report = {
        "all_passed": True, "point_count": 10, "selection": "recommended reference only",
        "source": SOURCE.relative_to(DATA.parents[1]).as_posix(),
        "source_checks_passed": source_validation["all_passed"],
        "source_sha256": source_validation["sha256"]["data/ten_case_results.json"],
        "x": {"metric": "tau", "scale": "log10", "limits": [low, high]},
        "y": {"metric": "rho", "scale": "log10", "limits": [low, high]},
        "unit": "decimal MB/s", "square_plot_verified": True,
        "equal_log_scale_verified": True, "unmodified_coordinates_verified": True,
        "guide_ratios": [.01, 1, 100],
        "ratio_interpretation": "In log10 coordinates, log10(rho)-log10(tau)=log10(RI_star); constant ratios are parallel lines, not different slopes.",
    }
    (DATA / f"{stem}_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: 10 typical points, square log-log axes, equal scale per decade, unmodified coordinates.\n{OUT / (stem + '.pdf')}")


if __name__ == "__main__":
    main()
