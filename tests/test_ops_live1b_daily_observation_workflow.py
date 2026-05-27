from pathlib import Path
import subprocess


WORKFLOW_PATH = Path('.github/workflows/ops_live1b_daily_observation.yml')


def _workflow_text() -> str:
    return WORKFLOW_PATH.read_text(encoding='utf-8')


def test_workflow_yaml_parses_successfully() -> None:
    result = subprocess.run(
        [
            'ruby',
            '-e',
            "require 'yaml'; data = YAML.safe_load(File.read('.github/workflows/ops_live1b_daily_observation.yml')); abort('missing jobs') unless data.is_a?(Hash) && data['jobs']",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_workflow_has_required_triggers_and_no_push() -> None:
    text = _workflow_text()
    assert 'workflow_dispatch:' in text
    assert 'schedule:' in text
    assert 'push:' not in text


def test_ingest_command_has_exactly_one_output() -> None:
    text = _workflow_text()
    assert text.count('--output') == 1

    expected = (
        'PYTHONPATH=. python scripts/run_ops_live1b_50_symbol_operational_ingest.py \\\n'
        '            --snapshot-date "$SNAPSHOT_DATE" \\\n'
        '            --output "$SNAPSHOT_OUTPUT_PATH"'
    )
    assert expected in text


def test_forbidden_legacy_strings_absent() -> None:
    text = _workflow_text()
    forbidden_literals = [
        '${{ env.SNAPSHOT_OUTPUT_DIR }}/ops_live1b_${{ env.SNAPSHOT_DATE }}.json',
        'SNAPSHOT_OUTPUT_PATH: ${{ env.SNAPSHOT_OUTPUT_DIR }}/ops_live1b_${{ env.SNAPSHOT_DATE }}.json',
        '--output "$SNAPSHOT_OUTPUT_DIR/ops_live1b_${SNAPSHOT_DATE}.json"',
        '${{ env.SNAPSHOT_DATE }}',
    ]
    for literal in forbidden_literals:
        assert literal not in text


def test_no_manifest_env_interpolation_for_snapshot_output_path() -> None:
    text = _workflow_text()
    start = text.index('Build artifact manifest')
    end = text.index('Upload observation artifacts')
    manifest_block = text[start:end]

    assert 'env:' not in manifest_block
    assert 'SNAPSHOT_OUTPUT_PATH:' not in manifest_block
    assert 'os.environ["SNAPSHOT_OUTPUT_PATH"]' in manifest_block


def test_upload_paths_use_only_snapshot_output_path_and_required_files() -> None:
    text = _workflow_text()
    start = text.index('Upload observation artifacts')
    upload_block = text[start:]

    assert '${{ env.SNAPSHOT_OUTPUT_PATH }}' in upload_block
    assert '${{ env.REVIEW_JSON_PATH }}' in upload_block
    assert '${{ env.REVIEW_MD_PATH }}' in upload_block
    assert '${{ env.MANIFEST_PATH }}' in upload_block

    assert '${{ env.SNAPSHOT_DATE }}' not in upload_block
    assert '${{ env.SNAPSHOT_OUTPUT_DIR }}/ops_live1b_${{ env.SNAPSHOT_DATE }}.json' not in upload_block


def test_snapshot_date_and_snapshot_output_path_are_written_to_github_env() -> None:
    text = _workflow_text()
    assert 'echo "SNAPSHOT_DATE=$SNAPSHOT_DATE" >> "$GITHUB_ENV"' in text
    assert 'echo "SNAPSHOT_OUTPUT_PATH=$SNAPSHOT_OUTPUT_DIR/ops_live1b_${SNAPSHOT_DATE}.json" >> "$GITHUB_ENV"' in text


def test_governance_boundaries_preserved() -> None:
    text = _workflow_text()
    lower = text.lower()

    assert 'FMP_API_KEY: ${{ secrets.FMP_API_KEY }}' in text
    assert 'SUPABASE_URL' not in text
    assert 'SUPABASE_SERVICE_ROLE_KEY' not in text
    assert 'git push' not in lower
    assert 'git commit' not in lower
    assert 'run_d21_limited_governed_backfill.py' not in text
    assert 'topology_activation_enabled' not in lower
    assert 'prediction_enabled' not in lower
    assert 'trading_enabled' not in lower
    assert 'streaming_observation_loader' not in lower
    assert 'no_supabase_write' in text
    assert 'no_repo_writeback' in text
    assert 'no_replay' in text
    assert 'no_topology_activation' in text
    assert 'no_prediction_or_trading_execution' in text
    assert 'no_streaming' in text
