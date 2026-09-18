#!/bin/sh
set -eu
case_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
/opt/anaconda3/bin/python "$case_dir/scripts/check_sram_dcim.py" --emit
cd "$case_dir/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build sram_dcim.tex
cp ../build/sram_dcim.pdf ../output/sram_dcim.pdf
/opt/anaconda3/bin/python ../scripts/render_pdf.py
