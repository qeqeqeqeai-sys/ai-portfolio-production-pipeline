from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

REGIMES = (
    "structurally_supported_expectation",
    "concentrated_fragility_expectation",
    "contradiction_heavy_expectation",
    "exhaustion_risk_expectation",
    "semantically_deteriorating_expectation",
    "evidence_supported_expectation",
    "caveat_heavy_expectation",
    "mixed_expectation_regime",
    "insufficient_intelligence",
)
STATUS_ORDER = ("OPERATIONALLY_USABLE", "DEGRADED_OPERATIONAL_INTELLIGENCE", "LIMITED_INTERPRETABILITY", "BLOCKED_EXPECTATION_INTELLIGENCE")


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _as_text(v: Any, default: str = "") -> str:
    t = str(v).strip() if v is not None else ""
    return t or default


def _num(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def classify_e5_expectation_regime(e1: Mapping[str, Any], e2: Mapping[str, Any], e3: Mapping[str, Any], e4: Mapping[str, Any]) -> str:
    if not e1:
        return "insufficient_intelligence"
    contradiction = _num((e1.get("contradiction_summary") or {}).get("contradiction_profile", {}).get("contradiction_persistence_score"))
    exhaustion = _as_text((e1.get("exhaustion_profile") or {}).get("exhaustion_risk_level"), "unknown")
    concentration = _num((e1.get("fragility_concentration_summary") or {}).get("fragility_concentration_profile", {}).get("top_theme_share"))
    evidence_profiles = _as_list((e2.get("evidence_quality_profiles") if isinstance(e2, Mapping) else []))
    weak_evidence = any(_num(row.get("evidence_quality_score")) < 50 for row in evidence_profiles)
    temporal = _as_text((e3.get("temporal_memory_index") or {}).get("history_sufficiency"), "insufficient_history")
    semantic_dir = _as_text((e4.get("narrative_drift_profile") or {}).get("narrative_drift_direction"), "unknown")
    if contradiction >= 0.6:
        return "contradiction_heavy_expectation"
    if exhaustion == "high":
        return "exhaustion_risk_expectation"
    if concentration >= 0.55:
        return "concentrated_fragility_expectation"
    if semantic_dir == "deteriorating":
        return "semantically_deteriorating_expectation"
    if temporal == "insufficient_history" and weak_evidence:
        return "caveat_heavy_expectation"
    if evidence_profiles and not weak_evidence:
        return "evidence_supported_expectation"
    return "mixed_expectation_regime"


def build_e5_expectation_regime_synthesis(e1, e2, e3, e4):
    dominant = classify_e5_expectation_regime(e1 or {}, e2 or {}, e3 or {}, e4 or {})
    supporting = sorted({
        "evidence_supported_expectation" if _as_list((e2 or {}).get("evidence_quality_profiles")) else "insufficient_intelligence",
        "semantically_deteriorating_expectation" if _as_text(((e4 or {}).get("narrative_drift_profile") or {}).get("narrative_drift_direction")) == "deteriorating" else "mixed_expectation_regime",
    })
    band = "high" if dominant in {"evidence_supported_expectation", "contradiction_heavy_expectation"} else "moderate" if dominant != "insufficient_intelligence" else "low"
    refs = sorted(set(_as_list(((e2 or {}).get("support_chain_summary") or {}).get("strong_support_refs")) + _as_list(((e4 or {}).get("semantic_memory_supervisor_summary") or {}).get("well_supported_themes"))))[:8]
    return OrderedDict([
        ("dominant_expectation_regime", dominant),
        ("supporting_regimes", supporting),
        ("regime_confidence_band", band),
        ("regime_interpretation", f"Dominant regime is {dominant} from deterministic E1-E4 precedence rules."),
        ("supporting_signal_refs", refs),
        ("caveats", ["Deterministic synthesis only; no prediction layer."]),
    ])


def build_e5_evidence_contradiction_synthesis(e1, e2, e4):
    support = sorted(_as_list(((e2 or {}).get("support_chain_summary") or {}).get("strong_support_refs")))[:8]
    weak = sorted([_as_text(r.get("finding_id")) for r in _as_list((e2 or {}).get("evidence_quality_profiles")) if _num(r.get("evidence_quality_score")) < 50])[:8]
    contradiction_clusters = _as_list((e4 or {}).get("semantic_contradiction_clusters"))
    unresolved = sorted([_as_text(c.get("contradiction_cluster_id")) for c in contradiction_clusters if _as_text(c.get("persistence_label")) in {"persistent", "recurring"}])
    return OrderedDict([
        ("strongest_supporting_evidence_refs", support),
        ("weakest_supporting_areas", weak),
        ("contradiction_priority_inventory", sorted([_as_text(c.get("contradiction_theme")) for c in contradiction_clusters])),
        ("unresolved_contradiction_clusters", unresolved),
        ("contradiction_significance_summary", f"{len(unresolved)} unresolved contradiction clusters identified deterministically."),
    ])


def build_e5_temporal_semantic_synthesis(e3, e4):
    ss = (e4 or {}).get("semantic_memory_supervisor_summary") or {}
    persistent = sorted(_as_list(ss.get("persisted_themes")))
    emerging = sorted(_as_list(ss.get("emerging_themes")))
    fading = sorted(_as_list(ss.get("fading_themes")))
    return OrderedDict([
        ("persistent_theme_inventory", persistent),
        ("emerging_theme_inventory", emerging),
        ("fading_theme_inventory", fading),
        ("semantic_drift_assessment", _as_text(((e4 or {}).get("narrative_drift_profile") or {}).get("narrative_drift_direction"), "unknown")),
        ("expectation_framing_assessment", _as_text(((e4 or {}).get("expectation_framing_drift") or {}).get("framing_shift_direction"), "unknown")),
        ("temporal_semantic_interpretation", f"Temporal sufficiency={_as_text(((e3 or {}).get('temporal_memory_index') or {}).get('history_sufficiency'),'insufficient_history')}; semantic persistence={len(persistent)} themes."),
    ])


def build_e5_caveat_consolidation(e2, e3, e4):
    caveats = set(_as_list((e2 or {}).get("confidence_caveats")))
    if _as_text(((e3 or {}).get("temporal_memory_index") or {}).get("history_sufficiency")) == "insufficient_history":
        caveats.add("insufficient history")
    if _as_text(((e4 or {}).get("narrative_drift_profile") or {}).get("status")) == "insufficient_history":
        caveats.add("narrow theme breadth")
    ordered = sorted(caveats)
    band = "low" if len(ordered) >= 4 else "moderate" if len(ordered) >= 2 else "high"
    return OrderedDict([
        ("consolidated_caveats", ordered),
        ("confidence_constraints", ordered[:6]),
        ("operational_limitations", ["Read-only deterministic synthesis.", "Bounded by persisted payload coverage."]),
        ("confidence_band", band),
    ])


def certify_e5_expectation_operational_usefulness(e1, e2, e3, e4, caveat):
    factors = []
    if not e1:
        factors.append("missing_e1")
    if _as_text(((e3 or {}).get("temporal_memory_index") or {}).get("history_sufficiency")) == "insufficient_history":
        factors.append("missing_history")
    if len(_as_list((caveat or {}).get("consolidated_caveats"))) >= 5:
        factors.append("caveat_overload")
    score = max(0, 100 - len(factors) * 25)
    status = "OPERATIONALLY_USABLE" if score >= 75 else "DEGRADED_OPERATIONAL_INTELLIGENCE" if score >= 50 else "LIMITED_INTERPRETABILITY" if score >= 25 else "BLOCKED_EXPECTATION_INTELLIGENCE"
    return OrderedDict([
        ("e5_operational_status", status),
        ("operational_readiness_score", score),
        ("operational_readiness_interpretation", f"Operational status={status} from deterministic readiness scoring."),
        ("blocking_or_degrading_factors", factors),
    ])


def build_e5_supervisor_closeout(regime, evidence, temporal_semantic, caveat, cert):
    return OrderedDict([
        ("dominant_expectation_regime", regime.get("dominant_expectation_regime")),
        ("strongest_supporting_evidence", evidence.get("strongest_supporting_evidence_refs", [])[:3]),
        ("key_contradictions", evidence.get("unresolved_contradiction_clusters", [])[:3]),
        ("temporal_semantic_change", temporal_semantic.get("temporal_semantic_interpretation")),
        ("confidence_caveats", caveat.get("consolidated_caveats", [])[:5]),
        ("operational_usefulness", cert.get("e5_operational_status")),
        ("closeout_interpretation", "Deterministic supervisor closeout generated from persisted E1-E4 intelligence layers."),
    ])


def build_e5_composite_synthesis(e1, e2, e3, e4):
    regime = build_e5_expectation_regime_synthesis(e1, e2, e3, e4)
    evidence = build_e5_evidence_contradiction_synthesis(e1, e2, e4)
    temporal_semantic = build_e5_temporal_semantic_synthesis(e3, e4)
    caveat = build_e5_caveat_consolidation(e2, e3, e4)
    cert = certify_e5_expectation_operational_usefulness(e1, e2, e3, e4, caveat)
    closeout = build_e5_supervisor_closeout(regime, evidence, temporal_semantic, caveat, cert)
    return OrderedDict([
        ("e5_composite_summary", OrderedDict([("regime", regime.get("dominant_expectation_regime")), ("status", cert.get("e5_operational_status"))])),
        ("e5_expectation_regime_synthesis", regime),
        ("e5_evidence_contradiction_synthesis", evidence),
        ("e5_temporal_semantic_synthesis", temporal_semantic),
        ("e5_caveat_inventory", caveat),
        ("e5_operational_status", cert),
        ("e5_supervisor_closeout", closeout),
    ])


def build_e5_expectation_intelligence_envelope(*, e1_payload: Mapping[str, Any] | None, e2_payload: Mapping[str, Any] | None, e3_payload: Mapping[str, Any] | None, e4_payload: Mapping[str, Any] | None, d7_context: Mapping[str, Any] | None = None, governance_metadata: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    e1 = deepcopy(e1_payload if isinstance(e1_payload, Mapping) else {})
    e2 = deepcopy(e2_payload if isinstance(e2_payload, Mapping) else {})
    e3 = deepcopy(e3_payload if isinstance(e3_payload, Mapping) else {})
    e4 = deepcopy(e4_payload if isinstance(e4_payload, Mapping) else {})
    synthesis = build_e5_composite_synthesis(e1, e2, e3, e4)
    out = OrderedDict([
        ("e5_version", "e5_expectation_supervisor_closeout_v1"),
        ("e5_expectation_intelligence_envelope", synthesis),
        ("e5_composite_summary", synthesis.get("e5_composite_summary", {})),
        ("e5_caveat_inventory", synthesis.get("e5_caveat_inventory", {})),
        ("e5_operational_status", synthesis.get("e5_operational_status", {})),
        ("e5_supervisor_closeout", synthesis.get("e5_supervisor_closeout", {})),
        ("e5_governance_flags", OrderedDict([("read_only", True), ("no_writes", True), ("no_live_fetching", True), ("no_llm_calls", True), ("input_immutable", True), ("additive_only", True)])),
        ("d7_context_refs", OrderedDict([("finding_count", len(_as_list((d7_context or {}).get("findings")))), ("narrative_count", len(_as_list((d7_context or {}).get("narratives"))))])),
        ("governance_metadata", deepcopy(governance_metadata if isinstance(governance_metadata, Mapping) else {})),
    ])
    out["e5_checksum"] = _stable_checksum(out)
    return out
