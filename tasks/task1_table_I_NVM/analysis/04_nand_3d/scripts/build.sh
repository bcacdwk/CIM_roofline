#!/bin/sh
set -eu
case_dir=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$case_dir"
case_python=${CASE_PYTHON:-/opt/anaconda3/bin/python}
"$case_python" scripts/check_nand.py
mkdir -p build output
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build tex/nand_3d.tex > build/build-console.log 2>&1
cp build/nand_3d.pdf output/nand_3d.pdf
