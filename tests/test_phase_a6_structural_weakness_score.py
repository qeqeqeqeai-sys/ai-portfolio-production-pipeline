from copy import deepcopy

from transmission_layers import expectation_failure as ef


def _payload(**overrides):
    base = {
        "ticker": "XYZ",
        "sector": "Technology",
        "subsector": "Software",
        "fragility_score": 35,
        "transmission_instability_score": 40,
        "divergence_score": 45,
        "regime_stress_score": 30,
        "structural_deterioration_score": 42,
        "propagation_weakness_score": 38,
        "data_quality_flags": ["audited"],
        "raw_evidence_refs": ["ref:phase_a6:base"],
    }
    base.update(overrides)
    return base


def test_public_api_exports_exist():
    for name in (
        "score_structural_weakness",
        "build_structural_weakness_thresholds",
        "build_structural_weakness_subcomponent_contract",
        "build_structural_weakness_evidence_summary",
        "build_phase_a6_structural_weakness_report",
    ):
        assert hasattr(ef, name)


def test_threshold_builder_returns_fixed_deterministic_thresholds():
    a = ef.build_structural_weakness_thresholds()
    b = ef.build_structural_weakness_thresholds()
    assert a == b
    assert a["weights"] == {
        "fragility_risk_score": 0.25,
        "transmission_instability_risk_score": 0.20,
        "divergence_risk_score": 0.20,
        "regime_stress_risk_score": 0.15,
        "deterioration_propagation_risk_score": 0.20,
    }


def test_subcomponent_contract_includes_all_required_components():
    contract = ef.build_structural_weakness_subcomponent_contract()
    assert set(contract["subcomponents"]) == {
        "fragility_risk_score",
        "transmission_instability_risk_score",
        "divergence_risk_score",
        "regime_stress_risk_score",
        "deterioration_propagation_risk_score",
    }


def test_score_deterministic_not_mutating_input_bounded_and_banded():
    payload = _payload()
    before = deepcopy(payload)
    out1 = ef.score_structural_weakness(payload)
    out2 = ef.score_structural_weakness(payload)
    assert out1 == out2
    assert payload == before
    assert 0 <= out1["score_value"] <= 100
    assert out1["score_band"] in {"low", "mild", "elevated", "high", "severe"}


def test_resilient_vs_stressed_inputs_map_to_expected_ranges():
    low = ef.score_structural_weakness(
        _payload(
            fragility_score=10,
            transmission_instability_score=12,
            divergence_score=14,
            regime_stress_score=16,
            structural_deterioration_score=15,
            propagation_weakness_score=10,
        )
    )
    high = ef.score_structural_weakness(
        _payload(
            fragility_score=92,
            transmission_instability_score=88,
            divergence_score=90,
            regime_stress_score=86,
            structural_deterioration_score=94,
            propagation_weakness_score=96,
        )
    )
    assert low["score_band"] in {"low", "mild"}
    assert high["score_band"] in {"high", "severe"}


def test_missing_inputs_and_out_of_range_clamping_and_template_and_flags():
    out = ef.score_structural_weakness(
        _payload(
            fragility_score=None,
            transmission_instability_score=-2,
            divergence_score=120,
            regime_stress_score=None,
            structural_deterioration_score=None,
            propagation_weakness_score=None,
            data_quality_flags=[],
        )
    )
    assert 0 <= out["score_value"] <= 100
    assert out["missing_inputs"]
    assert "fragility_score" in out["missing_inputs"]
    assert "deterioration_propagation_risk_score" in out["missing_inputs"]
    assert "clamped_low:transmission_instability_score" in out["data_quality_flags"]
    assert "clamped_high:divergence_score" in out["data_quality_flags"]
    assert out["explanation_template_id"] == "template_structural_weakness_limited_data_v1"


def test_thresholds_triggered_explainability_invariants_and_explicit_exclusions():
    out = ef.score_structural_weakness(_payload())
    assert isinstance(out["thresholds_triggered"], list)
    assert out["thresholds_triggered"]
    assert out["explanation"].startswith("Structural Weakness is")
    assert all(out["invariant_flags"].values())
    assert out["invariant_flags"]["no_upstream_mutation"] is True
    assert out["invariant_flags"]["bridge_only_mapping"] is True

    contracts = ef.build_expectation_failure_score_contracts()
    assert any(c["score_name"] == "structural_weakness_score" for c in contracts)

    report = ef.build_phase_a6_structural_weakness_report()
    boundaries = " ".join(report["implementation_boundaries"])
    assert "no_composite_ai_expectation_failure_score" in boundaries
    assert "no_prediction" in boundaries and "optimization" in boundaries and "adaptive" in boundaries


def test_phase_a1_through_a5_regressions_still_pass_contractually():
    assert ef.score_valuation_stretch(_payload(pe_ratio=20, sector_pe_median=18, ev_to_sales=4, sector_ev_to_sales_median=4, forward_revenue_growth=22, market_implied_revenue_growth=20, rule_of_40=45, price_to_gross_profit=9, sector_price_to_gross_profit_median=8))["score_name"] == "valuation_stretch_score"
    assert ef.score_fundamental_support(_payload(fcf_margin=18, sector_fcf_margin_median=12, gross_margin_change=2, operating_margin_change=1, roic=22, sector_roic_median=12, net_debt_to_ebitda=0.5, cash_to_debt=2.5, share_dilution_rate=0.5, cash_burn_rate=-2))["score_name"] == "fundamental_support_score"
    assert ef.score_narrative_saturation(_payload(ai_keyword_density=1.2, sector_ai_keyword_density_median=1.5, news_volume_spike=1.0, sentiment_overheating=25, thematic_crowding=20, retail_attention_spike=1.1, management_ai_mention_intensity=2, etf_theme_inclusion_count=1))["score_name"] == "narrative_saturation_score"
    assert ef.score_certainty_fragility(_payload(estimate_dispersion=25, revenue_revision_instability=30, eps_revision_instability=35, execution_dependency=45, customer_concentration=20, product_concentration=30, margin_expansion_dependency=40, competitive_intensity=50, uncertainty_concentration=45))["score_name"] == "certainty_fragility_score"
