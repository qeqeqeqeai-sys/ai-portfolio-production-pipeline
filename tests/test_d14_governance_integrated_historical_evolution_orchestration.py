from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_d14_cross_phase_audit_continuity,
    build_d14_dashboard_supervisory_cards,
    build_d14_orchestration_inventory,
    build_d14_report_markdown,
    build_d14_report_payload,
    build_d14_supervisory_operational_narrative,
    build_d14_supervisory_rollup,
    certify_d14_historical_evolution_orchestration,
    validate_d14_orchestration_eligibility,
)


def _fake_payloads():
    d11 = {"historical_replay_windows": {"lineage_refs": ["L1", "L2"], "replay_windows": [{"window": "W1"}]}, "certification": {"certification_status": "CERTIFIED_D11"}}
    d12 = {
        "historical_expectation_inventory": {"lineage_refs": ["L1", "L2"]},
        "cross_window_patterns": [{"pattern_family": "A"}, {"pattern_family": "B"}],
        "expectation_intelligence_synthesis": {"replay_depth_interpretation": "SUFFICIENT_REPLAY_DEPTH", "continuity_interpretation": "continuous", "unresolved_constraints": ["constraint_x"]},
        "regime_classification": {"historical_expectation_regime": "stable_expectation_history"},
        "certification": {"certification_status": "CERTIFIED_D12"},
    }
    d13 = {
        "current_snapshot": {"lineage_refs": ["L1", "L2"], "historical_expectation_regime": "stable_expectation_history", "replay_depth_interpretation": "SUFFICIENT_REPLAY_DEPTH", "unresolved_constraints": ["constraint_x"]},
        "delta_comparison": {"delta_status": "EXPECTATION_DELTA_STABLE"},
        "regime_evolution_classification": {"regime_evolution_class": "REGIME_STABLE"},
        "certification": {"certification_status": "CERTIFIED_REGIME_EVOLUTION_ANALYSIS"},
    }
    return d11, d12, d13


def _pipeline(d11, d12, d13):
    inv = build_d14_orchestration_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13)
    elig = validate_d14_orchestration_eligibility(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13, orchestration_inventory=inv)
    audit = build_d14_cross_phase_audit_continuity(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13)
    roll = build_d14_supervisory_rollup(orchestration_inventory=inv, eligibility_validation=elig, audit_continuity=audit)
    cert = certify_d14_historical_evolution_orchestration(d13_report_payload=d13, eligibility_validation=elig, audit_continuity=audit, supervisory_rollup=roll, orchestration_inventory=inv)
    nar = build_d14_supervisory_operational_narrative(orchestration_inventory=inv, supervisory_rollup=roll, audit_continuity=audit, certification=cert)
    cards = build_d14_dashboard_supervisory_cards(orchestration_inventory=inv, supervisory_rollup=roll, supervisory_operational_narrative=nar, certification=cert)
    payload = build_d14_report_payload(orchestration_inventory=inv, eligibility_validation=elig, supervisory_rollup=roll, audit_continuity=audit, supervisory_operational_narrative=nar, dashboard_cards=cards, certification=cert)
    return inv, elig, audit, roll, cert, nar, cards, payload


def test_api_presence_export():
    d11, d12, d13 = _fake_payloads()
    inv, *_ = _pipeline(d11, d12, d13)
    assert "inventory_checksum" in inv


def test_deterministic_checksum_and_input_immutability():
    d11, d12, d13 = _fake_payloads()
    original = deepcopy((d11, d12, d13))
    inv1 = build_d14_orchestration_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13)
    inv2 = build_d14_orchestration_inventory(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13)
    assert inv1["inventory_checksum"] == inv2["inventory_checksum"]
    assert (d11, d12, d13) == original


def test_blocked_missing_payloads():
    inv = build_d14_orchestration_inventory(d11_report_payload=None, d12_report_payload=None, d13_report_payload=None)
    elig = validate_d14_orchestration_eligibility(d11_report_payload=None, d12_report_payload=None, d13_report_payload=None, orchestration_inventory=inv)
    assert inv["inventory_status"] == "ORCHESTRATION_BLOCKED"
    assert elig["eligibility_status"] == "ORCHESTRATION_BLOCKED"


