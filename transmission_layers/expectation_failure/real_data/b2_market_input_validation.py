"""B2 deterministic validation and quarantine for normalized market inputs."""

from __future__ import annotations

from copy import deepcopy
from datetime import date
from typing import Iterable, Mapping

from .b2_market_input_normalizer import CANONICAL_METRICS, MAX_SOURCE_AGE_DAYS, SUPPORTED_CURRENCIES

REASON_SEVERITY = {
    "unknown_symbol": "high",
    "unsupported_metric": "medium",
    "missing_value": "medium",
    "invalid_numeric_value": "high",
    "invalid_date": "high",
    "stale_source_timestamp": "medium",
    "unsupported_currency": "high",
    "duplicate_observation": "low",
}

REMEDIATION_HINT = {
    "unknown_symbol": "use_b1_registry_symbol",
    "unsupported_metric": "use_supported_metric_name",
    "missing_value": "provide_metric_value",
    "invalid_numeric_value": "provide_numeric_metric_value",
    "invalid_date": "use_iso8601_date",
    "stale_source_timestamp": "refresh_observation_source_timestamp",
    "unsupported_currency": "convert_to_usd",
    "duplicate_observation": "remove_duplicate_observation",
}


def build_quarantine_record(record: dict, reason_code: str, original_index: int) -> dict:
    return {
        "symbol": record.get("symbol", ""),
        "metric_name": record.get("metric_name", ""),
        "reason_code": reason_code,
        "original_record_reference": f"record_index_{original_index}",
        "deterministic_severity": REASON_SEVERITY[reason_code],
        "remediation_hint": REMEDIATION_HINT[reason_code],
    }


def validate_normalized_records(
    normalized_records: Iterable[dict],
    allowed_symbols: set[str],
    as_of_date: str,
) -> tuple[list[dict], list[dict]]:
    accepted: list[dict] = []
    quarantined: list[dict] = []
    seen = set()
    cutoff_anchor = date.fromisoformat(as_of_date)

    for idx, row in enumerate(deepcopy(list(normalized_records))):
        reasons: list[str] = []
        key = (row.get("symbol"), row.get("observation_date"), row.get("metric_name"), row.get("source_name"))

        if row.get("symbol") not in allowed_symbols:
            reasons.append("unknown_symbol")
        if row.get("metric_name") not in CANONICAL_METRICS:
            reasons.append("unsupported_metric")
        if row.get("metric_value") is None:
            reasons.append("missing_value")
        if row.get("normalization_flags", {}).get("invalid_numeric_value"):
            reasons.append("invalid_numeric_value")
        if not row.get("observation_date"):
            reasons.append("invalid_date")
        if row.get("currency") not in SUPPORTED_CURRENCIES:
            reasons.append("unsupported_currency")
        if key in seen:
            reasons.append("duplicate_observation")
        else:
            seen.add(key)

        source_timestamp = row.get("source_timestamp")
        if source_timestamp:
            source_date = date.fromisoformat(source_timestamp)
            age_days = (cutoff_anchor - source_date).days
            if age_days > MAX_SOURCE_AGE_DAYS:
                reasons.append("stale_source_timestamp")
        else:
            reasons.append("invalid_date")

        if reasons:
            for reason in sorted(set(reasons)):
                quarantined.append(build_quarantine_record(row, reason, idx))
        else:
            accepted.append(row)

    accepted.sort(key=lambda r: (r["symbol"], r["observation_date"], r["metric_name"], r["source_name"]))
    quarantined.sort(key=lambda r: (r["reason_code"], r["symbol"], r["metric_name"], r["original_record_reference"]))
    return accepted, quarantined
