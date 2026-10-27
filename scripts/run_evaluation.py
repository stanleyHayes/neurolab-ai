"""Run the disclosed fixed/random/replay tool-selection baseline."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from neurolab.evaluation import write_evaluation  # noqa: E402
from neurolab.ghana import load_ghana  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--budget", type=int, default=2)
    args = parser.parse_args()
    report = write_evaluation(load_ghana(ROOT), ROOT / "eval", seed=args.seed, budget=args.budget)
    for name, result in report["summary"].items():
        print(f"{name}: {result['tasks_completed']}/{result['task_count']} target tools selected")
    print(f"Scientific task fixture count: {len(report['tasks'])}; no LLM answer quality is scored")
    print("Meta comparison: not run; live adapter unavailable")
    print(f"Evidence: {ROOT / 'eval/results.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
