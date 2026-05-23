from copy import deepcopy

import transmission_layers.expectation_failure.dashboard_operationalization as pkg
from transmission_layers.expectation_failure.dashboard_operationalization.d4_real_persistence_readback_verification import *


class _Resp:
    def __init__(self, data):
        self.data = data


class FakeClient:
    def __init__(self, table_to_data=None, fail_tables=None):
        self.table_to_data = table_to_data or {}
        self.fail_tables = set(fail_tables or [])
        self.calls = 0

    def table(self, name):
        self._table = name
        return self

    def select(self, _):
        return self

    def in_(self, _, __):
        return self

    def execute(self):
        self.calls += 1
        if self._table in self.fail_tables:
            raise RuntimeError("boom")
        return _Resp(self.table_to_data.get(self._table, []))


def _d3_like_payload():
    return {
        "batches": [
            {"target_table": "dashboard_finding_records", "records": [{"record_id": "r1", "finding_id": "f1", "evidence_refs": ["e1"], "lineage_refs": ["l1"], "export_checksum": "c1"}]}
        ]
    }


def test_public_api_and_exports_and_non_regression_imports():
    for fn in (
        "build_d4_readback_execution_plan",
        "validate_d4_readback_execution_request",
        "execute_d4_dashboard_readback",
        "verify_d4_dashboard_persistence",
        "build_d4_readback_execution_summary",
        "build_d4_dashboard_verification_handoff",
        "certify_d4_real_persistence_readback_verification",
        "build_d4_real_persistence_readback_verification_report",
    ):
        assert fn in globals()
        assert hasattr(pkg, fn)
    assert hasattr(pkg, "build_o8_readback_query_plan")
    assert hasattr(pkg, "execute_d3_dashboard_persistence")


def test_deterministic_checksum_and_immutability():
    payload = _d3_like_payload()
    frozen = deepcopy(payload)
    p1 = build_d4_readback_execution_plan(payload)
    p2 = build_d4_readback_execution_plan(payload)
    assert p1 == p2
    assert p1["execution_plan_checksum"] == p2["execution_plan_checksum"]
    assert payload == frozen


def test_happy_paths_and_degraded_blocked():
    d3_payload = _d3_like_payload()
    o8_plan = {"query_items": [{"query_id": "q1", "target_table": "dashboard_finding_records", "expected_record_ids": ["r1"], "expected_checksums": ["c1"], "expected_record_count": 1}]}
    assert build_d4_readback_execution_plan(d3_payload)["query_items"]
    assert build_d4_readback_execution_plan(o8_plan)["query_items"]
    assert validate_d4_readback_execution_request({})["certification_status"] == DEGRADED_REAL_READBACK_VERIFIED
    assert validate_d4_readback_execution_request("bad")["certification_status"] == BLOCKED_REAL_READBACK_INVALID


def test_dry_run_and_no_client_and_success_failure_paths():
    payload = {"query_items": [{"query_id": "q1", "target_table": "dashboard_finding_records", "expected_record_ids": ["r1"], "expected_checksums": ["c1"], "expected_record_count": 1}]}
    client = FakeClient({"dashboard_finding_records": [{"record_id": "r1", "finding_id": "f1", "evidence_refs": ["e1"], "lineage_refs": ["l1"], "export_checksum": "c1"}]})
    dry = execute_d4_dashboard_readback(payload, client=client, dry_run=True)
    assert dry["execution_state"] == DRY_RUN_NOT_EXECUTED
    assert client.calls == 0
    noc = execute_d4_dashboard_readback(payload, client=None, dry_run=False)
    assert noc["execution_state"] == NOT_EXECUTED_NO_CLIENT
    ok = execute_d4_dashboard_readback(payload, client=client, dry_run=False)
    assert ok["execution_state"] == EXECUTED
    shape = ok["table_results"][0]
    for key in ("target_table", "expected_record_count", "returned_record_count", "readback_status", "error_type", "error_message_short", "query_checksum", "result_checksum"):
        assert key in shape
    fail = execute_d4_dashboard_readback(payload, client=FakeClient(fail_tables=["dashboard_finding_records"]), dry_run=False)
    assert fail["execution_state"] == EXECUTED_WITH_FAILURES
    assert fail["table_results"][0]["readback_status"] == "READBACK_FAILED"


def test_verification_and_handoff_certification_report_and_governance_text():
    payload = {"query_items": [{"query_id": "q1", "target_table": "dashboard_finding_records", "expected_record_ids": ["r1", "r2"], "expected_checksums": ["c1", "c2"], "expected_record_count": 2}]}
    readback = {"table_results": [{"target_table": "dashboard_finding_records", "records": [{"record_id": "r1", "finding_id": "f1", "evidence_refs": ["e1"], "lineage_refs": ["l1"], "export_checksum": "bad"}, {"record_id": "r3", "export_checksum": "cx"}]}]}
    v = verify_d4_dashboard_persistence(payload, readback)
    assert v["matched_records"] == []
    assert v["missing_records"]
    assert v["checksum_mismatches"]
    assert v["unexpected_records"]
    summary = execute_d4_dashboard_readback(payload, client=None, dry_run=True)
    handoff = build_d4_dashboard_verification_handoff(summary, v)
    assert "handoff_checksum" in handoff
    cert = certify_d4_real_persistence_readback_verification(payload)
    assert "forbidden_capability_inventory" in cert
    assert cert["checks"]["injected_client_only_boundary"] is True
    assert cert["checks"]["dry_run_safety"] is True
    report = build_d4_real_persistence_readback_verification_report(payload)
    assert "certification" in report and "verification" in report
    inv = list(cert["forbidden_capability_inventory"].keys())
    assert "internal_supabase_client_creation" in inv
