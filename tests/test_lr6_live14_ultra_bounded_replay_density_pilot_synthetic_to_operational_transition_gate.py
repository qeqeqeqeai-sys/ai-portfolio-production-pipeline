from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live14_ultra_bounded_replay_density_pilot_synthetic_to_operational_transition_gate as live14,
)


def test_api_existence():
    names = [
        "build_lr6_live14_ultra_bounded_transition_context",
        "build_lr6_live14_ultra_bounded_sequences",
        "build_lr6_live14_transition_snapshot",
        "build_lr6_live14_transition_telemetry_review",
        "build_lr6_live14_operational_transition_review",
        "build_lr6_live14_transition_pressure_classification",
        "build_lr6_live14_transition_continuity_review",
        "build_lr6_live14_transition_safeguards",
        "build_lr6_live14_transition_risk_review",
        "build_lr6_live14_live15_eligibility_gate",
        "build_lr6_live14_supervisor_review",
        "build_lr6_live14_markdown_report",
        "certify_lr6_live14_transition_boundary",
    ]
    for n in names:
        assert hasattr(live14, n)


def test_ultra_bounded_sequence_determinism_and_control_coherence():
    assert live14.build_lr6_live14_ultra_bounded_sequences() == live14.build_lr6_live14_ultra_bounded_sequences()
    control = live14.build_lr6_live14_ultra_bounded_sequences()["ultra_bounded_control"]
    review = live14.build_lr6_live14_transition_telemetry_review("ultra_bounded_control", control)
    assert review["operational_transition_pressure"] in {"low", "moderate"}
    assert review["governance_auditability_continuity"] is True


def test_operational_transition_pressure_and_failure_classification():
    seqs = live14.build_lr6_live14_ultra_bounded_sequences()
    moderate = live14.build_lr6_live14_transition_pressure_classification(
        live14.build_lr6_live14_transition_telemetry_review("operational_transition_pressure", seqs["operational_transition_pressure"])
    )
    failure = live14.build_lr6_live14_transition_pressure_classification(
        live14.build_lr6_live14_transition_telemetry_review("governance_transition_failure", seqs["governance_transition_failure"])
    )
    assert moderate["classification"] in {"LOW_TRANSITION_PRESSURE", "MODERATE_TRANSITION_PRESSURE"}
    assert failure["classification"] == "HIGH_TRANSITION_PRESSURE"


def test_identity_and_duplicate_transition_pressure_handling():
    seqs = live14.build_lr6_live14_ultra_bounded_sequences()
    identity = live14.build_lr6_live14_transition_telemetry_review("replay_identity_transition_pressure", seqs["replay_identity_transition_pressure"])
    duplicate = live14.build_lr6_live14_transition_telemetry_review("duplicate_prevention_transition_pressure", seqs["duplicate_prevention_transition_pressure"])
    assert identity["replay_identity_continuity"] is False
    assert duplicate["duplicate_prevention_continuity"] is False


def test_telemetry_coherence_and_live11_live12_live13_continuity_intact():
    continuity = live14.build_lr6_live14_transition_continuity_review()
    assert continuity["append_only_continuity_preserved"] is True
    assert continuity["live11_telemetry_scenario_derived"] is True
    assert continuity["live12_multi_batch_continuity_functional"] is True
    assert continuity["live13_saturation_telemetry_coherent"] is True


def test_safeguards_and_live15_gate_classification_behavior():
    safeguards = live14.build_lr6_live14_transition_safeguards()
    assert "operational_transition_overload_guard" in safeguards
    telemetry = live14.build_lr6_live14_operational_transition_review()
    classifications = {k: live14.build_lr6_live14_transition_pressure_classification(v) for k, v in telemetry.items()}
    gate = live14.build_lr6_live14_live15_eligibility_gate(classifications)
    assert gate["live15_eligibility_gate"] in {
        "LIVE15_BLOCKED",
        "LIVE15_CONDITIONALLY_ELIGIBLE",
        "LIVE15_READY_FOR_RECERTIFICATION_PRECHECK",
    }
    assert gate["scaling_authorized"] is False


def test_exact_boundary_flags_no_forbidden_expansion_paths_or_live_dependencies():
    assert live14.certify_lr6_live14_transition_boundary() == {
        "ultra_bounded_transition_only": True,
        "synthetic_operational_transition_only": True,
        "live_density_scaling_enabled": False,
        "broad_scaling_enabled": False,
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


def test_report_section_completeness_and_report_file_presence():
    review = live14.build_lr6_live14_supervisor_review()
    md = live14.build_lr6_live14_markdown_report(review)
    for section in [
        "## objective",
        "## transition context",
        "## ultra-bounded pilot scenarios",
        "## operational-transition telemetry findings",
        "## transition pressure classifications",
        "## continuity findings",
        "## governance transition safeguards",
        "## LIVE15 eligibility findings",
        "## governance boundary certification",
        "## residual risks",
        "## recommendation",
    ]:
        assert section in md
    text = str(review)
    assert "'broad_scaling_enabled': False" in text
    report_path = Path("reports/lr6_live14_ultra_bounded_replay_density_pilot_synthetic_to_operational_transition_gate.md")
    assert report_path.exists()
    assert "# LR6-LIVE14 — Ultra-Bounded Replay Density Pilot (Synthetic-to-Operational Transition Gate)" in report_path.read_text(encoding="utf-8")
