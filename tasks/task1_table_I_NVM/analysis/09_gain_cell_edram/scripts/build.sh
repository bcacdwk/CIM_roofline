#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
GAIN_CELL_PYTHON=${GAIN_CELL_PYTHON:-/opt/anaconda3/bin/python}
"$GAIN_CELL_PYTHON" "$HERE/scripts/check_gain_cell_edram.py"
mkdir -p "$HERE/build" "$HERE/output"
cd "$HERE/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir="$HERE/build" gain_cell_edram.tex
cp "$HERE/build/gain_cell_edram.pdf" "$HERE/output/gain_cell_edram.pdf"
