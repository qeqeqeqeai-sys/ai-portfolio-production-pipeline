from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .scenario_semantics import normalize_structural_scenario
from .scenario_semantics import clamp_score


def _checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def compute_scenario_response_signature(scenario: Dict[str, Any], metrics: Dict[str, Any], sensitivity: Dict[str, Any], regime: Dict[str, Any]) -> Dict[str, Any]:
    norm = normalize_structural_scenario(scenario)
    out = {
        "scenario_type": norm["scenario_type"],
        "dominant_response_factors": sorted(metrics.get("dominant_response_factors", [])),
        "affected_nodes": norm["target_nodes"],
        "affected_corridors": norm["target_corridors"],
        "regime_name": str(regime.get("regime_name", "stable")),
        "regime_shift_detected": bool(metrics.get("regime_shift_intensity", 0.0) > 0.0),
        "impact_score": clamp_score(metrics.get("scenario_impact_score", 0.0)),
        "sensitivity_score": clamp_score(sensitivity.get("sensitivity_score", 0.0)),
    }
    out["signature_checksum"] = _checksum(out)
    return out


def compare_scenario_signatures(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "same_regime": a.get("regime_name") == b.get("regime_name"),
        "impact_score_delta": round(abs(float(a.get("impact_score", 0.0)) - float(b.get("impact_score", 0.0))), 6),
        "sensitivity_score_delta": round(abs(float(a.get("sensitivity_score", 0.0)) - float(b.get("sensitivity_score", 0.0))), 6),
        "same_signature_checksum": a.get("signature_checksum") == b.get("signature_checksum"),
    }


def summarize_scenario_signature(sig: Dict[str, Any]) -> Dict[str, Any]:
    return {"scenario_type": sig.get("scenario_type", "baseline"), "regime_name": sig.get("regime_name", "stable"), "impact_score": sig.get("impact_score", 0.0), "signature_checksum": sig.get("signature_checksum", "")}
