from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from datetime import date, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence
from urllib.parse import urlencode, quote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError
import inspect
from collections import Counter

from transmission_layers.expectation_failure.real_data.ops_hist_cache_raw_fmp import (
    cached_row_to_historical_input_row,
    identify_missing_symbol_dates,
    normalize_fmp_historical_price_row,
    raw_cache_write_readiness,
    read_cached_historical_prices,
    summarize_write_result,
    write_raw_historical_prices,
)

from transmission_layers.expectation_failure.real_data.ops_live1_controlled_ecosystem_ingestion import (
    GOVERNANCE_BOUNDARIES,
    build_live_fmp_fetcher,
    build_normalized_operational_surfaces,
    build_operator_payloads,
    get_ops_live1b_controlled_universe,
    ingest_controlled_daily_snapshot,
)

DEFAULT_HIST_WINDOW_DAYS = 30
MAX_HIST_WINDOW_DAYS = 90
MAX_SNAPSHOTS_PER_RUN = 90
OPS_HIST1_SCHEMA_VERSION = "ops_hist1_v1"
OPS_HIST1_OBSERVATION_MODE = "controlled_historical_observation"
PROGRESS_INTERVAL_DEFAULT = 5
PROGRESS_INTERVAL_MIN = 1
PROGRESS_INTERVAL_MAX = 20
FMP_HTTP_TIMEOUT_SECONDS = 20
FMP_HTTP_MAX_ATTEMPTS = 3
SNAPSHOT_HEARTBEAT_SECONDS = 60
DEFAULT_TELEMETRY_MAX_SAMPLES = 25
TELEMETRY_MAX_SAMPLES_HARD_CAP = 100

FMP_STABLE_HISTORICAL_PRICE_URL = "https://financialmodelingprep.com/stable/historical-price-eod/full"
FMP_STABLE_HISTORICAL_PRICE_LIGHT_URL = "https://financialmodelingprep.com/stable/historical-price-eod/light"
FMP_LEGACY_HISTORICAL_PRICE_URL = "https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
FMP_LEGACY_HISTORICAL_MARKET_CAP_URL = "https://financialmodelingprep.com/api/v3/historical-market-capitalization/{symbol}"


def _build_fmp_url(base_url: str, params: dict[str, str]) -> str:
    return f"{base_url}?{urlencode(params)}"


def _bounded_telemetry_limit(max_samples: int | None = None) -> int:
    requested = DEFAULT_TELEMETRY_MAX_SAMPLES if max_samples is None else int(max_samples)
    return max(1, min(requested, TELEMETRY_MAX_SAMPLES_HARD_CAP))


def _sort_endpoint_failure_sample(sample: dict[str, Any]) -> tuple[Any, ...]:
    return (
        str(sample.get("requested_snapshot_date", "")),
        str(sample.get("symbol", "")),
        str(sample.get("endpoint_name", "")),
        int(sample.get("attempt_index", 0)),
    )


def _bounded_sleep_seconds(attempt_index: int) -> float:
    return min(1.0 * attempt_index, 2.0)


def _request_json_with_retries(*, url: str, endpoint_family: str, symbol: str, snapshot_date: str, timeout_seconds: int = FMP_HTTP_TIMEOUT_SECONDS, max_attempts: int = FMP_HTTP_MAX_ATTEMPTS) -> Any:
    last_exc: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        try:
            with urlopen(url, timeout=timeout_seconds) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except HTTPError:
            raise
        except Exception as exc:
            last_exc = exc
            if attempt >= max_attempts:
                break
            time.sleep(_bounded_sleep_seconds(attempt))
    reason = "TIMEOUT" if isinstance(last_exc, TimeoutError) else ("URL_ERROR" if isinstance(last_exc, URLError) else "UNEXPECTED_ERROR")
    raise TimeoutError(
        "OPS-HIST-1 fails closed: request retries exhausted "
        f"(endpoint_family={endpoint_family}, symbol={symbol}, snapshot_date={snapshot_date}, "
        f"attempts={max_attempts}, timeout_seconds={timeout_seconds}, last_reason={reason})"
    )


