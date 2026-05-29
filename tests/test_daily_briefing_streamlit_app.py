from pathlib import Path


def test_daily_briefing_streamlit_entrypoint_sets_project_root_before_project_imports():
    app_path = Path("apps/sefi_daily_briefing.py")
    assert app_path.exists()

    source = app_path.read_text(encoding="utf-8")
    assert "PROJECT_ROOT" in source
    assert "sys.path.insert" in source
    assert "from transmission_layers.daily_briefing" in source
    assert source.index("sys.path.insert") < source.index("from transmission_layers.daily_briefing")


def test_daily_briefing_streamlit_ui_surfaces_lifecycle_without_top_level_evidence_ids():
    source = Path("apps/sefi_daily_briefing.py").read_text(encoding="utf-8")

    assert "Lifecycle:" in source
    assert "Narrative archetype:" in source
    assert "Continuity explanation:" in source
    assert source.index("with st.expander(\"Evidence drill-down: supporting fact and evidence IDs\")") < source.index(
        "Supporting evidence IDs:"
    )


def test_daily_briefing_streamlit_ui_surfaces_quality_gate_metadata_without_suppressed_dumps():
    source = Path("apps/sefi_daily_briefing.py").read_text(encoding="utf-8")

    assert "Quality status" in source
    assert "Briefing quality gate" in source
    assert "suppression_summary" in source
    assert "No major ecosystem changes detected for the selected date." in source
    assert "Limited briefing-worthy intelligence detected; review watchlist items before escalating." in source
    assert "suppressed_items" not in source
