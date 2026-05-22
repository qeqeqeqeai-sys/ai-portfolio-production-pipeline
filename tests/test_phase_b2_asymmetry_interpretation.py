from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_b2_evidence_chain,
    build_cluster_asymmetry_summary,
    build_downside_asymmetry_classification,
    build_expectation_support_mismatch,
    build_long_risk_fragility_interpretation,
    build_phase_b2_asymmetry_report,
    build_ranking_asymmetry_interpretation,
    build_relative_resilience_interpretation,
    build_subsector_asymmetry_summary,
)


def _entity(**overrides):
    base = {
        "entity_id": "E1",
        "entity_name": "Entity One",
        "ticker": "EONE",
        "subsector": "Software",
        "cluster_id": "C1",
        "ai_expectation_failure_score": 82,
        "valuation_stretch_score": 80,
        "fundamental_support_score": 35,
        "narrative_saturation_score": 70,
        "certainty_fragility_score": 72,
        "structural_weakness_score": 65,
    }
    base.update(overrides)
    return base


def test_public_api_and_determinism_and_checksum():
    entities = [_entity(), _entity(entity_id="E2", ticker="ETWO", ai_expectation_failure_score=20, fundamental_support_score=80, structural_weakness_score=20, certainty_fragility_score=15)]
    out1 = build_phase_b2_asymmetry_report(entities)
    out2 = build_phase_b2_asymmetry_report(entities)
    assert out1 == out2
    assert out1["replay_metadata"]["input_checksum"] == out2["replay_metadata"]["input_checksum"]
    assert out1["replay_metadata"]["output_checksum"] == out2["replay_metadata"]["output_checksum"]


def test_input_immutable_and_bounding_and_missing_invalid():
    e = _entity(ai_expectation_failure_score=150, valuation_stretch_score=-5, narrative_saturation_score="bad", certainty_fragility_score=None)
    before = deepcopy(e)
    d = build_downside_asymmetry_classification(e)
    assert e == before
    s = d["normalized_scores"]
    assert s["ai_expectation_failure_score"] == 100
    assert s["valuation_stretch_score"] == 0
    assert s["narrative_saturation_score"] == 50
    assert s["certainty_fragility_score"] == 50


def test_labels_and_precedence():
    assert build_downside_asymmetry_classification(_entity())["downside_asymmetry_label"] == "EXTREME_DOWNSIDE_ASYMMETRY"
    assert build_downside_asymmetry_classification(_entity(ai_expectation_failure_score=72, valuation_stretch_score=70, fundamental_support_score=50, certainty_fragility_score=50))["downside_asymmetry_label"] == "HIGH_DOWNSIDE_ASYMMETRY"
    assert build_downside_asymmetry_classification(_entity(ai_expectation_failure_score=61, valuation_stretch_score=20, fundamental_support_score=80))["downside_asymmetry_label"] == "MODERATE_DOWNSIDE_ASYMMETRY"
    assert build_downside_asymmetry_classification(_entity(ai_expectation_failure_score=50, valuation_stretch_score=30, narrative_saturation_score=30, certainty_fragility_score=30, fundamental_support_score=85))["downside_asymmetry_label"] == "LOW_DOWNSIDE_ASYMMETRY"


def test_mismatch_fragility_resilience_labels():
    assert build_expectation_support_mismatch(_entity())["expectation_support_mismatch_label"] == "HIGH_EXPECTATION_SUPPORT_MISMATCH"
    assert build_long_risk_fragility_interpretation(_entity())["long_risk_fragility_label"] == "VERY_FRAGILE_LONG_EXPOSURE"
    assert build_relative_resilience_interpretation(_entity(entity_id="E3", ai_expectation_failure_score=20, fundamental_support_score=85, structural_weakness_score=20, certainty_fragility_score=20))["relative_resilience_label"] == "HIGH_RELATIVE_RESILIENCE"


def test_ranking_labels_tiebreak_cluster_subsector_evidence_chain_and_template_and_language_and_additive():
    entities = [
        _entity(entity_id="E1", ticker="A"),
        _entity(entity_id="E2", ticker="B", ai_expectation_failure_score=70, valuation_stretch_score=65, fundamental_support_score=45),
        _entity(entity_id="E3", ticker="C", ai_expectation_failure_score=40, fundamental_support_score=80, structural_weakness_score=20, certainty_fragility_score=10),
        _entity(entity_id="E4", ticker="D", ai_expectation_failure_score=30),
    ]
    rankings = [{"entity_id": e["entity_id"], "rank": i + 1} for i, e in enumerate(entities)]
    assert build_ranking_asymmetry_interpretation(entities[0], rankings)["ranking_interpretation_label"] == "TOP_FRAGILITY_CANDIDATE"
    assert build_ranking_asymmetry_interpretation(entities[-1], rankings)["ranking_interpretation_label"] in {"LOW_FRAGILITY_CANDIDATE", "RELATIVE_RESILIENCE_CANDIDATE"}
    c = build_cluster_asymmetry_summary("C", entities[:2])
    assert c["cluster_label"] == "UNSUPPORTED_VALUATION_CLUSTER"
    s = build_subsector_asymmetry_summary("Software", entities, b1_rankings=rankings)
    assert "subsector_asymmetry_label" in s
    chain = build_b2_evidence_chain(entities[0], b1_rankings=rankings)
    for field in ["entity_id", "downside_asymmetry_label", "long_risk_fragility_label", "expectation_support_mismatch_label", "relative_resilience_label", "ranking_interpretation_label", "normalized_scores", "classification_rule_id", "explanation_template_id", "replay_metadata"]:
        assert field in chain
    assert chain["explanation_template_id"] == "template_phase_b2_asymmetry_v1"
    text = chain["interpretation_summary"].lower()
    for bad in ["buy", "sell", "short this", "go long", "target price", "trade", "entry", "exit", "allocation", "position sizing"]:
        assert bad not in text
    report = build_phase_b2_asymmetry_report(entities, b1_rankings=rankings)
    assert report["replay_metadata"]["phase_id"] == "B2"