def build_historical_fmp_fetcher(api_key: str) -> Callable[[Sequence[str], str], Iterable[dict]]:
    if not api_key:
        raise RuntimeError("FMP_API_KEY is required for historical mode")

    profile_cache: dict[str, dict[str, str]] = {}

    def _bounded_profile_failure_reason(exc: Exception) -> str:
        if isinstance(exc, HTTPError):
            return f"HTTP_{exc.code}"
        if isinstance(exc, URLError):
            return "URL_ERROR"
        if isinstance(exc, TimeoutError):
            return "TIMEOUT"
        return "UNEXPECTED_ERROR"

    def _fetch_profile(symbol: str, diagnostics: dict[str, Any]) -> dict[str, str]:
        sym = str(symbol).upper()
        if sym in profile_cache:
            return profile_cache[sym]
        profile_q = urlencode({"symbol": sym, "apikey": api_key})
        try:
            payload = _request_json_with_retries(
                url=f"https://financialmodelingprep.com/stable/profile?{profile_q}",
                endpoint_family="stable_profile",
                symbol=sym,
                snapshot_date=diagnostics.get("current_snapshot_date", "unknown"),
            )
            diagnostics["profile_records_requested"] += 1
            if isinstance(payload, list) and payload:
                row = payload[0] if isinstance(payload[0], dict) else {}
            elif isinstance(payload, dict):
                row = payload
            else:
                row = {}
            sector = str(row.get("sector") or "unknown")
            industry = str(row.get("industry") or "unknown")
            profile = {"sector": sector, "industry": industry}
            if sector != "unknown" or industry != "unknown":
                diagnostics["profile_records_returned"] += 1
            profile_cache[sym] = profile
            return profile
        except Exception as exc:  # best effort only
            diagnostics["profile_records_requested"] += 1
            diagnostics["profile_fetch_failure_count"] += 1
            reason = _bounded_profile_failure_reason(exc)
            diagnostics["profile_fetch_failure_reasons"][reason] = diagnostics["profile_fetch_failure_reasons"].get(reason, 0) + 1
            diagnostics["profile_enrichment_status"] = "failed"
            diagnostics["sector_industry_fallback_used"] = True
            profile = {"sector": "unknown", "industry": "unknown"}
            profile_cache[sym] = profile
            return profile

    def _fetch(symbols: Sequence[str], snapshot_date: str, progress_callback: Callable[[int, str, str], None] | None = None) -> list[dict]:
        snapshot_dt = date.fromisoformat(snapshot_date)
        lookback_from = (snapshot_dt - timedelta(days=7)).isoformat()
        run_diag: dict[str, Any] = {
            "cache_enabled": str(os.getenv("OPS_HIST_RAW_CACHE_ENABLED", "false")).lower() == "true",
            "cache_write_enabled": str(os.getenv("OPS_HIST_RAW_CACHE_WRITE_ENABLED", "false")).lower() == "true",
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_rows_written": 0,
            "cache_read_failures": 0,
            "cache_write_failures": 0,
            "requested_symbol_dates_count": 0,
            "cache_lookup_attempted_count": 0,
            "valid_cached_rows_count": 0,
            "malformed_cached_rows_count": 0,
            "missing_symbol_dates_count": 0,
            "fetched_symbol_dates_count": 0,
            "write_attempted_rows_count": 0,
            "write_success_rows_count": 0,
            "write_failed_rows_count": 0,
            "cache_write_status": "not_attempted",
            "cache_write_confirmation_limited": False,
            "cache_write_error_reason_counts": {},
            "sample_symbol_date_trace": {},

            "fmp_endpoint_family_used": "stable/historical-price-eod/full + legacy/historical-market-capitalization + stable/profile",
            "historical_price_endpoint_family": "stable_historical_price_eod_full",
            "primary_endpoint_family": "stable_historical_price_eod_full",
            "fallback_endpoint_family": "legacy_historical_price_full",
            "historical_price_url_shape_valid": True,
            "historical_price_query_parameters_present": True,
            "historical_price_endpoint_status": "ok",
            "historical_market_cap_endpoint_status": "ok",
            "historical_market_cap_reconciliation_policy": "exact_or_nearest_prior_within_5_calendar_days",
            "historical_price_http_status_counts": {},
            "historical_price_failure_reasons": {},
            "historical_price_records_requested": 0,
            "historical_price_records_returned": 0,
            "historical_price_records_matched_to_snapshot_date": 0,
            "historical_price_symbols_succeeded": 0,
            "historical_price_symbols_failed": 0,
            "sample_historical_price_raw_keys_observed": [],
            "historical_price_endpoint_status_counts": {},
            "historical_price_symbol_diagnostics": [],
            "profile_endpoint_status": "ok",
            "profile_enrichment_status": "ok",
            "profile_records_requested": 0,
            "profile_records_returned": 0,
            "profile_fetch_failure_count": 0,
            "profile_fetch_failure_reasons": {},
            "sector_industry_fallback_used": False,
            "current_snapshot_date": snapshot_date,
        }
        cache_only_validation = str(os.getenv("OPS_HIST_CACHE_ONLY_VALIDATION", "false")).lower() == "true"
        def _record_price_failure(reason: str, http_status: int | None = None) -> None:
            run_diag["historical_price_failure_reasons"][reason] = run_diag["historical_price_failure_reasons"].get(reason, 0) + 1
            if http_status is not None:
                key = f"HTTP_{http_status}"
                run_diag["historical_price_http_status_counts"][key] = run_diag["historical_price_http_status_counts"].get(key, 0) + 1

        def _bounded_http_reason(exc: Exception) -> str:
            if isinstance(exc, HTTPError):
                return f"HTTP_{exc.code}"
            if isinstance(exc, URLError):
                return "URL_ERROR"
            if isinstance(exc, TimeoutError):
                return "TIMEOUT"
            return "UNEXPECTED_ERROR"

        def _parse_price_records(payload: Any) -> list[dict[str, Any]]:
            if isinstance(payload, list):
                return [row for row in payload if isinstance(row, dict)]
            if isinstance(payload, dict):
                if isinstance(payload.get("historical"), list):
                    return [row for row in payload.get("historical", []) if isinstance(row, dict)]
                for k in ("data", "results"):
                    if isinstance(payload.get(k), list):
                        return [row for row in payload.get(k, []) if isinstance(row, dict)]
                for v in payload.values():
                    if isinstance(v, list) and all(isinstance(x, dict) for x in v):
                        return [row for row in v if isinstance(row, dict)]
                if any(k in payload for k in ("date", "close", "adjClose", "price")):
                    return [payload]
            return []

        def _top_level_shape(payload: Any) -> tuple[str, list[str]]:
            if isinstance(payload, list):
                return "list", []
            if isinstance(payload, dict):
                return "dict", list(payload.keys())[:10]
            return "other", []

        def _select_price_row(prices: list[dict[str, Any]], requested: str) -> tuple[dict[str, Any], dict[str, Any]]:
            meta = {
                "requested_snapshot_date": requested,
                "exact_date_match_found": False,
                "selected_record_date": None,
                "date_reconciliation_used": False,
                "date_reconciliation_distance_days": None,
                "date_reconciliation_policy": None,
            }
            exact = [p for p in prices if str(p.get("date", "")) == requested]
            if exact:
                meta["exact_date_match_found"] = True
                meta["selected_record_date"] = requested
                return exact[0], meta
            requested_dt = date.fromisoformat(requested)
            prior_candidates: list[tuple[int, dict[str, Any]]] = []
            for p in prices:
                ds = str(p.get("date", ""))
                try:
                    dt = date.fromisoformat(ds)
                except Exception:
                    continue
                diff = (requested_dt - dt).days
                if 0 < diff <= 5:
                    prior_candidates.append((diff, p))
            if prior_candidates:
                prior_candidates.sort(key=lambda x: x[0])
                diff, row = prior_candidates[0]
                meta["selected_record_date"] = row.get("date")
                meta["date_reconciliation_used"] = True
                meta["date_reconciliation_distance_days"] = diff
                meta["date_reconciliation_policy"] = "nearest_prior_within_5_calendar_days"
                return row, meta
            return {}, meta

        def _parse_market_cap_records(payload: Any) -> list[dict[str, Any]]:
            if isinstance(payload, list):
                return [row for row in payload if isinstance(row, dict)]
            if isinstance(payload, dict):
                if isinstance(payload.get("historical"), list):
                    return [row for row in payload.get("historical", []) if isinstance(row, dict)]
                for k in ("data", "results"):
                    if isinstance(payload.get(k), list):
                        return [row for row in payload.get(k, []) if isinstance(row, dict)]
                if "marketCap" in payload:
                    return [payload]
            return []

        def _select_market_cap_row(records: list[dict[str, Any]], requested: str) -> tuple[dict[str, Any], dict[str, Any]]:
            meta = {
                "market_cap_exact_match_found": False,
                "market_cap_reconciled_prior_date": None,
                "market_cap_reconciliation_distance_days": None,
                "market_cap_reconciliation_policy": "exact_or_nearest_prior_within_5_calendar_days",
                "market_cap_missing_after_reconciliation": True,
            }
            exact = [r for r in records if str(r.get("date", "")) == requested and r.get("marketCap") is not None]
            if exact:
                meta["market_cap_exact_match_found"] = True
                meta["market_cap_missing_after_reconciliation"] = False
                return exact[0], meta
            requested_dt = date.fromisoformat(requested)
            prior_candidates: list[tuple[int, dict[str, Any]]] = []
            for r in records:
                if r.get("marketCap") is None:
                    continue
                ds = str(r.get("date", ""))
                try:
                    dt = date.fromisoformat(ds)
                except Exception:
                    continue
                diff = (requested_dt - dt).days
                if 0 < diff <= 5:
                    prior_candidates.append((diff, r))
            if prior_candidates:
                prior_candidates.sort(key=lambda x: x[0])
                diff, row = prior_candidates[0]
                meta["market_cap_reconciled_prior_date"] = row.get("date")
                meta["market_cap_reconciliation_distance_days"] = diff
                meta["market_cap_missing_after_reconciliation"] = False
                return row, meta
            return {}, meta

        rows: list[dict] = []
        requested_total = len([s for s in symbols if str(s).strip()])
        run_diag["requested_symbol_dates_count"] = requested_total
        run_diag["cache_lookup_attempted_count"] = requested_total
        cached_rows, cache_read_failures = read_cached_historical_prices(symbols, [snapshot_date])
        run_diag["cache_read_failures"] = int(cache_read_failures)
        valid_cached_rows = [r for r in cached_rows if str(r.get("price_date", "")) == snapshot_date]
        run_diag["valid_cached_rows_count"] = len(valid_cached_rows)
        run_diag["malformed_cached_rows_count"] = max(0, len(cached_rows) - len(valid_cached_rows))
        cached_by_symbol = {str(r.get("symbol", "")).upper(): r for r in valid_cached_rows}
        missing_map = identify_missing_symbol_dates(symbols, [snapshot_date], valid_cached_rows)
        run_diag["missing_symbol_dates_count"] = sum(len(v) for v in missing_map.values())
        trace_symbol = str(symbols[0]).upper() if symbols else ""
        trace = {"cache_key": f"fmp|{trace_symbol}|{snapshot_date}", "read_before_fetch": "miss", "fetched_from_fmp": False, "write_attempted": False, "write_confirmed": None, "read_after_write": "not_attempted"}
        if trace_symbol in cached_by_symbol:
            trace["read_before_fetch"] = "hit"
        elif run_diag["malformed_cached_rows_count"] > 0:
            trace["read_before_fetch"] = "malformed"
        run_diag["sample_symbol_date_trace"] = trace
        readiness = {"ready": True, "reason": "not_required"}
        if run_diag.get("cache_write_enabled"):
            readiness = raw_cache_write_readiness()
        run_diag["raw_cache_readiness"] = readiness
        if run_diag.get("cache_write_enabled") and not readiness.get("ready", False):
            raise RuntimeError(
                "OPS-HIST-1 fails closed: raw cache write readiness failed; "
                f"reason={readiness.get('reason')}"
            )

        endpoint_candidates = (
            ("stable_historical_price_eod_full", FMP_STABLE_HISTORICAL_PRICE_URL, False),
            ("stable_historical_price_eod_light", FMP_STABLE_HISTORICAL_PRICE_LIGHT_URL, False),
            ("legacy_historical_price_full", FMP_LEGACY_HISTORICAL_PRICE_URL, True),
        )
        fresh_cache_candidates: list[dict[str, Any]] = []
        for symbol_index, symbol in enumerate(symbols, start=1):
            if sym := str(symbol).upper():
                if sym in cached_by_symbol:
                    c = cached_by_symbol[sym]
                    run_diag["cache_hits"] += 1
                    profile = {"sector": "unknown", "industry": "unknown"} if cache_only_validation else _fetch_profile(sym, run_diag)
                    rows.append(
                        cached_row_to_historical_input_row(
                            c,
                            snapshot_date=snapshot_date,
                            sector=profile.get("sector", "unknown") or "unknown",
                            industry=profile.get("industry", "unknown") or "unknown",
                        )
                    )
                    continue
                run_diag["cache_misses"] += 1
                if cache_only_validation:
                    raise RuntimeError(
                        f"OPS-HIST-1 fails closed: cache-only validation missing cached row for symbol={sym} snapshot_date={snapshot_date}"
                    )
                run_diag["fetched_symbol_dates_count"] += 1
                if sym == trace_symbol:
                    run_diag["sample_symbol_date_trace"]["fetched_from_fmp"] = True
            sym = str(symbol).upper()
            run_diag["historical_price_records_requested"] += 1
            sym_diag: dict[str, Any] = {"symbol": sym, "requested_snapshot_date": snapshot_date, "endpoint_attempts": []}
            price_row: dict[str, Any] = {}
            sel_meta: dict[str, Any] = {}
            for endpoint_family, endpoint_url, symbol_in_path in endpoint_candidates:
                if progress_callback is not None:
                    progress_callback(symbol_index, sym, endpoint_family)
                params = {"from": lookback_from, "to": snapshot_date, "apikey": api_key}
                if not symbol_in_path:
                    params["symbol"] = sym
                url = _build_fmp_url(endpoint_url.format(symbol=quote(sym, safe="")), params)
                run_diag["historical_price_query_parameters_present"] = run_diag["historical_price_query_parameters_present"] and all(k in url for k in ["from=", "to=", "apikey="])
                payload = None
                status = "ok"
                try:
                    payload = _request_json_with_retries(
                        url=url,
                        endpoint_family=endpoint_family,
                        symbol=sym,
                        snapshot_date=snapshot_date,
                    )
                except Exception as exc:
                    if isinstance(exc, TimeoutError) and "request retries exhausted" in str(exc):
                        raise RuntimeError(str(exc))
                    status = _bounded_http_reason(exc)
                    run_diag["historical_price_endpoint_status"] = "degraded"
                    _record_price_failure(status, getattr(exc, "code", None))
                shape_type, shape_keys = _top_level_shape(payload)
                prices = _parse_price_records(payload)
                run_diag["historical_price_records_returned"] += len(prices)
                sample_record_keys = list(prices[0].keys())[:10] if prices else []
                sample_dates = [str(r.get("date")) for r in prices if r.get("date")][:5]
                selected, sel_meta = _select_price_row(prices, snapshot_date)
                attempt_diag = {
                    "endpoint_family": endpoint_family,
                    "http_status": status,
                    "response_top_level_type": shape_type,
                    "response_top_level_keys": shape_keys,
                    "record_count_returned": len(prices),
                    "sample_record_keys": sample_record_keys,
                    "sample_returned_dates": sample_dates,
                    **sel_meta,
                    "failure_reason": None,
                }
                if status != "ok":
                    attempt_diag["failure_reason"] = status
                elif not prices:
                    attempt_diag["failure_reason"] = "zero_records_returned"
                elif not selected:
                    attempt_diag["failure_reason"] = "missing_reconciled_historical_date"
                elif selected.get("adjClose") is None and selected.get("close") is None and selected.get("price") is None:
                    attempt_diag["failure_reason"] = "missing_price_field"
                if attempt_diag["failure_reason"] is None:
                    sym_diag["endpoint_attempts"].append(attempt_diag)
                    price_row = selected
                    run_diag["historical_price_symbols_succeeded"] += 1
                    run_diag["historical_price_endpoint_family"] = endpoint_family
                    run_diag["historical_price_records_matched_to_snapshot_date"] += 1 if sel_meta["exact_date_match_found"] else 0
                    break
                _record_price_failure(attempt_diag["failure_reason"])
                sym_diag["endpoint_attempts"].append(attempt_diag)
                run_diag["historical_price_endpoint_status_counts"][f"{endpoint_family}:{status}"] = run_diag["historical_price_endpoint_status_counts"].get(f"{endpoint_family}:{status}", 0) + 1
            if not price_row:
                run_diag["historical_price_symbols_failed"] += 1
            if len(sym_diag["endpoint_attempts"]) > 3:
                sym_diag["endpoint_attempts"] = sym_diag["endpoint_attempts"][:3]
            run_diag["historical_price_symbol_diagnostics"].append(sym_diag)

            mc_q = {"from": lookback_from, "to": snapshot_date, "apikey": api_key}
            mc_url = _build_fmp_url(FMP_LEGACY_HISTORICAL_MARKET_CAP_URL.format(symbol=sym), mc_q)
            mc_row: dict[str, Any] = {}
            mc_meta: dict[str, Any] = {
                "market_cap_exact_match_found": False,
                "market_cap_reconciled_prior_date": None,
                "market_cap_reconciliation_distance_days": None,
                "market_cap_reconciliation_policy": "exact_or_nearest_prior_within_5_calendar_days",
                "market_cap_missing_after_reconciliation": True,
            }
            try:
                mc = _request_json_with_retries(
                    url=mc_url,
                    endpoint_family="legacy_historical_market_cap",
                    symbol=sym,
                    snapshot_date=snapshot_date,
                )
                mc_records = _parse_market_cap_records(mc)
                mc_row, mc_meta = _select_market_cap_row(mc_records, snapshot_date)
            except Exception as exc:
                if isinstance(exc, TimeoutError) and "request retries exhausted" in str(exc):
                    raise RuntimeError(str(exc))
                run_diag["historical_market_cap_endpoint_status"] = "degraded"
            if mc_meta.get("market_cap_missing_after_reconciliation"):
                run_diag["historical_market_cap_endpoint_status"] = "degraded"
            profile = _fetch_profile(sym, run_diag)
            rows.append({
                "symbol": sym,
                "date": snapshot_date,
                "price": price_row.get("adjClose", price_row.get("close", price_row.get("price"))),
                "volume": price_row.get("volume"),
                "marketCap": mc_row.get("marketCap"),
                "sector": profile.get("sector", "unknown") or "unknown",
                "industry": profile.get("industry", "unknown") or "unknown",
                "historical_adapter_mode": "fmp_historical_price_plus_market_cap",
                **mc_meta,
            })
            normalized_cache_row = normalize_fmp_historical_price_row({"symbol": sym, "date": snapshot_date, "open": price_row.get("open"), "high": price_row.get("high"), "low": price_row.get("low"), "close": price_row.get("close"), "adjClose": price_row.get("adjClose", price_row.get("price")), "volume": price_row.get("volume")}, endpoint_family=run_diag.get("historical_price_endpoint_family"))
            if normalized_cache_row is not None and sym in missing_map:
                fresh_cache_candidates.append(normalized_cache_row)
        if run_diag.get("cache_write_enabled") and run_diag.get("cache_misses", 0) > 0:
            write_result = summarize_write_result(fresh_cache_candidates)
            run_diag["write_attempted_rows_count"] = int(write_result.get("write_attempted_rows", 0))
            run_diag["write_success_rows_count"] = write_result.get("write_success_rows")
            run_diag["write_failed_rows_count"] = int(write_result.get("write_failed_rows", 0))
            run_diag["cache_rows_written"] = int(write_result.get("write_success_rows") or 0)
            run_diag["cache_write_failures"] = int(write_result.get("write_failed_rows", 0))
            run_diag["cache_write_status"] = str(write_result.get("write_status", "unknown"))
            run_diag["cache_write_confirmation_limited"] = bool(write_result.get("write_confirmation_limited", False))
            run_diag["cache_write_error_reason_counts"] = dict(write_result.get("error_reason_counts", {}))
            run_diag["sample_symbol_date_trace"]["write_attempted"] = run_diag["write_attempted_rows_count"] > 0
            succ = write_result.get("write_success_rows")
            run_diag["sample_symbol_date_trace"]["write_confirmed"] = (None if succ is None else bool(succ))
            if run_diag["sample_symbol_date_trace"]["write_attempted"]:
                post_rows, _ = read_cached_historical_prices([trace_symbol], [snapshot_date])
                run_diag["sample_symbol_date_trace"]["read_after_write"] = "hit" if post_rows else "miss"
            if run_diag["write_attempted_rows_count"] == 0 and run_diag.get("historical_price_symbols_succeeded", 0) > 0:
                raise RuntimeError(
                    "OPS-HIST-1 fails closed: cache writes enabled and misses fetched "
                    "but no write attempts were made"
                )
        requested_total = run_diag["cache_hits"] + run_diag["cache_misses"]
        run_diag["cache_hit_ratio"] = round((run_diag["cache_hits"] / requested_total), 6) if requested_total else 0.0
        run_diag["fmp_requests_avoided_estimate"] = int(run_diag["cache_hits"])
        if run_diag["historical_price_symbols_succeeded"] == 0 and run_diag["cache_hits"] == 0:
            top_reasons = Counter(run_diag["historical_price_failure_reasons"]).most_common(3)
            raise RuntimeError(
                "OPS-HIST-1 fails closed: all symbols failed historical price fetch; "
                f"endpoint_status_counts={run_diag['historical_price_endpoint_status_counts']}; "
                f"top_failure_reasons={top_reasons}"
            )
        if run_diag["profile_fetch_failure_count"] > 0:
            run_diag["profile_endpoint_status"] = "degraded"
        _fetch.last_profile_diagnostics = run_diag
        return rows

    _fetch.last_profile_diagnostics = {}
    return _fetch



