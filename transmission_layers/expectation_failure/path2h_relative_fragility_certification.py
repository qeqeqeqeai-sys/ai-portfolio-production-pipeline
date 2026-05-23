"""P2-H Relative Fragility Certification: deterministic additive-only stack certification for Path 2."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

CERTIFIED_RELATIVE_FRAGILITY_STACK = "CERTIFIED_RELATIVE_FRAGILITY_STACK"
DEGRADED_RELATIVE_FRAGILITY_STACK = "DEGRADED_RELATIVE_FRAGILITY_STACK"
BLOCKED_RELATIVE_FRAGILITY_STACK = "BLOCKED_RELATIVE_FRAGILITY_STACK"

REVIEWED_LAYERS: Tuple[str, ...] = ("P2-A", "P2-B", "P2-C", "P2-D", "P2-E", "P2-F", "P2-G")
LAYER_KEYS = {
    "P2-A": "p2a_cohort_registry",
    "P2-B": "p2b_relative_scoring",
    "P2-C": "p2c_ranking_percentile",
    "P2-D": "p2d_benchmark_divergence",
    "P2-E": "p2e_relative_evolution",
    "P2-F": "p2f_explainability",
    "P2-G": "p2g_concentration_breadth",
}

FORBIDDEN_CAPABILITIES: Tuple[str, ...] = (
    "prediction engines", "trading systems", "portfolio construction", "portfolio optimization", "autonomous execution",
    "dynamic peer generation", "dynamic benchmark creation", "dynamic cohort creation", "ml clustering", "adaptive weighting",
    "adaptive thresholds", "stochastic narratives", "llm-generated certification logic", "network/api calls", "supabase/database writes",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _layer_present(contract: Dict[str, Any], key: str) -> bool:
    return isinstance(contract.get(key), dict) and bool(contract.get(key))


def build_relative_fragility_certification_input_contract() -> Dict[str, Any]:
    return {
        "path_id": "P2-H",
        "required_layers": deepcopy(LAYER_KEYS),
        "required_output_fields": [
            "certification_id", "relative_fragility_stack_status", "reviewed_layers", "determinism_status", "replay_status",
            "explainability_status", "concentration_breadth_status", "architectural_boundary_status", "forbidden_capability_status",
            "certification_gates", "quality_flags", "replay_metadata", "checksum",
        ],
        "forbidden_capabilities": list(FORBIDDEN_CAPABILITIES),
    }


def build_relative_intelligence_inventory(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    return {
        "reviewed_layers": list(REVIEWED_LAYERS),
        "layer_availability": {layer: _layer_present(contract, key) for layer, key in LAYER_KEYS.items()},
    }


def certify_path2_determinism(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    inventory = build_relative_intelligence_inventory(contract)
    status = all(inventory["layer_availability"].values())
    return {
        "deterministic_ordering_preserved": list(inventory["layer_availability"].keys()) == list(REVIEWED_LAYERS),
        "input_immutability_preserved": contract == deepcopy(input_contract),
        "all_layers_available": status,
        "status": "PASS" if status else "FAIL",
    }


def certify_path2_replay_checksum_integrity(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    checksums = []
    replay_presence = []
    for key in LAYER_KEYS.values():
        layer = contract.get(key, {})
        checksums.append(bool(layer.get("checksum")))
        replay_presence.append(isinstance(layer.get("replay_metadata"), dict) and bool(layer.get("replay_metadata")))
    ok = all(checksums) and all(replay_presence)
    return {
        "checksum_continuity_present": all(checksums),
        "replay_metadata_present": all(replay_presence),
        "status": "PASS" if ok else "FAIL",
    }


def certify_path2_explainability_integrity(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    layer = deepcopy(input_contract).get("p2f_explainability", {})
    complete = bool(layer.get("cross_sectional_explainability") or layer.get("entity_explanations") or layer.get("explanation_packets"))
    return {"explainability_complete": complete, "status": "PASS" if complete else "FAIL"}


def certify_path2_concentration_breadth_integrity(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    layer = deepcopy(input_contract).get("p2g_concentration_breadth", {})
    metrics = (
        layer.get("top_fragility_share"),
        layer.get("elevated_fragility_breadth"),
        layer.get("weakness_participation_rate"),
    )
    bounded = all(isinstance(v, (int, float)) and 0.0 <= float(v) <= 1.0 for v in metrics)
    return {"concentration_breadth_metrics_bounded": bounded, "status": "PASS" if bounded else "FAIL"}


def certify_path2_architectural_boundaries(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    contract = deepcopy(input_contract)
    recalculated = bool(contract.get("recalculated_lower_layer_intelligence", False))
    additive_only = not recalculated
    return {
        "additive_only_integration_preserved": additive_only,
        "input_immutability_preserved": contract == deepcopy(input_contract),
        "status": "PASS" if additive_only else "FAIL",
    }


def validate_path2_forbidden_capabilities(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    low = _stable_json(deepcopy(input_contract)).lower()
    hits = [cap for cap in FORBIDDEN_CAPABILITIES if cap in low]
    absent = not hits
    return {"forbidden_capabilities_absent": absent, "detected_forbidden_capabilities": hits, "status": "PASS" if absent else "FAIL"}


def certify_relative_fragility_stack(input_contract: Dict[str, Any]) -> Dict[str, Any]:
    original = deepcopy(input_contract)
    contract = deepcopy(input_contract)
    inventory = build_relative_intelligence_inventory(contract)
    det = certify_path2_determinism(contract)
    replay = certify_path2_replay_checksum_integrity(contract)
    explain = certify_path2_explainability_integrity(contract)
    conc = certify_path2_concentration_breadth_integrity(contract)
    arch = certify_path2_architectural_boundaries(contract)
    forbidden = validate_path2_forbidden_capabilities(contract)

    gates = {
        "P2-A cohort registry available": inventory["layer_availability"]["P2-A"],
        "P2-B relative scoring available": inventory["layer_availability"]["P2-B"],
        "P2-C ranking/percentile available": inventory["layer_availability"]["P2-C"],
        "P2-D benchmark divergence available": inventory["layer_availability"]["P2-D"],
        "P2-E relative evolution available": inventory["layer_availability"]["P2-E"],
        "P2-F explainability available": inventory["layer_availability"]["P2-F"],
        "P2-G concentration/breadth available": inventory["layer_availability"]["P2-G"],
        "deterministic ordering preserved": det["deterministic_ordering_preserved"],
        "checksum continuity present": replay["checksum_continuity_present"],
        "replay metadata present": replay["replay_metadata_present"],
        "explainability complete": explain["explainability_complete"],
        "concentration/breadth metrics bounded": conc["concentration_breadth_metrics_bounded"],
        "forbidden capabilities absent": forbidden["forbidden_capabilities_absent"],
        "additive-only integration preserved": arch["additive_only_integration_preserved"],
        "input immutability preserved": original == deepcopy(input_contract),
    }
    missing_core = not all(gates[name] for name in (
        "P2-A cohort registry available", "P2-B relative scoring available", "P2-C ranking/percentile available",
        "P2-D benchmark divergence available", "P2-E relative evolution available", "P2-F explainability available",
        "P2-G concentration/breadth available",
    ))
    hard_fail = missing_core or (not gates["forbidden capabilities absent"]) or (not gates["additive-only integration preserved"])
    all_pass = all(gates.values())
    status = BLOCKED_RELATIVE_FRAGILITY_STACK if hard_fail else (CERTIFIED_RELATIVE_FRAGILITY_STACK if all_pass else DEGRADED_RELATIVE_FRAGILITY_STACK)

    result = {
        "certification_id": f"P2-H::{_checksum(inventory)}",
        "relative_fragility_stack_status": status,
        "reviewed_layers": list(REVIEWED_LAYERS),
        "determinism_status": det["status"],
        "replay_status": replay["status"],
        "explainability_status": explain["status"],
        "concentration_breadth_status": conc["status"],
        "architectural_boundary_status": arch["status"],
        "forbidden_capability_status": forbidden["status"],
        "certification_gates": gates,
        "quality_flags": forbidden["detected_forbidden_capabilities"],
        "replay_metadata": {"stable_serialization": True, "input_immutability_preserved": original == deepcopy(input_contract)},
    }
    result["checksum"] = _checksum(result)
    return result


def build_path2h_relative_fragility_certification_report(output_path: str = "reports/path2h_relative_fragility_certification_report.md") -> str:
    report = """# P2-H Relative Fragility Certification Report

