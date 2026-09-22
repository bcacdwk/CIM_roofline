#!/usr/bin/env python3
"""Ten reference points: tighter y range, larger dots, labels below without leaders."""
from __future__ import annotations

import json
import math
import sys

sys.dont_write_bytecode = True

from build_figures import COLORS, DATA, LABELS, MUTED, OUT, load_and_validate, plt
from matplotlib.ticker import LogFormatterMathtext, LogLocator, NullLocator
import numpy as np


def main():
    OUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    _, groups, source_validation = load_and_validate()
    rows = [group["reference"] for group in groups]
    assert len(rows) == 10 and all(row["recommended"] for row in rows)

    requested_limits = (1e-2, 1e3)
    excluded = [row["case_id"] for row in rows if not (
        requested_limits[0] <= row["tau"] <= requested_limits[1]
        and requested_limits[0] <= row["rho"] <= requested_limits[1])]
    assert set(excluded) == {"01_sram_acim", "02_sram_dcim", "04_nand_3d"}
    xlimits, ylimits = (1e-3, 1e4), requested_limits
    assert all(xlimits[0] <= row["tau"] <= xlimits[1]
               and ylimits[0] <= row["rho"] <= ylimits[1] for row in rows)

    fig = plt.figure(figsize=(11.5, 11.9), facecolor="white")
    ax = fig.add_axes([.115, .17, .82, .79244])
    ax.set(xscale="log", yscale="log", xlim=xlimits, ylim=ylimits)
    # Preserve a square box; the different decade spans imply different display
    # scales on x/y. The equality line remains exact but is no longer 45 degrees.
    ax.set_box_aspect(1)
    ax.set_xlabel(r"Resident update capacity $\tau$ [MB/s]", fontsize=13, labelpad=12)
    ax.set_ylabel(r"Input evaluation capacity $\rho$ [MB/s]", fontsize=13, labelpad=12)
    ax.spines[["top", "right"]].set_visible(False)
    for axis in (ax.xaxis, ax.yaxis):
        axis.set_major_locator(LogLocator(base=10, numticks=9))
        axis.set_major_formatter(LogFormatterMathtext(base=10))
        axis.set_minor_locator(NullLocator())
    ax.tick_params(labelsize=12, length=4, pad=6)
    ax.grid(color="#e3e9ee", lw=.75, zorder=0)

    xx = np.geomspace(*xlimits, 800)
    ax.fill_between(xx, np.clip(xx, *ylimits), ylimits[1], color="#fbf8f3", zorder=0)
    ax.fill_between(xx, ylimits[0], np.clip(xx, *ylimits), color="#f3f8fb", zorder=0)
    for ratio in (.01, 1, 100):
        yy = xx * ratio
        visible = (yy >= ylimits[0]) & (yy <= ylimits[1])
        ax.plot(xx[visible], yy[visible],
                color="#4b657b" if ratio == 1 else "#c5cfd8",
                lw=1.6 if ratio == 1 else .9,
                ls=(0, (5, 4)) if ratio == 1 else (0, (3, 5)), zorder=2)

    fig.canvas.draw()
    p0, p1 = ax.transData.transform([[.1, .1], [1, 1]])
    angle = math.degrees(math.atan2(p1[1] - p0[1], p1[0] - p0[0]))
    ax.text(.006, 250, r"$\rho>\tau$" + "\n" + r"$\mathrm{RI}^{*}>1$",
            fontsize=13, color="#947041", ha="left", va="center", linespacing=1.5)
    ax.text(2600, .055, r"$\rho<\tau$" + "\n" + r"$\mathrm{RI}^{*}<1$",
            fontsize=13, color="#4a7795", ha="right", va="center", linespacing=1.5)
    ax.text(90, 160, r"$\rho=\tau$  ($\mathrm{RI}^{*}=1$)", rotation=angle,
            rotation_mode="anchor", color="#4b657b", fontsize=10.8,
            bbox=dict(facecolor="#fbf8f3", edgecolor="none", pad=1.5))
    ax.text(.012, 1.7, r"$\mathrm{RI}^{*}=10^{2}$", rotation=angle,
            rotation_mode="anchor", color="#98a6b2", fontsize=9.5)
    ax.text(1.6, .024, r"$\mathrm{RI}^{*}=10^{-2}$", rotation=angle,
            rotation_mode="anchor", color="#98a6b2", fontsize=9.5)

    artists, annotations = [], []
    for i, row in enumerate(rows):
        artist = ax.scatter(row["tau"], row["rho"], s=185, marker="o", c=COLORS[i],
                            edgecolors="white", linewidths=1.15, zorder=6)
        artists.append(artist)
        # Name-only labels keep neighboring MRAM/FeRAM labels clear. The ratios
        # remain readable through the guide lines and the accompanying data table.
        anchor = (row["tau"], row["rho"])
        offset = (0, -14)
        if i in (0, 1):
            # The two SRAM points have exactly the same tau and close rho values.
            # Stack their colored names under the pair, in the points' top/bottom
            # order, without shifting either point or adding a leader.
            anchor = (row["tau"], min(rows[0]["rho"], rows[1]["rho"]))
            offset = (0, -14 if i == 1 else -32)
        annotation = ax.annotate(LABELS[i], anchor, xytext=offset,
                                 textcoords="offset points", ha="center", va="top",
                                 fontsize=12.2, color=COLORS[i], weight="medium",
                                 bbox=dict(facecolor="white", edgecolor="none", alpha=.92, pad=.18),
                                 zorder=8)
        annotations.append(annotation)

    ax.set_title("Typical CIM designs in the ρ–τ plane", fontsize=20,
                 weight="bold", loc="left", pad=42)
    ax.text(0, 1.027, "10 reference points  ·  logarithmic axes  ·  28 nm CMOS reference periphery",
            transform=ax.transAxes, fontsize=10.8, color=MUTED, va="bottom")
    fig.text(.115, .087, r"$\mathrm{RI}^{*}=\rho/\tau$. The dashed lines mark fixed capacity ratios; the bold line marks equal capacity.",
             fontsize=10, color=MUTED)
    fig.text(.115, .055, r"All ten points are retained: $\tau=10^{-3}$–$10^{4}$ and $\rho=10^{-2}$–$10^{3}$ MB/s. The two axes span different numbers of decades.",
             fontsize=9.5, color=MUTED)
    fig.text(.115, .025, "Gain-cell includes refresh.  3D FeFET denotes the 2026 vertical AND design.  Values are paired reference estimates.",
             fontsize=9.5, color=MUTED)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    box = ax.get_window_extent()
    assert math.isclose(box.width, box.height, rel_tol=1e-8)
    for artist, row, annotation in zip(artists, rows, annotations):
        np.testing.assert_array_equal(artist.get_offsets().data[0], [row["tau"], row["rho"]])
        assert annotation.arrow_patch is None
        bounds = annotation.get_window_extent(renderer)
        assert bounds.y1 < ax.transData.transform((row["tau"], row["rho"]))[1]
        assert box.contains(bounds.x0, bounds.y0) and box.contains(bounds.x1, bounds.y1)
    for i, first in enumerate(annotations):
        for second in annotations[i + 1:]:
            assert not first.get_window_extent(renderer).overlaps(second.get_window_extent(renderer)), (
                first.get_text(), second.get_text())

    stem = "rho_tau_typical_loglog_compact"
    for extension in ("png", "pdf", "svg"):
        fig.savefig(OUT / f"{stem}.{extension}", dpi=250, bbox_inches="tight", pad_inches=.18)
    plt.close(fig)
    report = {
        "all_passed": True, "point_count": len(rows), "selection": "recommended reference only",
        "requested_xy_limits": list(requested_limits),
        "points_excluded_by_requested_limits": excluded,
        "x": {"metric": "tau", "scale": "log10", "limits": list(xlimits)},
        "y": {"metric": "rho", "scale": "log10", "limits": list(ylimits)},
        "square_plot_verified": True, "all_points_in_bounds": True,
        "unmodified_coordinates_verified": True,
        "marker_area_points_squared": 185, "previous_marker_area_points_squared": 66,
        "labels_below_points_verified": True, "no_label_leaders_verified": True,
        "label_boxes_do_not_overlap": True, "labels_within_axes_verified": True,
        "label_content": "Technology names; SRAM names stacked under their same-tau point pair",
        "equality_line_display_angle_degrees": angle,
        "equal_scale_per_decade": False,
        "source_checks_passed": source_validation["all_passed"],
        "source_sha256": source_validation["sha256"]["data/ten_case_results.json"],
    }
    (DATA / f"{stem}_validation.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: all 10 unchanged points; square axes; larger dots; labels below, without leaders or overlaps.")
    print(f"Requested limits exclude: {', '.join(excluded)}")
    print(OUT / f"{stem}.pdf")


if __name__ == "__main__":
    main()
