from __future__ import annotations

import json
import os
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping, Sequence

from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import (
    DEFAULT_MAX_SYMBOLS,
    _effective_symbols,
)
from transmission_layers.expectation_failure.real_data.sde2_curated_symbol_ecology_expansion import (
    CATEGORY_TO_SECTOR,
    SDE2_VERSION,
    get_sde2_symbol_validation_metadata,
)

SEFI_OBSERVATION_UNIVERSE_TABLE = "sefi_observation_universe"
SEFI_OBSERVATION_UNIVERSE_VERSION = f"{SDE2_VERSION}_effective_241"
SEFI_OBSERVATION_UNIVERSE_SOURCE_PHASE = "hist_density3_curated_241_effective"
EXPECTED_SEFI_OBSERVATION_UNIVERSE_ACTIVE_COUNT = 241
BOUNDED_SAMPLE_SIZE = 5
ETF_SYMBOLS = {
    "ARKK", "DBA", "DBC", "DIA", "GLD", "HYG", "ICLN", "IEF", "IWM", "JNK", "KBE", "KRE", "LQD", "QQQ", "SHY", "SLV", "SPY", "TAN", "TIP", "TLT", "UUP", "VIXY", "VNQ", "USO", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
}


def canonical_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def get_active_config_sefi_universe_symbols() -> list[str]:
    """Return the current file/config-derived SEFI universe; this remains the active default."""
    symbols, _ = _effective_symbols(
        max_symbols=DEFAULT_MAX_SYMBOLS,
        include_high_risk_symbols=False,
        apply_sde2_replacements=True,
    )
    return [canonical_symbol(s) for s in symbols if canonical_symbol(s)]


def _symbol_metadata(symbol: str, metadata: Mapping[str, Mapping[str, Any]]) -> Mapping[str, Any]:
    return metadata.get(symbol, {}) or {}


