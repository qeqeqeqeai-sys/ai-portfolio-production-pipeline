from __future__ import annotations

from pathlib import Path

from unittest.mock import patch

from transmission_layers.operationalization import (
    build_operational_certification_gates,
    run_operational_certification_closure,
    run_recovery_historical_closure,
    run_replay_observability_closure,
)
from transmission_layers.operationalization.export_envelope import build_manifest_export_envelope
from transmission_layers.operationalization.export_persistence import persist_manifest_export_envelope
from transmission_layers.operationalization.manifests import empty_manifest
from transmission_layers.operationalization.serialization import stable_serialize


def _required_kwargs():
    return {
        "run_id": "run_20260522_2001",
        "run_type": "tier4_structural_simulation",
        "tier_scope": "tier4",
        "generated_at_sgt": "2026-05-22T08:00:00+08:00",
    }


def _persist_valid_fixture(tmp_path: Path) -> tuple[dict, Path]:
    manifest = empty_manifest(**_required_kwargs())
    persisted = persist_manifest_export_envelope(manifest, tmp_path)
    return manifest, Path(persisted["export_path"])


def _write_envelope(path: Path, envelope: dict) -> None:
    path.write_text(stable_serialize(envelope), encoding="utf-8")


def test_deterministic_repeated_output(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert run_operational_certification_closure(export_path) == run_operational_certification_closure(export_path)


def test_checksum_stability(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    first = run_operational_certification_closure(export_path)
    second = run_operational_certification_closure(export_path)
    assert first["checksum"] == second["checksum"]


def test_certified_ready_case(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_operational_certification_closure(export_path)
    assert result["status"] == "certified"
    assert result["certification"]["trust_status"] == "operationally_trusted"
    assert result["certification"]["operational_closure_complete"] is True


def test_certified_with_findings_or_blocked_case(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_summary"]["readiness_status"] = "blocked"
    _write_envelope(export_path, envelope)

    result = run_operational_certification_closure(export_path)
    assert result["status"] in {"certified_with_findings", "degraded", "blocked"}


def test_blocked_case(tmp_path: Path):
    manifest, export_path = _persist_valid_fixture(tmp_path)
    envelope = build_manifest_export_envelope(manifest)
    envelope["export_ready"] = False
    _write_envelope(export_path, envelope)

    result = run_operational_certification_closure(export_path)
    assert result["status"] == "blocked"
    assert result["certification"]["trust_status"] == "not_trusted"


def test_invalid_input_case(tmp_path: Path):
    result = run_operational_certification_closure(tmp_path / "missing.json")
    assert result["status"] == "invalid_input"
    assert result["certification"]["trust_status"] == "invalid_input"


def test_closure_boundary_and_invariants(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    result = run_operational_certification_closure(export_path)
    assert result["closure_boundary"]["further_operationalization_allowed"] is False
    assert result["closure_boundary"]["allowed_only_for_intelligence_risk_gap"] is True
    assert result["closure_boundary"]["prevents_infrastructure_sprawl"] is True
    assert result["invariants"]["executes_runtime_logic"] is False
    assert result["invariants"]["restores_artifacts"] is False
    assert result["invariants"]["mutates_external_state"] is False


def test_certification_gate_ordering_and_no_runtime_flags(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    gates = build_operational_certification_gates(export_path)["gates"]
    names = [gate["gate"] for gate in gates]
    assert names == [
        "replay_determinism",
        "checksum_stability",
        "immutable_input_safety",
        "observability_completeness",
        "recovery_safety",
        "historical_reconstruction_sufficiency",
        "no_runtime_replay_execution",
        "no_artifact_restore",
        "no_external_mutation",
        "no_prediction",
        "no_optimization",
        "no_adaptive_control",
        "additive_only_operational_architecture",
    ]
    invariant_gate_map = {gate["gate"]: gate["result"] for gate in gates}
    assert invariant_gate_map["no_runtime_replay_execution"] == "PASS"
    assert invariant_gate_map["no_artifact_restore"] == "PASS"


def test_no_writes_no_mutation(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    before_text = export_path.read_text(encoding="utf-8")
    before_mtime = export_path.stat().st_mtime_ns
    _ = run_operational_certification_closure(export_path)
    assert before_text == export_path.read_text(encoding="utf-8")
    assert before_mtime == export_path.stat().st_mtime_ns



def test_degraded_status_case_with_failed_gate(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)

    o1 = run_replay_observability_closure(export_path)
    o2 = run_recovery_historical_closure(export_path)
    o1["status"] = "degraded"
    o1["replay_integrity"]["deterministic_repeated_output"] = False

    with patch("transmission_layers.operationalization.operational_certification_closure.run_replay_observability_closure", return_value=o1), patch(
        "transmission_layers.operationalization.operational_certification_closure.run_recovery_historical_closure", return_value=o2
    ):
        result = run_operational_certification_closure(export_path)

    assert result["status"] == "degraded"
    assert result["certification"]["trust_status"] == "not_trusted"

def test_public_api_export(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert isinstance(build_operational_certification_gates(export_path), dict)
    assert isinstance(run_operational_certification_closure(export_path), dict)


def test_o1_o2_non_regression(tmp_path: Path):
    _, export_path = _persist_valid_fixture(tmp_path)
    assert run_replay_observability_closure(export_path)["status"] == "ready"
    assert run_recovery_historical_closure(export_path)["status"] == "ready"
