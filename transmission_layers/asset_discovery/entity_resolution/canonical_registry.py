from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanonicalEntity:
    ticker: str
    exchange: str
    canonical_name: str
    asset_type: str
    aliases: tuple[str, ...] = ()


REGISTRY: tuple[CanonicalEntity, ...] = (
    CanonicalEntity("NVDA", "XNAS", "NVIDIA Corporation", "equity", ("nvidia",)),
    CanonicalEntity("MSFT", "XNAS", "Microsoft Corporation", "equity", ("microsoft",)),
    CanonicalEntity("AAPL", "XNAS", "Apple Inc.", "equity", ("apple",)),
    CanonicalEntity("AMZN", "XNAS", "Amazon.com Inc.", "equity", ("amazon",)),
    CanonicalEntity("GOOGL", "XNAS", "Alphabet Inc.", "equity", ("alphabet", "google")),
    CanonicalEntity("META", "XNAS", "Meta Platforms Inc.", "equity", ("meta", "facebook")),
    CanonicalEntity("AMD", "XNAS", "Advanced Micro Devices Inc.", "equity", ("advanced micro devices",)),
    CanonicalEntity("AVGO", "XNAS", "Broadcom Inc.", "equity", ("broadcom",)),
    CanonicalEntity("TSM", "XNYS", "Taiwan Semiconductor Manufacturing Company Limited", "equity", ("tsmc", "taiwan semiconductor")),
    CanonicalEntity("ASML", "XNAS", "ASML Holding N.V.", "equity", ("asml holding",)),
    CanonicalEntity("SMH", "ARCX", "VanEck Semiconductor ETF", "etf", ("vaneck semiconductor etf",)),
    CanonicalEntity("SOXX", "XNAS", "iShares Semiconductor ETF", "etf", ("ishares semiconductor etf",)),
    CanonicalEntity("QQQ", "XNAS", "Invesco QQQ Trust", "etf", ("invesco qqq",)),
)


def _norm(value: str | None) -> str:
    return (value or "").strip().lower()


def lookup_by_ticker(ticker: str | None) -> list[CanonicalEntity]:
    t = (ticker or "").strip().upper()
    if not t:
        return []
    return [row for row in REGISTRY if row.ticker == t]


def lookup_by_name(normalized_name: str | None) -> list[CanonicalEntity]:
    n = _norm(normalized_name)
    if not n:
        return []
    return [row for row in REGISTRY if _norm(row.canonical_name) == n]


def lookup_by_alias(normalized_name: str | None) -> list[CanonicalEntity]:
    n = _norm(normalized_name)
    if not n:
        return []
    return [row for row in REGISTRY if n in {_norm(a) for a in row.aliases}]
