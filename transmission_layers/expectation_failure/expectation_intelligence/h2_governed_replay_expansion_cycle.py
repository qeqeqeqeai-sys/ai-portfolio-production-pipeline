from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Mapping

CERTIFIED_GOVERNED_REPLAY_EXPANSION_CYCLE = "CERTIFIED_GOVERNED_REPLAY_EXPANSION_CYCLE"
DEGRADED_GOVERNED_REPLAY_EXPANSION_CYCLE = "DEGRADED_GOVERNED_REPLAY_EXPANSION_CYCLE"
BLOCKED_GOVERNED_REPLAY_EXPANSION_CYCLE = "BLOCKED_GOVERNED_REPLAY_EXPANSION_CYCLE"
H2_DENSITY_IMPROVED = "H2_DENSITY_IMPROVED"
H2_DENSITY_UNCHANGED = "H2_DENSITY_UNCHANGED"
H2_DENSITY_DEGRADED = "H2_DENSITY_DEGRADED"
H2_POST_RUN_INSUFFICIENT_DATA = "H2_POST_RUN_INSUFFICIENT_DATA"

_FORBIDDEN_RE = re.compile(r"\b(buy|sell|trade|predict|forecast|autonomous|auto-execute|execute now)\b", re.IGNORECASE)


def _d(v: Any) -> dict[str, Any]:
    return dict(v) if isinstance(v, Mapping) else {}


def _t(v: Any, d: str = "") -> str:
    return (str(v).strip() if v is not None else "") or d


