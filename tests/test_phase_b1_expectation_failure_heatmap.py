from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_expectation_failure_heatmap,
    build_fragility_cluster_summary,
    build_heatmap_evidence_summary,
    build_phase_b1_heatmap_report,
    build_relative_fragility_ranking,
)


def _payload():
    return {
        "universe_name": "U1",
        "as_of_date": "2026-05-22",
        "entities": [
            {"ticker": "AAA", "sector": "Tech", "subsector": "AI", "ai_expectation_failure_score": 90, "valuation_stretch_score": 80, "fundamental_support_score": 75, "narrative_saturation_score": 78, "certainty_fragility_score": 76, "structural_weakness_score": 74, "data_quality_flags": [], "raw_evidence_refs": ["a"]},
            {"ticker": "BBB", "sector": "Tech", "subsector": "AI", "ai_expectation_failure_score": 90, "valuation_stretch_score": 70, "fundamental_support_score": 60, "narrative_saturation_score": 80, "certainty_fragility_score": 65, "structural_weakness_score": 75, "data_quality_flags": [], "raw_evidence_refs": ["b"]},
            {"ticker": "CCC", "sector": "Health", "subsector": "Bio", "ai_expectation_failure_score": 40, "valuation_stretch_score": -5, "fundamental_support_score": None, "narrative_saturation_score": 30, "certainty_fragility_score": 35, "structural_weakness_score": 101, "data_quality_flags": ["src"], "raw_evidence_refs": ["c"]},
            {"ticker": "DDD", "sector": "Health", "subsector": "Bio", "ai_expectation_failure_score": 52, "valuation_stretch_score": 71, "fundamental_support_score": 66, "narrative_saturation_score": 20, "certainty_fragility_score": 20, "structural_weakness_score": 20, "data_quality_flags": [], "raw_evidence_refs": ["d"]},
        ],
    }


def test_public_api_exports_exist():
    assert callable(build_expectation_failure_heatmap)
    assert callable(build_relative_fragility_ranking)
    assert callable(build_fragility_cluster_summary)
    assert callable(build_heatmap_evidence_summary)
    assert callable(build_phase_b1_heatmap_report)


def test_deterministic_and_immutable_inputs():
    payload = _payload()
    before = deepcopy(payload)
    out1 = build_expectation_failure_heatmap(payload)
    out2 = build_expectation_failure_heatmap(payload)
    assert out1 == out2
    assert payload == before


def test_scores_bounded_missing_clamped_and_flags():
    out = build_expectation_failure_heatmap(_payload())
    ccc = next(x for x in out["ranked_entities"] if x["ticker"] == "CCC")
    assert ccc["component_scores"]["valuation_stretch_score"] == 0
    assert ccc["component_scores"]["fundamental_support_score"] == 50
    assert ccc["component_scores"]["structural_weakness_score"] == 100
    assert "CCC:fundamental_support_score" in out["missing_inputs"]
    assert any(flag.startswith("CCC:clamped_low:valuation_stretch_score") for flag in out["data_quality_flags"])
    assert any(flag.startswith("CCC:clamped_high:structural_weakness_score") for flag in out["data_quality_flags"])


def test_ranking_tie_breakers_and_drivers_and_labels_small_universe():
    out = build_expectation_failure_heatmap(_payload())
    tickers = [r["ticker"] for r in out["ranked_entities"]]
    assert tickers[:2] == ["BBB", "AAA"]
    top = out["ranked_entities"][0]
    assert top["dominant_risk_driver"] == "narrative_saturation_score" or top["dominant_risk_driver"] == "structural_weakness_score"
    assert top["secondary_risk_driver"] in top["component_scores"]
    labels = [r["relative_fragility_label"] for r in out["ranked_entities"]]
    assert labels == ["highest_relative_fragility", "moderate_relative_fragility", "moderate_relative_fragility", "lower_relative_fragility"]


def test_cluster_precedence_subsector_summary_and_cluster_summary_and_templates():
    out = build_expectation_failure_heatmap(_payload())
    by_ticker = {r["ticker"]: r for r in out["ranked_entities"]}
    assert by_ticker["AAA"]["cluster_label"] == "broad_expectation_failure_cluster"
    assert by_ticker["BBB"]["cluster_label"] == "broad_expectation_failure_cluster"
    assert by_ticker["DDD"]["cluster_label"] == "fundamental_support_gap_cluster"
    assert by_ticker["CCC"]["cluster_label"] == "low_fragility_cluster"
    assert all(r["explanation_template_id"] == "template_phase_b1_relative_fragility_v1" for r in out["ranked_entities"])
    ai_summary = next(s for s in out["subsector_summaries"] if s["subsector"] == "AI")
    assert ai_summary["entity_count"] == 2
    assert ai_summary["average_ai_expectation_failure_score"] == 90
    assert "dominant_cluster" in ai_summary
    assert "cluster_counts" in out["cluster_summary"]


def test_invariants_and_report_boundaries_and_no_phase_a_recompute_proxy():
    out = build_expectation_failure_heatmap(_payload())
    assert all(out["invariant_flags"].values())
    report = build_phase_b1_heatmap_report()
    assert report["phase"] == "Phase B1"
    assert report["implementation_boundaries"]["trading_signals"] == "excluded"
    assert report["scoring_scope"]["no_phase_a_recompute"] is True
