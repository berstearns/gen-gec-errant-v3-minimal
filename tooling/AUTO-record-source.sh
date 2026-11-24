#!/usr/bin/env bash
# WHAT: Commit the known minimal source/docs/tooling paths after a passing gate.
# WHY: A reproducible public SHA is needed before any fresh-user clone; inline
#      git-add/commit commands obscure exactly what entered the published tree.
# INPUTS: $1 commit message (required, non-empty). No environment values used.
# OUTPUTS: stages README, ignore policy, code, data placeholders, tooling and
#          build README; creates one local Git commit. Exit 0 success; 64 usage;
#          nonzero Git failure. Does not push or publish.
# USAGE (combinatorial):
#   bash tooling/AUTO-record-source.sh 'Add fresh user CPU bootstrap'
#       # commit allowed source paths
#   bash tooling/AUTO-record-source.sh 'Revise CPU runbook'
#       # same paths for a later documented revision
#   bash tooling/AUTO-record-source.sh
#       # INVALID: missing message, exit 64
#   bash tooling/AUTO-record-source.sh ''
#       # INVALID: empty message, exit 64
# RE-RUN SAFETY: refuses to commit if no staged delta exists; never amends or
#                force-pushes. The caller reviews the source diff first.
set -euo pipefail
if [[ $# -ne 1 || -z "$1" ]]; then
  printf 'usage: bash tooling/AUTO-record-source.sh MESSAGE\n' >&2
  exit 64
fi
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
git add .gitignore README.md build/README.md code data tooling
if git diff --cached --quiet; then
  printf 'No source changes to commit.\n' >&2
  exit 1
fi
git diff --cached --stat
git commit -m "$1"
