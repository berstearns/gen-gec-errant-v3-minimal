#!/usr/bin/env python3
# WHAT: Bootstrap and execute a pinned, synthetic CPU run from an anonymous HTTPS clone.
# WHY: A fresh-user run must not inherit the developer's checkout, data, models or config.
# INPUTS: bootstrap [--remote HTTPS_GIT_URL --sha FULL_SHA] [--base ABS_PATH]
#         execute --base ABS_PATH; check --base ABS_PATH; retire --base ABS_PATH;
#         selfcheck (no args, development gate).
#         Without --remote/--sha, bootstrap derives both from this clean checkout.
#         No environment variable supplies run parameters or credentials.
# OUTPUTS: bootstrap creates only <base>/{repo,data,configs} and a titled tmux
#          tmuxinator session. execute writes input, wheels, venv, outputs and evidence under
#          data/. configs/.runrc is atomically generated mode 0600 by bootstrap.
#          Exit 0 success; 64 bad arguments; 65 incomplete/unsafe contract;
#          1 clone/build/run/test failure. No paid or remote compute is started.
# USAGE (combinatorial):
#   python tooling/AUTO-user-run.py bootstrap
#     # derive public origin and SHA; generate unique base and session
#   python tooling/AUTO-user-run.py bootstrap --remote https://github.com/OWNER/REPO.git --sha FULL_SHA
#     # explicit public source, generated base and session
#   python tooling/AUTO-user-run.py bootstrap --remote https://github.com/OWNER/REPO.git --sha FULL_SHA --base /home/user/runs/gge-cpu-test
#     # explicit fresh base; session auto-named
#   python tooling/AUTO-user-run.py check --base /home/user/runs/gge-cpu-test
#     # read-only launch-contract gate
#   python tooling/AUTO-user-run.py execute --base /home/user/runs/gge-cpu-test
#     # one-shot build and CPU experiment in the named pane
#   python tooling/AUTO-user-run.py retire --base /home/user/runs/gge-cpu-test
#     # retire a completed user session before a separate fresh run
#   python tooling/AUTO-user-run.py selfcheck
#     # lint, boundary and fixture tests in the current checkout
#   python tooling/AUTO-user-run.py bootstrap --remote /local/repo --sha FULL_SHA
#     # INVALID: local source rejected, exit 64
# RE-RUN SAFETY: bootstrap refuses an existing base; execute refuses existing run
#                evidence; check is read-only and repeatable. No silent repair.

"""Fresh public-clone CPU experiment. No model or data acquisition path exists."""

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
import venv
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

