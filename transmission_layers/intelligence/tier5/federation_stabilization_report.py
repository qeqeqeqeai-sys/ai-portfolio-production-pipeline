from __future__ import annotations

from typing import Any

from .federation_determinism import stable_checksum


def build_federation_stabilization_report(integrity: dict[str, Any]) -> dict[str, Any]:
    classification = str(integrity.get("federation_integrity_classification", "stabilization_required"))
    dominant = str(integrity.get("dominant_integrity_factor", "federation_stabilization_gap_score"))
    templates = {
        "report_template": "Tier5H stabilization report: deterministic integrity contracts evaluated.",
        "classification_template": f"Tier5H classification: {classification}.",
        "dominant_factor_template": f"Tier5H dominant factor: {dominant}.",
    }
    return {
        **templates,
        "federation_stabilization_report_checksum": stable_checksum(templates, prefix="tier5h_report"),
    }
