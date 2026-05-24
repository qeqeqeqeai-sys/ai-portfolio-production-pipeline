from transmission_layers.expectation_failure.expectation_intelligence.d8_evidence_prioritization_operational_insight import (
    build_d8_evidence_priority_inventory,
    build_d8_dashboard_view_model,
    certify_d8_evidence_prioritization,
)


def _fixtures():
    findings = [
        {"finding_id": "F1", "confidence": "high"},
        {"finding_id": "F2", "confidence": "weak"},
    ]
    evidence = [
        {"evidence_ref": "EV1", "evidence_metadata": {"metric": "spread"}},
        {"evidence_ref": "EV2", "evidence_metadata": {"metric": "macro"}},
    ]
    e2 = {
        "evidence_quality_profiles": [
            {"evidence_ref": "EV1", "evidence_quality_score": 90, "evidence_quality_band": "strong"},
            {"evidence_ref": "EV2", "evidence_quality_score": 60, "evidence_quality_band": "moderate"},
        ],
        "evidence_finding_linkages": [
            {"evidence_ref": "EV1", "finding_id": "F1", "linkage_strength_score": 85},
            {"evidence_ref": "EV2", "finding_id": "F2", "linkage_strength_score": 55},
        ],
        "evidence_support_buckets": {"contradiction_evidence": ["EV2"]},
        "contradiction_evidence_map": [{"contradiction_claim": "macro conflicts", "contradiction_strength": 60, "affected_findings": ["F2"], "persistence_context": "persistent", "supporting_evidence_refs": ["EV2"]}],
    }
    e3 = {"contradiction_drift": {"direction": "rising"}, "expectation_pressure_drift": {"direction": "weakening"}, "history_sufficiency": "sufficient_history"}
    e4 = {"narrative_drift_profile": {"narrative_drift_direction": "widening"}}
    e5 = {"composite_regime_synthesis": {"dominant_expectation_regime": "valuation_persistence", "supporting_signal_refs": ["E1", "E2"]}, "caveat_inventory": {"consolidated_caveats": ["low_specificity"]}}
    return findings, evidence, e2, e3, e4, e5


def test_d8_deterministic_and_stable_ordering_and_checksum():
    args = _fixtures()
    p1 = build_d8_evidence_priority_inventory(*args)
    p2 = build_d8_evidence_priority_inventory(*args)
    assert p1["d8_checksum"] == p2["d8_checksum"]
    ranked = p1["supporting_evidence_rankings"]["ranked_evidence"]
    assert ranked[0]["evidence_ref"] == "EV1"


def test_d8_contradiction_prioritization_and_dashboard_compatibility():
    payload = build_d8_evidence_priority_inventory(*_fixtures())
    top = payload["contradiction_priority_summary"]["top_contradiction"]
    assert top["severity"] in {"high", "moderate", "low"}
    vm = build_d8_dashboard_view_model(payload)
    assert "strongest_supporting_evidence_panel" in vm
    assert "contradiction_severity_summaries" in vm


def test_d8_governance_and_no_prediction_capability():
    payload = build_d8_evidence_priority_inventory(*_fixtures())
    cert = certify_d8_evidence_prioritization(payload)
    assert cert["deterministic"] is True
    inv = payload["forbidden_capability_inventory"]
    assert inv["prediction_engine"] is False
    assert inv["trading_recommendation"] is False
    assert inv["writes"] is False
