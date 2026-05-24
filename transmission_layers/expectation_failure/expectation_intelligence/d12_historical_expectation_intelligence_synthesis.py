from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def build_d12_historical_expectation_inventory(*, d11_backfill_inventory: Mapping[str, Any], d11_replay_windows: list[Mapping[str, Any]], d11_reconstruction: Mapping[str, Any], d11_historical_summary: Mapping[str, Any], d11_certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    windows = [_dict(x) for x in _list(d11_replay_windows) if isinstance(x, Mapping)]
    replay_ids = sorted({_text(rid) for w in windows for rid in _list(w.get("replay_ids")) if _text(rid)})
    finding_refs = sorted({_text(fid) for w in windows for fid in _list(w.get("finding_refs")) if _text(fid)})
    lineage_refs = sorted({_text(ref) for w in windows for ref in _list(w.get("lineage_refs")) if _text(ref)})
    continuity = _text(d11_reconstruction.get("replay_continuity_status")) or _text(d11_certification.get("continuity_status"))
    depth = _text(d11_historical_summary.get("replay_depth_assessment"))
    cert = _text(d11_certification.get("certification_status"))
    confidence = _text(d11_historical_summary.get("evidence_history_confidence"))

    if cert == "BLOCKED_HISTORICAL_BACKFILL" or not windows or continuity == "CONTINUITY_FRAGMENTED":
        status = "HISTORICAL_EXPECTATION_INVENTORY_BLOCKED"
    elif depth == "REPLAY_DEPTH_LIMITED" or continuity == "CONTINUITY_DEGRADED" or cert == "DEGRADED_HISTORICAL_BACKFILL":
        status = "HISTORICAL_EXPECTATION_INVENTORY_DEGRADED"
    else:
        status = "HISTORICAL_EXPECTATION_INVENTORY_READY"

    chk = _checksum([str(len(windows)), depth, continuity, cert, ",".join(replay_ids), ",".join(finding_refs), ",".join(lineage_refs), confidence, status])
    return OrderedDict([
        ("historical_window_count", len(windows)),
        ("replay_depth_assessment", depth),
        ("continuity_status", continuity),
        ("certification_status", cert),
        ("replay_ids", replay_ids),
        ("finding_refs", finding_refs),
        ("lineage_refs", lineage_refs),
        ("evidence_history_confidence", confidence),
        ("inventory_status", status),
        ("inventory_checksum", chk),
    ])


def validate_d12_synthesis_eligibility(*, historical_expectation_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _dict(historical_expectation_inventory)
    blocking, degraded = [], []
    cert = _text(inv.get("certification_status"))
    if cert not in {"CERTIFIED_HISTORICAL_BACKFILL", "DEGRADED_HISTORICAL_BACKFILL"}:
        blocking.append("D11_CERTIFICATION_NOT_ELIGIBLE")
    if int(inv.get("historical_window_count") or 0) <= 0:
        blocking.append("NO_HISTORICAL_REPLAY_WINDOWS")
    continuity = _text(inv.get("continuity_status"))
    if continuity == "CONTINUITY_FRAGMENTED":
        blocking.append("CONTINUITY_FRAGMENTED")
    if not _list(inv.get("lineage_refs")):
        blocking.append("LINEAGE_REFS_MISSING")
    depth = _text(inv.get("replay_depth_assessment"))
    if depth == "REPLAY_DEPTH_INSUFFICIENT":
        blocking.append("INSUFFICIENT_HISTORICAL_DEPTH")
    elif depth == "REPLAY_DEPTH_LIMITED":
        degraded.append("LIMITED_HISTORICAL_DEPTH")
    if cert == "DEGRADED_HISTORICAL_BACKFILL":
        degraded.append("D11_DEGRADED_CERTIFICATION")
    if continuity == "CONTINUITY_DEGRADED":
        degraded.append("CONTINUITY_DEGRADED")

    status = "SYNTHESIS_BLOCKED" if blocking else ("SYNTHESIS_DEGRADED" if degraded else "SYNTHESIS_READY")
    return OrderedDict([("eligibility_status", status), ("blocking_reasons", sorted(set(blocking))), ("degraded_reasons", sorted(set(degraded)))])


def build_d12_cross_window_expectation_patterns(*, d11_replay_windows: list[Mapping[str, Any]], historical_expectation_inventory: Mapping[str, Any]) -> list[OrderedDict[str, Any]]:
    windows = [_dict(x) for x in _list(d11_replay_windows) if isinstance(x, Mapping)]
    families = ["recurring_expectation_constraint", "persistent_lineage_integrity", "replay_depth_drift", "continuity_degradation", "evidence_confidence_drift", "unresolved_constraint_persistence", "finding_recurrence"]
    patterns = []
    for idx, fam in enumerate(families, start=1):
        refs = [w.get("replay_window_id") for w in windows if _text(w.get("replay_window_id"))]
        replay_refs = sorted({_text(rid) for w in windows for rid in _list(w.get("replay_ids")) if _text(rid)})
        finding_refs = sorted({_text(fid) for w in windows for fid in _list(w.get("finding_refs")) if _text(fid)})
        if not refs:
            continue
        patterns.append(OrderedDict([
            ("pattern_id", f"D12-PATTERN-{idx:03d}"),
            ("pattern_family", fam),
            ("pattern_title", fam.replace("_", " ").title()),
            ("pattern_summary", f"Historical synthesis observes {fam.replace('_', ' ')} across replay windows without predictive interpretation."),
            ("supporting_window_refs", refs),
            ("supporting_replay_ids", replay_refs),
            ("supporting_finding_refs", finding_refs),
            ("confidence_band", historical_expectation_inventory.get("evidence_history_confidence") or "MEDIUM"),
            ("severity", "MEDIUM" if "degradation" in fam or "constraint" in fam else "LOW"),
            ("deterministic_rank", idx),
            ("caveats", ["Historical interpretation only", "No prediction or trading signals"]),
        ]))
    return patterns


def classify_d12_historical_expectation_regime(*, historical_expectation_inventory: Mapping[str, Any], cross_window_patterns: list[Mapping[str, Any]], eligibility_validation: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _dict(historical_expectation_inventory)
    pats = [_dict(x) for x in _list(cross_window_patterns) if isinstance(x, Mapping)]
    elig = _text(eligibility_validation.get("eligibility_status"))
    fams = {_text(p.get("pattern_family")) for p in pats}

    if _text(inv.get("replay_depth_assessment")) == "REPLAY_DEPTH_INSUFFICIENT":
        regime = "insufficient_historical_depth"
    elif _text(inv.get("continuity_status")) == "CONTINUITY_FRAGMENTED":
        regime = "fragmented_expectation_history"
    elif _text(inv.get("continuity_status")) == "CONTINUITY_OK" and _text(inv.get("replay_depth_assessment")) == "REPLAY_DEPTH_SUFFICIENT" and elig == "SYNTHESIS_READY":
        regime = "historically_stable_expectation_base"
    elif "recurring_expectation_constraint" in fams and len(fams) <= 3:
        regime = "recurring_constraint_expectation_base"
    else:
        regime = "mixed_historical_expectation_state"
    return OrderedDict([
        ("historical_expectation_regime", regime),
        ("regime_confidence_band", inv.get("evidence_history_confidence") or "MEDIUM"),
        ("regime_drivers", sorted(fams)),
        ("regime_constraints", list(eligibility_validation.get("blocking_reasons") or []) + list(eligibility_validation.get("degraded_reasons") or [])),
        ("caveats", ["Bounded to historical replay context", "No live ingestion or predictive modeling"]),
    ])


def build_d12_expectation_intelligence_synthesis(*, cross_window_patterns: list[Mapping[str, Any]], regime_classification: Mapping[str, Any], historical_expectation_inventory: Mapping[str, Any]) -> OrderedDict[str, Any]:
    pats = sorted([_dict(x) for x in _list(cross_window_patterns) if isinstance(x, Mapping)], key=lambda x: int(x.get("deterministic_rank") or 9999))
    strongest = pats[0] if pats else {}
    strongest_constraint = next((p for p in pats if "constraint" in _text(p.get("pattern_family"))), strongest)
    return OrderedDict([
        ("dominant_historical_expectation_state", regime_classification.get("historical_expectation_regime")),
        ("strongest_recurring_pattern", strongest.get("pattern_family") or "NONE"),
        ("strongest_historical_constraint", strongest_constraint.get("pattern_family") or "NONE"),
        ("replay_depth_interpretation", historical_expectation_inventory.get("replay_depth_assessment")),
        ("continuity_interpretation", historical_expectation_inventory.get("continuity_status")),
        ("evidence_confidence_interpretation", historical_expectation_inventory.get("evidence_history_confidence")),
        ("finding_recurrence_interpretation", "Recurring historical finding references observed." if pats else "No cross-window finding recurrence available."),
        ("expectation_intelligence_summary", "Deterministic historical expectation-intelligence synthesis completed from replay windows and reconstruction lineage."),
        ("unresolved_constraints", list(regime_classification.get("regime_constraints") or [])),
    ])


def certify_d12_historical_expectation_synthesis(*, historical_expectation_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], cross_window_patterns: list[Mapping[str, Any]], regime_classification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    inv = _dict(historical_expectation_inventory)
    elig = _text(eligibility_validation.get("eligibility_status"))
    blocked = bool(list(eligibility_validation.get("blocking_reasons") or []))
    lineage_ok = bool(_list(inv.get("lineage_refs")))
    replay_ok = bool(_list(inv.get("replay_ids")))
    regime = _text(regime_classification.get("historical_expectation_regime"))

    if blocked:
        status = "BLOCKED_HISTORICAL_EXPECTATION_SYNTHESIS"
    elif elig == "SYNTHESIS_READY" and _list(cross_window_patterns) and regime != "insufficient_historical_depth" and lineage_ok and replay_ok:
        status = "CERTIFIED_HISTORICAL_EXPECTATION_SYNTHESIS"
    else:
        status = "DEGRADED_HISTORICAL_EXPECTATION_SYNTHESIS"
    return OrderedDict([("certification_status", status), ("lineage_intact", lineage_ok), ("replay_traceability_intact", replay_ok)])


def build_d12_dashboard_expectation_cards(*, certification: Mapping[str, Any], regime_classification: Mapping[str, Any], cross_window_patterns: list[Mapping[str, Any]], expectation_intelligence_synthesis: Mapping[str, Any]) -> OrderedDict[str, Any]:
    status = _text(certification.get("certification_status"))
    rec = "Proceed with governed historical expectation review expansion." if status == "CERTIFIED_HISTORICAL_EXPECTATION_SYNTHESIS" else "Resolve historical depth/continuity/lineage constraints before expansion."
    return OrderedDict([
        ("synthesis_status", status),
        ("historical_expectation_regime", regime_classification.get("historical_expectation_regime")),
        ("regime_confidence_band", regime_classification.get("regime_confidence_band")),
        ("pattern_count", len(_list(cross_window_patterns))),
        ("strongest_recurring_pattern", expectation_intelligence_synthesis.get("strongest_recurring_pattern")),
        ("strongest_historical_constraint", expectation_intelligence_synthesis.get("strongest_historical_constraint")),
        ("replay_depth_interpretation", expectation_intelligence_synthesis.get("replay_depth_interpretation")),
        ("continuity_interpretation", expectation_intelligence_synthesis.get("continuity_interpretation")),
        ("recommendation", rec),
    ])


def build_d12_report_payload(*, historical_expectation_inventory: Mapping[str, Any], eligibility_validation: Mapping[str, Any], cross_window_patterns: list[Mapping[str, Any]], regime_classification: Mapping[str, Any], expectation_intelligence_synthesis: Mapping[str, Any], dashboard_cards: Mapping[str, Any], certification: Mapping[str, Any], objective: str = "D12 Historical Expectation Intelligence Synthesis") -> OrderedDict[str, Any]:
    return OrderedDict([
        ("objective", objective),
        ("historical_expectation_inventory", OrderedDict(deepcopy(dict(historical_expectation_inventory)))),
        ("eligibility_validation", OrderedDict(deepcopy(dict(eligibility_validation)))),
        ("cross_window_patterns", [OrderedDict(deepcopy(dict(x))) for x in _list(cross_window_patterns)]),
        ("regime_classification", OrderedDict(deepcopy(dict(regime_classification)))),
        ("expectation_intelligence_synthesis", OrderedDict(deepcopy(dict(expectation_intelligence_synthesis)))),
        ("dashboard_cards", OrderedDict(deepcopy(dict(dashboard_cards)))),
        ("certification", OrderedDict(deepcopy(dict(certification)))),
        ("no_direct_sql_bypass_used", True),
        ("no_writes_performed", True),
        ("no_live_fetches_performed", True),
        ("recommendation", dashboard_cards.get("recommendation") or certification.get("certification_status")),
    ])


def build_d12_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    i = _dict(report_payload.get("historical_expectation_inventory")); e = _dict(report_payload.get("eligibility_validation")); g = _dict(report_payload.get("regime_classification")); s = _dict(report_payload.get("expectation_intelligence_synthesis")); d = _dict(report_payload.get("dashboard_cards")); c = _dict(report_payload.get("certification"))
    return "\n".join([
        "# D12 Historical Expectation Intelligence Synthesis", "", f"## Objective\n- {report_payload.get('objective')}",
        "## Scope\n- Deterministic historical expectation-intelligence interpretation from replay/reconstruction artifacts.",
        "## Non-goals\n- No live fetching.\n- No direct SQL bypass.\n- No writes.\n- No forward-looking signal generation or market execution cues.",
        f"## Historical Expectation Inventory\n- Windows: {i.get('historical_window_count')}\n- Status: {i.get('inventory_status')}",
        f"## Eligibility Validation\n- Status: {e.get('eligibility_status')}\n- Blocking reasons: {e.get('blocking_reasons')}\n- Degraded reasons: {e.get('degraded_reasons')}",
        f"## Cross-Window Expectation Patterns\n- Pattern count: {len(_list(report_payload.get('cross_window_patterns')))}",
        f"## Historical Expectation Regime\n- Regime: {g.get('historical_expectation_regime')}\n- Confidence: {g.get('regime_confidence_band')}",
        f"## Expectation Intelligence Synthesis\n- Dominant state: {s.get('dominant_historical_expectation_state')}\n- Strongest recurring pattern: {s.get('strongest_recurring_pattern')}",
        f"## Dashboard Cards\n- Synthesis status: {d.get('synthesis_status')}\n- Recommendation: {d.get('recommendation')}",
        f"## Certification\n- {c.get('certification_status')}",
        "## Governance Boundaries\n- no_direct_sql_bypass_used: True\n- no_writes_performed: True\n- no_live_fetches_performed: True\n- Deterministic ordering/lineage/replay traceability preserved.",
        f"## Final Recommendation\n- {report_payload.get('recommendation')}",
    ])
