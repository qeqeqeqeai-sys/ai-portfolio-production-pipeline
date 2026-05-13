"""Canonical normalization utilities for Phase 5A.2 structural intermediaries."""
from __future__ import annotations

import re
from typing import Iterable

_STOPWORDS = {"the", "and", "of", "for", "to", "in", "on", "a", "an"}
_MANUAL_SYNONYMS = {
    "data center": "data_centers",
    "data centers": "data_centers",
    "datacenter": "data_centers",
    "datacenters": "data_centers",
    "data centre": "data_centers",
    "data centres": "data_centers",
    "power grid": "power_grid",
    "electric grid": "power_grid",
    "electrical grid": "power_grid",
    "utilities": "utilities",
    "utility": "utilities",
    "semiconductors": "semiconductors",
    "semiconductor": "semiconductors",
    "chips": "semiconductors",
    "gpu": "gpu_compute",
    "gpus": "gpu_compute",
    "ai accelerator": "gpu_compute",
    "ai accelerators": "gpu_compute",
    "copper demand": "copper_demand",
    "copper": "copper",
}


def normalize_text(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip().lower()
    text = text.replace("&", " and ")
    text = re.sub(r"[\-/]+", " ", text)
    text = re.sub(r"[^a-z0-9\s_]+", " ", text)
    text = text.replace("_", " ")
    text = re.sub(r"\s+", " ", text).strip()
    if text in _MANUAL_SYNONYMS:
        return _MANUAL_SYNONYMS[text]
    tokens = [t for t in text.split() if t not in _STOPWORDS]
    if not tokens:
        return ""
    # conservative singular handling; avoid damaging terms such as gas
    cleaned = []
    for token in tokens:
        if len(token) > 4 and token.endswith("ies"):
            token = token[:-3] + "y"
        elif len(token) > 4 and token.endswith("s") and not token.endswith("ss"):
            token = token[:-1]
        cleaned.append(token)
    key = "_".join(cleaned)
    return _MANUAL_SYNONYMS.get(key.replace("_", " "), key)


def canonical_name(key: str) -> str:
    return key.replace("_", " ").title() if key else "Unknown"


def collect_normalized_forms(values: Iterable[object]) -> list[str]:
    forms = sorted({str(v).strip() for v in values if v is not None and str(v).strip()})
    return forms[:50]
