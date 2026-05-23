"""B1 deterministic benchmark registry."""

from __future__ import annotations

from typing import Dict, List, Tuple

FIXED_BENCHMARK_ORDER: Tuple[str, ...] = ("SOXX", "QQQ", "SPY")


def build_fixed_benchmark_registry() -> List[dict]:
    benchmark_type: Dict[str, str] = {"SOXX": "sector", "QQQ": "growth", "SPY": "broad_market"}
    return [
        {
            "benchmark_id": f"benchmark_{symbol}",
            "symbol": symbol,
            "deterministic_order": idx,
            "benchmark_type": benchmark_type[symbol],
            "registry_version": "b1_benchmark_registry_v1",
        }
        for idx, symbol in enumerate(FIXED_BENCHMARK_ORDER, start=1)
    ]
