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
