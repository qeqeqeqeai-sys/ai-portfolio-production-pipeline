from pathlib import Path

from scripts.run_d21_limited_governed_backfill import (
    STATUS_CONNECTIVITY_FAILED,
    STATUS_EXEC_FAILED,
    STATUS_GOV_BLOCKED,
    STATUS_SUCCESS,
)


def _workflow_text() -> str:
    return Path(".github/workflows/d21_limited_governed_backfill.yml").read_text(encoding="utf-8")


def test_workflow_exists_and_dispatch_only():
    text = _workflow_text()
    assert "workflow_dispatch:" in text
    assert "on:" in text
    assert "pull_request:" not in text
    assert "push:" not in text


def test_workflow_enforces_window_count_and_approval_phrases():
    text = _workflow_text()
    assert "window_count must be exactly 1 for first live run" in text
    assert "I_APPROVE_D21_NON_DRY_BACKFILL" in text
    assert "I_APPROVE_APPEND_ONLY_PERSISTENCE" in text
    assert "I_APPROVE_DUPLICATE_PREVENTION" in text
    assert "I_APPROVE_CHECKSUM_LINEAGE" in text


def test_workflow_uses_expected_secret_names_and_no_direct_sql():
    text = _workflow_text()
    assert "SUPABASE_URL" in text
    assert "SUPABASE_SERVICE_ROLE_KEY" in text
    assert "select(" not in text.lower()
    assert "insert(" not in text.lower()
    assert "update(" not in text.lower()
    assert "delete(" not in text.lower()


def test_workflow_avoids_secret_echoing():
    text = _workflow_text().lower()
    assert "supabase_url_fingerprint" in text
    assert "supabase_service_role_key_fingerprint" in text
    assert "echo $supabase" not in text


def test_script_statuses_are_allowed_set():
    allowed = {
        "CONNECTIVITY_FAILED_NO_WRITE",
        "GOVERNANCE_BLOCKED_NO_WRITE",
        "D21_EXECUTED_WINDOW_1_SUCCESS",
        "D21_EXECUTION_FAILED_AFTER_APPROVAL",
    }
    assert {STATUS_CONNECTIVITY_FAILED, STATUS_GOV_BLOCKED, STATUS_SUCCESS, STATUS_EXEC_FAILED} == allowed
