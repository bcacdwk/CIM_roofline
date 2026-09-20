#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
FERAM_PYTHON=${FERAM_PYTHON:-/opt/anaconda3/bin/python}
"$FERAM_PYTHON" "$HERE/scripts/check_feram.py"
mkdir -p "$HERE/build" "$HERE/output"
cd "$HERE/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir="$HERE/build" feram_hfo2.tex
cp "$HERE/build/feram_hfo2.pdf" "$HERE/output/feram_hfo2.pdf"
