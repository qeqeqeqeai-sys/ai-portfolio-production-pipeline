from pathlib import Path

SCRIPT_PATH = Path("scripts/run_d1_dashboard_sample_seed.py")
WORKFLOW_PATH = Path('.github/workflows/run-d1-dashboard-seed.yml')
O6_PATH = Path('transmission_layers/expectation_failure/dashboard_operationalization/dashboard_o6_supabase_read_adapter.py')


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding='utf-8')


def test_verify_readback_flag_exists() -> None:
    assert '--verify-readback' in _script_text()


def test_credential_priority_prefers_service_role() -> None:
    text = _script_text()
    assert 'SUPABASE_SERVICE_ROLE_KEY' in text
    assert 'SUPABASE_ANON_KEY' in text
    assert 'SUPABASE_KEY' in text
    assert 'service_role_key' in text


def test_credential_fallback_to_anon_key_when_service_role_missing() -> None:
    text = _script_text()
    assert '("SUPABASE_SERVICE_ROLE_KEY", "service_role_key")' in text
    assert '("SUPABASE_ANON_KEY", "anon_key")' in text


def test_credential_source_printed_without_secret_leakage() -> None:
    text = _script_text()
    assert 'print(f"credential_source={credential_source}")' in text
    assert 'print(key' not in text


def test_workflow_maps_service_role_and_verify_readback() -> None:
    text = WORKFLOW_PATH.read_text(encoding='utf-8')
    assert 'SUPABASE_SERVICE_ROLE_KEY: ${{ secrets.SUPABASE_SERVICE_ROLE_KEY }}' in text
    assert 'python scripts/run_d1_dashboard_sample_seed.py --execute --verify-readback' in text


def test_all_empty_readback_exits_non_zero() -> None:
    text = _script_text()
    assert 'if execute and verification_status != "verified_non_empty":' in text
    assert 'return 1' in text


def test_no_raw_sql_and_no_secret_leakage_tokens() -> None:
    text = _script_text().lower()
    assert 'execute_sql' not in text
    assert 'from_(' not in text
    assert 'sql(' not in text
    forbidden = ['printenv', 'set -x', 'echo "${supabase_service_role_key}"', 'echo "${supabase_anon_key}"']
    for token in forbidden:
        assert token not in text


def test_canonical_tables_match_o6_inventory() -> None:
    script_text = _script_text()
    o6_text = O6_PATH.read_text(encoding='utf-8')
    expected = [
        'dashboard_entity_facts',
        'dashboard_subsector_facts',
        'dashboard_alert_facts',
        'dashboard_benchmark_facts',
        'dashboard_replay_facts',
        'dashboard_evidence_facts',
        'dashboard_certification_reports',
        'dashboard_run_manifests',
    ]
    for table in expected:
        assert table in o6_text
    assert 'build_dashboard_read_table_inventory' in script_text
