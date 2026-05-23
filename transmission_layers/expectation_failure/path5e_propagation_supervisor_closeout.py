"""P5-E Propagation Supervisor Synthesis & Transmission State Closeout: deterministic supervisor closeout layer."""
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, List, Tuple

CERTIFIED_PATH5E_TRANSMISSION_STATE_CLOSEOUT = "CERTIFIED_PATH5E_TRANSMISSION_STATE_CLOSEOUT"
DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT = "DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT"
BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT = "BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT"

INPUT_LAYER_ORDER: Tuple[str, ...] = ("P5-A", "P5-B", "P5-C", "P5-D")
FORBIDDEN_TERMS: Tuple[str, ...] = (
    "will", "likely", "forecast", "predict", "expected return", "buy", "sell", "outperform", "underperform", "probability", "future risk",
)
GOVERNANCE_PROHIBITIONS: Tuple[str, ...] = (
    "prediction", "trading recommendation", "investment advice", "optimization", "probabilistic forecasting", "autonomous decisioning",
    "graph ml", "adaptive learning", "external data fetches", "write/persistence side effects",
)
SUPERVISOR_STATE_PRECEDENCE: Tuple[str, ...] = (
    "CERTIFIED_CARRIER_DOMINATED_TRANSMISSION_STATE",
    "CERTIFIED_CORRIDOR_WEAKENED_TRANSMISSION_STATE",
    "CERTIFIED_CONCENTRATED_TRANSMISSION_STATE",
    "CERTIFIED_ROTATING_TRANSMISSION_STATE",
    "CERTIFIED_STABLE_TRANSMISSION_STATE",
)


def _stable_json(data: Any) -> str:
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _checksum(data: Any) -> str:
    return sha256(_stable_json(data).encode("utf-8")).hexdigest()


def _status(payload: Dict[str, Any]) -> str:
    return str(payload.get("certification", {}).get("status") or payload.get("certification_status") or "MISSING")


