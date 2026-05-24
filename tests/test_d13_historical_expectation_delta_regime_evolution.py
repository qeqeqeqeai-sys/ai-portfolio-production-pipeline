from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d13_expectation_synthesis_snapshot,
    compare_d13_expectation_snapshots,
    classify_d13_regime_evolution,
    build_d13_regime_evolution_narrative,
    certify_d13_regime_evolution,
    build_d13_dashboard_regime_evolution_cards,
    build_d13_report_payload,
    build_d13_report_markdown,
)


def _d12_payload(regime="historically_stable_expectation_base", confidence="MEDIUM", continuity="CONTINUITY_OK", depth="REPLAY_DEPTH_SUFFICIENT", families=None, unresolved=None):
    families = families if families is not None else ["recurring_expectation_constraint", "finding_recurrence"]
    unresolved = unresolved if unresolved is not None else ["LIMITED_HISTORICAL_DEPTH"]
    return {
        "regime_classification": {"historical_expectation_regime": regime, "regime_confidence_band": confidence},
        "expectation_intelligence_synthesis": {
            "strongest_recurring_pattern": families[0],
            "strongest_historical_constraint": "unresolved_constraint_persistence",
            "replay_depth_interpretation": depth,
            "continuity_interpretation": continuity,
            "unresolved_constraints": unresolved,
        },
        "historical_expectation_inventory": {"replay_ids": ["R1", "R2"], "lineage_refs": ["L1", "L2"]},
        "cross_window_patterns": [{"pattern_family": x} for x in families],
    }


def _build_flow(cur, prev_list):
    delta = compare_d13_expectation_snapshots(current_snapshot=cur, previous_snapshots=prev_list)
    cls = classify_d13_regime_evolution(delta_comparison=delta)
    nar = build_d13_regime_evolution_narrative(delta_comparison=delta, regime_evolution_classification=cls, current_snapshot=cur)
    cert = certify_d13_regime_evolution(current_snapshot=cur, previous_snapshots=prev_list, delta_comparison=delta, regime_evolution_classification=cls, d12_certification={"certification_status": "CERTIFIED_HISTORICAL_EXPECTATION_SYNTHESIS"})
    cards = build_d13_dashboard_regime_evolution_cards(current_snapshot=cur, delta_comparison=delta, regime_evolution_classification=cls, regime_evolution_narrative=nar, certification=cert)
    report = build_d13_report_payload(current_snapshot=cur, delta_comparison=delta, regime_evolution_classification=cls, regime_evolution_narrative=nar, dashboard_cards=cards, certification=cert)
    return delta, cls, nar, cert, cards, report


def test_api_export_presence_and_deterministic_checksum_and_immutability():
    payload = _d12_payload()
    original = deepcopy(payload)
    s1 = build_d13_expectation_synthesis_snapshot(d12_report_payload=payload, cycle_id="C1", snapshot_timestamp="2026-05-24T00:00:00Z")
    s2 = build_d13_expectation_synthesis_snapshot(d12_report_payload=payload, cycle_id="C1", snapshot_timestamp="2026-05-24T00:00:00Z")
    assert s1["snapshot_checksum"] == s2["snapshot_checksum"]
    assert payload == original


def test_insufficient_history_delta():
    cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload())
    delta = compare_d13_expectation_snapshots(current_snapshot=cur, previous_snapshots=[])
    assert delta["delta_status"] == "EXPECTATION_DELTA_INSUFFICIENT_HISTORY"
    assert classify_d13_regime_evolution(delta_comparison=delta)["regime_evolution_class"] == "REGIME_INSUFFICIENT_HISTORY"


