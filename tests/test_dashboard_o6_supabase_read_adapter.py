from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o6_supabase_read_adapter import (
    build_dashboard_o6_read_adapter_report_payload,
    build_dashboard_read_column_inventory,
    build_dashboard_read_table_inventory,
    build_dashboard_supabase_snapshot,
    load_dashboard_entity_facts,
)


class _Result:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, table, data, recorder, fail=False):
        self.table_name = table
        self.data = data
        self.recorder = recorder
        self.fail = fail

    def select(self, columns):
        self.recorder.append(("select", self.table_name, columns))
        return self

    def eq(self, key, value):
        self.recorder.append(("eq", self.table_name, key, value))
        self.data = [r for r in self.data if r.get(key) == value]
        return self

    def order(self, key, desc=False):
        self.recorder.append(("order", self.table_name, key, desc))
        self.data = sorted(self.data, key=lambda r: r.get(key))
        return self

    def limit(self, value):
        self.recorder.append(("limit", self.table_name, value))
        self.data = self.data[:value]
        return self

    def execute(self):
        if self.fail:
            raise RuntimeError("query failed")
        self.recorder.append(("execute", self.table_name))
        return _Result(self.data)


class FakeClient:
    def __init__(self, datasets, fail_tables=None):
        self.datasets = deepcopy(datasets)
        self.fail_tables = set(fail_tables or [])
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return FakeQuery(name, deepcopy(self.datasets.get(name, [])), self.calls, fail=name in self.fail_tables)


def test_inventory_and_exports_are_fixed_and_additive():
    tables = build_dashboard_read_table_inventory()
    cols = build_dashboard_read_column_inventory()
    assert tables == [
        "dashboard_entity_facts", "dashboard_subsector_facts", "dashboard_alert_facts", "dashboard_benchmark_facts", "dashboard_replay_facts", "dashboard_evidence_facts", "dashboard_certification_reports", "dashboard_run_manifests",
    ]
    assert set(cols.keys()) == set(tables)
    for name in [
        "build_dashboard_read_table_inventory", "build_dashboard_read_column_inventory", "load_dashboard_entity_facts", "load_dashboard_subsector_facts", "load_dashboard_alert_facts", "load_dashboard_benchmark_facts", "load_dashboard_replay_facts", "load_dashboard_evidence_facts", "load_dashboard_certification_metadata", "build_dashboard_supabase_snapshot", "build_dashboard_o6_read_adapter_report_payload",
    ]:
        assert hasattr(mod, name)


def test_deterministic_repeated_output_limit_clamping_immutability_and_no_writes():
    data = {"dashboard_entity_facts": [{"run_id": "r1", "run_date_sgt": "2026-05-22", "entity_id": "E2"}, {"run_id": "r1", "run_date_sgt": "2026-05-22", "entity_id": "E1"}]}
    original = deepcopy(data)
    c1 = FakeClient(data)
    c2 = FakeClient(data)
    a = load_dashboard_entity_facts(c1, run_id="r1", as_of_date="2026-05-22", limit=9999)
    b = load_dashboard_entity_facts(c2, run_id="r1", as_of_date="2026-05-22", limit=9999)
    assert data == original
    assert a == b
    assert a["applied_limit"] == 500
    assert a["status"] == "ok"
    call_text = str(c1.calls).lower()
    for forbidden in ["insert", "update", "delete", "upsert", "rpc", "sql"]:
        assert forbidden not in call_text


def test_injected_client_only_degraded_failure_empty_behavior_and_snapshot_sections():
    none_result = load_dashboard_entity_facts(None)
    assert none_result["status"] == "degraded"
    assert none_result["rows"] == []

    c = FakeClient({"dashboard_entity_facts": []}, fail_tables={"dashboard_entity_facts"})
    failed = load_dashboard_entity_facts(c)
    assert failed["status"] == "degraded"
    assert "RuntimeError" in failed["error"]

    snap = build_dashboard_supabase_snapshot(FakeClient({}))
    expected_keys = [
        "schema_version", "module_version", "table_inventory", "column_inventory", "entity_facts", "subsector_facts", "alert_facts", "benchmark_facts", "replay_facts", "evidence_facts", "certification_metadata", "invariant_flags",
    ]
    assert list(snap.keys()) == expected_keys
    assert snap["entity_facts"]["rows"] == []


def test_report_payload_stable():
    a = build_dashboard_o6_read_adapter_report_payload()
    b = build_dashboard_o6_read_adapter_report_payload()
    assert a == b