def _governance_flags() -> dict[str, Any]:
    flags = deepcopy(GOVERNANCE_BOUNDARIES)
    flags.update(
        {
            "historical_observation_mode": True,
            "schema_version": OPS_HIST1_SCHEMA_VERSION,
            "persistence_mode": "local_json_only",
            "supabase_write_enabled": False,
            "repo_writeback_enabled": False,
            "orchestration_enabled": False,
            "streaming_enabled": False,
        }
    )
    return flags


def _parse_date(d: str) -> date:
    return date.fromisoformat(d)


def _emit_ops_hist1_progress(lines: dict[str, Any]) -> None:
    print("[OPS-HIST-1]", flush=True)
    for key, value in lines.items():
        print(f"{key}={value}", flush=True)


def _emit_endpoint_summary(success_counts: dict[str, int], failure_counts: dict[str, int]) -> None:
    print("[OPS-HIST-1][historical_price]", flush=True)
    print(f"endpoint_success_counts={dict(sorted(success_counts.items()))}", flush=True)
    print(f"endpoint_failure_counts={dict(sorted(failure_counts.items()))}", flush=True)


def _bounded_progress_interval(progress_interval: int) -> int:
    if progress_interval < PROGRESS_INTERVAL_MIN:
        return PROGRESS_INTERVAL_MIN
    if progress_interval > PROGRESS_INTERVAL_MAX:
        return PROGRESS_INTERVAL_MAX
    return progress_interval


