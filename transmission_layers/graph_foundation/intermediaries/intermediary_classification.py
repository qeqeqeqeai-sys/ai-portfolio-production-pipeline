"""Deterministic rule-based classification for structural intermediary nodes."""
from __future__ import annotations

_RULES: list[tuple[str, tuple[str, ...]]] = [
    ("infrastructure", ("grid", "utility", "utilities", "infrastructure", "transmission", "pipeline", "network")),
    ("energy", ("power", "energy", "electric", "gas", "oil", "renewable", "nuclear", "solar", "battery")),
    ("compute", ("compute", "gpu", "cloud", "data_center", "server", "hyperscaler", "ai_accelerator")),
    ("semiconductor", ("semiconductor", "chip", "foundry", "memory", "hbm", "wafer", "lithography")),
    ("supply_chain", ("supply", "supplier", "inventory", "manufacturing", "capacity", "input", "component")),
    ("capital_flow", ("capital", "funding", "capex", "investment", "valuation", "multiple", "earnings")),
    ("macro_pressure", ("inflation", "rates", "yield", "credit", "spread", "dollar", "macro")),
    ("demand_transmission", ("demand", "consumption", "order", "booking", "revenue", "adoption")),
    ("liquidity", ("liquidity", "flow", "volume", "risk_appetite", "fund_flow")),
    ("policy", ("policy", "regulation", "tariff", "subsidy", "export", "government")),
    ("industrial", ("industrial", "copper", "steel", "mining", "commodity", "materials")),
    ("logistics", ("shipping", "freight", "logistics", "port", "transport")),
]


def classify_intermediary(intermediary_key: str) -> str:
    key = (intermediary_key or "").lower()
    for category, needles in _RULES:
        if any(n in key for n in needles):
            return category
    return "uncategorized"
