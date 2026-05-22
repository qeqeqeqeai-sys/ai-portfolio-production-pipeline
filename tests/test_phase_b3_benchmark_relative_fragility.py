from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_b3_evidence_chain,
    build_benchmark_context_summary,
    build_benchmark_relative_fragility_label,
    build_benchmark_relative_resilience_interpretation,
    build_peer_relative_fragility_interpretation,
    build_phase_b3_benchmark_relative_report,
    build_relative_fragility_delta,
    build_subsector_relative_fragility_interpretation,
    build_universe_relative_fragility_interpretation,
    build_phase_b1_heatmap_report,
    build_phase_b2_asymmetry_report,
)


def _entities():
    return [
        {"entity_id": "A", "entity_name": "Alpha", "peer_group": "P1", "subsector": "S1", "benchmark_id": "S1", "ai_expectation_failure_score": 90, "valuation_stretch_score": 90, "fundamental_support_score": 10, "narrative_saturation_score": 90, "certainty_fragility_score": 90, "structural_weakness_score": 90},
        {"entity_id": "B", "entity_name": "Beta", "peer_group": "P1", "subsector": "S1", "benchmark_id": "S1", "ai_expectation_failure_score": 20, "valuation_stretch_score": 20, "fundamental_support_score": 80, "narrative_saturation_score": 20, "certainty_fragility_score": 20, "structural_weakness_score": 20},
        {"entity_id": "C", "entity_name": "Gamma", "peer_group": "P2", "subsector": "S2", "benchmark_id": "S2", "ai_expectation_failure_score": None, "valuation_stretch_score": "x", "fundamental_support_score": -1, "narrative_saturation_score": 150, "certainty_fragility_score": 55, "structural_weakness_score": 45},
    ]


def test_public_api_presence_and_init_exports():
    assert callable(build_benchmark_context_summary)
    assert callable(build_phase_b3_benchmark_relative_report)
    assert callable(build_phase_b1_heatmap_report)
    assert callable(build_phase_b2_asymmetry_report)


def test_summary_grouping_and_clamping_missing_invalid():
    summaries = build_benchmark_context_summary(_entities(), group_key="subsector")
    assert len(summaries) == 2
    s2 = [s for s in summaries if s["benchmark_id"] == "S2"][0]
    assert s2["average_fundamental_support_score"] == 0
    assert s2["average_narrative_saturation_score"] == 100


def test_relative_delta_support_inversion_and_direction_and_label():
    uni = build_benchmark_context_summary(_entities())[0]
    delta = build_relative_fragility_delta(_entities()[0], uni)
    assert delta["fundamental_support_delta"] > 0
    assert delta["relative_fragility_direction"] == "MORE_FRAGILE_THAN_BENCHMARK"
    assert build_benchmark_relative_fragility_label(delta["fragility_delta"]) in {"HIGH_RELATIVE_FRAGILITY", "EXTREME_RELATIVE_FRAGILITY", "MODERATE_RELATIVE_FRAGILITY"}


def test_relative_peer_subsector_universe_labels_and_driver_precedence():
    groups = build_benchmark_context_summary(_entities(), group_key="peer_group")
    p1 = [g for g in groups if g["benchmark_id"] == "P1"][0]
    peer = build_peer_relative_fragility_interpretation(_entities()[0], p1)
    assert peer["peer_relative_label"].startswith("PEER_")
    assert peer["dominant_relative_driver"] == "valuation_stretch_delta"
    assert "trading recommendation" in peer["interpretation_summary"]
    subs = build_subsector_relative_fragility_interpretation(_entities()[0], build_benchmark_context_summary(_entities(), group_key="subsector")[0])
    uni = build_universe_relative_fragility_interpretation(_entities()[0], build_benchmark_context_summary(_entities())[0])
    assert subs["subsector_relative_label"].startswith("SUBSECTOR_")
    assert uni["universe_relative_label"].startswith("UNIVERSE_")


def test_resilience_and_evidence_chain_and_immutability_and_repeatability_checksums():
    ents = _entities()
    original = deepcopy(ents)
    bench = build_benchmark_context_summary(ents)[0]
    res = build_benchmark_relative_resilience_interpretation(ents[1], bench)
    assert "BENCHMARK" in res["benchmark_relative_resilience_label"]
    chain = build_b3_evidence_chain(ents[0], bench, b1_rankings=[{"entity_id": "A", "rank": 1}], b2_asymmetry_outputs=[{"entity_id": "A"}])
    assert chain["explanation_template_id"] == "template_phase_b3_benchmark_relative_v1"
    assert chain["b1_context_used"]
    assert chain["b2_context_used"]
    assert ents == original
    rep1 = build_phase_b3_benchmark_relative_report(ents)
    rep2 = build_phase_b3_benchmark_relative_report(ents)
    assert rep1 == rep2
    assert rep1["replay_metadata"]["input_checksum"] == rep2["replay_metadata"]["input_checksum"]
    assert rep1["replay_metadata"]["output_checksum"] == rep2["replay_metadata"]["output_checksum"]
    assert "architecture_constraints" in rep1
