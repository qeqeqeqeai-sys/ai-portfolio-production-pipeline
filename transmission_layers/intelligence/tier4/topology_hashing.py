"""Tier 4B deterministic topology hashing."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .structural_simulation import clamp_normalized_score


def normalize_deterministic(value: Any) -> Any:
    if isinstance(value, bool):
        return value
    if isinstance(value, float):
        return clamp_normalized_score(value) if 0.0 <= value <= 1.0 else round(float(value), 6)
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return {str(k): normalize_deterministic(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        normalized = [normalize_deterministic(v) for v in list(value)]
        return sorted(normalized, key=lambda x: json.dumps(x, sort_keys=True, separators=(",", ":"), ensure_ascii=True))
    return value


def canonical_json_bytes(value: Any) -> bytes:
    normalized = normalize_deterministic(value)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def generate_topology_hash(snapshot_payload: Dict[str, Any]) -> str:
    payload = {
        "simulation_health_state": str(snapshot_payload.get("simulation_health_state", "mixed")),
        "node_metrics": normalize_deterministic(snapshot_payload.get("node_metrics", snapshot_payload.get("node_structural_metrics", {}))),
        "corridor_metrics": normalize_deterministic(snapshot_payload.get("corridor_metrics", snapshot_payload.get("corridor_structural_metrics", {}))),
        "propagation_summary": normalize_deterministic(snapshot_payload.get("propagation_summary", snapshot_payload.get("propagation_summaries", {}))),
        "health_classifications": normalize_deterministic(snapshot_payload.get("health_classifications", {})),
        "topology_metadata": normalize_deterministic(snapshot_payload.get("topology_metadata", {})),
    }
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()
