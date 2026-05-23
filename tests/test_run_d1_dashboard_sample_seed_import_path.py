from pathlib import Path


WORKFLOW_PATH = Path(".github/workflows/run-d1-dashboard-seed.yml")
SCRIPT_PATH = Path("scripts/run_d1_dashboard_sample_seed.py")


def test_script_bootstraps_project_root_in_sys_path() -> None:
    text = SCRIPT_PATH.read_text(encoding="utf-8")
    assert "PROJECT_ROOT = Path(__file__).resolve().parents[1]" in text
    assert "if str(PROJECT_ROOT) not in sys.path:" in text
    assert "sys.path.insert(0, str(PROJECT_ROOT))" in text


def test_workflow_sets_pythonpath_to_workspace() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    assert "PYTHONPATH: ${{ github.workspace }}" in text


def test_workflow_execute_stays_manual_and_guardrailed() -> None:
    text = WORKFLOW_PATH.read_text(encoding="utf-8")
    lowered = text.lower()
    assert "workflow_dispatch:" in text
    assert "schedule:" not in lowered
    assert "cron:" not in lowered
    assert "python scripts/run_d1_dashboard_sample_seed.py --execute" in text


def test_no_raw_sql_or_secret_leakage_patterns() -> None:
    wf_text = WORKFLOW_PATH.read_text(encoding="utf-8").lower()
    script_text = SCRIPT_PATH.read_text(encoding="utf-8").lower()

    for token in ["psql ", "sqlite3 ", "mysql ", "sqlcmd ", "raw sql", "execute sql"]:
        assert token not in wf_text
        assert token not in script_text

    for token in [
        'echo "${supabase_url}"',
        "echo '${supabase_url}'",
        'echo "${supabase_anon_key}"',
        "echo '${supabase_anon_key}'",
        "printenv",
        "env |",
        "set -x",
    ]:
        assert token not in wf_text
