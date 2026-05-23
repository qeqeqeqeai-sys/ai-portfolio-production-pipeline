"""B3 deterministic mapping from B2 accepted records to B1-compatible snapshot inputs."""

from __future__ import annotations

from copy import deepcopy
from typing import Dict, Iterable, List

from .b1_benchmark_registry import FIXED_BENCHMARK_ORDER, build_fixed_benchmark_registry
from .b1_real_entity_registry import FIXED_ENTITY_ORDER, build_fixed_real_entity_registry

METRIC_POLICY = {
    "required_for_certified": (
        "forward_pe",
        "ev_to_ebitda",
        "price_momentum_30d",
        "price_momentum_90d",
        "realized_volatility",
        "benchmark_relative_return",
        "price",
    ),
    "required_for_degraded": ("price", "realized_volatility"),
    "optional_context": (),
}

ENTITY_FIELDS = (
    ("valuation_metrics", ("forward_pe", "ev_to_ebitda")),
    ("momentum_metrics", ("price_momentum_30d", "price_momentum_90d")),
    ("volatility_metrics", ("realized_volatility",)),
    ("benchmark_relative_metrics", ("benchmark_relative_return",)),
)


def _index_records(records: Iterable[dict]) -> Dict[str, Dict[str, dict]]:
    by_symbol: Dict[str, Dict[str, dict]] = {}
    for record in records:
        by_symbol.setdefault(record["symbol"], {})[record["metric_name"]] = deepcopy(record)
    return by_symbol


def map_b2_candidate_to_b1_snapshot_inputs(accepted_records: list[dict], as_of_date: str) -> dict:
    indexed = _index_records(deepcopy(accepted_records))
    entity_registry = build_fixed_real_entity_registry()
    benchmark_registry = build_fixed_benchmark_registry()

    entity_inputs: List[dict] = []
    b1_entity_scores: List[dict] = []
    for ent in entity_registry:
        metrics = indexed.get(ent["ticker"], {})
        missing_required = sorted([m for m in METRIC_POLICY["required_for_certified"] if m not in metrics])
        evidence_flags = [f"missing_{m}" for m in missing_required]
        payload = {"ticker": ent["ticker"], "subsector": ent["subsector"], "observation_date": as_of_date}
        for key, metric_names in ENTITY_FIELDS:
            payload[key] = {m: metrics.get(m, {}).get("metric_value") for m in metric_names}
        payload["price_metrics"] = {"price": metrics.get("price", {}).get("metric_value")}
        payload["evidence_flags"] = evidence_flags
        payload["source_trace"] = {
            m: {"source": metrics[m].get("source"), "source_timestamp": metrics[m].get("source_timestamp")}
            for m in sorted(metrics)
        }
        entity_inputs.append(payload)
        b1_entity_scores.append(
            {
                "ticker": ent["ticker"],
                "price_momentum_score": metrics.get("price_momentum_30d", {}).get("metric_value", 50),
                "fundamental_health_score": metrics.get("forward_pe", {}).get("metric_value", 50),
                "expectation_pressure_score": metrics.get("benchmark_relative_return", {}).get("metric_value", 50),
            }
        )

    benchmark_inputs: List[dict] = []
    b1_benchmark_scores: List[dict] = []
    for bmk in benchmark_registry:
        metrics = indexed.get(bmk["symbol"], {})
        score = metrics.get("benchmark_relative_return", {}).get("metric_value", 50)
        benchmark_inputs.append(
            {
                "symbol": bmk["symbol"],
                "observation_date": as_of_date,
                "benchmark_metrics": {"benchmark_relative_return": metrics.get("benchmark_relative_return", {}).get("metric_value")},
                "evidence_flags": [] if "benchmark_relative_return" in metrics else ["missing_benchmark_relative_return"],
                "source_trace": {
                    m: {"source": metrics[m].get("source"), "source_timestamp": metrics[m].get("source_timestamp")}
                    for m in sorted(metrics)
                },
            }
        )
        b1_benchmark_scores.append({"symbol": bmk["symbol"], "benchmark_pressure_score": score})

    mapping_summary = {
        "entity_order": list(FIXED_ENTITY_ORDER),
        "benchmark_order": list(FIXED_BENCHMARK_ORDER),
        "metric_policy": deepcopy(METRIC_POLICY),
    }

    return {
        "entity_snapshot_inputs": entity_inputs,
        "benchmark_snapshot_inputs": benchmark_inputs,
        "b1_entity_score_inputs": b1_entity_scores,
        "b1_benchmark_score_inputs": b1_benchmark_scores,
        "mapping_summary": mapping_summary,
    }
