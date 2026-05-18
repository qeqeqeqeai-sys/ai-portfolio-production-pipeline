from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_WHITESPACE = re.compile(r"\s+")
NORMALIZATION_VERSION = "tier3h5_phase2a_v1"

_EXCHANGE_ALIASES = {
    "NYSEARCA": "ARCA",
    "NYSE ARCA": "ARCA",
    "ARCA": "ARCA",
    "AMEX": "ARCA",
    "NYSEMKT": "ARCA",
    "NASDAQGS": "NASDAQ",
    "NASDAQGM": "NASDAQ",
    "NASDAQCM": "NASDAQ",
    "NASDAQ": "NASDAQ",
    "NYSE": "NYSE",
    "TSX": "TSX",
    "LSE": "LSE",
    "HKEX": "HKEX",
    "SGX": "SGX",
}

_SECURITY_TYPE_ALIASES = {
    "EQUITY": "equity",
    "COMMON_STOCK": "equity",
    "COMMON": "equity",
    "ETF": "etf",
    "ADR": "adr",
    "DEPOSITARY_RECEIPT": "adr",
    "REIT": "reit",
    "PREFERRED_SHARE": "preferred_share",
    "PREFERRED": "preferred_share",
    "WARRANT": "warrant",
    "UNIT": "unit",
}


def _collapse_spaces(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def normalize_exchange_code(exchange_code: str | None) -> str:
    if not exchange_code:
        return ""
    collapsed = _collapse_spaces(exchange_code).upper()
    compact = collapsed.replace(" ", "")
    return _EXCHANGE_ALIASES.get(compact) or _EXCHANGE_ALIASES.get(collapsed) or compact


def normalize_ticker(ticker: str | None) -> str:
    if not ticker:
        return ""
    cleaned = _collapse_spaces(ticker).upper()
    return cleaned.replace(" ", "").replace(".", "-").replace("/", "-")


def normalize_issuer_name(issuer_name: str | None) -> str:
    if not issuer_name:
        return ""
    cleaned = _collapse_spaces(issuer_name).upper()
    cleaned = cleaned.replace(".", "")
    return _collapse_spaces(cleaned)


def normalize_security_type(security_type: str | None) -> str:
    if not security_type:
        return "unknown"
    collapsed = _collapse_spaces(security_type).upper().replace("-", "_").replace(" ", "_")
    return _SECURITY_TYPE_ALIASES.get(collapsed, collapsed.lower())


def compute_source_record_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
