from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live15_governance_recertification_under_ultra_bounded_operational_replay_conditions as live15,
)


def test_api_surface_exists():
    names = [
        "build_lr6_live15_governance_recertification_context",
        "build_lr6_live15_operational_recertification_sequences",
        "build_lr6_live15_operational_snapshot",
        "build_lr6_live15_operational_telemetry_review",
        "build_lr6_live15_longitudinal_governance_review",
        "build_lr6_live15_governance_recertification_classification",
        "build_lr6_live15_longitudinal_continuity_review",
        "build_lr6_live15_recertification_safeguards",
        "build_lr6_live15_recertification_risk_review",
        "build_lr6_live15_post_pilot_discussion_gate",
        "build_lr6_live15_supervisor_review",
        "build_lr6_live15_markdown_report",
        "certify_lr6_live15_recertification_boundary",
    ]
    for n in names:
        assert hasattr(live15, n)


def test_operational_sequence_determinism_and_coherence():
    assert live15.build_lr6_live15_operational_recertification_sequences() == live15.build_lr6_live15_operational_recertification_sequences()
    seqs = live15.build_lr6_live15_operational_recertification_sequences()
    stable = seqs["stable_operational_recertification_cycle"]
    review = live15.build_lr6_live15_operational_telemetry_review("stable_operational_recertification_cycle", stable)
    assert review["replay_identity_continuity"] is True
    assert review["duplicate_prevention_continuity"] is True
    assert review["governance_telemetry_coherence"] == "coherent"


def test_pressure_and_degradation_detection():
    seqs = live15.build_lr6_live15_operational_recertification_sequences()
    repeated = live15.build_lr6_live15_operational_telemetry_review("repeated_operational_pressure_cycle", seqs["repeated_operational_pressure_cycle"])
    identity = live15.build_lr6_live15_operational_telemetry_review("replay_identity_recertification_pressure", seqs["replay_identity_recertification_pressure"])
    duplicate = live15.build_lr6_live15_operational_telemetry_review("duplicate_prevention_recertification_pressure", seqs["duplicate_prevention_recertification_pressure"])
    telemetry = live15.build_lr6_live15_operational_telemetry_review("telemetry_coherence_recertification_pressure", seqs["telemetry_coherence_recertification_pressure"])
    assert repeated["operational_replay_pressure_accumulation"] == "high"
    assert identity["replay_identity_continuity"] is False
    assert duplicate["duplicate_prevention_continuity"] is False
    assert telemetry["governance_telemetry_coherence"] == "degraded"


def test_classification_and_gate_behavior():
    seqs = live15.build_lr6_live15_operational_recertification_sequences()
    warning = live15.build_lr6_live15_governance_recertification_classification(
        live15.build_lr6_live15_operational_telemetry_review("governance_recertification_warning", seqs["governance_recertification_warning"])
    )
    failure = live15.build_lr6_live15_governance_recertification_classification(
        live15.build_lr6_live15_operational_telemetry_review("governance_recertification_failure", seqs["governance_recertification_failure"])
    )
    assert warning["classification"] in {"GOVERNANCE_RECERTIFICATION_AT_RISK", "GOVERNANCE_RECERTIFIED_WITH_WARNINGS"}
    assert failure["classification"] == "GOVERNANCE_RECERTIFICATION_FAILED"

    gate_blocked = live15.build_lr6_live15_post_pilot_discussion_gate({"failure": failure})
    assert gate_blocked["post_live15_pilot_discussion_gate"] == "POST_LIVE15_PILOT_DISCUSSION_BLOCKED"


def test_longitudinal_continuity_safeguards_boundary_and_report():
    continuity = live15.build_lr6_live15_longitudinal_continuity_review()
    assert continuity["live11_telemetry_scenario_derived"] is True
    assert continuity["live12_multi_batch_continuity_functional"] is True
    assert continuity["live13_saturation_telemetry_coherent"] is True
    assert continuity["live14_operational_transition_telemetry_coherent"] is True
    assert continuity["append_only_continuity_preserved"] is True
    assert continuity["replay_identity_fragmentation_detected"] is True
    assert continuity["operational_replay_observability_preserved"] is True
    assert continuity["no_governance_auditability_gaps"] is True

    safeguards = live15.build_lr6_live15_recertification_safeguards()
    assert "longitudinal_governance_instability_guard" in safeguards

    boundary = live15.certify_lr6_live15_recertification_boundary()
    assert boundary == {
        "governance_recertification_only": True,
        "ultra_bounded_operational_replay_only": True,
        "broad_scaling_enabled": False,
        "replay_density_scaling_enabled": False,
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

    review = live15.build_lr6_live15_supervisor_review()
    md = live15.build_lr6_live15_markdown_report(review)
    required_sections = [
        "## objective",
        "## governance re-certification context",
        "## repeated operational replay sequences",
        "## longitudinal governance telemetry findings",
        "## governance re-certification classifications",
        "## longitudinal continuity findings",
        "## governance safeguards",
        "## post-LIVE15 pilot discussion findings",
        "## governance boundary certification",
        "## residual risks",
        "## recommendation",
    ]
    for section in required_sections:
        assert section in md


def test_report_file_exists():
    report_path = Path("reports/lr6_live15_governance_recertification_under_ultra_bounded_operational_replay_conditions.md")
    assert report_path.exists()
    assert "# LR6-LIVE15 — Governance Re-Certification Under Ultra-Bounded Operational Replay Conditions" in report_path.read_text(encoding="utf-8")