def deterministic_historical_window_dates(snapshot_date: str, window_days: int) -> list[str]:
    if window_days > MAX_HIST_WINDOW_DAYS:
        raise ValueError(f"historical window {window_days} exceeds max {MAX_HIST_WINDOW_DAYS}")
    end = _parse_date(snapshot_date)
    picked: list[str] = []
    cursor = end
    while len(picked) < window_days:
        if cursor.weekday() < 5:
            picked.append(cursor.isoformat())
        cursor -= timedelta(days=1)
    return sorted(picked)


def historical_window_checksum(
    dates: Sequence[str],
    universe: Sequence[str],
    window_days: int,
    schema_version: str = OPS_HIST1_SCHEMA_VERSION,
    observation_mode: str = OPS_HIST1_OBSERVATION_MODE,
) -> str:
    payload = {
        "window_dates": list(dates),
        "universe": list(universe),
        "window_days": int(window_days),
        "schema_version": schema_version,
        "observation_mode": observation_mode,
    }
    return sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:20]


def _deterministic_hist_snapshot_id(snapshot_date: str, universe_checksum: str) -> str:
    seed = f"{snapshot_date}|{universe_checksum}|{OPS_HIST1_SCHEMA_VERSION}|{OPS_HIST1_OBSERVATION_MODE}"
    return f"OPS_HIST1_{snapshot_date}_{sha256(seed.encode('utf-8')).hexdigest()[:12]}"


def _continuity_observation_rows(snapshots: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    prev = None
    for s in snapshots:
        d = s["operational_diagnostics"]
        p = s["posture"]
        row = {
            "snapshot_id": s["snapshot_id"],
            "snapshot_date": s["snapshot_date"],
            "posture": p,
            "posture_transition": "initial" if prev is None else ("changed" if prev["posture"] != p else "unchanged"),
            "fragmentation_value": d["fragmentation_avg"],
            "resilience_value": d["resilience_avg"],
            "sector_concentration_hhi": d["sector_hhi"],
            "volatility_avg": d["volatility_avg"],
            "valuation_dispersion": d["valuation_dispersion"],
            "normalization_completeness": d["normalization_completeness"],
            "fallback_usage": d["fallback_usage"],
        }
        rows.append(row)
        prev = row
    return rows


def _range(values: list[float]) -> dict[str, float]:
    return {"min": round(min(values), 6), "max": round(max(values), 6)} if values else {"min": 0.0, "max": 0.0}


def _snapshot_payload(snapshot_date: str, ingest_result: dict[str, Any], universe: Sequence[str], window_dates: Sequence[str]) -> dict[str, Any]:
    rows = ingest_result.get("rows", [])
    universe_checksum = sha256("|".join(universe).encode("utf-8")).hexdigest()[:16]
    sid = _deterministic_hist_snapshot_id(snapshot_date, universe_checksum)
    op = ingest_result.get("operator_payload", {})
    post = (op.get("daily_ecosystem_posture") or [{}])[0].get("posture", "unknown")
    sector_counts: dict[str, int] = {}
    for r in rows:
        sector_counts[r["sector"]] = sector_counts.get(r["sector"], 0) + 1
    total = max(len(rows), 1)
    hhi = round(sum((c / total) ** 2 for c in sector_counts.values()), 6)
    vol = round(sum(r["volatility_structure"] for r in rows) / total, 6)
    res = round(sum(r["profitability_structure"] - r["leverage_liquidity_structure"] for r in rows) / total, 6)
    frag = round(sum(r["breadth_dispersion_structure"] for r in rows) / total, 6)
    vals = sorted(r["valuation_structure"] for r in rows)
    val_disp = round(vals[-1] - vals[0], 6) if vals else 0.0
    window_checksum = historical_window_checksum(window_dates, universe, len(window_dates))
    diagnostics = {
        "symbols_requested": len(universe),
        "symbols_successfully_normalized": len(rows),
        "normalization_completeness": round((len(rows) / max(len(universe), 1)) * 100.0, 6),
        "fallback_usage": 0.0,
        "fragmentation_avg": frag,
        "resilience_avg": res,
        "sector_hhi": hhi,
        "volatility_avg": vol,
        "valuation_dispersion": val_disp,
        "persistence_mode": "local_json_only",
        "supabase_write_enabled": False,
        "repo_writeback_enabled": False,
        "orchestration_enabled": False,
        "streaming_enabled": False,
    }
    streamlit_payloads = {
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "historical_posture_timeline": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "posture": post}],
        "fragmentation_timeline": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "fragmentation": frag}],
        "resilience_migration_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "resilience": res}],
        "sector_transition_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "sector_hhi": hhi}],
        "continuity_stability_panel": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "window_checksum": window_checksum}],
        "diagnostics_evolution_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "normalization_completeness": diagnostics["normalization_completeness"], "fallback_usage": 0.0}],
        "valuation_dispersion_timeline": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "valuation_dispersion": val_disp}],
        "volatility_transition_table": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "volatility": vol}],
    }
    canonical_tables = {
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "historical_snapshot_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "symbol_count": len(rows)}],
        "historical_posture_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "posture": post}],
        "fragmentation_evolution_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "fragmentation": frag}],
        "resilience_evolution_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "resilience": res}],
        "sector_transition_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "sector_hhi": hhi}],
        "diagnostics_evolution_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "normalization_completeness": diagnostics["normalization_completeness"], "fallback_usage": 0.0}],
        "continuity_stability_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, "historical_window_checksum": window_checksum}],
        "governance_rows": [{"snapshot_id": sid, "snapshot_date": snapshot_date, **_governance_flags()}],
    }
    return {
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "snapshot_id": sid,
        "snapshot_date": snapshot_date,
        "historical_window_metadata": {
            "window_days": len(window_dates),
            "max_window_days": MAX_HIST_WINDOW_DAYS,
            "window_dates": list(window_dates),
        },
        "universe_checksum": universe_checksum,
        "historical_window_checksum": window_checksum,
        "continuity_metadata": {"observation_mode": OPS_HIST1_OBSERVATION_MODE},
        "governance_metadata": _governance_flags(),
        "canonical_payloads": canonical_tables,
        "streamlit_payloads": streamlit_payloads,
        "operational_diagnostics": diagnostics,
        "posture": post,
    }


