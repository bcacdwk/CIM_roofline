#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
RRAM_PYTHON=${RRAM_PYTHON:-/opt/anaconda3/bin/python}
"$RRAM_PYTHON" "$HERE/scripts/check_rram.py"
mkdir -p "$HERE/build" "$HERE/output/pdf"
cd "$HERE/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir="$HERE/build" rram.tex
cp "$HERE/build/rram.pdf" "$HERE/output/pdf/rram.pdf"
