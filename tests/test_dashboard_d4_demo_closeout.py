from transmission_layers.expectation_failure import dashboard_operationalization as dops
from transmission_layers.expectation_failure.dashboard_operationalization import dashboard_d4_demo_closeout as d4


def _gate_status_map(result):
    return {item["gate"]: item["status"] for item in result["gate_results"]}


def test_d4_public_api_export_presence_and_additive_behavior():
    expected = {
        "build_d4_closeout_inventory","build_d4_certification_gates","build_d4_demo_readiness_manifest",
        "certify_d4_operationalization_chain","certify_d4_sample_data_chain","certify_d4_visibility_chain",
        "certify_d4_playback_chain","certify_d4_safety_boundaries","run_d4_demo_environment_closeout",
        "build_d4_closeout_report_payload",
    }
    for name in expected:
        assert hasattr(d4, name)
        assert hasattr(dops, name)


def test_d4_deterministic_repeated_output_and_checksum_stability_and_gate_order():
    payload = {"dashboard_entity_facts": []}
    r1 = d4.run_d4_demo_environment_closeout(payload)
    r2 = d4.run_d4_demo_environment_closeout(payload)
    assert r1 == r2
    assert r1["manifest_checksum"] == r2["manifest_checksum"]
    assert r1["gate_sequence"] == d4.build_d4_certification_gates()


def test_d4_all_pass_closeout_and_linkages_and_boundaries(monkeypatch):
    monkeypatch.setattr(d4, "certify_d4_operationalization_chain", lambda payload: "PASS")
    monkeypatch.setattr(d4, "certify_d4_sample_data_chain", lambda payload, guardrails: {"D1_SAMPLE_DATA_SEEDING_CERTIFIED": "PASS", "D1G_GUARDRAILS_FROZEN": "PASS"})
    monkeypatch.setattr(d4, "certify_d4_visibility_chain", lambda payload: "PASS")
    monkeypatch.setattr(d4, "certify_d4_playback_chain", lambda payload, acceptance: {"D3_PLAYBACK_CERTIFIED": "PASS", "SUPERVISOR_ACCEPTANCE_PAYLOAD_AVAILABLE": "PASS"})
    result = d4.run_d4_demo_environment_closeout({"dashboard_entity_facts": []})
    assert result["decision"] == d4.D4_APPROVED_DECISION
    assert result["overall_status"] == "PASS"
    gates = _gate_status_map(result)
    assert all(gates[g] == "PASS" for g in d4.D4_GATE_SEQUENCE)
    assert result["chain_linkage"]["d1g_guardrails"] == "certified"
    assert result["safety_boundary_certification"]["read_only_dashboard_boundary"] == "PASS"
    assert result["safety_boundary_certification"]["o3_only_persistence_boundary"] == "PASS"
    assert result["safety_boundary_certification"]["sample_data_labeling_preserved"] == "PASS"
    assert "predictive_modelling" in result["forbidden_behavior_exclusions"]


def test_d4_degraded_closeout_path(monkeypatch):
    monkeypatch.setattr(d4, "certify_d4_operationalization_chain", lambda payload: "PASS")
    monkeypatch.setattr(d4, "certify_d4_sample_data_chain", lambda payload, guardrails: {"D1_SAMPLE_DATA_SEEDING_CERTIFIED": "PASS", "D1G_GUARDRAILS_FROZEN": "PASS"})
    monkeypatch.setattr(d4, "certify_d4_visibility_chain", lambda payload: "DEGRADED")
    monkeypatch.setattr(d4, "certify_d4_playback_chain", lambda payload, acceptance: {"D3_PLAYBACK_CERTIFIED": "PASS", "SUPERVISOR_ACCEPTANCE_PAYLOAD_AVAILABLE": "PASS"})
    result = d4.run_d4_demo_environment_closeout({})
    assert result["overall_status"] == "DEGRADED"
    assert result["decision"] == "REVIEW_REQUIRED"


def test_d4_blocked_closeout_path(monkeypatch):
    monkeypatch.setattr(d4, "certify_d4_operationalization_chain", lambda payload: "BLOCKED")
    monkeypatch.setattr(d4, "certify_d4_sample_data_chain", lambda payload, guardrails: {"D1_SAMPLE_DATA_SEEDING_CERTIFIED": "PASS", "D1G_GUARDRAILS_FROZEN": "PASS"})
    monkeypatch.setattr(d4, "certify_d4_visibility_chain", lambda payload: "PASS")
    monkeypatch.setattr(d4, "certify_d4_playback_chain", lambda payload, acceptance: {"D3_PLAYBACK_CERTIFIED": "PASS", "SUPERVISOR_ACCEPTANCE_PAYLOAD_AVAILABLE": "PASS"})
    result = d4.run_d4_demo_environment_closeout({})
    assert result["overall_status"] == "BLOCKED"
    assert result["decision"] == "REVIEW_REQUIRED"


def test_d4_immutable_input_safety_and_no_mutation_of_input():
    payload = {"dashboard_entity_facts": [{"entity_id": "x"}]}
    snapshot = {"dashboard_entity_facts": [{"entity_id": "x"}]}
    result = d4.run_d4_demo_environment_closeout(payload)
    assert payload == snapshot
    assert result["immutable_input_preserved"] is True


def test_d4_report_payload_and_manifest_chain_stability(monkeypatch):
    monkeypatch.setattr(d4, "certify_d4_operationalization_chain", lambda payload: "PASS")
    monkeypatch.setattr(d4, "certify_d4_sample_data_chain", lambda payload, guardrails: {"D1_SAMPLE_DATA_SEEDING_CERTIFIED": "PASS", "D1G_GUARDRAILS_FROZEN": "PASS"})
    monkeypatch.setattr(d4, "certify_d4_visibility_chain", lambda payload: "PASS")
    monkeypatch.setattr(d4, "certify_d4_playback_chain", lambda payload, acceptance: {"D3_PLAYBACK_CERTIFIED": "PASS", "SUPERVISOR_ACCEPTANCE_PAYLOAD_AVAILABLE": "PASS"})
    report = d4.build_d4_closeout_report_payload({})
    result = d4.run_d4_demo_environment_closeout({})
    assert report["final_supervisor_decision"] == d4.D4_APPROVED_DECISION
    assert result["readiness_manifest"]["manifest_checksum"]
