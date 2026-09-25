#!/bin/sh
set -eu
attention_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
attention_python=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
export PYTHONDONTWRITEBYTECODE=1
"$attention_python" "$attention_root/scripts/generate.py"
"$attention_python" "$attention_root/scripts/check.py"
mkdir -p "$attention_root/build" "$attention_root/output"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$attention_root/tex/attention.zh.tex" > "$attention_root/build/build-console.log" 2>&1
cp "$attention_root/build/attention.zh.pdf" "$attention_root/output/attention.zh.pdf"
printf '%s\n' 'Built table_IIb/03_attention/output/attention.zh.pdf'
