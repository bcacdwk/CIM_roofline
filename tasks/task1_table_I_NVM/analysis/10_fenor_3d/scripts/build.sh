#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FENOR_PYTHON=${FENOR_PYTHON:-/opt/anaconda3/bin/python}
"$FENOR_PYTHON" "$HERE/scripts/check_fenor.py"
mkdir -p "$HERE/build" "$HERE/output"
cd "$HERE/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir="$HERE/build" fenor_3d.tex
cp "$HERE/build/fenor_3d.pdf" "$HERE/output/fenor_3d.pdf"
