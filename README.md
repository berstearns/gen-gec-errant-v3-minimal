# Minimal generation → GEC → edit annotation

This repository contains five small Python distributions under `code/`: a
versioned JSONL contract, three independent stages, and optional composition.
`tooling/` contains the reproducible CPU runner and public tests. Repository
`data/` and `build/` are placeholders for local development; the fresh-user run
writes only under its separate `~/runs/.../data/` and `configs/` directories.

## Fresh user CPU run

Requirements: GNU/Linux, Python 3.10+, Git, tmux, tmuxinator, the `pane-name`
shell function, and network access to this
public GitHub repository and PyPI. No GPU, credentials, private dataset, model
weights, or remote compute service is used. The run intentionally uses a tiny
synthetic input and deterministic fixture providers.

Get the published source, then run the tracked bootstrap:

```sh
git clone https://github.com/berstearns/gen-gec-errant-v3-minimal.git gge-cpu-bootstrap
cd gge-cpu-bootstrap
python tooling/AUTO-user-run.py bootstrap
```

The tracked program derives `origin` and the current clean commit, checks that
the same SHA is anonymously advertised on the public `main` branch, creates a
fresh `~/runs/gge-cpu-<UTC timestamp>/` with exactly `repo/`, `data/`, and
`configs/`, clones that public SHA, and atomically generates a mode-0600
`configs/.runrc`. It prints the new base and session switch command.
The tmuxinator session `gge--gen-gec-err-v3-user`, window `run`, pane `gge1`
runs `AUTO-user-run.py execute` from the fresh clone. Switch between it and
the dev session with `tmux switch-client -t gge--gen-gec-err-v3-user` and
`tmux switch-client -t gge--gen-gec-err-v2` from inside tmux.
The program creates synthetic input in `data/`, builds five wheels from the
clone, installs them in `data/venv`, runs all three stage CLIs plus composition,
compares field-level output, and writes `data/evidence/verdict.json` and
`commands.log`. A failed step produces a FAIL receipt; it does not retry using
local files or download any dataset or model.

For an explicit fresh root, use:

```sh
python tooling/AUTO-user-run.py bootstrap --base /absolute/path/under/runs
```

The root must not already exist. `check --base` is read-only; `execute --base`
is one-shot and normally runs inside tmux. All paths in `.runrc` are derived
from the run root and cloned SHA. There are no secrets to autofill for this CPU
experiment. The program refuses local clone URLs and relative run roots.

## Development gate

```sh
python tooling/AUTO-user-run.py selfcheck
```

The fixture generator copies prompts, the identity corrector copies text, and
the token diff reports approximate edits. Passing the CPU run proves packaging,
stage interfaces, and file composition. It does not prove model generation,
grammar correction, or genuine ERRANT classification. Python providers can be
injected through the public stage APIs. A native binary is not provided.

See [the run plan](tooling/USER-RUN-PLAN.md) for failure branches and the command
contract. The fresh-user run is complete only when its pinned-SHA evidence
receipt and an independent tester verdict agree.
