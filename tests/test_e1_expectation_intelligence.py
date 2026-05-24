from copy import deepcopy

from transmission_layers.expectation_failure.expectation_intelligence import (
    build_e1_contradiction_profile,
    build_e1_expectation_intelligence_payload,
    build_e1_expectation_pressure_profile,
    build_e1_fragility_concentration_profile,
    build_e1_semantic_pressure_profile,
    classify_e1_exhaustion_state,
    classify_e1_expectation_pressure_state,
)


def _sample_findings():
    return [
        {"finding_id": "F1", "finding_type": "EXPECTATION_FRAGILITY_ELEVATED", "finding_severity": "HIGH", "finding_summary": "conflicted divergence"},
        {"finding_id": "F2", "finding_type": "SEMANTIC_PRESSURE_CONCENTRATED", "finding_severity": "HIGH", "finding_summary": "contradiction persists"},
        {"finding_id": "F3", "finding_type": "MARKET_CONTEXT_CONFLICTED", "finding_severity": "MODERATE", "finding_summary": "conflicted"},
    ]


def _sample_narratives():
    return [
        {"narrative_section": "semantic_pressure", "narrative_text": "supportive but degraded deterioration signals"},
        {"narrative_section": "contradictions", "narrative_text": "divergence contradiction persistence"},
    ]


def test_api_and_determinism_and_checksum_stability():
    a = build_e1_expectation_intelligence_payload(_sample_findings(), _sample_narratives(), [])
    b = build_e1_expectation_intelligence_payload(_sample_findings(), _sample_narratives(), [])
    assert a["e1_checksum"] == b["e1_checksum"]
    assert a == b
    assert "strategist_summary" in a


def test_immutable_input_and_graceful_degraded_partial_payloads():
    findings = _sample_findings()
    original = deepcopy(findings)
    out = build_e1_expectation_intelligence_payload(findings, None, None)
    assert findings == original
    assert out["expectation_pressure_summary"]["pressure_profile"]["finding_count"] == len(findings)


def test_classification_and_ordering_and_bounded_behavior():
    profile = build_e1_expectation_pressure_profile(_sample_findings(), _sample_narratives())
    state = classify_e1_expectation_pressure_state(profile)
    assert state in {
        "diffuse_expectation", "concentrated_expectation", "momentum_supported_expectation", "valuation_supported_expectation",
        "semantic_supported_expectation", "structurally_fragile_expectation", "late_cycle_expectation", "exhaustion_risk",
    }
    assert profile["severity_concentration_ratio"] <= 1.0


def test_contradiction_exhaustion_concentration_semantic_layers():
    contradictions = build_e1_contradiction_profile(_sample_findings(), _sample_narratives())
    concentration = build_e1_fragility_concentration_profile(_sample_findings())
    semantic = build_e1_semantic_pressure_profile(_sample_narratives())
    assert contradictions["contradiction_persistence_score"] >= 0.0
    assert concentration["concentration_regime"] in {"isolated_fragility", "clustered_fragility", "systemic_fragility_concentration"}
    assert semantic["thematic_coherence"] <= 1.0
    assert classify_e1_exhaustion_state({"exhaustion_score": 0.8}) == "high"


def test_forbidden_capabilities_and_replay_continuity_shape():
    payload = build_e1_expectation_intelligence_payload(_sample_findings(), _sample_narratives(), [])
    assert payload["forbidden_capability_inventory"]["prediction_engine"] is False
    assert payload["forbidden_capability_inventory"]["trading_recommendation"] is False
    assert isinstance(payload["e1_checksum"], str) and len(payload["e1_checksum"]) == 64
