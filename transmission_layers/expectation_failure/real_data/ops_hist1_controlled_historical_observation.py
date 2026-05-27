from __future__ import annotations

import json
import os
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

FMP_STABLE_HISTORICAL_PRICE_URL = "https://financialmodelingprep.com/stable/historical-price-eod/full"
FMP_STABLE_HISTORICAL_PRICE_LIGHT_URL = "https://financialmodelingprep.com/stable/historical-price-eod/light"
FMP_LEGACY_HISTORICAL_PRICE_URL = "https://financialmodelingprep.com/api/v3/historical-price-full/{symbol}"
FMP_LEGACY_HISTORICAL_MARKET_CAP_URL = "https://financialmodelingprep.com/api/v3/historical-market-capitalization/{symbol}"


def _build_fmp_url(base_url: str, params: dict[str, str]) -> str:
    return f"{base_url}?{urlencode(params)}"


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
            with urlopen(f"https://financialmodelingprep.com/stable/profile?{profile_q}", timeout=20) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
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

    def _fetch(symbols: Sequence[str], snapshot_date: str) -> list[dict]:
        snapshot_dt = date.fromisoformat(snapshot_date)
        lookback_from = (snapshot_dt - timedelta(days=7)).isoformat()
        run_diag: dict[str, Any] = {
            "fmp_endpoint_family_used": "stable/historical-price-eod/full + legacy/historical-market-capitalization + stable/profile",
            "historical_price_endpoint_family": "stable_historical_price_eod_full",
            "primary_endpoint_family": "stable_historical_price_eod_full",
            "fallback_endpoint_family": "legacy_historical_price_full",
            "historical_price_url_shape_valid": True,
            "historical_price_query_parameters_present": True,
            "historical_price_endpoint_status": "ok",
            "historical_market_cap_endpoint_status": "ok",
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
        }
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

        rows: list[dict] = []
        endpoint_candidates = (
            ("stable_historical_price_eod_full", FMP_STABLE_HISTORICAL_PRICE_URL, False),
            ("stable_historical_price_eod_light", FMP_STABLE_HISTORICAL_PRICE_LIGHT_URL, False),
            ("legacy_historical_price_full", FMP_LEGACY_HISTORICAL_PRICE_URL, True),
        )
        for symbol in symbols:
            sym = str(symbol).upper()
            run_diag["historical_price_records_requested"] += 1
            sym_diag: dict[str, Any] = {"symbol": sym, "requested_snapshot_date": snapshot_date, "endpoint_attempts": []}
            price_row: dict[str, Any] = {}
            sel_meta: dict[str, Any] = {}
            for endpoint_family, endpoint_url, symbol_in_path in endpoint_candidates:
                params = {"from": lookback_from, "to": snapshot_date, "apikey": api_key}
                if not symbol_in_path:
                    params["symbol"] = sym
                url = _build_fmp_url(endpoint_url.format(symbol=quote(sym, safe="")), params)
                run_diag["historical_price_query_parameters_present"] = run_diag["historical_price_query_parameters_present"] and all(k in url for k in ["from=", "to=", "apikey="])
                payload = None
                status = "ok"
                try:
                    with urlopen(url, timeout=20) as resp:
                        payload = json.loads(resp.read().decode("utf-8"))
                except Exception as exc:
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

            mc_q = {"from": snapshot_date, "to": snapshot_date, "limit": "1", "apikey": api_key}
            mc_url = _build_fmp_url(FMP_LEGACY_HISTORICAL_MARKET_CAP_URL.format(symbol=sym), mc_q)
            try:
                with urlopen(mc_url, timeout=20) as resp:
                    mc = json.loads(resp.read().decode("utf-8"))
                mc_row = mc[0] if isinstance(mc, list) and mc else {}
            except Exception:
                run_diag["historical_market_cap_endpoint_status"] = "degraded"
                mc_row = {}
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
            })
        if run_diag["historical_price_symbols_succeeded"] == 0:
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




def _fetch_with_optional_date(fetch_batch: Callable[..., Iterable[dict]], symbols: Sequence[str], snapshot_date: str) -> list[dict]:
    params = inspect.signature(fetch_batch).parameters
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

def run_ops_hist1_historical_backfill(*, snapshot_date: str, output_dir: str, window_days: int = DEFAULT_HIST_WINDOW_DAYS, fetch_batch: Callable[[Sequence[str]], Iterable[dict]] | None = None) -> dict[str, Any]:
    if fetch_batch is None:
        api_key = os.getenv("FMP_API_KEY", "")
        if not api_key:
            raise RuntimeError("FMP_API_KEY missing; OPS-HIST-1 fails closed")
        fetch_batch = build_historical_fmp_fetcher(api_key)

    window_dates = deterministic_historical_window_dates(snapshot_date, window_days)
    if len(window_dates) > MAX_SNAPSHOTS_PER_RUN:
        raise ValueError("OPS-HIST-1 fails closed: snapshot count exceeds MAX_SNAPSHOTS_PER_RUN")
    universe = get_ops_live1b_controlled_universe()
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    snapshots = []
    for d in window_dates:
        raw_rows = _fetch_with_optional_date(fetch_batch, universe, d)
        result = ingest_controlled_daily_snapshot(universe, d, lambda batch, _raw=raw_rows: _raw)
        profile_diag = dict(getattr(fetch_batch, "last_profile_diagnostics", {}) or {})
        diag = _historical_diagnostics(raw_rows, result.get("rows", []), universe, d, profile_diag)
        if diag["empty_snapshot_fail_closed"]:
            raise RuntimeError(f"OPS-HIST-1 fails closed: empty normalized snapshot for {d}; reasons={diag['top_normalization_failure_reasons']}")
        result["surfaces"] = build_normalized_operational_surfaces(result.get("rows", []), result.get("snapshot_ts", ""), result.get("snapshot_identity", {}))
        result["operator_payload"] = build_operator_payloads(result["surfaces"])
        snap = _snapshot_payload(d, result, universe, window_dates)
        snap["adapter_diagnostics"] = diag
        Path(out_dir / f"ops_hist1_{d}.json").write_text(json.dumps(snap, indent=2, sort_keys=True), encoding="utf-8")
        snapshots.append(snap)
    continuity_rows = _continuity_observation_rows(snapshots)
    return {"status": "ok", "schema_version": OPS_HIST1_SCHEMA_VERSION, "snapshot_count": len(snapshots), "output_dir": str(out_dir), "continuity_rows": continuity_rows, "governance_metadata": _governance_flags()}


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
