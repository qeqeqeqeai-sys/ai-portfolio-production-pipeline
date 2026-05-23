from copy import deepcopy

from transmission_layers.expectation_failure import (
    BLOCKED_RELATIVE_FRAGILITY_STACK,
    CERTIFIED_RELATIVE_FRAGILITY_STACK,
    DEGRADED_RELATIVE_FRAGILITY_STACK,
    build_path2h_relative_fragility_certification_report,
    build_relative_fragility_certification_input_contract,
    build_relative_intelligence_inventory,
    certify_path2_architectural_boundaries,
    certify_path2_concentration_breadth_integrity,
    certify_path2_determinism,
    certify_path2_explainability_integrity,
    certify_path2_replay_checksum_integrity,
    certify_relative_fragility_stack,
    validate_path2_forbidden_capabilities,
)


def _layer_payload(name: str):
    return {"layer": name, "checksum": f"cs-{name}", "replay_metadata": {"snapshot": "2026-01-01"}}


def _valid_contract():
    return {
        "p2a_cohort_registry": _layer_payload("p2a"),
        "p2b_relative_scoring": _layer_payload("p2b"),
        "p2c_ranking_percentile": _layer_payload("p2c"),
        "p2d_benchmark_divergence": _layer_payload("p2d"),
        "p2e_relative_evolution": _layer_payload("p2e"),
        "p2f_explainability": {**_layer_payload("p2f"), "cross_sectional_explainability": "ok"},
        "p2g_concentration_breadth": {
            **_layer_payload("p2g"),
            "top_fragility_share": 0.5,
            "elevated_fragility_breadth": 0.4,
            "weakness_participation_rate": 0.6,
        },
    }


def test_public_api_export_presence():
    contract = build_relative_fragility_certification_input_contract()
    assert contract["path_id"] == "P2-H"
    assert callable(build_relative_intelligence_inventory)
    assert callable(certify_relative_fragility_stack)


def test_deterministic_repeated_output_and_checksum_stability():
    payload = _valid_contract()
    first = certify_relative_fragility_stack(payload)
    second = certify_relative_fragility_stack(payload)
    assert first == second
    assert first["checksum"] == second["checksum"]


def test_immutable_input_behavior():
    payload = _valid_contract()
    before = deepcopy(payload)
    certify_relative_fragility_stack(payload)
    assert payload == before


def test_full_certified_stack_outcome():
    out = certify_relative_fragility_stack(_valid_contract())
    assert out["relative_fragility_stack_status"] == CERTIFIED_RELATIVE_FRAGILITY_STACK


def test_degraded_stack_outcome():
    payload = _valid_contract()
    payload["p2g_concentration_breadth"]["weakness_participation_rate"] = 1.1
    out = certify_relative_fragility_stack(payload)
    assert out["relative_fragility_stack_status"] == DEGRADED_RELATIVE_FRAGILITY_STACK


def test_blocked_stack_outcome_and_missing_layers():
    layer_keys = [
        "p2a_cohort_registry", "p2b_relative_scoring", "p2c_ranking_percentile",
        "p2d_benchmark_divergence", "p2e_relative_evolution", "p2f_explainability", "p2g_concentration_breadth",
    ]
    for key in layer_keys:
        payload = _valid_contract()
        payload.pop(key)
        out = certify_relative_fragility_stack(payload)
        assert out["relative_fragility_stack_status"] == BLOCKED_RELATIVE_FRAGILITY_STACK


def test_forbidden_capability_detection_and_boundary_validation():
    payload = _valid_contract()
    payload["note"] = "contains trading systems"
    forbid = validate_path2_forbidden_capabilities(payload)
    assert forbid["status"] == "FAIL"
    payload2 = _valid_contract()
    payload2["recalculated_lower_layer_intelligence"] = True
    arch = certify_path2_architectural_boundaries(payload2)
    assert arch["status"] == "FAIL"


def test_replay_explainability_concentration_checks():
    payload = _valid_contract()
    assert certify_path2_replay_checksum_integrity(payload)["status"] == "PASS"
    assert certify_path2_explainability_integrity(payload)["status"] == "PASS"
    assert certify_path2_concentration_breadth_integrity(payload)["status"] == "PASS"
    assert certify_path2_determinism(payload)["status"] == "PASS"


def test_report_builder_smoke(tmp_path):
    out = build_path2h_relative_fragility_certification_report(str(tmp_path / "p2h.md"))
    assert out.endswith("p2h.md")


def test_smoke_imports_path2a_to_path2g_and_path1():
    from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import certify_cohort_registry
    from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import certify_relative_fragility_scoring
    from transmission_layers.expectation_failure.path2c_percentile_ranking_engine import certify_percentile_ranking_engine
    from transmission_layers.expectation_failure.path2d_benchmark_divergence_intelligence import certify_benchmark_divergence_intelligence
    from transmission_layers.expectation_failure.path2e_relative_evolution_interpretation import certify_relative_evolution_interpretation
    from transmission_layers.expectation_failure.path2f_cross_sectional_explainability import certify_cross_sectional_explainability
    from transmission_layers.expectation_failure.path2g_structural_concentration_breadth import certify_concentration_breadth_intelligence
    from transmission_layers.expectation_failure.phase_a2_valuation_stretch import score_valuation_stretch

    assert callable(certify_cohort_registry)
    assert callable(certify_relative_fragility_scoring)
    assert callable(certify_percentile_ranking_engine)
    assert callable(certify_benchmark_divergence_intelligence)
    assert callable(certify_relative_evolution_interpretation)
    assert callable(certify_cross_sectional_explainability)
    assert callable(certify_concentration_breadth_intelligence)
    assert callable(score_valuation_stretch)
