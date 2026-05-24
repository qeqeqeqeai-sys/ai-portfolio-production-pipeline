from transmission_layers.expectation_failure.expectation_intelligence.d8_a1_explainability_causal_narratives import build_d8_a1_explainability_causal_narratives

def test_d8_a1_deterministic_narratives_and_confidence_bounds():
    d8_2={"semantic_persistence_summary":{"recurring_themes":["supply"]},"theme_evolution_summary":{"weakening_themes":["demand"]},"regime_transition_history":{"transition_count":2,"continuity_status":"continuous"}}
    d8_5={"caveat_reasons":["low_specificity"]}
    d8_6={"weakest_linkage_areas":["low_multiplicity_graph"],"linkage_density_score":0.6,"strongest_evidence_candidates":[{"evidence_ref":"EV1"}]}
    d8_b1={"historical_density_status":"REPLAY_CONTINUITY_MODERATE","replay_continuity_score":0.5,"evidence_reinforcement_score":0.5}
    reinf={"recurring_evidence_refs":{"EV1":2},"recurring_contradiction_refs":{"C1":2}}
    out1=build_d8_a1_explainability_causal_narratives(d8_2_payload=d8_2,d8_5_payload=d8_5,d8_6_payload=d8_6,d8_b1_payload=d8_b1,d8_b1_reinforcement=reinf)
    out2=build_d8_a1_explainability_causal_narratives(d8_2_payload=d8_2,d8_5_payload=d8_5,d8_6_payload=d8_6,d8_b1_payload=d8_b1,d8_b1_reinforcement=reinf)
    assert out1["d8_a1_checksum"] == out2["d8_a1_checksum"]
    assert out1["explainability_status"] in {"EXPLAINABILITY_MODERATE","EXPLAINABILITY_STRONG"}
    assert "Evidence reinforcement observed" in out1["narratives"]["evidence_reinforcement_narrative"]

def test_d8_a1_sparse_history_degrades_without_fabrication():
    out=build_d8_a1_explainability_causal_narratives(d8_2_payload={},d8_5_payload={},d8_6_payload={},d8_b1_payload={},d8_b1_reinforcement={})
    assert out["explainability_status"] == "EXPLAINABILITY_BLOCKED"
    assert out["forbidden_capability_inventory"]["writes"] is False
