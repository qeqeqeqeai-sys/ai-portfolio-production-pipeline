"""Tier 4B deterministic structural state snapshots."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import hashlib
import json

from .structural_simulation import clamp_normalized_score



def _stable_json(payload: Dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))



def _stable_list(values: List[str]) -> List[str]:
    return sorted({str(v) for v in values if str(v).strip()})


@dataclass(frozen=True)
class StructuralSnapshot:
    run_date: str
    simulation_run_id: str
    simulation_health_state: str
    node_metrics: Dict[str, Dict[str, float]]
    corridor_metrics: Dict[str, Dict[str, Any]]
    propagation_summary: Dict[str, float]
    health_classifications: Dict[str, List[str]]
    explainability_summary: Dict[str, List[str]]
    topology_metadata: Dict[str, Any]
    invariant_validation: Dict[str, Any]
    topology_hash: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "run_date": self.run_date,
            "simulation_run_id": self.simulation_run_id,
            "simulation_health_state": self.simulation_health_state,
            "node_metrics": self.node_metrics,
            "corridor_metrics": self.corridor_metrics,
            "propagation_summary": self.propagation_summary,
            "health_classifications": self.health_classifications,
            "explainability_summary": self.explainability_summary,
            "topology_metadata": self.topology_metadata,
            "invariant_validation": self.invariant_validation,
            "topology_hash": self.topology_hash,
        }



def generate_topology_hash(snapshot_payload: Dict[str, Any]) -> str:
    normalized = {
        "nodes": sorted(snapshot_payload.get("node_metrics", {}).items(), key=lambda x: x[0]),
        "corridors": sorted(snapshot_payload.get("corridor_metrics", {}).items(), key=lambda x: x[0]),
        "health": snapshot_payload.get("simulation_health_state", ""),
        "propagation_summary": snapshot_payload.get("propagation_summary", {}),
        "health_classifications": snapshot_payload.get("health_classifications", {}),
    }
    return hashlib.sha256(_stable_json(normalized).encode("utf-8")).hexdigest()



def build_structural_snapshot(run_date: str, simulation_result: Dict[str, Any]) -> StructuralSnapshot:
    stressed_nodes = _stable_list(simulation_result.get("stressed_nodes", []))
    overloaded_nodes = _stable_list(simulation_result.get("overloaded_nodes", []))

    node_metrics = {
        node_id: {
            "is_stressed": 1.0 if node_id in stressed_nodes else 0.0,
            "is_overloaded": 1.0 if node_id in overloaded_nodes else 0.0,
        }
        for node_id in sorted(set(stressed_nodes + overloaded_nodes))
    }
    corridor_metrics = {}
    for state_key in ["resilient_corridors", "degraded_corridors", "suppressed_corridors", "failed_corridors"]:
        for corridor in _stable_list(simulation_result.get(state_key, [])):
            corridor_metrics[corridor] = {"state": state_key.replace("_corridors", "")}

    propagation_summary = {
        "initial_stress_score": clamp_normalized_score(simulation_result.get("initial_stress_score", 0.0)),
        "propagated_stress_score": clamp_normalized_score(simulation_result.get("propagated_stress_score", 0.0)),
        "amplification_effect_score": clamp_normalized_score(simulation_result.get("amplification_effect_score", 0.0)),
        "suppression_cascade_score": clamp_normalized_score(simulation_result.get("suppression_cascade_score", 0.0)),
        "chokepoint_overload_score": clamp_normalized_score(simulation_result.get("chokepoint_overload_score", 0.0)),
        "resilience_degradation_score": clamp_normalized_score(simulation_result.get("resilience_degradation_score", 0.0)),
    }
    health_classifications = {
        "simulation_health_state": [str(simulation_result.get("simulation_health_state", "mixed"))],
        "structural_failure_warning": ["true" if simulation_result.get("structural_failure_warning", False) else "false"],
    }
    explainability_summary = {
        k: _stable_list(v)
        for k, v in simulation_result.get("explainability_payload", {}).items()
        if isinstance(v, list)
    }
    topology_metadata = {
        "node_count": len(node_metrics),
        "corridor_count": len(corridor_metrics),
    }
    invariant_validation = simulation_result.get("invariant_validation", {"all_invariants_valid": True, "failed_invariants": []})

    payload = {
        "node_metrics": node_metrics,
        "corridor_metrics": corridor_metrics,
        "simulation_health_state": simulation_result.get("simulation_health_state", "mixed"),
        "propagation_summary": propagation_summary,
        "health_classifications": health_classifications,
    }
    topology_hash = generate_topology_hash(payload)
    return StructuralSnapshot(
        run_date=str(run_date),
        simulation_run_id=str(simulation_result.get("simulation_run_id", "tier4b_deterministic_run")),
        simulation_health_state=str(simulation_result.get("simulation_health_state", "mixed")),
        node_metrics=node_metrics,
        corridor_metrics={k: corridor_metrics[k] for k in sorted(corridor_metrics)},
        propagation_summary=propagation_summary,
        health_classifications=health_classifications,
        explainability_summary=explainability_summary,
        topology_metadata=topology_metadata,
        invariant_validation=invariant_validation,
        topology_hash=topology_hash,
    )
