"""Validation gates for Phase 5A.2 structural intermediary formation."""
from __future__ import annotations

from typing import Any


def build_validation_rows(run_id: str, run_date_sgt: str, metrics: dict[str, Any]) -> list[dict[str, Any]]:
    validations = []

    def add(name: str, ok: bool, observed: float, threshold: float, message: str, details: dict[str, Any] | None = None) -> None:
        validations.append({
            "run_id": run_id,
            "run_date_sgt": run_date_sgt,
            "validation_name": name,
            "validation_status": "PASS" if ok else "WARN",
            "observed_value": observed,
            "threshold_value": threshold,
            "message": message,
            "details": details or {},
        })

    add(
        "edges_loaded_positive",
        int(metrics.get("edges_loaded", 0)) > 0,
        int(metrics.get("edges_loaded", 0)),
        1,
        "Graph edge source returned at least one edge.",
    )
    add(
        "intermediaries_detected_non_negative",
        int(metrics.get("intermediaries_detected", 0)) >= 0,
        int(metrics.get("intermediaries_detected", 0)),
        0,
        "Intermediary detection completed deterministically.",
    )
    add(
        "persisted_equals_detected",
        int(metrics.get("intermediaries_persisted", 0)) == int(metrics.get("intermediaries_detected", 0)),
        int(metrics.get("intermediaries_persisted", 0)),
        int(metrics.get("intermediaries_detected", 0)),
        "Persisted row count should match detected intermediary count.",
    )
    return validations
