#!/usr/bin/env python3
"""Read-only verification of Agent D's final local delivery manifest."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root/'DELIVERY.json').read_text())
assert manifest['status'] == 'ready_for_review'
assert manifest['path_base'] == 'this DELIVERY.json directory'
for item in manifest['artifacts']:
    path = root/item['path']
    assert path.resolve().is_relative_to(root)
    assert hashlib.sha256(path.read_bytes()).hexdigest() == item['sha256'], item['path']
    assert path.stat().st_size == item['bytes'], item['path']
print('PASS: D revision '+str(manifest['delivery_revision'])+'; '+str(len(manifest['artifacts']))+' local artifact hashes verified.')
