from __future__ import annotations

from collections import OrderedDict
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping


DELTA_STABLE = "EXPECTATION_DELTA_STABLE"
DELTA_CHANGED = "EXPECTATION_DELTA_CHANGED"
DELTA_INSUFFICIENT = "EXPECTATION_DELTA_INSUFFICIENT_HISTORY"

EVOLUTION_STABLE = "REGIME_STABLE"
EVOLUTION_IMPROVING = "REGIME_IMPROVING"
EVOLUTION_DEGRADING = "REGIME_DEGRADING"
EVOLUTION_FRAGMENTING = "REGIME_FRAGMENTING"
EVOLUTION_RECOVERING = "REGIME_RECOVERING"
EVOLUTION_INSUFFICIENT = "REGIME_INSUFFICIENT_HISTORY"
EVOLUTION_MIXED = "REGIME_MIXED"


def _text(value: Any) -> str:
    return str(value).strip() if value is not None else ""


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _dict(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _checksum(parts: list[str]) -> str:
    return sha256("|".join(parts).encode("utf-8")).hexdigest()[:24].upper()


def build_d13_expectation_synthesis_snapshot(*, d12_report_payload: Mapping[str, Any] | None = None, d12_synthesis: Mapping[str, Any] | None = None, cycle_id: str | None = None, snapshot_timestamp: str | None = None) -> OrderedDict[str, Any]:
    payload = _dict(d12_report_payload)
    synth = _dict(d12_synthesis) if d12_synthesis else _dict(payload.get("expectation_intelligence_synthesis"))
    regime = _dict(payload.get("regime_classification"))
    inventory = _dict(payload.get("historical_expectation_inventory"))
    patterns = [_dict(x) for x in _list(payload.get("cross_window_patterns")) if isinstance(x, Mapping)]

    families = sorted({_text(p.get("pattern_family")) for p in patterns if _text(p.get("pattern_family"))})
    unresolved = sorted({_text(x) for x in _list(synth.get("unresolved_constraints")) if _text(x)})
    replay_ids = sorted({_text(x) for x in _list(inventory.get("replay_ids")) if _text(x)})
    lineage_refs = sorted({_text(x) for x in _list(inventory.get("lineage_refs")) if _text(x)})
    cycle = _text(cycle_id) or _text(payload.get("cycle_id")) or "D13-CYCLE-UNSPECIFIED"
    ts = _text(snapshot_timestamp) or _text(payload.get("snapshot_timestamp")) or "SNAPSHOT_TS_UNSPECIFIED"

    snapshot_id = f"D13-SNAPSHOT-{_checksum([cycle, ts, _text(regime.get('historical_expectation_regime'))])[:12]}"
    chk = _checksum([snapshot_id, cycle, _text(regime.get("historical_expectation_regime")), _text(regime.get("regime_confidence_band")), str(len(families)), ",".join(families), _text(synth.get("strongest_recurring_pattern")), _text(synth.get("strongest_historical_constraint")), _text(synth.get("replay_depth_interpretation")), _text(synth.get("continuity_interpretation")), ",".join(unresolved), ",".join(replay_ids), ",".join(lineage_refs)])

    return OrderedDict([
        ("snapshot_id", snapshot_id),
        ("cycle_id", cycle),
        ("historical_expectation_regime", _text(regime.get("historical_expectation_regime"))),
        ("regime_confidence_band", _text(regime.get("regime_confidence_band")) or "MEDIUM"),
        ("pattern_count", len(families)),
        ("pattern_families", families),
        ("strongest_recurring_pattern", _text(synth.get("strongest_recurring_pattern")) or "NONE"),
        ("strongest_historical_constraint", _text(synth.get("strongest_historical_constraint")) or "NONE"),
        ("replay_depth_interpretation", _text(synth.get("replay_depth_interpretation"))),
        ("continuity_interpretation", _text(synth.get("continuity_interpretation"))),
        ("unresolved_constraints", unresolved),
        ("replay_ids", replay_ids),
        ("lineage_refs", lineage_refs),
        ("snapshot_checksum", chk),
    ])


def compare_d13_expectation_snapshots(*, current_snapshot: Mapping[str, Any], previous_snapshots: list[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    current = _dict(current_snapshot)
    previous = [_dict(x) for x in _list(previous_snapshots) if isinstance(x, Mapping)]
    if not previous:
        return OrderedDict([("regime_changed", False), ("previous_regime", ""), ("current_regime", _text(current.get("historical_expectation_regime"))), ("regime_transition", "INSUFFICIENT_HISTORY"), ("confidence_band_change", "UNCHANGED"), ("pattern_count_delta", 0), ("new_pattern_families", []), ("recurring_pattern_families", []), ("resolved_pattern_families", []), ("constraint_persistence", "UNKNOWN"), ("continuity_change", "UNCHANGED"), ("replay_depth_change", "UNCHANGED"), ("delta_status", DELTA_INSUFFICIENT)])

    prev = previous[-1]
    cur_f = set(_list(current.get("pattern_families"))); prev_f = set(_list(prev.get("pattern_families")));
    cur_c = set(_list(current.get("unresolved_constraints"))); prev_c = set(_list(prev.get("unresolved_constraints")))
    regime_changed = _text(prev.get("historical_expectation_regime")) != _text(current.get("historical_expectation_regime"))
    confidence_changed = "CHANGED" if _text(prev.get("regime_confidence_band")) != _text(current.get("regime_confidence_band")) else "UNCHANGED"
    continuity_change = "CHANGED" if _text(prev.get("continuity_interpretation")) != _text(current.get("continuity_interpretation")) else "UNCHANGED"
    depth_change = "CHANGED" if _text(prev.get("replay_depth_interpretation")) != _text(current.get("replay_depth_interpretation")) else "UNCHANGED"
    transition = f"{_text(prev.get('historical_expectation_regime'))} -> {_text(current.get('historical_expectation_regime'))}" if regime_changed else "NO_REGIME_CHANGE"
    delta = int(current.get("pattern_count") or 0) - int(prev.get("pattern_count") or 0)
    new_f, rec_f, res_f = sorted(cur_f - prev_f), sorted(cur_f & prev_f), sorted(prev_f - cur_f)
    persistent = sorted(cur_c & prev_c)
    constraint_persistence = "PERSISTENT" if persistent else ("RESOLVING" if prev_c and not cur_c else "SHIFTING")
    status = DELTA_CHANGED if regime_changed or confidence_changed == "CHANGED" or delta != 0 or new_f or res_f or continuity_change == "CHANGED" or depth_change == "CHANGED" else DELTA_STABLE
    return OrderedDict([("regime_changed", regime_changed), ("previous_regime", _text(prev.get("historical_expectation_regime"))), ("current_regime", _text(current.get("historical_expectation_regime"))), ("regime_transition", transition), ("confidence_band_change", confidence_changed), ("pattern_count_delta", delta), ("new_pattern_families", new_f), ("recurring_pattern_families", rec_f), ("resolved_pattern_families", res_f), ("constraint_persistence", constraint_persistence), ("continuity_change", continuity_change), ("replay_depth_change", depth_change), ("delta_status", status)])


def classify_d13_regime_evolution(*, delta_comparison: Mapping[str, Any]) -> OrderedDict[str, Any]:
    d = _dict(delta_comparison)
    if _text(d.get("delta_status")) == DELTA_INSUFFICIENT:
        cls = EVOLUTION_INSUFFICIENT
    elif _text(d.get("regime_transition")).startswith("fragmented") or _text(d.get("current_regime")) == "fragmented_expectation_history":
        cls = EVOLUTION_FRAGMENTING
    elif _text(d.get("constraint_persistence")) == "RESOLVING" and int(d.get("pattern_count_delta") or 0) <= 0 and _text(d.get("continuity_change")) == "UNCHANGED":
        cls = EVOLUTION_IMPROVING
    elif _text(d.get("constraint_persistence")) == "PERSISTENT" and int(d.get("pattern_count_delta") or 0) > 0:
        cls = EVOLUTION_DEGRADING
    elif _text(d.get("constraint_persistence")) == "RESOLVING" and _text(d.get("continuity_change")) == "CHANGED":
        cls = EVOLUTION_RECOVERING
    elif _text(d.get("delta_status")) == DELTA_STABLE:
        cls = EVOLUTION_STABLE
    else:
        cls = EVOLUTION_MIXED
    return OrderedDict([("regime_evolution_class", cls)])


def build_d13_regime_evolution_narrative(*, delta_comparison: Mapping[str, Any], regime_evolution_classification: Mapping[str, Any], current_snapshot: Mapping[str, Any]) -> OrderedDict[str, Any]:
    d, c, s = _dict(delta_comparison), _dict(regime_evolution_classification), _dict(current_snapshot)
    state = _text(c.get("regime_evolution_class"))
    driver = "constraint_persistence" if _text(d.get("constraint_persistence")) == "PERSISTENT" else ("pattern_family_shift" if _list(d.get("new_pattern_families")) or _list(d.get("resolved_pattern_families")) else "regime_transition")
    return OrderedDict([
        ("dominant_evolution_state", state),
        ("strongest_evolution_driver", driver),
        ("strongest_persistent_constraint", _text(s.get("strongest_historical_constraint")) or "NONE"),
        ("regime_transition_interpretation", _text(d.get("regime_transition")) or "INSUFFICIENT_HISTORY"),
        ("continuity_evolution_interpretation", f"Continuity change: {_text(d.get('continuity_change')) or 'UNCHANGED'}"),
        ("replay_depth_evolution_interpretation", f"Replay depth change: {_text(d.get('replay_depth_change')) or 'UNCHANGED'}"),
        ("pattern_evolution_interpretation", f"Pattern count delta: {int(d.get('pattern_count_delta') or 0)}; new={_list(d.get('new_pattern_families'))}; resolved={_list(d.get('resolved_pattern_families'))}."),
        ("unresolved_constraint_interpretation", f"Constraint persistence: {_text(d.get('constraint_persistence')) or 'UNKNOWN'}"),
        ("caveats", ["Historical regime evolution analysis only", "No predictive or trading signal generation"]),
    ])


def certify_d13_regime_evolution(*, current_snapshot: Mapping[str, Any] | None, previous_snapshots: list[Mapping[str, Any]], delta_comparison: Mapping[str, Any], regime_evolution_classification: Mapping[str, Any], d12_certification: Mapping[str, Any] | None = None) -> OrderedDict[str, Any]:
    cur = _dict(current_snapshot)
    d12 = _dict(d12_certification)
    lineage_ok = bool(_list(cur.get("lineage_refs")))
    replay_ok = bool(_list(cur.get("replay_ids")))
    current_valid = bool(cur and _text(cur.get("snapshot_id")) and _text(cur.get("snapshot_checksum")))
    prev_exists = bool(_list(previous_snapshots))
    d12_blocked = _text(d12.get("certification_status")).startswith("BLOCKED")
    delta_status = _text(delta_comparison.get("delta_status"))
    evo = _text(regime_evolution_classification.get("regime_evolution_class"))
    if not current_valid or d12_blocked or not lineage_ok or not replay_ok:
        status = "BLOCKED_REGIME_EVOLUTION_ANALYSIS"
    elif prev_exists and delta_status != DELTA_INSUFFICIENT and evo != EVOLUTION_INSUFFICIENT and evo != EVOLUTION_MIXED:
        status = "CERTIFIED_REGIME_EVOLUTION_ANALYSIS"
    else:
        status = "DEGRADED_REGIME_EVOLUTION_ANALYSIS"
    return OrderedDict([("certification_status", status), ("current_snapshot_valid", current_valid), ("history_available", prev_exists), ("lineage_intact", lineage_ok), ("replay_traceability_intact", replay_ok)])


def build_d13_dashboard_regime_evolution_cards(*, current_snapshot: Mapping[str, Any], delta_comparison: Mapping[str, Any], regime_evolution_classification: Mapping[str, Any], regime_evolution_narrative: Mapping[str, Any], certification: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("regime_evolution_status", certification.get("certification_status")),
        ("historical_expectation_regime", current_snapshot.get("historical_expectation_regime")),
        ("regime_evolution_class", regime_evolution_classification.get("regime_evolution_class")),
        ("regime_transition", delta_comparison.get("regime_transition")),
        ("strongest_evolution_driver", regime_evolution_narrative.get("strongest_evolution_driver")),
        ("strongest_persistent_constraint", regime_evolution_narrative.get("strongest_persistent_constraint")),
        ("pattern_count_delta", delta_comparison.get("pattern_count_delta")),
        ("continuity_change", delta_comparison.get("continuity_change")),
        ("replay_depth_change", delta_comparison.get("replay_depth_change")),
        ("recommendation", "Continue governed historical regime evolution review." if _text(certification.get("certification_status")) == "CERTIFIED_REGIME_EVOLUTION_ANALYSIS" else "Address history/lineage/continuity constraints before promotion."),
    ])


def build_d13_report_payload(*, current_snapshot: Mapping[str, Any], delta_comparison: Mapping[str, Any], regime_evolution_classification: Mapping[str, Any], regime_evolution_narrative: Mapping[str, Any], dashboard_cards: Mapping[str, Any], certification: Mapping[str, Any], objective: str = "D13 Historical Expectation Delta & Regime Evolution") -> OrderedDict[str, Any]:
    return OrderedDict([("objective", objective), ("current_snapshot", OrderedDict(deepcopy(dict(current_snapshot)))), ("delta_comparison", OrderedDict(deepcopy(dict(delta_comparison)))), ("regime_evolution_classification", OrderedDict(deepcopy(dict(regime_evolution_classification)))), ("regime_evolution_narrative", OrderedDict(deepcopy(dict(regime_evolution_narrative)))), ("dashboard_cards", OrderedDict(deepcopy(dict(dashboard_cards)))), ("certification", OrderedDict(deepcopy(dict(certification)))), ("no_direct_sql_bypass_used", True), ("no_writes_performed", True), ("no_live_fetches_performed", True), ("no_alerts_sent", True), ("recommendation", dashboard_cards.get("recommendation") or certification.get("certification_status"))])


def build_d13_report_markdown(*, report_payload: Mapping[str, Any]) -> str:
    r = _dict(report_payload)
    s = _dict(r.get("current_snapshot")); d = _dict(r.get("delta_comparison")); e = _dict(r.get("regime_evolution_classification")); n = _dict(r.get("regime_evolution_narrative")); c = _dict(r.get("dashboard_cards")); cert = _dict(r.get("certification"))
    return "\n".join([
        "# D13 Historical Expectation Delta & Regime Evolution", "", f"## Objective\n- {r.get('objective')}",
        "## Scope\n- Deterministic comparison of historical D12 expectation synthesis snapshots across runs/windows.",
        "## Non-goals\n- No prediction.\n- No trading signals.\n- No live ingestion.\n- No writes or alerts.",
        f"## Current Expectation Snapshot\n- Snapshot: {s.get('snapshot_id')}\n- Regime: {s.get('historical_expectation_regime')}\n- Pattern families: {s.get('pattern_families')}",
        f"## Delta Comparison\n- Delta status: {d.get('delta_status')}\n- Transition: {d.get('regime_transition')}\n- Pattern delta: {d.get('pattern_count_delta')}",
        f"## Regime Evolution Classification\n- Class: {e.get('regime_evolution_class')}",
        f"## Evolution Narrative\n- Dominant state: {n.get('dominant_evolution_state')}\n- Driver: {n.get('strongest_evolution_driver')}",
        f"## Dashboard Cards\n- Status: {c.get('regime_evolution_status')}\n- Recommendation: {c.get('recommendation')}",
        f"## Certification\n- {cert.get('certification_status')}",
        "## Governance Boundaries\n- no_direct_sql_bypass_used: True\n- no_writes_performed: True\n- no_live_fetches_performed: True\n- no_alerts_sent: True",
        f"## Final Recommendation\n- {r.get('recommendation')}",
    ])
