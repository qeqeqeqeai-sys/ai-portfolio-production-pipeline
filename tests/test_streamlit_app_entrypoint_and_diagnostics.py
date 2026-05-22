from pathlib import Path

from apps import streamlit_expectation_failure_dashboard as app
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o7_streamlit_supabase_runtime import (
    build_streamlit_supabase_runtime_config,
    load_streamlit_dashboard_snapshot,
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


def test_root_entrypoint_delegates_to_canonical_app():
    root_entrypoint = Path("streamlit_expectation_failure_dashboard.py")
    assert root_entrypoint.exists()
    source = root_entrypoint.read_text(encoding="utf-8")
    assert "from apps.streamlit_expectation_failure_dashboard import main" in source
    assert "main()" in source


def test_runtime_diagnostics_have_non_none_required_fields_and_no_secrets():
    runtime_output = load_streamlit_dashboard_snapshot(
        runtime_config=build_streamlit_supabase_runtime_config(supabase_url=None, supabase_key=None),
        fallback_payload=_fallback_payload(),
    )
    diagnostics = runtime_output["runtime_diagnostics"]
    assert diagnostics["runtime_mode"] is not None
    assert diagnostics["payload_source"] is not None
    assert isinstance(diagnostics["credentials_present"], bool)
    assert "supabase_key" not in str(diagnostics).lower()


def test_app_metadata_constants_present():
    assert app.APP_ENTRYPOINT == "apps/streamlit_expectation_failure_dashboard.py"
    assert app.APP_VERSION
    assert app.DIAGNOSTICS_SCHEMA_VERSION
    assert app.RUNTIME_MODULE_VERSION
