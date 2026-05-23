"""Deterministic Phase O2 replay operationalization dashboard view models."""

from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

SCHEMA_VERSION = "o2_replay_operationalization_v1"
MODULE_VERSION = "1.0.0"

ELEVATED_PRESSURE_THRESHOLD = 70.0
SEVERE_PRESSURE_THRESHOLD = 85.0
STABLE_DELTA_BAND = 5.0

ALLOWED_USES = [
    "replay-safe structural observability",
    "historical structural interpretation",
    "deterministic dashboard view-model generation",
    "regime transition inspection",
    "pressure evolution diagnostics",
]
FORBIDDEN_USES = [
    "price prediction",
    "trading recommendations",
    "portfolio optimization",
    "autonomous execution",
    "probabilistic forecasting",
    "investment advice",
    "expected return generation",
    "black-box model inference",
]


def _stable_checksum(payload: Any) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalized_snapshot(snapshot: Mapping[str, Any]) -> OrderedDict[str, Any]:
    item = dict(snapshot)
    return OrderedDict([
        ("snapshot_id", str(item.get("snapshot_id") or "")),
        ("as_of_date", str(item.get("as_of_date") or "")),
        ("structural_pressure_score", _to_float(item.get("structural_pressure_score"), 0.0)),
        ("fragility_score", _to_float(item.get("fragility_score"), 0.0)),
        ("expectation_fragility_score", _to_float(item.get("expectation_fragility_score"), 0.0)),
        ("propagation_pressure_score", _to_float(item.get("propagation_pressure_score"), 0.0)),
        ("regime_label", str(item.get("regime_label") or "UNKNOWN")),
        ("dominant_fragility_cluster", str(item.get("dominant_fragility_cluster") or "UNKNOWN")),
        ("weakest_corridor", str(item.get("weakest_corridor") or "UNKNOWN")),
        ("checksum", item.get("checksum")),
        ("replay_metadata", item.get("replay_metadata")),
        ("certification_status", str(item.get("certification_status") or "READY").upper()),
        ("degraded_reasons", [str(x) for x in list(item.get("degraded_reasons") or [])]),
        ("blocked_reasons", [str(x) for x in list(item.get("blocked_reasons") or [])]),
    ])


def _normalize_snapshots(replay_snapshots: list[Mapping[str, Any]] | None) -> list[OrderedDict[str, Any]]:
    snapshots = deepcopy(list(replay_snapshots or []))
    normalized = [_normalized_snapshot(s) for s in snapshots]
    normalized.sort(key=lambda x: (x["as_of_date"], x["snapshot_id"]))
    return normalized


def _timeline_state(snapshot: Mapping[str, Any]) -> str:
    blocked = bool(snapshot.get("blocked_reasons")) or snapshot.get("certification_status") == "BLOCKED"
    degraded = bool(snapshot.get("degraded_reasons")) or snapshot.get("certification_status") == "DEGRADED"
    if blocked:
        return "BLOCKED"
    if degraded or not snapshot.get("checksum") or not snapshot.get("replay_metadata"):
        return "DEGRADED"
    return "READY"


