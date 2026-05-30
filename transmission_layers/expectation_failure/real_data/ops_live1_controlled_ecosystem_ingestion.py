"""OPS-LIVE-1 controlled live ecosystem state ingestion.

Deterministic, bounded, observational-only ingestion + normalization layer for the
curated 300-stock universe.
"""

from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
from typing import Callable, Iterable, Sequence
from urllib.parse import urlencode
from urllib.request import urlopen

MAX_INGESTION_BATCH_SIZE = 50
MAX_SNAPSHOT_ROWS = 300
MAX_CONTINUITY_WINDOW_DAYS = 90
MAX_DASHBOARD_PAYLOAD_ROWS = 120
MAX_STRUCTURAL_SUMMARY_ITEMS = 12
MAX_RETRY_ATTEMPTS = 2

MAX_DIAGNOSTIC_SAMPLE_KEYS = 12
MAX_DIAGNOSTIC_EXCEPTION_CHARS = 180

FAILURE_STAGE_SUCCESS = "success"
FAILURE_STAGE_FETCH_FAILED = "fetch_failed"
FAILURE_STAGE_INVALID_PAYLOAD_SHAPE = "invalid_payload_shape"
FAILURE_STAGE_EMPTY_FMP_PAYLOAD = "empty_fmp_payload"
FAILURE_STAGE_ALL_ROWS_REJECTED_BY_SYMBOL_FILTER = "all_rows_rejected_by_symbol_filter"
FAILURE_STAGE_SCHEMA_VALIDATION_FAILED = "schema_validation_failed"
FAILURE_STAGE_NORMALIZATION_FAILED = "normalization_failed"

DEFAULT_PROBE_UNIVERSE = ("AAPL", "MSFT", "JPM", "XOM", "UNH", "PG", "NEM", "NEE")
MAX_PROBE_UNIVERSE_SIZE = 10

GOVERNANCE_BOUNDARIES = {
    "observational_only": True,
    "no_recursive_replay_operationalization": True,
    "no_autonomous_replay": True,
    "no_topology_activation": True,
    "no_self_modifying_pathways": True,
    "no_prediction_or_trading_execution": True,
    "no_graph_execution_engines": True,
    "no_high_frequency_streaming": True,
}


def _deterministic_snapshot_timestamp(snapshot_date: str) -> str:
    return f"{snapshot_date}T00:00:00Z"


def _chunked(symbols: Sequence[str], size: int) -> list[list[str]]:
    return [list(symbols[i : i + size]) for i in range(0, len(symbols), size)]


def _bounded_float(value: object, default: float = 0.0) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    return float(value)


def canonicalize_symbol(symbol: object) -> str:
    """Single-source symbol canonicalization for OPS ingestion boundaries."""
    return str(symbol).strip().upper()


def _normalize_row(row: dict, snapshot_ts: str) -> dict:
    return {
        "symbol": canonicalize_symbol(row.get("symbol", "")),
        "snapshot_ts": snapshot_ts,
        "price_state": _bounded_float(row.get("price")),
        "market_cap": _bounded_float(row.get("marketCap")),
        "sector": str(row.get("sector", "UNKNOWN")),
        "subsector": str(row.get("subsector", row.get("industry", "UNKNOWN"))),
        "volatility_structure": _bounded_float(row.get("volatility", row.get("beta"))),
        "valuation_structure": _bounded_float(row.get("valuation", row.get("pe"))),
        "profitability_structure": _bounded_float(row.get("profitability", row.get("roe"))),
        "leverage_liquidity_structure": _bounded_float(row.get("leverageLiquidity", row.get("debtToEquity"))),
        "breadth_dispersion_structure": _bounded_float(row.get("breadthDispersion", row.get("dispersion"))),
        "ecosystem_continuity_ts": snapshot_ts,
    }


def _normalize_probe_symbols(symbols: Sequence[str] | None = None, max_size: int = MAX_PROBE_UNIVERSE_SIZE) -> list[str]:
    bounded = symbols or DEFAULT_PROBE_UNIVERSE
    return sorted({canonicalize_symbol(s) for s in bounded if canonicalize_symbol(s)})[: max(1, min(max_size, MAX_PROBE_UNIVERSE_SIZE))]


def _fmp_to_ops_mapping_diagnostics(raw: dict, normalized: dict) -> dict:
    mappings = {
        "price_state": ("price",),
        "market_cap": ("marketCap",),
        "sector": ("sector",),
        "subsector": ("subsector", "industry"),
        "volatility_structure": ("volatility", "beta"),
        "valuation_structure": ("valuation", "pe"),
        "profitability_structure": ("profitability", "roe"),
        "leverage_liquidity_structure": ("leverageLiquidity", "debtToEquity"),
        "breadth_dispersion_structure": ("breadthDispersion", "dispersion"),
    }
    fields_mapped, missing_fields, null_fields, fallback_fields_used = [], [], [], []
    for target, candidates in mappings.items():
        selected = next((f for f in candidates if f in raw), None)
        if selected is None:
            missing_fields.append(target)
            continue
        value = raw.get(selected)
        if value is None:
            null_fields.append(target)
        if len(candidates) > 1 and selected != candidates[0]:
            fallback_fields_used.append({"target": target, "fallback_source": selected})
        fields_mapped.append({"target": target, "source": selected, "normalized_value": normalized.get(target)})
    return {
        "fields_mapped": fields_mapped,
        "missing_fields": sorted(missing_fields),
        "null_fields": sorted(null_fields),
        "fallback_fields_used": fallback_fields_used,
    }


