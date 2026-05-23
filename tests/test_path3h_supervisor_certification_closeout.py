from copy import deepcopy

from transmission_layers import expectation_failure as ef
from transmission_layers.expectation_failure import (
    APPROVED_PATH3_CLOSEOUT,
    BLOCKED_PATH3_CLOSEOUT,
    DEGRADED_PATH3_CLOSEOUT,
    build_path3h_closeout_manifest,
    build_path3h_layer_inventory,
    build_path3h_report,
    build_path3h_required_api_inventory,
    certify_path3h_checksum_lineage,
    certify_path3h_dashboard_readiness,
    certify_path3h_governance_boundaries,
    certify_path3h_path3_closeout,
    certify_path3h_replay_integrity,
    certify_path3h_supervisor_readiness,
    validate_path3h_api_presence,
    validate_path3h_export_presence,
)


def _sample_payload():
    return {
        "path3a": {"certification": {"status": "CERTIFIED"}},
        "path3b": {"certification": {"status": "CERTIFIED"}},
        "path3c": {"certification": {"status": "CERTIFIED"}},
        "path3d": {"certification": {"status": "CERTIFIED"}},
        "path3e": {"certification": {"status": "CERTIFIED"}},
        "path3f": {"asymmetry_regime": "CONCENTRATED_FRAGILITY_REGIME"},
        "path3g": {"summary_sentence": "Structural conditions remain bounded.", "certification_status": "CERTIFIED_STRUCTURAL_INTERPRETATION"},
    }


def test_public_api_presence_and_exports():
    for name in (
        "build_path3h_layer_inventory", "build_path3h_required_api_inventory", "validate_path3h_api_presence",
        "validate_path3h_export_presence", "certify_path3h_replay_integrity", "certify_path3h_checksum_lineage",
        "certify_path3h_governance_boundaries", "certify_path3h_dashboard_readiness", "certify_path3h_supervisor_readiness",
        "build_path3h_closeout_manifest", "certify_path3h_path3_closeout", "build_path3h_report",
    ):
        assert hasattr(ef, name)


def test_inventory_ordering_and_api_completeness():
    inv = build_path3h_layer_inventory()
    assert [x["layer_id"] for x in inv] == ["P3-A", "P3-B", "P3-C", "P3-D", "P3-E", "P3-F", "P3-G"]
    req = build_path3h_required_api_inventory()
    assert list(req.keys()) == ["path3a", "path3b", "path3c", "path3d", "path3e", "path3f", "path3g"]


def test_api_and_export_validation():
    assert validate_path3h_api_presence()["passed"] is True
    assert validate_path3h_export_presence()["passed"] is True


def test_determinism_checksum_immutability_and_serialization_stability():
    payload = _sample_payload()
    before = deepcopy(payload)
    m1 = build_path3h_closeout_manifest(payload)
    m2 = build_path3h_closeout_manifest(payload)
    assert payload == before
    assert m1 == m2
    assert m1["checksums"]["manifest_checksum"] == m2["checksums"]["manifest_checksum"]


def test_gate_inventory_order_and_count_and_manifest_structure():
    manifest = build_path3h_closeout_manifest(_sample_payload())
    assert len(manifest["gate_inventory"]) == 30
    assert manifest["gate_inventory"][0] == "P3 layer inventory present"
    assert set(["layer_inventory", "required_api_inventory", "governance", "replay", "checksums"]).issubset(manifest.keys())


def test_approved_degraded_blocked_paths():
    approved = certify_path3h_path3_closeout(_sample_payload())
    assert approved["certification_status"] == APPROVED_PATH3_CLOSEOUT

    degraded_payload = _sample_payload()
    degraded_payload["path3g"] = {"summary_sentence": "Structural conditions remain bounded."}
    degraded = certify_path3h_path3_closeout(degraded_payload)
    assert degraded["certification_status"] == DEGRADED_PATH3_CLOSEOUT

    blocked_payload = _sample_payload()
    blocked_payload["path3g"]["summary_sentence"] = "Buy now due to expected return expansion."
    blocked = certify_path3h_path3_closeout(blocked_payload)
    assert blocked["certification_status"] == BLOCKED_PATH3_CLOSEOUT


def test_replay_lineage_governance_dashboard_supervisor_and_report():
    payload = _sample_payload()
    assert certify_path3h_replay_integrity(payload)["passed"] is True
    assert certify_path3h_checksum_lineage(payload)["passed"] is True
    assert certify_path3h_governance_boundaries(payload)["passed"] is True
    assert certify_path3h_dashboard_readiness(payload)["passed"] is True
    assert certify_path3h_supervisor_readiness(payload)["passed"] is True
    report = build_path3h_report()
    assert "Objective" in report and "Final Closeout Decision Logic" in report


def test_bounded_semantics_and_no_runtime_dependency_behavior_and_non_regression_smoke():
    payload = _sample_payload()
    gov = certify_path3h_governance_boundaries(payload)
    assert gov["forbidden_terms_detected"] == []
    caps = gov["forbidden_capabilities"]
    assert caps["network_access"] is False and caps["file_writes"] is False and caps["llm_calls"] is False

    from transmission_layers.expectation_failure.path3a_structural_resilience_foundation import run_p3a_structural_resilience_foundation
    from transmission_layers.expectation_failure.path3b_structural_asymmetry_engine import run_p3b_structural_asymmetry_engine
    assert isinstance(run_p3a_structural_resilience_foundation({}), dict)
    assert isinstance(run_p3b_structural_asymmetry_engine({}), dict)
