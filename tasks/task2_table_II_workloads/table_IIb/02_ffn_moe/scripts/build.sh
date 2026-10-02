#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
TASK2_PYTHON=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
FFN_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
"$TASK2_PYTHON" "$FFN_ROOT/scripts/generate.py"
"$TASK2_PYTHON" "$FFN_ROOT/scripts/check.py"
mkdir -p "$FFN_ROOT/build" "$FFN_ROOT/output"
cd "$FFN_ROOT/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -file-line-error -outdir=../build report.zh.tex
cp ../build/report.zh.pdf ../output/report.zh.pdf
