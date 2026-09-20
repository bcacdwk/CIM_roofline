#!/bin/sh
set -eu
case_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
NOR_PYTHON=${NOR_PYTHON:-/opt/anaconda3/bin/python}
"$NOR_PYTHON" "$case_dir/scripts/check_nor.py"
mkdir -p "$case_dir/build" "$case_dir/output"
cd "$case_dir/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build nor_2d.tex
cp ../build/nor_2d.pdf ../output/nor_2d.pdf
"$NOR_PYTHON" ../scripts/render_pdf.py