PACKAGES = ("contracts", "generation", "gec", "errant", "composition")
DIST_NAMES = tuple(f"gge-{name}==0.1.0" for name in PACKAGES)
PROVIDERS = {"generation": "fixture", "gec": "identity", "errant": "token-diff"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
USER_SESSION = "gge--gen-gec-err-v3-user"
SYNTHETIC = (
    {"version": 1, "id": "synthetic-1", "prompt": "She go to school."},
    {"version": 1, "id": "synthetic-2", "prompt": "They are here."},
)


class ContractError(Exception):
    """The run root or its .runrc cannot authorize this run."""


def timestamp():
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def git_env():
    # Force an anonymous network check: local Git credential helpers cannot hide a
    # private remote from a fresh user.
    env = os.environ.copy()
    for key in ("GIT_ASKPASS", "SSH_ASKPASS", "GH_TOKEN", "GITHUB_TOKEN", "GIT_CONFIG_COUNT"):
        env.pop(key, None)
    env.update(
        GIT_TERMINAL_PROMPT="0",
        GIT_CONFIG_NOSYSTEM="1",
        GIT_CONFIG_GLOBAL=os.devnull,
        HOME="/nonexistent",
    )
    return env


def command(argv, *, cwd=None, env=None, log=None):
    printable = " ".join(str(part) for part in argv)
    print(f"RUN {printable}", flush=True)
    result = subprocess.run(
        [str(part) for part in argv], cwd=cwd, env=env, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False,
    )
    if log is not None:
        with log.open("a", encoding="utf-8") as stream:
            stream.write(f"$ {printable}\n{result.stdout}\nexit={result.returncode}\n")
    if result.returncode:
        raise RuntimeError(f"command failed ({result.returncode}): {printable}\n{result.stdout}")
    return result.stdout.strip()


def absolute_base(value):
    base = Path(value).expanduser()
    if not base.is_absolute() or base.is_symlink():
        raise ContractError("--base must be an absolute, non-symlink path")
    return base


def public_url(value):
    if not isinstance(value, str):
        raise ValueError("--remote must be a string HTTPS URL")
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.netloc != "github.com" or not parsed.path.endswith(".git"):
        raise ValueError("--remote must be an HTTPS github.com .git URL; local clones are forbidden")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("--remote cannot embed authentication or query parameters")
    return value


def runrc_payload(base, remote, sha):
    return {
        "schema": 1,
        "remote_url": remote,
        "git_sha": sha,
        "base": str(base),
        "repo": str(base / "repo"),
        "data": str(base / "data"),
        "evidence": str(base / "data/evidence"),
        "venv": str(base / "data/venv"),
        "input": str(base / "data/input.jsonl"),
        "output": str(base / "data/annotated.jsonl"),
        "providers": PROVIDERS,
        "dataset": "generated-public-synthetic-v1",
    }


def write_runrc(path, payload):
    if path.exists():
        raise ContractError("configs/.runrc already exists; refusing to replace it")
    fd, temporary = tempfile.mkstemp(prefix=".runrc-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, sort_keys=True, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def check(base):
    if not base.is_dir() or base.is_symlink():
        raise ContractError("run root missing or symlinked")
    if {p.name for p in base.iterdir()} != {"repo", "data", "configs"}:
        raise ContractError("run root must contain exactly repo, data, configs")
    config = base / "configs/.runrc"
    if config.is_symlink() or not config.is_file() or stat.S_IMODE(config.stat().st_mode) != 0o600:
        raise ContractError("configs/.runrc must be a regular mode-0600 file")
    payload = json.loads(config.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema") != 1:
        raise ContractError("unsupported .runrc schema")
    sha = payload.get("git_sha", "")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ContractError(".runrc lacks a full git SHA")
    try:
        remote = public_url(payload.get("remote_url", ""))
    except ValueError as exc:
        raise ContractError(str(exc)) from exc
    expected = runrc_payload(base, remote, sha)
    if payload != expected:
        raise ContractError(".runrc fields differ from the complete derived CPU contract")
    for name in ("repo", "data", "configs"):
        if (base / name).is_symlink():
            raise ContractError(f"{name} cannot be a symlink")
    head = command(("git", "-C", base / "repo", "rev-parse", "HEAD"))
    origin = command(("git", "-C", base / "repo", "remote", "get-url", "origin"))
    dirty = command(("git", "-C", base / "repo", "status", "--short"))
    if head != sha or origin != remote or dirty:
        raise ContractError("clone SHA, origin, or clean-worktree assertion failed")
    print(f"RUNRC_CHECK_PASS sha={sha} base={base}", flush=True)
    return payload


def bootstrap(args):
    source = Path(__file__).resolve().parents[1]
    if (args.remote is None) != (args.sha is None):
        raise ValueError("--remote and --sha must be supplied together")
    if args.remote is None:
        if command(("git", "-C", source, "status", "--short")):
            raise ContractError("bootstrap checkout is dirty; commit first")
        remote = public_url(command(("git", "-C", source, "remote", "get-url", "origin")))
        sha = command(("git", "-C", source, "rev-parse", "HEAD"))
    else:
        remote = public_url(args.remote)
        sha = args.sha
    if not SHA_RE.fullmatch(sha):
        raise ValueError("--sha must be a full 40-character lowercase git SHA")
    stamp = timestamp()
    base = absolute_base(args.base or str(Path.home() / f"runs/gge-cpu-{stamp}"))
    if base.exists():
        raise ContractError(f"fresh run root already exists: {base}")
    if subprocess.run(("tmux", "has-session", "-t", USER_SESSION),
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                      check=False).returncode == 0:
        raise ContractError(f"tmuxinator user session already exists: {USER_SESSION}")
    # Verify reachability without the operator's credential helper before creating
    # state. The SHA must be the public main branch tip for this run.
    advertised = command(("git", "ls-remote", remote, "refs/heads/main"), env=git_env())
    if not advertised or advertised.split()[0] != sha:
        raise ContractError("public main branch does not advertise the requested SHA")
    base.mkdir(parents=True, mode=0o700)
    (base / "data").mkdir(mode=0o700)
    (base / "configs").mkdir(mode=0o700)
    command(("git", "clone", "--branch", "main", "--single-branch", remote, base / "repo"), env=git_env())
    actual = command(("git", "-C", base / "repo", "rev-parse", "HEAD"))
    if actual != sha:
        raise ContractError(f"clone SHA drift: expected {sha}, got {actual}")
    write_runrc(base / "configs/.runrc", runrc_payload(base, remote, actual))
    check(base)
    template = base / "repo/tooling/tmuxinator/gge--gen-gec-err-v3-user.yml"
    env = os.environ.copy()
    env["GGE_USER_RUN_BASE"] = str(base)
    command(("tmuxinator", "start", "-p", template, "--no-attach"), env=env)
    panes = command(("tmux", "list-panes", "-t", f"{USER_SESSION}:run", "-F", "#{pane_title}"))
    if "gge1" not in panes.splitlines():
        raise ContractError(f"named user pane did not come up: {panes}")
    print(f"USER_RUN_STARTED base={base} sha={actual} session={USER_SESSION} pane=gge1")
    print(f"SWITCH tmux switch-client -t {USER_SESSION}")
    print(f"WATCH tmux attach -t {USER_SESSION}  # only from outside tmux")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def execute(base):
    payload = check(base)
    data = base / "data"
    evidence = data / "evidence"
    if evidence.exists() or (data / "input.jsonl").exists():
        raise ContractError("run evidence or input already exists; fresh execution required")
    evidence.mkdir(mode=0o700)
    log = evidence / "commands.log"
    receipt = evidence / "verdict.json"
    result = {"target_sha": payload["git_sha"], "remote_url": payload["remote_url"],
              "base": str(base), "started_utc": datetime.now(timezone.utc).isoformat(),
              "steps": [], "verdict": "FAIL"}
    try:
        input_path = data / "input.jsonl"
        input_path.write_text(
            "".join(json.dumps(row, sort_keys=True) + "\n" for row in SYNTHETIC),
            encoding="utf-8",
        )
        result["steps"].append("generated synthetic input")
        wheels = data / "wheels"
        wheels.mkdir()
        for package in PACKAGES:
            command((sys.executable, "-m", "pip", "wheel", "--no-deps", "--wheel-dir", wheels,
                     base / "repo/code" / package), log=log)
            result["steps"].append(f"built {package} wheel")
        wheel_files = sorted(wheels.glob("*.whl"))
        if len(wheel_files) != len(PACKAGES):
            raise RuntimeError("expected exactly five freshly built wheels")
        result["wheel_sha256"] = {file.name: digest(file) for file in wheel_files}
        venv.EnvBuilder(with_pip=True).create(data / "venv")
        python = data / "venv/bin/python"
        cli = data / "venv/bin"
        command((python, "-m", "pip", "install", "--no-index", "--find-links", wheels,
                 *DIST_NAMES), log=log)
        result["steps"].append("installed five local wheels")
        generated = data / "generated.jsonl"
        corrected = data / "corrected.jsonl"
        annotated = data / "annotated.jsonl"
        composed = data / "composed.jsonl"
        command((cli / "gge-generate", "--input", input_path, "--output", generated,
                 "--provider", "fixture"), log=log)
        command((cli / "gge-correct", "--input", generated, "--output", corrected,
                 "--provider", "identity"), log=log)
        command((cli / "gge-annotate", "--input", corrected, "--output", annotated,
                 "--provider", "token-diff"), log=log)
        command((cli / "gge-pipeline", "--input", input_path, "--output", composed), log=log)
        if annotated.read_bytes() != composed.read_bytes():
            raise RuntimeError("individual and composed CLI outputs differ")
        rows = [json.loads(line) for line in annotated.read_text(encoding="utf-8").splitlines()]
        expected = [{"version": 1, "id": row["id"], "source": row["prompt"],
                     "corrected": row["prompt"], "edits": []} for row in SYNTHETIC]
        if rows != expected:
            raise RuntimeError("CPU fixture output differs from the expected field-level contract")
        result["steps"].append("three stage CLIs and composition matched")
        result["input_sha256"] = digest(input_path)
        result["output_sha256"] = digest(annotated)
        result["verdict"] = "PASS"
        print(f"CPU_EXPERIMENT_PASS sha={payload['git_sha']} output={annotated}")
    except Exception as exc:
        result["failure"] = str(exc)
        print(f"CPU_EXPERIMENT_FAIL {exc}", file=sys.stderr)
        raise
    finally:
        result["finished_utc"] = datetime.now(timezone.utc).isoformat()
        receipt.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def retire(base):
    check(base)
    receipt = base / "data/evidence/verdict.json"
    if not receipt.is_file() or json.loads(receipt.read_text(encoding="utf-8")).get("verdict") != "PASS":
        raise ContractError("only a completed PASS user session can be retired")
    command(("tmux", "kill-session", "-t", USER_SESSION))
    print(f"USER_SESSION_RETIRED session={USER_SESSION} evidence={receipt}")


def selfcheck():
    root = Path(__file__).resolve().parents[1]
    command(("ruff", "check", "code", "tooling"), cwd=root)
    from boundary_checks import check as check_boundaries

    failures = check_boundaries()
    if failures:
        raise RuntimeError("stage import boundaries: " + "; ".join(failures))
    print("stage import boundaries: PASS")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join(str(root / "code" / name / "src") for name in PACKAGES)
    print(command((sys.executable, "-m", "pytest", "-q", "tooling/tests"), cwd=root, env=env))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="mode", required=True)
    boot = sub.add_parser("bootstrap", help="create fresh root, clone public SHA, and start user tmux")
    boot.add_argument("--remote")
    boot.add_argument("--sha")
    boot.add_argument("--base")
    for name in ("check", "execute", "retire"):
        part = sub.add_parser(name)
        part.add_argument("--base", required=True)
    sub.add_parser("selfcheck")
    args = parser.parse_args(argv)
    try:
        if args.mode == "bootstrap":
            bootstrap(args)
        elif args.mode == "check":
            check(absolute_base(args.base))
        elif args.mode == "selfcheck":
            selfcheck()
        elif args.mode == "retire":
            retire(absolute_base(args.base))
        else:
            execute(absolute_base(args.base))
    except (ContractError, ValueError) as exc:
        print(f"CONTRACT_FAIL {exc}", file=sys.stderr)
        return 65 if isinstance(exc, ContractError) else 64
    except Exception as exc:
        print(f"RUN_FAIL {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
