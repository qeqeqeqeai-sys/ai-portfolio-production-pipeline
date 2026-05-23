"""B1 deterministic real entity registry for controlled expectation-failure snapshots."""

from __future__ import annotations

from copy import deepcopy
from types import MappingProxyType
from typing import Dict, Iterable, List, Mapping, Tuple

FIXED_ENTITY_ORDER: Tuple[str, ...] = (
    "NVDA",
    "AMD",
    "TSM",
    "ASML",
    "AVGO",
    "SMCI",
    "MSFT",
    "GOOGL",
    "META",
    "AMZN",
)

FIXED_SUBSECTOR_ORDER: Tuple[str, ...] = (
    "AI Infrastructure",
    "Semiconductor Supply Chain",
    "Hyperscaler AI Exposure",
    "AI Applications",
)

_ENTITY_SUBSECTOR_MAP: Dict[str, str] = {
    "NVDA": "AI Infrastructure",
    "AMD": "AI Infrastructure",
    "TSM": "Semiconductor Supply Chain",
    "ASML": "Semiconductor Supply Chain",
    "AVGO": "Semiconductor Supply Chain",
    "SMCI": "AI Infrastructure",
    "MSFT": "Hyperscaler AI Exposure",
    "GOOGL": "Hyperscaler AI Exposure",
    "META": "AI Applications",
    "AMZN": "Hyperscaler AI Exposure",
}


def build_fixed_real_entity_registry() -> List[dict]:
    """Return deterministic ordered registry with immutable field mapping."""
    registry: List[dict] = []
    for idx, ticker in enumerate(FIXED_ENTITY_ORDER, start=1):
        registry.append(
            {
                "entity_id": f"entity_{ticker}",
                "ticker": ticker,
                "entity_name": ticker,
                "deterministic_order": idx,
                "subsector": _ENTITY_SUBSECTOR_MAP[ticker],
                "registry_version": "b1_entity_registry_v1",
                "immutability_contract": "input_read_only",
            }
        )
    return registry


def build_entity_lookup_proxy(registry: Iterable[Mapping[str, object]]) -> Mapping[str, Mapping[str, object]]:
    """Return a mapping-proxy lookup keyed by ticker for immutable read behavior."""
    mutable = {str(row["ticker"]): deepcopy(dict(row)) for row in registry}
    immutable_inner = {k: MappingProxyType(v) for k, v in mutable.items()}
    return MappingProxyType(immutable_inner)
