"""Minimal versioned JSONL exchange format for GGE stages."""

import json
from pathlib import Path

VERSION = 1


def read_rows(path, required):
    seen = set()
    with Path(path).open(encoding="utf-8") as stream:
        for number, line in enumerate(stream, 1):
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{number}: invalid JSON") from exc
            if not isinstance(row, dict) or row.get("version") != VERSION:
                raise ValueError(f"{path}:{number}: expected object with version 1")
            if not all(isinstance(row.get(key), str) for key in required):
                raise ValueError(f"{path}:{number}: missing string field")
            if not row.get("id") or row["id"] in seen:
                raise ValueError(f"{path}:{number}: empty or duplicate id")
            seen.add(row["id"])
            yield row


def write_rows(path, rows):
    with Path(path).open("w", encoding="utf-8") as stream:
        for row in rows:
            payload = {**row, "version": VERSION}
            stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
