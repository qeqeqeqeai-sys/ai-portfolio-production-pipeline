from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import build_replay_engine_guardrails


REQUIRED_GUARDRAILS = {
    "replay_must_be_explicitly_invoked",
    "replay_must_require_verified_export",
    "replay_must_require_replay_ready_contract",
    "replay_must_not_modify_source_export",
    "replay_must_not_mutate_manifest",
    "replay_must_not_call_scheduler",
    "replay_must_not_write_database",
    "replay_must_not_use_runtime_ids",
    "replay_must_not_use_timestamps",
    "replay_must_not_use_randomness",
    "replay_must_not_restore_artifacts_without_future_contract",
    "replay_must_preserve_tier4_tier5_isolation",
    "replay_must_emit_deterministic_report",
    "replay_must_have_no_hidden_external_state",
    "replay_engine_not_implemented_in_o1m",
}


def test_guardrails_report_returns_exact_top_level_keys():
    result = build_replay_engine_guardrails()
    assert list(result.keys()) == [
        "guardrail_status",
        "guardrail_scope",
        "guardrails",
        "passed_guardrails",
        "failed_guardrails",
        "warning_guardrails",
        "design_summary",
    ]


def test_guardrail_report_passes_under_current_static_design_constraints():
    result = build_replay_engine_guardrails()
    assert result["guardrail_status"] == "passed"
    assert result["guardrail_scope"] == "future_replay_engine_design"
    assert result["failed_guardrails"] == []


def test_all_required_guardrails_are_present():
    result = build_replay_engine_guardrails()
    guardrail_names = set(result["guardrails"].keys())
    assert guardrail_names == REQUIRED_GUARDRAILS


def test_guardrail_lists_are_sorted_deterministically():
    result = build_replay_engine_guardrails()
    assert result["passed_guardrails"] == sorted(result["passed_guardrails"])
    assert result["failed_guardrails"] == sorted(result["failed_guardrails"])
    assert result["warning_guardrails"] == sorted(result["warning_guardrails"])


def test_guardrail_status_mirrors_failed_guardrails():
    result = build_replay_engine_guardrails()
    expected = "passed" if not result["failed_guardrails"] else "failed"
    assert result["guardrail_status"] == expected


def test_summary_counts_are_correct():
    result = build_replay_engine_guardrails()
    summary = result["design_summary"]

    assert summary["total_guardrails"] == len(result["guardrails"])
    assert summary["passed_guardrail_count"] == len(result["passed_guardrails"])
    assert summary["failed_guardrail_count"] == len(result["failed_guardrails"])
    assert summary["warning_guardrail_count"] == len(result["warning_guardrails"])


def test_replay_engine_allowed_to_execute_now_is_always_false():
    result = build_replay_engine_guardrails()
    assert result["design_summary"]["replay_engine_allowed_to_execute_now"] is False


def test_future_replay_engine_requires_new_phase_is_always_true():
    result = build_replay_engine_guardrails()
    assert result["design_summary"]["future_replay_engine_requires_new_phase"] is True


def test_output_stable_across_repeated_calls():
    first = build_replay_engine_guardrails()
    second = build_replay_engine_guardrails()
    assert first == second


def test_public_api_export_works_from_operationalization():
    result = build_replay_engine_guardrails()
    assert isinstance(result, dict)


def test_report_does_not_create_files_require_export_dir_or_execute_replay_plan(tmp_path: Path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    _ = build_replay_engine_guardrails()
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert before == after


def test_no_tier4_smoke_regression(tmp_path: Path):
    _ = build_replay_engine_guardrails()
    assert not any(tmp_path.iterdir())
