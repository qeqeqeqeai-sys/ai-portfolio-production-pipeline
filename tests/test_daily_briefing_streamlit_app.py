from pathlib import Path


def test_daily_briefing_streamlit_entrypoint_sets_project_root_before_project_imports():
    app_path = Path("apps/sefi_daily_briefing.py")
    assert app_path.exists()

    source = app_path.read_text(encoding="utf-8")
    assert "PROJECT_ROOT" in source
    assert "sys.path.insert" in source
    assert "from transmission_layers.daily_briefing" in source
    assert source.index("sys.path.insert") < source.index("from transmission_layers.daily_briefing")
