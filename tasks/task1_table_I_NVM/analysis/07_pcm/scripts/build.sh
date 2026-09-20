#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
PCM_PYTHON=${PCM_PYTHON:-/opt/anaconda3/bin/python}
"$PCM_PYTHON" "$HERE/scripts/check_pcm.py"
mkdir -p "$HERE/build" "$HERE/output"
cd "$HERE/tex"
latexmk -xelatex -interaction=nonstopmode -halt-on-error -outdir="$HERE/build" pcm.tex
cp "$HERE/build/pcm.pdf" "$HERE/output/pcm.pdf"
