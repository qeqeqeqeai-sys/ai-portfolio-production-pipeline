from __future__ import annotations

from copy import deepcopy

from transmission_layers.expectation_failure.dashboard_operationalization.d3_controlled_dashboard_persistence_execution import (
    BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID,
    CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY,
    DRY_RUN_NOT_EXECUTED,
    NOT_EXECUTED_NO_CLIENT,
    build_d3_controlled_dashboard_persistence_execution_report,
    build_d3_persistence_execution_plan,
    build_d3_persistence_execution_summary,
    build_d3_persistence_verification_handoff,
    certify_d3_controlled_dashboard_persistence_execution,
    execute_d3_dashboard_persistence,
    validate_d3_persistence_execution_request,
)
from transmission_layers.expectation_failure.dashboard_operationalization.o6_finding_persistence_export_contract import build_o6_dashboard_export_bundle
from transmission_layers.expectation_failure.dashboard_operationalization.o7_dashboard_persistence_adapter import build_o7_write_batch_plan
import transmission_layers.expectation_failure.dashboard_operationalization as pkg


def _o5_payload():
    return {
        "o5_version": "v1",
        "o5_checksum": "abc123",
        "semantic_findings": [{"finding_id": "F-1", "finding_type": "fragility", "finding_title": "T", "lineage_refs": {"o4": "x"}, "supporting_evidence_refs": ["E-1"]}],
        "dashboard_insight_narratives": {"overview": "narr"},
        "finding_evidence_map": {"F-1": ["E-1"]},
        "supervisor_interpretation_panel": {"certification_status": "ok"},
        "certification": {"checksum": "c1"},
    }


class _Resp:
    def __init__(self, data): self.data = data


class FakeClient:
    def __init__(self, fail_table=None):
        self.calls = []
        self.fail_table = fail_table
        self._table = None

    def table(self, table_name):
        self._table = table_name
        return self

    def upsert(self, records, on_conflict=None):
        self.calls.append((self._table, len(records), on_conflict))
        if self.fail_table == self._table:
            raise RuntimeError("boom")
        self._records = records
        return self

    def execute(self):
        return _Resp(self._records)


def test_public_api_presence_and_pkg_export():
    for name in [
        "build_d3_persistence_execution_plan",
        "validate_d3_persistence_execution_request",
        "execute_d3_dashboard_persistence",
        "build_d3_persistence_execution_summary",
        "build_d3_persistence_verification_handoff",
        "certify_d3_controlled_dashboard_persistence_execution",
        "build_d3_controlled_dashboard_persistence_execution_report",
    ]:
        assert hasattr(pkg, name)


def test_determinism_checksum_immutability_and_o6_o7_happy_paths():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    original = deepcopy(bundle)
    p1 = build_d3_persistence_execution_plan(bundle)
    p2 = build_d3_persistence_execution_plan(bundle)
    assert p1 == p2
    assert p1["execution_plan_checksum"] == p2["execution_plan_checksum"]
    assert bundle == original

    o7 = build_o7_write_batch_plan(bundle)
    v = validate_d3_persistence_execution_request(o7)
    assert v["certification_status"] in {CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY, "DEGRADED_DASHBOARD_PERSISTENCE_EXECUTION_READY"}


def test_degraded_and_blocked_paths():
    degraded = validate_d3_persistence_execution_request({})
    assert degraded["certification_status"] in {CERTIFIED_DASHBOARD_PERSISTENCE_EXECUTION_READY, "DEGRADED_DASHBOARD_PERSISTENCE_EXECUTION_READY"}
    blocked = validate_d3_persistence_execution_request({"batches": [{"target_table": "bad", "records": [{}]}]})
    assert blocked["certification_status"] == BLOCKED_DASHBOARD_PERSISTENCE_EXECUTION_INVALID


def test_dry_run_and_no_client_paths():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    c = FakeClient()
    dry = execute_d3_dashboard_persistence(bundle, client=c, dry_run=True)
    assert dry["execution_state"] == DRY_RUN_NOT_EXECUTED
    assert c.calls == []
    nc = execute_d3_dashboard_persistence(bundle, client=None, dry_run=False)
    assert nc["execution_state"] == NOT_EXECUTED_NO_CLIENT


def test_injected_client_success_and_failure_and_shapes_and_handoff():
    bundle = build_o6_dashboard_export_bundle(_o5_payload())
    ok_client = FakeClient()
    ok = execute_d3_dashboard_persistence(bundle, client=ok_client, dry_run=False)
    assert ok["table_results"]
    r = ok["table_results"][0]
    for k in ["target_table", "attempted_record_count", "execution_status", "batch_checksum", "result_checksum"]:
        assert k in r
    assert ok["audit_records"]
    finding_record = next(x for x in bundle["finding_records"] if x["finding_id"] == "F-1")
    assert finding_record["record_id"].startswith("O6FR-")
    assert "lineage_refs" in finding_record and "supporting_evidence_refs" in finding_record and "export_checksum" in finding_record

    fail_client = FakeClient(fail_table="dashboard_finding_records")
    failed = execute_d3_dashboard_persistence(bundle, client=fail_client, dry_run=False)
    assert any(x["execution_status"] == "FAILED" for x in failed["table_results"])

    handoff = build_d3_persistence_verification_handoff(ok)
    assert set(["verification_layer", "summary_checksum", "handoff_checksum"]).issubset(handoff.keys())


def test_governance_report_and_import_smoke():
    cert = certify_d3_controlled_dashboard_persistence_execution(build_o6_dashboard_export_bundle(_o5_payload()))
    assert "forbidden_capability_inventory" in cert
    text = " ".join(cert["forbidden_capability_inventory"].keys())
    assert "llm_calls" in text and "portfolio_optimization" in text
    report = build_d3_controlled_dashboard_persistence_execution_report(build_o6_dashboard_export_bundle(_o5_payload()))
    assert "objective" in report and "certification" in report
    __import__("transmission_layers.expectation_failure.dashboard_operationalization.o9_dashboard_operationalization_closeout")
