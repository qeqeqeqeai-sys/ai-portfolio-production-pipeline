from __future__ import annotations

from typing import Any, Dict


def explain_recovery_dynamics(summary: Dict[str, Any]) -> str:
    durable = float(summary.get("recovery_durability_score", 0.0)) >= 0.6
    relapse = bool(summary.get("relapse_detected", False))
    persistence = float(summary.get("recovery_persistence_score", 0.0))
    if durable and not relapse:
        base = "resilience reinforcement persisted across replay windows."
    elif relapse:
        base = "recovery trajectory exhibited partial relapse behavior."
    else:
        base = "recovery durability remained bounded and stable."
    factors = [
        ("dominant_decay_factor", str(summary.get("dominant_decay_factor", "none"))),
        ("recovery_persistence_score", round(persistence, 6)),
        ("recovery_durability_score", round(float(summary.get("recovery_durability_score", 0.0)), 6)),
    ]
    suffix = "; ".join(f"{k}={v}" for k, v in factors)
    return f"{base} factors: {suffix}."[:280]
