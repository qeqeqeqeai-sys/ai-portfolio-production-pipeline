"""Tier 3I Phase 3B deterministic regime drift intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

SCORING_VERSION = "3I.3B.v1"

_REQUIRED_METRICS = {
    "structural_fragility_score": "fragility_drift",
    "structural_stability_score": "stability_drift",
    "overheating_score": "overheating_drift",
    "fragmentation_score": "fragmentation_drift",
    "graph_concentration_score": "concentration_drift",
    "propagation_density_score": "propagation_density_drift",
}


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _transition_persistence_count(history: Sequence[Dict[str, Any]]) -> int:
    count = 0
    for record in reversed(history):
        if bool(record.get("regime_transition_warning", False)):
            count += 1
        else:
            break
    return count


def _regime_persistence_count(history: Sequence[Dict[str, Any]]) -> int:
    latest_state = str(history[-1].get("regime_state", "unknown"))
    count = 0
    for record in reversed(history):
        if str(record.get("regime_state", "unknown")) == latest_state:
            count += 1
        else:
            break
    return count


def _average_step_delta(history: Sequence[Dict[str, Any]], key: str) -> float:
    if len(history) < 2:
        return 0.0
    deltas = []
    for i in range(1, len(history)):
        prev = _to_float(history[i - 1].get(key), 0.0)
        cur = _to_float(history[i].get(key), 0.0)
        deltas.append(cur - prev)
    return sum(deltas) / len(deltas)


def compute_regime_drift(history: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = [dict(record) for record in history if isinstance(record, dict)]
    if len(ordered) < 2:
        return {
            "tier": "3I",
            "phase": "3B",
            "scoring_version": SCORING_VERSION,
            "drift_direction": "insufficient_history",
            "transition_state": "no_transition",
            "regime_drift_score": 0.0,
            "fragility_drift": 0.0,
            "stability_drift": 0.0,
            "overheating_drift": 0.0,
            "fragmentation_drift": 0.0,
            "concentration_drift": 0.0,
            "propagation_density_drift": 0.0,
            "regime_persistence_count": _regime_persistence_count(ordered) if ordered else 0,
            "transition_persistence_count": _transition_persistence_count(ordered) if ordered else 0,
            "deterioration_signal": 0.0,
            "improvement_signal": 0.0,
            "explainability_payload": {
                "drift_rationale": ["Insufficient structural regime history for deterministic drift computation."],
                "key_metric_deltas": {},
                "dominant_drift_drivers": [],
                "transition_explanation": "No transition assessment due to insufficient history.",
                "deterioration_warnings": [],
                "improvement_notes": [],
                "latest_regime_state": str(ordered[-1].get("regime_state", "unknown")) if ordered else "unknown",
                "previous_regime_state": "unknown",
            },
            "status": "success",
        }

    latest = ordered[-1]
    previous = ordered[-2]

    drifts: Dict[str, float] = {}
    deltas: Dict[str, float] = {}
    for key, drift_key in _REQUIRED_METRICS.items():
        delta = _to_float(latest.get(key), 0.0) - _to_float(previous.get(key), 0.0)
        deltas[key] = round(delta, 6)
        drifts[drift_key] = round(_clip01((delta + 1.0) / 2.0), 6)

    deterioration_signal = _clip01(
        0.30 * max(0.0, deltas["structural_fragility_score"])
        + 0.25 * max(0.0, deltas["overheating_score"])
        + 0.25 * max(0.0, deltas["fragmentation_score"])
        + 0.20 * max(0.0, deltas["graph_concentration_score"])
    )
    improvement_signal = _clip01(
        0.50 * max(0.0, deltas["structural_stability_score"])
        + 0.50 * max(0.0, deltas["propagation_density_score"])
    )

    net = improvement_signal - deterioration_signal
    if abs(net) <= 0.03:
        drift_direction = "stable"
    elif improvement_signal >= 0.04 and deterioration_signal >= 0.04:
        drift_direction = "mixed"
    elif net > 0:
        drift_direction = "improving"
    else:
        drift_direction = "deteriorating"

    transition_count = _transition_persistence_count(ordered)
    fragility_accel = _average_step_delta(ordered[-3:], "structural_fragility_score")
    overheating_accel = _average_step_delta(ordered[-3:], "overheating_score")
    cooling = deltas["overheating_score"] <= -0.03 and deltas["structural_stability_score"] >= 0.03
    if cooling:
        transition_state = "cooling_transition"
    elif transition_count >= 3 and (fragility_accel > 0.03 or overheating_accel > 0.03):
        transition_state = "accelerating_transition"
    elif transition_count >= 3:
        transition_state = "persistent_transition"
    elif transition_count >= 1:
        transition_state = "early_transition"
    else:
        transition_state = "no_transition"

    regime_persistence = _regime_persistence_count(ordered)
    regime_drift_score = _clip01(0.5 + ((deterioration_signal - improvement_signal) / 2.0))

    ranked_drivers = sorted(
        deltas.items(),
        key=lambda kv: (-abs(kv[1]), kv[0]),
    )
    dominant_drivers = [name for name, _ in ranked_drivers[:3]]

    deterioration_warnings: List[str] = []
    if deterioration_signal >= 0.08:
        deterioration_warnings.append("Deterioration pressure elevated from fragility/overheating/fragmentation/concentration drift.")
    if transition_state == "accelerating_transition":
        deterioration_warnings.append("Transition pressure is accelerating across recent structural summaries.")

    improvement_notes: List[str] = []
    if improvement_signal >= 0.08:
        improvement_notes.append("Stability and propagation density are improving together.")
    if transition_state == "cooling_transition":
        improvement_notes.append("Overheating is cooling while structural stability improves.")

    return {
        "tier": "3I",
        "phase": "3B",
        "scoring_version": SCORING_VERSION,
        "drift_direction": drift_direction,
        "transition_state": transition_state,
        "regime_drift_score": round(regime_drift_score, 6),
        **drifts,
        "regime_persistence_count": regime_persistence,
        "transition_persistence_count": transition_count,
        "deterioration_signal": round(deterioration_signal, 6),
        "improvement_signal": round(improvement_signal, 6),
        "explainability_payload": {
            "drift_rationale": [
                "Deterministic drift compares latest structural regime summary with immediate previous summary.",
                "Deterioration rises when fragility/overheating/fragmentation/concentration increase; improvement rises when stability and propagation density increase.",
            ],
            "key_metric_deltas": deltas,
            "dominant_drift_drivers": dominant_drivers,
            "transition_explanation": f"Transition state={transition_state} from transition_persistence_count={transition_count} and recent drift acceleration checks.",
            "deterioration_warnings": deterioration_warnings,
            "improvement_notes": improvement_notes,
            "latest_regime_state": str(latest.get("regime_state", "unknown")),
            "previous_regime_state": str(previous.get("regime_state", "unknown")),
        },
        "status": "success",
    }


def _sample_history() -> List[Dict[str, Any]]:
    return [
        {
            "run_date_sgt": "2026-01-01",
            "regime_state": "transitioning",
            "graph_concentration_score": 0.40,
            "fragmentation_score": 0.44,
            "overheating_score": 0.58,
            "propagation_density_score": 0.42,
            "structural_fragility_score": 0.52,
            "structural_stability_score": 0.45,
            "regime_transition_warning": True,
            "status": "success",
        },
        {
            "run_date_sgt": "2026-01-02",
            "regime_state": "transitioning",
            "graph_concentration_score": 0.42,
            "fragmentation_score": 0.41,
            "overheating_score": 0.54,
            "propagation_density_score": 0.50,
            "structural_fragility_score": 0.49,
            "structural_stability_score": 0.52,
            "regime_transition_warning": True,
            "status": "success",
        },
    ]


def main() -> None:
    input_path = Path("logs/tier3i_structural_regime_summary.json")
    if input_path.exists():
        raw = json.loads(input_path.read_text(encoding="utf-8"))
        history = raw if isinstance(raw, list) else [raw]
    else:
        history = _sample_history()

    summary = compute_regime_drift(history)
    output_path = Path("logs/tier3i_regime_drift_summary.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(
        "[tier3i] "
        f"drift_direction={summary['drift_direction']} "
        f"transition_state={summary['transition_state']} "
        f"drift_score={summary['regime_drift_score']:.3f} "
        f"status={summary['status']}"
    )


if __name__ == "__main__":
    main()
