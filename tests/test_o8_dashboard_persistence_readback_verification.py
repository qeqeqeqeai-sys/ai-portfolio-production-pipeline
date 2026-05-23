from pathlib import Path
from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization import (
    build_o8_readback_table_contract,
    build_o8_readback_query_plan,
    read_o8_persisted_dashboard_records,
    verify_o8_persisted_dashboard_records,
    build_o8_readback_verification_summary,
    build_o8_persistence_reconciliation_report_payload,
    certify_o8_dashboard_persistence_readback_verification,
    build_o8_dashboard_persistence_readback_verification_report,
)


def _o7_payload():
    return {
        "batches": [
            {"target_table": "dashboard_finding_records", "records": [{"record_id": "R1", "record_type": "finding_record", "finding_id": "F1", "lineage_ref": "L1", "evidence_ref": "E1", "export_checksum": "C1", "source_payload_checksum": "S1"}]},
            {"target_table": "dashboard_narrative_records", "records": [{"record_id": "R2", "record_type": "narrative_record", "export_checksum": "C2", "source_payload_checksum": "S2"}]},
        ]
    }


class _Resp:
    def __init__(self, data): self.data = data

class FakeClient:
    def __init__(self, table_data=None, fail_tables=None):
        self.table_data = table_data or {}
        self.fail_tables = set(fail_tables or [])
        self.calls = 0
    def table(self, name):
        self.name = name
        return self
    def select(self, _):
        return self
    def in_(self, _, ids):
        self.ids = ids
        return self
    def execute(self):
        self.calls += 1
        if self.name in self.fail_tables:
            raise RuntimeError(f"failed:{self.name}")
        return _Resp([r for r in self.table_data.get(self.name, []) if r.get("record_id") in set(self.ids)])


def test_public_api_presence_and_package_exports_and_non_regression_imports():
    import transmission_layers.expectation_failure.dashboard_operationalization as m
    for n in [
        "build_o8_readback_table_contract","build_o8_readback_query_plan","read_o8_persisted_dashboard_records",
        "verify_o8_persisted_dashboard_records","build_o8_readback_verification_summary",
        "build_o8_persistence_reconciliation_report_payload","certify_o8_dashboard_persistence_readback_verification",
        "build_o8_dashboard_persistence_readback_verification_report","build_o7_write_batch_plan","build_o6_dashboard_export_bundle",
    ]:
        assert hasattr(m, n)


def test_determinism_checksum_immutability_and_contract_completeness():
    p = _o7_payload()
    p0 = deepcopy(p)
    assert build_o8_readback_query_plan(p) == build_o8_readback_query_plan(p)
    assert build_o8_readback_table_contract()["contract_checksum"] == build_o8_readback_table_contract()["contract_checksum"]
    assert p == p0
    c = build_o8_readback_table_contract()
    assert len(c["approved_tables"]) == 8
    assert sorted(c["approved_tables"]) == sorted({t["target_table"] for t in c["table_contracts"]})


def test_missing_partial_degraded_and_structural_invalid_blocked():
    d = certify_o8_dashboard_persistence_readback_verification({})
    assert d["certification_status"] == "DEGRADED_READBACK_VERIFIED"
    b = certify_o8_dashboard_persistence_readback_verification("bad")
    assert b["certification_status"] == "BLOCKED_READBACK_INVALID"


def test_dry_run_and_no_client_behavior():
    p = _o7_payload()
    c = FakeClient()
    r = read_o8_persisted_dashboard_records(p, c, dry_run=True)
    assert r["execution_state"] == "DRY_RUN_NOT_EXECUTED"
    assert c.calls == 0
    n = read_o8_persisted_dashboard_records(p, None, dry_run=False)
    assert n["execution_state"] == "NOT_EXECUTED_NO_CLIENT"


def test_injected_client_success_and_failure_encoded():
    p = _o7_payload()
    client = FakeClient({"dashboard_finding_records": [{"record_id": "R1", "finding_id": "F1", "lineage_ref": "L1", "evidence_ref": "E1", "export_checksum": "C1"}], "dashboard_narrative_records": [{"record_id": "R2", "export_checksum": "C2"}]})
    ok = read_o8_persisted_dashboard_records(p, client, dry_run=False)
    assert ok["execution_state"] == "EXECUTED"
    bad = read_o8_persisted_dashboard_records(p, FakeClient(fail_tables={"dashboard_narrative_records"}), dry_run=False)
    assert bad["execution_state"] == "EXECUTED_WITH_FAILURES"


def test_verification_detection_and_preservation_and_reports():
    p = _o7_payload()
    rb = {"table_results": [
        {"target_table": "dashboard_finding_records", "records": [{"record_id": "R1", "finding_id": "F1", "lineage_ref": "L1", "evidence_ref": "E1", "export_checksum": "C1"}, {"record_id": "RX", "export_checksum": "CX"}]},
        {"target_table": "dashboard_narrative_records", "records": [{"record_id": "R2", "export_checksum": "WRONG"}]},
    ]}
    v = verify_o8_persisted_dashboard_records(p, rb)
    assert v["matched_records"]
    assert v["unexpected_records"]
    assert v["checksum_mismatches"]
    assert not v["missing_records"]
    rb_missing = {"table_results": [{"target_table": "dashboard_finding_records", "records": []}]}
    assert verify_o8_persisted_dashboard_records(p, rb_missing)["missing_records"]
    assert build_o8_readback_verification_summary(p, rb)["summary_checksum"]
    assert build_o8_persistence_reconciliation_report_payload(p, rb)["verification"]["verification_checksum"]
    rep = build_o8_dashboard_persistence_readback_verification_report(p, rb)
    assert rep["report_checksum"]


def test_no_unapproved_routing_and_governance_forbidden_inventory_and_language_checks():
    p = {"batches": [{"target_table": "bad_table", "records": []}]}
    c = certify_o8_dashboard_persistence_readback_verification(p)
    assert c["certification_status"] == "BLOCKED_READBACK_INVALID"
    assert c["forbidden_capability_inventory"]["environment_variable_reads"] is True
    cert_text = str(c["forbidden_capability_inventory"])
    assert "trading_instructions" in cert_text
    module_text = Path("transmission_layers/expectation_failure/dashboard_operationalization/o8_dashboard_persistence_readback_verification.py").read_text().lower()
    for blocked_call in ["os.environ", "openai", "requests.get", "client = create_client"]:
        assert blocked_call not in module_text
