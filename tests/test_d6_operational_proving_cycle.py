from transmission_layers.expectation_failure.dashboard_operationalization.d6_operational_proving_cycle import (
    build_d6_operational_proving_input,
    execute_d6_operational_proving_cycle,
    build_d6_operational_proving_summary,
    build_d6_operational_proving_report,
    certify_d6_operational_proving_cycle,
)


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


def test_d6_dry_run_graceful_and_reporting_shape():
    result = execute_d6_operational_proving_cycle(build_d6_operational_proving_input(), client=None, dry_run=True)
    summary = build_d6_operational_proving_summary(result)
    report = build_d6_operational_proving_report(result)
    cert = certify_d6_operational_proving_cycle(result)
    assert summary["persistence_state"] == "DRY_RUN_NOT_EXECUTED"
    assert summary["readback_verification_status"] in {"CERTIFIED_REAL_READBACK_VERIFIED", "DEGRADED_REAL_READBACK_VERIFIED"}
    assert "evaluation" in report and "observed_limitations" in report
    assert cert["certification_status"].startswith("CERTIFIED_") or cert["certification_status"].startswith("DEGRADED_")
