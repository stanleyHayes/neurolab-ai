"""Record synthetic containment contracts; never invokes a provider."""

import argparse
import json
from pathlib import Path

from neurolab.adversarial_evaluation import collect_probes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    # Exclusive creation preserves earlier successful and failed collections.
    with args.output.open("x") as stream:
        result = collect_probes()
        stream.write(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                "protocol": result["protocol"],
                "records": len(result["records"]),
                "all_contract_checks_passed": result["all_contract_checks_passed"],
                "live_model_calls": 0,
            }
        )
    )
    return 0 if result["all_contract_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
