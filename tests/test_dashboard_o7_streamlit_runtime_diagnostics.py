from copy import deepcopy

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
    return {
        "entity_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "entity_name": "RealCo", "ticker": "REAL", "subsector": "Infra", "composite_score": 75.0, "relative_fragility_band": "elevated", "alert_state": "watch", "benchmark_relative_label": "neutral", "evidence_quality_flag": "sufficient", "certification_status": "certified", "replay_checksum": "chk"}]},
        "subsector_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "subsector": "Infra", "entity_count": 1, "avg_composite_score": 75.0, "fragile_entity_count": 1, "alert_entity_count": 1, "subsector_fragility_band": "elevated", "evidence_quality_summary": "sufficient", "replay_checksum": "chk"}]},
        "alert_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "alert_state": "watch", "alert_severity_band": "medium", "active_alert_flag": True, "dominant_alert_driver": "volatility", "evidence_quality_flag": "sufficient", "replay_checksum": "chk"}]},
        "replay_facts": {"status": "ok", "rows": [{"run_id": "run-real", "replay_date_sgt": "2026-05-19", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "composite_score": 71.0, "fragility_band": "elevated", "alert_state": "watch", "deterioration_label": "flat", "replay_sequence": 1, "replay_checksum": "chk"}]},
        "benchmark_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "benchmark_id": "QQQ", "entity_fragility_score": 75.0, "benchmark_fragility_score": 70.0, "relative_gap": 5.0, "relative_gap_band": "normal", "benchmark_relative_label": "neutral", "outlier_flag": False, "replay_checksum": "chk"}]},
        "evidence_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "evidence_id": "EV1", "evidence_type": "metric", "source_metric": "x", "source_value": 1.0, "normalized_score": 0.8, "quality_flag": "sufficient", "evidence_chain_position": 1, "template_id": "t1", "replay_checksum": "chk"}]},
        "certification_metadata": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "certification_status": "certified", "report_type": "institutional_dashboard", "export_manifest_checksum": "manifest-1"}]},
    }


def test_missing_credentials_diagnostics():
    out = load_streamlit_dashboard_snapshot(runtime_config=build_streamlit_supabase_runtime_config(supabase_url=None, supabase_key=None), fallback_payload=_fallback_payload())
    d = out["runtime_diagnostics"]
    assert out["mode"] == "fallback_demo_mode"
    assert d["credentials_present"] is False
    assert d["client_resolved"] is False
    assert d["snapshot_loaded"] is False


def test_client_creation_failure_diagnostics():
    def bad_factory(_url, _key):
        raise RuntimeError("cannot create")

    out = load_streamlit_dashboard_snapshot(runtime_config=build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k"), fallback_payload=_fallback_payload(), client_factory=bad_factory)
    d = out["runtime_diagnostics"]
    assert out["mode"] == "degraded_data_loading_mode"
    assert d["error_type"] == "RuntimeError"
    assert "cannot create" in (d["error_message_short"] or "")


def test_degraded_snapshot_diagnostics():
    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter as o6

    snapshot = _healthy_snapshot()
    snapshot["alert_facts"]["status"] = "degraded"

    orig = o6.build_dashboard_supabase_snapshot
    o6.build_dashboard_supabase_snapshot = lambda *_args, **_kwargs: snapshot
    try:
        out = load_streamlit_dashboard_snapshot(runtime_config=build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k"), fallback_payload=_fallback_payload(), client=DummyClient())
    finally:
        o6.build_dashboard_supabase_snapshot = orig

    d = out["runtime_diagnostics"]
    assert out["mode"] == "degraded_data_loading_mode"
    assert "alert_facts" in d["degraded_sections"]
    assert d["normalization_status"] == "snapshot_degraded"


def test_normalization_failure_diagnostics_and_fallback_safe_and_immutable_input():
    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter as o6

    fallback = _fallback_payload()
    original = deepcopy(fallback)
    snapshot = _healthy_snapshot()

    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime as o7

    orig = o6.build_dashboard_supabase_snapshot
    orig_norm = o7.build_dashboard_payload_from_supabase_snapshot
    o6.build_dashboard_supabase_snapshot = lambda *_args, **_kwargs: snapshot
    o7.build_dashboard_payload_from_supabase_snapshot = lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("forced_normalization_error"))
    try:
        out = load_streamlit_dashboard_snapshot(runtime_config=build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k"), fallback_payload=fallback, client=DummyClient())
    finally:
        o6.build_dashboard_supabase_snapshot = orig
        o7.build_dashboard_payload_from_supabase_snapshot = orig_norm

    d = out["runtime_diagnostics"]
    assert out["mode"] == "degraded_data_loading_mode"
    assert out["payload_source"] == "fallback_payload"
    assert d["normalization_status"] == "failed"
    assert fallback == original


def test_healthy_snapshot_diagnostics_and_no_secret_leakage():
    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter as o6

    secret = "sk-super-secret-key"
    cfg = build_streamlit_supabase_runtime_config(supabase_url="https://example.supabase.co", supabase_key=secret)
    orig = o6.build_dashboard_supabase_snapshot
    o6.build_dashboard_supabase_snapshot = lambda *_args, **_kwargs: _healthy_snapshot()
    try:
        out = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=_fallback_payload(), client=DummyClient())
    finally:
        o6.build_dashboard_supabase_snapshot = orig

    d = out["runtime_diagnostics"]
    assert out["mode"] == "read_only_supabase_mode"
    assert d["payload_source"] == "supabase_snapshot"
    assert d["normalization_status"] == "ok"
    assert d["degraded_sections"] == []
    assert "dashboard_entity_facts" in d["expected_tables"]
    lowered = str(d).lower()
    assert "supabase_key" not in lowered
    assert secret.lower() not in lowered
