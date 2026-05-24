from pathlib import Path


def test_d7_operational_dashboard_viewer_is_intelligence_first():
    source = Path("streamlit_apps/d7_operational_dashboard_viewer.py").read_text(encoding="utf-8")

    assert "render_e6_expectation_executive_summary" in source
    assert "render_d7_intelligence_overview" in source
    assert "render_d7_finding_cards" in source
    assert "render_d7_narrative_sections" in source
    assert "render_d7_evidence_highlights" in source
    assert "render_d7_integrity_overview" in source
    assert "render_d7_debug_archive" in source

    assert "st.dataframe(" not in source
    assert "Supabase table row counts" not in source
    assert "D7 runtime diagnostics" not in source


def test_d7_operational_dashboard_viewer_main_smoke_catches_signature_mismatches(monkeypatch):
    import streamlit_apps.d7_operational_dashboard_viewer as app

    calls = {}

    class _Ctx:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeSt:
        secrets = {}

        def cache_data(self, ttl=0):
            def _decorator(fn):
                return fn
            return _decorator

        def set_page_config(self, **kwargs):
            return None

        def title(self, *_args, **_kwargs):
            return None

        def warning(self, *_args, **_kwargs):
            return None

        def info(self, *_args, **_kwargs):
            return None

        def success(self, *_args, **_kwargs):
            return None

        def tabs(self, labels):
            return [_Ctx() for _ in labels]

    fake_st = _FakeSt()

    vm = {
        "findings": [],
        "narratives": [],
        "evidence_maps": [],
        "integrity_overview": {},
        "runtime_sections": {
            "findings_payload": {"row_count": 0},
            "narratives_payload": {"row_count": 0},
            "evidence_payload": {"row_count": 0},
            "integrity_payload": {"manifests": {"row_count": 0}, "audits": {"row_count": 0}, "replay": {"row_count": 0}},
        },
    }

    monkeypatch.setattr(app, "st", fake_st)
    monkeypatch.setattr(app, "build_streamlit_supabase_runtime_config", lambda **kwargs: {})
    monkeypatch.setattr(app, "resolve_streamlit_supabase_client", lambda _cfg: {"client": None, "client_resolved": False})
    monkeypatch.setattr(app, "_load_view_model_cached", lambda _client: vm)
    monkeypatch.setattr(app, "build_d7_runtime_diagnostics", lambda **kwargs: {})

    monkeypatch.setattr(app, "build_d7_intelligence_cards", lambda findings, evidence_maps: [])
    monkeypatch.setattr(app, "build_d7_evidence_highlights", lambda evidence_maps, findings: [])
    monkeypatch.setattr(app, "build_d7_supervisor_summary", lambda model: {})
    monkeypatch.setattr(app, "build_d7_debug_payload_sections", lambda model: {})

    def _build_narrative_sections(narratives):
        calls["narratives_arg"] = narratives
        return []

    monkeypatch.setattr(app, "build_d7_narrative_sections", _build_narrative_sections)
    monkeypatch.setattr(app, "render_e6_expectation_executive_summary", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_intelligence_overview", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_supervisor_interpretation", lambda summary, *, st: None)
    monkeypatch.setattr(app, "render_d7_finding_cards", lambda cards, *, st: None)
    monkeypatch.setattr(app, "render_d7_narrative_sections", lambda sections, *, st: None)
    monkeypatch.setattr(app, "render_d7_evidence_highlights", lambda highlights, *, st: None)
    monkeypatch.setattr(app, "render_d7_integrity_overview", lambda overview, *, st: None)
    def _render_debug(archive, *, st):
        calls["debug_archive"] = archive

    monkeypatch.setattr(app, "render_d7_debug_archive", _render_debug)

    app.main()

    assert "narratives_arg" in calls
    assert calls["narratives_arg"] == []
    assert "debug_archive" in calls
    assert "runtime_diagnostics" in calls["debug_archive"]


def test_d7_operational_dashboard_viewer_imported_helpers_match_runtime_contracts():
    import inspect
    import streamlit_apps.d7_operational_dashboard_viewer as app

    expected = {
        "build_d7_dashboard_view_model": "(findings_payload, narratives_payload, evidence_payload, integrity_payload, historical_runs_payloads)",
        "build_d7_debug_payload_sections": "(view_model)",
        "build_d7_evidence_highlights": "(evidence_maps, findings)",
        "build_d7_intelligence_cards": "(findings, evidence_maps)",
        "build_d7_narrative_sections": "(narratives)",
        "build_d7_runtime_diagnostics": "(runtime_config, client_resolution, table_payloads)",
        "build_d7_supervisor_summary": "(view_model)",
        "render_d7_debug_archive": "(debug_payload_sections, st)",
        "render_d7_evidence_highlights": "(evidence_highlights, st)",
        "render_d7_finding_cards": "(intelligence_cards, st)",
        "render_d7_integrity_overview": "(integrity_overview, st)",
        "render_d7_intelligence_overview": "(view_model, st)",
        "render_d7_narrative_sections": "(narrative_sections, st)",
        "render_d7_supervisor_interpretation": "(supervisor_summary, st)",
        "render_e6_expectation_executive_summary": "(view_model, st)",
        "load_d7_dashboard_evidence_maps": "(client, limit)",
        "load_d7_dashboard_findings": "(client, limit)",
        "load_d7_dashboard_narratives": "(client, limit)",
        "load_d7_dashboard_operational_integrity": "(client)",
    }

    for name, expected_params in expected.items():
        params = tuple(inspect.signature(getattr(app, name)).parameters.keys())
        actual = f"({', '.join(params)})"
        assert actual == expected_params
