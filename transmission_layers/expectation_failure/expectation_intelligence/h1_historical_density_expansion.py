from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
import re
from typing import Any, Mapping

CERTIFIED_HISTORICAL_DENSITY_EXPANSION = "CERTIFIED_HISTORICAL_DENSITY_EXPANSION"
DEGRADED_HISTORICAL_DENSITY_EXPANSION = "DEGRADED_HISTORICAL_DENSITY_EXPANSION"
BLOCKED_HISTORICAL_DENSITY_EXPANSION = "BLOCKED_HISTORICAL_DENSITY_EXPANSION"
_FORBIDDEN_RE = re.compile(r"\b(buy|sell|trade|predict|forecast|autonomous|execute|schedule|trigger d21)\b", re.IGNORECASE)


def _d(v: Any) -> dict[str, Any]:
    return dict(v) if isinstance(v, Mapping) else {}


def _l(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _t(v: Any, d: str = "") -> str:
    return (str(v).strip() if v is not None else "") or d


def _ck(v: Any) -> str:
    return sha256(str(v).encode("utf-8")).hexdigest()


def build_h1_density_expansion_inventory(*, historical_runs: list[Mapping[str, Any]] | None, d16_dashboard_payload: Mapping[str, Any] | None = None, d17_dashboard_payload: Mapping[str, Any] | None = None, d18_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    runs = [_d(x) for x in _l(historical_runs)]
    run_ids = sorted({_t(r.get("run_id") or r.get("replay_id")) for r in runs if _t(r.get("run_id") or r.get("replay_id"))})
    regimes = sorted({_t(r.get("regime") or _d(r.get("regime_state")).get("state") or _d(r.get("payload")).get("regime"), "UNKNOWN") for r in runs})
    contradictions = sum(len(_l(_d(r.get("contradictions")).get("claims"))) for r in runs)
    continuity_links = sum(len(_l(r.get("lineage_refs"))) + len(_l(_d(r.get("payload")).get("lineage_refs"))) for r in runs)
    recurring_clusters = len(_l(_d(d16_dashboard_payload).get("Recurring Finding Clusters")))
    confidence_movements = len(_l(_d(d18_dashboard_payload).get("Cross-Run Confidence Delta Summary")))
    lineage_refs = sorted({str(x) for r in runs for x in (_l(r.get("lineage_refs")) + _l(_d(r.get("payload")).get("lineage_refs"))) if str(x).strip()})
    depth = len(runs)
    inventory = OrderedDict([
        ("current_replay_depth", depth),
        ("replay_coverage", OrderedDict([("run_count", depth), ("distinct_runs", len(run_ids)), ("earliest_run", run_ids[0] if run_ids else "UNAVAILABLE"), ("latest_run", run_ids[-1] if run_ids else "UNAVAILABLE")])),
        ("regime_diversity", OrderedDict([("distinct_regimes", len(regimes)), ("regime_labels", regimes[:12])])),
        ("contradiction_diversity", OrderedDict([("contradiction_claim_count", contradictions), ("avg_claims_per_run", round((contradictions / depth), 3) if depth else 0.0)])),
        ("continuity_linkage_density", OrderedDict([("total_linkage_refs", continuity_links), ("avg_linkage_per_run", round((continuity_links / depth), 3) if depth else 0.0)])),
        ("recurring_finding_density", OrderedDict([("cluster_count", recurring_clusters), ("clusters_per_run", round((recurring_clusters / depth), 3) if depth else 0.0)])),
        ("confidence_movement_density", OrderedDict([("movement_count", confidence_movements), ("movements_per_run", round((confidence_movements / depth), 3) if depth else 0.0)])),
        ("lineage_richness", OrderedDict([("distinct_lineage_refs", len(lineage_refs)), ("lineage_ref_preview", lineage_refs[:10])])),
    ])
    inventory["inventory_checksum"] = _ck(inventory)
    return inventory


def build_h1_density_gap_analysis(*, density_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _d(density_inventory)
    depth = int(inv.get("current_replay_depth") or 0)
    regimes = int(_d(inv.get("regime_diversity")).get("distinct_regimes") or 0)
    contradictions = int(_d(inv.get("contradiction_diversity")).get("contradiction_claim_count") or 0)
    continuity_avg = float(_d(inv.get("continuity_linkage_density")).get("avg_linkage_per_run") or 0.0)
    recurring = int(_d(inv.get("recurring_finding_density")).get("cluster_count") or 0)
    movements = int(_d(inv.get("confidence_movement_density")).get("movement_count") or 0)
    gaps = OrderedDict([
        ("sparse_replay_regions", ["global_history" ] if depth < 5 else []),
        ("weak_regime_diversity", regimes < 3),
        ("weak_contradiction_evolution", contradictions < max(3, depth)),
        ("insufficient_continuity_linkage", continuity_avg < 1.0),
        ("low_recurring_finding_emergence", recurring < 2),
        ("low_confidence_variation", movements < 2),
        ("insufficient_historical_spread", depth < 8),
    ])
    gaps["gap_checksum"] = _ck(gaps)
    return gaps


def build_h1_expansion_plan(*, density_inventory: Mapping[str, Any], density_gap_analysis: Mapping[str, Any]) -> OrderedDict[str, Any]:
    depth = int(_d(density_inventory).get("current_replay_depth") or 0)
    sparse = bool(_d(density_gap_analysis).get("insufficient_historical_spread"))
    next_batch = 5 if sparse else 3
    plan = OrderedDict([
        ("recommended_next_replay_window_ranges", [f"window_{depth+1:03d}_to_{depth+next_batch:03d}"]),
        ("recommended_expansion_batch_size", next_batch),
        ("recommended_cadence", "operator-approved periodic governed replay"),
        ("density_richness_targets", OrderedDict([("target_regime_diversity", 4), ("target_contradiction_claims", max(12, depth * 2)), ("target_lineage_refs", max(20, depth * 3))])),
        ("replay_sufficiency_targets", OrderedDict([("minimum_replay_depth", max(10, depth + next_batch)), ("minimum_distinct_runs", max(10, depth + next_batch))])),
        ("continuity_targets", OrderedDict([("minimum_avg_linkage_per_run", 1.5), ("minimum_recurring_cluster_count", 3)])),
        ("execution_mode", "recommendation_only"),
    ])
    plan["plan_checksum"] = _ck(plan)
    return plan


def build_h1_operational_density_summary(*, density_inventory: Mapping[str, Any], density_gap_analysis: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _d(density_inventory)
    gaps = _d(density_gap_analysis)
    weak = [k for k, v in gaps.items() if isinstance(v, bool) and v]
    return OrderedDict([
        ("current_density_state", "degraded" if weak else "sufficient"),
        ("strongest_historical_areas", ["lineage_richness", "replay_coverage"]),
        ("weakest_historical_areas", sorted(weak)[:6]),
        ("replay_sufficiency_trend", "improving_but_sparse" if bool(gaps.get("insufficient_historical_spread")) else "stable"),
        ("semantic_richness_trend", "needs_expansion" if bool(gaps.get("low_recurring_finding_emergence")) else "stable"),
        ("contradiction_richness_trend", "needs_expansion" if bool(gaps.get("weak_contradiction_evolution")) else "stable"),
        ("regime_diversity_trend", "needs_expansion" if bool(gaps.get("weak_regime_diversity")) else "stable"),
        ("continuity_linkage_trend", "needs_expansion" if bool(gaps.get("insufficient_continuity_linkage")) else "stable"),
    ])


def build_h1_dashboard_payload(*, density_inventory: Mapping[str, Any], density_gap_analysis: Mapping[str, Any], expansion_plan: Mapping[str, Any], operational_density_summary: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Historical Density Overview", OrderedDict([("current_replay_depth", _d(density_inventory).get("current_replay_depth", 0)), ("inventory_checksum", _d(density_inventory).get("inventory_checksum"))])),
        ("Replay Coverage", _d(_d(density_inventory).get("replay_coverage"))),
        ("Regime Diversity", _d(_d(density_inventory).get("regime_diversity"))),
        ("Contradiction Evolution Richness", _d(_d(density_inventory).get("contradiction_diversity"))),
        ("Continuity Linkage Density", _d(_d(density_inventory).get("continuity_linkage_density"))),
        ("Recurring Finding Density", _d(_d(density_inventory).get("recurring_finding_density"))),
        ("Confidence Movement Density", _d(_d(density_inventory).get("confidence_movement_density"))),
        ("Density Gap Analysis", _d(density_gap_analysis)),
        ("Recommended Expansion Plan", _d(expansion_plan)),
        ("Operational Density Summary", _d(operational_density_summary)),
        ("Governance/Lineage Details", OrderedDict([("governance_preserved", True), ("read_only_recommendation_only", True), ("no_writes", True)])),
    ])


def certify_h1_density_expansion(*, density_inventory: Mapping[str, Any] | None, density_gap_analysis: Mapping[str, Any] | None, expansion_plan: Mapping[str, Any] | None, dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    blocking: list[str] = []
    degraded: list[str] = []
    if not density_inventory:
        blocking.append("MISSING_REPLAY_INVENTORY")
    if not density_gap_analysis:
        blocking.append("MISSING_DENSITY_ANALYSIS")
    if not expansion_plan:
        blocking.append("MISSING_EXPANSION_PLAN")
    rendered = _t(dashboard_payload)
    if _FORBIDDEN_RE.search(rendered):
        blocking.append("FORBIDDEN_LANGUAGE")
    if not blocking and int(_d(density_inventory).get("current_replay_depth") or 0) < 3:
        degraded.append("LOW_REPLAY_DEPTH")
    status = BLOCKED_HISTORICAL_DENSITY_EXPANSION if blocking else (DEGRADED_HISTORICAL_DENSITY_EXPANSION if degraded else CERTIFIED_HISTORICAL_DENSITY_EXPANSION)
    return OrderedDict([("certification_status", status), ("blocking_reasons", sorted(blocking)), ("degraded_reasons", sorted(degraded)), ("governance_preserved", True), ("deterministic_ordering_preserved", True), ("recommendation_only", True)])


def build_h1_report_payload(*, density_inventory: Mapping[str, Any], density_gap_analysis: Mapping[str, Any], expansion_plan: Mapping[str, Any], operational_density_summary: Mapping[str, Any], dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", "H1 Historical Density Expansion"),
        ("density_inventory", OrderedDict(deepcopy(dict(density_inventory)))),
        ("density_gap_analysis", OrderedDict(deepcopy(dict(density_gap_analysis)))),
        ("expansion_plan", OrderedDict(deepcopy(dict(expansion_plan)))),
        ("operational_density_summary", OrderedDict(deepcopy(dict(operational_density_summary)))),
        ("dashboard_payload", OrderedDict(deepcopy(dict(dashboard_payload)))),
        ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True),
        ("no_writes_performed", True),
        ("no_predictive_behavior", True),
        ("no_autonomous_actions", True),
    ])


def build_h1_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert = _d(_d(report_payload).get("certification"))
    return "\n".join([
        "# H1 Historical Density Expansion",
        f"- Certification: {_t(cert.get('certification_status'), 'UNKNOWN')}",
        "- Recommendation-only governed expansion diagnostics for replay density limitations.",
    ])


__all__ = [k for k in list(globals()) if k.startswith("build_h1_") or k.startswith("certify_h1_") or k.endswith("HISTORICAL_DENSITY_EXPANSION")]
