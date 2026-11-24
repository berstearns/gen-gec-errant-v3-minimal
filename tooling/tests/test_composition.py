"""The composed CPU example runs stage APIs through explicit files."""

import json

from gge_composition import run


def test_composed_fixture(tmp_path):
    source = tmp_path / "input.jsonl"
    output = tmp_path / "output.jsonl"
    source.write_text('{"version":1,"id":"demo","prompt":"She go."}\n')
    run(source, output)
    assert json.loads(output.read_text()) == {
        "version": 1,
        "id": "demo",
        "source": "She go.",
        "corrected": "She go.",
        "edits": [],
    }
