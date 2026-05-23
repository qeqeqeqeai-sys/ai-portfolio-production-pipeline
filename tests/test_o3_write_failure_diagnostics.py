from __future__ import annotations

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o2_supabase_contracts import build_dashboard_o2_upsert_payload
from transmission_layers.expectation_failure.dashboard_operationalization.dashboard_o3_supabase_write_adapter import build_dashboard_o3_write_plan, execute_dashboard_o3_write_plan


class _FailingTable:
    def __init__(self, name: str):
        self.name = name

    def upsert(self, rows, on_conflict):
        return self

    def execute(self):
        raise RuntimeError("permission denied by row-level security for token=SECRET_TOKEN and SUPABASE_SERVICE_ROLE_KEY=abc")


class _FailingClient:
    def table(self, table_name):
        return _FailingTable(table_name)


class _SuccessTable:
    def upsert(self, rows, on_conflict):
        self._rows = rows
        return self

    def execute(self):
        return {"data": list(self._rows)}


class _SuccessClient:
    def table(self, table_name):
        return _SuccessTable()


def _payload():
    return {
        "dashboard_entity_facts": [{"run_id": "r1", "entity_id": "e1", "entity_name": "A"}],
        "dashboard_subsector_facts": [{"run_id": "r1", "subsector": "AI"}],
        "dashboard_alert_facts": [{"run_id": "r1", "entity_id": "e1", "alert_state": "watch"}],
        "dashboard_replay_facts": [{"run_id": "r1", "replay_date_sgt": "2026-01-01", "entity_id": "e1", "replay_sequence": "1"}],
        "dashboard_benchmark_facts": [{"run_id": "r1", "entity_id": "e1", "benchmark_id": "b1"}],
        "dashboard_evidence_facts": [{"run_id": "r1", "entity_id": "e1", "evidence_id": "ev1"}],
        "dashboard_certification_reports": [{"run_id": "r1", "report_id": "rp1"}],
        "dashboard_run_manifests": [{"run_id": "r1", "checksum": "c1"}],
    }


def test_failed_o3_write_diagnostics_include_type_message_and_redaction():
    o2 = build_dashboard_o2_upsert_payload(_payload())
    plan = build_dashboard_o3_write_plan(o2, execution_mode="execute", dry_run=False)
    out = execute_dashboard_o3_write_plan(plan, supabase_client=_FailingClient())
    failed = out["table_results"][0]
    assert failed["status"] == "failed"
    assert failed["error_type"] == "rls_or_policy_failure"
    assert failed["error_message_short"]
    assert len(failed["error_message_short"]) <= 200
    assert "SUPABASE_SERVICE_ROLE_KEY" not in failed["error_message_short"]


def test_successful_writes_have_stable_diagnostics_shape():
    o2 = build_dashboard_o2_upsert_payload(_payload())
    plan = build_dashboard_o3_write_plan(o2, execution_mode="execute", dry_run=False)
    out = execute_dashboard_o3_write_plan(plan, supabase_client=_SuccessClient())
    first = out["table_results"][0]
    assert first["status"] == "success"
    assert "payload_sample_keys" in first
    assert "missing_payload_columns" in first


def test_runner_prints_detailed_diagnostics_and_nonzero_failure_guard():
    text = Path("scripts/run_d1_dashboard_sample_seed.py").read_text(encoding="utf-8")
    assert "write_result_statuses_detailed=" in text
    assert "error_type=" in text
    assert "if execute and any(status == \"failed\" for status in table_write_statuses.values()):" in text
    assert "return 1" in text


def test_no_raw_sql_runtime_execution_added():
    text = Path("transmission_layers/expectation_failure/dashboard_operationalization/dashboard_o3_supabase_write_adapter.py").read_text(encoding="utf-8").lower()
    assert "execute_sql" not in text
    assert "sql(" not in text
