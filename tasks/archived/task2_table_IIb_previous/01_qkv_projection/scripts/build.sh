#!/bin/sh
set -eu
qkv_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
qkv_python=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
export PYTHONDONTWRITEBYTECODE=1
"$qkv_python" "$qkv_root/scripts/generate.py"
"$qkv_python" "$qkv_root/scripts/check.py"
mkdir -p "$qkv_root/build" "$qkv_root/output/pdf"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$qkv_root/tex/qkv.zh.tex" > "$qkv_root/build/build-console.log" 2>&1
cp "$qkv_root/build/qkv.zh.pdf" "$qkv_root/output/pdf/qkv.zh.pdf"
printf '%s\n' 'Built table_IIb/01_qkv_projection/output/pdf/qkv.zh.pdf'
