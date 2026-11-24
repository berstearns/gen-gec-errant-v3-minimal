"""The fresh-user contract rejects local sources and unsafe run manifests."""

import importlib.util
import json
import stat
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "AUTO-user-run.py"
SPEC = importlib.util.spec_from_file_location("auto_user_run", SCRIPT)
run = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(run)


def test_local_source_is_rejected():
    with pytest.raises(ValueError, match="local clones are forbidden"):
        run.public_url("/home/user/project")


def test_runrc_writer_is_atomic_and_mode_600(tmp_path):
    path = tmp_path / ".runrc"
    payload = {"schema": 1, "git_sha": "a" * 40}
    run.write_runrc(path, payload)
    assert json.loads(path.read_text()) == payload
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    with pytest.raises(run.ContractError, match="already exists"):
        run.write_runrc(path, payload)


def test_check_rejects_incomplete_contract_before_running_git(tmp_path):
    for name in ("repo", "data", "configs"):
        (tmp_path / name).mkdir()
    config = tmp_path / "configs/.runrc"
    payload = run.runrc_payload(tmp_path, "https://github.com/x/y.git", "a" * 40)
    payload.pop("providers")
    run.write_runrc(config, payload)
    with pytest.raises(run.ContractError, match="fields differ"):
        run.check(tmp_path)
