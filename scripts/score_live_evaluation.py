"""Summarize preserved live-matrix records and bound reviews; never performs inference."""

import argparse
import json
from pathlib import Path

from neurolab.live_scoring import summarize_live_answers


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--records", type=Path, required=True)
    parser.add_argument("--reviews", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    records = [json.loads(row) for row in args.records.read_text().splitlines() if row.strip()]
    summary = summarize_live_answers(records, json.loads(args.reviews.read_text()))
    with args.output.open("x") as output:
        output.write(json.dumps(summary, indent=2, allow_nan=False) + "\n")
    print(
        json.dumps(
            {
                key: summary[key]
                for key in ("record_count", "collection_complete", "reviews_completed")
            }
        )
    )


if __name__ == "__main__":
    main()
