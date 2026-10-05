# P1 MRAM fresh integration candidates

Three fresh source/build/runs; independent review pending. This directory is NOT an accepted result set. Hardware and 100 ns digital clock are fixed; the finite scenarios vary the same UMEM programming-plateau policy. The canonical computational package is shared, while the scenario selector and resolved input hashes are distinct in point_bindings.json.

|Scenario|rho MB/s|tau MB/s|Delta us|T_R ms|RI*|U*|
|---|---:|---:|---:|---:|---:|---:|
|optimistic|0.398505604|1.90458477|160.6|2.1506|0.2092349|13.3910336|
|reference|0.398505604|1.29024129|160.6|3.1746|0.308861301|19.7671233|
|pessimistic|0.398505604|0.78428369|160.6|5.2226|0.508114103|32.5193026|

Local integration: /Users/shine/neurosim/runs/step4-v5/integration/p1-mram-integration-20261005. Each machine row links the native source/build, stages/resources, functional evidence and input snapshot. No candidate_points or reference_snapshot file was read to generate these values. No old PCM tau was included.
