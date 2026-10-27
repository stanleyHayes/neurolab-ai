"""Hash-verified source-manifest inventory, never pooled scientific observations."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path


def source_inventory(root: Path) -> dict:
    payload = (root / "data/manifest.json").read_bytes()
    manifest = json.loads(payload)
    result = []
    for path, metadata in sorted(manifest.items()):
        source = root / path
        if not source.resolve().is_relative_to((root / "data/raw").resolve()):
            raise ValueError("Source inventory path is outside raw staging")
        if not 0 <= metadata["fully_empty_rows"] <= metadata["rows"]:
            raise ValueError("Invalid source inventory record counts")
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        if digest != metadata["sha256"]:
            raise ValueError(f"Source inventory hash mismatch: {path}")
        enabled = path == "data/raw/ghana/maize_combined_phenotypes.csv"
        if "/iita/" in path:
            reason = "Audited reference only; matched year/replicate/environment semantics and cross-source genotype identity are not proven. No pooling or row-order joining."
        elif "dictionary" in path:
            reason = "Source metadata, not independent plot observations."
        else:
            reason = (
                "Canonical combined analysis source."
                if enabled
                else "Regime component overlaps the combined source; never add as independent observations."
            )
        result.append(
            {
                "source_file": path,
                "source_sha256": digest,
                "physical_rows": metadata["rows"],
                "fully_empty_rows": metadata["fully_empty_rows"],
                "substantive_rows": metadata["rows"] - metadata["fully_empty_rows"],
                "original_columns": metadata["columns"],
                "analysis_enabled": enabled,
                "eligibility_reason": reason,
                "count_provenance": "Audited manifest counts, verified against current source-byte hash at tool execution",
            }
        )
    return {"files": result, "manifest_sha256": hashlib.sha256(payload).hexdigest()}
