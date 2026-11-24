"""Check that standalone stage packages do not import peer stages or composition."""

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "code"
STAGES = {"generation", "gec", "errant"}


def check():
    failures = []
    for stage in sorted(STAGES):
        root = ROOT / stage / "src"
        forbidden = {"gge_" + peer for peer in STAGES - {stage}} | {
            "gge_composition",
            "gen_gec_errant",
        }
        for file in root.rglob("*.py"):
            tree = ast.parse(file.read_text(encoding="utf-8"), filename=str(file))
            for node in ast.walk(tree):
                names = []
                if isinstance(node, ast.Import):
                    names = [alias.name for alias in node.names]
                elif isinstance(node, ast.ImportFrom) and node.module:
                    names = [node.module]
                for name in names:
                    if name.split(".")[0] in forbidden:
                        failures.append(f"{file}:{node.lineno}: {name}")
    return failures


if __name__ == "__main__":
    errors = check()
    if errors:
        raise SystemExit("\n".join(errors))
    print("v3 stage import boundaries: PASS")