def _build_snapshot_telemetry_fields(
    *,
    snapshot_date: str,
    symbol_diagnostics: Sequence[dict[str, Any]],
    sample_limit: int,
) -> dict[str, Any]:
    missing_record_samples: list[dict[str, Any]] = []
    endpoint_failure_samples: list[dict[str, Any]] = []
    failure_reason_counts: Counter[str] = Counter()
    for symbol_diag in symbol_diagnostics:
        attempts = list(symbol_diag.get("endpoint_attempts", []) or [])
        if not attempts:
            continue
        success_attempt = next((a for a in attempts if a.get("failure_reason") is None), None)
        for attempt_index, attempt in enumerate(attempts, start=1):
            reason = attempt.get("failure_reason")
            if not reason:
                continue
            failure_reason_counts[str(reason)] += 1
            endpoint_failure_samples.append(
                {
                    "symbol": str(symbol_diag.get("symbol", "")),
                    "requested_snapshot_date": snapshot_date,
                    "endpoint_name": str(attempt.get("endpoint_family", "unknown")),
                    "attempt_index": int(attempt_index),
                    "failure_reason": str(reason),
                    "http_status": None if str(attempt.get("http_status")) == "ok" else str(attempt.get("http_status")),
                    "records_returned_count": int(attempt.get("record_count_returned", 0) or 0),
                    "terminal_failure_for_symbol_date": bool(success_attempt is None and attempt is attempts[-1]),
                }
            )
        if success_attempt is None:
            terminal_reason = str((attempts[-1].get("failure_reason") if attempts else "missing_reconciled_historical_date") or "missing_reconciled_historical_date")
            failure_reason_counts[terminal_reason] += 1
            final_attempt = attempts[-1] if attempts else {}
            missing_record_samples.append(
                {
                    "symbol": str(symbol_diag.get("symbol", "")),
                    "requested_snapshot_date": snapshot_date,
                    "reconciliation_window_days": 5,
                    "exact_match_found": False,
                    "reconciled_prior_date": final_attempt.get("selected_record_date"),
                    "final_missing_after_reconciliation": True,
                    "final_failure_reason": terminal_reason,
                }
            )
        elif not success_attempt.get("exact_date_match_found") and not success_attempt.get("date_reconciliation_used"):
            missing_record_samples.append(
                {
                    "symbol": str(symbol_diag.get("symbol", "")),
                    "requested_snapshot_date": snapshot_date,
                    "reconciliation_window_days": 5,
                    "exact_match_found": False,
                    "reconciled_prior_date": None,
                    "final_missing_after_reconciliation": True,
                    "final_failure_reason": "missing_reconciled_historical_date",
                }
            )
    sorted_missing_samples = sorted(missing_record_samples, key=lambda s: (str(s.get("requested_snapshot_date", "")), str(s.get("symbol", ""))))[:sample_limit]
    sorted_endpoint_failure_samples = sorted(endpoint_failure_samples, key=_sort_endpoint_failure_sample)[:sample_limit]
    affected_symbols = sorted({str(s.get("symbol", "")) for s in (sorted_missing_samples + sorted_endpoint_failure_samples) if str(s.get("symbol", ""))})
    affected_dates = sorted({str(s.get("requested_snapshot_date", "")) for s in (sorted_missing_samples + sorted_endpoint_failure_samples) if str(s.get("requested_snapshot_date", ""))})
    return {
        "missing_record_samples": sorted_missing_samples,
        "endpoint_failure_samples": sorted_endpoint_failure_samples,
        "missing_record_sample_count": len(sorted_missing_samples),
        "endpoint_failure_sample_count": len(sorted_endpoint_failure_samples),
        "affected_symbol_count": len(affected_symbols),
        "affected_date_count": len(affected_dates),
        "top_failure_reasons": [{"reason": k, "count": int(v)} for k, v in failure_reason_counts.most_common(5)],
    }



def _minimum_safe_normalized_ratio() -> float:
    raw = os.getenv("OPS_HIST1_MINIMUM_SAFE_RATIO", "0.5")
    try:
        value = float(raw)
    except Exception:
        value = 0.5
    return max(0.0, min(value, 1.0))


def _partition_normalization_candidates(raw_rows: Sequence[dict[str, Any]], universe: Sequence[str]) -> tuple[list[dict[str, Any]], dict[str, list[str]], Counter[str]]:
    by_symbol = {str(r.get("symbol", "")).upper(): r for r in raw_rows if str(r.get("symbol", "")).strip()}
    failures_by_symbol: dict[str, list[str]] = {}
    reason_counts: Counter[str] = Counter()
    valid_rows: list[dict[str, Any]] = []
    for sym in [str(s).upper() for s in universe if str(s).strip()]:
        row = by_symbol.get(sym)
        reasons: list[str] = []
        if row is None:
            reasons.append("empty_provider_response")
        else:
            price = row.get("price")
            if price is None:
                reasons.append("missing_price")
            else:
                try:
                    float(price)
                except Exception:
                    reasons.append("malformed_numeric_conversion")
            market_cap = row.get("marketCap")
            if market_cap is not None:
                try:
                    float(market_cap)
                except Exception:
                    reasons.append("malformed_numeric_conversion")
        if reasons:
            failures_by_symbol[sym] = sorted(set(reasons))
            for reason in set(reasons):
                reason_counts[reason] += 1
        else:
            valid_rows.append(row)
    return valid_rows, failures_by_symbol, reason_counts


def _partition_downstream_ingestion_candidates(rows: Sequence[dict[str, Any]], universe: Sequence[str], snapshot_date: str) -> tuple[list[dict[str, Any]], dict[str, list[str]], Counter[str]]:
    by_symbol = {str(r.get("symbol", "")).upper(): r for r in rows if str(r.get("symbol", "")).strip()}
    failures_by_symbol: dict[str, list[str]] = {}
    reason_counts: Counter[str] = Counter()
    valid_rows: list[dict[str, Any]] = []
    for sym in [str(s).upper() for s in universe if str(s).strip()]:
        row = by_symbol.get(sym)
        reasons: list[str] = []
        if row is None:
            reasons.append("missing_post_fetch_row")
        else:
            patched_row = dict(row)
            if not str(patched_row.get("date", "")).strip():
                patched_row["date"] = snapshot_date
            if not str(row.get("symbol", "")).strip():
                reasons.append("missing_symbol")
            if not str(patched_row.get("date", "")).strip():
                reasons.append("missing_date")
            try:
                float(patched_row.get("price"))
            except Exception:
                reasons.append("invalid_price_numeric")
            if patched_row.get("marketCap") is None:
                reasons.append("missing_market_cap")
            if not str(patched_row.get("sector", "")).strip():
                reasons.append("missing_sector")
            if not str(patched_row.get("industry", patched_row.get("subsector", ""))).strip():
                reasons.append("missing_industry_or_subsector")
        if reasons:
            failures_by_symbol[sym] = sorted(set(reasons))
            for reason in set(reasons):
                reason_counts[reason] += 1
        else:
            valid_rows.append(patched_row)
    return valid_rows, failures_by_symbol, reason_counts


def _fetch_with_optional_date(
    fetch_batch: Callable[..., Iterable[dict]],
    symbols: Sequence[str],
    snapshot_date: str,
    progress_callback: Callable[[int, str, str], None] | None = None,
) -> list[dict]:
    params = inspect.signature(fetch_batch).parameters
    if "progress_callback" in params:
        return list(fetch_batch(symbols, snapshot_date, progress_callback=progress_callback))
    if len(params) >= 2:
        return list(fetch_batch(symbols, snapshot_date))
    return list(fetch_batch(symbols))


