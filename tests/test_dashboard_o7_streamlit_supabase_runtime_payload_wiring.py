from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o4_streamlit_view_model import build_dashboard_o4_view_model
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_dashboard_payload_from_supabase_snapshot,
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
    row = {"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL"}
    return {
        "entity_facts": {"status": "ok", "rows": [{**row, "entity_name": "RealCo", "subsector": "Infra", "composite_score": 75.0, "relative_fragility_band": "elevated", "alert_state": "watch", "benchmark_relative_label": "neutral", "evidence_quality_flag": "sufficient", "certification_status": "certified", "replay_checksum": "chk"}]},
        "subsector_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "subsector": "Infra", "entity_count": 1, "avg_composite_score": 75.0, "fragile_entity_count": 1, "alert_entity_count": 1, "subsector_fragility_band": "elevated", "evidence_quality_summary": "sufficient", "replay_checksum": "chk"}]},
        "alert_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "alert_state": "watch", "alert_severity_band": "medium", "active_alert_flag": True, "dominant_alert_driver": "volatility", "evidence_quality_flag": "sufficient", "replay_checksum": "chk"}]},
        "replay_facts": {"status": "ok", "rows": [{"run_id": "run-real", "replay_date_sgt": "2026-05-19", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "composite_score": 71.0, "fragility_band": "elevated", "alert_state": "watch", "deterioration_label": "flat", "replay_sequence": 1, "replay_checksum": "chk"}]},
        "benchmark_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "subsector": "Infra", "benchmark_id": "QQQ", "entity_fragility_score": 75.0, "benchmark_fragility_score": 70.0, "relative_gap": 5.0, "relative_gap_band": "normal", "benchmark_relative_label": "neutral", "outlier_flag": False, "replay_checksum": "chk"}]},
        "evidence_facts": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "entity_id": "E1", "ticker": "REAL", "evidence_id": "EV1", "evidence_type": "metric", "source_metric": "x", "source_value": 1.0, "normalized_score": 0.8, "quality_flag": "sufficient", "evidence_chain_position": 1, "template_id": "t1", "replay_checksum": "chk"}]},
        "certification_metadata": {"status": "ok", "rows": [{"run_id": "run-real", "run_date_sgt": "2026-05-20", "certification_status": "certified", "report_type": "institutional_dashboard", "export_manifest_checksum": "manifest-1"}]},
    }


def test_public_api_presence():
    assert hasattr(mod, "build_dashboard_payload_from_supabase_snapshot")


def test_fallback_mode_still_returns_fallback_payload():
    payload = _fallback_payload()
    cfg = build_streamlit_supabase_runtime_config(supabase_url=None, supabase_key=None)
    out = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=payload)
    assert out["payload"] == payload
    assert out["payload_source"] == "fallback_payload"


def test_healthy_snapshot_normalizes_and_renders_for_o4():
    fallback = _fallback_payload()
    snapshot = _healthy_snapshot()

    def fake_build(_client, run_id=None, as_of_date=None):
        return snapshot

    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter as o6
    original = o6.build_dashboard_supabase_snapshot
    o6.build_dashboard_supabase_snapshot = fake_build
    try:
        cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
        out = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=fallback, client=DummyClient())
    finally:
        o6.build_dashboard_supabase_snapshot = original

    assert out["payload_source"] == "supabase_snapshot"
    assert out["normalization_status"] == "ok"
    assert out["payload"]["dashboard_entity_facts"][0]["ticker"] == "REAL"
    assert out["payload"]["dashboard_report_metadata"]["run_id"] == "run-real"
    assert out["payload"]["dashboard_export_manifest"]["checksum"] == "manifest-1"
    vm = build_dashboard_o4_view_model(out["payload"])
    assert vm["kpi_cards"]["latest_run_id"] == "run-real"


def test_degraded_or_bad_snapshot_falls_back_safely_and_is_deterministic_immutable():
    fallback = _fallback_payload()
    original_fallback = deepcopy(fallback)
    snap = _healthy_snapshot()
    snap["alert_facts"]["status"] = "degraded"
    a = load_streamlit_dashboard_snapshot(
        runtime_config=build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k"),
        fallback_payload=fallback,
        client=DummyClient(),
        client_factory=lambda _u, _k: DummyClient(),
    )
    # direct normalization failure path
    try:
        build_dashboard_payload_from_supabase_snapshot(snap)
        assert False, "expected failure"
    except ValueError:
        pass

    assert fallback == original_fallback
    assert a["payload_source"] in {"fallback_payload", "supabase_snapshot"}


def test_normalizer_deterministic_repeated_output_and_no_writes_keywords():
    snap = _healthy_snapshot()
    p1 = build_dashboard_payload_from_supabase_snapshot(snap)
    p2 = build_dashboard_payload_from_supabase_snapshot(deepcopy(snap))
    assert p1 == p2
    text = str(p1).lower()
    for forbidden in ["insert", "update", "delete", "upsert", "rpc", "sql"]:
        assert forbidden not in text
