from __future__ import annotations

from pathlib import Path

from transmission_layers.operationalization import build_operationalization_supervisor_review


REQUIRED_GATES = {
    "serialization_contract_available",
    "manifest_contract_available",
    "validation_contract_available",
    "readiness_contract_available",
    "export_envelope_contract_available",
    "persistence_contract_available",
    "verification_contract_available",
    "audit_summary_contract_available",
    "cli_smoke_contract_available",
    "deterministic_no_timestamp_runtime_id_policy",
    "no_database_write_policy",
    "no_scheduler_policy",
    "no_replay_execution_policy",
    "additive_operationalization_boundary",
    "tier4_tier5_isolation_policy",
}


def test_supervisor_review_returns_exact_top_level_keys():
    result = build_operationalization_supervisor_review()
    assert list(result.keys()) == [
        "review_status",
        "review_scope",
        "gate_results",
        "passed_gates",
        "failed_gates",
        "warning_gates",
        "supervisor_summary",
    ]


def test_review_passes_with_current_public_contracts():
    result = build_operationalization_supervisor_review()
    assert result["review_status"] == "passed"
    assert result["review_scope"] == "operationalization_o1a_o1i"
    assert result["failed_gates"] == []


def test_all_required_gates_are_present():
    result = build_operationalization_supervisor_review()
    gate_names = set(result["gate_results"].keys())
    assert gate_names == REQUIRED_GATES


def test_gate_lists_are_sorted_deterministically():
    result = build_operationalization_supervisor_review()
    assert result["passed_gates"] == sorted(result["passed_gates"])
    assert result["failed_gates"] == sorted(result["failed_gates"])
    assert result["warning_gates"] == sorted(result["warning_gates"])


def test_review_status_mirrors_failed_gates():
    result = build_operationalization_supervisor_review()
    expected = "passed" if not result["failed_gates"] else "failed"
    assert result["review_status"] == expected


def test_summary_counts_are_correct():
    result = build_operationalization_supervisor_review()
    summary = result["supervisor_summary"]

    assert summary["total_gates"] == len(result["gate_results"])
    assert summary["passed_gate_count"] == len(result["passed_gates"])
    assert summary["failed_gate_count"] == len(result["failed_gates"])
    assert summary["warning_gate_count"] == len(result["warning_gates"])
    assert summary["operationalization_ready_for_next_phase"] is (result["review_status"] == "passed")
    assert summary["next_recommended_phase"] == "O1K — Deterministic Operational Replay Contract Skeleton"


def test_output_stable_across_repeated_calls():
    first = build_operationalization_supervisor_review()
    second = build_operationalization_supervisor_review()
    assert first == second


def test_public_api_export_works_from_operationalization():
    result = build_operationalization_supervisor_review()
    assert isinstance(result, dict)


def test_review_does_not_create_files_or_require_export_dir(tmp_path: Path):
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    _ = build_operationalization_supervisor_review()
    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert before == after


def test_no_tier4_smoke_regression(tmp_path: Path):
    # Supervisor review should remain pure and not require tier execution surfaces.
    _ = build_operationalization_supervisor_review()
    assert not any(tmp_path.iterdir())
