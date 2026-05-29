from __future__ import annotations

import copy
import subprocess
import sys
from pathlib import Path
from typing import Any

from transmission_layers.history_read_model.observation_fact_retrieval import (
    HARD_LIMIT,
    retrieve_observation_facts,
    write_observation_fact_retrieval_outputs,
)


class _Result:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class _ReadOnlyQuery:
    def __init__(self, rows: list[dict[str, Any]], calls: list[tuple[str, Any]]):
        self.rows = rows
        self.calls = calls
        self.filters: list[tuple[str, Any]] = []
        self._limit: int | None = None
        self.orders: list[tuple[str, bool]] = []

    def select(self, columns: str):
        self.calls.append(("select", columns))
        return self

    def eq(self, key: str, value: Any):
        self.calls.append(("eq", (key, value)))
        self.filters.append((key, value))
        return self

    def order(self, key: str, desc: bool = False):
        self.calls.append(("order", (key, desc)))
        self.orders.append((key, desc))
        return self

    def limit(self, value: int):
        self.calls.append(("limit", value))
        self._limit = value
        return self

    def execute(self):
        self.calls.append(("execute", None))
        rows = [row for row in self.rows if all(row.get(key) == value for key, value in self.filters)]
        for key, desc in reversed(self.orders):
            rows = sorted(rows, key=lambda row: str(row.get(key) or ""), reverse=desc)
        if self._limit is not None:
            rows = rows[: self._limit]
        return _Result(rows)

    def insert(self, *_args: Any, **_kwargs: Any):  # pragma: no cover
        raise AssertionError("OBS-QUERY-1 retrieval must not write")

    upsert = update = delete = insert


class _ReadOnlyClient:
    def __init__(self, rows: list[dict[str, Any]]):
        self.rows = rows
        self.calls: list[tuple[str, Any]] = []

    def table(self, name: str):
        self.calls.append(("table", name))
        assert name == "sefi_observation_facts"
        return _ReadOnlyQuery(copy.deepcopy(self.rows), self.calls)


def _fact(
    *,
    fact_id: int,
    entity_type: str = "symbol",
    entity_id: str = "NVDA",
    metric_name: str = "replay_density",
    metric_value: float | None = 0.9,
    phase_id: str = "HIST-INTEL-4",
    loaded_at: str = "2026-05-01T00:00:00Z",
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "phase_id": phase_id,
        "phase_name": phase_id.lower(),
        "window_days": 30,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "artifact_id": f"artifact-{fact_id}",
        "run_id": f"run-{fact_id}",
        "created_at": loaded_at,
        "loaded_at": loaded_at,
        "payload_jsonb": payload or {},
        "duplicate_prevention_key": f"dup-{fact_id}",
    }


def _rows() -> list[dict[str, Any]]:
    return [
        _fact(fact_id=3, entity_id="MSFT", metric_name="stability", loaded_at="2026-05-03T00:00:00Z"),
        _fact(fact_id=1, entity_id="NVDA", metric_name="replay_density", loaded_at="2026-05-01T00:00:00Z", payload={"evidence_id": "ev-1"}),
        _fact(fact_id=2, entity_id="NVDA", metric_name="taxonomy_a", loaded_at="2026-05-02T00:00:00Z", payload={"symbol": "NVDA"}),
    ]


def test_bounded_limit_enforcement():
    result = retrieve_observation_facts(fact_rows=[_fact(fact_id=i) for i in range(600)], limit=9999)
    assert result["hard_limit"] == HARD_LIMIT
    assert result["effective_limit"] == HARD_LIMIT
    assert result["row_count"] == HARD_LIMIT


def test_unsupported_filter_handling():
    result = retrieve_observation_facts(fact_rows=_rows(), sector="Technology", subsector="Semiconductors", min_confidence=0.8)
    assert [item["filter"] for item in result["unsupported_filters"]] == ["sector", "subsector", "min_confidence"]
    assert result["governance_certification"]["retrieval_only"] is True


def test_deterministic_ordering():
    first = retrieve_observation_facts(fact_rows=_rows())
    second = retrieve_observation_facts(fact_rows=list(reversed(_rows())))
    assert [fact["fact_id"] for fact in first["facts"]] == ["1", "2", "3"]
    assert first == second


def test_empty_result_handling():
    result = retrieve_observation_facts(fact_rows=[], symbol="NVDA")
    assert result["row_count"] == 0
    assert result["facts"] == []
    assert result["evidence_references"] == []


def test_symbol_filter():
    result = retrieve_observation_facts(fact_rows=_rows(), symbol="NVDA")
    assert result["row_count"] == 2
    assert {fact["entity_id"] for fact in result["facts"]} == {"NVDA"}


def test_taxonomy_category_filter():
    result = retrieve_observation_facts(fact_rows=_rows(), taxonomy="taxonomy_a")
    assert result["row_count"] == 1
    assert result["facts"][0]["taxonomy"] == "taxonomy_a"


def test_evidence_or_fact_id_filter():
    by_fact_id = retrieve_observation_facts(fact_rows=_rows(), evidence_id="2")
    by_payload_evidence = retrieve_observation_facts(fact_rows=_rows(), evidence_id="ev-1")
    assert [fact["fact_id"] for fact in by_fact_id["facts"]] == ["2"]
    assert [fact["evidence_id"] for fact in by_payload_evidence["facts"]] == ["ev-1"]


def test_no_external_provider_calls_and_no_writes_with_client():
    client = _ReadOnlyClient(_rows())
    result = retrieve_observation_facts(client=client, symbol="NVDA", taxonomy="taxonomy_a", limit=10)
    methods = [name for name, _ in client.calls]
    assert result["row_count"] == 1
    assert "execute" in methods
    assert not ({"insert", "upsert", "update", "delete"} & set(methods))
    assert result["governance_certification"]["provider_api_calls_enabled"] is False
    assert result["governance_certification"]["db_writes_enabled"] is False


def test_output_json_and_markdown_creation(tmp_path: Path):
    result = retrieve_observation_facts(fact_rows=_rows(), symbol="NVDA", limit=2)
    output_json = tmp_path / "obs_query1.json"
    output_md = tmp_path / "obs_query1.md"
    paths = write_observation_fact_retrieval_outputs(result, output_json=output_json, output_md=output_md)
    assert paths["output_json"] == str(output_json)
    assert paths["output_md"] == str(output_md)
    assert '"query_parameters"' in output_json.read_text(encoding="utf-8")
    md = output_md.read_text(encoding="utf-8")
    assert "## Query summary" in md
    assert "## Governance certification" in md


def test_cli_creates_outputs_without_supabase_env(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    monkeypatch.delenv("SUPABASE_SERVICE_ROLE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_KEY", raising=False)
    monkeypatch.delenv("SUPABASE_ANON_KEY", raising=False)
    output_json = tmp_path / "cli.json"
    output_md = tmp_path / "cli.md"
    proc = subprocess.run(
        [
            sys.executable,
            "scripts/run_obs_query1_fact_retrieval.py",
            "--limit",
            "10",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    assert '"status": "ok"' in proc.stdout
    assert output_json.exists()
    assert output_md.exists()
