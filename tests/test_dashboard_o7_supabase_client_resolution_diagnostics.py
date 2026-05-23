from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    load_streamlit_dashboard_snapshot,
    resolve_streamlit_supabase_client,
)


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


class DummyClient:
    pass


def test_credentials_missing_client_unresolved():
    cfg = build_streamlit_supabase_runtime_config(supabase_url=None, supabase_key=None)
    result = resolve_streamlit_supabase_client(cfg)
    assert result["client_resolved"] is False
    assert result["client_factory_source"] == "unavailable"


def test_supabase_package_unavailable_clear_error_type():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
    result = resolve_streamlit_supabase_client(cfg)
    assert result["client_resolved"] is False
    assert result["supabase_package_available"] is False
    assert result["client_error_type"] in {"ModuleNotFoundError", "ImportError"}


def test_injected_factory_success():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
    result = resolve_streamlit_supabase_client(cfg, client_factory=lambda _u, _k: DummyClient())
    assert result["client_resolved"] is True
    assert result["client_factory_source"] == "injected_factory"


def test_injected_factory_failure_sets_error_type_and_redacts():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")

    def fail(_u, _k):
        raise RuntimeError("bad token sk-secret-value and supabase_key exposed")

    result = resolve_streamlit_supabase_client(cfg, client_factory=fail)
    assert result["client_resolved"] is False
    assert result["client_error_type"] == "RuntimeError"
    short = result["client_error_message_short"] or ""
    assert "sk-secret-value" not in short
    assert "supabase_key" not in short


def test_injected_client_success():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
    result = resolve_streamlit_supabase_client(cfg, client=DummyClient())
    assert result["client_resolved"] is True
    assert result["client_factory_source"] == "injected_client"


def test_snapshot_unresolved_means_snapshot_not_loaded_and_fallback_preserved_and_deterministic():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k")
    payload = _fallback_payload()
    out1 = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=payload)
    out2 = load_streamlit_dashboard_snapshot(runtime_config=cfg, fallback_payload=payload)
    assert out1["snapshot"] is None
    assert out1["runtime_diagnostics"]["snapshot_loaded"] is False
    assert out1["normalization_status"] == "client_unresolved"
    assert out1["payload_source"] == "fallback_payload"
    assert out1["payload"]["dashboard_entity_facts"] == payload["dashboard_entity_facts"]
    assert out1["runtime_diagnostics"] == out2["runtime_diagnostics"]
