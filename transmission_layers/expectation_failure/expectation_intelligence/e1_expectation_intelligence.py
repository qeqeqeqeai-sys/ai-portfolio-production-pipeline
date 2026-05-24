from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

PRESSURE_PRECEDENCE = (
    "exhaustion_risk",
    "late_cycle_expectation",
    "structurally_fragile_expectation",
    "concentrated_expectation",
    "momentum_supported_expectation",
    "valuation_supported_expectation",
    "semantic_supported_expectation",
    "diffuse_expectation",
)


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _normalize(findings: list[Mapping[str, Any]] | None, narratives: list[Mapping[str, Any]] | None, evidence: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("findings", deepcopy(_as_list(findings))),
        ("narratives", deepcopy(_as_list(narratives))),
        ("evidence", deepcopy(_as_list(evidence))),
    ])


def build_e1_expectation_pressure_profile(findings: list[Mapping[str, Any]] | None, narratives: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    base = _normalize(findings, narratives, None)
    severe = sum(1 for f in base["findings"] if str(f.get("finding_severity", f.get("severity", ""))).upper() in {"SEVERE", "HIGH"})
    categories = sorted({str(f.get("finding_type") or "unspecified") for f in base["findings"]})
    concentration = _as_float(severe / max(len(base["findings"]), 1))
    momentum = sum(1 for n in base["narratives"] if "pressure" in str(n).lower() or "elevat" in str(n).lower())
    return OrderedDict([
        ("finding_count", len(base["findings"])),
        ("high_severity_count", severe),
        ("severity_concentration_ratio", round(concentration, 4)),
        ("theme_breadth", len(categories)),
        ("themes", categories),
        ("momentum_signal_count", momentum),
    ])


def classify_e1_expectation_pressure_state(profile: Mapping[str, Any]) -> str:
    ratio = _as_float(profile.get("severity_concentration_ratio"))
    breadth = int(_as_float(profile.get("theme_breadth"), 0))
    momentum = int(_as_float(profile.get("momentum_signal_count"), 0))
    if ratio >= 0.7:
        return "exhaustion_risk"
    if ratio >= 0.5 and breadth <= 2:
        return "late_cycle_expectation"
    if ratio >= 0.5:
        return "structurally_fragile_expectation"
    if breadth <= 2 and ratio >= 0.3:
        return "concentrated_expectation"
    if momentum >= 2:
        return "momentum_supported_expectation"
    if breadth >= 5:
        return "diffuse_expectation"
    return "semantic_supported_expectation"


def build_e1_expectation_pressure_summary(profile: Mapping[str, Any]) -> OrderedDict[str, Any]:
    state = classify_e1_expectation_pressure_state(profile)
    return OrderedDict([
        ("expectation_pressure_state", state),
        ("pressure_profile", OrderedDict(sorted(dict(profile).items()))),
        ("precedence_order", list(PRESSURE_PRECEDENCE)),
    ])


def build_e1_contradiction_profile(findings: list[Mapping[str, Any]] | None, narratives: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    base = _normalize(findings, narratives, None)
    texts = [json.dumps(x, ensure_ascii=True).lower() for x in (base["findings"] + base["narratives"])]
    contradictions = [t for t in texts if "contradict" in t or "diverg" in t or "conflict" in t]
    recurrence = len(contradictions)
    spread = len({i for i, t in enumerate(texts) if t in contradictions})
    severity = "high" if recurrence >= 4 else "moderate" if recurrence >= 2 else "low"
    score = min(1.0, round((recurrence * 0.2) + (0.1 if spread > 1 else 0.0), 4))
    regime = "persistent_contradiction" if score >= 0.6 else "localized_contradiction" if score >= 0.3 else "contained_contradiction"
    return OrderedDict([
        ("contradiction_recurrence", recurrence),
        ("contradiction_spread", spread),
        ("contradiction_severity", severity),
        ("contradiction_persistence_score", score),
        ("contradiction_regime_label", regime),
    ])


def build_e1_contradiction_summary(profile: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("contradiction_profile", OrderedDict(sorted(dict(profile).items()))),
        ("contradiction_interpretation", f"Contradiction regime is {profile.get('contradiction_regime_label', 'unknown')} with persistence score {profile.get('contradiction_persistence_score', 0.0)}."),
    ])


def build_e1_fragility_concentration_profile(findings: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    rows = _as_list(findings)
    by_theme: dict[str, int] = {}
    for row in rows:
        key = str(row.get("finding_type") or "unspecified")
        by_theme[key] = by_theme.get(key, 0) + 1
    ranked = sorted(by_theme.items(), key=lambda x: (-x[1], x[0]))
    top_share = (ranked[0][1] / max(len(rows), 1)) if ranked else 0.0
    regime = "systemic_fragility_concentration" if top_share >= 0.6 else "clustered_fragility" if top_share >= 0.35 else "isolated_fragility"
    hotspots = [OrderedDict([("theme", k), ("count", v)]) for k, v in ranked[:5]]
    return OrderedDict([
        ("theme_count", len(by_theme)),
        ("top_theme_share", round(top_share, 4)),
        ("concentration_regime", regime),
        ("concentration_hotspots", hotspots),
    ])


def build_e1_fragility_concentration_summary(profile: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("fragility_concentration_profile", OrderedDict(sorted((k, v) for k, v in dict(profile).items() if k != "concentration_hotspots"))),
        ("concentration_hotspots", list(profile.get("concentration_hotspots", []))),
        ("concentration_interpretation", f"Fragility concentration is classified as {profile.get('concentration_regime', 'unknown')} based on deterministic theme concentration."),
    ])


def build_e1_semantic_pressure_profile(narratives: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    rows = _as_list(narratives)
    text = " ".join(json.dumps(r, ensure_ascii=True).lower() for r in rows)
    optimism = text.count("supportive") + text.count("optim")
    deterioration = text.count("deterior") + text.count("degrad")
    divergence = text.count("diverg") + text.count("contradict")
    coherence = max(0.0, 1.0 - min(1.0, divergence / max(len(rows), 1)))
    return OrderedDict([
        ("optimism_persistence", optimism),
        ("narrative_deterioration", deterioration),
        ("semantic_divergence", divergence),
        ("thematic_coherence", round(coherence, 4)),
    ])


def build_e1_semantic_pressure_summary(profile: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("semantic_pressure_profile", OrderedDict(sorted(dict(profile).items()))),
        ("semantic_pressure_interpretation", "Semantic pressure reflects persisted narrative tone concentration and divergence, without forecast or recommendation semantics."),
    ])


def classify_e1_exhaustion_state(profile: Mapping[str, Any]) -> str:
    score = _as_float(profile.get("exhaustion_score"))
    if score >= 0.75:
        return "high"
    if score >= 0.45:
        return "moderate"
    return "low"


def build_e1_expectation_exhaustion_profile(pressure: Mapping[str, Any], contradiction: Mapping[str, Any], semantic: Mapping[str, Any], concentration: Mapping[str, Any]) -> OrderedDict[str, Any]:
    drivers: list[str] = []
    if _as_float(pressure.get("severity_concentration_ratio")) >= 0.5:
        drivers.append("rising_fragility_concentration")
    if _as_float(contradiction.get("contradiction_persistence_score")) >= 0.5:
        drivers.append("contradiction_persistence")
    if _as_float(semantic.get("narrative_deterioration")) > _as_float(semantic.get("optimism_persistence")):
        drivers.append("semantic_deterioration")
    if _as_float(concentration.get("top_theme_share")) >= 0.5:
        drivers.append("narrowing_participation")
    score = min(1.0, round(0.2 * len(drivers) + 0.2 * _as_float(contradiction.get("contradiction_persistence_score")), 4))
    risk = classify_e1_exhaustion_state({"exhaustion_score": score})
    confidence = "high" if len(drivers) >= 3 else "medium" if len(drivers) >= 2 else "low"
    return OrderedDict([
        ("exhaustion_risk_level", risk),
        ("exhaustion_score", score),
        ("exhaustion_drivers", sorted(drivers)),
        ("exhaustion_confidence", confidence),
        ("exhaustion_interpretation", f"Exhaustion state is {risk} from current persisted structural drivers; interpretation is descriptive and non-predictive."),
    ])


def build_e1_supervisor_interpretation(e1_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("dominant_expectation_regime", _as_text(_nested(e1_payload, "expectation_pressure_summary", "expectation_pressure_state"), "semantic_supported_expectation")),
        ("contradiction_significance", _as_text(_nested(e1_payload, "contradiction_summary", "contradiction_interpretation"), "No explicit contradiction persistence signals detected.")),
        ("exhaustion_interpretation", _as_text(_nested(e1_payload, "exhaustion_profile", "exhaustion_interpretation"), "Exhaustion interpretation unavailable due to partial payload.")),
        ("operational_caveats", ["Deterministic and read-only interpretation from persisted payloads.", "No forecasting, no trading recommendations, no autonomous execution."]),
    ])


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def _as_text(v: Any, default: str = "") -> str:
    t = str(v).strip() if v is not None else ""
    return t or default


