from copy import deepcopy

from transmission_layers.expectation_failure import (
    APPROVED_PATH2_CLOSEOUT,
    BLOCKED_PATH2_CLOSEOUT,
    DEGRADED_PATH2_CLOSEOUT,
    build_path2_closeout_input_contract,
    build_path2_layer_inventory,
    build_path2i_supervisor_final_closeout_report,
    certify_path2_additive_integration,
    certify_path2_architectural_boundaries,
    certify_path2_checksum_lineage,
    certify_path2_deterministic_replay,
    certify_path2_explainability_interpretation,
    run_path2_supervisor_closeout,
    validate_path2_final_forbidden_capabilities,
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
        "p2h_relative_fragility_certification": _layer_payload("p2h"),
    }


def test_public_api_export_presence():
    contract = build_path2_closeout_input_contract()
    assert contract["path_id"] == "P2-I"
    assert callable(build_path2_layer_inventory)
    assert callable(run_path2_supervisor_closeout)


def test_deterministic_repeated_output_checksum_stability_and_immutability():
    payload = _valid_contract()
    before = deepcopy(payload)
    first = run_path2_supervisor_closeout(payload)
    second = run_path2_supervisor_closeout(payload)
    assert first == second
    assert first["checksum"] == second["checksum"]
    assert payload == before


def test_approved_degraded_blocked_outcomes():
    approved = run_path2_supervisor_closeout(_valid_contract())
    assert approved["path2_closeout_status"] == APPROVED_PATH2_CLOSEOUT

    degraded_payload = _valid_contract()
    degraded_payload["p2g_concentration_breadth"]["weakness_participation_rate"] = 1.1
    degraded = run_path2_supervisor_closeout(degraded_payload)
    assert degraded["path2_closeout_status"] == DEGRADED_PATH2_CLOSEOUT

    blocked_payload = _valid_contract()
    blocked_payload["note"] = "includes trading systems"
    blocked = run_path2_supervisor_closeout(blocked_payload)
    assert blocked["path2_closeout_status"] == BLOCKED_PATH2_CLOSEOUT


def test_missing_p2a_to_p2h_behavior_blocked():
    for key in list(_valid_contract().keys()):
        payload = _valid_contract()
        payload.pop(key)
        out = run_path2_supervisor_closeout(payload)
        assert out["path2_closeout_status"] == BLOCKED_PATH2_CLOSEOUT


def test_replay_checksum_explainability_breadth_and_architecture_and_additive():
    payload = _valid_contract()
    assert certify_path2_deterministic_replay(payload)["status"] == "PASS"
    assert certify_path2_checksum_lineage(payload)["status"] == "PASS"
    assert certify_path2_explainability_interpretation(payload)["status"] == "PASS"
    assert certify_path2_architectural_boundaries(payload)["status"] == "PASS"
    assert certify_path2_additive_integration(payload)["status"] == "PASS"


def test_forbidden_capability_detection_and_additive_failure():
    payload = _valid_contract()
    payload["note"] = "autonomous execution"
    forbidden = validate_path2_final_forbidden_capabilities(payload)
    assert forbidden["status"] == "FAIL"

    payload2 = _valid_contract()
    payload2["non_additive_integration"] = True
    additive = certify_path2_additive_integration(payload2)
    assert additive["status"] == "FAIL"


def test_report_builder_smoke(tmp_path):
    out = build_path2i_supervisor_final_closeout_report(str(tmp_path / "path2i.md"))
    assert out.endswith("path2i.md")


def test_smoke_imports_path2a_to_p2h_and_path1():
    from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import certify_cohort_registry
    from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import certify_relative_fragility_scoring
    from transmission_layers.expectation_failure.path2c_percentile_ranking_engine import certify_percentile_ranking_engine
    from transmission_layers.expectation_failure.path2d_benchmark_divergence_intelligence import certify_benchmark_divergence_intelligence
    from transmission_layers.expectation_failure.path2e_relative_evolution_interpretation import certify_relative_evolution_interpretation
    from transmission_layers.expectation_failure.path2f_cross_sectional_explainability import certify_cross_sectional_explainability
    from transmission_layers.expectation_failure.path2g_structural_concentration_breadth import certify_concentration_breadth_intelligence
    from transmission_layers.expectation_failure.path2h_relative_fragility_certification import certify_relative_fragility_stack
    from transmission_layers.expectation_failure.phase_a2_valuation_stretch import score_valuation_stretch

    assert callable(certify_cohort_registry)
    assert callable(certify_relative_fragility_scoring)
    assert callable(certify_percentile_ranking_engine)
    assert callable(certify_benchmark_divergence_intelligence)
    assert callable(certify_relative_evolution_interpretation)
    assert callable(certify_cross_sectional_explainability)
    assert callable(certify_concentration_breadth_intelligence)
    assert callable(certify_relative_fragility_stack)
    assert callable(score_valuation_stretch)
