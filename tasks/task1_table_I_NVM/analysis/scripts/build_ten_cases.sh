#!/bin/sh
# Verify source-derived artifacts before compiling the current unified cards.
# Regeneration is explicit: run each changed calculator --emit, then the
# exporter --emit and independent checker --emit before invoking this build.
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TEN_CASE_PYTHON=${TEN_CASE_PYTHON:-/opt/anaconda3/bin/python}
"$TEN_CASE_PYTHON" "$HERE/shared_baseline/scripts/check_shared.py"
for PAIR in \
  01_sram_acim:check_sram_acim \
  02_sram_dcim:check_sram_dcim \
  03_nor_2d:check_nor \
  04_nand_3d:check_nand \
  05_rram:check_rram \
  06_mram:check_mram \
  07_pcm:check_pcm \
  08_feram_hfo2:check_feram \
  09_gain_cell_edram:check_gain_cell_edram \
  10_fenor_3d:check_fenor; do
  CASE=${PAIR%:*}
  CHECK=${PAIR#*:}
  "$TEN_CASE_PYTHON" "$HERE/$CASE/scripts/$CHECK.py"
done
"$TEN_CASE_PYTHON" "$HERE/scripts/export_ten_cases.py"
"$TEN_CASE_PYTHON" "$HERE/scripts/check_ten_cases.py"
for CASE in shared_baseline 01_sram_acim 02_sram_dcim 03_nor_2d 04_nand_3d 05_rram 06_mram 07_pcm 08_feram_hfo2 09_gain_cell_edram 10_fenor_3d; do
  case_name=${CASE#??_}
  if [ "$CASE" = shared_baseline ]; then case_name=shared_baseline; fi
  case_output="$HERE/$CASE/output"
  if [ "$CASE" = 05_rram ]; then case_output="$case_output/pdf"; fi
  mkdir -p "$HERE/$CASE/build" "$case_output"
  (
    cd "$HERE/$CASE/tex"
    latexmk -xelatex -interaction=nonstopmode -halt-on-error \
      -outdir=../build "$case_name.tex" > ../build/build-console.log 2>&1
  )
  cp "$HERE/$CASE/build/$case_name.pdf" "$case_output/$case_name.pdf"
  "$TEN_CASE_PYTHON" "$HERE/$CASE/scripts/render_pdf.py"
done
