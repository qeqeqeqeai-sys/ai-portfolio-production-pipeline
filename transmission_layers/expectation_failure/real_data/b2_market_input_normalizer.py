"""B2 deterministic normalization for controlled market input records."""

from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Iterable, Tuple

CANONICAL_METRICS: Tuple[str, ...] = (
    "benchmark_relative_return",
    "ev_to_ebitda",
    "forward_pe",
    "price",
    "price_momentum_30d",
    "price_momentum_90d",
    "realized_volatility",
    "revenue_growth",
)
SUPPORTED_CURRENCIES: Tuple[str, ...] = ("USD",)
MAX_SOURCE_AGE_DAYS = 7
NUMERIC_BOUNDS: Dict[str, Tuple[float, float]] = {
    "price": (0.0, 1_000_000.0),
    "forward_pe": (0.0, 500.0),
    "ev_to_ebitda": (-100.0, 500.0),
    "revenue_growth": (-5.0, 10.0),
    "price_momentum_30d": (-2.0, 5.0),
    "price_momentum_90d": (-5.0, 10.0),
    "realized_volatility": (0.0, 5.0),
    "benchmark_relative_return": (-5.0, 5.0),
}


def _parse_date(raw: object) -> date | None:
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


def normalize_market_input_record(record: dict) -> dict:
    """Return canonical immutable projection for a raw input record."""
    row = deepcopy(record)
    metric_name = str(row.get("metric_name", "")).strip().lower()
    symbol = str(row.get("symbol", "")).strip().upper()
    currency = str(row.get("currency", "USD")).strip().upper() or "USD"
    source_name = str(row.get("source_name", "UNKNOWN")).strip() or "UNKNOWN"
    data_quality_hint = str(row.get("data_quality_hint", "unspecified")).strip().lower() or "unspecified"

    observation_date_raw = row.get("observation_date")
    source_timestamp_raw = row.get("source_timestamp")
    observation_date = _parse_date(observation_date_raw)
    source_timestamp = _parse_date(source_timestamp_raw)

    metric_value = row.get("metric_value")
    numeric_value = None
    invalid_numeric_value = False
    if isinstance(metric_value, bool) or metric_value is None:
        numeric_value = None
    else:
        try:
            numeric_value = float(Decimal(str(metric_value)))
        except Exception:
            invalid_numeric_value = True
            numeric_value = None

    bounded = None
    clamped = False
    if numeric_value is not None and metric_name in NUMERIC_BOUNDS:
        lo, hi = NUMERIC_BOUNDS[metric_name]
        bounded = max(lo, min(hi, numeric_value))
        clamped = bounded != numeric_value

    return {
        "symbol": symbol,
        "observation_date": observation_date.isoformat() if observation_date else None,
        "metric_name": metric_name,
        "metric_value": bounded if bounded is not None else numeric_value,
        "source_name": source_name,
        "source_timestamp": source_timestamp.isoformat() if source_timestamp else None,
        "currency": currency,
        "data_quality_hint": data_quality_hint,
        "normalization_flags": {
            "invalid_numeric_value": invalid_numeric_value,
            "metric_value_clamped": clamped,
            "missing_observation_date": observation_date is None,
            "missing_source_timestamp": source_timestamp is None,
        },
    }


def normalize_market_input_records(records: Iterable[dict]) -> list[dict]:
    return [normalize_market_input_record(rec) for rec in deepcopy(list(records))]
