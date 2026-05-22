from copy import deepcopy

from transmission_layers import expectation_failure as ef


def _payload(**overrides):
    base = {
        "ticker": "NVDA",
        "sector": "Technology",
        "subsector": "Semiconductors",
        "forward_pe": 60.0,
        "sector_forward_pe_median": 25.0,
        "ev_sales": 30.0,
        "sector_ev_sales_median": 8.0,
        "ev_ebitda": 45.0,
        "sector_ev_ebitda_median": 14.0,
        "historical_valuation_percentile": 94.0,
        "revenue_growth_expectation": 28.0,
        "sector_revenue_growth_median": 10.0,
        "data_quality_flags": ["audited_inputs"],
        "raw_evidence_refs": ["ref:valuation:2026q2"],
    }
    base.update(overrides)
    return base


def test_public_api_exports_exist():
    for name in [
        "score_valuation_stretch",
        "build_valuation_stretch_thresholds",
        "build_valuation_stretch_subcomponent_contract",
        "build_valuation_stretch_evidence_summary",
        "build_phase_a2_valuation_stretch_report",
    ]:
        assert hasattr(ef, name)


def test_threshold_builder_deterministic():
    assert ef.build_valuation_stretch_thresholds() == ef.build_valuation_stretch_thresholds()


def test_subcomponent_contract_has_required_five():
    contract = ef.build_valuation_stretch_subcomponent_contract()
    assert set(contract["subcomponents"]) == {
        "forward_pe_premium_score",
        "ev_sales_premium_score",
        "ev_ebitda_premium_score",
        "historical_percentile_score",
        "growth_expectation_intensity_score",
    }


def test_scoring_is_deterministic_across_calls_and_input_immutable():
    payload = _payload()
    baseline = deepcopy(payload)
    out1 = ef.score_valuation_stretch(payload)
    out2 = ef.score_valuation_stretch(payload)
    assert out1 == out2
    assert payload == baseline


def test_score_bounded_and_band_contract():
    out = ef.score_valuation_stretch(_payload())
    assert 0 <= out["score_value"] <= 100
    assert out["score_band"] in {"low", "mild", "elevated", "high", "severe"}


def test_high_valuation_premium_produces_high_or_severe():
    out = ef.score_valuation_stretch(_payload())
    assert out["score_band"] in {"high", "severe"}


def test_low_valuation_premium_produces_low_or_mild():
    out = ef.score_valuation_stretch(
        _payload(
            forward_pe=12,
            sector_forward_pe_median=20,
            ev_sales=3,
            sector_ev_sales_median=8,
            ev_ebitda=7,
            sector_ev_ebitda_median=12,
            historical_valuation_percentile=35,
            revenue_growth_expectation=8,
            sector_revenue_growth_median=12,
        )
    )
    assert out["score_band"] in {"low", "mild"}


def test_missing_inputs_fallback_and_flags():
    out = ef.score_valuation_stretch(_payload(forward_pe=None, sector_forward_pe_median=None))
    assert 0 <= out["score_value"] <= 100
    assert "forward_pe_premium_score" in out["missing_inputs"]


def test_thresholds_triggered_and_explanation_template_and_invariants():
    out = ef.score_valuation_stretch(_payload())
    assert len(out["thresholds_triggered"]) == 5
    assert all(":" in trigger for trigger in out["thresholds_triggered"])
    assert out["explanation_template_id"].startswith("template_valuation_stretch")
    assert out["explanation"].startswith("Valuation Stretch is")
    assert all(out["invariant_flags"].values())


def test_no_composite_or_prediction_modules_added():
    report = ef.build_phase_a2_valuation_stretch_report()
    boundaries = " ".join(report["implementation_boundaries"])
    assert "no_composite" in boundaries
    assert "no_prediction" in boundaries


def test_phase_a1_contracts_still_pass_shape():
    contracts = ef.build_expectation_failure_score_contracts()
    assert any(c["score_name"] == "valuation_stretch_score" for c in contracts)
