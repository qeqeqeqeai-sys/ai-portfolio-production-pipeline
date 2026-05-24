from transmission_layers.expectation_failure.expectation_intelligence.d8_2_evidence_density_historical_replay_expansion import (
    build_d8_2_payload,
    build_d8_2_replay_density_inventory,
    build_d8_2_semantic_persistence_summary,
    build_d8_2_theme_evolution_summary,
    build_d8_2_contradiction_persistence_summary,
    build_d8_2_dashboard_view_model,
    certify_d8_2_replay_density_expansion,
)


def _fixtures():
    historical = [
        {"run_id": "r1", "timestamp": "2026-05-22T00:00:00Z", "regime": "fragile", "semantic": {"themes": ["liquidity_stress", "spread_widening"]}, "contradictions": {"claims": ["macro conflicts"]}},
        {"run_id": "r2", "timestamp": "2026-05-23T00:00:00Z", "regime": "fragile", "semantic": {"themes": ["liquidity_stress", "earnings_dispersion"]}, "contradictions": {"claims": ["macro conflicts", "valuation tension"]}},
        {"run_id": "r3", "timestamp": "2026-05-24T00:00:00Z", "regime": "transition", "semantic": {"themes": ["earnings_dispersion", "credit_risk"]}, "contradictions": {"claims": ["macro conflicts"]}},
    ]
    findings = [{"finding_id": "F1"}, {"finding_id": "F2"}]
    narratives = [{"record_id": "N1"}]
    evidence = [
        {"evidence_ref": "EV1", "finding_refs": ["F1"]},
        {"evidence_ref": "EV2", "finding_refs": ["F1", "F2"]},
        {"evidence_ref": "EV3", "finding_refs": ["F2"]},
    ]
    e2 = {
        "evidence_finding_linkages": [
            {"evidence_ref": "EV1", "finding_id": "F1"},
            {"evidence_ref": "EV2", "finding_id": "F1"},
            {"evidence_ref": "EV2", "finding_id": "F2"},
            {"evidence_ref": "EV3", "finding_id": "F2"},
        ],
        "contradiction_evidence_map": [
            {"contradiction_claim": "macro conflicts", "supporting_evidence_refs": ["EV2"]},
            {"contradiction_claim": "valuation tension", "supporting_evidence_refs": ["EV3"]},
        ],
    }
    e3 = {"history_sufficiency": "sufficient_history"}
    e4 = {"semantic_memory_inventory": {"themes": ["liquidity_stress", "earnings_dispersion", "credit_risk"]}}
    e5 = {"caveat_inventory": {"consolidated_caveats": ["weak_linkage"]}}
    return historical, findings, narratives, evidence, e2, e3, e4, e5


def test_d8_2_replay_aggregation_and_checksum_deterministic():
    h, f, n, e, e2, e3, e4, e5 = _fixtures()
    p1 = build_d8_2_payload(h, f, n, e, e2, e3, e4, e5)
    p2 = build_d8_2_payload(h, f, n, e, e2, e3, e4, e5)
    assert p1["d8_2_checksum"] == p2["d8_2_checksum"]
    assert p1["replay_density_inventory"]["runs_observed"] == 3


def test_d8_2_semantic_persistence_and_evolution_correctness():
    h, f, n, e, e2, e3, e4, e5 = _fixtures()
    replay = build_d8_2_replay_density_inventory(h, f, e, e2, e3, e4, e5)
    replay["historical_runs_payloads"] = h
    semantic = build_d8_2_semantic_persistence_summary(replay)
    evo = build_d8_2_theme_evolution_summary(semantic)
    assert "liquidity_stress" in semantic["recurring_themes"]
    assert "credit_risk" in semantic["emerging_themes"]
    assert "liquidity_stress" in semantic["decaying_themes"]
    assert evo["weakening_themes"] == semantic["decaying_themes"]


def test_d8_2_contradiction_persistence_behavior_and_no_fabrication():
    h, _, _, _, e2, _, _, _ = _fixtures()
    contradiction = build_d8_2_contradiction_persistence_summary(h, e2)
    assert contradiction["persistent_contradiction_themes"] == ["macro conflicts"]
    assert set(contradiction["tracked_contradiction_themes"]) == {"macro conflicts", "valuation tension"}


def test_d8_2_sparse_history_degraded_handling_and_dashboard_compatibility():
    h, f, n, e, e2, e3, e4, e5 = _fixtures()
    payload = build_d8_2_payload(h[:1], f, n, e[:1], e2, e3, e4, e5)
    assert payload["regime_transition_history"]["continuity_status"] in {"insufficient_history", "continuous"}
    vm = build_d8_2_dashboard_view_model(payload)
    assert "semantic_persistence_summary" in vm
    assert "persistent_contradiction_tracking" in vm


def test_d8_2_governance_boundaries_and_read_only_contract():
    h, f, n, e, e2, e3, e4, e5 = _fixtures()
    payload = build_d8_2_payload(h, f, n, e, e2, e3, e4, e5)
    cert = certify_d8_2_replay_density_expansion(payload)
    assert cert["deterministic"] is True
    inv = payload["forbidden_capability_inventory"]
    assert inv["prediction_engine"] is False
    assert inv["trading_recommendation"] is False
    assert inv["execution_engine"] is False
    assert inv["writes"] is False
    assert inv["network_calls"] is False
