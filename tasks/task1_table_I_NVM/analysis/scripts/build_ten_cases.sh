#!/bin/sh
set -eu
HERE=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
TEN_CASE_PYTHON=${TEN_CASE_PYTHON:-/opt/anaconda3/bin/python}
"$TEN_CASE_PYTHON" "$HERE/shared_baseline/scripts/check_shared.py"
"$TEN_CASE_PYTHON" "$HERE/scripts/export_ten_cases.py"
"$TEN_CASE_PYTHON" "$HERE/scripts/check_ten_cases.py"
for CASE in 01_sram_acim 02_sram_dcim 03_nor_2d 04_nand_3d 05_rram 06_mram 07_pcm 08_feram_hfo2 09_gain_cell_edram 10_fenor_3d; do
  sh "$HERE/$CASE/scripts/build.sh"
done
