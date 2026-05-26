from pathlib import Path

from transmission_layers.expectation_failure.replay_ecology import (
    lr6_live13_controlled_replay_density_pilot_readiness_and_governance_saturation_precheck as live13,
)


def test_api_existence():
    names = [
        "build_lr6_live13_density_pilot_readiness_context",
        "build_lr6_live13_density_pilot_sequences",
        "build_lr6_live13_density_snapshot",
        "build_lr6_live13_governance_saturation_review",
        "build_lr6_live13_density_telemetry_review",
        "build_lr6_live13_density_pressure_classification",
        "build_lr6_live13_density_continuity_review",
        "build_lr6_live13_governance_saturation_safeguards",
        "build_lr6_live13_density_risk_review",
        "build_lr6_live13_live14_readiness_gate",
        "build_lr6_live13_supervisor_review",
        "build_lr6_live13_markdown_report",
        "certify_lr6_live13_density_precheck_boundary",
    ]
    for n in names:
        assert hasattr(live13, n)


def test_fixture_determinism_and_baseline_stability():
    assert live13.build_lr6_live13_density_pilot_sequences() == live13.build_lr6_live13_density_pilot_sequences()
    baseline = live13.build_lr6_live13_density_pilot_sequences()["baseline_density_control"]
    review = live13.build_lr6_live13_governance_saturation_review("baseline_density_control", baseline)
    assert review["monitoring_load_pressure"] == "low"
    assert review["telemetry_coherence"] is True


def test_modest_density_remains_bounded_and_coherent():
    seq = live13.build_lr6_live13_density_pilot_sequences()["modest_density_increase"]
    review = live13.build_lr6_live13_governance_saturation_review("modest_density_increase", seq)
    assert review["rows"] == 6
    assert review["boundedness_integrity"] is True
    assert review["telemetry_coherence"] is True


def test_saturation_warning_and_failure_classification():
    seqs = live13.build_lr6_live13_density_pilot_sequences()
    warn = live13.build_lr6_live13_density_pressure_classification(
        live13.build_lr6_live13_governance_saturation_review("governance_saturation_warning", seqs["governance_saturation_warning"])
    )
    fail = live13.build_lr6_live13_density_pressure_classification(
        live13.build_lr6_live13_governance_saturation_review("governance_saturation_failure", seqs["governance_saturation_failure"])
    )
    assert warn["classification"] in {"MODERATE_GOVERNANCE_PRESSURE", "HIGH_GOVERNANCE_SATURATION"}
    assert fail["classification"] == "HIGH_GOVERNANCE_SATURATION"


def test_duplicate_and_identity_pressure_handling():
    seqs = live13.build_lr6_live13_density_pilot_sequences()
    id_review = live13.build_lr6_live13_governance_saturation_review("replay_identity_pressure", seqs["replay_identity_pressure"])
    dup_review = live13.build_lr6_live13_governance_saturation_review("duplicate_prevention_pressure", seqs["duplicate_prevention_pressure"])
    assert id_review["replay_identity_stability"] is False
    assert dup_review["duplicate_prevention_reliability"] is False


def test_telemetry_coherence_and_live11_live12_assumptions_intact():
    continuity = live13.build_lr6_live13_density_continuity_review()
    assert continuity["continuity_telemetry_coherent"] is True
    assert continuity["live11_drift_telemetry_scenario_derived"] is True
    assert continuity["live12_continuity_validation_functional"] is True


def test_live14_readiness_gate_behavior():
    telemetry = live13.build_lr6_live13_density_telemetry_review()
    classifications = {k: live13.build_lr6_live13_density_pressure_classification(v) for k, v in telemetry.items()}
    gate = live13.build_lr6_live13_live14_readiness_gate(classifications)
    assert gate["live14_readiness_gate"] in {
        "LIVE14_BLOCKED",
        "LIVE14_CONDITIONALLY_ELIGIBLE",
        "LIVE14_READY_FOR_BOUNDED_PILOT_PRECHECK",
    }
    assert gate["scaling_authorization_granted"] is False


def test_exact_boundary_flags_no_forbidden_paths_and_no_live_persistence_dependencies():
    assert live13.certify_lr6_live13_density_precheck_boundary() == {
        "readiness_assessment_only": True,
        "synthetic_density_only": True,
        "live_density_expansion_enabled": False,
        "scaling_enabled": False,
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


def test_report_section_completeness_and_file_heading():
    review = live13.build_lr6_live13_supervisor_review()
    md = live13.build_lr6_live13_markdown_report(review)
    for section in [
        "## objective",
        "## density readiness context",
        "## synthetic density scenarios",
        "## governance saturation telemetry findings",
        "## density pressure classifications",
        "## continuity-under-density findings",
        "## governance saturation safeguards",
        "## LIVE14 readiness gate findings",
        "## governance boundary certification",
        "## residual risks",
        "## recommendation",
    ]:
        assert section in md
    text = str(review)
    assert "live_density_expansion_enabled': False" in text
    report_path = Path("reports/lr6_live13_controlled_replay_density_pilot_readiness_and_governance_saturation_precheck.md")
    assert report_path.exists()
    assert "# LR6-LIVE13 — Controlled Replay Density Pilot Readiness & Governance Saturation Precheck" in report_path.read_text(encoding="utf-8")
