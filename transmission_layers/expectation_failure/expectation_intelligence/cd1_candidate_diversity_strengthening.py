"""CD1 Candidate-Diversity Strengthening Framework (deterministic, read-only, recommendation-only)."""

from __future__ import annotations

from collections import Counter, OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

CERTIFIED_CANDIDATE_DIVERSITY_STRENGTHENING = "CERTIFIED_CANDIDATE_DIVERSITY_STRENGTHENING"
DEGRADED_CANDIDATE_DIVERSITY_STRENGTHENING = "DEGRADED_CANDIDATE_DIVERSITY_STRENGTHENING"
BLOCKED_CANDIDATE_DIVERSITY_STRENGTHENING = "BLOCKED_CANDIDATE_DIVERSITY_STRENGTHENING"

CD1_TAXONOMY_CATEGORIES = (
    "contradiction-heavy", "continuity-stable", "continuity-fragmented", "transition-regime", "confidence-converging",
    "confidence-diverging", "confidence-oscillatory", "recurring-theme-dense", "sparse-theme", "mixed-state",
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_rows(rows: Any) -> list[dict[str, Any]]:
    if isinstance(rows, Mapping):
        return [dict(rows)]
    return [dict(r) for r in list(rows or []) if isinstance(r, Mapping)]


def _token_set(value: Any) -> list[str]:
    items = value if isinstance(value, list) else [value] if value else []
    out = sorted({str(v).strip().lower() for v in items if str(v).strip()})
    return out


def build_cd1_candidate_diversity_inventory(*, replay_candidates: Any, d16_dashboard_payload: Mapping[str, Any] | None = None, d19_dashboard_payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    rows = _as_rows(deepcopy(replay_candidates))
    regimes = sorted({str(r.get("regime") or r.get("regime_label") or "unknown") for r in rows})
    contradictions = sorted({str(r.get("contradiction_state") or r.get("contradiction_label") or "unknown") for r in rows})
    continuity = sorted({str(r.get("continuity_state") or "unknown") for r in rows})
    confidence = sorted({str(r.get("confidence_state") or r.get("confidence_label") or "unknown") for r in rows})
    recurring = sorted({x for r in rows for x in _token_set(r.get("recurring_findings") or r.get("theme_refs"))})
    semantic = sorted({x for r in rows for x in _token_set(r.get("semantic_themes") or r.get("themes"))})
    families = Counter(str(r.get("pattern_family") or "unclassified") for r in rows)
    return OrderedDict([
        ("candidate_count", len(rows)),
        ("regimes", regimes),
        ("contradiction_states", contradictions),
        ("continuity_states", continuity),
        ("confidence_states", confidence),
        ("recurring_finding_refs", recurring),
        ("semantic_themes", semantic),
        ("pattern_families", OrderedDict((k, families[k]) for k in sorted(families))),
        ("lineage_controls", OrderedDict([("read_only", True), ("no_writes", True), ("no_d21_execution", True)])),
    ])


def build_cd1_diversity_gap_analysis(*, candidate_diversity_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = deepcopy(dict(candidate_diversity_inventory))
    count = int(inv.get("candidate_count") or 0)
    diversity = OrderedDict([
        ("regime diversity", len(inv.get("regimes", []))),
        ("contradiction diversity", len(inv.get("contradiction_states", []))),
        ("continuity-state diversity", len(inv.get("continuity_states", []))),
        ("confidence-state diversity", len(inv.get("confidence_states", []))),
        ("recurring-finding diversity", len(inv.get("recurring_finding_refs", []))),
        ("semantic-theme diversity", len(inv.get("semantic_themes", []))),
    ])
    max_family = max(list((inv.get("pattern_families") or {"unclassified": 0}).values()) or [0])
    structural_risk = "elevated" if count and (max_family / max(count, 1)) >= 0.6 else "contained"
    return OrderedDict(list(diversity.items()) + [
        ("structural concentration risk", structural_risk),
        ("dominant replay-pattern families", [k for k, v in (inv.get("pattern_families") or {}).items() if v == max_family]),
        ("replay-density-without-richness patterns", "present" if count > 0 and len(inv.get("semantic_themes", [])) <= 2 else "not_observed"),
    ])


def build_cd1_candidate_diversity_taxonomy(*, candidate_diversity_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = deepcopy(dict(candidate_diversity_inventory))
    assigned = []
    if len(inv.get("contradiction_states", [])) > 1:
        assigned.append("contradiction-heavy")
    if "stable" in {str(x).lower() for x in inv.get("continuity_states", [])}:
        assigned.append("continuity-stable")
    if any("fragment" in str(x).lower() for x in inv.get("continuity_states", [])):
        assigned.append("continuity-fragmented")
    if len(inv.get("regimes", [])) > 1:
        assigned.append("transition-regime")
    if "converging" in {str(x).lower() for x in inv.get("confidence_states", [])}:
        assigned.append("confidence-converging")
    if "diverging" in {str(x).lower() for x in inv.get("confidence_states", [])}:
        assigned.append("confidence-diverging")
    if "oscillatory" in {str(x).lower() for x in inv.get("confidence_states", [])}:
        assigned.append("confidence-oscillatory")
    assigned.append("recurring-theme-dense" if len(inv.get("recurring_finding_refs", [])) >= 3 else "sparse-theme")
    if not assigned:
        assigned = ["mixed-state"]
    return OrderedDict([("available_categories", list(CD1_TAXONOMY_CATEGORIES)), ("assigned_categories", sorted(set(assigned)))])


def build_cd1_diversification_recommendations(*, diversity_gap_analysis: Mapping[str, Any], taxonomy: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    gaps = dict(diversity_gap_analysis)
    recs = [OrderedDict([("priority", 1), ("title", "Expand semantic-theme coverage"), ("action_type", "recommendation_only"), ("narrative", "Prioritize replay-candidate selection that increases semantic-theme diversity without increasing autonomous execution scope.")])]
    if gaps.get("structural concentration risk") == "elevated":
        recs.append(OrderedDict([("priority", 2), ("title", "Reduce dominant replay-pattern concentration"), ("action_type", "recommendation_only"), ("narrative", "Propose additional candidate families through governed operator review; do not execute D21 commands automatically.")]))
    recs.append(OrderedDict([("priority", 3), ("title", "Governance-preserving diversification"), ("action_type", "recommendation_only"), ("narrative", "Keep all recommendations read-only, non-predictive, and outside live market decision flows.")]))
    return recs


def build_cd1_semantic_richness_assessment(*, candidate_diversity_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = dict(candidate_diversity_inventory)
    replay = int(inv.get("candidate_count") or 0)
    richness = len(inv.get("semantic_themes", [])) + len(inv.get("recurring_finding_refs", []))
    return OrderedDict([
        ("richness growth vs replay growth", "lagging" if replay and richness / replay < 1 else "balanced"),
        ("semantic saturation risk", "elevated" if len(inv.get("semantic_themes", [])) <= 2 and replay >= 5 else "contained"),
        ("recurring-pattern emergence", "dense" if len(inv.get("recurring_finding_refs", [])) >= 3 else "limited"),
        ("structural novelty trajectory", "improving" if len(inv.get("regimes", [])) >= 2 else "flat"),
        ("diminishing-return signals", "present" if replay > 0 and len(inv.get("semantic_themes", [])) <= 1 else "not_observed"),
    ])


def build_cd1_dashboard_payload(*, candidate_diversity_inventory: Mapping[str, Any], diversity_taxonomy: Mapping[str, Any], diversity_gap_analysis: Mapping[str, Any], semantic_richness_assessment: Mapping[str, Any], diversification_recommendations: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("Candidate Diversity Overview", deepcopy(dict(candidate_diversity_inventory))),
        ("Diversity Taxonomy", deepcopy(dict(diversity_taxonomy))),
        ("Diversity Gap Analysis", deepcopy(dict(diversity_gap_analysis))),
        ("Regime Diversity", diversity_gap_analysis.get("regime diversity")),
        ("Contradiction Diversity", diversity_gap_analysis.get("contradiction diversity")),
        ("Continuity-State Diversity", diversity_gap_analysis.get("continuity-state diversity")),
        ("Confidence-State Diversity", diversity_gap_analysis.get("confidence-state diversity")),
        ("Semantic Richness Assessment", deepcopy(dict(semantic_richness_assessment))),
        ("Diversification Recommendations", [OrderedDict(r) for r in diversification_recommendations]),
        ("Governance/Lineage Controls", OrderedDict([("read_only", True), ("no_writes", True), ("no_d21_execution", True), ("no_predictive_or_trading_behavior", True)])),
    ])


def certify_cd1_candidate_diversity_strengthening(*, candidate_diversity_inventory: Mapping[str, Any], dashboard_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    count = int(candidate_diversity_inventory.get("candidate_count") or 0)
    if count <= 0:
        status = BLOCKED_CANDIDATE_DIVERSITY_STRENGTHENING
    elif count < 2:
        status = DEGRADED_CANDIDATE_DIVERSITY_STRENGTHENING
    else:
        status = CERTIFIED_CANDIDATE_DIVERSITY_STRENGTHENING
    return OrderedDict([("status", status), ("candidate_count", count), ("checksum", _stable_checksum({"inventory": candidate_diversity_inventory, "dashboard": dashboard_payload})), ("no_writes", True), ("recommendation_only", True)])


def build_cd1_report_payload(*, dashboard_payload: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([("dashboard", deepcopy(dict(dashboard_payload))), ("certification", deepcopy(dict(certification)))])


def build_cd1_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    cert = (report_payload or {}).get("certification", {}) if isinstance(report_payload, Mapping) else {}
    return "\n".join(["# CD1 Candidate-Diversity Strengthening", f"- Status: {cert.get('status', 'UNKNOWN')}", "- Recommendation layer is read-only and non-autonomous."])


__all__ = [x for x in globals() if x.startswith("build_cd1_") or x.startswith("certify_cd1_") or x.endswith("CANDIDATE_DIVERSITY_STRENGTHENING") or x == "CD1_TAXONOMY_CATEGORIES"]