def test_stable_improving_degrading_fragmenting_recovering_mixed_and_persistence_and_family_deltas_and_cards_and_cert_paths_and_report_shape():
    prev = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(confidence="MEDIUM", families=["a", "b"], unresolved=["C1"], continuity="CONTINUITY_OK"))

    stable_cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(confidence="MEDIUM", families=["a", "b"], unresolved=["C1"], continuity="CONTINUITY_OK"))
    d, c, n, cert, cards, report = _build_flow(stable_cur, [prev])
    assert d["delta_status"] == "EXPECTATION_DELTA_STABLE" and c["regime_evolution_class"] == "REGIME_STABLE"
    assert d["constraint_persistence"] == "PERSISTENT"
    for k in ["regime_evolution_status", "historical_expectation_regime", "regime_evolution_class", "regime_transition", "strongest_evolution_driver", "strongest_persistent_constraint", "pattern_count_delta", "continuity_change", "replay_depth_change", "recommendation"]:
        assert k in cards
    assert cert["certification_status"] == "CERTIFIED_REGIME_EVOLUTION_ANALYSIS"

    improving_cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(confidence="HIGH", families=["a"], unresolved=[]))
    d = compare_d13_expectation_snapshots(current_snapshot=improving_cur, previous_snapshots=[prev])
    assert classify_d13_regime_evolution(delta_comparison=d)["regime_evolution_class"] == "REGIME_IMPROVING"

    degrading_cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(confidence="MEDIUM", families=["a", "b", "c"], unresolved=["C1", "C2"]))
    d = compare_d13_expectation_snapshots(current_snapshot=degrading_cur, previous_snapshots=[prev])
    assert classify_d13_regime_evolution(delta_comparison=d)["regime_evolution_class"] == "REGIME_DEGRADING"

    frag_cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(regime="fragmented_expectation_history", families=["a", "x"], unresolved=["C1"]))
    d = compare_d13_expectation_snapshots(current_snapshot=frag_cur, previous_snapshots=[prev])
    assert classify_d13_regime_evolution(delta_comparison=d)["regime_evolution_class"] == "REGIME_FRAGMENTING"

    rec_cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(confidence="MEDIUM", families=["a", "b"], unresolved=[], continuity="CONTINUITY_DEGRADED"))
    d = compare_d13_expectation_snapshots(current_snapshot=rec_cur, previous_snapshots=[prev])
    assert classify_d13_regime_evolution(delta_comparison=d)["regime_evolution_class"] == "REGIME_RECOVERING"

    mix_cur = build_d13_expectation_synthesis_snapshot(d12_report_payload=_d12_payload(confidence="LOW", families=["a", "z"], unresolved=["C3"]))
    d = compare_d13_expectation_snapshots(current_snapshot=mix_cur, previous_snapshots=[prev])
    assert classify_d13_regime_evolution(delta_comparison=d)["regime_evolution_class"] == "REGIME_MIXED"
    assert d["new_pattern_families"] == ["z"] and d["recurring_pattern_families"] == ["a"] and d["resolved_pattern_families"] == ["b"]

    bad_cert = certify_d13_regime_evolution(current_snapshot={}, previous_snapshots=[], delta_comparison={"delta_status": "EXPECTATION_DELTA_INSUFFICIENT_HISTORY"}, regime_evolution_classification={"regime_evolution_class": "REGIME_INSUFFICIENT_HISTORY"}, d12_certification={"certification_status": "BLOCKED_HISTORICAL_EXPECTATION_SYNTHESIS"})
    assert bad_cert["certification_status"] == "BLOCKED_REGIME_EVOLUTION_ANALYSIS"
    deg_cert = certify_d13_regime_evolution(current_snapshot=stable_cur, previous_snapshots=[], delta_comparison={"delta_status": "EXPECTATION_DELTA_INSUFFICIENT_HISTORY"}, regime_evolution_classification={"regime_evolution_class": "REGIME_INSUFFICIENT_HISTORY"}, d12_certification={"certification_status": "CERTIFIED_HISTORICAL_EXPECTATION_SYNTHESIS"})
    assert deg_cert["certification_status"] == "DEGRADED_REGIME_EVOLUTION_ANALYSIS"

    text = build_d13_report_markdown(report_payload=report)
    assert "No prediction" in text and "No trading signals" in text
    assert report["no_direct_sql_bypass_used"] and report["no_writes_performed"] and report["no_live_fetches_performed"] and report["no_alerts_sent"]
    assert "api_key" not in text.lower() and "secret" not in text.lower()
    assert set(stable_cur["replay_ids"]) == {"R1", "R2"} and set(stable_cur["lineage_refs"]) == {"L1", "L2"}
