from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from transmission_layers.history_read_model.obs_query_validation import (
    build_validation_fact_fixture,
    render_obs_query5_validation_markdown,
    run_obs_query5_validation,
    write_obs_query5_validation_outputs,
)


def _category(result: dict, name: str) -> dict:
    return next(category for category in result["categories"] if category["category_name"] == name)


def test_retrieval_validation_execution():
    result = run_obs_query5_validation()
    category = _category(result, "Category A — Retrieval Correctness")
    assert category["tests_executed"] == 6
    assert category["tests_passed"] == 6
    assert {test["test_name"] for test in category["tests"]} == {
        "persisted_retrieval",
        "changed_retrieval",
        "recurrence_retrieval",
        "dominant_retrieval",
        "weakening_retrieval",
        "transition_retrieval",
    }


def test_comparison_validation_execution():
    result = run_obs_query5_validation()
    category = _category(result, "Category B — Historical vs Live Validation")
    assert category["tests_executed"] == 6
    assert category["tests_passed"] == 6
    assert {test["test_name"] for test in category["tests"]} >= {
        "overlap_detection",
        "live_only_anomaly_detection",
        "historical_only_detection",
        "strengthening_detection",
        "weakening_detection",
        "recurrence_detection",
    }


def test_consumption_validation_execution():
    result = run_obs_query5_validation()
    category = _category(result, "Category C — Consumption View Validation")
    assert category["tests_executed"] == 2
    assert category["tests_passed"] == 2
    assert result["coverage_metrics"]["consumption_view_coverage"] == 1.0


def test_traceability_validation_execution():
    result = run_obs_query5_validation()
    category = _category(result, "Category D — Traceability Validation")
    assert category["tests_executed"] == 1
    assert category["tests_passed"] == 1
    test = category["tests"][0]
    assert test["traceability"]["fixture_fact_ids"]
    assert test["traceability"]["fixture_evidence_ids"]


def test_governance_validation_execution():
    result = run_obs_query5_validation()
    category = _category(result, "Category E — Governance Validation")
    assert category["tests_executed"] == 1
    assert category["tests_passed"] == 1
    certification = result["governance_certification"]
    assert certification["provider_api_calls_enabled"] is False
    assert certification["db_writes_enabled"] is False
    assert certification["schema_migrations_enabled"] is False
    assert certification["no_new_intelligence_generation"] is True


def test_deterministic_outputs():
    first = run_obs_query5_validation()
    second = run_obs_query5_validation(fact_rows=list(reversed(build_validation_fact_fixture())))
    assert first == second
    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_output_generation(tmp_path: Path):
    result = run_obs_query5_validation()
    output_json = tmp_path / "obs_query5.json"
    output_md = tmp_path / "obs_query5.md"
    paths = write_obs_query5_validation_outputs(result, output_json=output_json, output_md=output_md)
    assert paths == {"output_json": str(output_json), "output_md": str(output_md)}
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert payload["schema_version"] == "obs_query5_validation_v1"
    assert payload["overall_status"] == "pass"
    assert "# OBS-QUERY Validation Summary" in markdown
    assert "## Overall Assessment" in markdown


def test_markdown_sections():
    markdown = render_obs_query5_validation_markdown(run_obs_query5_validation())
    assert "## Retrieval Validation" in markdown
    assert "## Historical vs Live Validation" in markdown
    assert "## Consumption Validation" in markdown
    assert "## Traceability Validation" in markdown
    assert "## Governance Validation" in markdown


def test_cli_execution(tmp_path: Path):
    output_json = tmp_path / "cli.json"
    output_md = tmp_path / "cli.md"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_obs_query5_validation.py",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(completed.stdout)
    assert summary["status"] == "pass"
    assert summary["tests_executed"] == 16
    assert json.loads(output_json.read_text(encoding="utf-8"))["tests_failed"] == 0
    assert "OBS-QUERY Validation Summary" in output_md.read_text(encoding="utf-8")
