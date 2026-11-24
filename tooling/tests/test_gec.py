import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "code/contracts/src"
GEC = ROOT / "code/gec/src"
sys.path[:0] = [str(CONTRACTS), str(GEC)]

from gge_gec import correct_file, correct_rows, identity  # noqa: E402


def test_identity_and_injectable_corrector(tmp_path):
    source = tmp_path / "input.jsonl"
    target = tmp_path / "output.jsonl"
    source.write_text(
        json.dumps({"version": 1, "id": "a", "prompt": "Write", "text": "I go"}) + "\n"
    )

    correct_file(source, target)
    assert [json.loads(line) for line in target.read_text().splitlines()] == [
        {"version": 1, "id": "a", "source": "I go", "corrected": "I go"}
    ]
    assert identity("unchanged") == "unchanged"
    assert list(correct_rows([{"id": "a", "text": "I go"}], lambda text: text + "ne")) == [
        {"id": "a", "source": "I go", "corrected": "I gone"}
    ]


def test_cli_identity(tmp_path):
    source = tmp_path / "input.jsonl"
    output = tmp_path / "output.jsonl"
    source.write_text(
        json.dumps({"version": 1, "id": "a", "prompt": "Write", "text": "I go"}) + "\n"
    )
    env = {**os.environ, "PYTHONPATH": os.pathsep.join((str(CONTRACTS), str(GEC)))}
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "gge_gec.cli",
            "--input",
            str(source),
            "--output",
            str(output),
            "--provider",
            "identity",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert all(row["source"] == row["corrected"] for row in rows)
    assert all(set(row) == {"version", "id", "source", "corrected"} for row in rows)


def test_rejects_invalid_input_and_corrector_output(tmp_path):
    source = tmp_path / "bad.jsonl"
    source.write_text('{"version":1,"id":"x","text":"hello"}\n')
    with pytest.raises(ValueError, match="missing string field"):
        correct_file(source, tmp_path / "output.jsonl")
    with pytest.raises(TypeError, match="must return a string"):
        list(correct_rows([{"id": "x", "text": "hello"}], lambda _: None))
