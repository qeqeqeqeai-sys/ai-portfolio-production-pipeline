import json
import subprocess
import sys
from pathlib import Path

import pytest

from transmission_layers.history_read_model.fact_emitter import OBSERVATION_FACTS_TABLE, ObservationFactEmissionError
from transmission_layers.live_ops import ops_live2_observation_fact_accumulation as mod
from transmission_layers.live_ops.ops_live2_observation_fact_accumulation import (
    MAX_LOCAL_INPUT_ROWS,
    build_ops_live2_context,
    build_ops_live2_fact_rows,
    build_ops_live2_observations,
    build_ops_live2_report,
    normalize_live_observation,
    run_ops_live2_accumulation,
)


class FakeInsert:
    def __init__(self, table):
        self.table = table

    def execute(self):
        self.table.calls.append(("execute", None))
        return {"ok": True}


class FakeTable:
    def __init__(self, client, name):
        self.client = client
        self.name = name
        self.calls = []

    def insert(self, rows):
        self.calls.append(("insert", rows))
        self.client.inserted.append((self.name, rows))
        return FakeInsert(self)

    def upsert(self, rows, **kwargs):
        self.calls.append(("upsert", rows, kwargs))
        self.client.upserted.append((self.name, rows, kwargs))
        return FakeInsert(self)

    def update(self, rows):  # pragma: no cover
        raise AssertionError("update must not be used")

    def delete(self):  # pragma: no cover
        raise AssertionError("delete must not be used")


