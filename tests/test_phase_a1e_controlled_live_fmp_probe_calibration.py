from transmission_layers.expectation_failure.phase_a1_curated_observational_expansion import (
    build_phase_a1e_live_probe_configuration,
    build_phase_a1e_probe_candidate_selection,
    build_phase_a1e_live_fmp_fetcher,
    execute_phase_a1e_live_fmp_probe,
    build_phase_a1e_probe_calibration_summary,
    build_phase_a1e_supervisor_review,
    build_phase_a1e_markdown_report,
    certify_phase_a_observational_expansion_boundary,
)


def mock_good_fetcher(ticker, endpoint):
    return {"ok": True, "http_status": 200, "endpoint_status": "ok", "error_type": "none", "payload_shape": "list", "record_count": 2, "has_required_payload": True}


def mock_control_fail_fetcher(ticker, endpoint):
    ctrls = {"MSFT", "AAPL", "NVDA", "AMZN", "GOOGL", "META", "AMD", "ORCL"}
    if ticker in ctrls:
        return {"ok": False, "http_status": 404, "endpoint_status": "http_404", "error_type": "not_found", "payload_shape": "none", "record_count": 0, "has_required_payload": False}
    return mock_good_fetcher(ticker, endpoint)


def test_api_existence_and_bounds():
    assert callable(build_phase_a1e_live_probe_configuration)
    assert callable(build_phase_a1e_live_fmp_fetcher)
    cfg = build_phase_a1e_live_probe_configuration(99, probe_mode="mock")
    assert cfg["max_entities"] == 40
    assert len(build_phase_a1e_probe_candidate_selection(40)) <= 40


def test_mock_mode_not_live_executed():
    out = execute_phase_a1e_live_fmp_probe(fetcher=mock_good_fetcher, max_entities=20, probe_mode="mock")
    assert out["live_probe_executed"] is False
    assert out["fetcher_type"] == "mock_fetcher"
    assert out["run_level_status"] == "LIVE_PROBE_MOCK_ONLY"


def test_live_mode_missing_key_fails_closed(monkeypatch):
    monkeypatch.delenv("FMP_API_KEY", raising=False)
    monkeypatch.delenv("FINANCIAL_MODELING_PREP_API_KEY", raising=False)
    out = execute_phase_a1e_live_fmp_probe(max_entities=10, probe_mode="live")
    assert out["diagnostics"]["api_key_present"] is False
    assert out["run_level_status"] == "LIVE_PROBE_NOT_CONFIGURED"


def test_control_failure_invalidates_and_suppresses_non_viable():
    out = execute_phase_a1e_live_fmp_probe(fetcher=mock_control_fail_fetcher, max_entities=20, probe_mode="live")
    assert out["run_level_status"] in {"LIVE_PROBE_INVALID_ENDPOINT_OR_AUTH_FAILURE", "LIVE_PROBE_INFRASTRUCTURE_FAILURE"}
    assert all(r["continuity_quality"] == "NOT_CLASSIFIED_DUE_TO_INVALID_PROBE" for r in out["results"])


def test_valid_live_shaped_and_governance_and_no_key_leak():
    out = execute_phase_a1e_live_fmp_probe(fetcher=mock_good_fetcher, max_entities=20, probe_mode="live")
    summary = build_phase_a1e_probe_calibration_summary(out)
    assert out["run_level_status"] == "LIVE_PROBE_VALID"
    assert summary["strong_continuity_count"] >= 1
    review = build_phase_a1e_supervisor_review(fetcher=mock_good_fetcher, max_entities=20, probe_mode="live")
    md = build_phase_a1e_markdown_report(review)
    assert "api_key" in md
    assert "sk-" not in md
    flags = certify_phase_a_observational_expansion_boundary()
    assert flags["observational_expansion_only"] is True
    assert flags["schema_expansion_enabled"] is False
    assert flags["direct_sql_allowed"] is False
    cfg = review["probe_configuration"]
    assert cfg["persistence_allowed"] is False
    assert cfg["supabase_writes_allowed"] is False
    assert cfg["sql_writes_allowed"] is False
