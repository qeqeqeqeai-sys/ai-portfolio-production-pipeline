from decimal import Decimal

import pytest

from transmission_layers.history_read_model.fact_emitter import (
    OBSERVATION_FACTS_TABLE,
    ObservationFactEmissionError,
    build_fact_emission_context,
    build_observation_fact_row,
    build_observation_fact_rows,
    emit_observation_facts,
    should_emit_facts,
    validate_observation_fact_row,
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

    def upsert(self, rows):  # pragma: no cover - must never be reached
        raise AssertionError("upsert must not be used")

    def update(self, rows):  # pragma: no cover - must never be reached
        raise AssertionError("update must not be used")

    def delete(self):  # pragma: no cover - must never be reached
        raise AssertionError("delete must not be used")


class FakeClient:
    def __init__(self):
        self.tables = []
        self.inserted = []

    def table(self, name):
        table = FakeTable(self, name)
        self.tables.append(table)
        return table

    def rpc(self, *args, **kwargs):  # pragma: no cover - must never be reached
        raise AssertionError("provider/API/live ingestion paths must not be used")

    def storage(self):  # pragma: no cover - must never be reached
        raise AssertionError("artifact or live ingestion storage must not be used")


BASE = dict(
    phase_id="HIST-LONG-8",
    phase_name="Future Direct Facts",
    artifact_id="artifact-1",
    run_id="run-1",
    entity_type="symbol",
    entity_id="aapl",
    metric_name=" Replay Density ",
    metric_value=Decimal("1.25"),
    window_days=30,
    payload_jsonb={"source": "unit", "rank": 1},
)


def test_deterministic_row_construction_and_symbol_normalization():
    row = build_observation_fact_row(**BASE)
    repeat = build_observation_fact_row(**BASE)

    assert row == repeat
    assert row["entity_type"] == "symbol"
    assert row["entity_id"] == "AAPL"
    assert row["metric_name"] == "replay density"
    assert row["payload_jsonb"] == {"rank": 1, "source": "unit"}
    assert validate_observation_fact_row(row) is True


def test_duplicate_key_stability_ignores_payload_order_but_changes_identity():
    first = build_observation_fact_row(**BASE)
    reordered_payload = dict(BASE, payload_jsonb={"rank": 1, "source": "unit"})
    second = build_observation_fact_row(**reordered_payload)
    different_metric = build_observation_fact_row(**dict(BASE, metric_name="other"))

    assert first["duplicate_prevention_key"] == second["duplicate_prevention_key"]
    assert first["duplicate_prevention_key"] != different_metric["duplicate_prevention_key"]


def test_payload_bound_enforcement():
    with pytest.raises(ObservationFactEmissionError, match="bounded metadata limit"):
        build_observation_fact_row(**dict(BASE, payload_jsonb={"blob": "x" * 9000}))


def test_required_field_validation_fails_closed():
    with pytest.raises(ObservationFactEmissionError, match="entity_id is required"):
        build_observation_fact_row(**dict(BASE, entity_id=" "))

    row = build_observation_fact_row(**BASE)
    del row["phase_id"]
    with pytest.raises(ObservationFactEmissionError, match="phase_id is required"):
        validate_observation_fact_row(row)


def test_metric_value_type_safety_allows_numeric_or_null_only():
    assert build_observation_fact_row(**dict(BASE, metric_value=None))["metric_value"] is None
    assert build_observation_fact_row(**dict(BASE, metric_value=2))["metric_value"] == 2

    for bad_value in (True, "1.0", object()):
        with pytest.raises(ObservationFactEmissionError, match="metric_value must be numeric or null"):
            build_observation_fact_row(**dict(BASE, metric_value=bad_value))


def test_dry_run_does_not_write():
    client = FakeClient()
    row = build_observation_fact_row(**BASE)

    result = emit_observation_facts(client, [row])

    assert result["dry_run"] is True
    assert result["attempted_rows"] == 1
    assert result["inserted_rows"] == 0
    assert client.tables == []
    assert client.inserted == []


def test_execute_mode_inserts_only_without_upsert_update_delete():
    client = FakeClient()
    row = build_observation_fact_row(**BASE)

    result = emit_observation_facts(client, [row], dry_run=False)

    assert result["dry_run"] is False
    assert result["inserted_rows"] == 1
    assert client.inserted == [(OBSERVATION_FACTS_TABLE, [row])]
    assert client.tables[0].calls[0] == ("insert", [row])
    assert client.tables[0].calls[1] == ("execute", None)


def test_disabled_context_blocks_emission():
    context = build_fact_emission_context(
        enabled=False,
        dry_run=True,
        phase_id="HIST-LONG-8",
        phase_name="Future Direct Facts",
        artifact_id="artifact-1",
        run_id="run-1",
    )

    assert should_emit_facts(context) is False
    assert build_observation_fact_rows(context=context, observations=[BASE]) == []


def test_enabled_context_builds_rows_without_provider_prediction_trading_or_live_paths():
    context = build_fact_emission_context(
        enabled=True,
        dry_run=True,
        phase_id="HIST-LONG-8",
        phase_name="Future Direct Facts",
        artifact_id="artifact-1",
        run_id="run-1",
    )
    observations = [
        {
            "entity_type": "sector",
            "entity_id": " technology ",
            "metric_name": "breadth",
            "metric_value": 3.5,
            "window_days": None,
            "payload_jsonb": {"note": "derived from existing phase output"},
        }
    ]

    rows = build_observation_fact_rows(context=context, observations=observations)
    result = emit_observation_facts(FakeClient(), rows, dry_run=context["dry_run"])

    assert should_emit_facts(context) is True
    assert rows[0]["entity_id"] == "technology"
    assert result["dry_run"] is True
    assert result["inserted_rows"] == 0