def _i(v: Any, d: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return d


def _f(v: Any, d: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return d


def _ck(v: Any) -> str:
    return sha256(str(v).encode("utf-8")).hexdigest()


def _extract_h1_inventory(h1_dashboard_payload: Mapping[str, Any] | None = None, h1_inventory: Mapping[str, Any] | None = None, d7_view_model: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(h1_inventory, Mapping) and h1_inventory:
        return _d(h1_inventory)
    d7 = _d(d7_view_model)
    if isinstance(d7.get("h1_historical_density_expansion"), Mapping):
        payload = _d(d7.get("h1_historical_density_expansion"))
    else:
        payload = _d(h1_dashboard_payload)
    return {
        "current_replay_depth": _i(_d(payload.get("Historical Density Overview")).get("current_replay_depth")),
        "replay_coverage": _d(payload.get("Replay Coverage")),
        "regime_diversity": _d(payload.get("Regime Diversity")),
        "contradiction_diversity": _d(payload.get("Contradiction Evolution Richness")),
        "continuity_linkage_density": _d(payload.get("Continuity Linkage Density")),
        "recurring_finding_density": _d(payload.get("Recurring Finding Density")),
        "confidence_movement_density": _d(payload.get("Confidence Movement Density")),
        "lineage_richness": _d(payload.get("Lineage Richness")),
    }


def build_h2_pre_expansion_baseline(*, h1_dashboard_payload: Mapping[str, Any] | None = None, h1_inventory: Mapping[str, Any] | None = None, d7_view_model: Mapping[str, Any] | None = None, h1_certification: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    inv = _extract_h1_inventory(h1_dashboard_payload, h1_inventory, d7_view_model)
    baseline = OrderedDict([
        ("replay_depth", _i(inv.get("current_replay_depth"))),
        ("replay_coverage", OrderedDict(_d(inv.get("replay_coverage")))),
        ("regime_diversity", OrderedDict(_d(inv.get("regime_diversity")))),
        ("contradiction_diversity", OrderedDict(_d(inv.get("contradiction_diversity")))),
        ("continuity_linkage_density", OrderedDict(_d(inv.get("continuity_linkage_density")))),
        ("recurring_finding_density", OrderedDict(_d(inv.get("recurring_finding_density")))),
        ("confidence_movement_density", OrderedDict(_d(inv.get("confidence_movement_density")))),
        ("lineage_richness", OrderedDict(_d(inv.get("lineage_richness")))),
        ("certification_status", _t(_d(h1_certification).get("certification_status"), "UNKNOWN_H1_STATUS")),
    ])
    baseline["baseline_checksum"] = _ck(baseline)
    return baseline


def build_h2_governed_expansion_recommendation(*, h1_expansion_plan: Mapping[str, Any] | None, pre_expansion_baseline: Mapping[str, Any] | None) -> OrderedDict[str, Any]:
    plan = _d(h1_expansion_plan)
    baseline = _d(pre_expansion_baseline)
    batch_size = _i(plan.get("recommended_expansion_batch_size"), 0)
    windows = list(plan.get("recommended_next_replay_window_ranges") or [])
    blocked: list[str] = []
    degraded: list[str] = []
    if not plan:
        blocked.append("MISSING_H1_EXPANSION_PLAN")
    if not baseline:
        blocked.append("MISSING_H1_BASELINE")
    if batch_size <= 0:
        degraded.append("NON_POSITIVE_BATCH_SIZE")
        batch_size = 1
    if not windows:
        degraded.append("MISSING_WINDOW_RANGES")
        windows = ["window_operator_defined"]
    return OrderedDict([
        ("recommended_batch_size", batch_size),
        ("recommended_replay_window_count", min(batch_size, 5)),
        ("recommended_expansion_window_strategy", "bounded_operator_approved_progressive_windows"),
        ("minimum_expected_density_improvement", 1),
        ("operator_approval_requirements", ["non_dry_run_explicit_approval", "explicit_window_count_confirmation", "governance_flag_confirmation"]),
        ("explicit_governance_requirements", ["D8.B4_governance_preserved", "append_only_persistence", "duplicate_prevention_preserved", "checksum_lineage_preserved", "no_direct_sql", "manual_operator_execution_only"]),
        ("recommended_window_ranges", windows),
        ("blocked_reasons", sorted(blocked)),
        ("degraded_reasons", sorted(degraded)),
        ("recommendation_mode", "recommendation_only_no_writes"),
    ])


def build_h2_operator_execution_checklist(*, recommendation: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    window_count = _i(_d(recommendation).get("recommended_replay_window_count"), 1)
    return [
        OrderedDict([("step", "confirm_d8_b4_governance_flags"), ("required", True)]),
        OrderedDict([("step", "confirm_non_dry_approval"), ("required", True)]),
        OrderedDict([("step", "confirm_append_only_persistence_approval"), ("required", True)]),
        OrderedDict([("step", "confirm_duplicate_prevention_approval"), ("required", True)]),
        OrderedDict([("step", "confirm_checksum_lineage_approval"), ("required", True)]),
        OrderedDict([("step", "confirm_no_direct_sql"), ("required", True)]),
        OrderedDict([("step", "confirm_bounded_window_count"), ("required", True), ("value", window_count)]),
        OrderedDict([("step", "confirm_d21_script_name_command"), ("required", True), ("value", "python -m transmission_layers.expectation_failure.expectation_intelligence.d21_limited_governed_non_dry_historical_backfill ...")]),
        OrderedDict([("step", "confirm_post_run_d8_c_readback"), ("required", True)]),
        OrderedDict([("step", "confirm_d7_h1_h2_rerender_after_execution"), ("required", True)]),
    ]


def build_h2_d21_command_template(*, recommendation: Mapping[str, Any]) -> str:
    window_count = max(1, _i(_d(recommendation).get("recommended_replay_window_count"), 1))
    return (
        "python -m transmission_layers.expectation_failure.expectation_intelligence.d21_limited_governed_non_dry_historical_backfill "
        f"--window-count {window_count} "
        "--non-dry-run false "
        "--operator-approval-token <REQUIRED_OPERATOR_APPROVAL_TOKEN> "
        "--governance-ack D8.B4 --append-only-ack true --duplicate-prevention-ack true --checksum-lineage-ack true"
    )


def build_h2_post_expansion_comparison(*, pre_expansion_baseline: Mapping[str, Any], post_h1_dashboard_payload: Mapping[str, Any] | None = None, post_h1_inventory: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    pre = _d(pre_expansion_baseline)
    post_inv = _extract_h1_inventory(post_h1_dashboard_payload, post_h1_inventory, None)
    if not pre or not post_inv:
        return OrderedDict([("density_improvement_verdict", H2_POST_RUN_INSUFFICIENT_DATA)])
    deltas = OrderedDict([
        ("depth_delta", _i(post_inv.get("current_replay_depth")) - _i(pre.get("replay_depth"))),
        ("regime_diversity_delta", _i(_d(post_inv.get("regime_diversity")).get("distinct_regimes")) - _i(_d(pre.get("regime_diversity")).get("distinct_regimes"))),
        ("contradiction_diversity_delta", _i(_d(post_inv.get("contradiction_diversity")).get("contradiction_claim_count")) - _i(_d(pre.get("contradiction_diversity")).get("contradiction_claim_count"))),
        ("continuity_linkage_delta", _f(_d(post_inv.get("continuity_linkage_density")).get("avg_linkage_per_run")) - _f(_d(pre.get("continuity_linkage_density")).get("avg_linkage_per_run"))),
        ("recurring_finding_delta", _i(_d(post_inv.get("recurring_finding_density")).get("cluster_count")) - _i(_d(pre.get("recurring_finding_density")).get("cluster_count"))),
        ("confidence_movement_delta", _i(_d(post_inv.get("confidence_movement_density")).get("movement_count")) - _i(_d(pre.get("confidence_movement_density")).get("movement_count"))),
        ("lineage_richness_delta", _i(_d(post_inv.get("lineage_richness")).get("distinct_lineage_refs")) - _i(_d(pre.get("lineage_richness")).get("distinct_lineage_refs"))),
    ])
    score = sum(1 for v in deltas.values() if float(v) > 0) - sum(1 for v in deltas.values() if float(v) < 0)
    verdict = H2_DENSITY_IMPROVED if score > 0 else (H2_DENSITY_DEGRADED if score < 0 else H2_DENSITY_UNCHANGED)
    deltas["density_improvement_verdict"] = verdict
    return deltas


def build_h2_cycle_dashboard_payload(*, pre_expansion_baseline: Mapping[str, Any], governed_expansion_recommendation: Mapping[str, Any], operator_execution_checklist: list[Mapping[str, Any]], d21_command_template: str, post_expansion_comparison: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Pre-Expansion Baseline", OrderedDict(deepcopy(dict(pre_expansion_baseline)))),
        ("Governed Expansion Recommendation", OrderedDict(deepcopy(dict(governed_expansion_recommendation)))),
        ("Operator Execution Checklist", [OrderedDict(deepcopy(dict(x))) for x in operator_execution_checklist]),
        ("D21 Command Template", d21_command_template),
        ("Post-Expansion Comparison", OrderedDict(deepcopy(dict(post_expansion_comparison or {})))),
        ("Governance/Lineage Controls", OrderedDict([("h2_is_recommendation_only", True), ("no_writes_by_h2", True), ("requires_operator_manual_execution", True), ("no_direct_sql", True), ("deterministic_ordering", True)])),
    ])


def certify_h2_governed_replay_expansion_cycle(*, pre_expansion_baseline: Mapping[str, Any] | None, governed_expansion_recommendation: Mapping[str, Any] | None, operator_execution_checklist: list[Mapping[str, Any]] | None, d21_command_template: str | None, cycle_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    blocking, degraded = [], []
    if not pre_expansion_baseline:
        blocking.append("MISSING_H1_BASELINE")
    if not governed_expansion_recommendation:
        blocking.append("MISSING_EXPANSION_RECOMMENDATION")
    if not operator_execution_checklist:
        blocking.append("MISSING_OPERATOR_CHECKLIST")
    cmd = _t(d21_command_template)
    if not cmd:
        blocking.append("MISSING_COMMAND_TEMPLATE")
    if "operator-approval-token" not in cmd:
        degraded.append("COMMAND_TEMPLATE_MISSING_APPROVAL_PLACEHOLDER")
    if _FORBIDDEN_RE.search(_t(cycle_dashboard_payload)):
        blocking.append("FORBIDDEN_LANGUAGE")
    status = BLOCKED_GOVERNED_REPLAY_EXPANSION_CYCLE if blocking else (DEGRADED_GOVERNED_REPLAY_EXPANSION_CYCLE if degraded else CERTIFIED_GOVERNED_REPLAY_EXPANSION_CYCLE)
    return OrderedDict([
        ("certification_status", status),
        ("blocking_reasons", sorted(blocking)),
        ("degraded_reasons", sorted(degraded)),
        ("no_direct_sql", True),
        ("no_writes_by_h2", True),
        ("no_predictive_trading_behavior", True),
        ("no_autonomous_actions", True),
        ("deterministic_ordering_preserved", True),
    ])


def build_h2_report_payload(*, cycle_dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", "H2 Governed Replay Expansion Execution Cycle"),
        ("cycle_dashboard_payload", OrderedDict(deepcopy(dict(cycle_dashboard_payload)))),
        ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True),
        ("no_writes_performed", True),
        ("no_predictive_behavior", True),
        ("no_autonomous_actions", True),
    ])


def build_h2_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert = _d(_d(report_payload).get("certification"))
    return "\n".join([
        "# H2 Governed Replay Expansion Execution Cycle",
        f"- Certification: {_t(cert.get('certification_status'), 'UNKNOWN')}",
        "- Execution wrapper only; no writes, no direct SQL, explicit operator approvals required.",
    ])


__all__ = [k for k in list(globals()) if k.startswith("build_h2_") or k.startswith("certify_h2_") or k.startswith("H2_") or k.endswith("GOVERNED_REPLAY_EXPANSION_CYCLE")]
