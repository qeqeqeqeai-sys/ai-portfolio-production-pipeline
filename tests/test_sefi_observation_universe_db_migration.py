from __future__ import annotations

from collections import OrderedDict
from pathlib import Path

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    get_ops_live1b_controlled_universe,
)
from transmission_layers.expectation_failure.real_data.sefi_observation_universe import (
    EXPECTED_SEFI_OBSERVATION_UNIVERSE_ACTIVE_COUNT,
    build_sefi_observation_universe_rows,
    get_active_config_sefi_universe_symbols,
    symbol_digest,
    upsert_sefi_observation_universe,
    validate_sefi_observation_universe_rows,
)


def test_migration_schema_presence():
    sql = Path("supabase/migrations/20260529000200_create_sefi_observation_universe.sql").read_text(encoding="utf-8")
    assert "create table if not exists public.sefi_observation_universe" in sql
    for column in (
        "symbol", "entity_name", "entity_type", "asset_class", "sector", "subsector", "ecosystem_group",
        "source_phase", "universe_version", "is_active", "created_at", "updated_at",
    ):
        assert column in sql
    assert "alter table public.ai_stock_universe" not in sql.lower()
    assert "drop table public.ai_stock_universe" not in sql.lower()
    assert "rename" not in sql.lower()


def test_deterministic_digest_is_stable_and_bounded_sample():
    rows = build_sefi_observation_universe_rows()
    validation = validate_sefi_observation_universe_rows(rows)
    assert validation["symbol_digest"] == symbol_digest([row["symbol"] for row in rows])
    assert validation["symbol_digest"] == validate_sefi_observation_universe_rows(build_sefi_observation_universe_rows())["symbol_digest"]
    assert len(validation["bounded_sample_symbols"]) <= 5


def test_duplicate_detection_blocks_readiness():
    rows = build_sefi_observation_universe_rows()
    duplicate = OrderedDict(rows[0])
    validation = validate_sefi_observation_universe_rows([*rows, duplicate])
    assert validation["duplicate_count"] == 1
    assert validation["duplicates_valid"] is False
    assert validation["ready"] is False


def test_active_count_validation():
    rows = build_sefi_observation_universe_rows()
    validation = validate_sefi_observation_universe_rows(rows)
    assert validation["active_count"] == EXPECTED_SEFI_OBSERVATION_UNIVERSE_ACTIVE_COUNT
    assert validation["unique_symbol_count"] == EXPECTED_SEFI_OBSERVATION_UNIVERSE_ACTIVE_COUNT
    assert validation["duplicate_count"] == 0
    assert validation["ready"] is True


def test_loader_staging_does_not_affect_current_active_universe_source():
    before_ops_live = get_ops_live1b_controlled_universe()
    before_config = get_active_config_sefi_universe_symbols()
    result = upsert_sefi_observation_universe(build_sefi_observation_universe_rows(), execute=False)
    assert result["status"] == "dry_run"
    assert result["attempted_rows"] == 0
    assert get_ops_live1b_controlled_universe() == before_ops_live
    assert get_active_config_sefi_universe_symbols() == before_config

class _Response:
    def __init__(self, data):
        self.data = data


class _Query:
    def __init__(self, rows):
        self.rows = list(rows)

    def select(self, _columns):
        return self

    def eq(self, key, value):
        self.rows = [row for row in self.rows if row.get(key) == value]
        return self

    def order(self, key):
        self.rows = sorted(self.rows, key=lambda row: str(row.get(key, "")))
        return self

    def execute(self):
        return _Response([dict(row) for row in self.rows])


class _Client:
    def __init__(self, rows):
        self.rows = list(rows)
        self.tables = []

    def table(self, name):
        self.tables.append(name)
        assert name == "sefi_observation_universe"
        return _Query(self.rows)


def test_db_valid_path_selected():
    from transmission_layers.expectation_failure.real_data.sefi_observation_universe import load_sefi_universe_symbols

    symbols, telemetry = load_sefi_universe_symbols(client=_Client(build_sefi_observation_universe_rows()))
    assert len(symbols) == 241
    assert telemetry["universe_source_used"] == "db"
    assert telemetry["universe_count"] == 241
    assert "fallback_reason" not in telemetry
    assert len(telemetry["bounded_sample_symbols"]) <= 5


def test_db_invalid_count_falls_back_to_config():
    from transmission_layers.expectation_failure.real_data.sefi_observation_universe import load_sefi_universe_symbols

    symbols, telemetry = load_sefi_universe_symbols(client=_Client(build_sefi_observation_universe_rows()[:-1]))
    assert len(symbols) == 241
    assert telemetry["universe_source_used"] == "config_fallback"
    assert telemetry["fallback_reason"].startswith("db_validation_failed:active_count")


def test_db_digest_mismatch_falls_back_to_config():
    from transmission_layers.expectation_failure.real_data.sefi_observation_universe import load_sefi_universe_symbols

    rows = [dict(row) for row in build_sefi_observation_universe_rows()]
    rows[0]["symbol"] = "ZZZTEST"
    symbols, telemetry = load_sefi_universe_symbols(client=_Client(rows))
    assert len(symbols) == 241
    assert telemetry["universe_source_used"] == "config_fallback"
    assert "digest" in telemetry["fallback_reason"]


def test_config_fallback_still_returns_241():
    from transmission_layers.expectation_failure.real_data.sefi_observation_universe import load_sefi_universe_symbols

    symbols, telemetry = load_sefi_universe_symbols(allow_db=False)
    assert len(symbols) == 241
    assert telemetry["universe_source_used"] == "config_fallback"
    assert telemetry["fallback_reason"] == "db_disabled"


def test_ops_live_loader_output_remains_compatible():
    universe = get_ops_live1b_controlled_universe()
    assert isinstance(universe, list)
    assert len(universe) == 50
    assert universe == sorted(universe)
    assert all(isinstance(symbol, str) and symbol for symbol in universe)


def test_no_ai_stock_universe_cutover_modification():
    changed_paths = {"transmission_layers/expectation_failure/real_data/sefi_observation_universe.py", "transmission_layers/expectation_failure/real_data/hist_density3_curated_ecology_expansion.py", "scripts/check_sefi_universe_source.py"}
    for path in changed_paths:
        text = Path(path).read_text(encoding="utf-8").lower()
        assert "ai_stock_universe" not in text
