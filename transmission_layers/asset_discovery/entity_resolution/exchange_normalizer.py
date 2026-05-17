from __future__ import annotations

EXCHANGE_MAP = {
    "NASDAQ": "XNAS", "NMS": "XNAS",
    "NYSE": "XNYS",
    "NYSE ARCA": "ARCX", "NYSEARCA": "ARCX", "ARCA": "ARCX",
    "LSE": "XLON",
    "HKEX": "XHKG", "SEHK": "XHKG",
    "SGX": "XSES",
    "TOKYO": "XTKS", "TSE": "XTKS",
}


def normalize_exchange(raw_exchange: str | None) -> str | None:
    if not raw_exchange:
        return None
    key = " ".join(str(raw_exchange).strip().upper().split())
    return EXCHANGE_MAP.get(key, key if len(key) <= 8 else None)
