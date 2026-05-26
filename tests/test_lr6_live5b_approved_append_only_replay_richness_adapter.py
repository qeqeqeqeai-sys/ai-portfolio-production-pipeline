from __future__ import annotations

import importlib

from scripts import run_lr6_live5_first_approved_non_dry_persistence_execution as runner
from transmission_layers.expectation_failure.replay_ecology.persistence.adapters import replay_richness_wave0_shadow_append_only_adapter as adapter


class _Resp:
    def __init__(self, count: int):
        self.count = count


class _Table:
    def __init__(self, dup=False):
        self.rows = []
        self.dup = dup

    def insert(self, rows):
        self.rows.extend(rows)
        return self

    def execute(self):
        count = len(self.rows)
        if self.dup:
            count = max(0, count - 1)
        return _Resp(count)


class FakeClient:
    def __init__(self, dup=False):
        self.dup = dup
        self.table_name = None
        self.t = _Table(dup=dup)

    def table(self, name):
        self.table_name = name
        return self.t


def _intent(key="k1"):
    return {
        "duplicate_prevention_key": key,
        "payload": {"metric_dimension": "replay_richness", "entity_id": "E1", "source_artifact_refs": ["a"]},
        "lineage_metadata": {"source_artifact_refs": ["a"]},
        "rollback_metadata": {"rollback_ready": True},
    }


def test_adapter_api_exists():
    assert callable(adapter.execute_append_only_insert)
    assert adapter.APPROVED_ADAPTER_NAME == "replay_richness_wave0_shadow_append_only_adapter"


def test_adapter_restrictions_and_safety_rejections():
    c = FakeClient()
    common = {"metric_target": "replay_richness", "target_name": "replay_richness_wave0_shadow", "append_only": True, "mode": "append_only_insert", "schema_confirmed": True}
    assert adapter.execute_append_only_insert(insert_intents=[_intent()], metadata={**common, "target_name": "wrong"}, client=c)["halt_triggered"] is True
    assert adapter.execute_append_only_insert(insert_intents=[_intent() for _ in range(6)], metadata=common, client=c)["halt_triggered"] is True
    bad = _intent(); bad["lineage_metadata"] = {}
    assert adapter.execute_append_only_insert(insert_intents=[bad], metadata=common, client=c)["halt_reason"] == "missing_lineage_metadata"
    bad = _intent(); bad["rollback_metadata"] = {}
    assert adapter.execute_append_only_insert(insert_intents=[bad], metadata=common, client=c)["halt_reason"] == "missing_rollback_metadata"
    bad = _intent(); bad["duplicate_prevention_key"] = ""
    assert adapter.execute_append_only_insert(insert_intents=[bad], metadata=common, client=c)["halt_reason"] == "missing_duplicate_prevention_key"
    assert adapter.execute_append_only_insert(insert_intents=[_intent()], metadata={**common, "upsert": True}, client=c)["halt_triggered"] is True
    assert adapter.execute_append_only_insert(insert_intents=[_intent()], metadata={**common, "direct_sql": True}, client=c)["direct_sql_used"] is False


def test_success_and_duplicate_reporting():
    m = {"metric_target": "replay_richness", "target_name": "replay_richness_wave0_shadow", "append_only": True, "mode": "append_only_insert", "schema_confirmed": True}
    r = adapter.execute_append_only_insert(insert_intents=[_intent("k1")], metadata=m, client=FakeClient())
    assert r["inserted_rows"] == 1
    r2 = adapter.execute_append_only_insert(insert_intents=[_intent("k1"), _intent("k1")], metadata=m, client=FakeClient())
    assert r2["duplicate_prevented"] is True




