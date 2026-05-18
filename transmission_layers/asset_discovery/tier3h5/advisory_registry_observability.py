from __future__ import annotations

import json
from pathlib import Path
from typing import Any

LOG_DIR = Path("logs")
SUMMARY_PATH = LOG_DIR / "tier3h5_advisory_registry_summary.json"


def summarize_advisory_registry(lookup_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    payload = lookup_payload or {}
    support_candidates = payload.get("support_candidates") or []
    propagation = payload.get("propagation_diagnostics") or {}
    support_strength_avg = round(
        sum(float(row.get("support_strength", 0.0)) for row in support_candidates) / len(support_candidates), 4
    ) if support_candidates else 0.0
    summary = {
        "advisory_registry_enabled": bool(payload.get("advisory_registry_enabled", False)),
        "registry_lookup_attempts": int(payload.get("registry_lookup_attempts", 0)),
        "registry_exact_matches": int(payload.get("registry_exact_matches", 0)),
        "registry_no_match": int(payload.get("registry_no_match", 0)),
        "registry_conflicts": int(payload.get("registry_conflicts", 0)),
        "registry_invalid_input": int(payload.get("registry_invalid_input", 0)),
        "registry_support_candidates": len(support_candidates),
        "registry_support_strength_avg": support_strength_avg,
        "advisory_registry_failures": int(payload.get("advisory_registry_failures", 0)),
        "tier3h4_behavior_mutated": False,
        "registry_propagation_candidates_seen": int(propagation.get("registry_propagation_candidates_seen", 0)),
        "registry_propagation_resolution_attempts": int(propagation.get("registry_propagation_resolution_attempts", 0)),
        "registry_propagation_accepted": int(propagation.get("registry_propagation_accepted", 0)),
        "registry_propagation_no_match": int(propagation.get("registry_propagation_no_match", 0)),
        "registry_propagation_conflicts": int(propagation.get("registry_propagation_conflicts", 0)),
        "registry_propagation_invalid_input": int(propagation.get("registry_propagation_invalid_input", 0)),
        "canonical_security_identity_used": int(propagation.get("canonical_security_identity_used", 0)),
        "canonical_issuer_identity_used": int(propagation.get("canonical_issuer_identity_used", 0)),
        "legacy_candidate_identity_preserved": int(propagation.get("legacy_candidate_identity_preserved", 0)),
        "duplicate_legacy_candidates_collapsed_by_canonical_id": int(propagation.get("duplicate_legacy_candidates_collapsed_by_canonical_id", 0)),
        "canonical_identity_conflict_preventions": int(propagation.get("canonical_identity_conflict_preventions", 0)),
        "propagation_identity_mode_counts": dict(propagation.get("propagation_identity_mode_counts", {})),
    }
    summary["status"] = "success" if summary["advisory_registry_failures"] == 0 else "completed_with_findings"
    return summary


def write_advisory_registry_summary(lookup_payload: dict[str, Any] | None = None) -> dict[str, Any]:
    summary = summarize_advisory_registry(lookup_payload)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary
