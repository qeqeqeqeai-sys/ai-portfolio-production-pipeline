from transmission_layers.expectation_failure.expectation_intelligence import *
from transmission_layers.expectation_failure.dashboard_operationalization.d7_streamlit_dashboard_viewer import build_d7_dashboard_view_model, D7_RENDER_SECTION_ORDER


def _sample_runs():
    return [
        {"run_id":"r2","run_timestamp":"2026-01-02T00:00:00Z","regime":"risk_off","contradiction_state":"high","continuity_state":"fragmented","confidence_state":"diverging","pattern_family":"pf_b","semantic_themes":["liquidity","credit"]},
        {"run_id":"r1","run_timestamp":"2026-01-01T00:00:00Z","regime":"risk_on","contradiction_state":"low","continuity_state":"stable","confidence_state":"converging","pattern_family":"pf_a","semantic_themes":["growth"]},
        {"run_id":"r3","run_timestamp":"2026-01-03T00:00:00Z","regime":"risk_off","contradiction_state":"high","continuity_state":"recovery","confidence_state":"oscillatory","pattern_family":"pf_b","semantic_themes":["liquidity","policy"]},
    ]


def test_h3_api_exports_and_determinism():
    inv1 = build_h3_replay_transition_inventory(replay_windows=_sample_runs())
    inv2 = build_h3_replay_transition_inventory(replay_windows=_sample_runs())
    assert inv1 == inv2
    assert inv1["replay_window_sequence"] == ["r1", "r2", "r3"]
    chains = build_h3_structural_transition_chains(transition_inventory=inv1)
    novelty = build_h3_transition_novelty_analysis(transition_inventory=inv1, transition_chains=chains)
    risk = build_h3_transition_risk_diagnostics(transition_inventory=inv1, novelty_analysis=novelty)
    recs = build_h3_operator_transition_recommendations(novelty_analysis=novelty, risk_diagnostics=risk)
    dash = build_h3_dashboard_payload(transition_inventory=inv1, transition_chains=chains, novelty_analysis=novelty, risk_diagnostics=risk, operator_recommendations=recs)
    cert1 = certify_h3_cross_replay_structural_transition_intelligence(transition_inventory=inv1, transition_chains=chains, dashboard_payload=dash)
    cert2 = certify_h3_cross_replay_structural_transition_intelligence(transition_inventory=inv1, transition_chains=chains, dashboard_payload=dash)
    assert cert1["checksum"] == cert2["checksum"]
    assert cert1["no_writes"] is True
    assert "predict" not in str(recs).lower() or "no predictive" in str(recs).lower()


def test_h3_degraded_behavior_and_input_immutability():
    data=[{"run_id":"x","run_timestamp":"2026-01-01T00:00:00Z"}]
    orig=list(data)
    inv=build_h3_replay_transition_inventory(replay_windows=data)
    assert data==orig
    chains=build_h3_structural_transition_chains(transition_inventory=inv)
    cert=certify_h3_cross_replay_structural_transition_intelligence(transition_inventory=inv, transition_chains=chains, dashboard_payload={})
    assert cert["status"] == BLOCKED_CROSS_REPLAY_STRUCTURAL_TRANSITION_INTELLIGENCE


def test_h3_d7_integration_and_ordering():
    vm=build_d7_dashboard_view_model(findings_payload={"rows":[]}, narratives_payload={"rows":[]}, evidence_payload={"rows":[]}, integrity_payload={"manifests":{"rows":[]},"audits":{"rows":[]},"replay":{"rows":[]}}, historical_runs_payloads=_sample_runs())
    assert "h3_cross_replay_structural_transition_intelligence" in vm
    assert D7_RENDER_SECTION_ORDER.index("cd1_candidate_diversity_strengthening") < D7_RENDER_SECTION_ORDER.index("h3_cross_replay_structural_transition_intelligence")
