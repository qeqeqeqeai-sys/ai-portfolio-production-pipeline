from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from transmission_layers.history_read_model.observation_intelligence_query import (
    HARD_LIMIT,
    get_changed_structures,
    get_dominant_structures,
    get_persistent_structures,
    get_recurrent_structures,
    get_transitioning_structures,
    get_weakening_structures,
    retrieve_intelligence_question,
    write_intelligence_question_outputs,
)


class _Result:
    def __init__(self, data: list[dict[str, Any]]):
        self.data = data


class _ReadOnlyQuery:
    def __init__(self, rows: list[dict[str, Any]], calls: list[tuple[str, Any]]):
        self.rows = rows
        self.calls = calls
        self.filters: list[tuple[str, Any]] = []
        self.orders: list[tuple[str, bool]] = []
        self._limit: int | None = None

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
        raise AssertionError("OBS-QUERY-2 retrieval must not write")

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
    entity_id: str,
    metric_name: str,
    metric_value: float | str | None,
    phase_id: str = "HIST-INTEL-4",
    loaded_at: str = "2026-05-01T00:00:00Z",
    window_days: int = 30,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "phase_id": phase_id,
        "phase_name": phase_id.lower(),
        "window_days": window_days,
        "entity_type": "symbol" if entity_id in {"NVDA", "MSFT"} else "phase",
        "entity_id": entity_id,
        "metric_name": metric_name,
        "metric_value": metric_value,
        "artifact_id": f"artifact-{fact_id}",
        "run_id": f"run-{fact_id}",
        "created_at": loaded_at,
        "loaded_at": loaded_at,
        "payload_jsonb": {"evidence_id": f"ev-{fact_id}", **(payload or {})},
        "duplicate_prevention_key": f"dup-{fact_id}",
    }


def _rows() -> list[dict[str, Any]]:
    return [
        _fact(fact_id=3, entity_id="HIST-LONG-8:alpha", metric_name="persistence_score", metric_value=0.92, loaded_at="2026-05-03T00:00:00Z", payload={"dimension": "alpha", "stability_class": "STABLE"}),
        _fact(fact_id=1, entity_id="HIST-LONG-8:beta", metric_name="persistence_score", metric_value=0.96, loaded_at="2026-05-01T00:00:00Z", payload={"dimension": "beta", "stability_class": "STABLE"}),
        _fact(fact_id=2, entity_id="HIST-LONG-9:replay", metric_name="replay_stability_drift", metric_value=-0.07, phase_id="HIST-LONG-9", loaded_at="2026-05-02T00:00:00Z", payload={"dimension": "replay", "drift_class": "DETERIORATING", "stability_class_transition": "STABLE->PARTIALLY_STABLE"}),
        _fact(fact_id=4, entity_id="HIST-INTEL-2:sector", metric_name="sector_hhi", metric_value=0.44, phase_id="HIST-INTEL-2", loaded_at="2026-05-04T00:00:00Z", payload={"dimension": "technology", "dominance_score": 0.44}),
        _fact(fact_id=5, entity_id="HIST-INTEL-3:morphology", metric_name="morphology_recurrence", metric_value=2, phase_id="HIST-INTEL-3", loaded_at="2026-05-05T00:00:00Z", payload={"recurring_structures": ["technology", "ai_supply_chain"]}),
        _fact(fact_id=6, entity_id="HIST-INTEL-3:morphology", metric_name="morphology_recurrence", metric_value=1, phase_id="HIST-INTEL-3", loaded_at="2026-05-06T00:00:00Z", payload={"recurring_structures": ["technology"]}),
        _fact(fact_id=7, entity_id="HIST-LONG-9:liquidity", metric_name="liquidity_weakening", metric_value=-0.12, phase_id="HIST-LONG-9", loaded_at="2026-05-07T00:00:00Z", payload={"dimension": "liquidity", "drift_class": "WEAKENING"}),
        _fact(fact_id=8, entity_id="NVDA", metric_name="symbol_persistence", metric_value=0.81, loaded_at="2026-05-08T00:00:00Z", payload={"symbol": "NVDA", "dimension": "NVDA"}),
    ]


def test_persisted_retrieval():
    result = get_persistent_structures(fact_rows=_rows(), limit=3)
    assert result["query_type"] == "persisted"
    assert [item["identifier"] for item in result["results"]][:2] == ["beta", "alpha"]
    assert result["results"][0]["ranking_metric"] == {"name": "persistence_score", "value": 0.96}


def test_changed_retrieval():
    result = get_changed_structures(fact_rows=_rows())
    assert result["query_type"] == "changed"
    assert result["results"][0]["identifier"] == "replay"
    assert "2" in result["supporting_fact_ids"]


