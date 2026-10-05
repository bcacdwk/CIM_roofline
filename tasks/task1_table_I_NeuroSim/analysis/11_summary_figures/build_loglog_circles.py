#!/usr/bin/env python3
"""NVM-template log-space circles for finite paired engineering scenarios."""
from __future__ import annotations
import math
import sys
sys.dont_write_bytecode=True
import numpy as np


def circle_for(group):
    a,b,p=[np.log10([group[k]['tau'],group[k]['rho']])
           for k in ('optimistic','pessimistic','reference')]
    midpoint,chord=(a+b)/2,b-a
    chord_squared=float(chord@chord)
    if chord_squared==0:
        # Equal endpoints remove the equal-distance constraint. The nearest
        # feasible center to p is exactly p; zero radius stays zero.
        center=p.copy()
        geometry_case='all_points_coincident' if np.array_equal(a,p) else 'coincident_endpoints'
    else:
        center=p-float((p-midpoint)@chord)/chord_squared*chord
        geometry_case='distinct_endpoints'
        assert abs(float((center-midpoint)@chord))<1e-11
    radius=float(np.linalg.norm(a-center));offset=float(np.linalg.norm(p-center))
    assert math.isclose(radius,float(np.linalg.norm(b-center)),rel_tol=1e-12,abs_tol=1e-14)
    # Do not enlarge or move a circle to conceal non-bracketing engineering data.
    if offset>radius+1e-12:
        raise ValueError(f"Typical point outside projection circle: {group['reference']['case_id']}; "
                         f"a={a.tolist()}, b={b.tolist()}, p={p.tolist()}, c={center.tolist()}, r={radius}")
    return {'case_id':group['reference']['case_id'],'center_log10':center.tolist(),
            'radius_decades':radius,'reference_center_distance_decades':offset,
            'reference_offset_over_radius':offset/radius if radius else 0,
            'optimistic_log10':a.tolist(),'pessimistic_log10':b.tolist(),'reference_log10':p.tolist(),
            'geometry_case':geometry_case,
            'degenerate_rule':'Equal endpoints remove the equal-distance constraint; nearest center is p, radius is endpoint distance, and all-three-coincident retains zero radius.' if chord_squared==0 else None,
            'extreme_points_on_circumference':True,'reference_inside':True,
            'sources':{k:group[k]['result_path'] for k in ('optimistic','reference','pessimistic')}}


if __name__=='__main__':
    from build_figures import main
    main()