def _raw_required_field_violations(raw_rows: Sequence[dict], expected_symbols: Sequence[str]) -> list[dict]:
    violations = []
    required = ("price", "marketCap", "sector")
    for symbol in expected_symbols:
        raw = next((r for r in raw_rows if canonicalize_symbol(r.get("symbol", "")) == canonicalize_symbol(symbol)), None)
        if raw is None:
            violations.append({"symbol": symbol, "missing_raw_fields": ["symbol_record_missing"]})
            continue
        missing = [f for f in required if f not in raw or raw.get(f) is None]
        if (raw.get("industry") is None) and (raw.get("subsector") is None):
            missing.append("industry_or_subsector")
        if missing:
            violations.append({"symbol": symbol, "missing_raw_fields": missing})
    return violations


def build_live_fmp_fetcher(api_key: str) -> Callable[[Sequence[str]], Iterable[dict]]:
    if not api_key:
        raise RuntimeError("FMP_API_KEY is required for live probe mode")

    def _fetch(symbols: Sequence[str]) -> list[dict]:
        query = urlencode({"symbol": ",".join(symbols), "apikey": api_key})
        with urlopen(f"https://financialmodelingprep.com/api/v3/quote/{','.join(symbols)}?{query}", timeout=20) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        if not isinstance(payload, list):
            raise RuntimeError("Invalid FMP payload shape")
        return payload

    return _fetch


def run_ops_live1a_controlled_fmp_probe(
    *,
    snapshot_date: str,
    output_path: str,
    symbols: Sequence[str] | None = None,
    fetch_batch: Callable[[Sequence[str]], Iterable[dict]] | None = None,
) -> dict:
    probe_symbols = _normalize_probe_symbols(symbols)
    if fetch_batch is None:
        api_key = os.getenv("FMP_API_KEY", "")
        if not api_key:
            raise RuntimeError("FMP_API_KEY missing; probe fails closed")
        fetch_batch = build_live_fmp_fetcher(api_key)

    raw_rows = list(fetch_controlled_fmp_snapshot_batch(probe_symbols, fetch_batch))
    raw_required_violations = _raw_required_field_violations(raw_rows, probe_symbols)
    if raw_required_violations:
        result = {"status": "failed_closed", "integrity": {"raw_required_field_violations": raw_required_violations}}
    else:
        result = ingest_controlled_daily_snapshot(probe_symbols, snapshot_date, fetch_batch)
    symbol_to_raw = {canonicalize_symbol(r.get("symbol", "")): r for r in raw_rows}
    diagnostics = {
        "symbols_failed_closed": result.get("integrity", {}).get("missing_symbols", []) if result.get("status") != "ok" else [],
        "symbols_successfully_normalized": [r["symbol"] for r in result.get("rows", [])],
        "invalid_values": result.get("integrity", {}).get("invalid_numeric_values", []) + result.get("integrity", {}).get("invalid_financial_values", []),
        "field_mapping": [],
    }
    for row in result.get("rows", []):
        raw = symbol_to_raw.get(row["symbol"], {})
        diagnostics["field_mapping"].append({"symbol": row["symbol"], **_fmp_to_ops_mapping_diagnostics(raw, row)})

    probe_report = {
        "probe_universe": probe_symbols,
        "probe_size": len(probe_symbols),
        "bounded_probe_only": True,
        "dry_run_local_output_only": True,
        "supabase_write_enabled": False,
        "snapshot_identity": result.get("snapshot_identity", {}),
        "payload_shape": {k: result.get("operator_payload", {}).get(k) for k in (
            "daily_ecosystem_posture", "dominant_structural_pressures", "strongest_resilience_pathways", "fragmentation_hotspots",
            "transition_state_summaries", "continuity_summaries", "normalization_observations", "compression_observability"
        )},
        "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
        "status": result.get("status"),
        "diagnostics": diagnostics,
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(probe_report, indent=2, sort_keys=True), encoding="utf-8")
    return probe_report


def _compute_snapshot_identity(rows: Sequence[dict], snapshot_ts: str) -> dict:
    ordered_symbols = sorted(r["symbol"] for r in rows)
    symbol_blob = "|".join(ordered_symbols)
    symbol_checksum = sha256(symbol_blob.encode("utf-8")).hexdigest()[:16]
    row_checksum_source = "|".join(
        f'{r["symbol"]}:{r["price_state"]}:{r["market_cap"]}:{r["sector"]}:{r["subsector"]}:{r["volatility_structure"]}:{r["valuation_structure"]}:{r["profitability_structure"]}:{r["leverage_liquidity_structure"]}:{r["breadth_dispersion_structure"]}'
        for r in rows
    )
    row_checksum = sha256(row_checksum_source.encode("utf-8")).hexdigest()[:16]
    snapshot_seed = f"{snapshot_ts}|{symbol_blob}|{len(rows)}|{symbol_checksum}"
    snapshot_id = sha256(snapshot_seed.encode("utf-8")).hexdigest()[:20]
    return {"snapshot_id": snapshot_id, "symbol_checksum": symbol_checksum, "row_checksum": row_checksum}


