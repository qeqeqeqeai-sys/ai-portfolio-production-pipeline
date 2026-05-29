from __future__ import annotations

import importlib
from collections import OrderedDict

import pytest

from transmission_layers.live_ops.ops_live3_structural_state_snapshot import (
    CLASS_DEGRADED,
    CLASS_HEALTHY,
    CLASS_INSUFFICIENT,
    CLASS_WATCH,
    MAX_FACT_ROWS,
    build_ops_live3_report,
    build_ops_live3_snapshot,
    build_ops_live3_state_summary,
    run_ops_live3_snapshot,
)


LIVE_ROWS = [
    {
        "phase_id": "OPS-LIVE-2",
        "phase_name": "OPS-LIVE-2_controlled_live_observation_fact_accumulation",
        "entity_type": "phase",
        "entity_id": "OPS-LIVE-1B",
        "metric_name": "live_ingestion_completeness",
        "metric_value": 0.97,
        "run_id": "db-run-a",
        "loaded_at": "2026-05-29T00:01:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:00:00Z", "source_run_id": "source-a"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "provider",
        "entity_id": "fmp",
        "metric_name": "live_provider_health",
        "metric_value": 0.83,
        "run_id": "db-run-b",
        "loaded_at": "2026-05-29T00:02:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:02:00Z", "source_run_id": "source-b"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "symbol",
        "entity_id": "AAPL",
        "metric_name": "live_symbol_weakness",
        "metric_value": 0.2,
        "run_id": "db-run-b",
        "loaded_at": "2026-05-29T00:03:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:03:00Z", "source_run_id": "source-b"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "replay",
        "entity_id": "density",
        "metric_name": "live_replay_density",
        "metric_value": 0.31,
        "run_id": "db-run-c",
        "loaded_at": "2026-05-29T00:04:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:04:00Z", "source_run_id": "source-c"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "replay",
        "entity_id": "saturation",
        "metric_name": "live_replay_saturation",
        "metric_value": 0.62,
        "run_id": "db-run-c",
        "loaded_at": "2026-05-29T00:05:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:05:00Z", "source_run_id": "source-c"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "ecosystem",
        "entity_id": "contradiction",
        "metric_name": "live_contradiction_burden",
        "metric_value": 0.0,
        "run_id": "db-run-d",
        "loaded_at": "2026-05-29T00:06:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:06:00Z", "source_run_id": "source-d"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "sector",
        "entity_id": "TECH",
        "metric_name": "live_sector_concentration",
        "metric_value": 0.49,
        "run_id": "db-run-e",
        "loaded_at": "2026-05-29T00:07:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:07:00Z", "source_run_id": "source-e"},
    },
    {
        "phase_id": "OPS-LIVE-2",
        "entity_type": "subsector",
        "entity_id": "SOFTWARE",
        "metric_name": "live_subsector_concentration",
        "metric_value": None,
        "run_id": "db-run-f",
        "loaded_at": "2026-05-29T00:08:00Z",
        "payload_jsonb": {"observed_at": "2026-05-29T00:08:00Z", "source_run_id": "source-f"},
    },
]


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    def __init__(self, rows, calls):
        self.rows = rows
        self.calls = calls

    def select(self, columns):
        self.calls.append(("select", columns))
        return self

    def eq(self, column, value):
        self.calls.append(("eq", column, value))
        return self

    def order(self, column, desc=False):
        self.calls.append(("order", column, desc))
        return self

    def limit(self, value):
        self.calls.append(("limit", value))
        return self

    def execute(self):
        self.calls.append(("execute",))
        return FakeResult(self.rows)

    def insert(self, *_args, **_kwargs):
        raise AssertionError("writes are forbidden")

    upsert = update = delete = insert


class FakeClient:
    def __init__(self, rows):
        self.rows = rows
        self.calls = []

    def table(self, name):
        self.calls.append(("table", name))
        return FakeQuery(self.rows, self.calls)


@pytest.fixture
def shuffled_rows():
    return list(reversed(LIVE_ROWS))


def test_deterministic_snapshot_output(shuffled_rows):
    first = build_ops_live3_snapshot(fact_rows=shuffled_rows)
    second = build_ops_live3_snapshot(fact_rows=list(LIVE_ROWS))
    assert first == second
    assert first["source_digest"] == second["source_digest"]


def test_fact_native_input_usage_and_no_report_parsing(shuffled_rows, tmp_path):
    from scripts.run_ops_live3_structural_state_snapshot import _read_bounded_fact_rows

    report_path = tmp_path / "ops_live2.md"
    report_path.write_text("# report with live_provider_health 1.0", encoding="utf-8")
    with pytest.raises(ValueError, match="does not parse markdown"):
        _read_bounded_fact_rows(str(report_path))
    snapshot = build_ops_live3_snapshot(fact_rows=shuffled_rows)
    assert snapshot["inspected_fact_count"] == len(LIVE_ROWS)
    assert snapshot["metric_values"]["live_provider_health"] == 0.83


