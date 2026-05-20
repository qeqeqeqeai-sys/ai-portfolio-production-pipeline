from __future__ import annotations

from typing import Any

from .fragility_signatures import compute_fragility_checksum


def _bound01(value: float) -> float:
    return max(0.0, min(1.0, round(float(value), 6)))


def _node_fragility(state: dict[str, Any]) -> dict[str, Any]:
    node_id = str(state.get("node_id", ""))
    overload = _bound01(float(state.get("overload", 0.0)))
    resilience = _bound01(float(state.get("resilience", 0.0)))
    fragmentation = _bound01(float(state.get("fragmentation", 0.0)))
    cascade_amplification = _bound01(float(state.get("cascade_amplification", overload * fragmentation)))
    relapse_persistence = _bound01(float(state.get("relapse_persistence", 1.0 - resilience)))
    fragility = _bound01(
        (overload * 0.35)
        + ((1.0 - resilience) * 0.30)
        + (fragmentation * 0.20)
        + (cascade_amplification * 0.10)
        + (relapse_persistence * 0.05)
    )
    return {
        "node_id": node_id,
        "fragility_score": fragility,
        "overload_contribution": overload,
        "resilience": resilience,
        "fragmentation_contribution": fragmentation,
        "cascade_amplification": cascade_amplification,
        "relapse_persistence": relapse_persistence,
    }


def compute_fragility_scores(node_states: list[dict[str, Any]]) -> dict[str, Any]:
    ranked = [_node_fragility(state) for state in sorted(node_states, key=lambda s: str(s.get("node_id", "")))]
    ranked = sorted(
        ranked,
        key=lambda x: (
            -x["fragility_score"],
            -x["overload_contribution"],
            x["resilience"],
            -x["fragmentation_contribution"],
            -x["cascade_amplification"],
            -x["relapse_persistence"],
            x["node_id"],
        ),
    )

    system_fragility = _bound01(sum(x["fragility_score"] for x in ranked) / max(1, len(ranked)))
    top = ranked[0] if ranked else {"node_id": "", "fragility_score": 0.0}
    out = {
        "node_fragility_ranking": ranked,
        "system_fragility_score": system_fragility,
        "node_count": len(ranked),
        "top_fragility_node": str(top.get("node_id", "")),
        "max_node_fragility_score": _bound01(float(top.get("fragility_score", 0.0))),
        "fragility_dispersion": _bound01(
            max((r["fragility_score"] for r in ranked), default=0.0)
            - min((r["fragility_score"] for r in ranked), default=0.0)
        ),
    }
    out["fragility_checksum"] = compute_fragility_checksum(out)
    return out


def compare_fragility_scores(a: dict[str, Any], b: dict[str, Any]) -> dict[str, Any]:
    delta = round(float(a.get("system_fragility_score", 0.0)) - float(b.get("system_fragility_score", 0.0)), 6)
    return {
        "system_fragility_delta": max(-1.0, min(1.0, delta)),
        "same_checksum": str(a.get("fragility_checksum", "")) == str(b.get("fragility_checksum", "")),
        "same_top_node": str(a.get("top_fragility_node", "")) == str(b.get("top_fragility_node", "")),
    }


def summarize_fragility_scores(fragility: dict[str, Any]) -> dict[str, Any]:
    return {
        "system_fragility_score": _bound01(float(fragility.get("system_fragility_score", 0.0))),
        "node_count": max(0, int(fragility.get("node_count", 0))),
        "top_fragility_node": str(fragility.get("top_fragility_node", "")),
        "max_node_fragility_score": _bound01(float(fragility.get("max_node_fragility_score", 0.0))),
        "fragility_checksum": str(fragility.get("fragility_checksum", "")),
    }
