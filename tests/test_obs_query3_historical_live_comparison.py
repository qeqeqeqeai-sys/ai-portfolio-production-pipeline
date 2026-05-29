from __future__ import annotations

import copy
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from transmission_layers.history_read_model.historical_live_comparison import (
    HARD_LIMIT,
    compare_historical_live_state,
    get_historically_weak_structures_strengthening_live,
    get_live_anomalies_vs_historical,
    get_live_baseline_deviations,
    get_live_recurring_historical_patterns,
    get_persistent_structures_weakening_live,
    write_historical_live_comparison_outputs,
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
        raise AssertionError("OBS-QUERY-3 retrieval must not write")

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
    identifier: str,
    metric_value: float | str | None,
    phase_id: str,
    metric_name: str = "persistence_score",
    loaded_at: str = "2026-05-01T00:00:00Z",
) -> dict[str, Any]:
    return {
        "id": fact_id,
        "phase_id": phase_id,
        "phase_name": phase_id.lower(),
        "window_days": 30,
        "entity_type": "phase",
        "entity_id": f"{phase_id}:{identifier}",
        "metric_name": metric_name,
        "metric_value": metric_value,
        "artifact_id": f"artifact-{fact_id}",
        "run_id": f"run-{fact_id}",
        "created_at": loaded_at,
        "loaded_at": loaded_at,
        "payload_jsonb": {"evidence_id": f"ev-{fact_id}", "identifier": identifier},
        "duplicate_prevention_key": f"dup-{fact_id}",
    }


def _rows() -> list[dict[str, Any]]:
    return [
        _fact(fact_id=1, identifier="overlap", metric_value=0.70, phase_id="HIST-INTEL-1"),
        _fact(fact_id=2, identifier="overlap", metric_value=0.80, phase_id="OPS-LIVE2"),
        _fact(fact_id=3, identifier="live_only", metric_value=0.40, phase_id="OPS-LIVE2"),
        _fact(fact_id=4, identifier="historical_only", metric_value=0.90, phase_id="HIST-INTEL-1"),
        _fact(fact_id=5, identifier="weaker", metric_value=0.95, phase_id="HIST-INTEL-1"),
        _fact(fact_id=6, identifier="weaker", metric_value=0.55, phase_id="OPS-LIVE2"),
        _fact(fact_id=7, identifier="stronger", metric_value=0.15, phase_id="HIST-INTEL-1"),
        _fact(fact_id=8, identifier="stronger", metric_value=0.65, phase_id="OPS-LIVE2"),
        _fact(fact_id=9, identifier="recurring", metric_value=0.20, phase_id="HIST-INTEL-1", loaded_at="2026-05-02T00:00:00Z"),
        _fact(fact_id=10, identifier="recurring", metric_value=0.22, phase_id="HIST-INTEL-2", loaded_at="2026-05-03T00:00:00Z"),
        _fact(fact_id=11, identifier="recurring", metric_value=0.21, phase_id="OPS-LIVE2", loaded_at="2026-05-04T00:00:00Z"),
    ]


def test_historical_live_overlap():
    result = compare_historical_live_state(comparison_type="baseline_overlap", fact_rows=_rows())
    overlap = next(item for item in result["results"] if item["identifier"] == "overlap")
    assert overlap["classification"] == "historical_and_live"
    assert overlap["historical_supporting_fact_ids"] == ["1"]
    assert overlap["live_supporting_fact_ids"] == ["2"]


def test_live_only_anomaly():
    result = get_live_anomalies_vs_historical(fact_rows=_rows())
    assert result["results"] == [
        {
            "identifier": "live_only",
            "classification": "live_only",
            "historical_metric": {"fact_count": 0, "numeric_values": [], "representative_value": None},
            "live_metric": {"fact_count": 1, "numeric_values": [0.4], "representative_value": 0.4},
            "delta": None,
            "ranking_metric": {"name": "live_fact_count", "value": 1},
            "historical_supporting_fact_ids": [],
            "live_supporting_fact_ids": ["3"],
            "supporting_evidence_ids": ["ev-3"],
            "source_phases": ["OPS-LIVE2"],
        }
    ]


def test_historical_only_baseline_item():
    result = compare_historical_live_state(comparison_type="baseline_overlap", fact_rows=_rows())
    item = next(item for item in result["results"] if item["identifier"] == "historical_only")
    assert item["classification"] == "historical_only"
    assert item["historical_supporting_fact_ids"] == ["4"]
    assert item["live_supporting_fact_ids"] == []


def test_live_weaker_than_historical():
    result = get_persistent_structures_weakening_live(fact_rows=_rows())
    assert result["results"][0]["identifier"] == "weaker"
    assert result["results"][0]["classification"] == "live_weaker_than_historical"
    assert result["results"][0]["delta"] == -0.4


