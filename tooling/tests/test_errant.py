"""Focused checks for the standalone edit stage."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code/contracts/src"))
sys.path.insert(0, str(ROOT / "code/errant/src"))

from gge_errant import annotate, token_diff  # noqa: E402


def test_token_diff_is_explicitly_approximate():
    edits = token_diff("I has cat", "I have a cat")
    assert edits == [
        {
            "provider": "token-diff",
            "approximate": True,
            "type": "TOKEN_DIFF_APPROXIMATION",
            "operation": "replace",
            "source_start": 1,
            "source_end": 2,
            "corrected_start": 1,
            "corrected_end": 3,
            "source_text": "has",
            "corrected_text": "have a",
        }
    ]
    assert token_diff("same", "same") == []


def test_annotate_preserves_fields_and_injects_provider(tmp_path):
    source, output = tmp_path / "input.jsonl", tmp_path / "output.jsonl"
    row = {"version": 1, "id": "a", "source": "x", "corrected": "y", "extra": 5}
    source.write_text(json.dumps(row) + "\n")
    annotate(str(source), str(output), lambda before, after: [{"pair": [before, after]}])
    assert json.loads(output.read_text()) == {
        "version": 1,
        "id": "a",
        "source": "x",
        "corrected": "y",
        "extra": 5,
        "edits": [{"pair": ["x", "y"]}],
    }


def test_invalid_contract_row(tmp_path):
    source, output = tmp_path / "input.jsonl", tmp_path / "output.jsonl"
    source.write_text('{"version":2,"id":"a","source":"x","corrected":"y"}\n')
    with pytest.raises(ValueError, match="version 1"):
        annotate(str(source), str(output))


def test_cli(tmp_path):
    source, output = tmp_path / "input.jsonl", tmp_path / "output.jsonl"
    source.write_text('{"version":1,"id":"a","source":"a","corrected":"b"}\n')
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        [str(ROOT / "code/contracts/src"), str(ROOT / "code/errant/src")]
    )
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "gge_errant.cli",
            "--input",
            str(source),
            "--output",
            str(output),
            "--provider",
            "token-diff",
        ],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(output.read_text())["edits"][0]["approximate"] is True
