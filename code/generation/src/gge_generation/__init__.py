"""Deterministic fixture generation; this package does not invoke a model."""

import argparse
from typing import Protocol

from gge_contracts import read_rows, write_rows


class Generator(Protocol):
    def __call__(self, prompt: str) -> str: ...


def fixture(prompt: str) -> str:
    """Copy a prompt for a CPU plumbing check; no model is involved."""
    return prompt


def generate_rows(rows, provider: Generator = fixture):
    """Yield input rows with text copied from prompt by the fixture provider."""
    for row in rows:
        if not isinstance(row.get("id"), str) or not isinstance(row.get("prompt"), str):
            raise ValueError("each row needs string id and prompt")
        text = provider(row["prompt"])
        if not isinstance(text, str):
            raise TypeError("generator must return a string")
        yield {**row, "text": text}


def generate_file(input_path, output_path, provider: Generator = fixture):
    """Read version 1 JSONL and write fixture-generated version 1 JSONL."""
    # Read before opening output, including when both paths are the same.
    rows = list(generate_rows(read_rows(input_path, required=("id", "prompt")), provider))
    write_rows(output_path, rows)


def main(argv=None):
    parser = argparse.ArgumentParser(
        prog="gge-generate",
        description="Fixture generation: copies each prompt to text; no model is used.",
    )
    parser.add_argument("--input", required=True, help="version 1 JSONL input path")
    parser.add_argument("--output", required=True, help="version 1 JSONL output path")
    parser.add_argument(
        "--provider", required=True, choices=("fixture",), help="fixture only; no model generation"
    )
    args = parser.parse_args(argv)
    generate_file(args.input, args.output, fixture)


__all__ = ["Generator", "fixture", "generate_rows", "generate_file", "main"]
