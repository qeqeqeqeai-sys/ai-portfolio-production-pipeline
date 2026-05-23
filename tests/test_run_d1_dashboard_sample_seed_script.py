from __future__ import annotations

from pathlib import Path


SCRIPT_PATH = Path("scripts/run_d1_dashboard_sample_seed.py")
README_PATH = Path("README_DEMO.md")


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_script_exists() -> None:
    assert SCRIPT_PATH.exists()


def test_defaults_to_dry_run() -> None:
    text = _script_text()
    assert "dry_run = not execute" in text
    assert "confirm_execute=execute, dry_run=dry_run" in text


def test_requires_execute_flag_for_writes() -> None:
    text = _script_text()
    assert "--execute" in text
    assert "mode={'execute' if execute else 'dry_run'}" in text


def test_references_controlled_seed_runner() -> None:
    text = _script_text()
    assert "run_d1_controlled_seed" in text


def test_does_not_use_raw_sql() -> None:
    text = _script_text().lower()
    assert "execute_sql" not in text
    assert "from_(" not in text
    assert "sql(" not in text


def test_no_random_uuid_or_datetime_now_calls() -> None:
    text = _script_text().lower()
    assert "random" not in text
    assert "uuid" not in text
    assert "datetime.now" not in text


def test_readme_documents_expected_commands() -> None:
    text = README_PATH.read_text(encoding="utf-8")
    assert "python scripts/run_d1_dashboard_sample_seed.py --dry-run" in text
    assert "python scripts/run_d1_dashboard_sample_seed.py --execute" in text


def test_no_secret_leakage_statements() -> None:
    text = _script_text()
    assert "print(key" not in text
    assert "SUPABASE_ANON_KEY=" not in text
    assert "SUPABASE_KEY=" not in text
