from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from .e3_temporal_expectation_memory import normalize_e3_temporal_runs

THEME_KEYWORDS = OrderedDict([
    ("valuation_pressure", ("valuation", "multiple", "overpriced", "stretch", "premium")),
    ("momentum_dependence", ("momentum", "trend", "chasing", "beta")),
    ("breadth_weakness", ("breadth", "narrow", "concentration", "few names")),
    ("semantic_deterioration", ("deterior", "weakening", "erosion", "degrade")),
    ("contradiction_pressure", ("contradiction", "conflict", "divergence", "inconsistent")),
    ("evidence_fragility", ("limited evidence", "thin evidence", "missing evidence", "unsupported")),
    ("expectation_exhaustion", ("exhaustion", "fatigue", "saturation", "overextended")),
    ("concentration_risk", ("concentration", "single driver", "crowded", "top theme")),
    ("confidence_instability", ("confidence", "uncertain", "unstable", "volatility")),
    ("operational_caveat", ("caveat", "limitation", "read-only", "degraded")),
])
PERSISTENCE = ("newly_emerging", "recurring", "persistent", "fading", "resolved", "insufficient_history")
DRIFT_DIRECTIONS = ("reinforcing", "deteriorating", "easing", "mixed", "stable", "unknown")


def _stable_checksum(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _as_text(v: Any) -> str:
    return str(v).strip() if v is not None else ""


def _as_list(v: Any) -> list[Any]:
    return list(v) if isinstance(v, list) else []


def _tokens(*parts: Any) -> set[str]:
    text = " ".join(_as_text(p).lower() for p in parts)
    return {t for t in "".join(ch if ch.isalnum() else " " for ch in text).split() if len(t) >= 4}


def _band(score: int) -> str:
    return "strong" if score >= 75 else "moderate" if score >= 50 else "weak" if score >= 25 else "insufficient"


def classify_e4_theme_category(text: str) -> str:
    tokens = _tokens(text)
    for cat, kws in THEME_KEYWORDS.items():
        if any(any(k in t for t in tokens) or k in _as_text(text).lower() for k in kws):
            return cat
    return "operational_caveat"


def extract_e4_semantic_theme_signals(run_payload: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    run = deepcopy(run_payload if isinstance(run_payload, Mapping) else {})
    rid = _as_text(run.get("run_id")) or "unknown_run"
    findings = _as_list(run.get("findings"))
    narratives = _as_list(run.get("narratives"))
    evidence = _as_list(run.get("evidence_highlights"))
    joined = [json.dumps(run.get("e1") or run.get("e1_payload") or {}, sort_keys=True), json.dumps(run.get("e2") or run.get("e2_payload") or {}, sort_keys=True), json.dumps(run.get("e3") or run.get("e3_payload") or {}, sort_keys=True)]
    signals: list[OrderedDict[str, Any]] = []
    for src, rows in (("findings", findings), ("narratives", narratives), ("evidence", evidence)):
        for idx, row in enumerate(rows):
            txt = json.dumps(row, sort_keys=True) + " " + " ".join(joined)
            cat = classify_e4_theme_category(txt)
            sig = _stable_checksum({"rid": rid, "src": src, "idx": idx, "cat": cat})[:12]
            signals.append(OrderedDict([("signal_id", f"e4_sig_{sig}"), ("run_id", rid), ("source", src), ("source_ref", _as_text(row.get("finding_id") or row.get("evidence_ref") or row.get("narrative_section") or f"{src}_{idx}")), ("theme_category", cat), ("theme_tokens", sorted(_tokens(txt))[:12])]))
    return sorted(signals, key=lambda s: (s["theme_category"], s["source"], s["source_ref"], s["signal_id"]))


def build_e4_theme_inventory(runs: list[Mapping[str, Any]] | None) -> list[OrderedDict[str, Any]]:
    ordered = normalize_e3_temporal_runs(runs)
    inv = []
    for r in ordered:
        inv.extend(extract_e4_semantic_theme_signals(r))
    return inv


def build_e4_semantic_theme_memory(runs: list[Mapping[str, Any]] | None) -> list[OrderedDict[str, Any]]:
    ordered = normalize_e3_temporal_runs(runs)
    if not ordered:
        return []
    by_cat: dict[str, list[Mapping[str, Any]]] = {k: [] for k in THEME_KEYWORDS}
    by_cat.update({"operational_caveat": []})
    for r in ordered:
        for s in extract_e4_semantic_theme_signals(r):
            by_cat.setdefault(s["theme_category"], []).append(s)
    out = []
    run_ids = [r["run_id"] for r in ordered]
    for cat, rows in sorted(by_cat.items()):
        if not rows:
            continue
        seen = sorted({_as_text(x["run_id"]) for x in rows})
        recurrence = len(seen)
        if len(run_ids) < 2:
            label = "insufficient_history"
        elif recurrence == len(run_ids):
            label = "persistent"
        elif recurrence >= 2:
            label = "recurring"
        else:
            label = "newly_emerging" if seen[-1] == run_ids[-1] else "fading"
        out.append(OrderedDict([
            ("theme_id", f"e4_theme_{_stable_checksum({'cat': cat})[:10]}"), ("theme_category", cat), ("first_seen_run", seen[0]), ("last_seen_run", seen[-1]),
            ("recurrence_count", recurrence), ("persistence_label", label),
            ("associated_findings", sorted({r['source_ref'] for r in rows if r['source'] == 'findings'})),
            ("associated_evidence", sorted({r['source_ref'] for r in rows if r['source'] == 'evidence'})),
            ("associated_narratives", sorted({r['source_ref'] for r in rows if r['source'] == 'narratives'})),
            ("support_strength", _band(min(100, recurrence * 25 + (25 if any(r['source'] == 'evidence' for r in rows) else 0)))),
            ("caveats", ["Deterministic keyword-based semantic mapping from persisted text fields."]),
        ]))
    return out


def build_e4_theme_memory_index(runs):
    mem = build_e4_semantic_theme_memory(runs)
    return OrderedDict([("theme_count", len(mem)), ("themes", mem), ("history_sufficiency", "sufficient" if len(normalize_e3_temporal_runs(runs)) >= 2 else "insufficient_history")])


def classify_e4_narrative_drift_direction(emerging: int, fading: int, intensified: int, weakened: int) -> str:
    if emerging == fading == intensified == weakened == 0:
        return "stable"
    if intensified > weakened and emerging >= fading:
        return "deteriorating"
    if weakened > intensified and fading >= emerging:
        return "easing"
    if emerging or fading:
        return "mixed"
    return "unknown"


def build_e4_narrative_drift_profile(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return OrderedDict([("status", "insufficient_history"), ("narrative_drift_direction", "unknown")])
    cur, prev = ordered[-1], ordered[-2]
    ct = {s['theme_category'] for s in extract_e4_semantic_theme_signals(cur) if s['source'] == 'narratives'}
    pt = {s['theme_category'] for s in extract_e4_semantic_theme_signals(prev) if s['source'] == 'narratives'}
    emerging, fading, recurring = sorted(ct-pt), sorted(pt-ct), sorted(ct&pt)
    intensified = sorted([x for x in recurring if "pressure" in x or "deterioration" in x])
    weakened = sorted([x for x in recurring if "caveat" in x])
    d = classify_e4_narrative_drift_direction(len(emerging), len(fading), len(intensified), len(weakened))
    return OrderedDict([("narrative_drift_direction", d), ("recurring_narrative_frames", recurring), ("emerging_narrative_frames", emerging), ("fading_narrative_frames", fading), ("intensified_frames", intensified), ("weakened_frames", weakened), ("narrative_drift_interpretation", f"Narrative drift classified as {d} from deterministic theme-frame comparison.")])


def build_e4_semantic_contradiction_clusters(runs):
    mem = build_e4_semantic_theme_memory(runs)
    out=[]
    for t in mem:
        if "contradiction" in t["theme_category"]:
            out.append(OrderedDict([("contradiction_cluster_id", f"e4_cc_{t['theme_id'][-8:]}"), ("contradiction_theme", t["theme_category"]), ("affected_findings", t["associated_findings"]), ("affected_evidence", t["associated_evidence"]), ("recurrence", t["recurrence_count"]), ("persistence_label", t["persistence_label"]), ("severity_context", "persistent" if t["recurrence_count"] >= 2 else "isolated"), ("interpretation", "Contradiction language appears semantically clustered across runs." )]))
    return out


def build_e4_expectation_framing_drift(runs):
    ordered = normalize_e3_temporal_runs(runs)
    if len(ordered) < 2:
        return OrderedDict([("status", "insufficient_history"), ("framing_shift_direction", "unknown")])
    cur = {m["theme_category"] for m in build_e4_semantic_theme_memory([ordered[-1]])}
    prev = {m["theme_category"] for m in build_e4_semantic_theme_memory([ordered[-2]])}
    new = sorted(cur-prev)
    direction = "deteriorating" if any("pressure" in x or "fragility" in x for x in new) else "stable"
    return OrderedDict([("previous_expectation_frame", sorted(prev)), ("current_expectation_frame", sorted(cur)), ("framing_shift_label", "shifted" if new else "unchanged"), ("framing_shift_direction", direction), ("framing_shift_interpretation", f"Expectation framing is {direction} based on deterministic theme-memory delta."), ("supporting_theme_refs", new[:6])])


def build_e4_theme_evidence_support_profile(runs):
    mem=build_e4_semantic_theme_memory(runs)
    out=[]
    for t in mem:
        score=min(100, t["recurrence_count"]*20 + (40 if t["associated_evidence"] else 0))
        out.append(OrderedDict([("theme_id", t["theme_id"]), ("theme_support_score", score), ("theme_support_band", _band(score)), ("supporting_evidence_refs", t["associated_evidence"][:8]), ("weak_or_missing_support_flags", [] if t["associated_evidence"] else ["missing_evidence_refs"]), ("contradiction_support_refs", t["associated_findings"][:4] if "contradiction" in t["theme_category"] else []), ("confidence_caveats", ["Theme support is deterministic and bounded; no predictive inference."])]))
    return out


def build_e4_semantic_memory_supervisor_summary(runs):
    mem=build_e4_semantic_theme_memory(runs)
    if len(normalize_e3_temporal_runs(runs))<2:
        return OrderedDict([("status","insufficient_history"),("summary","Need at least two persisted runs for semantic memory drift assessment.")])
    persisted=[t["theme_category"] for t in mem if t["persistence_label"] in {"persistent","recurring"}]
    emerged=[t["theme_category"] for t in mem if t["persistence_label"]=="newly_emerging"]
    faded=[t["theme_category"] for t in mem if t["persistence_label"]=="fading"]
    contradiction=build_e4_semantic_contradiction_clusters(runs)
    framing=build_e4_expectation_framing_drift(runs)
    support=build_e4_theme_evidence_support_profile(runs)
    strong=[s["theme_id"] for s in support if s["theme_support_band"] in {"strong","moderate"}]
    weak=[s["theme_id"] for s in support if s["theme_support_band"] in {"weak","insufficient"}]
    return OrderedDict([("persisted_themes", sorted(persisted)),("emerging_themes", sorted(emerged)),("fading_themes", sorted(faded)),("narrative_framing_assessment", build_e4_narrative_drift_profile(runs).get("narrative_drift_direction","unknown")),("contradictions_semantically_clustered", bool(contradiction)),("expectation_framing_shift", framing.get("framing_shift_direction","unknown")),("well_supported_themes", strong),("caveat_heavy_themes", weak),("confidence_caveats", ["Deterministic historical semantic comparison only."])])


def build_e4_semantic_narrative_drift_report(runs):
    out=OrderedDict([("e4_version","e4_semantic_theme_memory_v1"),("forbidden_capability_inventory",OrderedDict([("prediction_engine",False),("trading_recommendation",False),("autonomous_reasoning",False),("live_fetching",False),("writes",False)]))])
    out["theme_inventory"]=build_e4_theme_inventory(runs)
    out["theme_memory_index"]=build_e4_theme_memory_index(runs)
    out["narrative_drift_profile"]=build_e4_narrative_drift_profile(runs)
    out["semantic_contradiction_clusters"]=build_e4_semantic_contradiction_clusters(runs)
    out["expectation_framing_drift"]=build_e4_expectation_framing_drift(runs)
    out["theme_evidence_support_profile"]=build_e4_theme_evidence_support_profile(runs)
    out["semantic_memory_supervisor_summary"]=build_e4_semantic_memory_supervisor_summary(runs)
    out["e4_checksum"]=_stable_checksum(out)
    return out