def _integrity_validate(rows: Sequence[dict], expected_symbols: Sequence[str]) -> dict:
    symbols = [r.get("symbol") for r in rows]
    unique = sorted(set(symbols))
    expected = sorted({canonicalize_symbol(s) for s in expected_symbols})
    missing = [s for s in expected if s not in unique]
    duplicates = len(symbols) - len(unique)
    malformed_symbols = sorted(
        s for s in unique if not isinstance(s, str) or not s.strip() or not s.replace("-", "").isalnum() or s != s.upper()
    )
    required_fields = (
        "symbol",
        "snapshot_ts",
        "price_state",
        "market_cap",
        "sector",
        "subsector",
        "volatility_structure",
        "valuation_structure",
        "profitability_structure",
        "leverage_liquidity_structure",
        "breadth_dispersion_structure",
        "ecosystem_continuity_ts",
    )
    missing_required_fields: list[dict] = []
    invalid_numeric_values: list[dict] = []
    invalid_financial_values: list[dict] = []
    missing_normalization_fields: list[dict] = []
    for r in rows:
        missing_fields = [f for f in required_fields if f not in r]
        if missing_fields:
            missing_required_fields.append({"symbol": r.get("symbol", ""), "missing_fields": missing_fields})
        if not str(r.get("sector", "")).strip() or not str(r.get("subsector", "")).strip():
            missing_normalization_fields.append({"symbol": r.get("symbol", ""), "issue": "missing_sector_or_subsector"})
        for nf in (
            "price_state",
            "market_cap",
            "volatility_structure",
            "valuation_structure",
            "profitability_structure",
            "leverage_liquidity_structure",
            "breadth_dispersion_structure",
        ):
            v = r.get(nf)
            if not isinstance(v, (int, float)) or not math.isfinite(float(v)):
                invalid_numeric_values.append({"symbol": r.get("symbol", ""), "field": nf, "value": v})
        if isinstance(r.get("market_cap"), (int, float)) and r["market_cap"] < 0:
            invalid_financial_values.append({"symbol": r.get("symbol", ""), "field": "market_cap", "value": r["market_cap"]})
        if isinstance(r.get("price_state"), (int, float)) and r["price_state"] < 0:
            invalid_financial_values.append({"symbol": r.get("symbol", ""), "field": "price_state", "value": r["price_state"]})
    is_valid = (
        (not missing)
        and duplicates == 0
        and len(rows) <= MAX_SNAPSHOT_ROWS
        and not malformed_symbols
        and not missing_required_fields
        and not invalid_numeric_values
        and not invalid_financial_values
        and not missing_normalization_fields
    )
    return {
        "is_valid": is_valid,
        "missing_symbols": missing,
        "duplicate_count": duplicates,
        "row_count": len(rows),
        "malformed_symbols": malformed_symbols,
        "missing_required_fields": missing_required_fields,
        "invalid_numeric_values": invalid_numeric_values,
        "invalid_financial_values": invalid_financial_values,
        "missing_normalization_fields": missing_normalization_fields,
    }


def _normalized_duplicate_identity(row: dict) -> tuple[object, ...]:
    return (
        row.get("price_state"),
        row.get("market_cap"),
        row.get("sector"),
        row.get("subsector"),
        row.get("volatility_structure"),
        row.get("valuation_structure"),
        row.get("profitability_structure"),
        row.get("leverage_liquidity_structure"),
        row.get("breadth_dispersion_structure"),
        row.get("ecosystem_continuity_ts"),
    )


def _bounded_symbol_sample(symbols: Iterable[str], limit: int = 25) -> list[str]:
    return sorted({s for s in symbols if s})[:limit]



class InvalidFmpPayloadShape(TypeError):
    def __init__(self, message: str, response_type: str, sample_response_keys: Sequence[str] | None = None) -> None:
        super().__init__(message)
        self.response_type = response_type
        self.sample_response_keys = sorted(str(k) for k in (sample_response_keys or []))[:MAX_DIAGNOSTIC_SAMPLE_KEYS]


def _bounded_exception_message(exc: Exception) -> str:
    msg = str(exc)
    api_key = os.getenv("FMP_API_KEY", "")
    if api_key:
        msg = msg.replace(api_key, "[REDACTED]")
    for marker in ("apikey=", "api_key="):
        lowered = msg.lower()
        idx = lowered.find(marker)
        if idx >= 0:
            end = len(msg)
            for sep in ("&", " ", "\n", "\t"):
                sep_idx = msg.find(sep, idx + len(marker))
                if sep_idx >= 0:
                    end = min(end, sep_idx)
            msg = f"{msg[:idx]}{marker}[REDACTED]{msg[end:]}"
    return msg[:MAX_DIAGNOSTIC_EXCEPTION_CHARS]


def _diagnostic_response_type(payload: object) -> str:
    if isinstance(payload, list):
        return "list"
    if isinstance(payload, tuple):
        return "tuple"
    if isinstance(payload, Mapping):
        return "dict"
    return type(payload).__name__


def _sample_response_keys(rows: Sequence[dict]) -> list[str]:
    for row in rows:
        if isinstance(row, Mapping):
            return sorted(str(k) for k in row.keys())[:MAX_DIAGNOSTIC_SAMPLE_KEYS]
    return []


