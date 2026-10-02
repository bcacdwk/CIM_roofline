#!/usr/bin/env python3
"""Compatibility entry for the current operator-level Table II(a).

The former generator is preserved under table_IIa/history/ports_v1/provenance/.
This entry no longer writes the historical shared/tex/IIa_values.generated.tex.
"""
from pathlib import Path
import runpy
import sys
sys.dont_write_bytecode=True
if __name__=='__main__':
    runpy.run_path(str(Path(__file__).resolve().parents[2]/'table_IIa/scripts/generate.py'),run_name='__main__')
