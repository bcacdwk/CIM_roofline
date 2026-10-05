#!/bin/sh
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd -P)
exec "${NEUROSIM_PYTHON:-python3}" "$SCRIPT_DIR/step1.py" setup "$@"