def _base_ingestion_boundary_diagnostics(
    *,
    fetch_status: str = "not_started",
    response_type: str = "unknown",
    raw_row_count: int = 0,
    accepted_row_count: int = 0,
    rejected_row_count: int = 0,
    sample_response_keys: Sequence[str] | None = None,
    failure_stage: str = FAILURE_STAGE_FETCH_FAILED,
    exception_type: str = "",
    exception_message: str = "",
    canonicalized_batch_symbols: Iterable[str] = (),
    canonicalized_row_symbols: Iterable[str] = (),
    dropped_due_to_batch_filter_count: int = 0,
    duplicate_elision_count: int = 0,
    rejected_row_reasons: Sequence[dict[str, str]] = (),
) -> dict:
    return {
        "fetch_status": fetch_status,
        "response_type": response_type,
        "raw_row_count": raw_row_count,
        "accepted_row_count": accepted_row_count,
        "rejected_row_count": rejected_row_count,
        "sample_response_keys": sorted(str(k) for k in (sample_response_keys or []))[:MAX_DIAGNOSTIC_SAMPLE_KEYS],
        "failure_stage": failure_stage,
        "exception_type": exception_type,
        "exception_message": exception_message,
        "canonicalized_batch_symbols_sample": _bounded_symbol_sample(canonicalized_batch_symbols),
        "canonicalized_row_symbols_sample": _bounded_symbol_sample(canonicalized_row_symbols),
        "dropped_due_to_batch_filter_count": dropped_due_to_batch_filter_count,
        "duplicate_elision_count": duplicate_elision_count,
        "rejected_row_reasons": list(rejected_row_reasons)[:25],
    }


def _classify_integrity_failure(integrity: dict, diagnostics: dict) -> str:
    if diagnostics["raw_row_count"] == 0:
        return FAILURE_STAGE_EMPTY_FMP_PAYLOAD
    if diagnostics["accepted_row_count"] == 0 and diagnostics["dropped_due_to_batch_filter_count"] == diagnostics["raw_row_count"]:
        return FAILURE_STAGE_ALL_ROWS_REJECTED_BY_SYMBOL_FILTER
    return FAILURE_STAGE_SCHEMA_VALIDATION_FAILED


def fetch_controlled_fmp_snapshot_batch(
    symbols: Sequence[str], fetch_batch: Callable[[Sequence[str]], Iterable[dict]]
) -> list[dict]:
    bounded_symbols = [canonicalize_symbol(s) for s in symbols if canonicalize_symbol(s)][:MAX_INGESTION_BATCH_SIZE]
    payload = fetch_batch(bounded_symbols)
    if isinstance(payload, Mapping):
        raise InvalidFmpPayloadShape(
            f"Invalid FMP payload shape: {_diagnostic_response_type(payload)}",
            _diagnostic_response_type(payload),
            sorted(str(k) for k in payload.keys())[:MAX_DIAGNOSTIC_SAMPLE_KEYS],
        )
    if isinstance(payload, (str, bytes)):
        raise InvalidFmpPayloadShape(
            f"Invalid FMP payload shape: {_diagnostic_response_type(payload)}",
            _diagnostic_response_type(payload),
        )
    try:
        rows = list(payload)
    except TypeError as exc:
        raise InvalidFmpPayloadShape(
            f"Invalid FMP payload shape: {_diagnostic_response_type(payload)}",
            _diagnostic_response_type(payload),
        ) from exc
    if any(not isinstance(row, Mapping) for row in rows):
        raise InvalidFmpPayloadShape("Invalid FMP payload row shape", _diagnostic_response_type(rows), _sample_response_keys(rows))
    return rows


