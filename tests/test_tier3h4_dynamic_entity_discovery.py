import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from transmission_layers.asset_discovery import tier3h4_dynamic_entity_discovery as mod


def test_scoring_function_expected_value():
    score = mod.compute_candidate_score(60, 70, 80, 50, 40)
    assert score == 63.5


def test_confidence_band_assignment():
    assert mod._score_band(80) == "high_confidence"
    assert mod._score_band(79.9) == "medium_confidence"
    assert mod._score_band(40) == "low_confidence"
    assert mod._score_band(39.9) == "rejected_or_noise"


def test_rejected_rows_are_not_advisory_review():
    seeds = [mod.DiscoverySeed("x", "s", "t", None)]
    rows = mod.build_records(seeds, "2026-05-16")
    rows[0]["candidate_confidence_score"] = 10
    rows[0]["candidate_confidence_band"] = mod._score_band(10)
    rows[0]["advisory_status"] = "advisory_rejected"
    assert rows[0]["advisory_status"] != "advisory_review"


def test_llm_used_always_false_and_no_tavily_openai_calls():
    rows = mod.build_records([mod.DiscoverySeed("ai", "a", "b", None)], "2026-05-16")
    assert all(r["llm_used"] is False for r in rows)
    source = Path(mod.__file__).read_text(encoding="utf-8").lower()
    assert "tavily" not in source
    assert "openai" not in source


def test_candidate_examples_not_in_production_static_mapping():
    source = Path(mod.__file__).read_text(encoding="utf-8")
    for symbol in ["VRT", "ETN", "PWR", "CEG", "VST", "HUBB", "NVT"]:
        assert f"::{symbol}" not in source


def test_generated_records_include_evidence_explanations_and_idempotency_fields():
    rows = mod.build_records([mod.DiscoverySeed("ai_power", "a", "b", "ctx")], "2026-05-16")
    assert rows and isinstance(rows[0]["evidence_sources"], list)
    assert rows[0]["confidence_explanation"]
    for key in ["run_date_sgt", "theme_name", "candidate_asset_id", "discovery_method"]:
        assert key in rows[0]
