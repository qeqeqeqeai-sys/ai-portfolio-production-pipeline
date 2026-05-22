from copy import deepcopy

from transmission_layers import expectation_failure as ef


def _payload(**overrides):
    base = {
        "ticker": "XYZ",
        "sector": "Technology",
        "subsector": "Software",
        "estimate_dispersion": 25,
        "revenue_revision_instability": 30,
        "eps_revision_instability": 35,
        "execution_dependency": 45,
        "customer_concentration": 20,
        "product_concentration": 30,
        "margin_expansion_dependency": 40,
        "competitive_intensity": 50,
        "uncertainty_concentration": 45,
        "data_quality_flags": ["audited"],
        "raw_evidence_refs": ["ref:phase_a5:base"],
    }
    base.update(overrides)
    return base


def test_public_api_exports_exist():
    for name in (
        "score_certainty_fragility",
        "build_certainty_fragility_thresholds",
        "build_certainty_fragility_subcomponent_contract",
        "build_certainty_fragility_evidence_summary",
        "build_phase_a5_certainty_fragility_report",
    ):
        assert hasattr(ef, name)


def test_threshold_builder_returns_fixed_deterministic_thresholds():
    a = ef.build_certainty_fragility_thresholds()
    b = ef.build_certainty_fragility_thresholds()
    assert a == b
    assert a["weights"] == {
        "estimate_dispersion_risk_score": 0.20,
        "revision_instability_risk_score": 0.20,
        "execution_dependency_risk_score": 0.25,
        "concentration_risk_score": 0.15,
        "competitive_uncertainty_risk_score": 0.20,
    }


def test_subcomponent_contract_includes_all_required_components():
    contract = ef.build_certainty_fragility_subcomponent_contract()
    assert set(contract["subcomponents"]) == {
        "estimate_dispersion_risk_score",
        "revision_instability_risk_score",
        "execution_dependency_risk_score",
        "concentration_risk_score",
        "competitive_uncertainty_risk_score",
    }


def test_score_deterministic_not_mutating_input_bounded_and_banded():
    payload = _payload()
    before = deepcopy(payload)
    out1 = ef.score_certainty_fragility(payload)
    out2 = ef.score_certainty_fragility(payload)
    assert out1 == out2
    assert payload == before
    assert 0 <= out1["score_value"] <= 100
    assert out1["score_band"] in {"low", "mild", "elevated", "high", "severe"}


def test_low_fragility_and_high_fragility_inputs_map_to_expected_ranges():
    low = ef.score_certainty_fragility(
        _payload(
            estimate_dispersion=10,
            revenue_revision_instability=10,
            eps_revision_instability=12,
            execution_dependency=15,
            margin_expansion_dependency=18,
            customer_concentration=12,
            product_concentration=15,
            competitive_intensity=18,
            uncertainty_concentration=10,
        )
    )
    high = ef.score_certainty_fragility(
        _payload(
            estimate_dispersion=90,
            revenue_revision_instability=85,
            eps_revision_instability=88,
            execution_dependency=95,
            margin_expansion_dependency=92,
            customer_concentration=84,
            product_concentration=86,
            competitive_intensity=90,
            uncertainty_concentration=85,
        )
    )
    assert low["score_band"] in {"low", "mild"}
    assert high["score_band"] in {"high", "severe"}


def test_missing_inputs_use_bounded_fallbacks_and_flags_and_fixed_template():
    out = ef.score_certainty_fragility(
        _payload(
            estimate_dispersion=None,
            revenue_revision_instability=None,
            eps_revision_instability=None,
            execution_dependency=None,
            margin_expansion_dependency=None,
            customer_concentration=None,
            product_concentration=None,
            competitive_intensity=None,
            uncertainty_concentration=None,
        )
    )
    assert 0 <= out["score_value"] <= 100
    assert out["missing_inputs"]
    assert out["explanation_template_id"] == "template_certainty_fragility_limited_data_v1"
    assert out["explanation"].startswith("Certainty Fragility is")


def test_thresholds_triggered_explainable_invariants_and_no_composite_or_autonomous_behavior():
    out = ef.score_certainty_fragility(_payload())
    assert isinstance(out["thresholds_triggered"], list)
    assert out["thresholds_triggered"]
    assert all(out["invariant_flags"].values())

    contracts = ef.build_expectation_failure_score_contracts()
    assert any(c["score_name"] == "certainty_fragility_score" for c in contracts)

    report = ef.build_phase_a5_certainty_fragility_report()
    boundaries = " ".join(report["implementation_boundaries"])
    assert "no_composite_ai_expectation_failure_score" in boundaries
    assert "no_prediction" in boundaries and "optimization" in boundaries and "adaptive" in boundaries


def test_phase_a1_through_a4_regressions_still_pass_contractually():
    assert ef.score_valuation_stretch(_payload(pe_ratio=20, sector_pe_median=18, ev_to_sales=4, sector_ev_to_sales_median=4, forward_revenue_growth=22, market_implied_revenue_growth=20, rule_of_40=45, price_to_gross_profit=9, sector_price_to_gross_profit_median=8))["score_name"] == "valuation_stretch_score"
    assert ef.score_fundamental_support(_payload(fcf_margin=18, sector_fcf_margin_median=12, gross_margin_change=2, operating_margin_change=1, roic=22, sector_roic_median=12, net_debt_to_ebitda=0.5, cash_to_debt=2.5, share_dilution_rate=0.5, cash_burn_rate=-2))["score_name"] == "fundamental_support_score"
    assert ef.score_narrative_saturation(_payload(ai_keyword_density=1.2, sector_ai_keyword_density_median=1.5, news_volume_spike=1.0, sentiment_overheating=25, thematic_crowding=20, retail_attention_spike=1.1, management_ai_mention_intensity=2, etf_theme_inclusion_count=1))["score_name"] == "narrative_saturation_score"
