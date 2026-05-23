from copy import deepcopy
from pathlib import Path

from transmission_layers.expectation_failure import (
    build_concentration_breadth_input_contract,
    build_cohort_fragility_distribution,
    calculate_top_fragility_share,
    interpret_fragility_concentration,
    calculate_elevated_fragility_breadth,
    interpret_cohort_participation_deterioration,
    classify_concentration_breadth_regime,
    build_structural_breadth_explanation,
    certify_concentration_breadth_intelligence,
    build_path2g_structural_concentration_breadth_report,
)
from transmission_layers.expectation_failure.path2a_cohort_registry_foundation import build_cohort_registry_contracts
from transmission_layers.expectation_failure.path2b_relative_fragility_scoring import build_relative_fragility_input_contract
from transmission_layers.expectation_failure.path2c_percentile_ranking_engine import build_percentile_ranking_input_contract
from transmission_layers.expectation_failure.path2f_cross_sectional_explainability import build_cross_sectional_explainability_input_contract
from transmission_layers.expectation_failure.real_data.t1_temporal_snapshot_sequencing import build_temporal_snapshot_sequence


def _payload(size=10):
    members = [{"entity_id": f"E{i}"} for i in range(1, size + 1)]
    scores = {f"E{i}": float(min(100, i * 10)) for i in range(1, size + 1)}
    pct = {f"E{i}": float(min(100, i * 10)) for i in range(1, size + 1)}
    return {
        "cohort_id": "C1",
        "cohort_version": "V1",
        "cohort_members": members,
        "relative_fragility_scores": scores,
        "percentiles": pct,
        "quality_flags": [],
        "replay_metadata": {"path1_snapshot_id": "S1", "input_immutability_preserved": True},
    }


def test_public_api_export_presence_and_distribution_generation():
    assert callable(build_concentration_breadth_input_contract)
    d = build_cohort_fragility_distribution(_payload())
    assert d["usable_member_count"] == 10


def test_deterministic_output_checksum_and_immutability():
    payload = _payload()
    baseline = deepcopy(payload)
    r1 = certify_concentration_breadth_intelligence(payload)
    r2 = certify_concentration_breadth_intelligence(payload)
    assert r1 == r2
    assert r1["checksum"] == r2["checksum"]
    assert payload == baseline


def test_top_n_policy_and_top_fragility_share_calculation():
    d3 = build_cohort_fragility_distribution(_payload(3))
    f3 = []
    assert calculate_top_fragility_share(d3["distribution"], d3["cohort_size"], f3)["top_n"] == 1 and "SMALL_COHORT" in f3
    d7 = build_cohort_fragility_distribution(_payload(7))
    assert calculate_top_fragility_share(d7["distribution"], d7["cohort_size"], [])["top_n"] == 2
    d10 = build_cohort_fragility_distribution(_payload(10))
    assert calculate_top_fragility_share(d10["distribution"], d10["cohort_size"], [])["top_n"] == 3


def test_breadth_participation_dispersion_and_interpretations():
    d = build_cohort_fragility_distribution(_payload(10))
    b = calculate_elevated_fragility_breadth(d["distribution"])
    assert b["elevated_fragility_breadth"] == 0.4
    assert b["weakness_participation_rate"] == 0.6
    assert b["fragility_dispersion"] == 90.0
    assert "concentrated" in interpret_fragility_concentration(0.6).lower()
    assert interpret_cohort_participation_deterioration(0.5, 0.6) == "BREADTH_DETERIORATION_HIGH"


def test_regime_classifications():
    assert classify_concentration_breadth_regime(0.6, 0.2, 0.2, 5) == "CONCENTRATED_FRAGILITY"
    assert classify_concentration_breadth_regime(0.3, 0.6, 0.7, 5) == "BROAD_BASED_WEAKNESS"
    assert classify_concentration_breadth_regime(0.56, 0.4, 0.4, 5) == "MIXED_CONCENTRATION_BREADTH"
    assert classify_concentration_breadth_regime(0.2, 0.1, 0.2, 5) == "LOW_STRUCTURAL_WEAKNESS"
    assert classify_concentration_breadth_regime(0.6, 0.6, 0.6, 1) == "INSUFFICIENT_BREADTH_EVIDENCE"


def test_degraded_blocked_and_clamped_and_explanation_and_forbidden_inventory_and_report_smoke():
    degraded = certify_concentration_breadth_intelligence(_payload(3))
    assert degraded["certification_decision"] == "DEGRADED_CONCENTRATION_BREADTH"

    partial = _payload(5)
    del partial["relative_fragility_scores"]["E5"]
    assert certify_concentration_breadth_intelligence(partial)["certification_decision"] == "DEGRADED_CONCENTRATION_BREADTH"

    blocked_id = _payload(5)
    blocked_id["cohort_id"] = ""
    assert certify_concentration_breadth_intelligence(blocked_id)["certification_decision"] == "BLOCKED_CONCENTRATION_BREADTH"

    blocked_ver = _payload(5)
    blocked_ver["cohort_version"] = ""
    assert certify_concentration_breadth_intelligence(blocked_ver)["certification_decision"] == "BLOCKED_CONCENTRATION_BREADTH"

    blocked_members = _payload(5)
    blocked_members["cohort_members"] = []
    assert certify_concentration_breadth_intelligence(blocked_members)["certification_decision"] == "BLOCKED_CONCENTRATION_BREADTH"

    clamped = _payload(5)
    clamped["relative_fragility_scores"]["E1"] = 120
    out = certify_concentration_breadth_intelligence(clamped)
    assert any(flag.startswith("CLAMPED_SCORE") for flag in out["quality_flags"])
    assert build_structural_breadth_explanation(out)

    contract = build_concentration_breadth_input_contract()
    assert "trading_signals" in contract["forbidden_capabilities"]
    assert "dynamic_benchmark_creation" in contract["forbidden_capabilities"]

    report_path = build_path2g_structural_concentration_breadth_report()
    assert Path(report_path).exists()


def test_path2_and_path1_smoke_imports_and_certified_outcome():
    assert isinstance(build_cohort_registry_contracts(), dict)
    assert isinstance(build_relative_fragility_input_contract(), dict)
    assert isinstance(build_percentile_ranking_input_contract(), dict)
    assert isinstance(build_cross_sectional_explainability_input_contract(), dict)
    assert isinstance(build_temporal_snapshot_sequence([]), dict)
    assert certify_concentration_breadth_intelligence(_payload(10))["certification_decision"] == "CERTIFIED_CONCENTRATION_BREADTH"
