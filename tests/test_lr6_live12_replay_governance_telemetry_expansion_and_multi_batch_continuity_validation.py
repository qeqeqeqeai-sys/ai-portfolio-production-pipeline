from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live12_replay_governance_telemetry_expansion_and_multi_batch_continuity_validation as live12,
)


def test_api_existence():
    names = [
        "build_lr6_live12_multi_batch_telemetry_context",
        "build_lr6_live12_synthetic_multi_batch_sequences",
        "build_lr6_live12_batch_snapshot",
        "build_lr6_live12_multi_batch_continuity_review",
        "build_lr6_live12_multi_batch_anomaly_classification",
        "build_lr6_live12_live11_telemetry_bridge_review",
        "build_lr6_live12_supervisor_review",
        "build_lr6_live12_markdown_report",
        "certify_lr6_live12_multi_batch_boundary",
    ]
    for n in names:
        assert hasattr(live12, n)


def test_fixture_determinism_and_stable_pass():
    assert live12.build_lr6_live12_synthetic_multi_batch_sequences() == live12.build_lr6_live12_synthetic_multi_batch_sequences()
    seq = live12.build_lr6_live12_synthetic_multi_batch_sequences()["stable_multi_batch_sequence"]
    review = live12.build_lr6_live12_multi_batch_continuity_review("stable_multi_batch_sequence", seq)
    assert review["continuity_pass"] is True
    assert review["violations"] == []


def test_detects_continuity_anomalies():
    sequences = live12.build_lr6_live12_synthetic_multi_batch_sequences()
    assert "INTRA_BATCH_WAVE_FRAGMENTATION" in live12.build_lr6_live12_multi_batch_continuity_review("x", sequences["wave_fragmentation_batch_sequence"])["violations"]
    assert "CROSS_BATCH_WAVE_COLLISION" in live12.build_lr6_live12_multi_batch_continuity_review("x", sequences["cross_batch_wave_collision_sequence"])["violations"]
    assert "CROSS_BATCH_DUPLICATE_KEY_COLLISION" in live12.build_lr6_live12_multi_batch_continuity_review("x", sequences["duplicate_key_cross_batch_sequence"])["violations"]
    assert "MULTI_BATCH_METRIC_SCOPE_VIOLATION" in live12.build_lr6_live12_multi_batch_continuity_review("x", sequences["metric_scope_violation_sequence"])["violations"]
    assert "MULTI_BATCH_APPEND_ONLY_BOUNDARY_VIOLATION" in live12.build_lr6_live12_multi_batch_continuity_review("x", sequences["append_only_boundary_violation_sequence"])["violations"]


def test_boundedness_violation_detected_if_simulated():
    sequence = live12.build_lr6_live12_synthetic_multi_batch_sequences()["stable_multi_batch_sequence"]
    sequence[0]["rows"] = 999
    review = live12.build_lr6_live12_multi_batch_continuity_review("stable", sequence)
    assert "MULTI_BATCH_BOUNDEDNESS_VIOLATION" in review["violations"]


def test_live11_bridge_scenario_derived_drift_rules():
    seqs = live12.build_lr6_live12_synthetic_multi_batch_sequences()
    stable = live12.build_lr6_live12_live11_telemetry_bridge_review("stable", seqs["stable_multi_batch_sequence"])
    degrading = live12.build_lr6_live12_live11_telemetry_bridge_review("degrading", seqs["degrading_governance_sequence"])
    improving = live12.build_lr6_live12_live11_telemetry_bridge_review("improving", seqs["improving_governance_sequence"])
    assert stable["governance_drift_detected"] is False
    assert degrading["governance_drift_detected"] is True
    assert improving["governance_drift_detected"] is False
    assert stable["drift_is_scenario_derived"] is True


def test_boundary_flags_and_no_forbidden_paths():
    b = live12.certify_lr6_live12_multi_batch_boundary()
    assert b == {
        "governance_telemetry_only": True,
        "multi_batch_validation_only": True,
        "live_persistence_enabled": False,
        "scaling_enabled": False,
        "new_replay_metrics_enabled": False,
        "topology_drift_enabled": False,
        "contradiction_persistence_migration_enabled": False,
        "prediction_enabled": False,
        "trading_enabled": False,
        "auto_expansion_enabled": False,
        "schema_expansion_enabled": False,
        "historical_row_rewrite_enabled": False,
        "replay_richness_only": True,
        "append_only_required": True,
        "deterministic_governance_required": True,
    }


def test_report_sections_and_no_live_persistence_dependencies():
    review = live12.build_lr6_live12_supervisor_review()
    md = live12.build_lr6_live12_markdown_report(review)
    for section in [
        "## objective",
        "## multi-batch telemetry context",
        "## synthetic multi-batch sequence inventory",
        "## continuity validation findings",
        "## cross-batch anomaly classifications",
        "## LIVE11 telemetry bridge findings",
        "## governance boundary certification",
        "## residual risks",
        "## LIVE13 recommendation",
    ]:
        assert section in md
    text = str(review)
    assert "live_persistence_enabled': False" in text
    assert "scaling_enabled': False" in text


def test_report_file_exists_and_has_required_heading():
    report_path = Path("reports/lr6_live12_replay_governance_telemetry_expansion_and_multi_batch_continuity_validation.md")
    assert report_path.exists()
    content = report_path.read_text(encoding="utf-8")
    assert "# LR6-LIVE12 — Replay Governance Telemetry Expansion & Multi-Batch Continuity Validation" in content
