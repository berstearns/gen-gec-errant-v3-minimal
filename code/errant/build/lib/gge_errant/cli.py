"""Command line entry point for edit annotation."""

import argparse

from . import annotate, token_diff


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Annotate version 1 JSONL with approximate token edits"
    )
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provider", required=True, choices=("token-diff",))
    args = parser.parse_args()
    annotate(args.input, args.output, token_diff)


if __name__ == "__main__":
    main()
