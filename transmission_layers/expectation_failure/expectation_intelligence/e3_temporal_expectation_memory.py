from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

DIRECTION_CATEGORIES = ("rising", "easing", "stable", "mixed", "unknown")
PERSISTENCE_CATEGORIES = ("newly_emerging", "persistent", "fading", "resolved", "insufficient_history")


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_text(v: Any, default: str = "") -> str:
    t = str(v).strip() if v is not None else ""
    return t or default


def _as_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _nested(payload: Mapping[str, Any], *keys: str) -> Any:
    cur: Any = payload
    for key in keys:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(key)
    return cur


def _tokens(*parts: Any) -> set[str]:
    text = " ".join(_as_text(p).lower() for p in parts)
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in text).split() if len(t) >= 4}


def normalize_e3_temporal_runs(runs: list[Mapping[str, Any]] | None) -> list[OrderedDict[str, Any]]:
    rows = deepcopy(_as_list(runs))
    normalized: list[OrderedDict[str, Any]] = []
    for idx, row in enumerate(rows):
        if not isinstance(row, Mapping):
            continue
        ts = _as_text(row.get("run_timestamp") or row.get("run_date"))
        rid = _as_text(row.get("run_id"), f"run_{idx+1:03d}")
        normalized.append(OrderedDict([
            ("run_id", rid),
            ("run_timestamp", ts or None),
            ("run_sort_timestamp", ts if ts else "9999-12-31T23:59:59Z"),
            ("source_index", idx),
            ("e1", deepcopy(row.get("e1_payload") if isinstance(row.get("e1_payload"), Mapping) else row.get("e1_expectation_intelligence") if isinstance(row.get("e1_expectation_intelligence"), Mapping) else {})),
            ("e2", deepcopy(row.get("e2_payload") if isinstance(row.get("e2_payload"), Mapping) else row.get("e2_evidence_interpretation") if isinstance(row.get("e2_evidence_interpretation"), Mapping) else {})),
            ("findings", deepcopy(_as_list(row.get("findings")))),
            ("narratives", deepcopy(_as_list(row.get("narratives")))),
            ("evidence_highlights", deepcopy(_as_list(row.get("evidence_highlights")))),
            ("integrity", deepcopy(row.get("integrity") if isinstance(row.get("integrity"), Mapping) else {})),
            ("replay_metadata", deepcopy(row.get("replay_metadata") if isinstance(row.get("replay_metadata"), Mapping) else {})),
        ]))
    return sorted(normalized, key=lambda r: (r["run_sort_timestamp"], _as_text(r["run_id"]), int(r["source_index"])))