def ingest_controlled_daily_snapshot(
    symbols: Sequence[str],
    snapshot_date: str,
    fetch_batch: Callable[[Sequence[str]], Iterable[dict]],
) -> dict:
    ordered_symbols = sorted({canonicalize_symbol(s) for s in symbols})[:MAX_SNAPSHOT_ROWS]
    snapshot_ts = _deterministic_snapshot_timestamp(snapshot_date)
    batches = _chunked(ordered_symbols, MAX_INGESTION_BATCH_SIZE)

    raw_rows: list[dict] = []
    filtered_rows: list[dict] = []
    attempts = 0
    dropped_due_to_batch_filter_count = 0
    duplicate_elision_count = 0
    canonicalized_batch_symbols: set[str] = set()
    canonicalized_row_symbols: set[str] = set()
    rejected_row_reasons: list[dict[str, str]] = []
    normalized_by_symbol: dict[str, tuple[object, ...]] = {}
    fetch_status = "not_started"
    response_type = "unknown"
    sample_response_keys: list[str] = []
    failure_stage = FAILURE_STAGE_FETCH_FAILED
    exception_type = ""
    exception_message = ""

    for batch in batches:
        batch_success = False
        canonical_batch = [canonicalize_symbol(s) for s in batch if canonicalize_symbol(s)]
        canonical_batch_set = set(canonical_batch)
        canonicalized_batch_symbols.update(canonical_batch_set)
        for _ in range(MAX_RETRY_ATTEMPTS):
            attempts += 1
            try:
                batch_rows = fetch_controlled_fmp_snapshot_batch(canonical_batch, fetch_batch)
                fetch_status = "ok"
                response_type = "list"
                if not sample_response_keys:
                    sample_response_keys = _sample_response_keys(batch_rows)
                raw_rows.extend(deepcopy(batch_rows))
                for row in batch_rows:
                    row_symbol = canonicalize_symbol(row.get("symbol", ""))
                    if row_symbol:
                        canonicalized_row_symbols.add(row_symbol)
                    if not row_symbol or row_symbol not in canonical_batch_set:
                        dropped_due_to_batch_filter_count += 1
                        if len(rejected_row_reasons) < 25:
                            rejected_row_reasons.append({
                                "symbol": row_symbol,
                                "rejection_reason": "symbol_not_in_canonicalized_batch",
                            })
                        continue
                    normalized_candidate = _normalize_row(row, snapshot_ts)
                    duplicate_identity = _normalized_duplicate_identity(normalized_candidate)
                    if row_symbol in normalized_by_symbol and normalized_by_symbol[row_symbol] == duplicate_identity:
                        duplicate_elision_count += 1
                        if len(rejected_row_reasons) < 25:
                            rejected_row_reasons.append({
                                "symbol": row_symbol,
                                "rejection_reason": "duplicate_symbol_after_canonicalization",
                            })
                        continue
                    normalized_by_symbol.setdefault(row_symbol, duplicate_identity)
                    filtered_rows.append(row)
                batch_success = True
                break
            except InvalidFmpPayloadShape as exc:
                fetch_status = "failed"
                response_type = exc.response_type
                if not sample_response_keys:
                    sample_response_keys = exc.sample_response_keys
                failure_stage = FAILURE_STAGE_INVALID_PAYLOAD_SHAPE
                exception_type = type(exc).__name__
                exception_message = _bounded_exception_message(exc)
                continue
            except Exception as exc:
                fetch_status = "failed"
                failure_stage = FAILURE_STAGE_FETCH_FAILED
                exception_type = type(exc).__name__
                exception_message = _bounded_exception_message(exc)
                continue
        if not batch_success:
            return {
                "status": "failed_closed",
                "snapshot_ts": snapshot_ts,
                "attempts": attempts,
                "batches": len(batches),
                "ingestion_boundary_diagnostics": _base_ingestion_boundary_diagnostics(
                    fetch_status=fetch_status,
                    response_type=response_type,
                    raw_row_count=len(raw_rows),
                    accepted_row_count=len(filtered_rows),
                    rejected_row_count=dropped_due_to_batch_filter_count + duplicate_elision_count,
                    sample_response_keys=sample_response_keys,
                    failure_stage=failure_stage,
                    exception_type=exception_type,
                    exception_message=exception_message,
                    canonicalized_batch_symbols=canonicalized_batch_symbols,
                    canonicalized_row_symbols=canonicalized_row_symbols,
                    dropped_due_to_batch_filter_count=dropped_due_to_batch_filter_count,
                    duplicate_elision_count=duplicate_elision_count,
                    rejected_row_reasons=rejected_row_reasons,
                ),
                "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
            }

    ingestion_boundary_diagnostics = _base_ingestion_boundary_diagnostics(
        fetch_status=fetch_status,
        response_type=response_type,
        raw_row_count=len(raw_rows),
        accepted_row_count=len(filtered_rows),
        rejected_row_count=dropped_due_to_batch_filter_count + duplicate_elision_count,
        sample_response_keys=sample_response_keys,
        failure_stage=FAILURE_STAGE_SUCCESS,
        canonicalized_batch_symbols=canonicalized_batch_symbols,
        canonicalized_row_symbols=canonicalized_row_symbols,
        dropped_due_to_batch_filter_count=dropped_due_to_batch_filter_count,
        duplicate_elision_count=duplicate_elision_count,
        rejected_row_reasons=rejected_row_reasons,
    )
    try:
        normalized = [_normalize_row(r, snapshot_ts) for r in filtered_rows if canonicalize_symbol(r.get("symbol", ""))]
        normalized = sorted(normalized, key=lambda r: r["symbol"])[:MAX_SNAPSHOT_ROWS]
    except Exception as exc:
        ingestion_boundary_diagnostics["failure_stage"] = FAILURE_STAGE_NORMALIZATION_FAILED
        ingestion_boundary_diagnostics["exception_type"] = type(exc).__name__
        ingestion_boundary_diagnostics["exception_message"] = _bounded_exception_message(exc)
        return {
            "status": "failed_closed",
            "snapshot_ts": snapshot_ts,
            "attempts": attempts,
            "batches": len(batches),
            "ingestion_boundary_diagnostics": ingestion_boundary_diagnostics,
            "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
        }
    integrity = _integrity_validate(normalized, ordered_symbols)
    if not integrity["is_valid"]:
        ingestion_boundary_diagnostics["failure_stage"] = _classify_integrity_failure(integrity, ingestion_boundary_diagnostics)
        ingestion_boundary_diagnostics["accepted_row_count"] = len(normalized)
        ingestion_boundary_diagnostics["rejected_row_count"] = max(0, ingestion_boundary_diagnostics["raw_row_count"] - len(normalized))
        return {
            "status": "failed_closed",
            "snapshot_ts": snapshot_ts,
            "attempts": attempts,
            "batches": len(batches),
            "integrity": integrity,
            "ingestion_boundary_diagnostics": ingestion_boundary_diagnostics,
            "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
        }

    ingestion_boundary_diagnostics["accepted_row_count"] = len(normalized)
    ingestion_boundary_diagnostics["rejected_row_count"] = max(0, ingestion_boundary_diagnostics["raw_row_count"] - len(normalized))
    snapshot_identity = _compute_snapshot_identity(normalized, snapshot_ts)
    surfaces = build_normalized_operational_surfaces(normalized, snapshot_ts, snapshot_identity)
    payload = build_operator_payloads(surfaces)
    return {
        "status": "ok",
        "snapshot_ts": snapshot_ts,
        "attempts": attempts,
        "batches": len(batches),
        "integrity": integrity,
        "ingestion_boundary_diagnostics": ingestion_boundary_diagnostics,
        "snapshot_identity": snapshot_identity,
        "rows": normalized,
        "surfaces": surfaces,
        "operator_payload": payload,
        "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
    }


