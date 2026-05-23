"""B1 deterministic fragility payload construction."""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, ROUND_HALF_UP
from typing import List


def _round_half_up(value: float) -> int:
    return int(Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def build_deterministic_fragility_payload(snapshot: dict) -> dict:
    entities: List[dict] = []
    for row in snapshot.get("entities", []):
        fragility = _round_half_up(
            (row["expectation_pressure_score"] * 0.5)
            + ((100 - row["fundamental_health_score"]) * 0.3)
            + (row["price_momentum_score"] * 0.2)
        )
        benchmark_relative = "IN_LINE"
        if fragility >= 70:
            benchmark_relative = "ELEVATED"
        elif fragility <= 35:
            benchmark_relative = "RESILIENT"
        explanation = (
            f"{row['ticker']} deterministic fragility={fragility} derived from bounded scores "
            "(expectation pressure, inverse fundamental health, momentum). "
            "Interpretation is structural and not a trading recommendation."
        )
        entities.append(
            {
                **deepcopy(row),
                "fragility_score": max(0, min(100, fragility)),
                "benchmark_relative_interpretation": benchmark_relative,
                "explanation_template_id": "b1_fragility_template_v1",
                "explanation": explanation,
            }
        )

    return {
        "payload_stage": "B1_REAL_DATA_FRAGILITY_PAYLOAD",
        "entities": entities,
        "benchmarks": deepcopy(snapshot.get("benchmarks", [])),
        "deterministic_output_bounds": "0_100",
    }
