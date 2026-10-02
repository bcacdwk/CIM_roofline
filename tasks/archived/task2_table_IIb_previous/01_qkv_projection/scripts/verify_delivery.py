#!/usr/bin/env python3
"""Read-only verification of the explicitly handed-off local delivery."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parents[1]
delivery=json.loads((HERE/'DELIVERY.json').read_text())
assert delivery['status']=='ready_for_review'
for artifact in delivery['artifacts']:
    path=HERE/artifact['path']
    assert path.is_relative_to(HERE)
    assert hashlib.sha256(path.read_bytes()).hexdigest()==artifact['sha256'],artifact['path']
data=json.loads((HERE/'data/results.json').read_text())
assert len(data['cases'])==delivery['case_count']==6
print(f"PASS: delivery revision {delivery['delivery_revision']}; {len(delivery['artifacts'])} artifacts; 6 cases")
