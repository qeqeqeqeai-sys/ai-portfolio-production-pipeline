from pathlib import Path


def _assert_project_root_setup_before_project_import(source: str, import_snippet: str) -> None:
    assert "PROJECT_ROOT" in source
    assert "sys.path.insert" in source
    assert import_snippet in source

    sys_path_insert_pos = source.index("sys.path.insert")
    transmission_import_pos = source.index(import_snippet)

    assert sys_path_insert_pos < transmission_import_pos


def test_streamlit_dashboard_has_project_root_path_setup_before_project_imports():
    app_path = Path("apps/streamlit_expectation_failure_dashboard.py")
    assert app_path.exists()

    source = app_path.read_text(encoding="utf-8")
    _assert_project_root_setup_before_project_import(source, "from transmission_layers")


def test_o4_view_model_test_has_project_root_path_setup_before_project_imports():
    test_path = Path("tests/test_dashboard_o4_streamlit_view_model.py")
    assert test_path.exists()

    source = test_path.read_text(encoding="utf-8")
    _assert_project_root_setup_before_project_import(
        source,
        "from transmission_layers.expectation_failure import dashboard_operationalization as mod",
    )
