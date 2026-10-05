#!/usr/bin/env python3
"""Restore the exact historical task tree into a fresh, local-only directory."""
import argparse,hashlib,json,shutil
from pathlib import Path
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
archive=Path(__file__).resolve().parent;out=a.out.expanduser().resolve()
assert not any(s in str(out).lower() for s in ('onedrive','icloud','mobile documents')), 'restore in a non-synchronized local directory'
assert not out.exists(), 'destination must be new'
manifest=json.loads((archive/'migration_manifest.json').read_text())
for row in manifest['files']:
 source=archive.parent/row['archive_path'];assert hashlib.sha256(source.read_bytes()).hexdigest()==row['sha256'],str(source)
shutil.copytree(archive/'history',out)
for row in manifest['files']:assert hashlib.sha256((out/row['original_path']).read_bytes()).hexdigest()==row['sha256'],row['original_path']
print(json.dumps({'status':'PASS','restored_files':len(manifest['files']),'out':str(out)}))
