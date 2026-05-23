from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o1_dashboard_view_model,
    build_o2_dashboard_view_model,
    build_o2_pressure_evolution_diagnostics,
    build_o2_regime_transition_history,
    build_o2_replay_certification_cards,
    build_o2_replay_operationalization_report,
    build_o2_replay_timeline,
    build_o2_snapshot_comparison_cards,
    build_o2_structural_evolution_summary,
    certify_o2_replay_operationalization,
)


def _snapshots():
    return [
        {"snapshot_id": "s2", "as_of_date": "2026-01-02", "structural_pressure_score": 80, "fragility_score": 45, "expectation_fragility_score": 55, "propagation_pressure_score": 60, "regime_label": "STRESS", "checksum": "c2", "replay_metadata": {"x": 1}, "certification_status": "READY", "weakest_corridor": "C2"},
        {"snapshot_id": "s1", "as_of_date": "2026-01-01", "structural_pressure_score": 60, "fragility_score": 40, "expectation_fragility_score": 50, "propagation_pressure_score": 58, "regime_label": "CALM", "checksum": "c1", "replay_metadata": {"x": 1}, "certification_status": "READY", "weakest_corridor": "C1"},
        {"snapshot_id": "s3", "as_of_date": "2026-01-03", "structural_pressure_score": 86, "fragility_score": 42, "expectation_fragility_score": 59, "propagation_pressure_score": 63, "regime_label": "STRESS", "checksum": "c3", "replay_metadata": {"x": 1}, "certification_status": "DEGRADED", "degraded_reasons": ["partial"]},
    ]


def test_public_api_presence_and_export_presence():
    assert callable(build_o2_replay_timeline)
    assert callable(build_o2_structural_evolution_summary)
    assert callable(build_o2_regime_transition_history)
    assert callable(build_o2_pressure_evolution_diagnostics)
    assert callable(build_o2_snapshot_comparison_cards)
    assert callable(build_o2_replay_certification_cards)
    assert callable(build_o2_dashboard_view_model)
    assert callable(certify_o2_replay_operationalization)
    assert callable(build_o2_replay_operationalization_report)


def test_deterministic_repeated_outputs_and_checksum_stability():
    snaps = _snapshots()
    a = build_o2_dashboard_view_model(snaps)
    b = build_o2_dashboard_view_model(snaps)
    assert a == b
    c1 = certify_o2_replay_operationalization(snaps)["checksum"]
    c2 = certify_o2_replay_operationalization(snaps)["checksum"]
    assert c1 == c2


def test_fixed_timeline_ordering():
    ids = [x["snapshot_id"] for x in build_o2_replay_timeline(_snapshots())]
    assert ids == ["s1", "s2", "s3"]


def test_structural_evolution_delta_correctness():
    s = build_o2_structural_evolution_summary(_snapshots())
    assert s["pressure_delta"] == 26
    assert s["fragility_delta"] == 2


def test_regime_transition_detection():
    tx = build_o2_regime_transition_history(_snapshots())
    assert len(tx) == 1
    assert tx[0]["transition_label"] == "CALM->STRESS"


def test_pressure_diagnostics_threshold_behavior():
    d = build_o2_pressure_evolution_diagnostics(_snapshots())
    assert d["pressure_persistence_count"] == 2
    assert d["elevated_pressure_periods"][1]["pressure_level"] == "SEVERE"


def test_snapshot_comparison_card_fields():
    cards = build_o2_snapshot_comparison_cards(_snapshots())
    for key in ["structural_pressure_card", "fragility_card", "expectation_fragility_card", "propagation_pressure_card", "regime_card", "corridor_card"]:
        assert set(["title", "first_value", "latest_value", "delta", "state", "interpretation"]).issubset(cards[key].keys())


def test_replay_certification_card_behavior():
    cards = build_o2_replay_certification_cards(_snapshots())
    assert cards["total_snapshots"] == 3
    assert cards["degraded_snapshots"] >= 1


def test_dashboard_view_model_required_keys():
    vm = build_o2_dashboard_view_model(_snapshots())
    for key in ["page_id", "page_title", "generated_at_policy", "replay_timeline", "structural_evolution_summary", "regime_transition_history", "pressure_evolution_diagnostics", "snapshot_comparison_cards", "replay_certification_cards", "supervisor_summary", "governance_boundaries", "certification_summary"]:
        assert key in vm


def test_certification_paths():
    ok = [dict(x, certification_status="READY", degraded_reasons=[], blocked_reasons=[]) for x in _snapshots()]
    assert certify_o2_replay_operationalization(ok)["certification_status"] == "O2_REPLAY_OPERATIONALIZED"
    assert certify_o2_replay_operationalization(_snapshots())["certification_status"] == "O2_REPLAY_OPERATIONALIZED_DEGRADED"
    blocked = [{"snapshot_id": "b1", "as_of_date": "2026-01-01", "certification_status": "BLOCKED", "blocked_reasons": ["x"]}]
    assert certify_o2_replay_operationalization(blocked)["certification_status"] == "O2_REPLAY_OPERATIONALIZATION_BLOCKED"


def test_immutability_missing_fields_and_governance_inventory():
    snaps = _snapshots()
    original = deepcopy(snaps)
    build_o2_dashboard_view_model(snaps)
    assert snaps == original
    missing = [{"snapshot_id": "m1", "as_of_date": "2026-01-01"}]
    vm = build_o2_dashboard_view_model(missing)
    assert vm["replay_timeline"][0]["structural_pressure_score"] == 0.0
    forbidden = vm["governance_boundaries"]["forbidden_uses"]
    assert "trading recommendations" in forbidden


def test_report_builder_and_language_guardrails_and_o1_smoke():
    report = build_o2_replay_operationalization_report(_snapshots())
    assert "Objective" in report
    blocked_words = ["machine learning", "buy", "sell signal"]
    for word in blocked_words:
        assert word not in report.lower()
    assert "page_id" in build_o1_dashboard_view_model({})
