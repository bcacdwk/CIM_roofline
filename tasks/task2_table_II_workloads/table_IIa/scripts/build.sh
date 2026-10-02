#!/bin/sh
set -eu
export PYTHONDONTWRITEBYTECODE=1
table_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
table_python=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
"$table_python" "$table_root/scripts/generate.py"
"$table_python" "$table_root/scripts/check.py"
mkdir -p "$table_root/build" "$table_root/output"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$table_root/tex/table_IIa.tex" > "$table_root/build/build-console.log" 2>&1
cp "$table_root/build/table_IIa.pdf" "$table_root/output/table_IIa.pdf"
printf '%s\n' 'Built current operator-level table_IIa/output/table_IIa.pdf'
