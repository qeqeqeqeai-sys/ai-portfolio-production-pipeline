from __future__ import annotations

import re
from dataclasses import dataclass

from transmission_layers.asset_discovery.entity_resolution.canonical_registry import REGISTRY
from transmission_layers.asset_discovery.entity_resolution.exchange_normalizer import EXCHANGE_MAP, normalize_exchange
from transmission_layers.asset_discovery.entity_resolution.ticker_normalizer import normalize_ticker

INVALID_UPPERCASE_WORDS = {"AI", "ON", "OR", "IT"}


@dataclass(frozen=True)
class SecurityIdentifierResult:
    extracted_ticker: str | None
    raw_exchange: str | None
    normalized_exchange: str | None
    security_type: str
    canonical_security_id: str | None
    identifier_source: str
    identifier_method: str
    identifier_confidence: float
    identifier_status: str
    identifier_explanation: str
    identifier_warnings: list[str]


_ALIAS_MAP = {
    alias.strip().lower(): entity for entity in REGISTRY for alias in entity.aliases
}
_CANONICAL_ID_MAP = {
    f"{entity.exchange}:{entity.ticker}": entity for entity in REGISTRY
}
_TICKER_EXCHANGE_MAP = {(entity.ticker, entity.exchange): entity for entity in REGISTRY}

_EXPLICIT_EXCHANGE_TICKER = re.compile(r"\b([A-Z][A-Z\s]{1,12}[A-Z]):\s*([A-Z][A-Z0-9.-]{0,7})\b")


def _security_type_from_entity(entity) -> str:
    if not entity:
        return "unknown"
    if entity.asset_type == "equity":
        return "company"
    if entity.asset_type in {"etf", "index"}:
        return entity.asset_type
    return "unknown"


def extract_security_identifier(candidate: dict) -> SecurityIdentifierResult:
    raw_name = str(candidate.get("candidate_name") or candidate.get("raw_entity_name") or "")
    raw_exchange = candidate.get("exchange") or candidate.get("candidate_exchange")
    explicit_ticker = candidate.get("ticker") or candidate.get("candidate_ticker")

    warnings: list[str] = []
    method = "none"
    source = "none"
    extracted_ticker = None
    normalized_exchange = normalize_exchange(raw_exchange)
    matched_entity = None

    # explicit exchange:ticker in text
    match = _EXPLICIT_EXCHANGE_TICKER.search(raw_name.upper())
    if match:
        source = "candidate_name"
        method = "explicit_exchange_ticker_pattern"
        raw_exchange = match.group(1)
        normalized_exchange = normalize_exchange(raw_exchange)
        extracted_ticker, suspicious = normalize_ticker(match.group(2))
        if suspicious:
            warnings.append("suspicious_extracted_ticker")

    if not extracted_ticker and explicit_ticker:
        source = "candidate_ticker"
        method = "explicit_ticker_field"
        extracted_ticker, suspicious = normalize_ticker(explicit_ticker)
        if suspicious:
            warnings.append("suspicious_extracted_ticker")

    if extracted_ticker in INVALID_UPPERCASE_WORDS:
        warnings.append("suppressed_invalid_uppercase_word")
        extracted_ticker = None

    canonical_id = candidate.get("canonical_security_id")
    if canonical_id and canonical_id in _CANONICAL_ID_MAP:
        method = "exact_canonical_security_id"
        source = "canonical_security_id"
        matched_entity = _CANONICAL_ID_MAP[canonical_id]
        extracted_ticker = matched_entity.ticker
        normalized_exchange = matched_entity.exchange

    if not matched_entity and extracted_ticker and normalized_exchange:
        matched_entity = _TICKER_EXCHANGE_MAP.get((extracted_ticker, normalized_exchange))
        if matched_entity:
            method = "exact_ticker_exchange_registry_match"
            source = "ticker_exchange"

    if not matched_entity and raw_name:
        alias_hit = _ALIAS_MAP.get(raw_name.strip().lower())
        if alias_hit:
            matched_entity = alias_hit
            method = "exact_alias_registry_match"
            source = "alias_registry"
            extracted_ticker = extracted_ticker or alias_hit.ticker
            normalized_exchange = normalized_exchange or alias_hit.exchange

    security_type = _security_type_from_entity(matched_entity)
    if security_type == "unknown" and extracted_ticker:
        security_type = "unknown"

    if matched_entity:
        status = "resolved"
        confidence = 1.0
        explanation = "Exact deterministic registry match found."
        canonical_security_id = f"{matched_entity.exchange}:{matched_entity.ticker}"
    elif extracted_ticker:
        status = "unresolved"
        confidence = 0.0
        explanation = "Ticker extracted deterministically but no exact registry match found."
        canonical_security_id = None
    else:
        status = "suppressed"
        confidence = 0.0
        explanation = "No deterministic security identifier evidence found."
        canonical_security_id = None

    return SecurityIdentifierResult(
        extracted_ticker=extracted_ticker,
        raw_exchange=raw_exchange,
        normalized_exchange=normalized_exchange,
        security_type=security_type,
        canonical_security_id=canonical_security_id,
        identifier_source=source,
        identifier_method=method,
        identifier_confidence=confidence,
        identifier_status=status,
        identifier_explanation=explanation,
        identifier_warnings=warnings,
    )