def build_sefi_observation_universe_rows(*, as_of: datetime | None = None) -> list[OrderedDict[str, Any]]:
    """Build deterministic rows for future DB seeding from the existing config universe."""
    now = (as_of or datetime.now(timezone.utc)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    metadata = get_sde2_symbol_validation_metadata()
    rows: list[OrderedDict[str, Any]] = []
    for symbol in get_active_config_sefi_universe_symbols():
        meta = _symbol_metadata(symbol, metadata)
        primary_category = str(meta.get("primary_category") or "unknown")
        sector = CATEGORY_TO_SECTOR.get(primary_category, "Unknown")
        rows.append(OrderedDict([
            ("symbol", symbol),
            ("entity_name", symbol),
            ("entity_type", "etf" if symbol in ETF_SYMBOLS else "company"),
            ("asset_class", "etf" if symbol in ETF_SYMBOLS else "equity"),
            ("sector", sector),
            ("subsector", primary_category),
            ("ecosystem_group", primary_category),
            ("source_phase", SEFI_OBSERVATION_UNIVERSE_SOURCE_PHASE),
            ("universe_version", SEFI_OBSERVATION_UNIVERSE_VERSION),
            ("is_active", True),
            ("created_at", now),
            ("updated_at", now),
        ]))
    return rows


def symbol_digest(symbols: Sequence[str]) -> str:
    ordered = sorted(canonical_symbol(s) for s in symbols if canonical_symbol(s))
    return sha256("|".join(ordered).encode("utf-8")).hexdigest()


def validate_sefi_observation_universe_rows(rows: Sequence[Mapping[str, Any]], *, expected_active_count: int = EXPECTED_SEFI_OBSERVATION_UNIVERSE_ACTIVE_COUNT) -> OrderedDict[str, Any]:
    active_symbols = [canonical_symbol(str(r.get("symbol", ""))) for r in rows if r.get("is_active") is not False and canonical_symbol(str(r.get("symbol", "")))]
    counts = Counter(active_symbols)
    duplicate_symbols = sorted(symbol for symbol, count in counts.items() if count > 1)
    required_columns = {
        "symbol", "entity_name", "entity_type", "asset_class", "sector", "subsector", "ecosystem_group",
        "source_phase", "universe_version", "is_active", "created_at", "updated_at",
    }
    missing_columns = sorted(required_columns - set(rows[0].keys())) if rows else sorted(required_columns)
    sample_symbols = sorted(counts)[:BOUNDED_SAMPLE_SIZE]
    return OrderedDict([
        ("expected_active_count", expected_active_count),
        ("active_count", len(active_symbols)),
        ("active_count_valid", len(active_symbols) == expected_active_count),
        ("unique_symbol_count", len(counts)),
        ("unique_symbol_count_valid", len(counts) == expected_active_count),
        ("duplicate_count", sum(count - 1 for count in counts.values() if count > 1)),
        ("duplicate_symbols_sample", duplicate_symbols[:BOUNDED_SAMPLE_SIZE]),
        ("duplicates_valid", not duplicate_symbols),
        ("symbol_digest", symbol_digest(active_symbols)),
        ("bounded_sample_symbols", sample_symbols),
        ("bounded_sample_size", len(sample_symbols)),
        ("missing_required_columns", missing_columns),
        ("schema_columns_valid", not missing_columns),
        ("source_phase", SEFI_OBSERVATION_UNIVERSE_SOURCE_PHASE),
        ("universe_version", SEFI_OBSERVATION_UNIVERSE_VERSION),
        ("ready", len(active_symbols) == expected_active_count and len(counts) == expected_active_count and not duplicate_symbols and not missing_columns),
    ])


def get_db_sefi_observation_universe(*, client: Any | None = None, active_only: bool = True, limit: int | None = None) -> list[dict[str, Any]]:
    """Read-only helper for future cutover; not used by active OPS-LIVE/HIST-LONG loaders."""
    c = client or _build_supabase_client()
    if c is None:
        return []
    query = c.table(SEFI_OBSERVATION_UNIVERSE_TABLE).select("symbol,entity_name,entity_type,asset_class,sector,subsector,ecosystem_group,source_phase,universe_version,is_active,created_at,updated_at")
    if active_only:
        query = query.eq("is_active", True)
    query = query.order("symbol")
    if limit is not None:
        query = query.limit(int(limit))
    resp = query.execute()
    return list(getattr(resp, "data", None) or [])


def _build_supabase_client() -> Any | None:
    url = os.getenv("SUPABASE_URL", "").strip()
    key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")).strip()
    if not url or not key:
        return None
    from supabase import create_client

    return create_client(url, key)


def upsert_sefi_observation_universe(rows: Sequence[Mapping[str, Any]], *, client: Any | None = None, execute: bool = False) -> OrderedDict[str, Any]:
    validation = validate_sefi_observation_universe_rows(rows)
    if not validation["ready"]:
        return OrderedDict([("status", "blocked_validation_failed"), ("attempted_rows", 0), ("validation", validation)])
    if not execute:
        return OrderedDict([("status", "dry_run"), ("attempted_rows", 0), ("candidate_rows", len(rows)), ("validation", validation)])
    c = client or _build_supabase_client()
    if c is None:
        return OrderedDict([("status", "blocked_client_unavailable"), ("attempted_rows", 0), ("validation", validation)])
    resp = c.table(SEFI_OBSERVATION_UNIVERSE_TABLE).upsert(list(rows), on_conflict="symbol,universe_version").execute()
    data = getattr(resp, "data", None)
    return OrderedDict([("status", "submitted"), ("attempted_rows", len(rows)), ("confirmed_rows", len(data) if isinstance(data, list) else None), ("validation", validation)])


def render_validation_report(validation: Mapping[str, Any]) -> str:
    return "\n".join([
        "# SEFI Observation Universe DB Migration Readiness",
        "",
        "## Scope",
        "- DB-readiness only for `public.sefi_observation_universe`.",
        "- Active OPS-LIVE / HIST-LONG universe source remains the existing file/config loader.",
        "- No prediction, trading, signal activation, replay activation, or live cutover changes are included.",
        "",
        "## Source discovery",
        "- Existing active source: SDE2 category/config universe transformed by HIST-DENSITY-3 effective-symbol replacement logic.",
        f"- Source phase: `{validation.get('source_phase')}`.",
        f"- Universe version: `{validation.get('universe_version')}`.",
        "",
        "## Validation",
        f"- Expected active count: {validation.get('expected_active_count')}",
        f"- Active count: {validation.get('active_count')}",
        f"- Unique symbol count: {validation.get('unique_symbol_count')}",
        f"- Duplicate count: {validation.get('duplicate_count')}",
        f"- Deterministic symbol digest: `{validation.get('symbol_digest')}`",
        f"- Bounded sample symbols: {json.dumps(validation.get('bounded_sample_symbols', []))}",
        f"- Missing required columns: {json.dumps(validation.get('missing_required_columns', []))}",
        f"- Ready: {validation.get('ready')}",
        "",
        "## Cutover posture",
        "- DB read helper is available for future use only.",
        "- Existing JSON/config universe remains active default.",
        "- Observation accumulation source was not changed.",
        "",
    ])
