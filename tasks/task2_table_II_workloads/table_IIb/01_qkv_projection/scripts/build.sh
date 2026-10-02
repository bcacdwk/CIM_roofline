#!/bin/sh
set -eu
TASK2_PYTHON=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
TASK2_QKV_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
export PYTHONDONTWRITEBYTECODE=1
export SOURCE_DATE_EPOCH=1790630400
export FORCE_SOURCE_DATE=1
"$TASK2_PYTHON" "$TASK2_QKV_DIR/scripts/generate.py"
"$TASK2_PYTHON" "$TASK2_QKV_DIR/scripts/check.py"
mkdir -p "$TASK2_QKV_DIR/build" "$TASK2_QKV_DIR/output"
cd "$TASK2_QKV_DIR/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build report.zh.tex
cp ../build/report.zh.pdf ../output/report.zh.pdf
