"""Apply reviewed server budget settings with compare-and-swap; no inference."""

import argparse
import os

from neurolab.model_spend import ModelSpendError, SpendPolicy, apply_policy
from neurolab.store import RunStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--expect-sha256", required=True, help="Current policy digest, or empty before first use"
    )
    args = parser.parse_args()
    store = None
    try:
        policy = SpendPolicy.from_environment()
        store = RunStore(os.getenv("DATABASE_URL", "postgresql:///neurolab"))
        digest = apply_policy(store, policy, args.expect_sha256)
    except ModelSpendError as error:
        parser.exit(1, str(error) + "\n")
    finally:
        if store is not None:
            store.close()
    print(
        "Applied reviewed spending policy "
        + digest
        + "; reservations retained; no inference requested."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
