"""Canonical Ghana trial data loading with source-row lineage preserved."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SOURCE_RELATIVE = Path("data/raw/ghana/maize_combined_phenotypes.csv")
DICTIONARY_RELATIVE = Path("data/raw/ghana/data_dictionary.csv")

CANONICAL_FIELDS = (
    "source_dataset",
    "source_file",
    "source_sha256",
    "source_row_number",
    "trial_family",
    "genotype_id",
    "year_code",
    "environment_code",
    "location_code",
    "water_regime",
    "replication",
    "block",
    "plot",
    "grain_yield_value",
    "grain_yield_unit",
    "anthesis_days",
    "silking_days",
    "asi_days",
    "plant_height_value",
    "plant_height_unit",
    "ear_height_value",
    "ear_height_unit",
    "ears_per_plant",
    "stay_green_score",
    "raw_extra_json",
)

SOURCE_MAP = {
    "genotype_id": "GENOTYPE",
    "year_code": "ENVT",
    "environment_code": "ENV",
    "water_regime": "CONDITION",
    "replication": "REP",
    "block": "BLK",
    "grain_yield_value": "YIELD",
    "anthesis_days": "POLLEN",
    "silking_days": "SILK",
    "asi_days": "ASI",
    "plant_height_value": "PLHT",
    "ear_height_value": "EHT",
    "ears_per_plant": "EPP",
    "stay_green_score": "STYG",
}

NUMERIC_FIELDS = {
    "grain_yield_value",
    "anthesis_days",
    "silking_days",
    "asi_days",
    "plant_height_value",
    "ear_height_value",
    "ears_per_plant",
    "stay_green_score",
}
MISSING_TOKENS = {"", "na", "n/a", "null", "nan", "."}


@dataclass(frozen=True)
class GhanaDataset:
    records: tuple[dict[str, Any], ...]
    source_file: str
    source_sha256: str
    source_row_count: int
    yield_unit: str
    warnings: tuple[str, ...]
    quarantine_rows: tuple[dict[str, Any], ...]


def _missing(value: str | None) -> bool:
    return value is None or value.strip().lower() in MISSING_TOKENS


def _parse_number(value: str | None, field: str) -> tuple[float | None, str | None]:
    if _missing(value):
        return None, None
    try:
        number = float(value.strip())
    except (TypeError, ValueError):
        return None, f"{field}: not numeric"
    if not math.isfinite(number):
        return None, f"{field}: not finite"
    return number, None


def _yield_unit(path: Path) -> str:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row.get("column") == "YIELD":
                unit = (row.get("unit_or_type") or "").strip()
                if unit:
                    return unit
    raise ValueError("Ghana source dictionary does not define a YIELD unit")


def _map_source_fields(source_row, record, physical_row):
    row_warnings = []
    for canonical, source in SOURCE_MAP.items():
        raw_value = source_row.get(source)
        if canonical in NUMERIC_FIELDS:
            numeric_value, error = _parse_number(raw_value, canonical)
            record[canonical] = numeric_value
            if error:
                warning = f"source row {physical_row}: {error}"
                row_warnings.append(warning)
        else:
            record[canonical] = None if _missing(raw_value) else raw_value.strip()

    return row_warnings


def load_ghana(root: Path = ROOT) -> GhanaDataset:
    """Load and explicitly map the combined source without changing raw files.

    ENVT is retained as `year_code`; it is not interpreted as a calendar year.
    All unmapped source columns are retained verbatim in `raw_extra_json`.
    """
    source_path = root / SOURCE_RELATIVE
    source_bytes = source_path.read_bytes()
    source_hash = hashlib.sha256(source_bytes).hexdigest()
    source_file = SOURCE_RELATIVE.as_posix()
    unit = _yield_unit(root / DICTIONARY_RELATIVE)
    records: list[dict[str, Any]] = []
    warnings: list[str] = []
    quarantine_rows: list[dict[str, Any]] = []

    with source_path.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        reader = csv.DictReader(stream)
        source_columns = reader.fieldnames or []
        for physical_row, source_row in enumerate(reader, start=2):
            row_warnings: list[str] = []
            record: dict[str, Any] = dict.fromkeys(CANONICAL_FIELDS)
            record.update(
                source_dataset="ghana_combined",
                source_file=source_file,
                source_sha256=source_hash,
                source_row_number=physical_row,
                trial_family="ghana_wacci_maize",
                location_code=None,
                grain_yield_unit=unit,
                plant_height_unit="cm",
                ear_height_unit="cm",
            )

            row_warnings = _map_source_fields(source_row, record, physical_row)
            warnings.extend(row_warnings)

            extras = {
                name: source_row.get(name)
                for name in source_columns
                if name not in set(SOURCE_MAP.values())
            }
            record["raw_extra_json"] = json.dumps(
                extras, ensure_ascii=False, sort_keys=True, separators=(",", ":")
            )
            records.append(record)
            if row_warnings:
                quarantine_rows.append(
                    {
                        "source_row_number": physical_row,
                        "raw_source_json": json.dumps(
                            source_row, ensure_ascii=False, sort_keys=True, separators=(",", ":")
                        ),
                        "warnings": " | ".join(row_warnings),
                    }
                )

    return GhanaDataset(
        records=tuple(records),
        source_file=source_file,
        source_sha256=source_hash,
        source_row_count=len(records),
        yield_unit=unit,
        warnings=tuple(warnings),
        quarantine_rows=tuple(quarantine_rows),
    )


def write_normalized(dataset: GhanaDataset, output: Path, quarantine: Path) -> None:
    """Write normalized CSV and a review file for rows with parse warnings."""
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=CANONICAL_FIELDS)
        writer.writeheader()
        writer.writerows(dataset.records)

    quarantine.parent.mkdir(parents=True, exist_ok=True)
    with quarantine.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(
            stream, fieldnames=("source_row_number", "raw_source_json", "warnings")
        )
        writer.writeheader()
        writer.writerows(dataset.quarantine_rows)


def iter_records(dataset: GhanaDataset) -> Iterator[dict[str, Any]]:
    """Yield independent record dictionaries to prevent callers mutating cache."""
    for record in dataset.records:
        yield dict(record)
