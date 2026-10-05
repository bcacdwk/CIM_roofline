#!/usr/bin/env python3
"""Rebuild Task III only; upstream tasks remain read-only."""
from pathlib import Path
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STEPS = [
    "shared/build_shared.py",
    "01_hardware_overlay/build.py",
    "02_demand_dual/build.py",
    "03_reuse_threshold/build.py",
    "04_normalized_response/build.py",
    "05_improvement_payoff/build.py",
    "review/independent_ACD.py",
    "review/independent_BE_check.py",
    "review/build_review.py",
]

if __name__ == "__main__":
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    for step in STEPS:
        print(f"Task III: {step}", flush=True)
        subprocess.run([sys.executable, str(HERE / step)], cwd=ROOT, env=env, check=True)
    print("Rebuilt all candidates and review artifacts. Inspect regenerated PDF pages before approval.")
