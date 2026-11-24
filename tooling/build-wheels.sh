#!/usr/bin/env sh
set -eu
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
mkdir -p "$root/build/wheels"
for stage in contracts generation gec errant composition; do
    python -m pip wheel --no-deps --wheel-dir "$root/build/wheels" "$root/code/$stage"
done
