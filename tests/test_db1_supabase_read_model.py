from __future__ import annotations

import json
from pathlib import Path

import pytest

from transmission_layers.history_read_model.loader import (
    ArtifactLoadError,
    MAX_PAYLOAD_BYTES,
    build_read_model_rows,
    build_rows_from_artifact,
    deterministic_duplicate_key,
)
from transmission_layers.history_read_model.queries import (
    get_latest_completed_phase,
    get_observation_facts,
    get_phase_run_summary,
    get_sector_morphology,
    get_symbol_metrics,
    get_window_metrics,
)


FIXED_LOADED_AT = "2026-05-29T00:00:00+00:00"


def _artifact(**overrides):
    payload = {
        "status": "ok",
        "schema_version": "fixture_v1",
        "review_date": "2026-05-29",
        "governance_certification": {
            "phase": "HIST-LONG-FIXTURE",
            "governance_mode": "observational_only",
            "local_artifacts_only": True,
            "prediction_enabled": False,
            "trading_execution_enabled": False,
            "replay_activation_enabled": False,
            "replay_execution_enabled": False,
            "topology_persistence_enabled": False,
            "supabase_write_enabled": False,
            "fmp_calls_enabled": False,
            "provider_api_calls_enabled": False,
        },
        "window_level_results": [
            {
                "window_trading_days": 20,
                "completeness": 1.0,
                "replay_density": 0.2,
                "replay_saturation": 0.3,
                "contradiction_burden": 0.0,
                "sector_hhi": {"hhi": 0.12},
                "subsector_hhi": {"hhi": 0.13},
                "effective_symbol_count": 2,
                "weak_symbols": ["ABC"],
                "source_mode": "fixture_local",
            }
        ],
        "findings": {
            "strongest_differentiated_sectors": [
                {"sector": "semiconductors", "symbol_count": 2, "symbol_share": 0.5}
            ]
        },
        "baseline_summary": {"primary_window": 20, "note": "bounded"},
    }
    payload.update(overrides)
    return payload


def _write_json(path: Path, payload: dict) -> Path:
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return path


class FakeResult:
    data = [{"ok": True}]


