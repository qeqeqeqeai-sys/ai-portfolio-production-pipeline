from copy import deepcopy

from transmission_layers import expectation_failure as ef


def _payload(**overrides):
    base = {
        "ticker": "ABC",
        "sector": "Technology",
        "subsector": "Software",
        "fcf_margin": 18,
        "sector_fcf_margin_median": 12,
        "gross_margin_change": 2,
        "operating_margin_change": 1,
        "roic": 22,
        "sector_roic_median": 12,
        "net_debt_to_ebitda": 0.5,
        "cash_to_debt": 2.5,
        "share_dilution_rate": 0.5,
        "cash_burn_rate": -2,
        "data_quality_flags": ["audited"],
        "raw_evidence_refs": ["filing:10k"],
    }
    base.update(overrides)
    return base


def test_public_api_exports_exist():
    for name in (
        "score_fundamental_support",
        "build_fundamental_support_thresholds",
        "build_fundamental_support_subcomponent_contract",
        "build_fundamental_support_evidence_summary",
        "build_phase_a3_fundamental_support_report",
    ):
        assert hasattr(ef, name)


def test_thresholds_and_contract_deterministic_and_complete():
    assert ef.build_fundamental_support_thresholds() == ef.build_fundamental_support_thresholds()
    contract = ef.build_fundamental_support_subcomponent_contract()
    assert contract["score_name"] == "fundamental_support_score"
    assert set(contract["subcomponents"]) == {
        "fcf_quality_risk_score",
        "margin_durability_risk_score",
        "capital_efficiency_risk_score",
        "balance_sheet_risk_score",
        "dilution_cash_burn_risk_score",
    }


def test_deterministic_output_and_input_immutability_and_bounds_and_band():
    payload = _payload()
    before = deepcopy(payload)
    out1 = ef.score_fundamental_support(payload)
    out2 = ef.score_fundamental_support(payload)
    assert out1 == out2
    assert payload == before
    assert 0 <= out1["score_value"] <= 100
    assert out1["score_band"] in {"low", "mild", "elevated", "high", "severe"}


def test_strong_and_weak_fundamentals_map_to_expected_risk_levels():
    strong = ef.score_fundamental_support(_payload())
    weak = ef.score_fundamental_support(
        _payload(
            fcf_margin=-5,
            sector_fcf_margin_median=10,
            gross_margin_change=-12,
            operating_margin_change=-8,
            roic=-3,
            sector_roic_median=10,
            net_debt_to_ebitda=5,
            cash_to_debt=0.1,
            share_dilution_rate=12,
            cash_burn_rate=60,
        )
    )
    assert strong["score_band"] in {"low", "mild"}
    assert weak["score_band"] in {"high", "severe"}


def test_missing_inputs_bounded_fallback_and_flags_and_template_and_triggers():
    out = ef.score_fundamental_support(_payload(fcf_margin=None, gross_margin_change=None, operating_margin_change=None, roic=None, net_debt_to_ebitda=None, cash_to_debt=None, share_dilution_rate=None, cash_burn_rate=None))
    assert 0 <= out["score_value"] <= 100
    assert len(out["missing_inputs"]) > 0
    assert out["explanation_template_id"] == "template_fundamental_support_limited_data_v1"
    assert out["explanation"].startswith("Fundamental Support risk is")
    assert isinstance(out["thresholds_triggered"], list) and out["thresholds_triggered"]


def test_invariant_flags_true_and_no_composite_or_prediction_behaviors():
    out = ef.score_fundamental_support(_payload())
    assert all(out["invariant_flags"].values())
    contracts = ef.build_expectation_failure_score_contracts()
    assert any(c["score_name"] == "fundamental_support_score" for c in contracts)
    report = ef.build_phase_a3_fundamental_support_report()
    boundaries = " ".join(report["implementation_boundaries"])
    assert "no_composite_ai_expectation_failure_score" in boundaries
    assert "no_prediction" in boundaries and "optimization" in boundaries and "adaptive" in boundaries
