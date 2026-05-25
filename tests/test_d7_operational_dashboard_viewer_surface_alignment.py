from pathlib import Path


def test_d7_operational_dashboard_viewer_is_intelligence_first():
    source = Path("streamlit_apps/d7_operational_dashboard_viewer.py").read_text(encoding="utf-8")

    assert "render_e6_expectation_executive_summary" in source
    assert "render_d15_historical_operational_intelligence" in source
    assert "render_d16_historical_findings_operator_narrative" in source
    assert "render_d17_historical_confidence_lineage" in source
    assert "render_d18_cross_run_confidence_delta_operator_triage" in source
    assert "render_d19_triage_explainability_continuity_taxonomy" in source
    assert "render_h1_historical_density_expansion" in source
    assert "render_d7_intelligence_overview" in source
    assert "render_d7_finding_cards" in source
    assert "render_d7_narrative_sections" in source
    assert "render_d7_evidence_highlights" in source
    assert "render_d7_integrity_overview" in source
    assert "render_d8_2_replay_evidence_density_summary" in source
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
    monkeypatch.setattr(app, "render_d15_historical_operational_intelligence", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d16_historical_findings_operator_narrative", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d17_historical_confidence_lineage", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d18_cross_run_confidence_delta_operator_triage", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d19_triage_explainability_continuity_taxonomy", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_h1_historical_density_expansion", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_intelligence_overview", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_supervisor_interpretation", lambda summary, *, st: None)
    monkeypatch.setattr(app, "render_d7_finding_cards", lambda cards, *, st: None)
    monkeypatch.setattr(app, "render_d8_1_operational_insight_cards", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_narrative_sections", lambda sections, *, st: None)
    monkeypatch.setattr(app, "render_d7_evidence_highlights", lambda highlights, *, st: None)
    monkeypatch.setattr(app, "render_d7_integrity_overview", lambda overview, *, st: None)
    monkeypatch.setattr(app, "render_d8_2_replay_evidence_density_summary", lambda model, *, st: None)
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
        "render_d8_2_replay_evidence_density_summary": "(view_model, st)",
        "render_d15_historical_operational_intelligence": "(view_model, st)",
        "render_d16_historical_findings_operator_narrative": "(view_model, st)",
        "render_d17_historical_confidence_lineage": "(view_model, st)",
        "render_d18_cross_run_confidence_delta_operator_triage": "(view_model, st)",
        "render_d19_triage_explainability_continuity_taxonomy": "(view_model, st)",
        "render_h1_historical_density_expansion": "(view_model, st)",
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


def test_d7_operational_dashboard_calls_d8_1_renderer(monkeypatch):
    import streamlit_apps.d7_operational_dashboard_viewer as app

    calls = {"d8_1": 0}

    class _Ctx:
        def __enter__(self):
            return self
        def __exit__(self, exc_type, exc, tb):
            return False

    class _FakeSt:
        secrets = {}
        def cache_data(self, ttl=0):
            return lambda fn: fn
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

    vm = {
        "findings": [], "narratives": [], "evidence_maps": [], "integrity_overview": {},
        "runtime_sections": {"findings_payload": {"row_count": 0}, "narratives_payload": {"row_count": 0}, "evidence_payload": {"row_count": 0}, "integrity_payload": {"manifests": {"row_count": 0}, "audits": {"row_count": 0}, "replay": {"row_count": 0}}},
    }
    monkeypatch.setattr(app, "st", _FakeSt())
    monkeypatch.setattr(app, "build_streamlit_supabase_runtime_config", lambda **kwargs: {})
    monkeypatch.setattr(app, "resolve_streamlit_supabase_client", lambda _cfg: {"client": None, "client_resolved": False})
    monkeypatch.setattr(app, "_load_view_model_cached", lambda _client: vm)
    monkeypatch.setattr(app, "build_d7_runtime_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(app, "build_d7_intelligence_cards", lambda findings, evidence_maps: [])
    monkeypatch.setattr(app, "build_d7_evidence_highlights", lambda evidence_maps, findings: [])
    monkeypatch.setattr(app, "build_d7_supervisor_summary", lambda model: {})
    monkeypatch.setattr(app, "build_d7_narrative_sections", lambda narratives: [])
    monkeypatch.setattr(app, "build_d7_debug_payload_sections", lambda model: {})
    monkeypatch.setattr(app, "render_e6_expectation_executive_summary", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d15_historical_operational_intelligence", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d16_historical_findings_operator_narrative", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d17_historical_confidence_lineage", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d18_cross_run_confidence_delta_operator_triage", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d19_triage_explainability_continuity_taxonomy", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_h1_historical_density_expansion", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_intelligence_overview", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_supervisor_interpretation", lambda summary, *, st: None)
    monkeypatch.setattr(app, "render_d7_finding_cards", lambda cards, *, st: None)
    monkeypatch.setattr(app, "render_d7_narrative_sections", lambda sections, *, st: None)
    monkeypatch.setattr(app, "render_d7_evidence_highlights", lambda highlights, *, st: None)
    monkeypatch.setattr(app, "render_d7_integrity_overview", lambda overview, *, st: None)
    monkeypatch.setattr(app, "render_d7_debug_archive", lambda archive, *, st: None)
    monkeypatch.setattr(app, "render_d8_2_replay_evidence_density_summary", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d8_1_operational_insight_cards", lambda model, *, st: calls.__setitem__("d8_1", calls["d8_1"] + 1))

    app.main()
    assert calls["d8_1"] == 1


def test_d7_operational_dashboard_calls_d8_2_renderer(monkeypatch):
    import streamlit_apps.d7_operational_dashboard_viewer as app
    calls = {"d8_2": 0}
    class _Ctx:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False
    class _FakeSt:
        secrets = {}
        def cache_data(self, ttl=0): return lambda fn: fn
        def set_page_config(self, **kwargs): return None
        def title(self, *_args, **_kwargs): return None
        def warning(self, *_args, **_kwargs): return None
        def info(self, *_args, **_kwargs): return None
        def success(self, *_args, **_kwargs): return None
        def tabs(self, labels): return [_Ctx() for _ in labels]
    vm = {"findings": [], "narratives": [], "evidence_maps": [], "integrity_overview": {}, "runtime_sections": {"findings_payload": {"row_count": 0}, "narratives_payload": {"row_count": 0}, "evidence_payload": {"row_count": 0}, "integrity_payload": {"manifests": {"row_count": 0}, "audits": {"row_count": 0}, "replay": {"row_count": 0}}}}
    monkeypatch.setattr(app, "st", _FakeSt())
    monkeypatch.setattr(app, "build_streamlit_supabase_runtime_config", lambda **kwargs: {})
    monkeypatch.setattr(app, "resolve_streamlit_supabase_client", lambda _cfg: {"client": None, "client_resolved": False})
    monkeypatch.setattr(app, "_load_view_model_cached", lambda _client: vm)
    monkeypatch.setattr(app, "build_d7_runtime_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(app, "build_d7_intelligence_cards", lambda findings, evidence_maps: [])
    monkeypatch.setattr(app, "build_d7_evidence_highlights", lambda evidence_maps, findings: [])
    monkeypatch.setattr(app, "build_d7_supervisor_summary", lambda model: {})
    monkeypatch.setattr(app, "build_d7_narrative_sections", lambda narratives: [])
    monkeypatch.setattr(app, "build_d7_debug_payload_sections", lambda model: {})
    monkeypatch.setattr(app, "render_e6_expectation_executive_summary", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d15_historical_operational_intelligence", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d16_historical_findings_operator_narrative", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d17_historical_confidence_lineage", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d18_cross_run_confidence_delta_operator_triage", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d19_triage_explainability_continuity_taxonomy", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_h1_historical_density_expansion", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_intelligence_overview", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_supervisor_interpretation", lambda summary, *, st: None)
    monkeypatch.setattr(app, "render_d7_finding_cards", lambda cards, *, st: None)
    monkeypatch.setattr(app, "render_d8_1_operational_insight_cards", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_narrative_sections", lambda sections, *, st: None)
    monkeypatch.setattr(app, "render_d7_evidence_highlights", lambda highlights, *, st: None)
    monkeypatch.setattr(app, "render_d7_integrity_overview", lambda overview, *, st: None)
    monkeypatch.setattr(app, "render_d7_debug_archive", lambda archive, *, st: None)
    monkeypatch.setattr(app, "render_d8_2_replay_evidence_density_summary", lambda model, *, st: calls.__setitem__("d8_2", calls["d8_2"] + 1))
    app.main()
    assert calls["d8_2"] == 1


def test_d7_operational_dashboard_locks_top_level_section_precedence_and_d15_fallbacks(monkeypatch):
    import streamlit_apps.d7_operational_dashboard_viewer as app

    calls = {"render_order": [], "d15_payload_variants": [], "d16_calls": 0, "d17_calls":0, "d18_calls":0}

    class _Ctx:
        def __enter__(self): return self
        def __exit__(self, exc_type, exc, tb): return False

    class _FakeSt:
        secrets = {}
        def cache_data(self, ttl=0): return lambda fn: fn
        def set_page_config(self, **kwargs): return None
        def title(self, *_args, **_kwargs): return None
        def warning(self, *_args, **_kwargs): return None
        def info(self, *_args, **_kwargs): return None
        def success(self, *_args, **_kwargs): return None
        def tabs(self, labels): return [_Ctx() for _ in labels]

    monkeypatch.setattr(app, "st", _FakeSt())
    monkeypatch.setattr(app, "build_streamlit_supabase_runtime_config", lambda **kwargs: {})
    monkeypatch.setattr(app, "resolve_streamlit_supabase_client", lambda _cfg: {"client": None, "client_resolved": False})
    monkeypatch.setattr(app, "build_d7_runtime_diagnostics", lambda **kwargs: {})
    monkeypatch.setattr(app, "build_d7_intelligence_cards", lambda findings, evidence_maps: [])
    monkeypatch.setattr(app, "build_d7_evidence_highlights", lambda evidence_maps, findings: [])
    monkeypatch.setattr(app, "build_d7_supervisor_summary", lambda model: {})
    monkeypatch.setattr(app, "build_d7_narrative_sections", lambda narratives: [])
    monkeypatch.setattr(app, "build_d7_debug_payload_sections", lambda model: {})
    monkeypatch.setattr(app, "render_d7_supervisor_interpretation", lambda summary, *, st: None)
    monkeypatch.setattr(app, "render_d7_finding_cards", lambda cards, *, st: None)
    monkeypatch.setattr(app, "render_d8_1_operational_insight_cards", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_narrative_sections", lambda sections, *, st: None)
    monkeypatch.setattr(app, "render_d7_evidence_highlights", lambda highlights, *, st: None)
    monkeypatch.setattr(app, "render_d7_integrity_overview", lambda overview, *, st: None)
    monkeypatch.setattr(app, "render_d8_2_replay_evidence_density_summary", lambda model, *, st: None)
    monkeypatch.setattr(app, "render_d7_debug_archive", lambda archive, *, st: None)

    def _e6(_model, *, st):
        calls["render_order"].append("e6_expectation_executive_summary")

    def _d15(model, *, st):
        calls["render_order"].append("d15_historical_operational_intelligence")
        payload = model.get("d15_historical_backfill_execution_enrichment")
        if payload is None:
            calls["d15_payload_variants"].append("missing")
        elif payload.get("historical_replay_depth") in (None, "", "UNAVAILABLE"):
            calls["d15_payload_variants"].append("degraded")
        else:
            calls["d15_payload_variants"].append("present")

    def _d17(_model, *, st):
        calls["render_order"].append("d17_historical_confidence_lineage")
        calls["d17_calls"] += 1

    def _overview(_model, *, st):
        calls["render_order"].append("intelligence_overview")
    def _d18(_model, *, st):
        calls["render_order"].append("d18_cross_run_confidence_delta_operator_triage")
    def _d19(view_model, *, st):
        calls["render_order"].append("d19_triage_explainability_continuity_taxonomy")
    def _h1(view_model, *, st):
        calls["render_order"].append("h1_historical_density_expansion")
        calls["d18_calls"] += 1
    def _d16(_model, *, st):
        calls["render_order"].append("d16_historical_findings_operator_narrative")
        calls["d16_calls"] += 1

    monkeypatch.setattr(app, "render_e6_expectation_executive_summary", _e6)
    monkeypatch.setattr(app, "render_d15_historical_operational_intelligence", _d15)
    monkeypatch.setattr(app, "render_d16_historical_findings_operator_narrative", _d16)
    monkeypatch.setattr(app, "render_d17_historical_confidence_lineage", _d17)
    monkeypatch.setattr(app, "render_d18_cross_run_confidence_delta_operator_triage", _d18)
    monkeypatch.setattr(app, "render_d19_triage_explainability_continuity_taxonomy", _d19)
    monkeypatch.setattr(app, "render_h1_historical_density_expansion", _h1)
    monkeypatch.setattr(app, "render_d7_intelligence_overview", _overview)

    base_vm = {
        "findings": [], "narratives": [], "evidence_maps": [], "integrity_overview": {},
        "runtime_sections": {"findings_payload": {"row_count": 0}, "narratives_payload": {"row_count": 0}, "evidence_payload": {"row_count": 0}, "integrity_payload": {"manifests": {"row_count": 0}, "audits": {"row_count": 0}, "replay": {"row_count": 0}}},
    }
    variants = [
        {"d15_historical_backfill_execution_enrichment": {"historical_replay_depth": "SUFFICIENT"}},
        {"d15_historical_backfill_execution_enrichment": None},
        {"d15_historical_backfill_execution_enrichment": {"historical_replay_depth": "UNAVAILABLE"}},
    ]
    for variant in variants:
        calls["render_order"].clear()
        monkeypatch.setattr(app, "_load_view_model_cached", lambda _client, _vm={**base_vm, **variant}: _vm)
        app.main()
        assert calls["render_order"][:8] == [
            "e6_expectation_executive_summary",
            "d15_historical_operational_intelligence",
            "d16_historical_findings_operator_narrative",
            "d17_historical_confidence_lineage",
            "d18_cross_run_confidence_delta_operator_triage",
            "d19_triage_explainability_continuity_taxonomy",
            "h1_historical_density_expansion",
            "intelligence_overview",
        ]
    assert calls["d15_payload_variants"] == ["present", "missing", "degraded"]
    assert calls["d16_calls"] == 3