class FakeQuery:
    def __init__(self, table_name, calls):
        self.table_name = table_name
        self.calls = calls

    def select(self, *args, **kwargs):
        self.calls.append(("select", args, kwargs))
        return self

    def eq(self, *args, **kwargs):
        self.calls.append(("eq", args, kwargs))
        return self

    def ilike(self, *args, **kwargs):
        self.calls.append(("ilike", args, kwargs))
        return self

    def in_(self, *args, **kwargs):
        self.calls.append(("in_", args, kwargs))
        return self

    def order(self, *args, **kwargs):
        self.calls.append(("order", args, kwargs))
        return self

    def limit(self, *args, **kwargs):
        self.calls.append(("limit", args, kwargs))
        return self

    def insert(self, *args, **kwargs):  # pragma: no cover - should never be used by query helpers
        raise AssertionError("query helpers must be read-only")

    def update(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("query helpers must be read-only")

    def delete(self, *args, **kwargs):  # pragma: no cover
        raise AssertionError("query helpers must be read-only")

    def execute(self):
        self.calls.append(("execute", (), {}))
        return FakeResult()


class FakeClient:
    def __init__(self):
        self.calls = []

    def table(self, name):
        self.calls.append(("table", (name,), {}))
        return FakeQuery(name, self.calls)


def test_deterministic_row_construction_and_duplicate_key_stability(tmp_path):
    path = _write_json(tmp_path / "artifact.json", _artifact())
    first = build_rows_from_artifact(path, run_id="run-a", loaded_at=FIXED_LOADED_AT)
    second = build_rows_from_artifact(path, run_id="run-a", loaded_at=FIXED_LOADED_AT)

    assert first == second
    assert first["sefi_phase_runs"][0]["duplicate_prevention_key"] == second["sefi_phase_runs"][0]["duplicate_prevention_key"]
    assert deterministic_duplicate_key("table", "a", 1) == deterministic_duplicate_key("table", "a", 1)
    artifact_id = first["sefi_artifact_registry"][0]["artifact_id"]
    assert first["sefi_phase_runs"][0]["artifact_id"] == artifact_id
    assert first["sefi_run_registry"][0]["artifact_id"] == artifact_id
    assert "source_artifact_path" not in first["sefi_window_metrics"][0]
    assert "source_artifact_sha256" not in first["sefi_sector_morphology"][0]
    assert first["sefi_window_metrics"][0]["window_days"] == 20
    assert first["sefi_sector_morphology"][0]["sector"] == "semiconductors"
    assert first["sefi_symbol_metrics"][0]["symbol"] == "ABC"
    assert any(row["metric_name"] == "completeness" for row in first["sefi_observation_facts"])


def test_loader_uses_local_artifacts_only_and_no_provider_calls(monkeypatch, tmp_path):
    def blocked_import(name, *args, **kwargs):
        assert name not in {"requests", "supabase", "fmp"}
        return original_import(name, *args, **kwargs)

    original_import = __import__
    monkeypatch.setattr("builtins.__import__", blocked_import)
    path = _write_json(tmp_path / "artifact.json", _artifact())

    rows = build_read_model_rows([path], run_id="run-local", loaded_at=FIXED_LOADED_AT)

    assert rows["sefi_phase_runs"][0]["run_id"] == rows["sefi_run_registry"][0]["run_id"]


def test_governance_boundaries_block_prediction_trading_replay_activation(tmp_path):
    payload = _artifact()
    payload["governance_certification"]["prediction_enabled"] = True
    path = _write_json(tmp_path / "bad.json", payload)

    with pytest.raises(ArtifactLoadError, match="governance boundary"):
        build_rows_from_artifact(path, loaded_at=FIXED_LOADED_AT)


@pytest.mark.parametrize("missing_key", ["status", "schema_version", "governance_certification"])
def test_missing_or_partial_artifacts_fail_closed(tmp_path, missing_key):
    payload = _artifact()
    payload.pop(missing_key)
    path = _write_json(tmp_path / "partial.json", payload)

    with pytest.raises(ArtifactLoadError):
        build_rows_from_artifact(path, loaded_at=FIXED_LOADED_AT)


def test_payload_size_is_bounded(tmp_path):
    path = _write_json(tmp_path / "artifact.json", _artifact())
    rows = build_rows_from_artifact(path, run_id="run-a", loaded_at=FIXED_LOADED_AT)

    for table_rows in rows.values():
        for row in table_rows:
            assert len(json.dumps(row["payload_jsonb"], sort_keys=True).encode("utf-8")) <= MAX_PAYLOAD_BYTES


def _table_block(schema: str, table: str) -> str:
    start = schema.index(f"create table if not exists public.{table}")
    end = schema.index("\n);", start) + 3
    return schema[start:end]


def test_schema_contains_required_columns_and_append_only_triggers():
    schema = Path("supabase/migrations/20260529000100_create_sefi_history_read_model.sql").read_text(encoding="utf-8")
    for table in [
        "sefi_artifact_registry",
        "sefi_run_registry",
        "sefi_phase_runs",
        "sefi_hist_observations",
        "sefi_window_metrics",
        "sefi_sector_morphology",
        "sefi_symbol_metrics",
        "sefi_observation_facts",
    ]:
        assert f"create table if not exists public.{table}" in schema
        assert "created_at timestamptz not null default now()" in schema
        assert "loaded_at timestamptz not null default now()" in schema
        assert "payload_jsonb jsonb not null" in schema
        assert "duplicate_prevention_key text not null unique" in schema
    artifact_block = _table_block(schema, "sefi_artifact_registry")
    assert "source_artifact_path text not null" in artifact_block
    assert "source_artifact_sha256 text not null" in artifact_block
    for table in ["sefi_phase_runs", "sefi_hist_observations", "sefi_window_metrics", "sefi_sector_morphology", "sefi_symbol_metrics", "sefi_observation_facts"]:
        block = _table_block(schema, table)
        assert "artifact_id text not null references public.sefi_artifact_registry" in block
        assert "run_id text not null references public.sefi_run_registry" in block
        assert "source_artifact_path" not in block
        assert "source_artifact_sha256" not in block
    facts_block = _table_block(schema, "sefi_observation_facts")
    for column in ["phase_id", "window_days", "entity_type", "entity_id", "metric_name", "metric_value", "artifact_id", "run_id"]:
        assert column in facts_block
    assert "before update or delete" in schema
    assert "drop table" not in schema.lower()
    assert "truncate" not in schema.lower()


def test_query_helpers_are_read_only():
    client = FakeClient()

    assert get_phase_run_summary(client, "DB-1") == [{"ok": True}]
    assert get_window_metrics(client, "DB-1", 20) == [{"ok": True}]
    assert get_sector_morphology(client, "DB-1") == [{"ok": True}]
    assert get_symbol_metrics(client, "DB-1", "abc") == [{"ok": True}]
    assert get_observation_facts(client, "DB-1", entity_type="window", window_days=20) == [{"ok": True}]
    assert get_latest_completed_phase(client, "HIST-LONG") == [{"ok": True}]

    mutating_calls = {"insert", "update", "delete", "upsert"}
    assert not any(call[0] in mutating_calls for call in client.calls)
