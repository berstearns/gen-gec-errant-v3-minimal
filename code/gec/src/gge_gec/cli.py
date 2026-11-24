"""Command line entry point for grammar correction."""

import argparse

from . import correct_file, identity


def main() -> None:
    parser = argparse.ArgumentParser(description="Correct GGE generation JSONL")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--provider", required=True, choices=("identity",))
    args = parser.parse_args()
    correct_file(args.input, args.output, identity)


if __name__ == "__main__":
    main()
