"""Collect real offline baseline answers or score evidence-bound semantic reviews."""

import argparse
import json
from pathlib import Path

from neurolab.answer_evaluation import summarize_answers, write_answer_evaluation
from neurolab.ghana import load_ghana


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    collect = commands.add_parser("collect")
    collect.add_argument("--output", type=Path, required=True)
    collect.add_argument("--seed", type=int, default=2026)
    collect.add_argument("--budget", type=int, choices=(1, 2), default=2)
    score = commands.add_parser("score")
    score.add_argument("--records", type=Path, required=True)
    score.add_argument("--reviews", type=Path, required=True)
    score.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "collect":
        summary = write_answer_evaluation(
            load_ghana(), args.output, seed=args.seed, budget=args.budget
        )
    else:
        records = [
            json.loads(line) for line in args.records.read_text().splitlines() if line.strip()
        ]
        summary = summarize_answers(records, json.loads(args.reviews.read_text()))
        with args.output.open("x") as output:
            output.write(json.dumps(summary, indent=2) + "\n")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
