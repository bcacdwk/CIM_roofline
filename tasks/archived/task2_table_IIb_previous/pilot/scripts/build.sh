#!/bin/sh
set -eu
pilot_root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
task2_root=$(CDPATH= cd -- "$pilot_root/../.." && pwd)
task2_python=${TASK2_PYTHON:-/opt/anaconda3/bin/python}
"$task2_python" "$task2_root/scripts/check_step1.py"
"$task2_python" "$task2_root/shared/scripts/check_counting.py"
"$task2_python" "$task2_root/shared/scripts/generate_IIa.py"
"$task2_python" "$pilot_root/scripts/generate.py"
"$task2_python" "$pilot_root/scripts/check.py"
mkdir -p "$pilot_root/build" "$pilot_root/output"
latexmk -cd -xelatex -interaction=nonstopmode -halt-on-error -outdir=../build "$pilot_root/tex/pilot.zh.tex" > "$pilot_root/build/build-console.log" 2>&1
cp "$pilot_root/build/pilot.zh.pdf" "$pilot_root/output/pilot.zh.pdf"
printf '%s\n' 'Built table_IIb/pilot/output/pilot.zh.pdf'
