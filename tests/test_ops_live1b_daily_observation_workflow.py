from pathlib import Path


WORKFLOW_PATH = Path('.github/workflows/ops_live1b_daily_observation.yml')


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_workflow_exists_and_has_dispatch_and_schedule() -> None:
    text = _workflow_text()
    assert WORKFLOW_PATH.exists()
    assert 'workflow_dispatch:' in text
    assert 'schedule:' in text


def test_workflow_uses_fmp_secret_and_bounded_scripts_only() -> None:
    text = _workflow_text()
    lower = text.lower()

    assert 'FMP_API_KEY: ${{ secrets.FMP_API_KEY }}' in text
    assert 'run_ops_live1b_50_symbol_operational_ingest.py' in text
    assert 'run_ops_live1b_snapshot_observation_review.py' in text
    assert 'actions/upload-artifact@v4' in text
    assert 'retention-days: 14' in text

    assert 'SUPABASE_URL' not in text
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in text
    assert 'run_d21_limited_governed_backfill.py' not in text
    assert 'topology_activation_enabled' not in lower
    assert 'prediction_enabled' not in lower
    assert 'trading_enabled' not in lower
    assert 'streaming_observation_loader' not in lower


def test_workflow_metadata_env_and_manifest_generation_exist() -> None:
    text = _workflow_text()
    lower = text.lower()

    assert 'OBSERVATION_MODE: controlled_operational_observation' in text
    assert 'OPS_PHASE: OPS_LIVE_1B_DAILY' in text
    assert 'GOVERNANCE_MODE: observational_only' in text
    assert 'SNAPSHOT_OUTPUT_DIR: reports/ops_live1b_runs' in text

    assert 'Build OPS-LIVE-1B daily artifact manifest' in text
    assert 'reports/ops_live1b_daily_artifact_manifest.json' in text
    assert 'generated_artifact_paths' in text
    assert 'no_supabase_write' in text
    assert 'no_repo_writeback' in text
    assert 'no_replay' in text
    assert 'no_topology_activation' in text
    assert 'no_prediction_or_trading_execution' in text
    assert 'no_streaming' in text



def test_workflow_does_not_commit_or_push_outputs() -> None:
    lower = _workflow_text().lower()
    forbidden = ['git add', 'git commit', 'git push']
    for token in forbidden:
        assert token not in lower
