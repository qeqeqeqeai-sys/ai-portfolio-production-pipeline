from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_controlled_replay_backfill_execution import build_d8_b2_dry_run_source_diagnostics
from transmission_layers.expectation_failure.expectation_intelligence.d8_b2r_replay_candidate_source_repair_audit import (
    adapt_history_row_to_candidate,
    audit_replay_candidate_sources,
    audit_supabase_client_resolution,
    build_d8_b2r_source_repair_report_payload,
    build_replay_candidate_source_inventory,
)


class _FakeResult:
    def __init__(self, data):
        self.data = data


class _FakeTable:
    def __init__(self, rows, fail=False):
        self._rows = rows
        self._fail = fail

    def select(self, _):
        return self

    def limit(self, _):
        return self

    def execute(self):
        if self._fail:
            raise RuntimeError("table_missing")
        return _FakeResult(self._rows)


class _FakeClient:
    def __init__(self, mapping):
        self.mapping = mapping

    def table(self, name):
        value = self.mapping.get(name, [])
        if isinstance(value, Exception):
            return _FakeTable([], fail=True)
        return _FakeTable(value)


def _history_row(i=1):
    return {"run_id": f"r{i}", "run_timestamp": "2026-05-20T00:00:00Z", "payload_checksum": f"c{i}", "source_trace": "persisted_replay", "payload_reference": f"p{i}"}


def test_client_unresolved_diagnosis():
    out = audit_supabase_client_resolution(runtime_config={"credentials_present": False}, client=None, client_factory=None)
    assert out["client_resolved"] is False


def test_source_empty_but_valid():
    client = _FakeClient({"dashboard_replay_metadata_records": [], "dashboard_export_manifests": []})
    src = audit_replay_candidate_sources(client=client)
    report = build_d8_b2r_source_repair_report_payload(client_audit={"client_resolved": True}, source_audit=src)
    assert report["status"] == "SOURCE_EMPTY_BUT_VALID"


def test_table_mismatch_diagnosis():
    client = _FakeClient({"dashboard_replay_metadata_records": RuntimeError("x"), "dashboard_export_manifests": RuntimeError("x")})
    src = audit_replay_candidate_sources(client=client)
    report = build_d8_b2r_source_repair_report_payload(client_audit={"client_resolved": True}, source_audit=src)
    assert report["status"] == "SOURCE_BLOCKED_TABLE_MISMATCH"


def test_shape_mismatch_diagnosis():
    inv = build_replay_candidate_source_inventory(replay_rows=[{"replay_id": "x"}], historical_runs_payloads=[{"run_id": "r1"}])
    source = {"accessible_tables": ["dashboard_replay_metadata_records"], "inventory": inv, "shape_comparison": {"source_shape_compatible": False}}
    report = build_d8_b2r_source_repair_report_payload(client_audit={"client_resolved": True}, source_audit=source)
    assert report["status"] == "SOURCE_BLOCKED_SHAPE_MISMATCH"


def test_source_ready_inventory_and_adapter_rules():
    cand = adapt_history_row_to_candidate(_history_row(1))
    assert cand is not None and cand["run_id"] == "r1"
    assert adapt_history_row_to_candidate({"run_id": "r2", "run_timestamp": "2026-05-20T00:00:00Z"}) is None


def test_no_fabricated_candidates():
    inv = build_replay_candidate_source_inventory(replay_rows=[{"replay_id": "x"}], historical_runs_payloads=[{"run_id": "r1"}])
    assert inv["candidate_derivation_source_count"] == 0


def test_d8_b2_dry_run_integration_status_client_unresolved():
    out = build_d8_b2_dry_run_source_diagnostics(runtime_config={"credentials_present": False}, client=None)
    assert out["status"] == "SOURCE_BLOCKED_CLIENT_UNRESOLVED"
