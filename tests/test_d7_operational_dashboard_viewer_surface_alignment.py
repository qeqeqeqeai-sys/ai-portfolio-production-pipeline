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
