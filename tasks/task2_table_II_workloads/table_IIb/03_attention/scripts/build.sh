#!/bin/sh
set -eu
TASK2_ATTENTION_DIR=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TASK2_PYTHON=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
export PYTHONDONTWRITEBYTECODE=1
"$TASK2_PYTHON" "$TASK2_ATTENTION_DIR/scripts/generate.py"
"$TASK2_PYTHON" "$TASK2_ATTENTION_DIR/scripts/check.py"
mkdir -p "$TASK2_ATTENTION_DIR/build" "$TASK2_ATTENTION_DIR/output"
cd "$TASK2_ATTENTION_DIR/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build report.zh.tex
cp ../build/report.zh.pdf ../output/report.zh.pdf
