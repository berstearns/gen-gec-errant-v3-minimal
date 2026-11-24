"""Explicit file based composition of independent stage APIs."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory


def run(input_path, output_path):
    from gge_errant import annotate
    from gge_gec import correct_file
    from gge_generation import generate_file

    with TemporaryDirectory() as tmp:
        generated = Path(tmp) / "generated.jsonl"
        corrected = Path(tmp) / "corrected.jsonl"
        generate_file(input_path, generated)
        correct_file(generated, corrected)
        annotate(corrected, output_path)


def main():
    parser = argparse.ArgumentParser(description="CPU fixture composition of GGE stages")
    parser.add_argument("--input", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    run(args.input, args.output)
