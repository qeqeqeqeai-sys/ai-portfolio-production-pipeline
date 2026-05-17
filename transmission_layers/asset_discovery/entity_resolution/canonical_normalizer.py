from __future__ import annotations
import re

LEGAL_SUFFIXES = {"inc", "corp", "corporation", "ltd", "plc", "adr"}
ETF_TERMS = {"etf", "fund", "trust"}
GENERIC_TERMS = {"ai", "cloud", "chips", "software", "semiconductor", "market", "technology"}


def normalize_name(raw_name: str | None) -> str:
    text = (raw_name or "").strip().lower()
    text = re.sub(r"[\[\](){}$#@!,:;\"'`~^*+=?|\\/.-]", " ", text)
    tokens = [t for t in re.sub(r"\s+", " ", text).strip().split(" ") if t]
    filtered = [t for t in tokens if t not in LEGAL_SUFFIXES]
    return " ".join(filtered)


def guess_asset_type(raw_name: str | None, ticker: str | None, context: dict | None = None) -> str:
    text = f"{raw_name or ''} {context.get('source_title', '') if isinstance(context, dict) else ''}".lower()
    if any(t in text for t in ETF_TERMS):
        return "etf"
    if ticker:
        return "equity"
    return "unknown"


def is_generic_name(normalized_name: str) -> bool:
    tokens = set((normalized_name or "").split())
    return bool(tokens) and tokens.issubset(GENERIC_TERMS)
