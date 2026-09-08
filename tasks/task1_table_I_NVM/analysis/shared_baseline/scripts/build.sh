#!/bin/sh
set -eu
baseline_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$baseline_dir"
baseline_python=${BASELINE_PYTHON:-python3}
"$baseline_python" scripts/check_shared.py
mkdir -p build output
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build tex/shared_baseline.tex > build/build-console.log 2>&1
cp build/shared_baseline.pdf output/shared_baseline.pdf
echo "Built output/shared_baseline.pdf"
