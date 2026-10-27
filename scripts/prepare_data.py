"""Lossless-ish CSV staging: remove fully empty IITA irrigation records only.
Retains source row number and all original header fields (including unnamed third column).
Never treats this as a validated paired irrigation/drought experiment.
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def prepare():
    src = ROOT / "data/raw/iita/m28fulli_irrigation-data.csv"
    out = ROOT / "data/processed/iita_full_irrigation_clean.csv"
    out.parent.mkdir(exist_ok=True, parents=True)
    n = empty = kept = 0
    with (
        src.open(encoding="utf-8-sig", newline="", errors="replace") as f,
        out.open("w", encoding="utf-8", newline="") as g,
    ):
        r = csv.reader(f)
        headers = next(r)
        safe_headers = [h if h else f"unnamed_column_{i + 1}" for i, h in enumerate(headers)]
        w = csv.writer(g)
        w.writerow(["source_row_number"] + safe_headers)
        for n, row in enumerate(r, start=2):
            if not any(x.strip() for x in row):
                empty += 1
                continue
            if len(row) != len(headers):
                raise ValueError(f"Ragged nonempty row {n}: {len(row)} columns vs {len(headers)}")
            w.writerow([n] + row)
            kept += 1
    report = {
        "input_rows": n - 1,
        "fully_empty_rows_removed": empty,
        "output_rows": kept,
        "source": str(src.relative_to(ROOT)),
        "output": str(out.relative_to(ROOT)),
        "notes": "No other rows filtered; no regime joins or unit inference",
    }
    (ROOT / "data/processed/preparation_report.json").write_text(json.dumps(report, indent=2))
    if (kept, empty) != (960, 336953):
        raise ValueError(
            "Unexpected irrigation row counts: "
            f"kept={kept} (expected 960), empty={empty} (expected 336953)"
        )
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    prepare()
