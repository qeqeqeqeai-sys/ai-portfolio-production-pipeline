from pathlib import Path


WORKFLOW_PATH = Path('.github/workflows/run-d1-dashboard-seed.yml')


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists()


def test_workflow_dispatch_present():
    text = _workflow_text()
    assert 'workflow_dispatch:' in text


def test_installs_requirements_txt():
    text = _workflow_text()
    assert 'pip install -r requirements.txt' in text


def test_executes_d1_seed_with_execute_flag():
    text = _workflow_text()
    assert 'python scripts/run_d1_dashboard_sample_seed.py --execute' in text


def test_references_required_supabase_secrets():
    text = _workflow_text()
    assert 'secrets.SUPABASE_URL' in text
    assert 'secrets.SUPABASE_ANON_KEY' in text


def test_no_cron_or_schedule_trigger():
    text = _workflow_text().lower()
    assert 'schedule:' not in text
    assert 'cron:' not in text


def test_no_raw_sql_execution():
    text = _workflow_text().lower()
    forbidden = ['psql ', 'sqlite3 ', 'mysql ', 'sqlcmd ', 'run sql', 'execute sql', 'raw sql']
    for token in forbidden:
        assert token not in text


def test_no_secret_leakage_patterns():
    text = _workflow_text().lower()
    forbidden = [
        'echo "${supabase_url}"',
        "echo '${supabase_url}'",
        'echo "${supabase_anon_key}"',
        "echo '${supabase_anon_key}'",
        'printenv',
        'env |',
        'set -x',
    ]
    for token in forbidden:
        assert token not in text