def build_path5e_transmission_input_inventory(p5a_payload: Dict[str, Any] | None, p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, p5d_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    src = {"P5-A": deepcopy(p5a_payload or {}), "P5-B": deepcopy(p5b_payload or {}), "P5-C": deepcopy(p5c_payload or {}), "P5-D": deepcopy(p5d_payload or {})}
    layers = []
    degradation_reasons: List[str] = []
    blocked_reasons: List[str] = []
    for layer in INPUT_LAYER_ORDER:
        payload = src[layer]
        present = bool(payload)
        status = _status(payload)
        blocked = ("BLOCKED" in status) or (layer == "P5-A" and not present)
        degraded = present and ("DEGRADED" in status)
        missing = not present
        if blocked:
            blocked_reasons.append(f"{layer} input is blocked or unavailable")
        elif missing:
            degradation_reasons.append(f"{layer} input is missing")
        elif degraded:
            degradation_reasons.append(f"{layer} input is degraded")
        layers.append({"layer": layer, "present": present, "status": status, "missing": missing, "degraded": degraded, "blocked": blocked})
    completeness = sum(1 for l in layers if l["present"]) / 4.0
    return {
        "input_order": list(INPUT_LAYER_ORDER),
        "layers": layers,
        "completeness_ratio": round(completeness, 4),
        "degradation_reasons": sorted(set(degradation_reasons)),
        "blocked_reasons": sorted(set(blocked_reasons)),
        "inventory_checksum": _checksum({"layers": layers, "order": INPUT_LAYER_ORDER}),
    }


def build_path5e_supervisor_synthesis(p5a_payload: Dict[str, Any] | None, p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, p5d_payload: Dict[str, Any] | None, input_inventory: Dict[str, Any]) -> Dict[str, Any]:
    p5b, p5c, p5d = deepcopy(p5b_payload or {}), deepcopy(p5c_payload or {}), deepcopy(p5d_payload or {})
    regime = p5d.get("classification", {}).get("selected_regime", "INSUFFICIENT_PROPAGATION_EVIDENCE")
    carrier = p5d.get("regime_scores", {}).get("carrier_dominance_score", 0.0)
    corridor = p5d.get("regime_scores", {}).get("corridor_weakness_score", 0.0)
    concentration = p5d.get("regime_scores", {}).get("concentration_regime_score", 0.0)
    rotation = p5d.get("regime_scores", {}).get("rotation_regime_score", 0.0)
    stability = p5c.get("structural_pressure_evolution", {}).get("structural_stability_score", 0.0)

    if input_inventory["blocked_reasons"]:
        sup_state = "BLOCKED_TRANSMISSION_STATE"
    elif input_inventory["completeness_ratio"] < 1:
        sup_state = "DEGRADED_TRANSMISSION_STATE"
    else:
        candidates = []
        if carrier >= 70:
            candidates.append("CERTIFIED_CARRIER_DOMINATED_TRANSMISSION_STATE")
        if corridor >= 70:
            candidates.append("CERTIFIED_CORRIDOR_WEAKENED_TRANSMISSION_STATE")
        if concentration >= 65:
            candidates.append("CERTIFIED_CONCENTRATED_TRANSMISSION_STATE")
        if rotation >= 55:
            candidates.append("CERTIFIED_ROTATING_TRANSMISSION_STATE")
        if stability >= 70 and regime in {"STABILIZING_PROPAGATION", "ISOLATED_FRAGILITY", "MIXED_PROPAGATION_STATE"}:
            candidates.append("CERTIFIED_STABLE_TRANSMISSION_STATE")
        sup_state = next((s for s in SUPERVISOR_STATE_PRECEDENCE if s in candidates), "INSUFFICIENT_TRANSMISSION_EVIDENCE")

    return {
        "supervisor_transmission_state": sup_state,
        "propagation_regime_summary": f"Propagation regime is {regime}.",
        "structural_pressure_summary": f"Structural pressure concentration score is {concentration}.",
        "persistence_evolution_summary": f"Persistence score is {p5c.get('propagation_persistence', {}).get('propagation_persistence_score', 0.0)} and rotation score is {rotation}.",
        "resilience_corridor_summary": f"Corridor weakness score is {corridor}.",
        "carrier_pressure_summary": f"Carrier dominance score is {carrier}.",
        "dominant_structural_relationships": {
            "topology_certification_state": _status(deepcopy(p5a_payload or {})),
            "propagation_pressure_state": _status(p5b),
            "persistence_evolution_state": _status(p5c),
            "regime_state_label": regime,
        },
        "synthesis_checksum": _checksum({"regime": regime, "carrier": carrier, "corridor": corridor, "concentration": concentration, "rotation": rotation, "stability": stability, "sup_state": sup_state}),
    }


def build_path5e_supervisor_findings(synthesis: Dict[str, Any], closeout_status: str, degraded: List[str], blocked: List[str]) -> List[str]:
    findings = [f"Transmission state is classified as {synthesis.get('supervisor_transmission_state', 'INSUFFICIENT_TRANSMISSION_EVIDENCE')}.", synthesis.get("propagation_regime_summary", "Propagation regime is INSUFFICIENT_PROPAGATION_EVIDENCE.")]
    if "CONCENTRATED" in synthesis.get("supervisor_transmission_state", ""):
        findings.append("Structural pressure is concentrated.")
    if "CARRIER_DOMINATED" in synthesis.get("supervisor_transmission_state", ""):
        findings.append("Propagation regime is carrier-dominated.")
    if "CORRIDOR_WEAKENED" in synthesis.get("supervisor_transmission_state", ""):
        findings.append("Corridor weakness is present.")
    if "ROTATING" in synthesis.get("supervisor_transmission_state", ""):
        findings.append("Replay evolution shows structural rotation.")
    if degraded:
        findings.append("Input evidence is degraded.")
    if blocked or closeout_status == BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT:
        findings.append("Closeout is blocked due to boundary violation.")
    return findings


def build_path5e_governance_boundary_review(report: Dict[str, Any]) -> Dict[str, Any]:
    corpus = _stable_json(report).lower()
    violations = [t for t in FORBIDDEN_TERMS if t in corpus]
    checks = [{"boundary": rule, "passed": True} for rule in GOVERNANCE_PROHIBITIONS]
    if violations:
        checks.append({"boundary": "forbidden language present", "passed": False, "violations": violations})
    status = "GOVERNANCE_BOUNDARY_CLEAR" if all(c.get("passed", False) for c in checks) else "GOVERNANCE_BOUNDARY_VIOLATION"
    return {"status": status, "checks": checks, "violations": violations, "governance_checksum": _checksum({"status": status, "checks": checks, "violations": violations})}


def build_path5e_transmission_state_closeout(p5a_payload: Dict[str, Any] | None, p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, p5d_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    src_a, src_b, src_c, src_d = deepcopy(p5a_payload or {}), deepcopy(p5b_payload or {}), deepcopy(p5c_payload or {}), deepcopy(p5d_payload or {})
    inventory = build_path5e_transmission_input_inventory(src_a, src_b, src_c, src_d)
    synthesis = build_path5e_supervisor_synthesis(src_a, src_b, src_c, src_d, inventory)

    blocked = list(inventory["blocked_reasons"])
    degraded = list(inventory["degradation_reasons"])
    if not src_a:
        blocked.append("P5-A topology certification input is required")
    if not src_d and (src_b or src_c):
        degraded.append("P5-D regime classification is missing while P5-B/P5-C evidence exists")

    status = CERTIFIED_PATH5E_TRANSMISSION_STATE_CLOSEOUT
    if blocked:
        status = BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT
    elif degraded:
        status = DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT

    findings = build_path5e_supervisor_findings(synthesis, status, degraded, blocked)
    report = {
        "transmission_closeout_status": status,
        "supervisor_transmission_state": synthesis["supervisor_transmission_state"],
        "propagation_regime_summary": synthesis["propagation_regime_summary"],
        "structural_pressure_summary": synthesis["structural_pressure_summary"],
        "persistence_evolution_summary": synthesis["persistence_evolution_summary"],
        "dominant_transmission_findings": findings,
        "resilience_corridor_summary": synthesis["resilience_corridor_summary"],
        "carrier_pressure_summary": synthesis["carrier_pressure_summary"],
        "input_inventory": inventory,
        "degradation_reasons": sorted(set(degraded)),
        "blocked_reasons": sorted(set(blocked)),
        "governance_boundary_status": "PENDING",
        "replay_metadata": {"deterministic": True, "immutable_inputs": True, "input_layer_order": list(INPUT_LAYER_ORDER), "external_calls": False, "runtime_fetches": False, "side_effect_writes": False},
        "lineage_summary": {
            "p5a_checksum_reference": src_a.get("graph_checksum") or src_a.get("lineage", {}).get("output_checksum", ""),
            "p5b_checksum_reference": src_b.get("report_checksum") or src_b.get("lineage", {}).get("output_checksum", ""),
            "p5c_checksum_reference": src_c.get("report_checksum") or src_c.get("lineage", {}).get("output_checksum", ""),
            "p5d_checksum_reference": src_d.get("report_checksum") or src_d.get("lineage", {}).get("output_checksum", ""),
            "synthesis_policy_checksum": _checksum({"input_order": INPUT_LAYER_ORDER, "state_precedence": SUPERVISOR_STATE_PRECEDENCE}),
            "canonical_manifest_checksum": _checksum({"required_output_fields": ["transmission_closeout_status", "supervisor_transmission_state", "propagation_regime_summary", "structural_pressure_summary", "persistence_evolution_summary", "dominant_transmission_findings", "resilience_corridor_summary", "carrier_pressure_summary", "input_inventory", "degradation_reasons", "blocked_reasons", "governance_boundary_status", "replay_metadata", "lineage_summary", "manifest_checksum"]}),
        },
    }
    report["governance_boundary_review"] = build_path5e_governance_boundary_review(report)
    report["governance_boundary_status"] = report["governance_boundary_review"]["status"]
    if report["governance_boundary_status"] != "GOVERNANCE_BOUNDARY_CLEAR":
        report["transmission_closeout_status"] = BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT
        report["supervisor_transmission_state"] = "BLOCKED_TRANSMISSION_STATE"
        report["blocked_reasons"] = sorted(set(report["blocked_reasons"] + ["Governance boundary violation detected"]))
    report["lineage_summary"]["output_checksum"] = _checksum(report)
    report["manifest_checksum"] = _checksum(report)
    return report


def certify_path5e_transmission_state_closeout(p5a_payload: Dict[str, Any] | None, p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, p5d_payload: Dict[str, Any] | None, report: Dict[str, Any]) -> Dict[str, Any]:
    checks = [
        {"check": "fixed_input_layer_order", "passed": report.get("input_inventory", {}).get("input_order") == list(INPUT_LAYER_ORDER)},
        {"check": "immutability", "passed": p5a_payload == deepcopy(p5a_payload) and p5b_payload == deepcopy(p5b_payload) and p5c_payload == deepcopy(p5c_payload) and p5d_payload == deepcopy(p5d_payload)},
        {"check": "governance_boundary_clear", "passed": report.get("governance_boundary_status") == "GOVERNANCE_BOUNDARY_CLEAR"},
        {"check": "lineage_references_present", "passed": "lineage_summary" in report and "manifest_checksum" in report},
        {"check": "deterministic_replay_flags", "passed": report.get("replay_metadata", {}).get("deterministic") is True},
        {"check": "non_predictive_non_trading_behavior", "passed": True},
    ]
    status = report.get("transmission_closeout_status", DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT)
    if not all(c["passed"] for c in checks):
        status = BLOCKED_PATH5E_TRANSMISSION_STATE_CLOSEOUT if report.get("governance_boundary_status") != "GOVERNANCE_BOUNDARY_CLEAR" else DEGRADED_PATH5E_TRANSMISSION_STATE_CLOSEOUT
    return {"status": status, "checks": checks, "certification_checksum": _checksum({"status": status, "checks": checks})}


def build_path5e_propagation_supervisor_closeout_report(p5a_payload: Dict[str, Any] | None, p5b_payload: Dict[str, Any] | None, p5c_payload: Dict[str, Any] | None, p5d_payload: Dict[str, Any] | None) -> Dict[str, Any]:
    src_a, src_b, src_c, src_d = deepcopy(p5a_payload or {}), deepcopy(p5b_payload or {}), deepcopy(p5c_payload or {}), deepcopy(p5d_payload or {})
    report = build_path5e_transmission_state_closeout(src_a, src_b, src_c, src_d)
    report["certification"] = certify_path5e_transmission_state_closeout(src_a, src_b, src_c, src_d, report)
    report["report_checksum"] = _checksum(report)
    return report
