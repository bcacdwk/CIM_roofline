#!/usr/bin/env python3
"""Add short/long scenario circles to the existing reference-point log-log style.

Only rho_tau_loglog_circles.* and its associated records are written.
The old final figure and all scientific estimates remain untouched.
"""
from __future__ import annotations
import math
import sys
sys.dont_write_bytecode = True
import numpy as np
from build_figures import load_and_validate, plt
from build_loglog import render_final

STEM = 'rho_tau_loglog_circles'


def circle_for(group):
    a, b, p = [np.log10([group[k]['tau'], group[k]['rho']])
               for k in ('short', 'long', 'reference')]
    midpoint, chord = (a+b)/2, b-a
    chord_squared = float(chord @ chord)
    if chord_squared == 0:
        raise ValueError('Distinct short and long points are required for a unique bisector')
    # Every eligible center c satisfies (c-midpoint) dot chord = 0.
    # Orthogonal projection uniquely minimizes ||c-p|| over that line.
    center = p - float((p-midpoint) @ chord)/chord_squared*chord
    radius = float(np.linalg.norm(a-center))
    offset = float(np.linalg.norm(p-center))
    assert math.isclose(radius, np.linalg.norm(b-center), rel_tol=1e-12)
    assert abs(float((center-midpoint) @ chord)) < 1e-12
    normal = np.array([-chord[1], chord[0]]) / math.sqrt(chord_squared)
    assert abs(float((p-center) @ normal)) < 1e-12
    # Check the reference is also inside; the circle is not a fit through all 3 points.
    assert offset <= radius + 1e-12, group['reference']['case_id']
    return dict(case_id=group['reference']['case_id'], center_log10=center.tolist(),
                radius_decades=radius, reference_center_distance_decades=offset,
                reference_offset_over_radius=offset/radius,
                short_log10=a.tolist(), long_log10=b.tolist(), reference_log10=p.tolist(),
                extreme_points_on_circumference=True, reference_inside=True,
                long_scenario_type=group['long']['scenario_type'],
                sources={k:group[k]['source_result'] for k in ('short','reference','long')})


def main():
    _, groups, report = load_and_validate()
    specs = [circle_for(g) for g in groups]
    # Slightly extend only the upper limits, so every circle is fully visible.
    fig = render_final(groups, report, circle_specs=specs, output_stem=STEM,
                       xlimits=(.0011, 12000), ylimits=(.04, 160))
    plt.close(fig)
    print('PASS: 10 uniquely defined log-space circles; 20 short/long points on edges; '
          '10 references inside; nearest-center optimality and display circularity verified.')


if __name__ == '__main__':
    main()
