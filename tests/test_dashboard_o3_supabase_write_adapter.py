from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from copy import deepcopy

from transmission_layers.expectation_failure import dashboard_operationalization as mod
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o1_export_schema import build_dashboard_o1_export_payload
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o2_supabase_contracts import build_dashboard_o2_upsert_payload
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o3_supabase_write_adapter import (
    build_dashboard_o3_dry_run_report,
    build_dashboard_o3_persistence_audit_report,
    build_dashboard_o3_write_plan,
    build_dashboard_o3_write_result_manifest,
    execute_dashboard_o3_write_plan,
    validate_dashboard_o3_write_plan,
)


def _o2_payload():
    o1 = build_dashboard_o1_export_payload(
        run_id="run-001",
        run_date_sgt="2026-05-22",
        entity_rows=[{"entity_id": "E1", "entity_name": "A", "ticker": "AAA", "subsector": "AI", "composite_score": 81}],
        alert_rows=[{"run_id": "run-001", "entity_id": "E1", "ticker": "AAA", "subsector": "AI", "alert_state": "watch"}],
        replay_rows=[{"run_id": "run-001", "replay_date_sgt": "2026-05-21", "entity_id": "E1", "replay_sequence": 1}],
        benchmark_rows=[{"run_id": "run-001", "entity_id": "E1", "benchmark_id": "QQQ"}],
        evidence_rows=[{"run_id": "run-001", "entity_id": "E1", "evidence_id": "EV1"}],
    )
    return build_dashboard_o2_upsert_payload(o1)


class _MockTable:
    def __init__(self, parent, table_name, fail=False):
        self.parent = parent
        self.table_name = table_name
        self.fail = fail

    def upsert(self, rows, on_conflict):
        self.parent.calls.append((self.table_name, rows, on_conflict))
        return self

    def execute(self):
        if self.fail and self.table_name == "dashboard_alert_facts":
            raise RuntimeError("forced failure")
        return {"ok": True}


class _MockClient:
    def __init__(self, fail=False):
        self.calls = []
        self.fail = fail

    def table(self, table_name):
        return _MockTable(self, table_name, fail=self.fail)


def test_public_apis_exist_and_additive_exports():
    for name in [
        "build_dashboard_o3_write_plan",
        "validate_dashboard_o3_write_plan",
        "execute_dashboard_o3_write_plan",
        "build_dashboard_o3_write_result_manifest",
        "build_dashboard_o3_dry_run_report",
        "build_dashboard_o3_persistence_audit_report",
    ]:
        assert hasattr(mod, name)


def test_determinism_checksum_order_and_immutability():
    payload = _o2_payload()
    original = deepcopy(payload)
    a = build_dashboard_o3_write_plan(payload)
    b = build_dashboard_o3_write_plan(deepcopy(payload))
    assert a == b
    assert payload == original
    assert a["write_plan_checksum"] == b["write_plan_checksum"]
    assert [s["step_sequence"] for s in a["write_steps"]] == list(range(1, len(a["write_steps"]) + 1))


def test_dry_run_default_and_no_client_calls():
    plan = build_dashboard_o3_write_plan(_o2_payload())
    client = _MockClient()
    out = execute_dashboard_o3_write_plan(plan, supabase_client=client)
    assert plan["dry_run"] is True
    assert out["execution_status"] == "completed"
    assert all(r["status"] == "skipped" for r in out["table_results"])
    assert client.calls == []


def test_execute_mode_requires_client_and_uses_injected_only():
    plan = build_dashboard_o3_write_plan(_o2_payload(), execution_mode="execute", dry_run=False)
    missing = execute_dashboard_o3_write_plan(plan)
    assert missing["execution_status"] == "failed"

    client = _MockClient()
    out = execute_dashboard_o3_write_plan(plan, supabase_client=client)
    assert out["execution_status"] == "completed"
    assert len(client.calls) == len(plan["write_steps"])
    expected_names = [s["table_name"] for s in plan["write_steps"]]
    assert [c[0] for c in client.calls] == expected_names
    assert [c[2] for c in client.calls] == [s["on_conflict"] for s in plan["write_steps"]]


def test_bounded_exception_validation_and_invalid_plan_failures():
    plan = build_dashboard_o3_write_plan(_o2_payload(), execution_mode="execute", dry_run=False)
    out = execute_dashboard_o3_write_plan(plan, supabase_client=_MockClient(fail=True))
    assert any(r["status"] == "failed" for r in out["table_results"])
    failed = [r for r in out["table_results"] if r["status"] == "failed"][0]
    assert failed["error_type"]
    assert failed["error_message_short"]

    invalid = deepcopy(plan)
    invalid.pop("write_steps")
    vr = validate_dashboard_o3_write_plan(invalid)
    assert vr["validation_status"] == "invalid"

    dup = deepcopy(plan)
    dup["write_steps"][0]["unique_key"] = ["run_id", "run_id"]
    assert validate_dashboard_o3_write_plan(dup)["validation_status"] == "invalid"

    mismatch = deepcopy(plan)
    mismatch["write_steps"][0]["row_count"] = 999
    assert validate_dashboard_o3_write_plan(mismatch)["validation_status"] == "invalid"


def test_forbidden_language_absence_manifest_and_reports_determinism():
    plan = build_dashboard_o3_write_plan(_o2_payload())
    assert validate_dashboard_o3_write_plan(plan)["validation_status"] == "valid"
    result = execute_dashboard_o3_write_plan(plan)

    manifest = build_dashboard_o3_write_result_manifest(plan, result)
    assert manifest["table_count"] == len(plan["write_steps"])
    assert manifest["total_row_count"] == sum(s["row_count"] for s in plan["write_steps"])

    dr1 = build_dashboard_o3_dry_run_report(plan, result)
    dr2 = build_dashboard_o3_dry_run_report(plan, result)
    assert dr1 == dr2

    ar1 = build_dashboard_o3_persistence_audit_report(plan, result)
    ar2 = build_dashboard_o3_persistence_audit_report(plan, result)
    assert ar1 == ar2
    assert ar1["boundaries"]["no_file_writes"] is True
    assert ar1["boundaries"]["no_streamlit_ui"] is True
