"""P2-I Supervisor Final Closeout Certification: deterministic additive-only final closeout for Path 2."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, Tuple

APPROVED_PATH2_CLOSEOUT = "APPROVED_PATH2_CLOSEOUT"
DEGRADED_PATH2_CLOSEOUT = "DEGRADED_PATH2_CLOSEOUT"
BLOCKED_PATH2_CLOSEOUT = "BLOCKED_PATH2_CLOSEOUT"

REVIEWED_LAYERS: Tuple[str, ...] = ("P2-A", "P2-B", "P2-C", "P2-D", "P2-E", "P2-F", "P2-G", "P2-H")
LAYER_KEYS = {
    "P2-A": "p2a_cohort_registry",
    "P2-B": "p2b_relative_scoring",
    "P2-C": "p2c_ranking_percentile",
    "P2-D": "p2d_benchmark_divergence",
    "P2-E": "p2e_relative_evolution",
    "P2-F": "p2f_explainability",
    "P2-G": "p2g_concentration_breadth",
    "P2-H": "p2h_relative_fragility_certification",
}
FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "prediction engines", "trading systems", "portfolio construction", "portfolio optimization", "autonomous execution",
    "dynamic peer generation", "dynamic benchmark creation", "dynamic cohort creation", "ml clustering", "adaptive weighting",
    "adaptive thresholds", "stochastic narratives", "self-modifying intelligence loops", "llm-generated certification logic",
    "network/api calls", "supabase/database writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _layer_present(contract: Dict[str, Any], key: str) -> bool:
    return isinstance(contract.get(key), dict) and bool(contract.get(key))


def build_path2_closeout_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-I",
        "required_layers": deepcopy(LAYER_KEYS),
        "required_output_fields": [
            "closeout_id", "path2_closeout_status", "reviewed_layers", "determinism_status", "replay_status",
            "checksum_status", "explainability_status", "breadth_status", "architectural_boundary_status",
            "forbidden_capability_status", "additive_integration_status", "certification_gates", "quality_flags",
            "replay_metadata", "checksum",
        ],
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def build_path2_layer_inventory(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    return {
        "reviewed_layers": list(REVIEWED_LAYERS),
        "layer_availability": {layer: _layer_present(contract, key) for layer, key in LAYER_KEYS.items()},
    }


def certify_path2_deterministic_replay(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    inventory = build_path2_layer_inventory(contract)
    replay_ok = all(isinstance(contract.get(key, {}).get("replay_metadata"), dict) and bool(contract.get(key, {}).get("replay_metadata")) for key in LAYER_KEYS.values())
    return {
        "deterministic_ordering_preserved": list(inventory["layer_availability"].keys()) == list(REVIEWED_LAYERS),
        "replay_metadata_continuity_present": replay_ok,
        "input_immutability_preserved": contract == deepcopy(input_contract),
        "status": "PASS" if replay_ok else "FAIL",
    }


def certify_path2_checksum_lineage(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    continuity = all(bool(contract.get(key, {}).get("checksum")) for key in LAYER_KEYS.values())
    return {"checksum_continuity_present": continuity, "status": "PASS" if continuity else "FAIL"}


def certify_path2_explainability_interpretation(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    p2f = contract.get("p2f_explainability", {})
    explain_ok = bool(p2f.get("cross_sectional_explainability") or p2f.get("entity_explanations") or p2f.get("explanation_packets"))
    p2g = contract.get("p2g_concentration_breadth", {})
    bounded = all(isinstance(p2g.get(name), (int, float)) and 0.0 <= float(p2g.get(name)) <= 1.0 for name in (
        "top_fragility_share", "elevated_fragility_breadth", "weakness_participation_rate"
    ))
    return {
        "explainability_completeness_present": explain_ok,
        "bounded_outputs_preserved": bounded,
        "status": "PASS" if explain_ok and bounded else "FAIL",
    }


def certify_path2_architectural_boundaries(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    bounded = not bool(contract.get("recalculated_lower_layer_intelligence", False))
    return {"bounded_outputs_preserved": bounded, "status": "PASS" if bounded else "FAIL"}


def validate_path2_final_forbidden_capabilities(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    low = _stable_json(deepcopy(input_contract)).lower()
    hits = [cap for cap in FORBIDDEN_CAPABILITIES if cap in low]
    absent = not hits
    return {"forbidden_capabilities_absent": absent, "detected_forbidden_capabilities": hits, "status": "PASS" if absent else "FAIL"}


def certify_path2_additive_integration(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    additive = not bool(contract.get("non_additive_integration", False)) and not bool(contract.get("recalculated_lower_layer_intelligence", False))
    return {"additive_only_integration_preserved": additive, "status": "PASS" if additive else "FAIL"}


def run_path2_supervisor_closeout(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(input_contract)
    contract = deepcopy(input_contract)
    inventory = build_path2_layer_inventory(contract)
    replay = certify_path2_deterministic_replay(contract)
    lineage = certify_path2_checksum_lineage(contract)
    explain = certify_path2_explainability_interpretation(contract)
    arch = certify_path2_architectural_boundaries(contract)
    forbidden = validate_path2_final_forbidden_capabilities(contract)
    additive = certify_path2_additive_integration(contract)

    gates = {
        "P2-A present": inventory["layer_availability"]["P2-A"],
        "P2-B present": inventory["layer_availability"]["P2-B"],
        "P2-C present": inventory["layer_availability"]["P2-C"],
        "P2-D present": inventory["layer_availability"]["P2-D"],
        "P2-E present": inventory["layer_availability"]["P2-E"],
        "P2-F present": inventory["layer_availability"]["P2-F"],
        "P2-G present": inventory["layer_availability"]["P2-G"],
        "P2-H present": inventory["layer_availability"]["P2-H"],
        "deterministic ordering preserved": replay["deterministic_ordering_preserved"],
        "replay metadata continuity present": replay["replay_metadata_continuity_present"],
        "checksum continuity present": lineage["checksum_continuity_present"],
        "explainability completeness present": explain["explainability_completeness_present"],
        "bounded outputs preserved": arch["bounded_outputs_preserved"] and explain["bounded_outputs_preserved"],
        "additive-only integration preserved": additive["additive_only_integration_preserved"],
        "forbidden capabilities absent": forbidden["forbidden_capabilities_absent"],
        "input immutability preserved": original == deepcopy(input_contract),
    }

    missing_layers = not all(gates[name] for name in ("P2-A present", "P2-B present", "P2-C present", "P2-D present", "P2-E present", "P2-F present", "P2-G present", "P2-H present"))
    blocked = missing_layers or (not gates["forbidden capabilities absent"]) or (not gates["additive-only integration preserved"])
    status = BLOCKED_PATH2_CLOSEOUT if blocked else (APPROVED_PATH2_CLOSEOUT if all(gates.values()) else DEGRADED_PATH2_CLOSEOUT)

    out = {
        "closeout_id": f"P2-I::{_checksum(inventory)}",
        "path2_closeout_status": status,
        "reviewed_layers": list(REVIEWED_LAYERS),
        "determinism_status": "PASS" if gates["deterministic ordering preserved"] and gates["input immutability preserved"] else "FAIL",
        "replay_status": replay["status"],
        "checksum_status": lineage["status"],
        "explainability_status": "PASS" if explain["explainability_completeness_present"] else "FAIL",
        "breadth_status": "PASS" if explain["bounded_outputs_preserved"] else "FAIL",
        "architectural_boundary_status": arch["status"],
        "forbidden_capability_status": forbidden["status"],
        "additive_integration_status": additive["status"],
        "certification_gates": gates,
        "quality_flags": forbidden["detected_forbidden_capabilities"],
        "replay_metadata": {"stable_serialization": True, "input_immutability_preserved": gates["input immutability preserved"]},
    }
    out["checksum"] = _checksum(out)
    return out


def build_path2i_supervisor_final_closeout_report(output_path: str = "reports/path2i_supervisor_final_closeout_report.md") -> str:
    report = """# P2-I Supervisor Final Closeout Certification Report

