"""Grammar correction stage with an injectable text corrector."""

from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Protocol

from gge_contracts import read_rows, write_rows


class Corrector(Protocol):
    """A callable that returns corrected text for one input string."""

    def __call__(self, text: str) -> str: ...


def identity(text: str) -> str:
    """Return text unchanged; this provider does not perform model correction."""
    return text


def correct_rows(rows: Iterable[dict], corrector: Corrector = identity) -> Iterator[dict]:
    """Convert validated generation rows to correction rows."""
    for row in rows:
        corrected = corrector(row["text"])
        if not isinstance(corrected, str):
            raise TypeError("corrector must return a string")
        yield {"id": row["id"], "source": row["text"], "corrected": corrected}


def correct_file(
    input_path: str | Path, output_path: str | Path, corrector: Corrector = identity
) -> None:
    """Read version 1 generation JSONL and write correction JSONL."""
    rows = read_rows(input_path, required=("id", "prompt", "text"))
    write_rows(output_path, correct_rows(rows, corrector))
