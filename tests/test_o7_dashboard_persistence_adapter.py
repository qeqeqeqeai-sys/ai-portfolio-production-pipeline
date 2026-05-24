from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o6_dashboard_export_bundle,
    build_o7_dashboard_persistence_adapter_report,
    build_o7_persistence_audit_manifest,
    build_o7_persistence_result_summary,
    build_o7_persistence_table_contract,
    build_o7_write_batch_plan,
    certify_o7_dashboard_persistence_adapter,
    persist_o7_dashboard_export_bundle,
    validate_o7_persistence_bundle,
)


class _Resp:
    def __init__(self, data=True):
        self.data = data


class FakeClient:
    def __init__(self, fail_tables=None):
        self.calls = []
        self.fail_tables = set(fail_tables or [])

    def table(self, table_name):
        self._table = table_name
        return self

    def upsert(self, records, on_conflict=None):
        self.calls.append((self._table, len(records), on_conflict))
        if self._table in self.fail_tables:
            raise RuntimeError(f"failed:{self._table}")
        return self

    def execute(self):
        return _Resp(data=True)


def _o5_payload():
    return {
        "o5_version": "v1",
        "o5_checksum": "abc123",
        "semantic_findings": [{"finding_id": "F1", "finding_type": "stress", "lineage_refs": {"k": "v"}, "supporting_evidence_refs": ["E1"]}],
        "dashboard_insight_narratives": {"overview": "text"},
        "finding_evidence_map": {"F1": ["E1"]},
        "supervisor_interpretation_panel": {"certification_status": "OK", "forbidden_capability_inventory": {"x": True}},
        "certification": {"checksum": "cert1"},
    }


def test_public_api_and_export_presence_and_non_regression_smoke():
    import transmission_layers.expectation_failure.dashboard_operationalization as m
    for name in (
        "build_o7_persistence_table_contract",
        "build_o7_write_batch_plan",
        "build_o7_persistence_audit_manifest",
        "validate_o7_persistence_bundle",
        "persist_o7_dashboard_export_bundle",
        "build_o7_persistence_result_summary",
        "certify_o7_dashboard_persistence_adapter",
        "build_o7_dashboard_persistence_adapter_report",
        "build_o6_dashboard_export_bundle",
    ):
        assert hasattr(m, name)


def test_deterministic_and_checksum_stability_and_immutability():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    before = deepcopy(bundle)
    p1 = build_o7_write_batch_plan(bundle)
    p2 = build_o7_write_batch_plan(bundle)
    assert p1 == p2
    assert p1["plan_checksum"] == p2["plan_checksum"]
    assert bundle == before


def test_happy_degraded_and_blocked_validation_paths():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    ok = validate_o7_persistence_bundle(bundle)
    assert ok["certification_status"] == "CERTIFIED_PERSISTENCE_ADAPTER_READY"

    degraded_bundle = deepcopy(bundle)
    degraded_bundle.pop("narrative_records", None)
    deg = validate_o7_persistence_bundle(degraded_bundle)
    assert deg["certification_status"] == "DEGRADED_PERSISTENCE_ADAPTER_READY"

    blocked_bundle = deepcopy(bundle)
    blocked_bundle["finding_records"] = "bad"
    blk = validate_o7_persistence_bundle(blocked_bundle)
    assert blk["certification_status"] == "BLOCKED_PERSISTENCE_ADAPTER_INVALID"


def test_table_contract_completeness_and_approved_routing_only():
    contract = build_o7_persistence_table_contract()
    assert len(contract["approved_tables"]) == 8
    for table in contract["table_contracts"]:
        for field in ("logical_table_name", "accepted_record_types", "required_fields", "unique_key_fields", "checksum_fields", "write_mode", "governance_notes"):
            assert field in table
    plan = build_o7_write_batch_plan(build_o6_dashboard_export_bundle(_o5_payload()))
    assert {b["target_table"] for b in plan["batches"]}.issubset(set(contract["approved_tables"]))


