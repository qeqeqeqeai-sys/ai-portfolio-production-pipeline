from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o1_dashboard_view_model,
    build_o2_dashboard_view_model,
    build_o3_dashboard_view_model,
    build_o3_expectation_fragility_inputs,
    build_o3_market_evidence_cards,
    build_o3_market_observation_inventory,
    build_o3_real_market_semantic_inputs_report,
    build_o3_semantic_category_summary,
    build_o3_semantic_evidence_records,
    certify_o3_real_market_semantic_inputs,
)


OBS = [
    {"observation_id": "1", "as_of_date": "2026-01-01", "symbol": "AAA", "entity_name": "A Co", "sector": "Tech", "subsector": "AI", "metric_name": "pe", "percentile": 110, "source_name": "src", "checksum": "x"},
    {"observation_id": "2", "as_of_date": "2026-01-01", "symbol": "AAA", "entity_name": "A Co", "sector": "Tech", "subsector": "AI", "metric_name": "vix", "z_score": 1.2, "source_name": "src", "checksum": "y"},
    {"observation_id": "3", "as_of_date": "2026-01-02", "symbol": "BBB", "entity_name": "B Co", "sector": "Fin", "subsector": "Banks", "metric_name": "unknown_metric", "metric_value": "bad", "source_name": "", "checksum": ""},
]


def test_public_api_presence():
    assert callable(build_o3_market_observation_inventory)
    assert callable(build_o3_semantic_evidence_records)
    assert callable(build_o3_expectation_fragility_inputs)
    assert callable(build_o3_market_evidence_cards)
    assert callable(build_o3_semantic_category_summary)
    assert callable(build_o3_dashboard_view_model)
    assert callable(certify_o3_real_market_semantic_inputs)
    assert callable(build_o3_real_market_semantic_inputs_report)


def test_determinism_checksum_ordering_and_mapping():
    r1 = build_o3_semantic_evidence_records(OBS)
    r2 = build_o3_semantic_evidence_records(OBS)
    assert r1 == r2
    assert [x["observation_id"] for x in r1] == ["1", "2", "3"]
    assert r1[0]["semantic_category"] == "VALUATION_STRETCH"
    assert r1[1]["semantic_category"] == "VOLATILITY_STRESS"


def test_scoring_paths():
    r = build_o3_semantic_evidence_records(OBS)
    assert r[0]["normalized_score"] == 100.0
    assert r[1]["normalized_score"] == 75.0
    assert r[2]["evidence_quality"] == "DEGRADED_MISSING_NUMERIC_VALUE"


def test_inventory_states():
    assert build_o3_market_observation_inventory([])["inventory_state"] == "O3_INVENTORY_BLOCKED"
    inv_deg = build_o3_market_observation_inventory(OBS)
    assert inv_deg["inventory_state"] == "O3_INVENTORY_DEGRADED"
    inv = build_o3_market_observation_inventory(OBS)
    assert "observed_metric_names" in inv and "observed_metric_categories" not in inv
    ready = [dict(x, source_name="s", checksum="c", metric_name="pe", percentile=40) for x in OBS[:2]]
    assert build_o3_market_observation_inventory(ready)["inventory_state"] == "O3_INVENTORY_READY"


def test_aggregation_cards_summary_dashboard_certification_and_immutability():
    obs = deepcopy(OBS)
    inputs = build_o3_expectation_fragility_inputs(obs)
    assert inputs["entity_expectation_fragility_inputs"]
    cards = build_o3_market_evidence_cards(obs)
    assert all(set(["title", "state", "score", "evidence_count", "interpretation"]).issubset(v.keys()) for v in cards.values())
    summary = build_o3_semantic_category_summary(obs)
    assert "category_counts" in summary and "highest_pressure_category" in summary
    vm = build_o3_dashboard_view_model(obs)
    for k in ["market_observation_inventory", "semantic_evidence_records", "expectation_fragility_inputs", "market_evidence_cards", "semantic_category_summary", "certification_summary"]:
        assert k in vm
    cert = certify_o3_real_market_semantic_inputs(obs)
    assert cert["certification_status"] == "O3_MARKET_SEMANTICS_DEGRADED"
    assert "price prediction" in cert["forbidden_capability_check"]
    blocked = certify_o3_real_market_semantic_inputs([])
    assert blocked["certification_status"] == "O3_MARKET_SEMANTICS_BLOCKED"
    ready_obs = [{"observation_id": "9", "as_of_date": "2026-01-01", "symbol": "C", "metric_name": "pe", "percentile": 45, "source_name": "s", "checksum": "c"}]
    assert certify_o3_real_market_semantic_inputs(ready_obs)["certification_status"] == "O3_MARKET_SEMANTICS_READY"
    assert obs == OBS


def test_report_language_and_o1_o2_non_regression():
    text = build_o3_real_market_semantic_inputs_report(OBS).lower()
    assert "objective" in text
    assert "final interpretation" in text
    assert isinstance(build_o1_dashboard_view_model(), dict)
    assert isinstance(build_o2_dashboard_view_model([]), dict)
