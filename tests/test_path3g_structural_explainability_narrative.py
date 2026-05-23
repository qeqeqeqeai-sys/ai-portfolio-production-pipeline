from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_path3g_bounded_grammar_registry,
    build_path3g_dashboard_explanation,
    build_path3g_explanation_registry,
    build_path3g_interpretation_blocks,
    build_path3g_narrative_manifest,
    build_path3g_report,
    build_path3g_structural_narrative,
    build_path3g_supervisor_report,
    certify_path3g_structural_explainability,
    evaluate_path3g_explanation_triggers,
)


def _sample_inputs():
    return {
        "path3a": {"resilience_dimensions": {"resilience_support": 55}},
        "path3b": {"asymmetry_dimensions": {"downside_asymmetry": 70}},
        "path3c": {"benchmark_asymmetry_dimensions": {"benchmark_relative_pressure": 66}},
        "path3d": {"persistence_dimensions": {"asymmetry_persistence": 68}},
        "path3e": {"imbalance_dimensions": {"fragility_concentration": 71}},
        "path3f": {"asymmetry_regime": "CONCENTRATED_FRAGILITY_REGIME"},
    }


def test_public_apis_present_and_exported():
    registry = build_path3g_explanation_registry()
    assert isinstance(registry, dict)
    assert callable(build_path3g_bounded_grammar_registry)
    assert callable(evaluate_path3g_explanation_triggers)
    assert callable(build_path3g_interpretation_blocks)
    assert callable(build_path3g_structural_narrative)
    assert callable(build_path3g_dashboard_explanation)
    assert callable(build_path3g_supervisor_report)
    assert callable(certify_path3g_structural_explainability)
    assert callable(build_path3g_narrative_manifest)
    assert callable(build_path3g_report)


def test_determinism_and_stable_checksums_and_serialization():
    inp = _sample_inputs()
    m1 = build_path3g_narrative_manifest(inp)
    m2 = build_path3g_narrative_manifest(inp)
    assert m1 == m2
    assert m1["manifest_checksum"] == m2["manifest_checksum"]


def test_input_immutability():
    inp = _sample_inputs()
    before = deepcopy(inp)
    _ = build_path3g_supervisor_report(inp)
    assert inp == before


def test_registry_and_grammar_structure_fixed():
    registry = build_path3g_explanation_registry()
    grammar = build_path3g_bounded_grammar_registry()
    assert registry["version"] == "P3G_REGISTRY_V1"
    assert len(registry["explanations"]) >= 5
    assert "registry_checksum" in registry
    assert grammar["rules"]["template_only"] is True
    assert "grammar_checksum" in grammar


def test_trigger_priority_dedup_and_dashboard_structure():
    inp = _sample_inputs()
    trig = evaluate_path3g_explanation_triggers(inp)
    priorities = [row["priority"] for row in trig["active_explanations"]]
    assert priorities == sorted(priorities)
    assert len({row["explanation_id"] for row in trig["active_explanations"]}) == len(trig["active_explanations"])
    dash = build_path3g_dashboard_explanation(inp)
    required = {"summary_sentence","regime_interpretation","primary_driver_labels","active_explanation_ids","source_layer_summary","certification_status","narrative_checksum","registry_checksum"}
    assert required.issubset(dash.keys())


def test_supervisor_report_and_lineage_completeness():
    inp = _sample_inputs()
    report = build_path3g_supervisor_report(inp)
    for key in ["objective","scope","non_goals","active_explanations","inactive_explanations_summary","trigger_matrix","bounded_grammar_inventory","narrative_lineage","checksum_manifest","certification_decision","governance_boundary_review","final_interpretation"]:
        assert key in report
    for row in report["narrative_lineage"]:
        assert "explanation_id" in row and "trigger_rule" in row and "narrative_checksum" in row


def test_certified_degraded_blocked_paths_and_forbidden_absence():
    full = _sample_inputs()
    cert = certify_path3g_structural_explainability(full)
    assert cert["certification_status"] == "CERTIFIED_STRUCTURAL_INTERPRETATION"

    degraded_inp = _sample_inputs()
    degraded_inp.pop("path3e")
    degraded = certify_path3g_structural_explainability(degraded_inp)
    assert degraded["certification_status"] == "DEGRADED_STRUCTURAL_INTERPRETATION"

    narrative = build_path3g_structural_narrative(full)
    narrative["summary_sentence"] = narrative["summary_sentence"] + " Investors should reduce exposure."
    narrative["forbidden_language_flags"] = {"forbidden_reduce_exposure": True}
    blocked = certify_path3g_structural_explainability(full, narrative)
    assert blocked["certification_status"] == "BLOCKED_STRUCTURAL_INTERPRETATION"

    clean = build_path3g_structural_narrative(full)
    assert not any(clean["forbidden_language_flags"].values())
    lower = clean["summary_sentence"].lower()
    for term in ("buy", "sell", "trade", "predict", "likely", "underperform"):
        assert term not in lower


def test_non_regression_smoke_and_no_runtime_dependencies():
    from transmission_layers.expectation_failure.path3a_structural_resilience_foundation import run_p3a_structural_resilience_foundation
    from transmission_layers.expectation_failure.path3b_structural_asymmetry_engine import run_p3b_structural_asymmetry_engine

    p3a = run_p3a_structural_resilience_foundation({})
    p3b = run_p3b_structural_asymmetry_engine({})
    assert isinstance(p3a, dict) and isinstance(p3b, dict)
