from apps import streamlit_expectation_failure_dashboard as app


def test_cache_schema_version_passed_into_cached_loader(monkeypatch):
    captured = {}

    def fake_cached(runtime_config, fallback_payload, cache_schema_version):
        captured["cache_schema_version"] = cache_schema_version
        return {"mode": "fallback_demo_mode", "payload": {}, "runtime_diagnostics": {}}

    monkeypatch.setattr(app, "_load_runtime_snapshot_cached", fake_cached)
    app._load_runtime_snapshot(runtime_config={}, fallback_payload={}, bypass_runtime_cache=False)
    assert captured["cache_schema_version"] == app.RUNTIME_CACHE_SCHEMA_VERSION


def test_bypass_path_calls_uncached_loader(monkeypatch):
    calls = {"uncached": 0, "cached": 0}

    def fake_cached(*_args, **_kwargs):
        calls["cached"] += 1
        return {}

    def fake_uncached(*_args, **_kwargs):
        calls["uncached"] += 1
        return {"mode": "fallback_demo_mode", "payload": {}}

    monkeypatch.setattr(app, "_load_runtime_snapshot_cached", fake_cached)
    monkeypatch.setattr(app, "load_streamlit_dashboard_snapshot", fake_uncached)

    app._load_runtime_snapshot(runtime_config={}, fallback_payload={}, bypass_runtime_cache=True)
    assert calls["uncached"] == 1
    assert calls["cached"] == 0


def test_empty_diagnostics_are_synthesized_and_source_populated():
    runtime_snapshot = {
        "mode": "degraded_data_loading_mode",
        "payload_source": "supabase",
        "normalization_status": "partial",
        "status": "degraded",
        "error": "sample error",
        "payload": {"dashboard_entity_facts": [{"run_id": "x"}]},
    }

    diagnostics, source = app._synthesize_runtime_diagnostics(runtime_snapshot)

    assert source == "synthesized_from_runtime_snapshot"
    assert diagnostics["diagnostics_source"] == "synthesized_from_runtime_snapshot"
    assert diagnostics["runtime_mode"] == "degraded_data_loading_mode"
    assert diagnostics["payload_source"] == "supabase"
    assert diagnostics["normalization_status"] == "partial"
    assert diagnostics["error_message_short"] == "sample error"
    assert diagnostics["expected_tables"] == ["dashboard_entity_facts"]


def test_missing_runtime_snapshot_fallback_and_required_keys_present():
    diagnostics, source = app._synthesize_runtime_diagnostics(None)

    assert source == "missing_runtime_snapshot"
    assert diagnostics["diagnostics_source"] == "missing_runtime_snapshot"
    for key in [
        "runtime_mode",
        "payload_source",
        "normalization_status",
        "credentials_present",
        "client_resolved",
        "snapshot_loaded",
        "degraded_sections",
        "snapshot_section_statuses",
        "error_type",
        "error_message_short",
        "expected_tables",
    ]:
        assert key in diagnostics


def test_no_secret_leakage_in_synthesized_diagnostics():
    secret = "sk-super-secret"
    runtime_snapshot = {
        "mode": "fallback_demo_mode",
        "status": "error",
        "error": "runtime unavailable",
        "payload": {"dashboard_entity_facts": []},
        "supabase_key": secret,
    }

    diagnostics, _ = app._synthesize_runtime_diagnostics(runtime_snapshot)
    lowered = str(diagnostics).lower()
    assert secret.lower() not in lowered
    assert "supabase_key" not in lowered
