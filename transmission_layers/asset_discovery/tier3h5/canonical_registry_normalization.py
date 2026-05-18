from __future__ import annotations

import hashlib
import json
import re
from typing import Any

_WHITESPACE = re.compile(r"\s+")


def _collapse_spaces(value: str) -> str:
    return _WHITESPACE.sub(" ", value).strip()


def normalize_exchange_code(exchange_code: str | None) -> str:
    if not exchange_code:
        return ""
    return _collapse_spaces(exchange_code).upper().replace(" ", "")


def normalize_ticker(ticker: str | None) -> str:
    if not ticker:
        return ""
    cleaned = _collapse_spaces(ticker).upper()
    return cleaned.replace(" ", "").replace(".", "-")


def normalize_issuer_name(issuer_name: str | None) -> str:
    if not issuer_name:
        return ""
    cleaned = _collapse_spaces(issuer_name).upper()
    cleaned = cleaned.replace(".", "")
    return _collapse_spaces(cleaned)


def compute_source_record_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
