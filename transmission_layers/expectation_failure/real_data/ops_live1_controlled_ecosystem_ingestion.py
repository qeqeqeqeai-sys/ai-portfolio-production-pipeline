"""OPS-LIVE-1 controlled live ecosystem state ingestion.

Deterministic, bounded, observational-only ingestion + normalization layer for the
curated 300-stock universe.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from hashlib import sha256
from typing import Callable, Iterable, Sequence

MAX_INGESTION_BATCH_SIZE = 50
MAX_SNAPSHOT_ROWS = 300
MAX_CONTINUITY_WINDOW_DAYS = 90
MAX_DASHBOARD_PAYLOAD_ROWS = 120
MAX_STRUCTURAL_SUMMARY_ITEMS = 12
MAX_RETRY_ATTEMPTS = 2

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


def _normalize_row(row: dict, snapshot_ts: str) -> dict:
    return {
        "symbol": str(row.get("symbol", "")).upper(),
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


def _integrity_validate(rows: Sequence[dict], expected_symbols: Sequence[str]) -> dict:
    symbols = [r.get("symbol") for r in rows]
    unique = sorted(set(symbols))
    expected = sorted(set(s.upper() for s in expected_symbols))
    missing = [s for s in expected if s not in unique]
    duplicates = len(symbols) - len(unique)
    return {
        "is_valid": (not missing) and duplicates == 0 and len(rows) <= MAX_SNAPSHOT_ROWS,
        "missing_symbols": missing,
        "duplicate_count": duplicates,
        "row_count": len(rows),
    }


def ingest_controlled_daily_snapshot(
    symbols: Sequence[str],
    snapshot_date: str,
    fetch_batch: Callable[[Sequence[str]], Iterable[dict]],
) -> dict:
    ordered_symbols = sorted(set(s.upper() for s in symbols))[:MAX_SNAPSHOT_ROWS]
    snapshot_ts = _deterministic_snapshot_timestamp(snapshot_date)
    batches = _chunked(ordered_symbols, MAX_INGESTION_BATCH_SIZE)

    raw_rows: list[dict] = []
    attempts = 0
    for batch in batches:
        batch_success = False
        for _ in range(MAX_RETRY_ATTEMPTS):
            attempts += 1
            try:
                batch_rows = list(fetch_batch(batch))
                raw_rows.extend(deepcopy(batch_rows))
                batch_success = True
                break
            except Exception:
                continue
        if not batch_success:
            return {
                "status": "failed_closed",
                "snapshot_ts": snapshot_ts,
                "attempts": attempts,
                "batches": len(batches),
                "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
            }

    normalized = [_normalize_row(r, snapshot_ts) for r in raw_rows if r.get("symbol")]
    normalized = sorted(normalized, key=lambda r: r["symbol"])[:MAX_SNAPSHOT_ROWS]
    integrity = _integrity_validate(normalized, ordered_symbols)
    if not integrity["is_valid"]:
        return {
            "status": "failed_closed",
            "snapshot_ts": snapshot_ts,
            "attempts": attempts,
            "batches": len(batches),
            "integrity": integrity,
            "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
        }

    surfaces = build_normalized_operational_surfaces(normalized, snapshot_ts)
    payload = build_operator_payloads(surfaces)
    return {
        "status": "ok",
        "snapshot_ts": snapshot_ts,
        "attempts": attempts,
        "batches": len(batches),
        "integrity": integrity,
        "rows": normalized,
        "surfaces": surfaces,
        "operator_payload": payload,
        "governance_boundaries": deepcopy(GOVERNANCE_BOUNDARIES),
    }


def build_normalized_operational_surfaces(rows: Sequence[dict], snapshot_ts: str) -> dict:
    ordered = sorted((deepcopy(r) for r in rows), key=lambda r: (r["symbol"], r["snapshot_ts"]))
    avg_vol = sum(r["volatility_structure"] for r in ordered) / max(len(ordered), 1)
    avg_val = sum(r["valuation_structure"] for r in ordered) / max(len(ordered), 1)
    avg_prof = sum(r["profitability_structure"] for r in ordered) / max(len(ordered), 1)
    avg_lev = sum(r["leverage_liquidity_structure"] for r in ordered) / max(len(ordered), 1)

    return {
        "ecosystem_state_snapshot": ordered,
        "propagation_state_snapshot": [{"snapshot_ts": snapshot_ts, "avg_volatility": round(avg_vol, 6)}],
        "contradiction_state_snapshot": [{"snapshot_ts": snapshot_ts, "valuation_minus_profitability": round(avg_val - avg_prof, 6)}],
        "resilience_state_snapshot": [{"snapshot_ts": snapshot_ts, "resilience_index": round(max(0.0, avg_prof - avg_lev), 6)}],
        "continuity_state_snapshot": [{"snapshot_ts": snapshot_ts, "continuity_marker": sha256(snapshot_ts.encode("utf-8")).hexdigest()[:12]}],
        "ecosystem_posture_snapshot": [{"snapshot_ts": snapshot_ts, "posture": "balanced" if avg_prof >= avg_lev else "fragile"}],
    }


def accumulate_longitudinal_continuity(history: Sequence[dict], new_snapshot: dict) -> list[dict]:
    combined = sorted([*deepcopy(history), deepcopy(new_snapshot)], key=lambda r: r["snapshot_ts"])
    return combined[-MAX_CONTINUITY_WINDOW_DAYS:]


def build_operator_payloads(surfaces: dict) -> dict:
    eco_rows = surfaces["ecosystem_state_snapshot"][:MAX_DASHBOARD_PAYLOAD_ROWS]
    top_pressure = sorted(eco_rows, key=lambda r: r["volatility_structure"], reverse=True)[:MAX_STRUCTURAL_SUMMARY_ITEMS]
    top_resilience = sorted(eco_rows, key=lambda r: r["profitability_structure"] - r["leverage_liquidity_structure"], reverse=True)[:MAX_STRUCTURAL_SUMMARY_ITEMS]

    return {
        "daily_ecosystem_posture": surfaces["ecosystem_posture_snapshot"],
        "dominant_structural_pressures": [{"symbol": r["symbol"], "volatility_structure": r["volatility_structure"]} for r in top_pressure],
        "strongest_resilience_pathways": [{"symbol": r["symbol"], "resilience_gap": round(r["profitability_structure"] - r["leverage_liquidity_structure"], 6)} for r in top_resilience],
        "fragmentation_hotspots": [{"symbol": r["symbol"], "breadth_dispersion_structure": r["breadth_dispersion_structure"]} for r in top_pressure],
        "transition_state_summaries": surfaces["propagation_state_snapshot"],
        "continuity_summaries": surfaces["continuity_state_snapshot"],
        "normalization_observations": {"row_count": len(eco_rows), "bounded": len(eco_rows) <= MAX_DASHBOARD_PAYLOAD_ROWS},
    }
