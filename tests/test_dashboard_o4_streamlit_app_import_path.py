from pathlib import Path


def test_streamlit_dashboard_has_project_root_path_setup_before_project_imports():
    app_path = Path("apps/streamlit_expectation_failure_dashboard.py")
    assert app_path.exists()

    source = app_path.read_text(encoding="utf-8")

    assert "PROJECT_ROOT" in source
    assert "sys.path.insert" in source
    assert "from transmission_layers" in source

    sys_path_insert_pos = source.index("sys.path.insert")
    transmission_import_pos = source.index("from transmission_layers")

    assert sys_path_insert_pos < transmission_import_pos