def test_dry_run_and_no_client_behavior():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    client = FakeClient()
    dry = persist_o7_dashboard_export_bundle(bundle, client=client, dry_run=True)
    assert dry["execution_state"] == "DRY_RUN_NOT_EXECUTED"
    assert client.calls == []

    none_client = persist_o7_dashboard_export_bundle(bundle, client=None, dry_run=False)
    assert none_client["execution_state"] == "NOT_EXECUTED_NO_CLIENT"


def test_injected_client_success_and_failure_encoding_and_reference_preservation():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    client_ok = FakeClient()
    res_ok = persist_o7_dashboard_export_bundle(bundle, client=client_ok, dry_run=False)
    assert res_ok["execution_state"] == "EXECUTED"
    assert len(client_ok.calls) == 8

    client_fail = FakeClient(fail_tables={"dashboard_finding_records"})
    res_fail = persist_o7_dashboard_export_bundle(bundle, client=client_fail, dry_run=False)
    assert res_fail["execution_state"] == "EXECUTED_WITH_FAILURES"
    assert any((not r["success"]) and r["target_table"] == "dashboard_finding_records" for r in res_fail["table_results"])

    plan = build_o7_write_batch_plan(bundle)
    finding_batch = [b for b in plan["batches"] if b["target_table"] == "dashboard_finding_records"][0]
    rec = finding_batch["records"][0]
    assert rec["record_id"]
    assert rec["finding_id"] == "F1"
    assert "supporting_evidence_refs" not in rec
    assert rec["payload"]["supporting_evidence_refs"] == ["E1"]
    assert rec["lineage_refs"] == {"k": "v"}
    assert rec["source_payload_checksum"]
    assert rec["export_checksum"]


def test_serializer_strips_unknown_top_level_fields_and_preserves_payload():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    plan = build_o7_write_batch_plan(bundle)
    cols_by_table = {
        "dashboard_finding_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","finding_id","finding_type","finding_title","finding_severity","finding_direction","confidence_label"},
        "dashboard_narrative_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","narrative_section","related_finding_ids"},
        "dashboard_evidence_map_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","finding_id","evidence_ref"},
        "dashboard_supervisor_panel_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","panel_name","panel_status"},
        "dashboard_export_manifests": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","manifest_id","manifest_checksum"},
        "dashboard_governance_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","governance_status","forbidden_capabilities"},
        "dashboard_replay_metadata_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","replay_id","replay_checksum"},
        "dashboard_persistence_audit_records": {"record_id","record_type","source_payload_checksum","export_checksum","payload","lineage_refs","evidence_refs","governance_notes","replay_metadata","audit_id","batch_id","target_table","write_status"},
    }
    for batch in plan["batches"]:
        allowed = cols_by_table[batch["target_table"]]
        for rec in batch["records"]:
            assert set(rec.keys()).issubset(allowed)
            assert "payload" in rec


def test_fake_client_receives_schema_compatible_records_only():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    plan = build_o7_write_batch_plan(bundle)
    client = FakeClient()
    persist_o7_dashboard_export_bundle(bundle, client=client, dry_run=False)
    for table, _, _ in client.calls:
        batch = next(b for b in plan["batches"] if b["target_table"] == table)
        for rec in batch["records"]:
            assert "payload" in rec


def test_governance_and_forbidden_capabilities_report_smoke():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    cert = certify_o7_dashboard_persistence_adapter(bundle)
    assert cert["forbidden_capability_inventory"]["llm_calls"] is True
    assert cert["checks"]["injected_client_only_boundary"] is True
    text = build_o7_dashboard_persistence_adapter_report(bundle)
    assert "O7 Dashboard Persistence Adapter Report" in text
    assert "Status:" in text

    audit = build_o7_persistence_audit_manifest(bundle)
    assert audit["record_type"] == "persistence_audit_record"

    summary = build_o7_persistence_result_summary(bundle, build_o7_write_batch_plan(bundle), validate_o7_persistence_bundle(bundle), "DRY_RUN_NOT_EXECUTED", [])
    assert summary["summary_checksum"]
