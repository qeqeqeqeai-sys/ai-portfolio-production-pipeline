from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


WORKFLOW = Path('.github/workflows/lr6_live5_first_approved_non_dry_persistence_execution.yml')
SCRIPT = Path('scripts/run_lr6_live5_first_approved_non_dry_persistence_execution.py')
RESULT = Path('outputs/lr6_live5_first_approved_non_dry_persistence_execution_result.json')


def _run(env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    run_env = os.environ.copy()
    run_env.update(env)
    return subprocess.run([sys.executable, str(SCRIPT)], capture_output=True, text=True, env=run_env)


def test_workflow_exists_and_dispatch_only():
    text = WORKFLOW.read_text(encoding='utf-8')
    assert WORKFLOW.exists()
    assert '\non:\n  workflow_dispatch:' in text
    assert 'pull_request:' not in text and 'push:' not in text


def test_required_inputs_and_guards_present():
    workflow_text = WORKFLOW.read_text(encoding='utf-8')
    for required_input in [
        'approval_phrase:', 'non_dry_execution_token:', 'max_entities:', 'metric_target:',
        'persistence_target:', 'append_only_confirmation:', 'rollback_confirmation:', 'lineage_confirmation:'
    ]:
        assert required_input in workflow_text
    script_text = SCRIPT.read_text(encoding='utf-8')
    assert 'max_entities <= MAX_ENTITIES' in script_text
    assert 'LIVE5_METRIC_TARGET") == TARGET_METRIC' in script_text
    assert 'LIVE5_PERSISTENCE_TARGET") == ISOLATED_PERSISTENCE_TARGET' in script_text
    assert 'LIVE5_APPEND_ONLY_CONFIRMATION' in script_text
    assert 'LIVE5_ROLLBACK_CONFIRMATION' in script_text
    assert 'LIVE5_LINEAGE_CONFIRMATION' in script_text


def test_secrets_referenced_not_printed_and_no_direct_sql():
    wf = WORKFLOW.read_text(encoding='utf-8')
    script = SCRIPT.read_text(encoding='utf-8')
    assert 'secrets.SUPABASE_URL' in wf
    assert 'secrets.SUPABASE_SERVICE_ROLE_KEY' in wf
    assert 'print(os.getenv("SUPABASE_' not in script
    assert 'select ' not in script.lower()
    assert 'insert into ' not in script.lower()


def test_script_refuses_missing_credentials(monkeypatch):
    cp = _run({
        'LIVE5_APPROVAL_PHRASE': 'I APPROVE LR6-LIVE NON-DRY TINY REPLAY EXECUTION',
        'LIVE5_NON_DRY_EXECUTION_TOKEN': 'LR6_LIVE_NON_DRY_TINY_EXECUTION_TOKEN_REQUIRED',
        'LIVE5_MAX_ENTITIES': '3',
        'LIVE5_METRIC_TARGET': 'replay_richness',
        'LIVE5_PERSISTENCE_TARGET': 'replay_richness_wave0_shadow',
        'LIVE5_APPEND_ONLY_CONFIRMATION': 'true',
        'LIVE5_ROLLBACK_CONFIRMATION': 'true',
        'LIVE5_LINEAGE_CONFIRMATION': 'true',
        'SUPABASE_URL': '',
        'SUPABASE_SERVICE_ROLE_KEY': '',
    })
    assert cp.returncode != 0
    payload = json.loads(RESULT.read_text(encoding='utf-8'))
    assert payload['status'] == 'APPROVED_EXECUTION_BLOCKED_MISSING_CREDENTIALS'


def test_script_refuses_missing_approval_and_wrong_metric():
    cp = _run({
        'LIVE5_APPROVAL_PHRASE': '',
        'LIVE5_NON_DRY_EXECUTION_TOKEN': 'LR6_LIVE_NON_DRY_TINY_EXECUTION_TOKEN_REQUIRED',
        'LIVE5_MAX_ENTITIES': '3',
        'LIVE5_METRIC_TARGET': 'wrong_metric',
        'LIVE5_PERSISTENCE_TARGET': 'replay_richness_wave0_shadow',
        'LIVE5_APPEND_ONLY_CONFIRMATION': 'true',
        'LIVE5_ROLLBACK_CONFIRMATION': 'true',
        'LIVE5_LINEAGE_CONFIRMATION': 'true',
        'SUPABASE_URL': 'https://example.supabase.co',
        'SUPABASE_SERVICE_ROLE_KEY': 'fake',
    })
    assert cp.returncode != 0
    payload = json.loads(RESULT.read_text(encoding='utf-8'))
    assert payload['status'] == 'APPROVED_EXECUTION_GOVERNANCE_FAILURE'
    assert payload['attempted'] is False
    assert payload['inserted_rows'] == 0


def test_script_distinguishes_simulated_from_real_rows_and_blocks_without_adapter():
    cp = _run({
        'LIVE5_APPROVAL_PHRASE': 'I APPROVE LR6-LIVE NON-DRY TINY REPLAY EXECUTION',
        'LIVE5_NON_DRY_EXECUTION_TOKEN': 'LR6_LIVE_NON_DRY_TINY_EXECUTION_TOKEN_REQUIRED',
        'LIVE5_MAX_ENTITIES': '3',
        'LIVE5_METRIC_TARGET': 'replay_richness',
        'LIVE5_PERSISTENCE_TARGET': 'replay_richness_wave0_shadow',
        'LIVE5_APPEND_ONLY_CONFIRMATION': 'true',
        'LIVE5_ROLLBACK_CONFIRMATION': 'true',
        'LIVE5_LINEAGE_CONFIRMATION': 'true',
        'SUPABASE_URL': 'https://example.supabase.co',
        'SUPABASE_SERVICE_ROLE_KEY': 'fake',
    })
    assert cp.returncode != 0
    payload = json.loads(RESULT.read_text(encoding='utf-8'))
    assert payload['status'] == 'APPROVED_EXECUTION_BLOCKED_NO_APPROVED_ADAPTER'
    assert payload['attempted'] is False
    assert payload['inserted_rows'] == 0
    assert payload['simulated_sample_rows'] == 0


def test_no_forbidden_expansion_terms():
    text = SCRIPT.read_text(encoding='utf-8').lower() + WORKFLOW.read_text(encoding='utf-8').lower()
    for forbidden in ['topology expansion', 'contradiction expansion', 'trading logic', 'prediction engine']:
        assert forbidden not in text
