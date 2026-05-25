from pathlib import Path

from transmission_layers.expectation_failure.semantic_ecosystem.sde1d_readiness_certification import (
    build_sde1d_contradiction_density_diagnostics,
    build_sde1d_ecosystem_coverage_diagnostics,
    build_sde1d_governance_certification,
    build_sde1d_low_information_risk_diagnostics,
    build_sde1d_monoculture_risk_diagnostics,
    build_sde1d_propagation_pathway_diagnostics,
    build_sde1d_readiness_report_payload,
    build_sde1d_regime_exposure_diagnostics,
    build_sde1d_topology_richness_diagnostics,
    certify_sde1d_semantic_ecosystem_readiness,
    load_sde1d_pruned_universe,
)

CONFIG = Path("configs/sde1c_pruned_entity_universe.yaml")
MODULE_PATH = Path("transmission_layers/expectation_failure/semantic_ecosystem/sde1d_readiness_certification.py")


def _loaded():
    return load_sde1d_pruned_universe(CONFIG)


def test_readiness_certification_determinism():
    data = _loaded()
    assert certify_sde1d_semantic_ecosystem_readiness(data) == certify_sde1d_semantic_ecosystem_readiness(data)


def test_ecosystem_coverage_completeness():
    d = build_sde1d_ecosystem_coverage_diagnostics(_loaded())
    assert d["ecosystem_coverage_completeness"] == 1.0
    assert d["ecosystem_balance_score"] > 0.85


def test_topology_richness_calculation():
    d = build_sde1d_topology_richness_diagnostics(_loaded())
    assert d["average_propagation_links"] >= 2.0
    assert d["topology_richness_score"] >= 0.75


def test_contradiction_density_calculation():
    d = build_sde1d_contradiction_density_diagnostics(_loaded())
    assert d["average_contradiction_surfaces"] >= 1.5
    assert d["contradiction_density_score"] >= 0.7


def test_propagation_pathway_calculation():
    d = build_sde1d_propagation_pathway_diagnostics(_loaded())
    assert d["propagation_role_diversity"] >= 4
    assert d["propagation_pathway_richness_score"] >= 0.75


def test_regime_exposure_diversity_calculation():
    d = build_sde1d_regime_exposure_diagnostics(_loaded())
    assert d["unique_regime_exposures"] >= 4
    assert d["regime_exposure_diversity_score"] >= 0.6


def test_monoculture_risk_detection():
    d = build_sde1d_monoculture_risk_diagnostics(_loaded())
    assert d["max_primary_ecosystem_share"] <= 0.2
    assert d["monoculture_risk_score"] < 0.8


def test_low_information_risk_detection():
    d = build_sde1d_low_information_risk_diagnostics(_loaded())
    assert d["low_information_entity_count"] >= 1
    assert d["low_information_risk_score"] <= 0.7


def test_readiness_threshold_behavior():
    c = certify_sde1d_semantic_ecosystem_readiness(_loaded())
    assert c["topology_readiness_score"] >= c["readiness_threshold"]
    assert c["lr6_reactivation_readiness_flag"] is True


def test_lr6_not_reactivated_and_no_unsafe_paths_introduced():
    text = MODULE_PATH.read_text().lower() + str(build_sde1d_governance_certification()).lower()
    banned_patterns = [
        "execute_replay",
        "run_replay",
        "persist_",
        "write_",
        "insert_into",
        "create table",
        "drop table",
        "select ",
        "http://",
        "https://",
        "requests.",
        "trading_signal",
        "buy_signal",
        "sell_signal",
    ]
    allowed_markers = {"no_replay_execution_introduced", "no_persistence_write_path_introduced"}
    for marker in allowed_markers:
        assert marker in text
    for pattern in banned_patterns:
        if pattern in {"persist_", "write_"}:
            sanitized = text
            for marker in allowed_markers:
                sanitized = sanitized.replace(marker, "")
            assert pattern not in sanitized
        else:
            assert pattern not in text


def test_additive_architecture_preserved():
    assert MODULE_PATH.exists()
    assert Path("configs/sde1d_semantic_ecosystem_readiness_certification.yaml").exists()
    assert Path("reports/sde1d_semantic_ecosystem_readiness_certification.md").exists()


def test_report_payload_contains_expected_dimensions():
    payload = build_sde1d_readiness_report_payload(_loaded())
    diagnostics = payload["diagnostics"]
    for key in [
        "ecosystem_coverage_completeness",
        "ecosystem_balance_score",
        "cross_ecosystem_connectivity_score",
        "contradiction_density_score",
        "propagation_pathway_richness_score",
        "regime_exposure_diversity_score",
        "monoculture_risk_score",
        "low_information_risk_score",
        "topology_readiness_score",
        "lr6_reactivation_readiness_flag",
    ]:
        assert key in diagnostics
