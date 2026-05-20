from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, Iterable, List

VALID_SCENARIO_TYPES = {
    "baseline",
    "corridor_removed",
    "node_stressed",
    "chokepoint_stressed",
    "corridor_degraded",
    "suppression_applied",
    "resilience_reduced",
    "fragmentation_probe",
    "overload_probe",
}


def round_score(value: Any) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        v = 0.0
    return round(v, 6)


def clamp_score(value: Any, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, round_score(value)))


def _stable_list(values: Iterable[Any]) -> List[str]:
    return sorted({str(v) for v in values if str(v).strip()})


def _stable_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for key in sorted(metadata.keys(), key=lambda k: str(k)):
        value = metadata[key]
        if isinstance(value, float):
            out[str(key)] = round_score(value)
        elif isinstance(value, list):
            out[str(key)] = sorted(value, key=lambda v: str(v))
        else:
            out[str(key)] = value
    return out


def normalize_structural_scenario(scenario: Dict[str, Any] | None) -> Dict[str, Any]:
    payload = scenario or {}
    scenario_id = str(payload.get("scenario_id") or "scenario_default")
    scenario_name = str(payload.get("scenario_name") or scenario_id)
    scenario_type = str(payload.get("scenario_type") or "baseline")
    metadata = payload.get("metadata") if isinstance(payload.get("metadata"), dict) else {}
    normalized = {
        "scenario_id": scenario_id,
        "scenario_name": scenario_name,
        "scenario_type": scenario_type if scenario_type in VALID_SCENARIO_TYPES else "baseline",
        "target_nodes": _stable_list(payload.get("target_nodes", [])),
        "target_corridors": _stable_list(payload.get("target_corridors", [])),
        "perturbation_strength": clamp_score(payload.get("perturbation_strength", 0.0)),
        "metadata": _stable_metadata(metadata),
    }
    normalized["diagnostics"] = {
        "requested_scenario_type": scenario_type,
        "scenario_type_supported": scenario_type in VALID_SCENARIO_TYPES,
    }
    normalized["scenario_checksum"] = compute_scenario_checksum(normalized)
    return normalized


def compute_scenario_checksum(scenario: Dict[str, Any]) -> str:
    checksum_payload = {
        "scenario_id": str(scenario.get("scenario_id", "")),
        "scenario_name": str(scenario.get("scenario_name", "")),
        "scenario_type": str(scenario.get("scenario_type", "baseline")),
        "target_nodes": _stable_list(scenario.get("target_nodes", [])),
        "target_corridors": _stable_list(scenario.get("target_corridors", [])),
        "perturbation_strength": clamp_score(scenario.get("perturbation_strength", 0.0)),
        "metadata": _stable_metadata(scenario.get("metadata") or {}),
    }
    raw = json.dumps(checksum_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def summarize_structural_scenario(scenario: Dict[str, Any]) -> Dict[str, Any]:
    norm = normalize_structural_scenario(scenario)
    return {
        "scenario_id": norm["scenario_id"],
        "scenario_type": norm["scenario_type"],
        "scenario_checksum": norm["scenario_checksum"],
        "target_node_count": len(norm["target_nodes"]),
        "target_corridor_count": len(norm["target_corridors"]),
        "perturbation_strength": norm["perturbation_strength"],
    }