def _historical_diagnostics(raw_rows: Sequence[dict], normalized_rows: Sequence[dict], universe: Sequence[str], snapshot_date: str, profile_diag: dict[str, Any] | None = None) -> dict[str, Any]:
    failures: list[str] = []
    for r in raw_rows:
        if not r.get("symbol"):
            failures.append("missing_symbol")
        if not r.get("date"):
            failures.append("missing_date")
        if r.get("price") is None:
            failures.append("missing_price")
    sample_keys = sorted({k for row in list(raw_rows)[:5] for k in row.keys() if "key" not in k.lower() and "token" not in k.lower()})[:20]
    profile_diag = profile_diag or {}
    sector_unknown_count = sum(1 for r in raw_rows if str(r.get("sector", "unknown")).lower() == "unknown")
    industry_unknown_count = sum(1 for r in raw_rows if str(r.get("industry", "unknown")).lower() == "unknown")
    return {
        "fmp_endpoint_family_used": profile_diag.get("fmp_endpoint_family_used", "historical-price-full + historical-market-capitalization + stable/profile"),
        "historical_date_requested": snapshot_date,
        "symbol_count_requested": len(universe),
        "symbol_count_returned_raw": len(raw_rows),
        "symbol_count_normalized": len(normalized_rows),
        "normalization_failure_count": max(0, len(raw_rows) - len(normalized_rows)),
        "top_normalization_failure_reasons": [r for r, _ in Counter(failures).most_common(5)],
        "sample_raw_keys_observed": sample_keys,
        "historical_adapter_mode": "real_ops_hist1_historical_adapter",
        "historical_price_endpoint_family": profile_diag.get("historical_price_endpoint_family", "stable_historical_price_eod_full"),
        "primary_endpoint_family": profile_diag.get("primary_endpoint_family", "stable_historical_price_eod_full"),
        "fallback_endpoint_family": profile_diag.get("fallback_endpoint_family", "legacy_historical_price_full"),
        "historical_price_url_shape_valid": bool(profile_diag.get("historical_price_url_shape_valid", True)),
        "historical_price_query_parameters_present": bool(profile_diag.get("historical_price_query_parameters_present", True)),
        "historical_price_endpoint_status": profile_diag.get("historical_price_endpoint_status", "ok"),
        "historical_price_http_status_counts": dict(profile_diag.get("historical_price_http_status_counts", {})),
        "historical_price_failure_reasons": dict(profile_diag.get("historical_price_failure_reasons", {})),
        "historical_price_records_requested": int(profile_diag.get("historical_price_records_requested", 0)),
        "historical_price_records_returned": int(profile_diag.get("historical_price_records_returned", 0)),
        "historical_price_records_matched_to_snapshot_date": int(profile_diag.get("historical_price_records_matched_to_snapshot_date", 0)),
        "historical_price_symbols_succeeded": int(profile_diag.get("historical_price_symbols_succeeded", 0)),
        "historical_price_symbols_failed": int(profile_diag.get("historical_price_symbols_failed", 0)),
        "sample_historical_price_raw_keys_observed": list(profile_diag.get("sample_historical_price_raw_keys_observed", [])),
        "historical_market_cap_endpoint_status": profile_diag.get("historical_market_cap_endpoint_status", "ok"),
        "profile_endpoint_status": profile_diag.get("profile_endpoint_status", "ok"),
        "profile_enrichment_status": profile_diag.get("profile_enrichment_status", "ok"),
        "profile_records_requested": int(profile_diag.get("profile_records_requested", 0)),
        "profile_records_returned": int(profile_diag.get("profile_records_returned", 0)),
        "profile_fetch_failure_count": int(profile_diag.get("profile_fetch_failure_count", 0)),
        "profile_fetch_failure_reasons": dict(profile_diag.get("profile_fetch_failure_reasons", {})),
        "sector_unknown_count": sector_unknown_count,
        "industry_unknown_count": industry_unknown_count,
        "sector_industry_fallback_used": bool(profile_diag.get("sector_industry_fallback_used", sector_unknown_count > 0 or industry_unknown_count > 0)),
        "empty_snapshot_fail_closed": len(normalized_rows) == 0 or all(r.get("price") is None for r in raw_rows),
    }


def _classify_empty_snapshot_cause(
    *,
    raw_rows: Sequence[dict[str, Any]],
    valid_rows: Sequence[dict[str, Any]],
    downstream_preflight_rows: Sequence[dict[str, Any]],
    normalized_rows: Sequence[dict[str, Any]],
    profile_diag: dict[str, Any],
    snapshot_date: str,
) -> tuple[str, str]:
    if not raw_rows:
        symbol_diags = profile_diag.get("historical_price_symbol_diagnostics", []) or []
        if symbol_diags:
            attempts = [a for s in symbol_diags for a in (s.get("endpoint_attempts", []) or [])]
            if attempts and all((a.get("failure_reason") == "missing_reconciled_historical_date") for a in attempts):
                return "unavailable_trading_day", "reconciliation"
            if any(str(a.get("failure_reason", "")).startswith(("HTTP_", "URL_ERROR", "TIMEOUT", "UNEXPECTED_ERROR")) for a in attempts):
                return "upstream_fetch_failure", "fetch"
            return "empty_batch_fetch", "fetch"
        return "provider_empty_response", "fetch"
    if raw_rows and not valid_rows:
        if any(not isinstance(r, dict) for r in raw_rows):
            return "malformed_provider_payload", "pre_normalization"
        return "all_symbols_filtered_pre_normalization", "pre_normalization"
    if valid_rows and not downstream_preflight_rows:
        return "downstream_preflight_schema_mismatch", "pre_normalization"
    if downstream_preflight_rows and not normalized_rows:
        return "downstream_ingestion_normalization_contract_mismatch", "normalization"
    if valid_rows and not normalized_rows:
        return "all_symbols_failed_normalization", "normalization"
    return "unsupported_schema", "normalization"

