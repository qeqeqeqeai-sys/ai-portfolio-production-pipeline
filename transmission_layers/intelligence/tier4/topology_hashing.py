"""Tier 4B deterministic topology hashing."""
from __future__ import annotations

import hashlib
import json
from typing import Any, Dict

from .structural_simulation import clamp_normalized_score


def _normalize(value: Any) -> Any:
    if isinstance(value, float):
        return clamp_normalized_score(value) if 0.0 <= value <= 1.0 else round(float(value), 6)
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_normalize(v) for v in sorted(list(value), key=lambda x: json.dumps(_normalize(x), sort_keys=True, separators=(",", ":")))]
    return value


def generate_topology_hash(snapshot_payload: Dict[str, Any]) -> str:
    payload = {
        "simulation_health_state": str(snapshot_payload.get("simulation_health_state", "mixed")),
        "node_metrics": _normalize(snapshot_payload.get("node_metrics", {})),
        "corridor_metrics": _normalize(snapshot_payload.get("corridor_metrics", {})),
        "propagation_summary": _normalize(snapshot_payload.get("propagation_summary", {})),
        "health_classifications": _normalize(snapshot_payload.get("health_classifications", {})),
        "topology_metadata": _normalize(snapshot_payload.get("topology_metadata", {})),
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()