def test_adapter_inserts_only_approved_top_level_columns():
    m = {"metric_target": "replay_richness", "target_name": "replay_richness_wave0_shadow", "append_only": True, "mode": "append_only_insert", "schema_confirmed": True}
    c = FakeClient()
    intent = _intent("k100")
    intent["payload"].update({
        "wave_id": "wave-0",
        "comparison_ready": True,
        "payload_id": "p-123",
        "replay_window_label": "window-a",
        "custom_field": "x",
    })

    r = adapter.execute_append_only_insert(insert_intents=[intent], metadata=m, client=c)
    assert r["halt_triggered"] is False
    assert len(c.t.rows) == 1
    row = c.t.rows[0]

    assert set(row.keys()) == set(adapter.APPROVED_TOP_LEVEL_COLUMNS)
    assert "payload_id" not in row
    assert "replay_window_label" not in row
    assert "custom_field" not in row

    assert row["payload"]["payload_id"] == "p-123"
    assert row["payload"]["replay_window_label"] == "window-a"
    assert row["payload"]["custom_field"] == "x"


def test_no_dynamic_column_whack_a_mole_behavior_for_multiple_rows():
    m = {"metric_target": "replay_richness", "target_name": "replay_richness_wave0_shadow", "append_only": True, "mode": "append_only_insert", "schema_confirmed": True}
    c = FakeClient()
    a = _intent("k1")
    b = _intent("k2")
    a["payload"].update({"payload_id": "p1", "new_dynamic_a": 1})
    b["payload"].update({"replay_window_label": "w2", "new_dynamic_b": 2})

    r = adapter.execute_append_only_insert(insert_intents=[a, b], metadata=m, client=c)
    assert r["inserted_rows"] == 2
    assert len(c.t.rows) == 2
    for row in c.t.rows:
        assert set(row.keys()) == set(adapter.APPROVED_TOP_LEVEL_COLUMNS)

    assert c.t.rows[0]["payload"]["new_dynamic_a"] == 1
    assert c.t.rows[1]["payload"]["new_dynamic_b"] == 2

def test_live5_runner_uses_adapter_and_not_no_adapter(monkeypatch):
    monkeypatch.setenv("LIVE5_APPROVAL_PHRASE", "LIVE5")
    monkeypatch.setenv("LIVE5_NON_DRY_EXECUTION_TOKEN", "LIVE5")
    monkeypatch.setenv("LIVE5_MAX_ENTITIES", "2")
    monkeypatch.setenv("LIVE5_METRIC_TARGET", "replay_richness")
    monkeypatch.setenv("LIVE5_PERSISTENCE_TARGET", "replay_richness_wave0_shadow")
    monkeypatch.setenv("LIVE5_APPEND_ONLY_CONFIRMATION", "true")
    monkeypatch.setenv("LIVE5_ROLLBACK_CONFIRMATION", "true")
    monkeypatch.setenv("LIVE5_LINEAGE_CONFIRMATION", "true")
    monkeypatch.setenv("LIVE5_SCHEMA_CONFIRMED", "true")
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake")
    rc = runner.main(supabase_client=FakeClient())
    assert rc == 0
    payload = runner.json.loads(runner.RESULT_PATH.read_text())
    assert payload["status"] != "APPROVED_EXECUTION_BLOCKED_NO_APPROVED_ADAPTER"


def test_runner_blocks_before_adapter_when_missing_credentials_or_governance(monkeypatch):
    monkeypatch.setenv("SUPABASE_URL", "")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "")
    assert runner.main(supabase_client=FakeClient()) == 1
    p = runner.json.loads(runner.RESULT_PATH.read_text())
    assert p["status"] == "APPROVED_EXECUTION_BLOCKED_MISSING_CREDENTIALS"
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "fake")
    monkeypatch.setenv("LIVE5_APPROVAL_PHRASE", "")
    assert runner.main(supabase_client=FakeClient()) == 1
    p = runner.json.loads(runner.RESULT_PATH.read_text())
    assert p["status"] == "APPROVED_EXECUTION_GOVERNANCE_FAILURE"


def test_report_sections_complete():
    text = open("reports/lr6_live5b_approved_append_only_replay_richness_adapter.md", encoding="utf-8").read().lower()
    for s in ["objective", "approved adapter design", "append-only semantics", "boundary certification", "recommendation for next step"]:
        assert s in text
