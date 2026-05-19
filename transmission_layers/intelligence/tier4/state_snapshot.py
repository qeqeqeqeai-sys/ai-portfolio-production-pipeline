"""Tier 4B deterministic structural state snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Mapping
import hashlib
import json

from .structural_simulation import clamp_normalized_score
from .topology_hashing import canonical_json_bytes, generate_topology_hash, normalize_deterministic


def _freeze_mapping(data: Mapping[str, Any]) -> Dict[str, Any]:
    return json.loads(canonical_json_bytes(data).decode("utf-8"))


@dataclass(frozen=True)
class StructuralSnapshot:
    run_date_sgt: str
    simulation_run_id: str
    simulation_health_state: str
    propagated_stress: float
    overload: float
    resilience: float
    node_structural_metrics: Dict[str, Dict[str, float]]
    corridor_structural_metrics: Dict[str, Dict[str, Any]]
    propagation_summaries: Dict[str, float]
    invariant_summaries: Dict[str, Any]
    explainability_summaries: Dict[str, Any]
    topology_metadata: Dict[str, Any]
    replay_checksum: str
    topology_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return _freeze_mapping(self.__dict__)


def build_structural_snapshot(run_date_sgt: str, simulation_result: Dict[str, Any]) -> StructuralSnapshot:
    stressed_nodes = sorted({str(v) for v in simulation_result.get("stressed_nodes", [])})
    overloaded_nodes = sorted({str(v) for v in simulation_result.get("overloaded_nodes", [])})

    nodes = sorted(set(stressed_nodes + overloaded_nodes))
    node_metrics = {
        node_id: {
            "is_stressed": 1.0 if node_id in stressed_nodes else 0.0,
            "is_overloaded": 1.0 if node_id in overloaded_nodes else 0.0,
        }
        for node_id in nodes
    }

    corridor_metrics: Dict[str, Dict[str, Any]] = {}
    for state_key in ["resilient_corridors", "degraded_corridors", "suppressed_corridors", "failed_corridors"]:
        state = state_key.replace("_corridors", "")
        for corridor_id in sorted({str(c) for c in simulation_result.get(state_key, [])}):
            corridor_metrics[corridor_id] = {"state": state}

    propagation = {
        "initial_stress": clamp_normalized_score(simulation_result.get("initial_stress_score", 0.0)),
        "propagated_stress": clamp_normalized_score(simulation_result.get("propagated_stress_score", 0.0)),
        "amplification": clamp_normalized_score(simulation_result.get("amplification_effect_score", 0.0)),
        "suppression": clamp_normalized_score(simulation_result.get("suppression_cascade_score", 0.0)),
        "overload": clamp_normalized_score(simulation_result.get("chokepoint_overload_score", 0.0)),
        "resilience": clamp_normalized_score(simulation_result.get("resilience_degradation_score", 0.0)),
    }

    health = str(simulation_result.get("simulation_health_state", "mixed"))
    classifications = {
        "simulation_health_state": [health],
        "structural_failure_warning": ["true" if simulation_result.get("structural_failure_warning", False) else "false"],
    }
    topology_metadata = {"node_count": len(node_metrics), "corridor_count": len(corridor_metrics)}
    topology_payload = {
        "simulation_health_state": health,
        "node_metrics": node_metrics,
        "corridor_metrics": corridor_metrics,
        "propagation_summary": propagation,
        "health_classifications": classifications,
        "topology_metadata": topology_metadata,
    }
    topology_hash = generate_topology_hash(topology_payload)
    replay_checksum = hashlib.sha256(canonical_json_bytes(topology_payload)).hexdigest()

    return StructuralSnapshot(
        run_date_sgt=str(run_date_sgt),
        simulation_run_id=str(simulation_result.get("simulation_run_id", "tier4b_deterministic_run")),
        simulation_health_state=health,
        propagated_stress=propagation["propagated_stress"],
        overload=propagation["overload"],
        resilience=propagation["resilience"],
        node_structural_metrics=node_metrics,
        corridor_structural_metrics={k: corridor_metrics[k] for k in sorted(corridor_metrics)},
        propagation_summaries=propagation,
        invariant_summaries=normalize_deterministic(simulation_result.get("invariant_validation", {"all_invariants_valid": True, "failed_invariants": []})),
        explainability_summaries=normalize_deterministic(simulation_result.get("explainability_payload", {})),
        topology_metadata=topology_metadata,
        replay_checksum=replay_checksum,
        topology_hash=topology_hash,
    )
