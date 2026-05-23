from pathlib import Path


WORKFLOW_PATH = Path('.github/workflows/run-d1-dashboard-seed.yml')


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_workflow_file_exists():
    assert WORKFLOW_PATH.exists()


def test_workflow_dispatch_present():
    text = _workflow_text()
    assert 'workflow_dispatch:' in text


def test_no_push_trigger():
    text = _workflow_text().lower()
    assert '\npush:' not in text


def test_installs_requirements_txt():
    text = _workflow_text()
    assert 'pip install -r requirements.txt' in text


def test_executes_d1_seed_with_execute_flag():
    text = _workflow_text()
    assert 'python scripts/run_d1_dashboard_sample_seed.py --execute --verify-readback' in text


def test_job_level_env_maps_required_values():
    text = _workflow_text()
    assert 'SUPABASE_URL: ${{ secrets.SUPABASE_URL }}' in text
    assert 'SUPABASE_ANON_KEY: ${{ secrets.SUPABASE_ANON_KEY }}' in text
    assert 'SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}' in text
    assert 'PYTHONPATH: ${{ github.workspace }}' in text


def test_validation_step_checks_both_secrets_and_only_reports_presence():
    text = _workflow_text()
    assert 'SUPABASE_URL: missing' in text
    assert 'SUPABASE_URL: present' in text
    assert 'SUPABASE_SERVICE_ROLE_KEY|SUPABASE_ANON_KEY: missing' in text
    assert 'credential_source: service_role_key' in text
    assert 'credential_source: anon_key' in text


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
