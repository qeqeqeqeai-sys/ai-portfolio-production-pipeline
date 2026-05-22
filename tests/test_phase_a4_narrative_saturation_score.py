from copy import deepcopy

from transmission_layers import expectation_failure as ef


def _payload(**overrides):
    base = {
        "ticker": "NVDA",
        "sector": "Technology",
        "subsector": "Semiconductors",
        "ai_keyword_density": 9.0,
        "sector_ai_keyword_density_median": 3.0,
        "news_volume_spike": 2.8,
        "sentiment_overheating": 86.0,
        "thematic_crowding": 84.0,
        "retail_attention_spike": 2.4,
        "management_ai_mention_intensity": 9.0,
        "etf_theme_inclusion_count": 12,
        "data_quality_flags": ["audited_inputs"],
        "raw_evidence_refs": ["ref:narrative:2026q2"],
    }
    base.update(overrides)
    return base


def test_public_api_exports_exist():
    for name in (
        "score_narrative_saturation",
        "build_narrative_saturation_thresholds",
        "build_narrative_saturation_subcomponent_contract",
        "build_narrative_saturation_evidence_summary",
        "build_phase_a4_narrative_saturation_report",
    ):
        assert hasattr(ef, name)


def test_threshold_builder_and_subcomponent_contract_deterministic_and_complete():
    assert ef.build_narrative_saturation_thresholds() == ef.build_narrative_saturation_thresholds()
    contract = ef.build_narrative_saturation_subcomponent_contract()
    assert set(contract["subcomponents"]) == {
        "ai_hype_intensity_score",
        "narrative_concentration_score",
        "sentiment_overheating_score",
        "thematic_crowding_score",
        "excessive_optimism_score",
    }


def test_scoring_deterministic_input_immutable_bounded_band_contract():
    payload = _payload()
    before = deepcopy(payload)
    out1 = ef.score_narrative_saturation(payload)
    out2 = ef.score_narrative_saturation(payload)
    assert out1 == out2
    assert payload == before
    assert 0 <= out1["score_value"] <= 100
    assert out1["score_band"] in {"low", "mild", "elevated", "high", "severe"}


def test_low_and_high_narrative_saturation_levels_map_to_expected_bands():
    low = ef.score_narrative_saturation(
        _payload(
            ai_keyword_density=0.5,
            sector_ai_keyword_density_median=2.0,
            news_volume_spike=0.8,
            management_ai_mention_intensity=0.5,
            sentiment_overheating=15,
            thematic_crowding=18,
            etf_theme_inclusion_count=0,
            retail_attention_spike=0.7,
        )
    )
    high = ef.score_narrative_saturation(_payload())
    assert low["score_band"] in {"low", "mild"}
    assert high["score_band"] in {"high", "severe"}


def test_missing_inputs_fallback_thresholds_explanation_invariants_and_boundaries():
    out = ef.score_narrative_saturation(
        _payload(
            ai_keyword_density=None,
            news_volume_spike=None,
            management_ai_mention_intensity=None,
            sentiment_overheating=None,
            thematic_crowding=None,
            etf_theme_inclusion_count=None,
            retail_attention_spike=None,
        )
    )
    assert 0 <= out["score_value"] <= 100
    assert out["missing_inputs"]
    assert out["thresholds_triggered"]
    assert out["explanation_template_id"] == "template_narrative_saturation_limited_data_v1"
    assert out["explanation"].startswith("Narrative Saturation is")
    assert all(out["invariant_flags"].values())

    contracts = ef.build_expectation_failure_score_contracts()
    assert any(c["score_name"] == "narrative_saturation_score" for c in contracts)

    report = ef.build_phase_a4_narrative_saturation_report()
    boundaries = " ".join(report["implementation_boundaries"])
    assert "no_composite_ai_expectation_failure_score" in boundaries
    assert "no_prediction" in boundaries and "optimization" in boundaries and "adaptive" in boundaries
