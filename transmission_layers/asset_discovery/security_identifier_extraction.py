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
_EXPLICIT_EXCHANGE_TICKER_EVIDENCE = re.compile(r"(?i)(?:\(|\[)?\s*(NASDAQ|Nasdaq|NasdaqGS|Nasdaq Global Select Market|NYSE|New York Stock Exchange|NYSEARCA|NYSE Arca|Arca|LSE|London Stock Exchange|HKEX|Hong Kong Stock Exchange|SGX|Singapore Exchange|TSE|Tokyo Stock Exchange)\s*:\s*([A-Z0-9]{1,6})\s*(?:\)|\])?")
_EXPLICIT_SYMBOL_FIELD = re.compile(r"(?i)\b(?:Ticker|Symbol)\s*:\s*([A-Z0-9]{1,6})\b")
_EXCHANGE_NORMALIZATION = {
    "nasdaq": "NASDAQ", "nasdaqgs": "NASDAQ", "nasdaq global select market": "NASDAQ",
    "nyse": "NYSE", "new york stock exchange": "NYSE",
    "nysearca": "NYSEARCA", "nyse arca": "NYSEARCA", "arca": "NYSEARCA",
    "lse": "LSE", "london stock exchange": "LSE",
    "hkex": "HKEX", "hong kong stock exchange": "HKEX",
    "sgx": "SGX", "singapore exchange": "SGX",
    "tse": "TSE", "tokyo stock exchange": "TSE",
}


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


def extract_security_identifiers_from_evidence(
    evidence_text: str | None,
    source_title: str | None,
    source_url: str | None,
    raw_evidence: dict | None,
    candidate_ticker: str | None = None,
    candidate_exchange: str | None = None,
) -> dict:
    warnings: list[str] = []
    extraction_notes: dict[str, str | None] = {"source_url": source_url}
    extraction_method = "none"
    extracted_ticker = None
    extracted_exchange = None
    normalized_ticker = None
    normalized_exchange = None
    text_parts = [evidence_text, source_title, source_url]
    if isinstance(raw_evidence, dict):
        text_parts.extend([str(raw_evidence.get("evidence_text") or ""), str(raw_evidence.get("source_title") or ""), str(raw_evidence.get("source_url") or "")])
    haystack = " ".join([p for p in text_parts if p]).strip()

    m = _EXPLICIT_EXCHANGE_TICKER_EVIDENCE.search(haystack)
    if m:
        extracted_exchange = m.group(1)
        extracted_ticker = m.group(2).upper()
        extraction_method = "explicit_exchange_ticker_regex"
    else:
        m2 = _EXPLICIT_SYMBOL_FIELD.search(haystack)
        if m2:
            extracted_ticker = m2.group(1).upper()
            extraction_method = "explicit_symbol_field_regex"

    if not extracted_ticker and candidate_ticker:
        t, suspicious = normalize_ticker(candidate_ticker)
        if not suspicious and t not in INVALID_UPPERCASE_WORDS:
            extracted_ticker = t
            extraction_method = "structured_candidate_ticker_field"
        elif suspicious:
            warnings.append("invalid_ticker_pattern")

    if not extracted_exchange and candidate_exchange:
        extracted_exchange = candidate_exchange
        extraction_method = "structured_candidate_fields" if extraction_method == "none" else extraction_method

    if extracted_ticker:
        normalized_ticker, suspicious = normalize_ticker(extracted_ticker)
        if suspicious or normalized_ticker in INVALID_UPPERCASE_WORDS:
            warnings.append("invalid_ticker_pattern")
            extracted_ticker = None
            normalized_ticker = None
    if extracted_exchange:
        normalized_exchange = _EXCHANGE_NORMALIZATION.get(str(extracted_exchange).strip().lower())
        if not normalized_exchange:
            warnings.append("unknown_exchange_variant")
    confidence = 1.0 if extracted_ticker else 0.0
    return {
        "extracted_ticker": extracted_ticker,
        "extracted_exchange": extracted_exchange,
        "normalized_ticker": normalized_ticker,
        "normalized_exchange": normalized_exchange,
        "extraction_method": extraction_method,
        "extraction_confidence": confidence,
        "extraction_notes": extraction_notes,
        "warnings": warnings,
    }