class FakeClient:
    def __init__(self):
        self.tables = []
        self.inserted = []
        self.upserted = []

    def table(self, name):
        table = FakeTable(self, name)
        self.tables.append(table)
        return table

    def rpc(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("provider/API calls must not be used")

    def storage(self):  # pragma: no cover
        raise AssertionError("artifact/live storage paths must not be used")


class FkCheckingTable(FakeTable):
    def _record_fk_state(self, rows):
        if self.name == mod.RUN_REGISTRY_TABLE:
            assert rows[0]["artifact_id"] in self.client.artifacts
            self.client.runs.add(rows[0]["run_id"])
        elif self.name == OBSERVATION_FACTS_TABLE:
            for row in rows:
                assert row["artifact_id"] in self.client.artifacts
                assert row["run_id"] in self.client.runs
        elif self.name == mod.ARTIFACT_REGISTRY_TABLE:
            self.client.artifacts.add(rows[0]["artifact_id"])

    def insert(self, rows):
        self._record_fk_state(rows)
        return super().insert(rows)

    def upsert(self, rows, **kwargs):
        self._record_fk_state(rows)
        return super().upsert(rows, **kwargs)


class FkCheckingClient(FakeClient):
    def __init__(self):
        super().__init__()
        self.artifacts = set()
        self.runs = set()

    def table(self, name):
        table = FkCheckingTable(self, name)
        self.tables.append(table)
        return table


BASE = {
    "observed_at": "2026-05-29T00:00:00Z",
    "source_phase": "OPS-LIVE-1B",
    "source_run_id": "run-1",
    "entity_type": "symbol",
    "entity_id": "aapl",
    "metric_name": " Live_Replay_Density ",
    "metric_value": 0.25,
    "window_days": 1,
    "payload_jsonb": {"b": 2, "a": 1},
}


def test_deterministic_context_construction():
    observations = build_ops_live2_observations([BASE])
    first = build_ops_live2_context(observations, enabled=True, dry_run=True)
    second = build_ops_live2_context(observations, enabled=True, dry_run=True)

    assert first == second
    assert first["enabled"] is True
    assert first["dry_run"] is True
    assert first["phase_id"] == "OPS-LIVE-2"
    assert first["artifact_id"].startswith("ops-live2-local-bounded-payload-")


def test_deterministic_normalization():
    row = normalize_live_observation(BASE)
    repeat = normalize_live_observation(dict(BASE, payload_jsonb={"a": 1, "b": 2}))

    assert row == repeat
    assert row["entity_type"] == "symbol"
    assert row["entity_id"] == "AAPL"
    assert row["metric_name"] == "live_replay_density"
    assert list(row["payload_jsonb"].keys()) == sorted(row["payload_jsonb"].keys())
    assert row["payload_jsonb"]["source_phase"] == "OPS-LIVE-1B"


@pytest.mark.parametrize("field", ["observed_at", "source_phase", "source_run_id", "entity_type", "entity_id", "metric_name", "metric_value"])
def test_required_field_fail_closed_behavior(field):
    payload = dict(BASE)
    payload.pop(field)

    with pytest.raises(ObservationFactEmissionError, match=f"{field} is required"):
        normalize_live_observation(payload)


def test_bounded_local_input_handling(tmp_path):
    script = Path("scripts/run_ops_live2_observation_fact_accumulation.py")
    oversized = [dict(BASE, entity_id=f"sym{i}") for i in range(MAX_LOCAL_INPUT_ROWS + 5)]
    source = tmp_path / "input.json"
    report = tmp_path / "report.md"
    source.write_text(json.dumps({"observations": oversized}), encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(script), "--input-json", str(source), "--report-path", str(report), "--enable-emission"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert f"normalized_observations={MAX_LOCAL_INPUT_ROWS}" in completed.stdout
    assert f"fact_rows={MAX_LOCAL_INPUT_ROWS}" in completed.stdout
    assert "Truncated: True" in report.read_text(encoding="utf-8")


def test_db2_fact_row_generation():
    rows = build_ops_live2_fact_rows([BASE], enabled=True, dry_run=True, artifact_id="artifact", run_id="run")

    assert len(rows) == 1
    assert rows[0]["phase_id"] == "OPS-LIVE-2"
    assert rows[0]["entity_id"] == "AAPL"
    assert rows[0]["metric_name"] == "live_replay_density"
    assert rows[0]["payload_jsonb"]["observed_at"] == "2026-05-29T00:00:00Z"


def test_dry_run_default_and_no_db_write_unless_explicit():
    client = FakeClient()
    result = run_ops_live2_accumulation(live_observations=[BASE], client=client)

    assert result["context"]["enabled"] is False
    assert result["context"]["dry_run"] is True
    assert result["fact_rows"] == []
    assert result["fact_emission"]["inserted_rows"] == 0
    assert client.tables == []


def test_enabled_dry_run_builds_rows_without_write():
    client = FakeClient()
    result = run_ops_live2_accumulation(live_observations=[BASE], client=client, enabled=True, dry_run=True)

    assert len(result["fact_rows"]) == 1
    assert result["fact_emission"]["attempted_rows"] == 1
    assert result["fact_emission"]["inserted_rows"] == 0
    assert client.tables == []


def test_injected_client_write_path_uses_idempotent_upserts_through_db2():
    client = FakeClient()
    result = run_ops_live2_accumulation(live_observations=[BASE], client=client, enabled=True, dry_run=False)

    assert result["registry_emission"]["inserted_rows"] == 2
    assert result["fact_emission"]["dry_run"] is False
    assert result["fact_emission"]["inserted_rows"] == 1
    assert [table for table, _rows, _kwargs in client.upserted] == [
        mod.ARTIFACT_REGISTRY_TABLE,
        mod.RUN_REGISTRY_TABLE,
        OBSERVATION_FACTS_TABLE,
    ]
    assert client.tables[0].calls == [("upsert", [result["artifact_registry_row"]], {"on_conflict": "artifact_id", "ignore_duplicates": True}), ("execute", None)]
    assert client.tables[1].calls == [("upsert", [result["run_registry_row"]], {"on_conflict": "run_id", "ignore_duplicates": True}), ("execute", None)]
    assert client.tables[2].calls == [("upsert", result["fact_rows"], {"on_conflict": "duplicate_prevention_key", "ignore_duplicates": True}), ("execute", None)]


def test_fk_safe_persistence_succeeds_after_parent_registration():
    client = FkCheckingClient()
    result = run_ops_live2_accumulation(live_observations=[BASE], client=client, enabled=True, dry_run=False)

    assert result["artifact_registry_row"]["artifact_id"] in client.artifacts
    assert result["run_registry_row"]["run_id"] in client.runs
    assert result["fact_emission"]["inserted_rows"] == 1


def test_repeated_same_snapshot_write_path_is_idempotent():
    client = FkCheckingClient()

    first = run_ops_live2_accumulation(live_observations=[BASE], client=client, enabled=True, dry_run=False)
    second = run_ops_live2_accumulation(live_observations=[BASE], client=client, enabled=True, dry_run=False)

    assert first["context"] == second["context"]
    assert first["artifact_registry_row"]["artifact_id"] == second["artifact_registry_row"]["artifact_id"]
    assert first["run_registry_row"]["run_id"] == second["run_registry_row"]["run_id"]
    assert first["registry_emission"]["conflict_strategy"] == "ignore_primary_key_conflicts"
    assert second["fact_emission"]["conflict_strategy"] == "ignore_duplicate_prevention_key"
    assert len(client.upserted) == 6


def test_duplicate_parent_registration_keys_remain_deterministic():
    observations = build_ops_live2_observations([BASE])
    context = build_ops_live2_context(observations, enabled=True, dry_run=False)
    loaded_at = "2026-05-29T00:00:00Z"
    first_artifact = mod.build_ops_live2_artifact_registry_row(context, observations, loaded_at=loaded_at)
    second_artifact = mod.build_ops_live2_artifact_registry_row(context, observations, loaded_at=loaded_at)
    first_run = mod.build_ops_live2_run_registry_row(context, loaded_at=loaded_at)
    second_run = mod.build_ops_live2_run_registry_row(context, loaded_at=loaded_at)

    assert first_artifact == second_artifact
    assert first_run == second_run
    assert first_artifact["duplicate_prevention_key"] == second_artifact["duplicate_prevention_key"]
    assert first_run["duplicate_prevention_key"] == second_run["duplicate_prevention_key"]


def test_no_provider_api_fmp_prediction_trading_replay_topology_paths(monkeypatch):
    result = run_ops_live2_accumulation(live_observations=[BASE], enabled=True, dry_run=True)
    governance = result["report_model"]["governance_review"]

    assert governance["provider_api_calls_enabled"] is False
    assert governance["fmp_calls_enabled"] is False
    assert governance["prediction_enabled"] is False
    assert governance["trading_execution_enabled"] is False
    assert governance["replay_execution_enabled"] is False
    assert governance["topology_persistence_enabled"] is False


def test_report_generation():
    result = run_ops_live2_accumulation(live_observations=[BASE], enabled=True, dry_run=True, input_source="unit")
    report = build_ops_live2_report(result)

    assert "OPS-LIVE-2 Controlled Live Observation Fact Accumulation" in report
    assert "## Governance Review" in report
    assert "live_replay_density" in report
    assert "Source: unit" in report


def test_payload_jsonb_boundedness():
    payload = dict(BASE, payload_jsonb={"blob": "x" * 9000})

    with pytest.raises(ObservationFactEmissionError, match="bounded metadata limit"):
        normalize_live_observation(payload)
