"""B1 deterministic market snapshot builder (no runtime network I/O)."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, Iterable, List

from transmission_layers.expectation_failure.real_data.b1_benchmark_registry import build_fixed_benchmark_registry
from transmission_layers.expectation_failure.real_data.b1_real_entity_registry import build_fixed_real_entity_registry

SCORE_FIELDS = ("price_momentum_score", "fundamental_health_score", "expectation_pressure_score")


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def _bounded_score(row: dict, field: str, flags: List[str]) -> int:
    raw = row.get(field)
    if raw is None:
        flags.append(f"missing_{field}")
        return 50
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        flags.append(f"invalid_{field}")
        return 50
    score = _round_half_up(float(raw))
    if score < 0:
        flags.append(f"clamped_{field}")
        return 0
    if score > 100:
        flags.append(f"clamped_{field}")
        return 100
    return score


def build_deterministic_market_snapshot(raw_entity_inputs: Iterable[dict], raw_benchmark_inputs: Iterable[dict]) -> dict:
    entity_registry = build_fixed_real_entity_registry()
    benchmark_registry = build_fixed_benchmark_registry()
    entity_by_ticker = {row["ticker"]: deepcopy(row) for row in raw_entity_inputs}
    benchmark_by_symbol = {row["symbol"]: deepcopy(row) for row in raw_benchmark_inputs}

    entities: List[dict] = []
    for reg in entity_registry:
        src = entity_by_ticker.get(reg["ticker"], {})
        flags: List[str] = []
        normalized = {f: _bounded_score(src, f, flags) for f in SCORE_FIELDS}
        entities.append({**deepcopy(reg), **normalized, "evidence_quality_flags": sorted(set(flags))})

    benchmarks: List[dict] = []
    for reg in benchmark_registry:
        src = benchmark_by_symbol.get(reg["symbol"], {})
        value = _bounded_score(src, "benchmark_pressure_score", [])
        degraded = "available" if reg["symbol"] in benchmark_by_symbol else "missing"
        benchmarks.append({**deepcopy(reg), "benchmark_pressure_score": value, "data_status": degraded})

    return {
        "snapshot_stage": "B1_REAL_DATA_MARKET_SNAPSHOT",
        "entity_count": len(entities),
        "benchmark_count": len(benchmarks),
        "entities": entities,
        "benchmarks": benchmarks,
        "deterministic_sort_policy": "fixed_registry_order",
        "network_policy": "offline_only",
    }