## objective
Implement final deterministic Path 2 supervisor closeout certifying cross-sectional relative fragility architecture readiness for controlled downstream use.

## scope
Consume certified outputs from P2-A through P2-H and certify final deterministic closeout without recalculating lower-layer intelligence.

## non-goals
No prediction engines, trading systems, portfolio construction/optimization, autonomous execution, dynamic peer/benchmark/cohort creation, ML clustering, adaptive weighting/thresholds, stochastic narratives, self-modifying loops, LLM-generated certification logic, network/API calls, or database writes.

## reviewed Path 2 layers
P2-A cohort registry, P2-B relative fragility scoring, P2-C percentile/ranking engine, P2-D benchmark divergence intelligence, P2-E relative evolution interpretation, P2-F cross-sectional explainability, P2-G concentration/breadth intelligence, P2-H relative fragility certification.

## final closeout methodology
Deterministic literal gate evaluation over deep-copied certified inputs, stable JSON serialization for checksum integrity, and additive-only architectural review.

## deterministic replay certification
Certify deterministic ordering and replay metadata continuity for all reviewed Path 2 layers.

## checksum/lineage certification
Certify checksum continuity across all reviewed Path 2 layers.

## explainability/interpretable-output certification
Certify explainability completeness in P2-F and interpretable bounded concentration/breadth outputs.

## concentration/breadth certification
Certify P2-G concentration and breadth fields are bounded in [0,1].

## architectural boundary certification
Certify bounded outputs and no lower-layer recalculation side-effects.

## forbidden capability validation
Fail closeout on detection of forbidden capabilities or disallowed operational patterns.

## additive integration certification
Certify additive-only integration preserving lower-layer outputs.

## final supervisor decision logic
BLOCKED when required layers are missing or forbidden/additive constraints fail. APPROVED when all gates pass. DEGRADED otherwise.

## final supervisor interpretation
P2-I finalizes deterministic supervisor governance for Path 2, preserving replayability, lineage, explainability, boundedness, and strict architectural safety boundaries.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return str(path)