def _classify_ecosystem_posture(ordered: Sequence[dict]) -> dict:
    n = max(len(ordered), 1)
    avg_vol = sum(r["volatility_structure"] for r in ordered) / n
    avg_val = sum(r["valuation_structure"] for r in ordered) / n
    avg_prof = sum(r["profitability_structure"] for r in ordered) / n
    avg_lev = sum(r["leverage_liquidity_structure"] for r in ordered) / n
    avg_disp = sum(r["breadth_dispersion_structure"] for r in ordered) / n
    valuation_profitability_gap = avg_val - avg_prof
    resilience_gap = avg_prof - avg_lev
    contradiction_pressure = max(0.0, valuation_profitability_gap) + max(0.0, avg_vol - 1.5)
    dispersion_pressure = max(0.0, avg_disp - 0.7) + max(0.0, avg_vol - 1.8)
    reasons = []
    if resilience_gap >= 0.4 and avg_vol <= 1.1 and avg_disp <= 0.4:
        posture = "stable_resilient"
        reasons.append("high_resilience_low_volatility")
    elif contradiction_pressure >= 1.4 and resilience_gap < 0.0:
        posture = "fragile"
        reasons.append("valuation_pressure_with_negative_resilience")
    elif dispersion_pressure >= 0.8:
        posture = "fragmented_pressure"
        reasons.append("high_dispersion_volatility_pressure")
    elif valuation_profitability_gap >= 0.9 or resilience_gap < 0.1:
        posture = "pressure_building"
        reasons.append("valuation_profitability_gap_or_thin_resilience")
    else:
        posture = "balanced"
        reasons.append("moderate_structural_balance")
    return {
        "posture": posture,
        "drivers": {
            "average_volatility": round(avg_vol, 6),
            "valuation_profitability_gap": round(valuation_profitability_gap, 6),
            "profitability_leverage_resilience_gap": round(resilience_gap, 6),
            "breadth_dispersion_pressure": round(dispersion_pressure, 6),
            "contradiction_pressure": round(contradiction_pressure, 6),
            "resilience_pressure": round(max(0.0, -resilience_gap), 6),
            "reasons": reasons,
        },
    }


def build_normalized_operational_surfaces(rows: Sequence[dict], snapshot_ts: str, snapshot_identity: dict | None = None) -> dict:
    ordered = sorted((deepcopy(r) for r in rows), key=lambda r: (r["symbol"], r["snapshot_ts"]))
    avg_vol = sum(r["volatility_structure"] for r in ordered) / max(len(ordered), 1)
    avg_val = sum(r["valuation_structure"] for r in ordered) / max(len(ordered), 1)
    avg_prof = sum(r["profitability_structure"] for r in ordered) / max(len(ordered), 1)
    avg_lev = sum(r["leverage_liquidity_structure"] for r in ordered) / max(len(ordered), 1)

    posture = _classify_ecosystem_posture(ordered)
    return {
        "snapshot_identity": deepcopy(snapshot_identity or {}),
        "ecosystem_state_snapshot": ordered,
        "propagation_state_snapshot": [{"snapshot_ts": snapshot_ts, "avg_volatility": round(avg_vol, 6)}],
        "contradiction_state_snapshot": [{"snapshot_ts": snapshot_ts, "valuation_minus_profitability": round(avg_val - avg_prof, 6)}],
        "resilience_state_snapshot": [{"snapshot_ts": snapshot_ts, "resilience_index": round(max(0.0, avg_prof - avg_lev), 6)}],
        "continuity_state_snapshot": [{"snapshot_ts": snapshot_ts, "continuity_marker": sha256(snapshot_ts.encode("utf-8")).hexdigest()[:12]}],
        "ecosystem_posture_snapshot": [{"snapshot_ts": snapshot_ts, "posture": posture["posture"], "drivers": posture["drivers"]}],
    }


def accumulate_longitudinal_continuity(history: Sequence[dict], new_snapshot: dict) -> dict:
    combined = sorted([*deepcopy(history), deepcopy(new_snapshot)], key=lambda r: r["snapshot_ts"])
    retained = combined[-MAX_CONTINUITY_WINDOW_DAYS:]
    return {
        "continuity_history": retained,
        "continuity_retention_metadata": {
            "continuity_window_size": len(retained),
            "max_continuity_window_days": MAX_CONTINUITY_WINDOW_DAYS,
            "retention_truncated": len(combined) > MAX_CONTINUITY_WINDOW_DAYS,
            "earliest_snapshot_retained": retained[0]["snapshot_ts"] if retained else None,
            "latest_snapshot_retained": retained[-1]["snapshot_ts"] if retained else None,
            "snapshots_suppressed_by_retention": max(0, len(combined) - len(retained)),
        },
    }