def test_blocked_fragmented_continuity():
    d11, d12, d13 = _fake_payloads()
    d12["expectation_intelligence_synthesis"]["continuity_interpretation"] = "fragmented"
    inv, elig, audit, *_ = _pipeline(d11, d12, d13)
    assert elig["eligibility_status"] == "ORCHESTRATION_BLOCKED"
    assert audit["audit_continuity_status"] in {"AUDIT_CONTINUITY_OK", "AUDIT_CONTINUITY_DEGRADED", "AUDIT_CONTINUITY_FRAGMENTED"}


def test_degraded_path_and_certified_path_and_rollup_deterministic():
    d11, d12, d13 = _fake_payloads()
    d12["certification"]["certification_status"] = "DEGRADED_D12"
    inv, elig, audit, roll1, cert, *_ = _pipeline(d11, d12, d13)
    roll2 = build_d14_supervisory_rollup(orchestration_inventory=inv, eligibility_validation=elig, audit_continuity=audit)
    assert inv["inventory_status"] == "ORCHESTRATION_DEGRADED"
    assert elig["eligibility_status"] == "ORCHESTRATION_DEGRADED"
    assert roll1["rollup_score"] == roll2["rollup_score"]
    assert cert["certification_status"] == "DEGRADED_HISTORICAL_EVOLUTION_ORCHESTRATION"

    d11, d12, d13 = _fake_payloads()
    d12["expectation_intelligence_synthesis"]["unresolved_constraints"] = []
    d13["current_snapshot"]["unresolved_constraints"] = []
    inv, elig, audit, _, cert, *_ = _pipeline(d11, d12, d13)
    assert elig["eligibility_status"] == "ORCHESTRATION_ELIGIBLE"
    assert cert["certification_status"] == "CERTIFIED_HISTORICAL_EVOLUTION_ORCHESTRATION"


def test_audit_status_variants_and_lineage_chain():
    d11, d12, d13 = _fake_payloads()
    audit_ok = build_d14_cross_phase_audit_continuity(d11_report_payload=d11, d12_report_payload=d12, d13_report_payload=d13)
    assert audit_ok["audit_continuity_status"] == "AUDIT_CONTINUITY_OK"
    assert "L1" in audit_ok["lineage_chain"]["common"]

    d12b = deepcopy(d12); d12b["historical_expectation_inventory"]["lineage_refs"] = ["L1", "L3"]
    audit_deg = build_d14_cross_phase_audit_continuity(d11_report_payload=d11, d12_report_payload=d12b, d13_report_payload=d13)
    assert audit_deg["audit_continuity_status"] == "AUDIT_CONTINUITY_DEGRADED"

    d11c = deepcopy(d11); d11c["historical_replay_windows"]["lineage_refs"] = []
    audit_frag = build_d14_cross_phase_audit_continuity(d11_report_payload=d11c, d12_report_payload=d12b, d13_report_payload=d13)
    assert audit_frag["audit_continuity_status"] == "AUDIT_CONTINUITY_FRAGMENTED"


def test_cards_narrative_payload_markdown_and_boundary_flags():
    d11, d12, d13 = _fake_payloads()
    _, _, _, _, _, nar, cards, payload = _pipeline(d11, d12, d13)
    for field in ["orchestration_status", "supervisory_operational_state", "dominant_historical_regime", "regime_evolution_class", "supervisory_risk_band", "strongest_integrity_signal", "strongest_historical_constraint", "strongest_evolutionary_change", "unresolved_constraint_count", "recommendation"]:
        assert field in cards
    for field in ["dominant_supervisory_state", "strongest_integrity_signal", "strongest_historical_constraint", "strongest_evolutionary_change", "historical_interpretation", "continuity_interpretation", "governance_interpretation", "supervisory_interpretation", "unresolved_constraints", "caveats"]:
        assert field in nar
    assert payload["no_direct_sql_bypass_used"] is True
    assert payload["no_writes_performed"] is True
    assert payload["no_live_fetches_performed"] is True
    assert payload["no_alerts_sent"] is True
    assert payload["no_predictive_behavior"] is True
    md = build_d14_report_markdown(report_payload=payload)
    assert "## Objective" in md and "## Final Recommendation" in md
    assert "secret" not in md.lower()
    blocked_terms = ["buy signal", "sell signal", "trade now", "autonomous execution"]
    assert not any(term in md.lower() for term in blocked_terms)
