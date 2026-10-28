"""Execute only a reviewed frozen live matrix; never loads .env or changes spend policy."""

import argparse
import json
import os
from pathlib import Path

from neurolab.ghana import load_ghana
from neurolab.live_evaluation import collect_live_matrix, validate_live_protocol
from neurolab.store import RunStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--owner", required=True, help="Existing operator-verified server owner ID")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--preflight-only", action="store_true")
    args = parser.parse_args()
    if not args.preflight_only and args.output is None:
        parser.error("--output is required for collection")
    manifest = json.loads(args.protocol.read_text())
    root = Path(__file__).resolve().parents[1]
    store = RunStore(os.environ["DATABASE_URL"])
    try:
        dataset = load_ghana(root)
        if args.preflight_only:
            validate_live_protocol(manifest, dataset, store, args.owner, root)
            summary = {"preflight": "passed", "model_calls": 0, "collection_started": False}
        else:
            summary = collect_live_matrix(manifest, dataset, store, args.owner, args.output, root)
        print(json.dumps(summary, indent=2))
    finally:
        store.close()


if __name__ == "__main__":
    main()
