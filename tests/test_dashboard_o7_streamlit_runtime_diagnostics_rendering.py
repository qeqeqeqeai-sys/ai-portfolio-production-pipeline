from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    load_streamlit_dashboard_snapshot,
)


class DummyClient:
    pass


def _fallback_payload():
    return {
        "dashboard_entity_facts": [{"run_id": "fallback"}],
        "dashboard_subsector_facts": [],
        "dashboard_alert_facts": [],
        "dashboard_replay_facts": [],
        "dashboard_benchmark_facts": [],
        "dashboard_evidence_facts": [],
        "dashboard_report_metadata": {"run_id": "fallback", "run_date_sgt": "2026-01-01"},
        "dashboard_export_manifest": {"checksum": "fallback"},
    }


def _healthy_snapshot():
    base = {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20"}]}
    return {
        "entity_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "entity_name": "RealCo", "ticker": "REAL", "subsector": "Infra", "composite_score": 75.0, "relative_fragility_band": "elevated", "alert_state": "watch", "benchmark_relative_label": "neutral", "evidence_quality_flag": "sufficient", "certification_status": "certified", "replay_checksum": "chk"}]},
        "subsector_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "subsector": "Infra", "entity_count": 1, "avg_composite_score": 75.0, "fragile_entity_count": 1, "alert_entity_count": 1, "subsector_fragility_band": "elevated", "evidence_quality_summary": "sufficient", "replay_checksum": "chk"}]},
        "alert_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "alert_state": "watch", "alert_severity_band": "medium", "active_alert_flag": True, "dominant_alert_driver": "volatility", "evidence_quality_flag": "sufficient", "replay_checksum": "chk"}]},
        "replay_facts": {"status": "ok", "rows": [{"run_id": "run-real", "replay_date_sgt": "2026-05-19", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "composite_score": 71.0, "fragility_band": "elevated", "alert_state": "watch", "deterioration_label": "flat", "replay_sequence": 1, "replay_checksum": "chk"}]},
        "benchmark_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "benchmark_id": "QQQ", "entity_fragility_score": 75.0, "benchmark_fragility_score": 70.0, "relative_gap": 5.0, "relative_gap_band": "normal", "benchmark_relative_label": "neutral", "outlier_flag": False, "replay_checksum": "chk"}]},
        "evidence_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "evidence_id": "EV1", "evidence_type": "metric", "source_metric": "x", "source_value": 1.0, "normalized_score": 0.8, "quality_flag": "sufficient", "evidence_chain_position": 1, "template_id": "t1", "replay_checksum": "chk"}]},
        "certification_metadata": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "certification_status": "certified", "report_type": "institutional_dashboard", "export_manifest_checksum": "manifest-1"}]},
    }


def _assert_populated(d):
    for k in ["runtime_mode", "payload_source", "normalization_status", "credentials_present", "client_resolved", "snapshot_loaded", "degraded_sections", "snapshot_section_statuses", "error_type", "error_message_short"]:
        assert k in d


def test_diagnostics_rendering_compatibility_all_paths_and_no_secret_leakage():
    out_fallback = load_streamlit_dashboard_snapshot(
        runtime_config=build_streamlit_supabase_runtime_config(supabase_url=None, supabase_key=None),
        fallback_payload=_fallback_payload(),
    )
    d_fallback = out_fallback["runtime_diagnostics"]
    _assert_populated(d_fallback)
    assert out_fallback["payload"]["runtime_diagnostics"]["runtime_mode"] == "fallback_demo_mode"

    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter as o6
    orig = o6.build_dashboard_supabase_snapshot
    degraded = _healthy_snapshot()
    degraded["alert_facts"]["status"] = "degraded"
    o6.build_dashboard_supabase_snapshot = lambda *_a, **_k: degraded
    try:
        out_degraded = load_streamlit_dashboard_snapshot(
            runtime_config=build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k"),
            fallback_payload=_fallback_payload(),
            client=DummyClient(),
        )
    finally:
        o6.build_dashboard_supabase_snapshot = orig
    d_degraded = out_degraded["runtime_diagnostics"]
    _assert_populated(d_degraded)
    assert d_degraded["runtime_mode"] == "degraded_data_loading_mode"

    o6.build_dashboard_supabase_snapshot = lambda *_a, **_k: _healthy_snapshot()
    try:
        secret = "sk-super-secret-key"
        out_healthy = load_streamlit_dashboard_snapshot(
            runtime_config=build_streamlit_supabase_runtime_config(supabase_url="https://example.supabase.co", supabase_key=secret),
            fallback_payload=_fallback_payload(),
            client=DummyClient(),
        )
    finally:
        o6.build_dashboard_supabase_snapshot = orig
    d_healthy = out_healthy["payload"]["runtime_diagnostics"]
    _assert_populated(d_healthy)
    assert d_healthy["runtime_mode"] == "read_only_supabase_mode"
    lowered = str(d_healthy).lower()
    assert secret.lower() not in lowered
    assert "supabase_key" not in lowered
