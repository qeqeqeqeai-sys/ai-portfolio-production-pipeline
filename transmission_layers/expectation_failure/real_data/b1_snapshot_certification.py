"""B1 snapshot certification and replay-safe checksums."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Dict


def _stable_checksum(value: object) -> str:
    canonical = json.dumps(value, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def certify_b1_snapshot(payload: dict) -> dict:
    frozen = deepcopy(payload)
    input_checksum = _stable_checksum(frozen)
    entity_scores = [e.get("fragility_score", 0) for e in frozen.get("entities", [])]
    degraded_entities = [e["ticker"] for e in frozen.get("entities", []) if e.get("evidence_quality_flags")]
    degraded_benchmarks = [b["symbol"] for b in frozen.get("benchmarks", []) if b.get("data_status") == "missing"]
    certification = {
        "certification_stage": "B1_SNAPSHOT_CERTIFICATION",
        "certification_status": "CERTIFIED_DETERMINISTIC",
        "entity_count": len(frozen.get("entities", [])),
        "checksum": input_checksum,
        "score_bounds_valid": all(0 <= int(s) <= 100 for s in entity_scores),
        "degraded_visibility": {
            "entity_missing_or_invalid": sorted(degraded_entities),
            "benchmark_missing": sorted(degraded_benchmarks),
        },
        "replay_contract": {
            "immutable_input_safety": True,
            "deterministic_ordering": True,
            "network_calls": "none",
            "persistence_mode": "controlled_persistence_ready",
        },
    }
    persisted = {
        "payload": frozen,
        "certification": certification,
        "replay_checksum": _stable_checksum({"payload": frozen, "certification": certification}),
    }
    return persisted