def test_bounded_local_fact_fallback():
    rows = [
        {
            "phase_id": "OPS-LIVE-2",
            "entity_type": "symbol",
            "entity_id": f"S{i}",
            "metric_name": "live_symbol_weakness",
            "metric_value": 0.1,
            "run_id": "bounded",
            "loaded_at": f"2026-05-29T00:00:{i % 60:02d}Z",
            "payload_jsonb": {"observed_at": f"2026-05-29T00:00:{i % 60:02d}Z"},
        }
        for i in range(MAX_FACT_ROWS + 50)
    ]
    snapshot = build_ops_live3_snapshot(fact_rows=rows, limit=MAX_FACT_ROWS + 50)
    assert snapshot["source_behavior"] == "bounded_local_fact_rows"
    assert snapshot["inspected_fact_count"] == MAX_FACT_ROWS


def test_read_only_client_behavior_and_fact_native_filtering(shuffled_rows):
    client = FakeClient(shuffled_rows + [{"phase_id": "OTHER", "metric_name": "historical_metric", "metric_value": 1.0}])
    snapshot = build_ops_live3_snapshot(client=client, limit=20)
    verbs = [call[0] for call in client.calls]
    assert verbs == ["table", "select", "order", "limit", "execute"]
    assert snapshot["source_behavior"] == "sefi_observation_facts"
    assert snapshot["inspected_fact_count"] == len(LIVE_ROWS)
    assert not {"insert", "upsert", "update", "delete"}.intersection(verbs)


def test_classification_logic(shuffled_rows):
    snapshot = build_ops_live3_snapshot(fact_rows=shuffled_rows)
    assert snapshot["ingestion_completeness_class"] == CLASS_HEALTHY
    assert snapshot["provider_health_class"] == CLASS_WATCH
    assert snapshot["weakness_pressure_class"] == CLASS_HEALTHY
    assert snapshot["replay_pressure_class"] == CLASS_DEGRADED
    assert snapshot["contradiction_pressure_class"] == CLASS_HEALTHY
    assert snapshot["concentration_pressure_class"] == CLASS_WATCH
    assert snapshot["live_health_class"] == CLASS_INSUFFICIENT


def test_insufficient_data_fail_closed_behavior():
    snapshot = build_ops_live3_snapshot(fact_rows=[])
    assert snapshot["snapshot_status"] == "INSUFFICIENT_DATA"
    assert snapshot["live_health_class"] == CLASS_INSUFFICIENT
    assert snapshot["latest_observed_at"] is None


def test_coverage_calculation_and_latest_observed_at(shuffled_rows):
    snapshot = build_ops_live3_snapshot(fact_rows=shuffled_rows)
    assert snapshot["entity_coverage_count"] == 8
    assert snapshot["source_run_count"] == 6
    assert snapshot["latest_observed_at"] == "2026-05-29T00:08:00Z"


def test_report_generation_contains_required_sections(shuffled_rows):
    snapshot = build_ops_live3_snapshot(fact_rows=shuffled_rows)
    report = build_ops_live3_report(snapshot)
    for section in (
        "Objective",
        "Source Behavior",
        "Inspected Fact Source Summary",
        "Live Structural State Summary",
        "Dimension Classifications",
        "Entity/Source Coverage",
        "Insufficient-Data Review",
        "Governance Review",
        "Limitations",
        "Next-Step Recommendation",
    ):
        assert f"## {section}" in report


def test_run_api_and_state_summary(shuffled_rows):
    result = run_ops_live3_snapshot(fact_rows=shuffled_rows)
    assert set(result) == {"snapshot", "summary", "report"}
    assert result["summary"] == build_ops_live3_state_summary(result["snapshot"])
    assert isinstance(result["summary"], OrderedDict)


def test_no_provider_api_fmp_prediction_trading_replay_topology_import_paths():
    module = importlib.import_module("transmission_layers.live_ops.ops_live3_structural_state_snapshot")
    text = module.__loader__.get_source(module.__name__)
    forbidden_tokens = (
        "requests.",
        "financialmodelingprep",
        "predict(",
        "trade(",
        "execute_replay",
        "persist_topology",
        "insert(",
        "upsert(",
        "update(",
        "delete(",
        "create_client",
    )
    assert all(token not in text for token in forbidden_tokens)


def test_governance_flags_false(shuffled_rows):
    snapshot = build_ops_live3_snapshot(fact_rows=shuffled_rows)
    assert all(value is False for value in snapshot["governance_review"].values())
