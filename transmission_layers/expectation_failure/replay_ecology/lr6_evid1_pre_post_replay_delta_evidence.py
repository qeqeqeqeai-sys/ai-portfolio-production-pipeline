"""LR6-EVID1 explicit pre/post replay delta evidence framework (evidence-only)."""
from __future__ import annotations

from typing import Any

DETERMINISTIC_VERSION = "LR6_EVID1_PRE_POST_REPLAY_DELTA_EVIDENCE_V1"
SOURCE_PHASE = "LR6-EVID1"

EVIDENCE_STATUS_VALUES = {
    "MEASURED",
    "PARTIAL",
    "MISSING_BASELINE",
    "MISSING_ENRICHED",
    "MISSING_BOTH",
    "NOT_COMPARABLE",
}

SUFFICIENCY_VALUES = {
    "SUFFICIENT_FOR_STRUCTURAL_IMPROVEMENT_CLAIM",
    "PARTIAL_EVIDENCE_ONLY",
    "INSUFFICIENT_EVIDENCE_FOR_IMPROVEMENT_CLAIM",
    "BASELINE_OR_ENRICHED_EVIDENCE_MISSING",
}


def _as_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def _delta_status(b: float | None, e: float | None) -> str:
    if b is None and e is None:
        return "MISSING_BOTH"
    if b is None:
        return "MISSING_BASELINE"
    if e is None:
        return "MISSING_ENRICHED"
    return "MEASURED"


def _build_delta_row(*, dimension: str, key: str, baseline: dict[str, Any], enriched: dict[str, Any], extras: dict[str, Any] | None = None) -> dict[str, Any]:
    b = _as_float(baseline.get(key))
    e = _as_float(enriched.get(key))
    status = _delta_status(b, e)
    row: dict[str, Any] = {
        "dimension": dimension,
        "metric_key": key,
        "baseline_value": b,
        "enriched_value": e,
        "delta": None if (b is None or e is None) else e - b,
        "evidence_status": status,
    }
    if extras:
        row.update(extras)
    return row


def build_lr6_evid1_evidence_context(*, baseline_evidence: dict[str, Any] | None = None, enriched_evidence: dict[str, Any] | None = None, inspected_sources: list[str] | None = None) -> dict[str, Any]:
    return {
        "meta": {
            "deterministic_version": DETERMINISTIC_VERSION,
            "source_phase": SOURCE_PHASE,
            "mode": "evidence_only_pre_post_comparison",
        },
        "inspected_sources": list(inspected_sources or []),
        "baseline_evidence": dict(baseline_evidence or {}),
        "enriched_evidence": dict(enriched_evidence or {}),
    }


def build_lr6_evid1_baseline_evidence_profile(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context.get("baseline_evidence") or {})
    return {"label": "baseline", "available": bool(payload), "metrics": payload}


def build_lr6_evid1_enriched_evidence_profile(context: dict[str, Any]) -> dict[str, Any]:
    payload = dict(context.get("enriched_evidence") or {})
    return {"label": "enriched", "available": bool(payload), "metrics": payload}


def build_lr6_evid1_weak_signal_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    return _build_delta_row(dimension="Weak-Signal Attribution", key="weak_signal_attribution_count", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))


def build_lr6_evid1_contradiction_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    row = _build_delta_row(dimension="Contradiction Persistence / Migration", key="contradiction_persistence_count", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))
    row["migration_visibility"] = baseline_profile.get("metrics", {}).get("contradiction_migration_visible") is True and enriched_profile.get("metrics", {}).get("contradiction_migration_visible") is True
    return row


def build_lr6_evid1_propagation_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    row = _build_delta_row(dimension="Propagation Diversity", key="propagation_bridge_diversity", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))
    row["non_obviousness_indicator"] = enriched_profile.get("metrics", {}).get("propagation_non_obvious") is True
    return row


def build_lr6_evid1_topology_drift_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    return _build_delta_row(dimension="Topology Drift", key="topology_drift_indicator", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))


def build_lr6_evid1_saturation_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    row = _build_delta_row(dimension="Replay Saturation / Monoculture", key="saturation_concentration", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))
    row["diversity_direction"] = "improved" if isinstance(row.get("delta"), float) and row["delta"] < 0 else "worsened_or_unknown"
    return row


def build_lr6_evid1_megacap_gravity_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    return _build_delta_row(dimension="Megacap Semantic Gravity", key="megacap_concentration", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))