def run_ops_hist1_historical_backfill(*, snapshot_date: str, output_dir: str, window_days: int = DEFAULT_HIST_WINDOW_DAYS, fetch_batch: Callable[[Sequence[str]], Iterable[dict]] | None = None, progress_interval: int = PROGRESS_INTERVAL_DEFAULT, symbol_universe_override: Sequence[str] | None = None, telemetry_max_samples: int = DEFAULT_TELEMETRY_MAX_SAMPLES) -> dict[str, Any]:
    if fetch_batch is None:
        api_key = os.getenv("FMP_API_KEY", "")
        if not api_key:
            raise RuntimeError("FMP_API_KEY missing; OPS-HIST-1 fails closed")
        fetch_batch = build_historical_fmp_fetcher(api_key)

    window_dates = deterministic_historical_window_dates(snapshot_date, window_days)
    if len(window_dates) > MAX_SNAPSHOTS_PER_RUN:
        raise ValueError("OPS-HIST-1 fails closed: snapshot count exceeds MAX_SNAPSHOTS_PER_RUN")
    universe = [str(s).upper() for s in (symbol_universe_override or get_ops_live1b_controlled_universe()) if str(s).strip()]
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots = []
    progress_interval = _bounded_progress_interval(progress_interval)
    run_start = time.monotonic()
    endpoint_success_counts: Counter[str] = Counter()
    endpoint_failure_counts: Counter[str] = Counter()
    failure_reason_counts: Counter[str] = Counter()
    missing_record_samples: list[dict[str, Any]] = []
    endpoint_failure_samples: list[dict[str, Any]] = []
    exact_date_matches = 0
    reconciled_prior_dates = 0
    missing_dates = 0
    normalized_total = 0
    partial_total = 0
    failed_total = 0
    sample_limit = _bounded_telemetry_limit(telemetry_max_samples)
    snapshot_durations: list[float] = []
    cache_totals = {"cache_hits": 0, "cache_misses": 0, "cache_rows_written": 0, "cache_read_failures": 0, "cache_write_failures": 0, "requested_symbol_dates_count": 0, "cache_lookup_attempted_count": 0, "valid_cached_rows_count": 0, "malformed_cached_rows_count": 0, "missing_symbol_dates_count": 0, "fetched_symbol_dates_count": 0, "write_attempted_rows_count": 0, "write_success_rows_count": 0, "write_failed_rows_count": 0}
    for d in window_dates:
        snapshot_started = time.monotonic()
        heartbeat_state = {"last_emitted_seconds": 0}
        def _snapshot_heartbeat(symbol_index: int, symbol: str, endpoint_family: str) -> None:
            elapsed = int(time.monotonic() - snapshot_started)
            if elapsed < SNAPSHOT_HEARTBEAT_SECONDS:
                return
            if elapsed - int(heartbeat_state["last_emitted_seconds"]) < SNAPSHOT_HEARTBEAT_SECONDS:
                return
            heartbeat_state["last_emitted_seconds"] = elapsed
            _emit_ops_hist1_progress(
                {
                    "snapshot_heartbeat": True,
                    "snapshot_index": f"{len(snapshots) + 1}/{len(window_dates)}",
                    "snapshot_date": d,
                    "current_symbol_index": f"{symbol_index}/{len(universe)}",
                    "current_symbol": symbol,
                    "elapsed_seconds_in_snapshot": elapsed,
                    "endpoint_family": endpoint_family,
                }
            )
        raw_rows = _fetch_with_optional_date(fetch_batch, universe, d, progress_callback=_snapshot_heartbeat)
        fetched_row_count = len(raw_rows)
        valid_rows, failures_by_symbol, isolation_reason_counts = _partition_normalization_candidates(raw_rows, universe)
        pre_normalization_row_count = len(valid_rows)
        downstream_rows, downstream_failures_by_symbol, downstream_reason_counts = _partition_downstream_ingestion_candidates(valid_rows, universe, d)
        valid_symbols = sorted({str(r.get("symbol", "")).upper() for r in downstream_rows if str(r.get("symbol", "")).strip()})
        reconciliation_retained_row_count = len(valid_symbols)
        result = ingest_controlled_daily_snapshot(valid_symbols, d, lambda batch, _raw=downstream_rows: [r for r in _raw if str(r.get("symbol", "")).upper() in set(batch)]) if valid_symbols else {"rows": [], "snapshot_ts": _deterministic_hist_snapshot_id(d, "empty"), "snapshot_identity": {}, "status": "failed_closed"}
        profile_diag = dict(getattr(fetch_batch, "last_profile_diagnostics", {}) or {})
        for k in list(cache_totals.keys()):
            v = profile_diag.get(k, 0)
            if v is None:
                v = 0
            cache_totals[k] += int(v)
        diag = _historical_diagnostics(raw_rows, result.get("rows", []), universe, d, profile_diag)
        requested = max(int(diag.get("symbol_count_requested", len(universe))), 1)
        preserved = int(diag.get("symbol_count_normalized", 0))
        isolated_failed = max(0, requested - preserved)
        failure_ratio = round(isolated_failed / requested, 6)
        normalized_ratio = round(preserved / requested, 6)
        minimum_safe_ratio = _minimum_safe_normalized_ratio()
        diag["normalization_failure_symbol_samples"] = [{"symbol": s, "reasons": failures_by_symbol.get(s, [])} for s in sorted(failures_by_symbol.keys())[:sample_limit]]
        diag["normalization_failure_reason_counts"] = dict(sorted((isolation_reason_counts or Counter()).items()))
        diag["normalization_failure_ratio"] = failure_ratio
        diag["isolated_failed_symbol_count"] = isolated_failed
        diag["preserved_normalized_symbol_count"] = preserved
        diag["minimum_safe_ratio"] = minimum_safe_ratio
        diag["normalization_mode"] = "isolated_symbol_failures" if isolated_failed > 0 and preserved > 0 else "all_symbols_healthy"
        diag["fetched_row_count"] = fetched_row_count
        diag["pre_normalization_row_count"] = pre_normalization_row_count
        diag["downstream_preflight_retained_row_count"] = len(downstream_rows)
        diag["downstream_preflight_failed_symbol_count"] = len(downstream_failures_by_symbol)
        diag["downstream_preflight_failure_reason_counts"] = dict(sorted((downstream_reason_counts or Counter()).items()))
        diag["downstream_preflight_failure_symbol_samples"] = [{"symbol": s, "reasons": downstream_failures_by_symbol.get(s, [])} for s in sorted(downstream_failures_by_symbol.keys())[:sample_limit]]
        diag["reconciliation_retained_row_count"] = reconciliation_retained_row_count
        diag["normalization_retained_row_count"] = preserved
        diag["final_preserved_symbol_count"] = preserved
        diag["fetch_empty_response_detected"] = fetched_row_count == 0
        diag["reconciliation_full_filter_detected"] = pre_normalization_row_count > 0 and reconciliation_retained_row_count == 0
        diag["normalization_full_filter_detected"] = pre_normalization_row_count > 0 and preserved == 0
        diag["downstream_normalization_zero_rows"] = len(downstream_rows) > 0 and preserved == 0
        if preserved == 0:
            empty_reason, empty_stage = _classify_empty_snapshot_cause(
                raw_rows=raw_rows,
                valid_rows=valid_rows,
                downstream_preflight_rows=downstream_rows,
                normalized_rows=result.get("rows", []),
                profile_diag=profile_diag,
                snapshot_date=d,
            )
            diag["empty_snapshot_reason_class"] = empty_reason
            diag["empty_snapshot_stage"] = empty_stage
            diag["top_normalization_failure_reasons"] = list(diag.get("top_normalization_failure_reasons") or []) or [empty_reason]
        if preserved == 0:
            raise RuntimeError(
                f"OPS-HIST-1 fails closed: empty normalized snapshot for {d}; "
                f"stage={diag.get('empty_snapshot_stage')}; class={diag.get('empty_snapshot_reason_class')}; "
                f"reasons={diag['top_normalization_failure_reasons']}; "
                f"downstream_preflight_top_reasons={list((downstream_reason_counts or Counter()).keys())[:5]}"
            )
        if normalized_ratio < minimum_safe_ratio:
            raise RuntimeError(
                "OPS-HIST-1 fails closed: normalized ratio below minimum safe threshold "
                f"for {d}; normalized_ratio={normalized_ratio}; minimum_safe_ratio={minimum_safe_ratio}; "
                f"top_failure_reasons={diag['top_normalization_failure_reasons']}"
            )
        result["surfaces"] = build_normalized_operational_surfaces(result.get("rows", []), result.get("snapshot_ts", ""), result.get("snapshot_identity", {}))
        result["operator_payload"] = build_operator_payloads(result["surfaces"])
        snap = _snapshot_payload(d, result, universe, window_dates)
        snap.update(_build_snapshot_telemetry_fields(snapshot_date=d, symbol_diagnostics=profile_diag.get("historical_price_symbol_diagnostics", []), sample_limit=sample_limit))
        snap["adapter_diagnostics"] = diag
        Path(out_dir / f"ops_hist1_{d}.json").write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
        snapshots.append(snap)
        normalized_count = int(diag.get("symbol_count_normalized", 0))
        requested_count = int(diag.get("symbol_count_requested", len(universe)))
        failed_count = max(0, requested_count - normalized_count)
        partial_count = 1 if 0 < normalized_count < requested_count else 0
        normalized_total += normalized_count
        partial_total += partial_count
        failed_total += failed_count
        for symbol_diag in profile_diag.get("historical_price_symbol_diagnostics", []):
            attempts = symbol_diag.get("endpoint_attempts", [])
            if not attempts:
                continue
            success_attempt = next((a for a in attempts if a.get("failure_reason") is None), None)
            if success_attempt:
                endpoint_success_counts[str(success_attempt.get("endpoint_family", "unknown"))] += 1
                if success_attempt.get("exact_date_match_found"):
                    exact_date_matches += 1
                elif success_attempt.get("date_reconciliation_used"):
                    reconciled_prior_dates += 1
                else:
                    missing_dates += 1
            else:
                missing_dates += 1
                endpoint_failure_counts[str(attempts[-1].get("failure_reason") or "unknown")] += 1
            for attempt in attempts:
                reason = attempt.get("failure_reason")
                if reason:
                    endpoint_failure_counts[str(reason)] += 1
                    failure_reason_counts[str(reason)] += 1
                    endpoint_failure_samples.append(
                        {
                            "symbol": str(symbol_diag.get("symbol", "")),
                            "requested_snapshot_date": d,
                            "endpoint_name": str(attempt.get("endpoint_family", "unknown")),
                            "attempt_index": int(attempts.index(attempt)) + 1,
                            "failure_reason": str(reason),
                            "http_status": None if str(attempt.get("http_status")) == "ok" else str(attempt.get("http_status")),
                            "records_returned_count": int(attempt.get("record_count_returned", 0) or 0),
                            "terminal_failure_for_symbol_date": bool(success_attempt is None and attempt is attempts[-1]),
                        }
                    )
            if success_attempt is None:
                terminal_reason = str((attempts[-1].get("failure_reason") if attempts else "missing_reconciled_historical_date") or "missing_reconciled_historical_date")
                failure_reason_counts[terminal_reason] += 1
                final_attempt = attempts[-1] if attempts else {}
                missing_record_samples.append(
                    {
                        "symbol": str(symbol_diag.get("symbol", "")),
                        "requested_snapshot_date": d,
                        "reconciliation_window_days": 5,
                        "exact_match_found": False,
                        "reconciled_prior_date": final_attempt.get("selected_record_date"),
                        "final_missing_after_reconciliation": True,
                        "final_failure_reason": terminal_reason,
                    }
                )
            elif not success_attempt.get("exact_date_match_found") and not success_attempt.get("date_reconciliation_used"):
                missing_record_samples.append(
                    {
                        "symbol": str(symbol_diag.get("symbol", "")),
                        "requested_snapshot_date": d,
                        "reconciliation_window_days": 5,
                        "exact_match_found": False,
                        "reconciled_prior_date": None,
                        "final_missing_after_reconciliation": True,
                        "final_failure_reason": "missing_reconciled_historical_date",
                    }
                )
        snapshot_durations.append(time.monotonic() - snapshot_started)
        snapshot_index = len(snapshots)
        if snapshot_index % progress_interval == 0 or snapshot_index == len(window_dates):
            elapsed_seconds = int(time.monotonic() - run_start)
            avg_snapshot_seconds = sum(snapshot_durations) / max(len(snapshot_durations), 1)
            remaining_snapshots = len(window_dates) - snapshot_index
            eta_minutes = round((avg_snapshot_seconds * remaining_snapshots) / 60.0, 2)
            _emit_ops_hist1_progress(
                {
                    "snapshot": f"{snapshot_index}/{len(window_dates)}",
                    "date": d,
                    "elapsed_seconds": elapsed_seconds,
                    "normalized_symbols": normalized_count,
                    "partial_symbols": partial_count,
                    "failed_symbols": failed_count,
                    "exact_date_matches": exact_date_matches,
                    "reconciled_prior_dates": reconciled_prior_dates,
                    "missing_dates": missing_dates,
                    "estimated_remaining_snapshots": remaining_snapshots,
                    "estimated_remaining_minutes": eta_minutes,
                }
            )
            requested_total = max(cache_totals["cache_hits"] + cache_totals["cache_misses"], 1)
            _emit_ops_hist1_progress({"raw_cache": True, "cache_enabled": str(os.getenv("OPS_HIST_RAW_CACHE_ENABLED", "false")).lower() == "true", "cache_write_enabled": str(os.getenv("OPS_HIST_RAW_CACHE_WRITE_ENABLED", "false")).lower() == "true", "cache_hits": cache_totals["cache_hits"], "cache_misses": cache_totals["cache_misses"], "cache_rows_written": cache_totals["cache_rows_written"], "cache_read_failures": cache_totals["cache_read_failures"], "cache_write_failures": cache_totals["cache_write_failures"], "cache_hit_ratio": round(cache_totals["cache_hits"] / requested_total, 6), "fmp_requests_avoided_estimate": cache_totals["cache_hits"]})
            _emit_endpoint_summary(dict(endpoint_success_counts), dict(endpoint_failure_counts))
    continuity_rows = _continuity_observation_rows(snapshots)
    sorted_missing_samples = sorted(missing_record_samples, key=lambda s: (str(s.get("requested_snapshot_date", "")), str(s.get("symbol", ""))))[:sample_limit]
    sorted_endpoint_failure_samples = sorted(endpoint_failure_samples, key=_sort_endpoint_failure_sample)[:sample_limit]
    affected_symbols = sorted({str(s.get("symbol", "")) for s in (sorted_missing_samples + sorted_endpoint_failure_samples) if str(s.get("symbol", ""))})
    affected_dates = sorted({str(s.get("requested_snapshot_date", "")) for s in (sorted_missing_samples + sorted_endpoint_failure_samples) if str(s.get("requested_snapshot_date", ""))})
    return {
        "status": "ok",
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "snapshot_count": len(snapshots),
        "output_dir": str(out_dir),
        "continuity_rows": continuity_rows,
        "governance_metadata": _governance_flags(),
        "telemetry_summary": {
            "elapsed_seconds": int(time.monotonic() - run_start),
            "normalized_symbol_total": normalized_total,
            "partial_symbol_total": partial_total,
            "failed_symbol_total": failed_total,
            "exact_date_matches": exact_date_matches,
            "reconciled_prior_dates": reconciled_prior_dates,
            "missing_dates": missing_dates,
            "endpoint_success_counts": dict(sorted(endpoint_success_counts.items())),
            "endpoint_failure_counts": dict(sorted(endpoint_failure_counts.items())),
            "missing_record_samples": sorted_missing_samples,
            "endpoint_failure_samples": sorted_endpoint_failure_samples,
            "missing_record_sample_count": len(sorted_missing_samples),
            "endpoint_failure_sample_count": len(sorted_endpoint_failure_samples),
            "affected_symbol_count": len(affected_symbols),
            "affected_date_count": len(affected_dates),
            "top_failure_reasons": [{"reason": k, "count": int(v)} for k, v in failure_reason_counts.most_common(5)],
            **cache_totals,
        },
    }


