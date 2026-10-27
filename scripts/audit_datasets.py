"""Reproduce immutable source manifest checks with Python standard library."""

import csv
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect(p):
    with p.open(encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        count = empty = invalid = 0
        for row in reader:
            count += 1
            if not any((v or "").strip() for v in row.values() if isinstance(v, str)):
                empty += 1
            if "YEAR" in row and not (
                (row.get("YEAR") or "").strip().isdigit()
                and len((row.get("YEAR") or "").strip()) == 4
            ):
                invalid += 1
    return {
        "rows": count,
        "columns": columns,
        "fully_empty_rows": empty,
        "invalid_year_rows": invalid,
        "sha256": hashlib.sha256(p.read_bytes()).hexdigest(),
    }


def audit():
    manifest = json.loads((ROOT / "data/manifest.json").read_text())
    errors = []
    for rel, expected in manifest.items():
        actual = inspect(ROOT / rel)
        for key in ["rows", "columns", "fully_empty_rows", "invalid_year_rows", "sha256"]:
            if actual[key] != expected[key]:
                errors.append(f"{rel}: {key}: expected {expected[key]!r}, actual {actual[key]!r}")
        print(
            f"{rel}: {actual['rows']:,} rows, {actual['fully_empty_rows']:,} fully empty, sha256={actual['sha256'][:12]}..."
        )
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("PASS: manifest integrity and source row counts")
    return 0


if __name__ == "__main__":
    sys.exit(audit())
