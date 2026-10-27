"""Create the canonical, lineage-preserving Ghana table and QA quarantine."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from neurolab.ghana import load_ghana, write_normalized  # noqa: E402


def main() -> int:
    dataset = load_ghana(ROOT)
    processed = ROOT / "data/processed"
    write_normalized(
        dataset,
        processed / "ghana_normalized.csv",
        processed / "ghana_quarantine.csv",
    )
    print(
        f"Normalized {dataset.source_row_count} source records; "
        f"sha256={dataset.source_sha256}; unit={dataset.yield_unit}; "
        f"quarantined={len(dataset.quarantine_rows)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
