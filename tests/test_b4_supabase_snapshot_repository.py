from transmission_layers.expectation_failure.real_data import (
    assemble_b3_certified_snapshot_from_b2_candidate,
    build_b2_controlled_ingestion_adapter,
    build_snapshot_persistence_record,
    persist_certified_market_snapshot,
)


class _Exec:
    def __init__(self, collector, table):
        self.collector = collector
        self.table = table

    def execute(self):
        self.collector.append(self.table)
        return {"ok": True}


class FakeClient:
    def __init__(self, should_fail=False):
        self.calls = []
        self.should_fail = should_fail

    def table(self, name):
        self._name = name
        return self

    def upsert(self, payload, on_conflict=None):
        if self.should_fail:
            raise RuntimeError("db down")
        self.calls.append((self._name, payload, on_conflict))
        return _Exec([], self._name)


def _envelope():
    raw = [{"symbol": "NVDA", "metric_name": "price", "metric_value": 99, "source": "x", "source_timestamp": "2026-05-20", "currency": "USD"}]
    candidate = build_b2_controlled_ingestion_adapter(raw, "2026-05-21")["candidate"]
    env = assemble_b3_certified_snapshot_from_b2_candidate(candidate)
    env["b3_decision"] = "CERTIFIED_SNAPSHOT_READY"
    return env


def test_b4_repository_persists_with_injected_client_and_idempotent_record():
    env = _envelope()
    r1 = build_snapshot_persistence_record(env)
    r2 = build_snapshot_persistence_record(env)
    assert r1 == r2
    client = FakeClient()
    out = persist_certified_market_snapshot(client, env, table_names={"audit": "custom_audit"})
    assert out["persistence_status"] == "PERSISTED_CERTIFIED_SNAPSHOT"
    assert "custom_audit" in out["written_tables"]
    assert len(client.calls) == 3


def test_b4_repository_blocks_repository_errors_deterministically():
    out = persist_certified_market_snapshot(FakeClient(should_fail=True), _envelope())
    assert out["persistence_status"] == "BLOCKED_REPOSITORY_ERROR"
    assert out["blocked_reason"] == "repository_error:RuntimeError"
