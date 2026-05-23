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


def _base_snapshot(status="ok", rows=None, error=None):
    rows = rows if rows is not None else [{"run_id": "r1", "run_date_sgt": "2026-05-22", "entity_id": "E1"}]
    section = {"status": status, "rows": rows, "row_count": len(rows), "error": error}
    snap = {
        "column_inventory": {
            "dashboard_entity_facts": ["run_id", "run_date_sgt", "entity_id"],
            "dashboard_subsector_facts": ["run_id", "run_date_sgt", "subsector"],
            "dashboard_alert_facts": ["run_id", "run_date_sgt", "entity_id"],
            "dashboard_replay_facts": ["run_id", "replay_date_sgt", "entity_id"],
            "dashboard_benchmark_facts": ["run_id", "run_date_sgt", "entity_id"],
            "dashboard_evidence_facts": ["run_id", "run_date_sgt", "entity_id"],
            "dashboard_certification_reports": ["run_id", "run_date_sgt", "certification_status"],
        },
        "section_filter_map": {k: "run_id/as_of_date" for k in ["entity_facts", "subsector_facts", "alert_facts", "benchmark_facts"]} | {"replay_facts": "run_id", "evidence_facts": "run_id", "certification_metadata": "run_id"},
    }
    for key in ["entity_facts", "subsector_facts", "alert_facts", "replay_facts", "benchmark_facts", "evidence_facts", "certification_metadata"]:
        snap[key] = deepcopy(section)
    return snap


def _load_with_snapshot(snapshot):
    import transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter as o6

    orig = o6.build_dashboard_supabase_snapshot
    o6.build_dashboard_supabase_snapshot = lambda *_a, **_k: snapshot
    try:
        return load_streamlit_dashboard_snapshot(
            runtime_config=build_streamlit_supabase_runtime_config(supabase_url="u", supabase_key="k", run_id="r1", as_of_date="2026-05-22"),
            fallback_payload=_fallback_payload(),
            client=DummyClient(),
        )
    finally:
        o6.build_dashboard_supabase_snapshot = orig


def test_section_read_diagnostics_health_matrix_and_fallback_preserved_and_immutable():
    fallback = _fallback_payload()
    orig_fb = deepcopy(fallback)

    healthy = _load_with_snapshot(_base_snapshot("ok"))
    d = healthy["runtime_diagnostics"]
    assert d["health_interpretation"] == "supabase_snapshot_healthy"
    assert d["section_read_diagnostics"][0]["sample_row_keys"]

    empty = _load_with_snapshot(_base_snapshot("empty", rows=[]))
    assert empty["runtime_diagnostics"]["health_interpretation"] == "tables_exist_but_empty_or_filters_exclude_rows"

    missing = _load_with_snapshot(_base_snapshot("missing", rows=[], error="PostgrestError: relation missing"))
    assert missing["runtime_diagnostics"]["missing_tables"]
    assert missing["runtime_diagnostics"]["health_interpretation"] == "dashboard_tables_missing"

    perm = _load_with_snapshot(_base_snapshot("permission_denied", rows=[], error="Permission denied"))
    assert perm["runtime_diagnostics"]["permission_denied_tables"]
    assert perm["runtime_diagnostics"]["health_interpretation"] == "rls_or_permission_denied"

    schema = _load_with_snapshot(_base_snapshot("schema_mismatch", rows=[], error="column missing"))
    assert schema["runtime_diagnostics"]["schema_mismatch_tables"]

    query = _load_with_snapshot(_base_snapshot("query_failed", rows=[], error="network error"))
    assert query["runtime_diagnostics"]["query_failed_tables"]

    mixed_snap = _base_snapshot("ok")
    mixed_snap["alert_facts"] = {"status": "empty", "rows": [], "row_count": 0, "error": None}
    mixed = _load_with_snapshot(mixed_snap)
    assert mixed["runtime_diagnostics"]["health_interpretation"] == "mixed_section_degradation"
    assert mixed["payload_source"] == "fallback_payload"
    assert fallback == orig_fb


def test_client_diagnostics_coherence_and_no_secret_leakage_and_filter_exposure():
    cfg = build_streamlit_supabase_runtime_config(supabase_url="https://x.supabase.co", supabase_key="sk-super-secret", run_id="r1", as_of_date="2026-05-22")
    out = _load_with_snapshot(_base_snapshot("ok"))
    d = out["runtime_diagnostics"]
    assert d["client_resolved"] is True
    assert d["client_factory_source"] == "injected_client"
    assert d["supabase_package_available"] is True
    assert d["client_error_type"] is None
    assert d["client_error_message_short"] is None
    assert any(x["filter_applied"] == "run_id/as_of_date" for x in d["section_read_diagnostics"])
    low = str(d).lower()
    assert "sk-super-secret" not in low
    assert "supabase.co" not in low