def build_e1_strategist_summary(e1_payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("dominant_expectation_regime", _nested(e1_payload, "expectation_pressure_summary", "expectation_pressure_state") or "unknown"),
        ("primary_fragility_drivers", list(_nested(e1_payload, "exhaustion_profile", "exhaustion_drivers") or [])),
        ("expectation_concentration_risks", _nested(e1_payload, "fragility_concentration_summary", "concentration_interpretation") or "unknown"),
        ("contradiction_significance", _nested(e1_payload, "contradiction_summary", "contradiction_interpretation") or "unknown"),
        ("confidence_caveats", "Confidence is bounded by persisted evidence completeness and deterministic template logic."),
    ])


def build_e1_expectation_intelligence_payload(findings: list[Mapping[str, Any]] | None, narratives: list[Mapping[str, Any]] | None, evidence: list[Mapping[str, Any]] | None = None) -> OrderedDict[str, Any]:
    pressure = build_e1_expectation_pressure_profile(findings, narratives)
    contradiction = build_e1_contradiction_profile(findings, narratives)
    concentration = build_e1_fragility_concentration_profile(findings)
    semantic = build_e1_semantic_pressure_profile(narratives)
    exhaustion = build_e1_expectation_exhaustion_profile(pressure, contradiction, semantic, concentration)
    payload = OrderedDict([
        ("e1_version", "e1_expectation_intelligence_v1"),
        ("expectation_pressure_summary", build_e1_expectation_pressure_summary(pressure)),
        ("exhaustion_profile", exhaustion),
        ("contradiction_summary", build_e1_contradiction_summary(contradiction)),
        ("fragility_concentration_summary", build_e1_fragility_concentration_summary(concentration)),
        ("semantic_pressure_summary", build_e1_semantic_pressure_summary(semantic)),
    ])
    payload["supervisor_interpretation"] = build_e1_supervisor_interpretation(payload)
    payload["strategist_summary"] = build_e1_strategist_summary(payload)
    payload["forbidden_capability_inventory"] = OrderedDict([
        ("prediction_engine", False), ("trading_recommendation", False), ("autonomous_reasoning", False), ("live_fetching", False),
    ])
    payload["e1_checksum"] = _stable_checksum(payload)
    return payload
