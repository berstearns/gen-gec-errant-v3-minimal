#!/usr/bin/env bash
# WHAT: Execute the README fresh-user clone and bootstrap commands from ~/runs.
# WHY: The documented entry point must work without using the developer checkout.
# INPUTS: none. Requires an absent ~/runs/gge-cpu-bootstrap path and published main.
# OUTPUTS: creates ~/runs/gge-cpu-bootstrap, then AUTO-user-run.py creates a new
#          three-directory run root and starts the named user tmuxinator session.
#          Exit 0 only if the documented bootstrap returns 0.
# USAGE (combinatorial):
#   bash tooling/AUTO-docs-fresh-user.sh
#       # execute README clone, cd and bootstrap commands verbatim
#   bash tooling/AUTO-docs-fresh-user.sh extra
#       # INVALID: exit 64
# RE-RUN SAFETY: refuses an existing bootstrap checkout; never overwrites or
#                deletes a prior run. Use a fresh environment for repetition.
set -euo pipefail
if [[ $# -ne 0 ]]; then
  printf 'usage: bash tooling/AUTO-docs-fresh-user.sh\n' >&2
  exit 64
fi
mkdir -p "$HOME/runs"
cd "$HOME/runs"
if [[ -e gge-cpu-bootstrap ]]; then
  printf 'Existing bootstrap checkout: %s/runs/gge-cpu-bootstrap\n' "$HOME" >&2
  exit 1
fi
git clone https://github.com/berstearns/gen-gec-errant-v3-minimal.git gge-cpu-bootstrap
cd gge-cpu-bootstrap
python tooling/AUTO-user-run.py bootstrap
