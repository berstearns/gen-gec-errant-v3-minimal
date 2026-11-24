#!/usr/bin/env sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
cd "$root"
python tooling/check_boundaries.py
PYTHONPATH=code/contracts/src:code/generation/src:code/gec/src:code/errant/src:code/composition/src python -m pytest -q tooling/tests
