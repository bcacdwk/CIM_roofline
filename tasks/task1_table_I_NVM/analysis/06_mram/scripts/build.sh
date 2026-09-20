#!/bin/sh
set -eu
case_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
case_python=${BASELINE_PYTHON:-/opt/anaconda3/bin/python}
"$case_python" "$case_dir/scripts/check_mram.py" --emit
mkdir -p "$case_dir/build" "$case_dir/output"
cd "$case_dir/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build mram.tex
cp ../build/mram.pdf ../output/mram.pdf
"$case_python" ../scripts/render_pdf.py
