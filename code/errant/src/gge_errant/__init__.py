"""Standalone edit annotation with an explicitly approximate token provider."""

from difflib import SequenceMatcher
from typing import Protocol

from gge_contracts import read_rows, write_rows


class Annotator(Protocol):
    def __call__(self, source: str, corrected: str) -> list[dict]: ...


def token_diff(source: str, corrected: str) -> list[dict]:
    """Return whitespace-token edits; these are not genuine ERRANT labels."""
    before, after = source.split(), corrected.split()
    edits = []
    for operation, start, end, replacement_start, replacement_end in SequenceMatcher(
        None, before, after, autojunk=False
    ).get_opcodes():
        if operation == "equal":
            continue
        edits.append(
            {
                "provider": "token-diff",
                "approximate": True,
                "type": "TOKEN_DIFF_APPROXIMATION",
                "operation": operation,
                "source_start": start,
                "source_end": end,
                "corrected_start": replacement_start,
                "corrected_end": replacement_end,
                "source_text": " ".join(before[start:end]),
                "corrected_text": " ".join(after[replacement_start:replacement_end]),
            }
        )
    return edits


def annotate(input_path: str, output_path: str, annotator: Annotator = token_diff) -> None:
    """Read version 1 rows and write rows with injected edit annotations."""

    def rows():
        for row in read_rows(input_path, ("id", "source", "corrected")):
            yield {**row, "edits": annotator(row["source"], row["corrected"])}

    write_rows(output_path, rows())


__all__ = ["Annotator", "annotate", "token_diff"]
