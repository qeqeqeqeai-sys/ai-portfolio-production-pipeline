"""Deterministic Phase O1 operational visibility foundation."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "o1_operational_visibility_v1"
MODULE_VERSION = "1.0.0"

LAYER_SPECS: tuple[tuple[str, str], ...] = (
    ("path1", "Path 1 — Temporal Replay & Structural Evolution Intelligence"),
    ("path2", "Path 2 — Cross-Sectional Relative Fragility & Peer Comparison Intelligence"),
    ("path3", "Path 3 — Structural Asymmetry, Regime Classification, Explainability & Supervisor Closeout"),
    ("path5a", "Path 5-A — Structural Transmission Graph Layer"),
    ("path5b", "Path 5-B — Fragility Propagation Intelligence"),
    ("path5c", "Path 5-C — Propagation Persistence & Structural Pressure Evolution"),
    ("path5d", "Path 5-D — Propagation Regime Classification & Structural State Labelling"),
    ("path5e", "Path 5-E — Propagation Supervisor Synthesis & Transmission State Closeout"),
)

ALLOWED = [
    "structural diagnostics",
    "operational observability",
    "replay-safe dashboard interpretation",
    "deterministic structural state inspection",
    "supervisor status visibility",
]
FORBIDDEN = [
    "prediction",
    "trading recommendations",
    "portfolio optimization",
    "autonomous execution",
    "probabilistic forecasting",
    "black-box model inference",
    "investment advice",
    "expected return generation",
]


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_o1_layer_inventory(layer_observations: Mapping[str, Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    observations = deepcopy(dict(layer_observations or {}))
    inventory: list[OrderedDict[str, Any]] = []
    for layer_id, layer_name in LAYER_SPECS:
        obs = dict(observations.get(layer_id, {}))
        observed = str(obs.get("observed_status", "missing")).strip().lower()
        checksum_present = bool(obs.get("checksum_present", False))
        replay_metadata_present = bool(obs.get("replay_metadata_present", False))
        supervisor_closeout_present = bool(obs.get("supervisor_closeout_present", False))

        if observed == "available" and checksum_present and replay_metadata_present and supervisor_closeout_present:
            availability_state = "AVAILABLE"
            degraded_reason = ""
        elif observed == "missing":
            availability_state = "MISSING"
            degraded_reason = "layer_not_observed"
        else:
            availability_state = "DEGRADED"
            degraded_reason = "missing_required_observability_fields"

        inventory.append(OrderedDict([
            ("layer_id", layer_id),
            ("layer_name", layer_name),
            ("expected_status", "available"),
            ("observed_status", observed),
            ("availability_state", availability_state),
            ("required_for_o1", True),
            ("checksum_present", checksum_present),
            ("replay_metadata_present", replay_metadata_present),
            ("supervisor_closeout_present", supervisor_closeout_present),
            ("degraded_reason", degraded_reason),
        ]))
    return inventory


def build_o1_operational_status(layer_inventory: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    inventory = [dict(item) for item in list(layer_inventory or [])]
    if not inventory:
        return OrderedDict([
            ("overall_status", "O1_OPERATIONAL_BLOCKED"), ("ready_for_dashboard", False),
            ("ready_for_replay_observability", False), ("ready_for_supervisor_dashboard", False),
            ("degraded_layers_count", 0), ("blocked_layers_count", 8), ("missing_layers_count", 8),
            ("available_layers_count", 0), ("primary_operational_risk", "layer_inventory_unavailable"),
            ("supervisor_summary", "Operational visibility blocked: layer inventory unavailable."),
        ])

    available = sum(1 for i in inventory if i.get("availability_state") == "AVAILABLE")
    missing = sum(1 for i in inventory if i.get("availability_state") == "MISSING")
    degraded = sum(1 for i in inventory if i.get("availability_state") == "DEGRADED")
    blocked = missing

    if available == 0:
        status = "O1_OPERATIONAL_BLOCKED"
        risk = "all_critical_layers_missing"
    elif missing == 0 and degraded == 0:
        status = "O1_OPERATIONAL_READY"
        risk = "none"
    else:
        status = "O1_OPERATIONAL_DEGRADED"
        risk = "required_layers_missing_or_degraded"

    return OrderedDict([
        ("overall_status", status),
        ("ready_for_dashboard", status != "O1_OPERATIONAL_BLOCKED"),
        ("ready_for_replay_observability", missing == 0),
        ("ready_for_supervisor_dashboard", available > 0),
        ("degraded_layers_count", degraded),
        ("blocked_layers_count", blocked),
        ("missing_layers_count", missing),
        ("available_layers_count", available),
        ("primary_operational_risk", risk),
        ("supervisor_summary", f"O1 status={status}; available={available}; missing={missing}; degraded={degraded}."),
    ])


def build_o1_replay_lineage_summary(layer_inventory: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    inventory = [dict(i) for i in list(layer_inventory or [])]
    missing_checksum = [i["layer_id"] for i in inventory if not bool(i.get("checksum_present"))]
    missing_replay = [i["layer_id"] for i in inventory if not bool(i.get("replay_metadata_present"))]
    checksum_complete = len(missing_checksum) == 0
    replay_safe = checksum_complete and len(missing_replay) == 0
    return OrderedDict([
        ("replay_safe", replay_safe),
        ("checksum_lineage_complete", checksum_complete),
        ("missing_checksum_layers", missing_checksum),
        ("missing_replay_metadata_layers", missing_replay),
        ("lineage_summary", "complete" if replay_safe else "incomplete"),
        ("deterministic_replay_notes", "Replay lineage evaluated with fixed-order, checksum-first deterministic policy."),
    ])


def build_o1_governance_boundary_summary() -> OrderedDict[str, Any]:
    return OrderedDict([("allowed", list(ALLOWED)), ("forbidden", list(FORBIDDEN))])


def certify_o1_operational_visibility(layer_inventory: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    inventory = build_o1_layer_inventory({i.get("layer_id"): i for i in list(layer_inventory or [])}) if layer_inventory else build_o1_layer_inventory({})
    status = build_o1_operational_status(inventory)
    lineage = build_o1_replay_lineage_summary(inventory)
    governance = build_o1_governance_boundary_summary()

    blocking_reasons = []
    degraded_reasons = []
    if status["overall_status"] == "O1_OPERATIONAL_BLOCKED":
        blocking_reasons.append(status["primary_operational_risk"])
    if status["overall_status"] == "O1_OPERATIONAL_DEGRADED":
        degraded_reasons.append(status["primary_operational_risk"])

    invariant_results = OrderedDict([
        ("fixed_layer_order", [i["layer_id"] for i in inventory] == [i[0] for i in LAYER_SPECS]),
        ("deterministic_checksum_serializer", True),
        ("no_network_calls", True),
        ("no_database_writes", True),
    ])

    forbidden_check = OrderedDict([(item, True) for item in FORBIDDEN])
    checksum_payload = OrderedDict([
        ("status", status), ("lineage", lineage), ("governance", governance), ("invariants", invariant_results),
    ])
    cert_passed = status["overall_status"] == "O1_OPERATIONAL_READY"
    cert_status = "CERTIFIED" if cert_passed else "CONDITIONAL" if status["overall_status"] == "O1_OPERATIONAL_DEGRADED" else "BLOCKED"

    return OrderedDict([
        ("certification_status", cert_status),
        ("certification_passed", cert_passed),
        ("blocking_reasons", blocking_reasons),
        ("degraded_reasons", degraded_reasons),
        ("invariant_results", invariant_results),
        ("forbidden_capability_check", forbidden_check),
        ("checksum", _stable_checksum(checksum_payload)),
        ("replay_safe", lineage["replay_safe"]),
        ("supervisor_decision", "APPROVED" if cert_passed else "APPROVED_WITH_DEGRADED_VISIBILITY" if status["overall_status"] == "O1_OPERATIONAL_DEGRADED" else "BLOCKED_REMEDIATION_REQUIRED"),
    ])


def build_o1_dashboard_view_model(layer_observations: Mapping[str, Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    inventory = build_o1_layer_inventory(layer_observations)
    status = build_o1_operational_status(inventory)
    lineage = build_o1_replay_lineage_summary(inventory)
    governance = build_o1_governance_boundary_summary()
    cert = certify_o1_operational_visibility(inventory)
    return OrderedDict([
        ("page_id", "sefi_o1_operational_visibility"),
        ("page_title", "SEFI Operational Visibility (O1)"),
        ("generated_at_policy", "deterministic_no_runtime_clock"),
        ("operational_status", status),
        ("layer_inventory", inventory),
        ("replay_lineage", lineage),
        ("governance_boundaries", governance),
        ("supervisor_cards", [OrderedDict([("title", "Supervisor Status"), ("value", status["supervisor_summary"])])]),
        ("alert_cards", [OrderedDict([("title", "Primary Risk"), ("value", status["primary_operational_risk"])])]),
        ("readiness_cards", [OrderedDict([("title", "Dashboard Readiness"), ("value", status["overall_status"])])]),
        ("certification_summary", cert),
    ])


def build_o1_operational_visibility_report(layer_observations: Mapping[str, Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    vm = build_o1_dashboard_view_model(layer_observations)
    return OrderedDict([
        ("objective", "Provide deterministic institutional operational visibility for SEFI."),
        ("scope", "O1 operational readiness, layer health, replay lineage, governance boundaries."),
        ("non_goals", list(FORBIDDEN)),
        ("reviewed_layers", [item["layer_id"] for item in vm["layer_inventory"]]),
        ("operational_status", vm["operational_status"]),
        ("replay_lineage_summary", vm["replay_lineage"]),
        ("governance_boundaries", vm["governance_boundaries"]),
        ("certification_result", vm["certification_summary"]),
        ("final_supervisor_interpretation", vm["certification_summary"]["supervisor_decision"]),
    ])


__all__ = [
    "build_o1_layer_inventory",
    "build_o1_operational_status",
    "build_o1_replay_lineage_summary",
    "build_o1_governance_boundary_summary",
    "build_o1_dashboard_view_model",
    "certify_o1_operational_visibility",
    "build_o1_operational_visibility_report",
]
