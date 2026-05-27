from pathlib import Path


WORKFLOW_PATH = Path('.github/workflows/hist_density1_90d_pilot.yml')


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_workflow_exists() -> None:
    assert WORKFLOW_PATH.exists()


def test_manual_trigger_only() -> None:
    text = _workflow_text()
    assert 'workflow_dispatch:' in text
    assert 'push:' not in text
    assert 'pull_request:' not in text
    assert 'schedule:' not in text


def test_uses_fmp_api_key_secret_and_real_hist_mode() -> None:
    text = _workflow_text()
    assert 'FMP_API_KEY: ${{ secrets.FMP_API_KEY }}' in text
    assert '--density-mode real_ops_hist1' in text


def test_no_repo_writeback_steps() -> None:
    text = _workflow_text().lower()
    assert 'git commit' not in text
    assert 'git push' not in text