def build_operator_payloads(surfaces: dict) -> dict:
    eco_rows = surfaces["ecosystem_state_snapshot"][:MAX_DASHBOARD_PAYLOAD_ROWS]
    top_pressure = sorted(eco_rows, key=lambda r: r["volatility_structure"], reverse=True)[:MAX_STRUCTURAL_SUMMARY_ITEMS]
    top_resilience = sorted(eco_rows, key=lambda r: r["profitability_structure"] - r["leverage_liquidity_structure"], reverse=True)[:MAX_STRUCTURAL_SUMMARY_ITEMS]

    return {
        "daily_ecosystem_posture": surfaces["ecosystem_posture_snapshot"],
        "snapshot_identity": surfaces.get("snapshot_identity", {}),
        "dominant_structural_pressures": [{"symbol": r["symbol"], "volatility_structure": r["volatility_structure"]} for r in top_pressure],
        "strongest_resilience_pathways": [{"symbol": r["symbol"], "resilience_gap": round(r["profitability_structure"] - r["leverage_liquidity_structure"], 6)} for r in top_resilience],
        "fragmentation_hotspots": [{"symbol": r["symbol"], "breadth_dispersion_structure": r["breadth_dispersion_structure"]} for r in top_pressure],
        "transition_state_summaries": surfaces["propagation_state_snapshot"],
        "continuity_summaries": surfaces["continuity_state_snapshot"],
        "normalization_observations": {"row_count": len(eco_rows), "bounded": len(eco_rows) <= MAX_DASHBOARD_PAYLOAD_ROWS},
        "compression_observability": {
            "input_rows": len(surfaces["ecosystem_state_snapshot"]),
            "emitted_payload_rows": len(eco_rows),
            "max_dashboard_payload_rows": MAX_DASHBOARD_PAYLOAD_ROWS,
            "suppressed_rows": max(0, len(surfaces["ecosystem_state_snapshot"]) - len(eco_rows)),
            "compression_ratio": round(len(eco_rows) / max(len(surfaces["ecosystem_state_snapshot"]), 1), 6),
            "structural_summary_limit": MAX_STRUCTURAL_SUMMARY_ITEMS,
            "summary_items_emitted": len(top_pressure),
        },
    }


OPS_LIVE1B_UNIVERSE = (
    "AAPL","MSFT","NVDA","GOOGL","AMZN","META","ORCL","CRM","CSCO","ADBE",
    "JPM","BAC","WFC","GS","MS","BLK",
    "UNH","JNJ","PFE","MRK","ABBV","TMO",
    "XOM","CVX","SLB","NEE","DUK","SO",
    "CAT","DE","GE","HON","BA","LMT",
    "WMT","COST","PG","KO","PEP","MCD",
    "AMT","PLD","SPG","LIN","SHW","FCX","NEM","UPS","FDX","DIS",
)
OPS_LIVE1B_UNIVERSE_CAP = 50
OPS_LIVE1B_OBSERVATION_MODE = "controlled_operational_observation"


def get_ops_live1b_controlled_universe() -> list[str]:
    ordered = sorted(set(OPS_LIVE1B_UNIVERSE))
    return ordered[:OPS_LIVE1B_UNIVERSE_CAP]


def _compute_universe_metadata(rows: Sequence[dict], symbols: Sequence[str]) -> dict:
    sector_counts = {}
    subsector_counts = {}
    for r in rows:
        sector = str(r.get("sector", "UNKNOWN"))
        subsector = str(r.get("subsector", "UNKNOWN"))
        sector_counts[sector] = sector_counts.get(sector, 0) + 1
        subsector_counts[subsector] = subsector_counts.get(subsector, 0) + 1
    ordered_symbols = list(symbols)
    checksum = sha256("|".join(ordered_symbols).encode("utf-8")).hexdigest()[:16]
    return {
        "universe_size": len(ordered_symbols),
        "sector_coverage": [{"sector": k, "count": sector_counts[k]} for k in sorted(sector_counts)],
        "subsector_coverage": [{"subsector": k, "count": subsector_counts[k]} for k in sorted(subsector_counts)],
        "universe_checksum": checksum,
        "observation_mode": OPS_LIVE1B_OBSERVATION_MODE,
    }


