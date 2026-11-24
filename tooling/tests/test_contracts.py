"""Stage exchange files reject ambiguous or incompatible input."""

import pytest
from gge_contracts import read_rows, write_rows


def test_round_trip_and_reject_duplicate_ids(tmp_path):
    path = tmp_path / "rows.jsonl"
    write_rows(path, [{"id": "one", "prompt": "café"}])
    assert list(read_rows(path, ("id", "prompt"))) == [
        {"version": 1, "id": "one", "prompt": "café"}
    ]
    path.write_text(path.read_text() * 2)
    with pytest.raises(ValueError, match="duplicate id"):
        list(read_rows(path, ("id", "prompt")))


@pytest.mark.parametrize("line", ["{}", '{"version":2,"id":"x","prompt":"p"}', "{oops"])
def test_reject_bad_rows(tmp_path, line):
    path = tmp_path / "bad.jsonl"
    path.write_text(line + "\n")
    with pytest.raises(ValueError):
        list(read_rows(path, ("id", "prompt")))
