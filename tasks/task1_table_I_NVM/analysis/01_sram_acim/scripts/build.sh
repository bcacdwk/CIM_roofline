#!/bin/sh
set -eu
case_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
case_python=${BASELINE_PYTHON:-/opt/anaconda3/bin/python}
"$case_python" "$case_dir/scripts/check_sram_acim.py"
mkdir -p "$case_dir/build" "$case_dir/output"
cd "$case_dir/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build sram_acim.tex
cp ../build/sram_acim.pdf ../output/sram_acim.pdf
"$case_python" ../scripts/render_pdf.py
