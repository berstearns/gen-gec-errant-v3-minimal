"""Focused checks for the standalone fixture generation stage."""

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "code" / "contracts" / "src"))
sys.path.insert(0, str(ROOT / "code" / "generation" / "src"))

from gge_generation import generate_file, generate_rows  # noqa: E402


def test_fixture_rows_copy_prompt_and_preserve_fields():
    row = {"version": 1, "id": "one", "prompt": "She go.", "source": "test"}
    assert list(generate_rows([row])) == [
        {"version": 1, "id": "one", "prompt": "She go.", "source": "test", "text": "She go."}
    ]
    assert "text" not in row


def test_file_round_trip_and_same_path(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"version":1,"id":"one","prompt":"Café"}\n', encoding="utf-8")
    generate_file(path, path)
    assert json.loads(path.read_text(encoding="utf-8")) == {
        "version": 1,
        "id": "one",
        "prompt": "Café",
        "text": "Café",
    }


def test_invalid_input_does_not_write_output(tmp_path):
    input_path = tmp_path / "input.jsonl"
    output_path = tmp_path / "output.jsonl"
    input_path.write_text(
        '{"version":1,"id":"one","prompt":"ok"}\n{"version":1,"id":"one","prompt":"dup"}\n'
    )
    with pytest.raises(ValueError, match="duplicate id"):
        generate_file(input_path, output_path)
    assert not output_path.exists()


def test_cli_fixture(tmp_path):
    output_path = tmp_path / "output.jsonl"
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(
        (
            str(ROOT / "code" / "generation" / "src"),
            str(ROOT / "code" / "contracts" / "src"),
        )
    )
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from gge_generation import main; main()",
            "--input",
            str(ROOT / "tooling" / "fixtures" / "input.jsonl"),
            "--output",
            str(output_path),
            "--provider",
            "fixture",
        ],
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    rows = [json.loads(line) for line in output_path.read_text().splitlines()]
    assert [row["text"] for row in rows] == ["She go to school.", "They are here."]
    assert all(row["text"] == row["prompt"] for row in rows)


def test_injected_generator_and_bad_output():
    from gge_generation import generate_rows

    row = {"id": "x", "prompt": "Go"}
    assert list(generate_rows([row], lambda prompt: prompt + " now"))[0]["text"] == "Go now"
    with pytest.raises(TypeError, match="generator must return a string"):
        list(generate_rows([row], lambda prompt: None))
