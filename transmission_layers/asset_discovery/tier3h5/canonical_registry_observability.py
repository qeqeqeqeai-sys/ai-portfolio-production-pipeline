from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def emit_tier3h5_diagnostics(summary: dict[str, Any]) -> None:
    print(f"[tier3h5] ingestion_run_id={summary['ingestion_run_id']} source_name={summary['source_name']} status={summary['status']}")
    print(
        "[tier3h5] "
        f"records_seen={summary['records_seen']} records_accepted={summary['records_accepted']} "
        f"records_rejected={summary['records_rejected']} duplicates={summary['duplicate_records_detected']} conflicts={summary['conflict_records_detected']}"
    )
    print(
        "[tier3h5] "
        f"issuer_rows_upserted={summary['issuer_rows_upserted']} security_rows_upserted={summary['security_rows_upserted']} "
        f"provenance_rows_inserted={summary['provenance_rows_inserted']} normalization_failures={summary['normalization_failures']} "
        f"deterministic_id_collisions={summary['deterministic_id_collisions']}"
    )


def write_registry_summary(summary: dict[str, Any], output_path: str = "logs/tier3h5_registry_foundation_summary.json") -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(summary, indent=2, sort_keys=True), encoding="utf-8")
    return out