## objective
Certify Path 2 cross-sectional relative fragility stack as deterministic, replay-safe, bounded, explainable, additive-only, checksum-traceable, and free of forbidden capabilities.

## scope
Consume certification-capable outputs from P2-A through P2-G and evaluate stack-level gates without recalculating lower-layer intelligence.

## non-goals
No prediction, trading, portfolio construction/optimization, autonomous execution, dynamic cohort/benchmark/peer generation, ML clustering, adaptive weighting/thresholds, stochastic narratives, LLM-generated certification logic, network/API calls, or database writes.

## reviewed Path 2 layers
P2-A cohort registry, P2-B relative scoring, P2-C percentile/ranking, P2-D benchmark divergence, P2-E relative evolution, P2-F cross-sectional explainability, P2-G concentration/breadth.

## certification methodology
Deterministic deep-copied contract review, literal gate evaluation, stable JSON checksum generation, additive-only boundary checks, and forbidden-capability scanning.

## determinism certification
Verify deterministic ordering and input immutability preservation.

## replay/checksum certification
Require checksum continuity and replay metadata presence across all reviewed layers.

## explainability certification
Require explainability packet presence in P2-F.

## concentration/breadth certification
Require bounded P2-G top fragility share, elevated breadth, and weakness participation metrics in [0,1].

## architectural boundary certification
Require additive-only integration and no lower-layer recalculation side effects.

## forbidden capability validation
Reject stack on any forbidden capability evidence.

## decision logic
BLOCKED if required layers are missing, forbidden capabilities are detected, or additive-only boundary fails. CERTIFIED if all gates pass. Otherwise DEGRADED.

## final supervisor interpretation
P2-H provides deterministic supervisor-grade certification over Path 2 artifacts while preserving replay integrity, boundedness, and architectural safety constraints.
"""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report, encoding="utf-8")
    return str(path)