def build_ops_live1b_canonical_payload(ingest_result: dict, universe_symbols: Sequence[str]) -> dict:
    rows = sorted(deepcopy(ingest_result.get("rows", [])), key=lambda r: r["symbol"])
    snapshot_ts = ingest_result.get("snapshot_ts")
    snapshot_id = ingest_result.get("snapshot_identity", {}).get("snapshot_id", "")
    universe_metadata = _compute_universe_metadata(rows, universe_symbols)
    sector_rollup = {}
    for r in rows:
        sector = r["sector"]
        entry = sector_rollup.setdefault(sector, {"symbols": 0, "avg_volatility": 0.0, "avg_resilience_gap": 0.0})
        entry["symbols"] += 1
        entry["avg_volatility"] += r["volatility_structure"]
        entry["avg_resilience_gap"] += (r["profitability_structure"] - r["leverage_liquidity_structure"])
    sector_summary_rows = []
    for sector in sorted(sector_rollup):
        c = sector_rollup[sector]["symbols"]
        sector_summary_rows.append({
            "snapshot_id": snapshot_id,
            "snapshot_ts": snapshot_ts,
            "sector": sector,
            "symbol_count": c,
            "avg_volatility": round(sector_rollup[sector]["avg_volatility"] / max(c,1), 6),
            "avg_resilience_gap": round(sector_rollup[sector]["avg_resilience_gap"] / max(c,1), 6),
        })
    op = ingest_result.get("operator_payload", {})
    ingestion_boundary_diagnostics = deepcopy(ingest_result.get("ingestion_boundary_diagnostics", {}))
    diagnostics = {
        "symbols_requested": len(universe_symbols),
        "symbols_successfully_normalized": len(rows),
        "symbols_failed_closed": max(0, len(universe_symbols) - len(rows)),
        "missing_fields": len(ingest_result.get("integrity", {}).get("missing_required_fields", [])),
        "null_fields": 0,
        "fallback_fields_used": 0,
        "invalid_values": len(ingest_result.get("integrity", {}).get("invalid_numeric_values", [])) + len(ingest_result.get("integrity", {}).get("invalid_financial_values", [])),
        "compression_ratio": op.get("compression_observability", {}).get("compression_ratio", 0.0),
        "payload_row_counts": {
            "symbol_snapshot_rows": len(rows),
            "sector_summary_rows": len(sector_summary_rows),
            "pressure_rows": len(op.get("dominant_structural_pressures", [])),
            "resilience_rows": len(op.get("strongest_resilience_pathways", [])),
        },
        "sector_distribution": universe_metadata["sector_coverage"],
        "data_completeness_summary": round((len(rows)/max(len(universe_symbols),1))*100.0,6),
        "normalization_completeness_percentage": round((len(rows)/max(len(universe_symbols),1))*100.0,6),
        "fallback_usage_percentage": 0.0,
        "ingestion_boundary_diagnostics": ingestion_boundary_diagnostics,
    }
    snapshot_metadata_rows = [{"snapshot_id": snapshot_id, "snapshot_ts": snapshot_ts, **universe_metadata}]
    symbol_snapshot_rows = [{"snapshot_id": snapshot_id, **r} for r in rows]
    integrity_rows = [{"snapshot_id": snapshot_id, "status": ingest_result.get("status"), "row_count": len(rows), "is_valid": ingest_result.get("integrity", {}).get("is_valid", False)}]
    governance_rows = [{"snapshot_id": snapshot_id, **deepcopy(GOVERNANCE_BOUNDARIES)}]
    compression_rows = [{"snapshot_id": snapshot_id, **deepcopy(op.get("compression_observability", {}))}]
    canonical = {
        "snapshot_metadata_rows": snapshot_metadata_rows,
        "symbol_snapshot_rows": symbol_snapshot_rows,
        "sector_summary_rows": sector_summary_rows,
        "pressure_rows": [{"snapshot_id": snapshot_id, **r} for r in op.get("dominant_structural_pressures", [])],
        "resilience_rows": [{"snapshot_id": snapshot_id, **r} for r in op.get("strongest_resilience_pathways", [])],
        "fragmentation_rows": [{"snapshot_id": snapshot_id, **r} for r in op.get("fragmentation_hotspots", [])],
        "continuity_rows": [{"snapshot_id": snapshot_id, **r} for r in op.get("continuity_summaries", [])],
        "integrity_rows": integrity_rows,
        "governance_rows": governance_rows,
        "compression_rows": compression_rows,
    }
    streamlit = {
        "streamlit_summary_cards": [{"label": "posture", "value": op.get("daily_ecosystem_posture", [{}])[0].get("posture", "unknown")}, {"label": "symbols", "value": len(rows)}],
        "streamlit_sector_summary": sector_summary_rows,
        "streamlit_pressure_table": canonical["pressure_rows"],
        "streamlit_resilience_table": canonical["resilience_rows"],
        "streamlit_fragmentation_table": canonical["fragmentation_rows"],
        "streamlit_continuity_panel": canonical["continuity_rows"],
        "streamlit_integrity_panel": integrity_rows,
        "streamlit_governance_panel": governance_rows,
        "streamlit_snapshot_metadata": snapshot_metadata_rows,
    }
    return {
        "snapshot_id": snapshot_id,
        "snapshot_ts": snapshot_ts,
        "observation_mode": OPS_LIVE1B_OBSERVATION_MODE,
        "supabase_write_enabled": False,
        "scheduling_enabled": False,
        "orchestration_enabled": False,
        "streaming_enabled": False,
        "canonical_tables": canonical,
        "streamlit_payloads": streamlit,
        "diagnostics": diagnostics,
        "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
    }


def run_ops_live1b_controlled_50_symbol_operational_ingest(*, snapshot_date: str, output_path: str, fetch_batch: Callable[[Sequence[str]], Iterable[dict]] | None = None) -> dict:
    universe = get_ops_live1b_controlled_universe()
    if fetch_batch is None:
        api_key = os.getenv("FMP_API_KEY", "")
        if not api_key:
            raise RuntimeError("FMP_API_KEY missing; OPS-LIVE-1B fails closed")
        fetch_batch = build_live_fmp_fetcher(api_key)
    ingest_result = ingest_controlled_daily_snapshot(universe, snapshot_date, fetch_batch)
    payload = build_ops_live1b_canonical_payload(ingest_result, universe)
    report = {
        "status": ingest_result.get("status"),
        "snapshot_identity": ingest_result.get("snapshot_identity", {}),
        "universe": universe,
        "universe_metadata": _compute_universe_metadata(ingest_result.get("rows", []), universe),
        "ingestion_boundary_diagnostics": deepcopy(ingest_result.get("ingestion_boundary_diagnostics", {})),
        "ops_live1b_payload": payload,
        "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
    }
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    Path(output_path).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    return report
