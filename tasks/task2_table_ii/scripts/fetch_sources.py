"""Optional online restoration from pinned manifest. Never downloads weights.

Offline reproduction uses already committed config/code sources and needs no fetch.
Full texts are opt-in and remain in sources/local-only (ignored).
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen, Request
ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(); ap.add_argument("--include-fulltext",action="store_true"); args=ap.parse_args()
for s in json.loads((ROOT/"sources/manifest.json").read_text()):
    path=ROOT/s["local_path"]
    if s.get("fetch_policy")=="frozen_snapshot_keep_local":
        assert path.exists(),f"Restore committed snapshot {path}; live API counters change."
        continue
    if "local-only" in path.parts and not args.include_fulltext: continue
    if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest()==s["sha256"]: continue
    assert path.resolve().is_relative_to(ROOT.resolve())
    data=urlopen(Request(s["url"],headers={"User-Agent":"Task2-source-reproduction/1.0"}),timeout=60).read()
    assert hashlib.sha256(data).hexdigest()==s["sha256"],f"Source changed: {s['source_id']}"
    path.parent.mkdir(parents=True,exist_ok=True); path.write_bytes(data)
    print(s["source_id"])