def test_recurrent_retrieval():
    result = get_recurrent_structures(fact_rows=_rows())
    assert result["results"][0]["identifier"] == "technology"
    assert result["results"][0]["ranking_metric"]["value"] == 2


def test_dominant_retrieval():
    result = get_dominant_structures(fact_rows=_rows())
    assert result["results"] == [
        {
            "identifier": "technology",
            "ranking_metric": {"name": "dominance_score", "value": 0.44},
            "supporting_fact_count": 1,
            "supporting_fact_ids": ["4"],
            "supporting_evidence_ids": ["ev-4"],
            "supporting_evidence": [{"fact_id": "4", "evidence_id": "ev-4", "artifact_id": "artifact-4", "run_id": "run-4", "source_phase": "HIST-INTEL-2"}],
            "source_phases": ["HIST-INTEL-2"],
        }
    ]


def test_weakened_retrieval():
    result = get_weakening_structures(fact_rows=_rows())
    assert result["results"][0]["identifier"] == "liquidity"
    assert result["results"][0]["ranking_metric"]["value"] == 0.12


def test_transitioned_retrieval():
    result = get_transitioning_structures(fact_rows=_rows())
    assert result["results"][0]["identifier"] == "STABLE->PARTIALLY_STABLE"
    assert result["results"][0]["supporting_fact_ids"] == ["2"]


def test_deterministic_ordering():
    first = get_persistent_structures(fact_rows=_rows())
    second = get_persistent_structures(fact_rows=list(reversed(_rows())))
    assert first == second


def test_bounded_limits():
    result = get_persistent_structures(fact_rows=[_fact(fact_id=i, entity_id=f"s:{i:04d}", metric_name="persistence_score", metric_value=1 / (i + 1)) for i in range(700)], limit=9999)
    assert result["effective_limit"] == HARD_LIMIT
    assert result["result_count"] == HARD_LIMIT


def test_empty_result_handling():
    result = get_dominant_structures(fact_rows=[], symbol="NVDA")
    assert result["result_count"] == 0
    assert result["results"] == []
    assert result["supporting_fact_ids"] == []
    assert result["supporting_evidence_ids"] == []


def test_evidence_traceability():
    result = get_recurrent_structures(fact_rows=_rows())
    item = result["results"][0]
    assert item["identifier"] == "technology"
    assert item["supporting_fact_ids"] == ["5", "6"]
    assert item["supporting_evidence_ids"] == ["ev-5", "ev-6"]
    assert set(result["supporting_fact_ids"]) >= {"5", "6"}
    assert set(result["supporting_evidence_ids"]) >= {"ev-5", "ev-6"}


def test_no_db_writes_with_client():
    client = _ReadOnlyClient(_rows())
    result = retrieve_intelligence_question(query_type="persisted", client=client, source_layer="HIST-INTEL-4")
    methods = [name for name, _ in client.calls]
    assert result["result_count"] == 3
    assert "execute" in methods
    assert not ({"insert", "upsert", "update", "delete"} & set(methods))
    assert result["governance_certification"]["db_writes_enabled"] is False


def test_no_provider_calls_governance():
    result = get_changed_structures(fact_rows=_rows())
    assert result["governance_certification"]["provider_api_calls_enabled"] is False
    assert result["governance_certification"]["no_new_intelligence_generation"] is True
    assert result["governance_certification"]["source_of_truth"] == "sefi_observation_facts"


def test_output_generation(tmp_path: Path):
    result = get_recurrent_structures(fact_rows=_rows())
    output_json = tmp_path / "obs_query2.json"
    output_md = tmp_path / "obs_query2.md"
    paths = write_intelligence_question_outputs(result, output_json=output_json, output_md=output_md)
    assert paths == {"output_json": str(output_json), "output_md": str(output_md)}
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert payload["query_type"] == "recurred"
    assert "## Query summary" in markdown
    assert "## Results table" in markdown
    assert "## Supporting facts" in markdown
    assert "## Supporting evidence" in markdown
    assert "## Governance certification" in markdown


def test_cli_execution(tmp_path: Path):
    local_rows = tmp_path / "facts.json"
    output_json = tmp_path / "cli.json"
    output_md = tmp_path / "cli.md"
    local_rows.write_text(json.dumps(_rows()), encoding="utf-8")
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/run_obs_query2_intelligence_query.py",
            "--query-type",
            "persisted",
            "--local-facts-json",
            str(local_rows),
            "--limit",
            "2",
            "--output-json",
            str(output_json),
            "--output-md",
            str(output_md),
        ],
        check=True,
        text=True,
        capture_output=True,
    )
    summary = json.loads(completed.stdout)
    assert summary["status"] == "ok"
    assert summary["result_count"] == 2
    assert json.loads(output_json.read_text(encoding="utf-8"))["result_count"] == 2
    assert "OBS-QUERY-2" in output_md.read_text(encoding="utf-8")
