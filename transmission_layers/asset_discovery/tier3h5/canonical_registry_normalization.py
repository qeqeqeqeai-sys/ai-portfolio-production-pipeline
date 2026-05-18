from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from typing import Any

_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[^A-Z0-9]")
_PUNCT_TO_SPACE_RE = re.compile(r"[\-_,./:;()\[\]{}'\"`]+")


def _unicode_normalize(value: str) -> str:
    return unicodedata.normalize("NFKC", value)


def normalize_exchange_code(value: str | None) -> str:
    if not value:
        return "UNKNOWN"
    cleaned = _unicode_normalize(value).upper().strip()
    cleaned = _NON_ALNUM_RE.sub("", cleaned)
    return cleaned or "UNKNOWN"


def normalize_ticker(value: str | None) -> str:
    if not value:
        return ""
    cleaned = _unicode_normalize(value).upper().strip()
    cleaned = _WHITESPACE_RE.sub("", cleaned)
    cleaned = _NON_ALNUM_RE.sub("", cleaned)
    return cleaned


def normalize_issuer_name(value: str | None) -> str:
    if not value:
        return ""
    cleaned = _unicode_normalize(value).upper().strip()
    cleaned = _PUNCT_TO_SPACE_RE.sub(" ", cleaned)
    cleaned = _WHITESPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def compute_source_record_hash(record: dict[str, Any]) -> str:
    payload = json.dumps(record, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
