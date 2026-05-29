from __future__ import annotations

import json
import os
from collections import Counter, OrderedDict
from datetime import datetime, timezone
from hashlib import sha256
from typing import Any, Mapping, Sequence

from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import (
    DEFAULT_MAX_SYMBOLS,
    _config_effective_symbols,
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
EXPECTED_SEFI_OBSERVATION_UNIVERSE_DIGEST = "2b25bc53631cdf1f95848fbe8a154cd7edd1aed5f4c52a931aedc1ff63a6c3af"
BOUNDED_SAMPLE_SIZE = 5
ETF_SYMBOLS = {
    "ARKK", "DBA", "DBC", "DIA", "GLD", "HYG", "ICLN", "IEF", "IWM", "JNK", "KBE", "KRE", "LQD", "QQQ", "SHY", "SLV", "SPY", "TAN", "TIP", "TLT", "UUP", "VIXY", "VNQ", "USO", "XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY",
}


def canonical_symbol(symbol: str) -> str:
    return str(symbol or "").strip().upper()


def get_active_config_sefi_universe_symbols() -> list[str]:
    """Return the deterministic file/config-derived SEFI universe fallback."""
    symbols, _ = _config_effective_symbols(
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


def validate_sefi_observation_universe_rows(rows: Sequence[Mapping[str, Any]], *, expected_active_count: int = EXPECTED_SEFI_OBSERVATION_UNIVERSE_ACTIVE_COUNT, expected_digest: str = EXPECTED_SEFI_OBSERVATION_UNIVERSE_DIGEST) -> OrderedDict[str, Any]:
    active_symbols = [canonical_symbol(str(r.get("symbol", ""))) for r in rows if r.get("is_active") is not False and canonical_symbol(str(r.get("symbol", "")))]
    counts = Counter(active_symbols)
    duplicate_symbols = sorted(symbol for symbol, count in counts.items() if count > 1)
    required_columns = {
        "symbol", "entity_name", "entity_type", "asset_class", "sector", "subsector", "ecosystem_group",
        "source_phase", "universe_version", "is_active", "created_at", "updated_at",
    }
    missing_columns = sorted(required_columns - set(rows[0].keys())) if rows else sorted(required_columns)
    sample_symbols = sorted(counts)[:BOUNDED_SAMPLE_SIZE]
    digest = symbol_digest(active_symbols)
    return OrderedDict([
        ("expected_active_count", expected_active_count),
        ("active_count", len(active_symbols)),
        ("active_count_valid", len(active_symbols) == expected_active_count),
        ("unique_symbol_count", len(counts)),
        ("unique_symbol_count_valid", len(counts) == expected_active_count),
        ("duplicate_count", sum(count - 1 for count in counts.values() if count > 1)),
        ("duplicate_symbols_sample", duplicate_symbols[:BOUNDED_SAMPLE_SIZE]),
        ("duplicates_valid", not duplicate_symbols),
        ("expected_symbol_digest", expected_digest),
        ("symbol_digest", digest),
        ("symbol_digest_valid", digest == expected_digest),
        ("bounded_sample_symbols", sample_symbols),
        ("bounded_sample_size", len(sample_symbols)),
        ("missing_required_columns", missing_columns),
        ("schema_columns_valid", not missing_columns),
        ("source_phase", SEFI_OBSERVATION_UNIVERSE_SOURCE_PHASE),
        ("universe_version", SEFI_OBSERVATION_UNIVERSE_VERSION),
        ("ready", len(active_symbols) == expected_active_count and len(counts) == expected_active_count and not duplicate_symbols and not missing_columns and digest == expected_digest),
    ])


def _rows_from_symbols(symbols: Sequence[str]) -> list[OrderedDict[str, Any]]:
    return [
        OrderedDict([
            ("symbol", canonical_symbol(symbol)),
            ("entity_name", canonical_symbol(symbol)),
            ("entity_type", "unknown"),
            ("asset_class", "unknown"),
            ("sector", "unknown"),
            ("subsector", "unknown"),
            ("ecosystem_group", "unknown"),
            ("source_phase", SEFI_OBSERVATION_UNIVERSE_SOURCE_PHASE),
            ("universe_version", SEFI_OBSERVATION_UNIVERSE_VERSION),
            ("is_active", True),
            ("created_at", "validation_only"),
            ("updated_at", "validation_only"),
        ])
        for symbol in symbols
        if canonical_symbol(symbol)
    ]


def _validation_failure_reason(validation: Mapping[str, Any], *, prefix: str) -> str:
    failed: list[str] = []
    if not validation.get("active_count_valid"):
        failed.append("active_count")
    if not validation.get("unique_symbol_count_valid"):
        failed.append("unique_symbol_count")
    if not validation.get("duplicates_valid"):
        failed.append("duplicate_count")
    if not validation.get("symbol_digest_valid"):
        failed.append("digest")
    if not validation.get("schema_columns_valid"):
        failed.append("schema_columns")
    return f"{prefix}_validation_failed:" + ",".join(failed or ["unknown"])


def _compact_universe_telemetry(*, source: str, symbols: Sequence[str], validation: Mapping[str, Any], fallback_reason: str | None = None) -> OrderedDict[str, Any]:
    telemetry = OrderedDict([
        ("universe_source_used", source),
        ("universe_count", len(symbols)),
        ("universe_digest", validation.get("symbol_digest")),
        ("bounded_sample_symbols", list(validation.get("bounded_sample_symbols", []))[:BOUNDED_SAMPLE_SIZE]),
    ])
    if fallback_reason:
        telemetry["fallback_reason"] = fallback_reason
    return telemetry


def load_sefi_universe_symbols(*, client: Any | None = None, allow_db: bool = True, config_loader: Any | None = None) -> tuple[list[str], OrderedDict[str, Any]]:
    """Prefer validated public.sefi_observation_universe, with validated config fallback."""
    fallback_reason: str | None = None
    if allow_db:
        try:
            db_rows = get_db_sefi_observation_universe(client=client)
            db_validation = validate_sefi_observation_universe_rows(db_rows)
            if db_validation.get("ready"):
                symbols = [canonical_symbol(str(row.get("symbol", ""))) for row in db_rows if row.get("is_active") is not False and canonical_symbol(str(row.get("symbol", "")))]
                return symbols, _compact_universe_telemetry(source="db", symbols=symbols, validation=db_validation)
            fallback_reason = _validation_failure_reason(db_validation, prefix="db")
        except Exception as exc:
            fallback_reason = f"db_read_failed:{type(exc).__name__}"
    else:
        fallback_reason = "db_disabled"

    loader = config_loader or _config_effective_symbols
    config_symbols, config_telemetry = loader(
        max_symbols=DEFAULT_MAX_SYMBOLS,
        include_high_risk_symbols=False,
        apply_sde2_replacements=True,
    )
    symbols = [canonical_symbol(s) for s in config_symbols if canonical_symbol(s)]
    config_validation = validate_sefi_observation_universe_rows(_rows_from_symbols(symbols))
    if not config_validation.get("ready"):
        raise ValueError(_validation_failure_reason(config_validation, prefix="config_fallback"))
    telemetry = _compact_universe_telemetry(
        source="config_fallback",
        symbols=symbols,
        validation=config_validation,
        fallback_reason=fallback_reason,
    )
    for key, value in dict(config_telemetry).items():
        telemetry.setdefault(key, value)
    return symbols, telemetry


def get_db_sefi_observation_universe(*, client: Any | None = None, active_only: bool = True, limit: int | None = None) -> list[dict[str, Any]]:
    """Read active SEFI observation-universe rows for the DB-default cutover loader."""
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
        "- Active OPS-LIVE / HIST-LONG universe source now prefers validated `public.sefi_observation_universe` with config fallback.",
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
        "- Source order: DB sefi_observation_universe -> validation gates -> config fallback.",
        "- Required DB gates: active_count=241, unique_symbol_count=241, duplicate_count=0, exact digest match.",
        "- If DB is empty or not loaded, run `python scripts/load_sefi_observation_universe.py --execute` before expecting DB selection.",
        "",
    ])
