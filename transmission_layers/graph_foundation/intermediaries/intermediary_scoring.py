"""Explainable scoring for Phase 5A.2 structural intermediaries."""
from __future__ import annotations

import math
from typing import Any


def _bounded_log_score(value: int, scale: float = 5.0) -> float:
    if value <= 0:
        return 0.0
    return min(1.0, math.log1p(value) / math.log1p(scale))


def calculate_scores(row: dict[str, Any]) -> dict[str, Any]:
    inbound = int(row.get("inbound_edge_count", 0) or 0)
    outbound = int(row.get("outbound_edge_count", 0) or 0)
    source_theme_count = int(row.get("source_theme_count", 0) or 0)
    target_theme_count = int(row.get("target_theme_count", 0) or 0)
    evidence_density = float(row.get("evidence_density", 0) or 0)

    inbound_score = _bounded_log_score(inbound)
    outbound_score = _bounded_log_score(outbound)
    balance_score = 0.0 if max(inbound, outbound) == 0 else min(inbound, outbound) / max(inbound, outbound)
    theme_reuse_score = _bounded_log_score(source_theme_count + target_theme_count, scale=6.0)
    continuity_potential = (inbound_score * outbound_score) ** 0.5 if inbound and outbound else 0.0
    evidence_score = max(0.0, min(1.0, evidence_density))

    activation = (
        0.24 * inbound_score
        + 0.24 * outbound_score
        + 0.20 * continuity_potential
        + 0.14 * balance_score
        + 0.10 * theme_reuse_score
        + 0.08 * evidence_score
    )

    component_scores = {
        "inbound_connectivity": round(inbound_score, 6),
        "outbound_connectivity": round(outbound_score, 6),
        "continuity_potential": round(continuity_potential, 6),
        "bridge_balance": round(balance_score, 6),
        "theme_reuse": round(theme_reuse_score, 6),
        "evidence_density": round(evidence_score, 6),
    }
    return {
        "continuity_potential": round(continuity_potential, 6),
        "intermediary_activation_score": round(activation, 6),
        "component_scores": component_scores,
    }
