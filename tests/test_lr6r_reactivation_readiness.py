from transmission_layers.expectation_failure.replay_ecology.lr6r_reactivation_readiness import (
    build_lr6r_bounded_dry_run_framework,
    build_lr6r_contradiction_density_requirements,
    build_lr6r_governance_boundary_inventory,
    build_lr6r_monoculture_protection_rules,
    build_lr6r_propagation_richness_requirements,
    build_lr6r_readiness_report_payload,
    build_lr6r_reactivation_prerequisites,
    build_lr6r_replay_ecology_gating_rules,
    build_lr6r_replay_saturation_protection,
    build_lr6r_semantic_diversity_requirements,
    certify_lr6r_readiness_plan,
)


def test_lr6r_readiness_plan_determinism() -> None:
    assert build_lr6r_readiness_report_payload() == build_lr6r_readiness_report_payload()


def test_bounded_replay_constraints_presence() -> None:
    bounded = build_lr6r_bounded_dry_run_framework()
    assert bounded["bounded_replay_window_days_max"] == 30
    assert bounded["execution_mode"] == "readiness_planning_only"


def test_dry_run_first_enforcement_presence() -> None:
    gating = build_lr6r_replay_ecology_gating_rules()
    assert gating["dry_run_first_required"] is True


def test_replay_saturation_protection_presence() -> None:
    saturation = build_lr6r_replay_saturation_protection()
    assert saturation["replay_saturation_limit"] > 0


def test_semantic_diversity_threshold_presence() -> None:
    diversity = build_lr6r_semantic_diversity_requirements()
    assert diversity["semantic_diversity_floor"] >= 0.7


def test_contradiction_richness_threshold_presence() -> None:
    contradiction = build_lr6r_contradiction_density_requirements()
    assert contradiction["contradiction_density_floor"] > 0.5


def test_propagation_richness_threshold_presence() -> None:
    propagation = build_lr6r_propagation_richness_requirements()
    assert propagation["propagation_richness_floor"] > 0.6


def test_monoculture_protection_presence() -> None:
    mono = build_lr6r_monoculture_protection_rules()
    assert mono["primary_ecosystem_share_cap"] < 0.25


def test_governance_certification_presence() -> None:
    cert = certify_lr6r_readiness_plan()
    assert cert["readiness_plan_certified"] is True


def test_lr6_not_activated() -> None:
    cert = certify_lr6r_readiness_plan()
    prereq = build_lr6r_reactivation_prerequisites()
    assert cert["lr6_reactivation_state"] == "not_reactivated"
    assert prereq["lr6_replay_execution_reactivated"] is False


def test_no_replay_execution_or_forbidden_paths_introduced() -> None:
    boundaries = build_lr6r_governance_boundary_inventory()
    assert boundaries["no_replay_execution"] is True
    assert boundaries["no_persistence_writes"] is True
    assert boundaries["no_direct_sql"] is True
    assert boundaries["no_external_apis"] is True
    assert boundaries["additive_architecture_preserved"] is True