def build_e3_temporal_memory_index(runs: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    ordered = normalize_e3_temporal_runs(runs)
    refs = [OrderedDict([("run_id", r["run_id"]), ("run_timestamp", r["run_timestamp"]), ("source_index", r["source_index"])]) for r in ordered]
    return OrderedDict([
        ("run_count", len(ordered)),
        ("ordered_run_refs", refs),
        ("history_sufficiency", "sufficient" if len(ordered) >= 2 else "insufficient_history"),
        ("latest_run_ref", refs[-1] if refs else {}),
        ("previous_run_ref", refs[-2] if len(refs) >= 2 else {}),
    ])


def classify_e3_pressure_direction(delta: float) -> str:
    if delta >= 0.08:
        return "rising"
    if delta <= -0.08:
        return "easing"
    return "stable"


def _persistence(curr: float, prev: float, eps: float = 0.02) -> str:
    if prev <= eps and curr > eps:
        return "newly_emerging"
    if curr <= eps and prev > eps:
        return "resolved"
    if curr > eps and prev > eps:
        return "persistent"
    if curr < prev:
        return "fading"
    return "insufficient_history"


def _degraded(msg: str) -> OrderedDict[str, Any]:
    return OrderedDict([("status", "insufficient_history"), ("interpretation", msg)])


def build_e3_expectation_pressure_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return _degraded("Need at least two persisted runs for expectation pressure drift.")
    cur, prev = ordered[-1], ordered[-2]
    cur_profile = _nested(cur, "e1", "expectation_pressure_summary", "pressure_profile") or {}
    prev_profile = _nested(prev, "e1", "expectation_pressure_summary", "pressure_profile") or {}
    c = _as_float(cur_profile.get("severity_concentration_ratio"))
    p = _as_float(prev_profile.get("severity_concentration_ratio"))
    delta = round(c - p, 4)
    direction = classify_e3_pressure_direction(delta)
    return OrderedDict([
        ("current_pressure_state", _nested(cur, "e1", "expectation_pressure_summary", "expectation_pressure_state") or "unknown"),
        ("previous_pressure_state", _nested(prev, "e1", "expectation_pressure_summary", "expectation_pressure_state") or "unknown"),
        ("pressure_direction", direction),
        ("pressure_delta_score", delta),
        ("pressure_persistence_label", _persistence(c, p)),
        ("pressure_drift_interpretation", f"Expectation pressure is {direction} versus prior persisted run (delta={delta})."),
        ("supporting_run_refs", [cur["run_id"], prev["run_id"]]),
    ])


def build_e3_contradiction_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return _degraded("Need at least two persisted runs for contradiction drift.")
    cur, prev = ordered[-1], ordered[-2]
    cs = _as_float(_nested(cur, "e1", "contradiction_summary", "contradiction_profile", "contradiction_persistence_score"))
    ps = _as_float(_nested(prev, "e1", "contradiction_summary", "contradiction_profile", "contradiction_persistence_score"))
    ct = _tokens(json.dumps(_nested(cur, "e1", "contradiction_summary") or {}), json.dumps(cur.get("findings", [])))
    pt = _tokens(json.dumps(_nested(prev, "e1", "contradiction_summary") or {}), json.dumps(prev.get("findings", [])))
    direction = classify_e3_pressure_direction(round(cs - ps, 4))
    return OrderedDict([
        ("current_contradiction_state", _nested(cur, "e1", "contradiction_summary", "contradiction_profile", "contradiction_regime_label") or "unknown"),
        ("previous_contradiction_state", _nested(prev, "e1", "contradiction_summary", "contradiction_profile", "contradiction_regime_label") or "unknown"),
        ("contradiction_direction", direction),
        ("contradiction_persistence_label", _persistence(cs, ps)),
        ("recurring_contradiction_themes", sorted(ct & pt)[:8]),
        ("resolved_or_fading_contradictions", sorted(pt - ct)[:8]),
        ("new_or_intensifying_contradictions", sorted(ct - pt)[:8]),
        ("contradiction_drift_interpretation", f"Contradictions are {direction} with persistence label {_persistence(cs, ps)}."),
    ])


def _quality_score(run):
    rows = _as_list(_nested(run, "e2", "evidence_quality_profiles"))
    return round(sum(_as_float(r.get("evidence_quality_score")) for r in rows) / max(len(rows), 1), 4)


def build_e3_evidence_support_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return _degraded("Need at least two persisted runs for evidence support drift.")
    cur, prev = ordered[-1], ordered[-2]
    c, p = _quality_score(cur), _quality_score(prev)
    cd = [d for r in _as_list(_nested(cur, "e2", "evidence_quality_profiles")) for d in _as_list(r.get("evidence_quality_drivers"))]
    pd = [d for r in _as_list(_nested(prev, "e2", "evidence_quality_profiles")) for d in _as_list(r.get("evidence_quality_drivers"))]
    direction = classify_e3_pressure_direction(round(c - p, 4))
    return OrderedDict([
        ("current_evidence_quality_band", "strong" if c >= 75 else "moderate" if c >= 50 else "weak" if c >= 25 else "insufficient"),
        ("previous_evidence_quality_band", "strong" if p >= 75 else "moderate" if p >= 50 else "weak" if p >= 25 else "insufficient"),
        ("evidence_support_direction", direction),
        ("support_strength_delta", round(c - p, 4)),
        ("weakening_support_drivers", sorted(set(pd) - set(cd))[:8]),
        ("strengthening_support_drivers", sorted(set(cd) - set(pd))[:8]),
        ("evidence_drift_interpretation", f"Evidence support is {direction} with average quality delta {round(c-p,4)}."),
    ])


def build_e3_fragility_concentration_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return _degraded("Need at least two persisted runs for fragility concentration drift.")
    cur, prev = ordered[-1], ordered[-2]
    c = _as_float(_nested(cur, "e1", "fragility_concentration_summary", "fragility_concentration_profile", "top_theme_share"))
    p = _as_float(_nested(prev, "e1", "fragility_concentration_summary", "fragility_concentration_profile", "top_theme_share"))
    ch = {str(x.get("theme")) for x in _as_list(_nested(cur, "e1", "fragility_concentration_summary", "concentration_hotspots"))}
    ph = {str(x.get("theme")) for x in _as_list(_nested(prev, "e1", "fragility_concentration_summary", "concentration_hotspots"))}
    direction = "broadening" if len(ch) > len(ph) else "narrowing" if len(ch) < len(ph) else "stable"
    return OrderedDict([
        ("current_concentration_regime", _nested(cur, "e1", "fragility_concentration_summary", "fragility_concentration_profile", "concentration_regime") or "unknown"),
        ("previous_concentration_regime", _nested(prev, "e1", "fragility_concentration_summary", "fragility_concentration_profile", "concentration_regime") or "unknown"),
        ("concentration_direction", direction),
        ("concentration_delta", round(c - p, 4)),
        ("broadening_themes", sorted(ch - ph)),
        ("narrowing_themes", sorted(ph - ch)),
        ("persistent_hotspots", sorted(ch & ph)),
        ("new_hotspots", sorted(ch - ph)),
        ("faded_hotspots", sorted(ph - ch)),
        ("concentration_drift_interpretation", f"Fragility concentration is {direction} with top-theme-share delta {round(c-p,4)}."),
    ])


def build_e3_semantic_pressure_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return _degraded("Need at least two persisted runs for semantic pressure drift.")
    cur, prev = ordered[-1], ordered[-2]
    ct = _tokens(json.dumps(_nested(cur, "e1", "semantic_pressure_summary", "semantic_pressure_profile") or {}), json.dumps(cur.get("narratives", [])))
    pt = _tokens(json.dumps(_nested(prev, "e1", "semantic_pressure_summary", "semantic_pressure_profile") or {}), json.dumps(prev.get("narratives", [])))
    direction = "mixed" if (ct - pt) and (pt - ct) else "rising" if (ct - pt) else "stable"
    return OrderedDict([
        ("semantic_pressure_direction", direction),
        ("recurring_semantic_themes", sorted(ct & pt)[:10]),
        ("emerging_semantic_themes", sorted(ct - pt)[:10]),
        ("fading_semantic_themes", sorted(pt - ct)[:10]),
        ("semantic_drift_interpretation", f"Semantic pressure is {direction} from deterministic cross-run narrative token comparison."),
        ("caveats", ["Token-based semantic comparison is deterministic but coarse-grained."]),
    ])


def build_e3_exhaustion_risk_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return _degraded("Need at least two persisted runs for exhaustion drift.")
    cur, prev = ordered[-1], ordered[-2]
    lv = {"low": 0.2, "moderate": 0.6, "high": 1.0}
    cl = _as_text(_nested(cur, "e1", "exhaustion_profile", "exhaustion_risk_level"), "unknown")
    pl = _as_text(_nested(prev, "e1", "exhaustion_profile", "exhaustion_risk_level"), "unknown")
    c = lv.get(cl, _as_float(_nested(cur, "e1", "exhaustion_profile", "exhaustion_score")))
    p = lv.get(pl, _as_float(_nested(prev, "e1", "exhaustion_profile", "exhaustion_score")))
    cd = set(_as_list(_nested(cur, "e1", "exhaustion_profile", "exhaustion_drivers")))
    pd = set(_as_list(_nested(prev, "e1", "exhaustion_profile", "exhaustion_drivers")))
    direction = classify_e3_pressure_direction(round(c - p, 4))
    return OrderedDict([
        ("current_exhaustion_level", cl),
        ("previous_exhaustion_level", pl),
        ("exhaustion_direction", direction),
        ("exhaustion_persistence_label", _persistence(c, p)),
        ("exhaustion_driver_changes", OrderedDict([("new_drivers", sorted(cd - pd)), ("faded_drivers", sorted(pd - cd)), ("persistent_drivers", sorted(cd & pd))])),
        ("exhaustion_drift_interpretation", f"Exhaustion risk is {direction} versus prior persisted run."),
    ])


def build_e3_temporal_supervisor_summary(drifts: Mapping[str, Any]) -> OrderedDict[str, Any]:
    if _as_text(drifts.get("history_sufficiency")) == "insufficient_history":
        return OrderedDict([("status", "insufficient_history"), ("summary", "Temporal comparison requires at least two persisted runs."), ("confidence_caveats", ["insufficient_history"])])
    return OrderedDict([
        ("what_changed_since_prior_run", [f"Expectation pressure: {((drifts.get('expectation_pressure_drift') or {}).get('pressure_direction', 'unknown'))}", f"Evidence support: {((drifts.get('evidence_support_drift') or {}).get('evidence_support_direction', 'unknown'))}"]),
        ("what_persisted", [f"Contradiction persistence: {((drifts.get('contradiction_drift') or {}).get('contradiction_persistence_label', 'unknown'))}"]),
        ("what_intensified", [f"Exhaustion: {((drifts.get('exhaustion_risk_drift') or {}).get('exhaustion_direction', 'unknown'))}"]),
        ("what_faded", [", ".join(((drifts.get("fragility_concentration_drift") or {}).get("faded_hotspots") or [])) or "none"]),
        ("evidence_support_assessment", ((drifts.get("evidence_support_drift") or {}).get("evidence_drift_interpretation", "unknown"))),
        ("contradiction_assessment", ((drifts.get("contradiction_drift") or {}).get("contradiction_drift_interpretation", "unknown"))),
        ("fragility_scope_assessment", ((drifts.get("fragility_concentration_drift") or {}).get("concentration_drift_interpretation", "unknown"))),
        ("confidence_caveats", ["Deterministic historical comparison only; no prediction layer."]),
    ])


def build_e3_temporal_drift_report(runs: list[Mapping[str, Any]] | None) -> OrderedDict[str, Any]:
    idx = build_e3_temporal_memory_index(runs)
    out = OrderedDict([("e3_version", "e3_temporal_expectation_memory_v1"), ("temporal_memory_index", idx), ("history_sufficiency", idx["history_sufficiency"]), ("forbidden_capability_inventory", OrderedDict([("prediction_engine", False), ("trading_recommendation", False), ("autonomous_reasoning", False), ("live_fetching", False), ("writes", False)]))])
    out["expectation_pressure_drift"] = build_e3_expectation_pressure_drift(runs)
    out["contradiction_drift"] = build_e3_contradiction_drift(runs)
    out["evidence_support_drift"] = build_e3_evidence_support_drift(runs)
    out["fragility_concentration_drift"] = build_e3_fragility_concentration_drift(runs)
    out["semantic_pressure_drift"] = build_e3_semantic_pressure_drift(runs)
    out["exhaustion_risk_drift"] = build_e3_exhaustion_risk_drift(runs)
    out["temporal_supervisor_summary"] = build_e3_temporal_supervisor_summary(out)
    out["e3_checksum"] = _stable_checksum(out)
    return out
