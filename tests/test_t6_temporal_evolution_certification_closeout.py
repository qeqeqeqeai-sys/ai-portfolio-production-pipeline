from copy import deepcopy

from transmission_layers.expectation_failure.real_data import (
    build_t6_temporal_evolution_closeout_report,
    build_temporal_evolution_closeout_manifest,
    build_temporal_evolution_gate_inventory,
    build_temporal_evolution_lineage_summary,
    certify_temporal_evolution_closeout,
    validate_temporal_evolution_closeout_inputs,
)


def _layer(status_key, status):
    return {
        status_key: status,
        "checksum_chain": {"chain": "x"},
        "temporal_lineage": {"prior": "x"},
        "result_checksum": f"{status_key}_checksum",
        "certification_gates": [{"gate": "a", "passed": True}],
        "invariant_flags": {"core": True},
        "forbidden_capabilities": {"prediction": False, "trading_execution": False},
        "summary": {"record_count": 1},
    }


def _inputs():
    return {
        "t1": _layer("t1_status", "TEMPORAL_SNAPSHOT_SEQUENCE_CERTIFIED"),
        "t2": _layer("t2_status", "STRUCTURAL_DELTA_INTELLIGENCE_CERTIFIED"),
        "t3": _layer("t3_status", "FRAGILITY_EVOLUTION_CURVES_CERTIFIED"),
        "t4": _layer("t4_status", "REGIME_TRANSITIONS_CERTIFIED"),
        "t5": _layer("t5_status", "HISTORICAL_EXPLAINABILITY_CERTIFIED"),
    }


def test_api_and_certified_flow():
    payload = _inputs()
    assert validate_temporal_evolution_closeout_inputs(payload)["valid"] is True
    result = certify_temporal_evolution_closeout(payload)
    assert result["t6_status"] == "TEMPORAL_EVOLUTION_CLOSEOUT_CERTIFIED"
    assert result["final_decision"] == "APPROVED_FOR_CONTROLLED_DOWNSTREAM_USE"


def test_blocked_missing_layer_and_blocked_upstream_and_forbidden_and_invariant_failure():
    missing = _inputs()
    missing.pop("t3")
    assert certify_temporal_evolution_closeout(missing)["t6_status"] == "TEMPORAL_EVOLUTION_CLOSEOUT_BLOCKED"
    blocked = _inputs()
    blocked["t4"]["t4_status"] = "REGIME_TRANSITIONS_BLOCKED"
    assert certify_temporal_evolution_closeout(blocked)["t6_status"] == "TEMPORAL_EVOLUTION_CLOSEOUT_BLOCKED"
    forbidden = _inputs()
    forbidden["t2"]["forbidden_capabilities"]["prediction"] = True
    assert certify_temporal_evolution_closeout(forbidden)["t6_status"] == "TEMPORAL_EVOLUTION_CLOSEOUT_BLOCKED"
    inv = _inputs()
    inv["t1"]["invariant_flags"]["core"] = False
    assert certify_temporal_evolution_closeout(inv)["t6_status"] == "TEMPORAL_EVOLUTION_CLOSEOUT_BLOCKED"


def test_degraded_and_checksum_lineage_and_ordering_and_determinism_and_immutability():
    degraded = _inputs()
    degraded["t5"]["t5_status"] = "HISTORICAL_EXPLAINABILITY_DEGRADED"
    degraded["t2"]["checksum_chain"] = {}
    before = deepcopy(degraded)
    result = certify_temporal_evolution_closeout(degraded)
    assert result["t6_status"] == "TEMPORAL_EVOLUTION_CLOSEOUT_DEGRADED"
    assert result["reviewed_layers"] == [
        "T1_TEMPORAL_SNAPSHOT_SEQUENCING",
        "T2_STRUCTURAL_DELTA_INTELLIGENCE",
        "T3_FRAGILITY_EVOLUTION_CURVES",
        "T4_REGIME_TRANSITION_DETECTION",
        "T5_HISTORICAL_EXPLAINABILITY",
    ]
    gates = build_temporal_evolution_gate_inventory(degraded)
    assert [g["gate_name"] for g in gates][:3] == ["t1_envelope_present", "t2_envelope_present", "t3_envelope_present"]
    assert len(gates) == 33
    manifest = build_temporal_evolution_closeout_manifest(degraded)
    assert manifest["gate_count"] == 33
    assert manifest["pass_count"] + manifest["warn_count"] + manifest["fail_count"] == 33
    a = certify_temporal_evolution_closeout(degraded)
    b = certify_temporal_evolution_closeout(degraded)
    assert a["result_checksum"] == b["result_checksum"]
    assert degraded == before


def test_summary_classifications_and_report_smoke():
    payload = _inputs()
    payload["t3"]["checksum_chain"] = {}
    lineage = build_temporal_evolution_lineage_summary(payload)
    assert lineage["lineage_status"] in {"LINEAGE_CONTINUITY_DEGRADED", "LINEAGE_CONTINUITY_BLOCKED"}
    result = certify_temporal_evolution_closeout(payload)
    assert result["checksum_continuity_summary"]["checksum_continuity_status"] in {"CHECKSUM_CONTINUITY_DEGRADED", "CHECKSUM_CONTINUITY_BLOCKED"}
    assert result["invariant_summary"]["invariant_status"] in {"INVARIANTS_CERTIFIED", "INVARIANTS_DEGRADED", "INVARIANTS_BLOCKED"}
    assert result["forbidden_capability_summary"]["forbidden_capability_status"] in {
        "FORBIDDEN_CAPABILITIES_BLOCKED", "FORBIDDEN_CAPABILITIES_DEGRADED", "FORBIDDEN_CAPABILITIES_FAILED"
    }
    report = build_t6_temporal_evolution_closeout_report(result)
    assert "T6 Temporal Evolution Certification Closeout Report" in report
