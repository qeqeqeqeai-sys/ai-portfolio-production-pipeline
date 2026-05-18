from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from transmission_layers.asset_discovery.tier3h5.canonical_registry_normalization import normalize_exchange_code, normalize_ticker
from transmission_layers.asset_discovery.tier3h5.canonical_registry_resolution_observability import (
    emit_tier3h5_resolution_diagnostics,
    write_registry_resolution_summary,
)
from transmission_layers.asset_discovery.tier3h5.canonical_registry_sample_sources import SAMPLE_REGISTRY_SOURCES


@dataclass(frozen=True)
class RegistryResolutionResult:
    resolution_status: str
    resolved_security_id: str | None
    resolved_issuer_id: str | None
    normalized_ticker: str
    normalized_exchange: str
    matched_source_registry: str | None
    match_rule: str
    explanation: str
    conflict_count: int
    candidate_count: int


def resolve_security_from_registry(
    ticker: str,
    exchange: str,
    security_registry: list[dict[str, Any]],
    security_type: str | None = None,
) -> RegistryResolutionResult:
    normalized_ticker = normalize_ticker(ticker)
    normalized_exchange = normalize_exchange_code(exchange)
    normalized_security_type = (security_type or "").strip().lower()

    if not normalized_ticker or not normalized_exchange:
        return RegistryResolutionResult(
            resolution_status="invalid_input",
            resolved_security_id=None,
            resolved_issuer_id=None,
            normalized_ticker=normalized_ticker,
            normalized_exchange=normalized_exchange,
            matched_source_registry=None,
            match_rule="invalid_missing_ticker_or_exchange",
            explanation="Deterministic resolution requires both ticker and exchange after normalization.",
            conflict_count=0,
            candidate_count=0,
        )

    base_matches = [
        row
        for row in security_registry
        if normalize_ticker(row.get("ticker")) == normalized_ticker
        and normalize_exchange_code(row.get("exchange")) == normalized_exchange
        and bool(row.get("is_active", True))
    ]

    if normalized_security_type:
        narrowed_matches = [row for row in base_matches if (row.get("security_type") or "").strip().lower() == normalized_security_type]
        if len(narrowed_matches) == 1:
            row = narrowed_matches[0]
            return RegistryResolutionResult(
                resolution_status="accepted",
                resolved_security_id=row.get("security_id"),
                resolved_issuer_id=row.get("issuer_id"),
                normalized_ticker=normalized_ticker,
                normalized_exchange=normalized_exchange,
                matched_source_registry=row.get("matched_source_registry", row.get("source_name")),
                match_rule="exact_exchange_ticker_security_type",
                explanation="Accepted deterministic exact match on normalized exchange, ticker, and security type.",
                conflict_count=0,
                candidate_count=1,
            )
        if len(narrowed_matches) > 1:
            return RegistryResolutionResult(
                resolution_status="conflict",
                resolved_security_id=None,
                resolved_issuer_id=None,
                normalized_ticker=normalized_ticker,
                normalized_exchange=normalized_exchange,
                matched_source_registry=None,
                match_rule="multiple_registry_matches",
                explanation="Conflict: multiple active registry entries matched normalized exchange, ticker, and security type.",
                conflict_count=len(narrowed_matches),
                candidate_count=len(narrowed_matches),
            )

    if len(base_matches) == 1:
        row = base_matches[0]
        return RegistryResolutionResult(
            resolution_status="accepted",
            resolved_security_id=row.get("security_id"),
            resolved_issuer_id=row.get("issuer_id"),
            normalized_ticker=normalized_ticker,
            normalized_exchange=normalized_exchange,
            matched_source_registry=row.get("matched_source_registry", row.get("source_name")),
            match_rule="exact_exchange_ticker",
            explanation="Accepted deterministic exact match on normalized exchange and ticker.",
            conflict_count=0,
            candidate_count=1,
        )
    if len(base_matches) > 1:
        return RegistryResolutionResult(
            resolution_status="conflict",
            resolved_security_id=None,
            resolved_issuer_id=None,
            normalized_ticker=normalized_ticker,
            normalized_exchange=normalized_exchange,
            matched_source_registry=None,
            match_rule="multiple_registry_matches",
            explanation="Conflict: multiple active registry entries matched normalized exchange and ticker.",
            conflict_count=len(base_matches),
            candidate_count=len(base_matches),
        )

    return RegistryResolutionResult(
        resolution_status="no_match",
        resolved_security_id=None,
        resolved_issuer_id=None,
        normalized_ticker=normalized_ticker,
        normalized_exchange=normalized_exchange,
        matched_source_registry=None,
        match_rule="no_match",
        explanation="No active registry entry matched normalized exchange and ticker exactly.",
        conflict_count=0,
        candidate_count=0,
    )


def summarize_registry_resolution(results: list[RegistryResolutionResult]) -> dict[str, Any]:
    summary = {
        "registry_resolution_attempts": len(results),
        "registry_resolution_accepted": sum(1 for r in results if r.resolution_status == "accepted"),
        "registry_resolution_no_match": sum(1 for r in results if r.resolution_status == "no_match"),
        "registry_resolution_conflicts": sum(1 for r in results if r.resolution_status == "conflict"),
        "registry_resolution_invalid_input": sum(1 for r in results if r.resolution_status == "invalid_input"),
        "exact_exchange_ticker_matches": sum(1 for r in results if r.match_rule == "exact_exchange_ticker"),
        "exact_exchange_ticker_security_type_matches": sum(
            1 for r in results if r.match_rule == "exact_exchange_ticker_security_type"
        ),
        "deterministic_resolution_failures": sum(1 for r in results if r.resolution_status in {"conflict", "invalid_input"}),
    }
    summary["status"] = "success" if summary["deterministic_resolution_failures"] == 0 else "completed_with_findings"
    return summary


def _fixture_registry_records() -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for source_name, rows in SAMPLE_REGISTRY_SOURCES.items():
        for row in rows:
            out.append(
                {
                    "security_id": f"fixture::{source_name}::{row.get('primary_exchange')}::{row.get('ticker')}::{row.get('security_type')}",
                    "issuer_id": f"fixture::{row.get('sec_cik', 'unknown')}",
                    "ticker": row.get("ticker"),
                    "exchange": row.get("primary_exchange"),
                    "security_type": row.get("security_type"),
                    "is_active": True,
                    "source_name": source_name,
                }
            )
    return out


def run_sample_registry_resolution() -> dict[str, Any]:
    fixture_registry = _fixture_registry_records()
    attempts = [
        resolve_security_from_registry("MSFT", "NASDAQ", fixture_registry, security_type="equity"),
        resolve_security_from_registry("IBM", "NYSE", fixture_registry),
        resolve_security_from_registry("MISSING", "NASDAQ", fixture_registry),
        resolve_security_from_registry("AAPL", "NASDAQ", fixture_registry),
        resolve_security_from_registry("", "NASDAQ", fixture_registry),
    ]
    summary = summarize_registry_resolution(attempts)
    write_registry_resolution_summary(summary)
    emit_tier3h5_resolution_diagnostics(summary)
    return {"summary": summary, "results": [asdict(r) for r in attempts]}


if __name__ == "__main__":
    run_sample_registry_resolution()
