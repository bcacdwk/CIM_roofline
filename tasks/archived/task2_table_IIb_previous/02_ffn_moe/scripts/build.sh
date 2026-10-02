#!/bin/sh
set -eu
local_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
task2_python=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
export PYTHONDONTWRITEBYTECODE=1
"$task2_python" "$local_root/scripts/generate.py"
"$task2_python" "$local_root/scripts/check.py"
mkdir -p "$local_root/build" "$local_root/output"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$local_root/tex/ffn_moe.zh.tex" > "$local_root/build/build-console.log" 2>&1
cp "$local_root/build/ffn_moe.zh.pdf" "$local_root/output/ffn_moe.zh.pdf"
printf '%s\n' 'Built table_IIb/02_ffn_moe/output/ffn_moe.zh.pdf'