def build_lr6_evid1_replay_richness_delta(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> dict[str, Any]:
    return _build_delta_row(dimension="Replay Richness", key="replay_richness_score", baseline=baseline_profile.get("metrics", {}), enriched=enriched_profile.get("metrics", {}))


def build_lr6_evid1_pre_post_delta_table(baseline_profile: dict[str, Any], enriched_profile: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        build_lr6_evid1_weak_signal_delta(baseline_profile, enriched_profile),
        build_lr6_evid1_contradiction_delta(baseline_profile, enriched_profile),
        build_lr6_evid1_propagation_delta(baseline_profile, enriched_profile),
        build_lr6_evid1_topology_drift_delta(baseline_profile, enriched_profile),
        build_lr6_evid1_saturation_delta(baseline_profile, enriched_profile),
        build_lr6_evid1_megacap_gravity_delta(baseline_profile, enriched_profile),
        build_lr6_evid1_replay_richness_delta(baseline_profile, enriched_profile),
    ]


def build_lr6_evid1_evidence_sufficiency_assessment(delta_table: list[dict[str, Any]]) -> dict[str, Any]:
    statuses = [row.get("evidence_status") for row in delta_table]
    measured_count = sum(1 for s in statuses if s == "MEASURED")
    missing_count = sum(1 for s in statuses if s in {"MISSING_BASELINE", "MISSING_ENRICHED", "MISSING_BOTH"})
    if missing_count > 0:
        decision = "BASELINE_OR_ENRICHED_EVIDENCE_MISSING"
    elif measured_count >= 5:
        decision = "SUFFICIENT_FOR_STRUCTURAL_IMPROVEMENT_CLAIM"
    elif measured_count >= 2:
        decision = "PARTIAL_EVIDENCE_ONLY"
    else:
        decision = "INSUFFICIENT_EVIDENCE_FOR_IMPROVEMENT_CLAIM"
    return {"decision": decision, "measured_count": measured_count, "missing_count": missing_count, "status_counts": {s: statuses.count(s) for s in sorted(set(statuses))}}


def build_lr6_evid1_supervisor_review(context: dict[str, Any]) -> dict[str, Any]:
    base = build_lr6_evid1_baseline_evidence_profile(context)
    enr = build_lr6_evid1_enriched_evidence_profile(context)
    table = build_lr6_evid1_pre_post_delta_table(base, enr)
    assessment = build_lr6_evid1_evidence_sufficiency_assessment(table)
    return {"context_meta": context.get("meta", {}), "delta_table": table, "evidence_sufficiency_assessment": assessment, "anti_hype_guardrail": "No ecological improvement claims without measured pre/post delta evidence."}


def certify_lr6_evid1_evidence_boundary() -> dict[str, Any]:
    return {
        "evidence_only": True,
        "comparison_only": True,
        "execution_authorized": False,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_evid1_markdown_report(context: dict[str, Any]) -> str:
    base = build_lr6_evid1_baseline_evidence_profile(context)
    enr = build_lr6_evid1_enriched_evidence_profile(context)
    table = build_lr6_evid1_pre_post_delta_table(base, enr)
    assess = build_lr6_evid1_evidence_sufficiency_assessment(table)
    boundary = certify_lr6_evid1_evidence_boundary()
    return "\n".join([
        "# LR6-EVID1 Pre/Post Replay Delta Evidence",
        "## objective",
        "Did enriched replay measurably change ecology versus baseline?",
        "## inspected evidence sources",
        ", ".join(context.get("inspected_sources", [])) or "None provided.",
        "## baseline evidence profile",
        str(base),
        "## enriched evidence profile",
        str(enr),
        "## pre/post delta table",
        str(table),
        "## weak-signal delta",
        str(table[0]),
        "## contradiction delta",
        str(table[1]),
        "## propagation delta",
        str(table[2]),
        "## topology drift delta",
        str(table[3]),
        "## saturation / monoculture delta",
        str(table[4]),
        "## megacap gravity delta",
        str(table[5]),
        "## replay richness delta",
        str(table[6]),
        "## evidence sufficiency assessment",
        str(assess),
        "## anti-hype interpretation guardrails",
        "Do not infer improvement from scaffolding, governance success, or report sophistication.",
        "## final recommendation",
        assess["decision"],
        "## boundary certification",
        str(boundary),
    ])


__all__ = [n for n in globals() if n.startswith("build_lr6_evid1_") or n == "certify_lr6_evid1_evidence_boundary" or n in {"EVIDENCE_STATUS_VALUES", "SUFFICIENCY_VALUES"}]
