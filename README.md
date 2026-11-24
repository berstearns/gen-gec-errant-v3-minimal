# Minimal generation → GEC → edit annotation

This is an independent, CPU-first repository. Its runnable code is in `code/`:
`contracts`, `generation`, `gec`, `errant`, and optional `composition` are separate
Python distributions. `tooling/` holds tests and public fixtures. `data/cfgs/`
contains configuration, `data/runs/` receives run output, `data/artifacts/` is for
local model assets, and `build/` receives wheels. Runs, assets and wheels are ignored.

## Run the CPU example

```sh
python -m venv .venv
. .venv/bin/activate
pip install ./code/contracts ./code/generation ./code/gec ./code/errant ./code/composition
mkdir -p data/runs/demo
gge-pipeline --input tooling/fixtures/input.jsonl --output data/runs/demo/annotated.jsonl
cat data/runs/demo/annotated.jsonl
```

Stage commands can also run separately:

```sh
gge-generate --input tooling/fixtures/input.jsonl --output data/runs/demo/generated.jsonl --provider fixture
gge-correct --input data/runs/demo/generated.jsonl --output data/runs/demo/corrected.jsonl --provider identity
gge-annotate --input data/runs/demo/corrected.jsonl --output data/runs/demo/annotated.jsonl --provider token-diff
```

Each stage installs alone with `./code/contracts` and has no heavy runtime dependency.
The fixture generator copies prompts, the identity corrector copies text, and the
token diff reports approximate edits. These commands verify the CPU file pipeline;
they do not run research models or produce genuine ERRANT labels. Python providers
can be injected through the public stage APIs. No model weights or private data are
included.

## Check and build

```sh
./tooling/check.sh
./tooling/build-wheels.sh
```

A frozen native binary is not provided; the console scripts require Python 3.10+.