def load_ops_hist1_snapshots(input_dir: str) -> list[dict[str, Any]]:
    rows = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(Path(input_dir).glob("ops_hist1_*.json"), key=lambda p: p.name)]
    return sorted(rows, key=lambda r: (r.get("snapshot_date", ""), r.get("snapshot_id", "")))


def build_ops_hist1_observation_review(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    if not snapshots:
        raise ValueError("No OPS-HIST-1 snapshots found")
    canonical_keys = [tuple(sorted(s.get("canonical_payloads", {}).keys())) for s in snapshots]
    streamlit_keys = [tuple(sorted(s.get("streamlit_payloads", {}).keys())) for s in snapshots]
    checks = {
        "continuity_stability": len(set(s["historical_window_checksum"] for s in snapshots)) == 1,
        "payload_stability": len(set(canonical_keys)) == 1,
        "streamlit_payload_stability": len(set(streamlit_keys)) == 1,
        "diagnostics_stability": all("normalization_completeness" in s["operational_diagnostics"] for s in snapshots),
    }
    rows = _continuity_observation_rows(snapshots)
    transition_counts = {
        "initial": sum(1 for r in rows if r["posture_transition"] == "initial"),
        "changed": sum(1 for r in rows if r["posture_transition"] == "changed"),
        "unchanged": sum(1 for r in rows if r["posture_transition"] == "unchanged"),
    }
    continuity_metrics = {
        "posture_transition_counts": transition_counts,
        "fragmentation_value_range": _range([float(r["fragmentation_value"]) for r in rows]),
        "resilience_value_range": _range([float(r["resilience_value"]) for r in rows]),
        "sector_concentration_hhi_range": _range([float(r["sector_concentration_hhi"]) for r in rows]),
        "volatility_avg_range": _range([float(r["volatility_avg"]) for r in rows]),
        "valuation_dispersion_range": _range([float(r["valuation_dispersion"]) for r in rows]),
        "normalization_completeness_range": _range([float(r["normalization_completeness"]) for r in rows]),
        "fallback_usage_range": _range([float(r["fallback_usage"]) for r in rows]),
    }
    review = {
        "status": "ok",
        "schema_version": OPS_HIST1_SCHEMA_VERSION,
        "reviewed_snapshot_count": len(snapshots),
        "governance_metadata": _governance_flags(),
        "continuity_stability": checks,
        "continuity_metrics": continuity_metrics,
        "posture_drift": rows,
        "fragmentation_persistence": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "fragmentation_value": r["fragmentation_value"]} for r in rows],
        "resilience_persistence": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "resilience_value": r["resilience_value"]} for r in rows],
        "sector_evolution": [{"snapshot_id": r["snapshot_id"], "snapshot_date": r["snapshot_date"], "sector_concentration_hhi": r["sector_concentration_hhi"]} for r in rows],
        "streamlit_review_payload": {"schema_version": OPS_HIST1_SCHEMA_VERSION, "continuity_stability_panel": [{"check": k, "value": v} for k, v in checks.items()], "historical_posture_timeline": rows, "continuity_metrics": continuity_metrics},
        "canonical_review_payload": {"schema_version": OPS_HIST1_SCHEMA_VERSION, "continuity_stability_rows": [{"check": k, "value": v} for k, v in checks.items()], "historical_snapshot_rows": [{"snapshot_id": s["snapshot_id"], "snapshot_date": s["snapshot_date"]} for s in snapshots], "continuity_metrics_rows": [{"metric": k, "value": v} for k, v in continuity_metrics.items()]},
    }
    return review


def render_ops_hist1_observation_review_markdown(review: dict[str, Any]) -> str:
    return "\n".join([
        "# OPS-HIST-1 Historical Observation Review",
        "## Objective",
        "Bounded historical observational review across deterministic 50-symbol snapshots.",
        f"## Schema version\n{review['schema_version']}",
        f"## Reviewed snapshots\n{review['reviewed_snapshot_count']}",
        "## Continuity stability",
        json.dumps(review["continuity_stability"], sort_keys=True),
        "## Continuity metrics",
        json.dumps(review["continuity_metrics"], sort_keys=True),
        "## Governance certification",
        "Observational-only historical mode; no replay/topology/prediction/trading/orchestration/streaming.",
    ])