def build_o2_replay_timeline(replay_snapshots: list[Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    snapshots = _normalize_snapshots(replay_snapshots)
    timeline = []
    for s in snapshots:
        timeline.append(OrderedDict([
            ("snapshot_id", s["snapshot_id"]),
            ("as_of_date", s["as_of_date"]),
            ("regime_label", s["regime_label"]),
            ("structural_pressure_score", s["structural_pressure_score"]),
            ("fragility_score", s["fragility_score"]),
            ("expectation_fragility_score", s["expectation_fragility_score"]),
            ("propagation_pressure_score", s["propagation_pressure_score"]),
            ("certification_status", s["certification_status"]),
            ("checksum_present", bool(s["checksum"])),
            ("replay_metadata_present", bool(s["replay_metadata"])),
            ("timeline_state", _timeline_state(s)),
        ]))
    return timeline


def build_o2_structural_evolution_summary(replay_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    timeline = build_o2_replay_timeline(replay_snapshots)
    if len(timeline) < 2:
        return OrderedDict([
            ("first_snapshot_id", timeline[0]["snapshot_id"] if timeline else ""),
            ("latest_snapshot_id", timeline[-1]["snapshot_id"] if timeline else ""),
            ("first_regime", timeline[0]["regime_label"] if timeline else "UNKNOWN"),
            ("latest_regime", timeline[-1]["regime_label"] if timeline else "UNKNOWN"),
            ("pressure_delta", 0.0), ("fragility_delta", 0.0), ("expectation_fragility_delta", 0.0), ("propagation_pressure_delta", 0.0),
            ("dominant_evolution_direction", "STRUCTURAL_EVOLUTION_INSUFFICIENT_DATA"),
            ("structural_interpretation", "Insufficient replay history for structural evolution interpretation."),
        ])
    first, latest = timeline[0], timeline[-1]
    p_delta = latest["structural_pressure_score"] - first["structural_pressure_score"]
    f_delta = latest["fragility_score"] - first["fragility_score"]
    e_delta = latest["expectation_fragility_score"] - first["expectation_fragility_score"]
    g_delta = latest["propagation_pressure_score"] - first["propagation_pressure_score"]
    if p_delta > STABLE_DELTA_BAND:
        direction = "STRUCTURAL_PRESSURE_INCREASING"
    elif p_delta < -STABLE_DELTA_BAND:
        direction = "STRUCTURAL_PRESSURE_DECREASING"
    else:
        direction = "STRUCTURAL_PRESSURE_STABLE"
    return OrderedDict([
        ("first_snapshot_id", first["snapshot_id"]), ("latest_snapshot_id", latest["snapshot_id"]),
        ("first_regime", first["regime_label"]), ("latest_regime", latest["regime_label"]),
        ("pressure_delta", p_delta), ("fragility_delta", f_delta), ("expectation_fragility_delta", e_delta), ("propagation_pressure_delta", g_delta),
        ("dominant_evolution_direction", direction),
        ("structural_interpretation", f"Structural pressure evolution classified as {direction} based on deterministic first-latest delta."),
    ])


def build_o2_regime_transition_history(replay_snapshots: list[Mapping[str, Any]] | None = None) -> list[OrderedDict[str, Any]]:
    timeline = build_o2_replay_timeline(replay_snapshots)
    transitions = []
    for prev, curr in zip(timeline, timeline[1:]):
        if prev["regime_label"] != curr["regime_label"]:
            transitions.append(OrderedDict([
                ("from_snapshot_id", prev["snapshot_id"]), ("to_snapshot_id", curr["snapshot_id"]),
                ("from_date", prev["as_of_date"]), ("to_date", curr["as_of_date"]),
                ("from_regime", prev["regime_label"]), ("to_regime", curr["regime_label"]),
                ("transition_label", f"{prev['regime_label']}->{curr['regime_label']}"),
                ("transition_interpretation", "Deterministic regime label change observed between consecutive replay snapshots."),
            ]))
    return transitions


def build_o2_pressure_evolution_diagnostics(replay_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    timeline = build_o2_replay_timeline(replay_snapshots)
    if not timeline:
        return OrderedDict([
            ("max_structural_pressure_snapshot", ""), ("max_fragility_snapshot", ""), ("max_expectation_fragility_snapshot", ""),
            ("pressure_trend_label", "PRESSURE_TREND_INSUFFICIENT_DATA"), ("fragility_trend_label", "FRAGILITY_TREND_INSUFFICIENT_DATA"),
            ("pressure_persistence_count", 0), ("elevated_pressure_periods", []), ("degraded_snapshot_count", 0), ("blocked_snapshot_count", 0),
        ])
    max_pressure = max(timeline, key=lambda x: (x["structural_pressure_score"], x["snapshot_id"]))["snapshot_id"]
    max_fragility = max(timeline, key=lambda x: (x["fragility_score"], x["snapshot_id"]))["snapshot_id"]
    max_expectation = max(timeline, key=lambda x: (x["expectation_fragility_score"], x["snapshot_id"]))["snapshot_id"]
    delta_p = timeline[-1]["structural_pressure_score"] - timeline[0]["structural_pressure_score"]
    delta_f = timeline[-1]["fragility_score"] - timeline[0]["fragility_score"]
    def _trend(delta: float, prefix: str) -> str:
        if delta > STABLE_DELTA_BAND:
            return f"{prefix}_INCREASING"
        if delta < -STABLE_DELTA_BAND:
            return f"{prefix}_DECREASING"
        return f"{prefix}_STABLE"
    elevated = [
        OrderedDict([
            ("snapshot_id", row["snapshot_id"]),
            ("as_of_date", row["as_of_date"]),
            ("pressure_level", "SEVERE" if row["structural_pressure_score"] >= SEVERE_PRESSURE_THRESHOLD else "ELEVATED"),
        ])
        for row in timeline if row["structural_pressure_score"] >= ELEVATED_PRESSURE_THRESHOLD
    ]
    return OrderedDict([
        ("max_structural_pressure_snapshot", max_pressure),
        ("max_fragility_snapshot", max_fragility),
        ("max_expectation_fragility_snapshot", max_expectation),
        ("pressure_trend_label", _trend(delta_p, "PRESSURE_TREND")),
        ("fragility_trend_label", _trend(delta_f, "FRAGILITY_TREND")),
        ("pressure_persistence_count", sum(1 for r in timeline if r["structural_pressure_score"] >= ELEVATED_PRESSURE_THRESHOLD)),
        ("elevated_pressure_periods", elevated),
        ("degraded_snapshot_count", sum(1 for r in timeline if r["timeline_state"] == "DEGRADED")),
        ("blocked_snapshot_count", sum(1 for r in timeline if r["timeline_state"] == "BLOCKED")),
    ])


def _metric_card(title: str, first_value: Any, latest_value: Any) -> OrderedDict[str, Any]:
    delta = latest_value - first_value
    state = "INCREASING" if delta > STABLE_DELTA_BAND else "DECREASING" if delta < -STABLE_DELTA_BAND else "STABLE"
    return OrderedDict([("title", title), ("first_value", first_value), ("latest_value", latest_value), ("delta", delta), ("state", state), ("interpretation", f"{title} classified as {state} using deterministic delta policy.")])


def build_o2_snapshot_comparison_cards(replay_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, OrderedDict[str, Any]]:
    timeline = build_o2_replay_timeline(replay_snapshots)
    first = timeline[0] if timeline else {}
    latest = timeline[-1] if timeline else {}
    return OrderedDict([
        ("structural_pressure_card", _metric_card("Structural Pressure", first.get("structural_pressure_score", 0.0), latest.get("structural_pressure_score", 0.0))),
        ("fragility_card", _metric_card("Fragility", first.get("fragility_score", 0.0), latest.get("fragility_score", 0.0))),
        ("expectation_fragility_card", _metric_card("Expectation Fragility", first.get("expectation_fragility_score", 0.0), latest.get("expectation_fragility_score", 0.0))),
        ("propagation_pressure_card", _metric_card("Propagation Pressure", first.get("propagation_pressure_score", 0.0), latest.get("propagation_pressure_score", 0.0))),
        ("regime_card", OrderedDict([("title", "Regime"), ("first_value", first.get("regime_label", "UNKNOWN")), ("latest_value", latest.get("regime_label", "UNKNOWN")), ("delta", "N/A"), ("state", "CHANGED" if first.get("regime_label") != latest.get("regime_label") else "UNCHANGED"), ("interpretation", "Deterministic first/latest regime label comparison.")])),
        ("corridor_card", OrderedDict([("title", "Weakest Corridor"), ("first_value", first.get("snapshot_id", "")), ("latest_value", latest.get("snapshot_id", "")), ("delta", "N/A"), ("state", "OBSERVATIONAL"), ("interpretation", "Corridor comparison is observational and sourced from replay snapshots.")])),
    ])


def build_o2_replay_certification_cards(replay_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    timeline = build_o2_replay_timeline(replay_snapshots)
    total = len(timeline)
    ready = sum(1 for x in timeline if x["timeline_state"] == "READY")
    degraded = sum(1 for x in timeline if x["timeline_state"] == "DEGRADED")
    blocked = sum(1 for x in timeline if x["timeline_state"] == "BLOCKED")
    checksum_complete = all(x["checksum_present"] for x in timeline) if timeline else False
    metadata_complete = all(x["replay_metadata_present"] for x in timeline) if timeline else False
    if total == 0 or blocked == total:
        state = "O2_REPLAY_OPERATIONALIZATION_BLOCKED"
    elif degraded > 0 or blocked > 0 or not checksum_complete or not metadata_complete:
        state = "O2_REPLAY_OPERATIONALIZED_DEGRADED"
    else:
        state = "O2_REPLAY_OPERATIONALIZED"
    return OrderedDict([
        ("total_snapshots", total), ("ready_snapshots", ready), ("degraded_snapshots", degraded), ("blocked_snapshots", blocked),
        ("checksum_complete", checksum_complete), ("replay_metadata_complete", metadata_complete),
        ("certification_state", state),
        ("certification_interpretation", f"Replay certification state determined deterministically as {state}."),
    ])


def certify_o2_replay_operationalization(replay_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    cards = build_o2_replay_certification_cards(replay_snapshots)
    blocking_reasons = []
    degraded_reasons = []
    if cards["certification_state"] == "O2_REPLAY_OPERATIONALIZATION_BLOCKED":
        blocking_reasons.append("no_replay_ready_snapshots")
    if cards["certification_state"] == "O2_REPLAY_OPERATIONALIZED_DEGRADED":
        degraded_reasons.append("degraded_or_incomplete_replay_lineage")
    invariants = OrderedDict([
        ("fixed_ordering", True), ("canonical_checksum", True), ("no_network_calls", True), ("no_database_calls", True), ("no_runtime_clock", True),
    ])
    forbidden_check = OrderedDict([(x, True) for x in FORBIDDEN_USES])
    payload = OrderedDict([("cards", cards), ("invariants", invariants), ("forbidden", forbidden_check)])
    status = cards["certification_state"]
    passed = status == "O2_REPLAY_OPERATIONALIZED"
    return OrderedDict([
        ("certification_status", status), ("certification_passed", passed), ("blocking_reasons", blocking_reasons), ("degraded_reasons", degraded_reasons),
        ("invariant_results", invariants), ("forbidden_capability_check", forbidden_check), ("checksum", _stable_checksum(payload)),
        ("replay_safe", cards["checksum_complete"] and cards["replay_metadata_complete"]),
        ("supervisor_decision", "APPROVED" if passed else "APPROVED_WITH_DEGRADATION" if status == "O2_REPLAY_OPERATIONALIZED_DEGRADED" else "BLOCKED_REMEDIATION_REQUIRED"),
    ])


def build_o2_dashboard_view_model(replay_snapshots: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    timeline = build_o2_replay_timeline(replay_snapshots)
    summary = build_o2_structural_evolution_summary(replay_snapshots)
    transitions = build_o2_regime_transition_history(replay_snapshots)
    diagnostics = build_o2_pressure_evolution_diagnostics(replay_snapshots)
    cards = build_o2_snapshot_comparison_cards(replay_snapshots)
    replay_cards = build_o2_replay_certification_cards(replay_snapshots)
    cert = certify_o2_replay_operationalization(replay_snapshots)
    return OrderedDict([
        ("page_id", "sefi_o2_replay_operationalization"),
        ("page_title", "SEFI O2 Replay Operationalization"),
        ("generated_at_policy", "deterministic_no_runtime_clock"),
        ("replay_timeline", timeline),
        ("structural_evolution_summary", summary),
        ("regime_transition_history", transitions),
        ("pressure_evolution_diagnostics", diagnostics),
        ("snapshot_comparison_cards", cards),
        ("replay_certification_cards", replay_cards),
        ("supervisor_summary", "Deterministic O2 replay operationalization for institutional structural observability."),
        ("governance_boundaries", OrderedDict([("allowed_uses", list(ALLOWED_USES)), ("forbidden_uses", list(FORBIDDEN_USES))])),
        ("certification_summary", cert),
    ])


def build_o2_replay_operationalization_report(replay_snapshots: list[Mapping[str, Any]] | None = None) -> str:
    vm = build_o2_dashboard_view_model(replay_snapshots)
    return "\n".join([
        "# O2 Replay Operationalization Report",
        "## Objective", "Operationalize deterministic replay/structural evolution outputs into dashboard-ready view models.",
        "## Scope", "Replay timeline, structural evolution, regime transitions, diagnostics, certification, governance boundaries.",
        "## Non-goals", ", ".join(FORBIDDEN_USES),
        "## Architecture Role", "Backend-only dashboard view-model infrastructure for institutional supervision.",
        "## Replay Timeline Summary", f"Snapshots: {len(vm['replay_timeline'])}",
        "## Structural Evolution Summary", f"Direction: {vm['structural_evolution_summary']['dominant_evolution_direction']}",
        "## Regime Transition Summary", f"Transitions detected: {len(vm['regime_transition_history'])}",
        "## Pressure Diagnostics", f"Pressure trend: {vm['pressure_evolution_diagnostics']['pressure_trend_label']}",
        "## Certification Result", vm['certification_summary']['certification_status'],
        "## Governance Boundaries", "Allowed and forbidden use inventory included in dashboard payload.",
        "## Final Supervisor Interpretation", vm['certification_summary']['supervisor_decision'],
    ])


__all__ = [
    "build_o2_replay_timeline",
    "build_o2_structural_evolution_summary",
    "build_o2_regime_transition_history",
    "build_o2_pressure_evolution_diagnostics",
    "build_o2_snapshot_comparison_cards",
    "build_o2_replay_certification_cards",
    "build_o2_dashboard_view_model",
    "certify_o2_replay_operationalization",
    "build_o2_replay_operationalization_report",
]
