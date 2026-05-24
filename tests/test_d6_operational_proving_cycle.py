from transmission_layers.expectation_failure.dashboard_operationalization.d6_operational_proving_cycle import (
    build_d6_operational_proving_input,
    execute_d6_operational_proving_cycle,
    build_d6_operational_proving_summary,
    build_d6_operational_proving_report,
    certify_d6_operational_proving_cycle,
    build_d6_post_execution_audit_record,
    build_d6_post_execution_replay_record,
    persist_d6_post_execution_summary_records,
)
from transmission_layers.expectation_failure.dashboard_operationalization.d3_controlled_dashboard_persistence_execution import EXECUTED_WITH_FAILURES
from scripts.run_d6_real_proving_cycle import _print_d3_persistence_diagnostics


class _Resp:
    def __init__(self, data):
        self.data = data


class FakeSupabaseClient:
    def __init__(self):
        self.tables = {}
        self._table = ""
        self._records = []

    def table(self, table_name):
        self._table = table_name
        return self

    def upsert(self, records, on_conflict=None):
        self._records = list(records)
        bucket = {str(r.get("record_id") or ""): dict(r) for r in self.tables.get(self._table, [])}
        for r in self._records:
            bucket[str(r.get("record_id") or "")] = dict(r)
        self.tables[self._table] = list(bucket.values())
        return self

    def select(self, _):
        return self

    def in_(self, field, values):
        vals = set(values)
        self._records = [r for r in self.tables.get(self._table, []) if r.get(field) in vals]
        return self

    def execute(self):
        return _Resp(self._records)


def test_d6_deterministic_and_injected_client_orchestration():
    inp = build_d6_operational_proving_input()
    assert inp["input_checksum"]
    client = FakeSupabaseClient()
    a = execute_d6_operational_proving_cycle(inp, client=client, dry_run=False)
    b = execute_d6_operational_proving_cycle(inp, client=client, dry_run=False)
    assert a["cycle_checksum"] == b["cycle_checksum"]
    assert a["o5"]["semantic_findings"]
    assert a["o5"]["dashboard_insight_narratives"]
    assert a["o5"]["finding_evidence_map"]
    assert a["d3_persistence"]["execution_state"] == "EXECUTED"
    assert a["d4_readback"]["execution_state"] == "EXECUTED"
    assert a["d6_post_execution_summary_persistence"]["execution_state"] == "EXECUTED"


def test_d6_post_execution_record_builders_are_deterministic():
    result = execute_d6_operational_proving_cycle(build_d6_operational_proving_input(), client=FakeSupabaseClient(), dry_run=False)
    a1 = build_d6_post_execution_audit_record(result)
    a2 = build_d6_post_execution_audit_record(result)
    r1 = build_d6_post_execution_replay_record(result)
    r2 = build_d6_post_execution_replay_record(result)
    assert a1 == a2
    assert r1 == r2
    assert a1["record_type"] == "d3_execution_summary_record"
    assert r1["record_type"] == "d6_operational_cycle_replay_record"


def test_d6_post_execution_persistence_respects_dry_run_and_client():
    base = execute_d6_operational_proving_cycle(build_d6_operational_proving_input(), client=FakeSupabaseClient(), dry_run=False)
    dry = persist_d6_post_execution_summary_records(base, client=FakeSupabaseClient(), dry_run=True)
    noclient = persist_d6_post_execution_summary_records(base, client=None, dry_run=False)
    persisted = persist_d6_post_execution_summary_records(base, client=FakeSupabaseClient(), dry_run=False)
    assert dry["execution_state"] == "DRY_RUN_NOT_EXECUTED"
    assert noclient["execution_state"] == "NOT_EXECUTED_NO_CLIENT"
    assert persisted["execution_state"] == "EXECUTED"


def test_d6_dry_run_graceful_and_reporting_shape():
    result = execute_d6_operational_proving_cycle(build_d6_operational_proving_input(), client=None, dry_run=True)
    summary = build_d6_operational_proving_summary(result)
    report = build_d6_operational_proving_report(result)
    cert = certify_d6_operational_proving_cycle(result)
    assert summary["persistence_state"] == "DRY_RUN_NOT_EXECUTED"
    assert summary["readback_verification_status"] in {"CERTIFIED_REAL_READBACK_VERIFIED", "DEGRADED_REAL_READBACK_VERIFIED"}
    assert "evaluation" in report and "observed_limitations" in report
    assert cert["certification_status"].startswith("CERTIFIED_") or cert["certification_status"].startswith("DEGRADED_")


def test_d6_summary_degrades_certified_readback_when_persistence_failed():
    result = execute_d6_operational_proving_cycle(build_d6_operational_proving_input(), client=FakeSupabaseClient(), dry_run=False)
    result["d3_persistence"]["execution_state"] = EXECUTED_WITH_FAILURES
    summary = build_d6_operational_proving_summary(result)
    report = build_d6_operational_proving_report(result)
    assert summary["readback_verification_status_raw"] == "CERTIFIED_REAL_READBACK_VERIFIED"
    assert summary["readback_verification_status"] == "DEGRADED_REAL_READBACK_VERIFIED"
    assert summary["persistence_failure_impacts_readback"] is True
    assert report["persistence_observability"]["persistence_failure_impacts_readback"] is True


def test_d6_summary_degrades_certified_readback_when_expected_but_zero_persisted():
    result = execute_d6_operational_proving_cycle(build_d6_operational_proving_input(), client=FakeSupabaseClient(), dry_run=False)
    for row in result["d3_persistence"]["table_results"]:
        row["persisted_record_count"] = 0
    summary = build_d6_operational_proving_summary(result)
    assert summary["persistence_expected_record_count"] > 0
    assert summary["persistence_persisted_record_count"] == 0
    assert summary["persistence_zero_records_with_expected"] is True
    assert summary["readback_verification_status"] == "DEGRADED_REAL_READBACK_VERIFIED"


def test_runner_prints_actionable_d3_persistence_diagnostics(capsys):
    _print_d3_persistence_diagnostics(
        {
            "d3_persistence": {
                "table_results": [
                    {
                        "target_table": "dashboard_finding_records",
                        "execution_status": "FAILED",
                        "attempted_record_count": 3,
                        "persisted_record_count": 0,
                        "error_type": "RuntimeError",
                        "error_message_short": "boom",
                        "batch_checksum": "abc123",
                    }
                ]
            }
        }
    )
    out = capsys.readouterr().out
    assert "d3_persistence_diagnostics=" in out
    assert "target_table=dashboard_finding_records" in out
    assert "execution_status=FAILED" in out
    assert "attempted_record_count=3" in out
    assert "persisted_record_count=0" in out
    assert "error_type=RuntimeError" in out
    assert "error_message_short=boom" in out
    assert "batch_checksum=abc123" in out