def test_live_stronger_than_historical():
    result = get_historically_weak_structures_strengthening_live(fact_rows=_rows())
    assert result["results"][0]["identifier"] == "stronger"
    assert result["results"][0]["classification"] == "live_stronger_than_historical"
    assert result["results"][0]["delta"] == 0.5


def test_baseline_deviation():
    result = get_live_baseline_deviations(fact_rows=_rows())
    identifiers = [item["identifier"] for item in result["results"]]
    assert identifiers[:2] == ["stronger", "weaker"]
    assert {item["classification"] for item in result["results"]} == {"live_deviates_from_historical"}


def test_recurring_historical_pattern():
    result = get_live_recurring_historical_patterns(fact_rows=_rows())
    item = next(item for item in result["results"] if item["identifier"] == "recurring")
    assert item["classification"] == "recurring_historical_pattern"
    assert item["ranking_metric"] == {"name": "historical_live_recurrence_count", "value": 3}
    assert item["historical_supporting_fact_ids"] == ["10", "9"]
    assert item["live_supporting_fact_ids"] == ["11"]


def test_deterministic_ordering():
    first = compare_historical_live_state(comparison_type="baseline_deviation", fact_rows=_rows())
    second = compare_historical_live_state(comparison_type="baseline_deviation", fact_rows=list(reversed(_rows())))
    assert first == second


def test_bounded_limits():
    rows = []
    for i in range(700):
        rows.append(_fact(fact_id=i, identifier=f"id-{i:04d}", metric_value=0.1, phase_id="HIST-INTEL-1"))
        rows.append(_fact(fact_id=1000 + i, identifier=f"id-{i:04d}", metric_value=0.2, phase_id="OPS-LIVE2"))
    result = compare_historical_live_state(comparison_type="baseline_deviation", fact_rows=rows, limit=9999)
    assert result["effective_limit"] == HARD_LIMIT
    assert result["result_count"] == HARD_LIMIT


def test_empty_result_handling():
    result = compare_historical_live_state(comparison_type="baseline_overlap", fact_rows=[])
    assert result["result_count"] == 0
    assert result["results"] == []
    assert result["historical_fact_ids"] == []
    assert result["live_fact_ids"] == []
    assert result["supporting_evidence_ids"] == []


def test_evidence_traceability():
    result = get_live_recurring_historical_patterns(fact_rows=_rows())
    item = next(item for item in result["results"] if item["identifier"] == "recurring")
    assert item["supporting_evidence_ids"] == ["ev-10", "ev-11", "ev-9"]
    assert set(result["historical_fact_ids"]) >= {"9", "10"}
    assert set(result["live_fact_ids"]) >= {"11"}
    assert set(result["supporting_evidence_ids"]) >= {"ev-9", "ev-10", "ev-11"}


def test_no_db_writes_with_client():
    client = _ReadOnlyClient(_rows())
    result = compare_historical_live_state(comparison_type="baseline_overlap", client=client, historical_source_layer="HIST-INTEL-1", live_source_layer="OPS-LIVE2")
    methods = [name for name, _ in client.calls]
    assert result["result_count"] > 0
    assert "execute" in methods
    assert not ({"insert", "upsert", "update", "delete"} & set(methods))
    assert result["governance_certification"]["db_writes_enabled"] is False


def test_no_provider_calls_governance():
    result = compare_historical_live_state(comparison_type="baseline_overlap", fact_rows=_rows())
    assert result["governance_certification"]["provider_api_calls_enabled"] is False
    assert result["governance_certification"]["no_new_intelligence_generation"] is True
    assert result["governance_certification"]["source_of_truth"] == "sefi_observation_facts"


def test_output_json_markdown_generation(tmp_path: Path):
    result = get_live_recurring_historical_patterns(fact_rows=_rows())
    output_json = tmp_path / "obs_query3.json"
    output_md = tmp_path / "obs_query3.md"
    paths = write_historical_live_comparison_outputs(result, output_json=output_json, output_md=output_md)
    assert paths == {"output_json": str(output_json), "output_md": str(output_md)}
    payload = json.loads(output_json.read_text(encoding="utf-8"))
    markdown = output_md.read_text(encoding="utf-8")
    assert payload["schema_version"] == "obs_query3_historical_live_comparison_v1"
    assert "## Query summary" in markdown
    assert "## Comparison results table" in markdown
    assert "## Historical supporting facts" in markdown
    assert "## Live supporting facts" in markdown
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
            "scripts/run_obs_query3_historical_live_comparison.py",
            "--comparison-type",
            "historical_recurrence",
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
    assert summary["comparison_type"] == "historical_recurrence"
    assert summary["result_count"] == 2
    assert json.loads(output_json.read_text(encoding="utf-8"))["result_count"] == 2
    assert "OBS-QUERY-3" in output_md.read_text(encoding="utf-8")
