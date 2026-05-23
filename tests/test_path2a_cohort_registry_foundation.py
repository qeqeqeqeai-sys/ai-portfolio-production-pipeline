from copy import deepcopy

from transmission_layers.expectation_failure import *


def _valid_inputs():
    cohorts = [
        {
            "cohort_id": "sector_semiconductors",
            "cohort_version": "2026.05",
            "cohort_type": "sector",
            "members": ["NVDA", "AMD", "INTC"],
            "inclusion_rationale": "GICS sector alignment",
            "exclusion_rules": ["exclude_missing_ticker"],
        },
        {
            "cohort_id": "stability_large_cap",
            "cohort_version": "2026.05",
            "cohort_type": "stability",
            "members": ["MSFT", "AAPL", "GOOGL"],
            "inclusion_rationale": "Stable mega-cap population",
            "exclusion_rules": ["exclude_unlisted"],
        },
    ]
    benchmark_map = {
        "sector_semiconductors": "SOXX",
        "stability_large_cap": "SPY",
    }
    return cohorts, benchmark_map


def test_public_api_export_presence_and_path1_smoke():
    required = [
        "build_cohort_registry_contracts",
        "build_cohort_manifest",
        "resolve_cohort_membership",
        "build_benchmark_mapping_registry",
        "validate_cohort_integrity",
        "build_cohort_explainability_metadata",
        "certify_cohort_registry",
        "build_path2a_cohort_registry_report",
        "CERTIFIED_COHORT_REGISTRY",
        "DEGRADED_COHORT_REGISTRY",
        "BLOCKED_COHORT_REGISTRY",
    ]
    for name in required:
        assert name in globals()

    assert callable(build_phase_b4_historical_replay_report)


def test_determinism_checksum_stability_and_immutability():
    cohorts, bm = _valid_inputs()
    c0, b0 = deepcopy(cohorts), deepcopy(bm)
    m1 = build_cohort_manifest(cohorts, bm)
    m2 = build_cohort_manifest(cohorts, bm)
    assert m1 == m2
    assert m1["manifest_checksum"] == m2["manifest_checksum"]
    assert cohorts == c0 and bm == b0


def test_allowed_and_blocked_cohort_types_and_missing_fields():
    cohorts, bm = _valid_inputs()
    bad = deepcopy(cohorts[0])
    bad["cohort_type"] = "unsupported"
    bad["cohort_id"] = ""
    bad["cohort_version"] = ""
    bad["members"] = []
    manifest = build_cohort_manifest([bad], bm)
    cert = certify_cohort_registry(manifest)
    assert cert["decision_status"] == BLOCKED_COHORT_REGISTRY


def test_duplicate_member_validation_and_deterministic_member_ordering():
    resolved = resolve_cohort_membership(["B", "A", "B", "A", "C"])
    assert resolved["members"] == ["A", "B", "C"]
    assert resolved["duplicate_members_detected"] is True


def test_valid_and_invalid_benchmark_mapping_outcomes():
    cohorts, bm = _valid_inputs()
    manifest_ok = build_cohort_manifest(cohorts, bm)
    assert certify_cohort_registry(manifest_ok)["decision_status"] == CERTIFIED_COHORT_REGISTRY

    manifest_bad = build_cohort_manifest(cohorts, {"sector_semiconductors": "SOXX"})
    assert certify_cohort_registry(manifest_bad)["decision_status"] == DEGRADED_COHORT_REGISTRY


def test_explainability_metadata_completeness_and_forbidden_inventory():
    cohorts, _ = _valid_inputs()
    metadata = build_cohort_explainability_metadata(cohorts[0])
    assert metadata["methodology"] == "deterministic_static_rule_set"
    assert metadata["inclusion_rationale"]
    forbidden = metadata["forbidden_dynamic_capabilities"]
    for cap in ["dynamic_clustering", "ml_peer_discovery", "adaptive_weighting"]:
        assert cap in forbidden


def test_checksum_tamper_blocks_and_report_smoke():
    cohorts, bm = _valid_inputs()
    manifest = build_cohort_manifest(cohorts, bm)
    tampered = deepcopy(manifest)
    tampered["cohorts"][0]["members"].append("ZZZZ")
    cert_bad = certify_cohort_registry(tampered)
    assert cert_bad["decision_status"] == BLOCKED_COHORT_REGISTRY

    cert = certify_cohort_registry(manifest)
    report = build_path2a_cohort_registry_report(manifest, cert)
    assert report["path_id"] == "P2-A"
    assert report["final_supervisor_interpretation"] == CERTIFIED_COHORT_REGISTRY
