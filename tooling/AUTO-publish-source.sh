#!/usr/bin/env bash
# WHAT: Publish this clean, independent CPU fixture repository to the named public GitHub remote.
# WHY: The fresh-user acceptance run must clone the exact SHA anonymously from a public URL.
# INPUTS: --dry-run (default), --publish, or --push-update. Requires gh authentication.
# OUTPUTS: dry-run prints the intended repo, SHA and tracked files without mutation;
#          --publish creates the public repository, sets origin and pushes main;
#          --push-update fast-forward pushes a reviewed local commit to origin/main.
#          Exit 0 success; 64 usage; nonzero Git/GitHub failure.
# USAGE (combinatorial):
#   bash tooling/AUTO-publish-source.sh --dry-run
#       # review publication target and source tree
#   bash tooling/AUTO-publish-source.sh --publish
#       # create public remote and push exactly clean main
#   bash tooling/AUTO-publish-source.sh --push-update
#       # fast-forward publish a reviewed correction to the same public remote
#   bash tooling/AUTO-publish-source.sh --unknown
#       # INVALID: exit 64
# RE-RUN SAFETY: refuses a dirty tree or mismatched origin; initial publish
#                refuses an existing target; update never force-pushes.
set -euo pipefail
mode=${1:---dry-run}
if [[ $# -gt 1 || ( "$mode" != --dry-run && "$mode" != --publish && "$mode" != --push-update ) ]]; then
  printf 'usage: bash tooling/AUTO-publish-source.sh [--dry-run|--publish|--push-update]\n' >&2
  exit 64
fi
root=$(cd "$(dirname "$0")/.." && pwd)
cd "$root"
target=berstearns/gen-gec-errant-v3-minimal
remote=https://github.com/$target.git
if [[ -n $(git status --porcelain) ]]; then
  printf 'Source tree is dirty. Commit and review first.\n' >&2
  exit 1
fi
if [[ $(git branch --show-current) != main ]]; then
  printf 'Expected main branch.\n' >&2
  exit 1
fi
if [[ "$mode" == --push-update ]]; then
  if [[ $(git remote get-url origin) != "$remote" ]]; then
    printf 'Origin does not match reviewed publication target.\n' >&2
    exit 1
  fi
else
  if [[ -n $(git remote) ]]; then
    printf 'Expected independent repo with no existing remote.\n' >&2
    exit 1
  fi
  if gh repo view "$target" --json name >/dev/null 2>&1; then
    printf 'Target already exists: %s\n' "$target" >&2
    exit 1
  fi
fi
printf 'target=%s\nurl=%s\nsha=%s\nvisibility=PUBLIC\ntracked_files=%s\n' \
  "$target" "$remote" "$(git rev-parse HEAD)" "$(git ls-files | wc -l)"
if [[ "$mode" == --dry-run ]]; then
  exit 0
fi
if [[ "$mode" == --push-update ]]; then
  git push origin main
  exit 0
fi
gh repo create "$target" --public --source=. --remote=origin --push
printf 'published=%s\n' "$remote"
