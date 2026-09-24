#!/bin/sh
set -eu
task2_root=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
task2_python=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
"$task2_python" "$task2_root/shared/scripts/check_counting.py"
"$task2_python" "$task2_root/shared/scripts/generate_IIa.py"
mkdir -p "$task2_root/shared/build" "$task2_root/shared/output" "$task2_root/table_IIa/build" "$task2_root/table_IIa/output"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$task2_root/shared/tex/counting_method.zh.tex" > "$task2_root/shared/build/build-console.log" 2>&1
cp "$task2_root/shared/build/counting_method.zh.pdf" "$task2_root/shared/output/counting_method.zh.pdf"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$task2_root/table_IIa/tex/table_IIa.tex" > "$task2_root/table_IIa/build/build-console.log" 2>&1
cp "$task2_root/table_IIa/build/table_IIa.pdf" "$task2_root/table_IIa/output/table_IIa.pdf"
printf '%s\n' 'Built shared/output/counting_method.zh.pdf and table_IIa/output/table_IIa.pdf'
