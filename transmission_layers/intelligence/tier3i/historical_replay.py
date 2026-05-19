"""Tier 3I Phase 3D deterministic historical structural replay."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Tuple

SCORING_VERSION = "3I.3D.v1"

FRAGILE_STATES = {"fragile", "overheated", "contagious", "transitioning", "deteriorating"}
OVERHEATED_STATES = {"overheated"}
CONTAGIOUS_STATES = {"amplified", "spreading", "contaminated", "fragile", "bottlenecked"}
RECOVERY_STATES = {"stable", "improving", "contained"}


def _clip01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_list(value: Any) -> List[Any]:
    return list(value) if isinstance(value, Sequence) and not isinstance(value, (str, bytes)) else []


def _normalize_delta(start: float, end: float) -> float:
    return _clip01(abs(end - start))


def _dedupe_sort(records: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sorted_records = sorted((dict(r) for r in records), key=lambda r: (str(r.get("run_date_sgt", "")), str(r.get("source_id", ""))))
    by_date: Dict[str, Dict[str, Any]] = {}
    for rec in sorted_records:
        by_date[str(rec.get("run_date_sgt", ""))] = rec
    return [by_date[d] for d in sorted(by_date.keys())]


def _is_fragile(rec: Dict[str, Any]) -> bool:
    return _to_float(rec.get("structural_fragility_score")) >= 0.6 or str(rec.get("regime_state", "")).lower() in FRAGILE_STATES


def _is_overheated(rec: Dict[str, Any]) -> bool:
    return _to_float(rec.get("overheating_score")) >= 0.6 or str(rec.get("regime_state", "")).lower() in OVERHEATED_STATES


def _is_contagious(rec: Dict[str, Any]) -> bool:
    return _to_float(rec.get("contagion_pressure_score")) >= 0.6 or str(rec.get("contagion_risk_state", "")).lower() in CONTAGIOUS_STATES


def _is_recovery_state(rec: Dict[str, Any]) -> bool:
    return str(rec.get("regime_state", "")).lower() in RECOVERY_STATES or str(rec.get("drift_direction", "")).lower() in {"improving", "stable"}


def build_historical_structural_replay(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    ordered = _dedupe_sort(records)
    n = len(ordered)
    latest = ordered[-1] if ordered else {}
    earliest = ordered[0] if ordered else {}

    memory_band = "thin" if n < 3 else "usable" if n <= 5 else "strong"

    base = {
        "tier": "3I",
        "phase": "3D",
        "scoring_version": SCORING_VERSION,
        "replay_window_size": n,
        "replay_start_date": earliest.get("run_date_sgt") if ordered else None,
        "replay_end_date": latest.get("run_date_sgt") if ordered else None,
        "latest_regime_state": latest.get("regime_state", "unknown"),
        "latest_drift_direction": latest.get("drift_direction", "unknown"),
        "latest_contagion_risk_state": latest.get("contagion_risk_state", "unknown"),
        "structural_memory_band": memory_band,
    }

    peaks = {
        "historical_fragility_peak": max((_to_float(r.get("structural_fragility_score")) for r in ordered), default=0.0),
        "historical_overheating_peak": max((_to_float(r.get("overheating_score")) for r in ordered), default=0.0),
        "historical_contagion_peak": max((_to_float(r.get("contagion_pressure_score")) for r in ordered), default=0.0),
        "historical_fragmentation_peak": max((_to_float(r.get("fragmentation_score")) for r in ordered), default=0.0),
        "historical_stability_peak": max((_to_float(r.get("structural_stability_score")) for r in ordered), default=0.0),
    }

    if n < 2:
        return {
            **base,
            **{k: round(v, 6) for k, v in peaks.items()},
            "fragility_trend_score": 0.0,
            "overheating_trend_score": 0.0,
            "contagion_trend_score": 0.0,
            "stability_trend_score": 0.0,
            "fragmentation_trend_score": 0.0,
            "regime_transition_count": 0,
            "drift_reversal_count": 0,
            "contagion_state_change_count": 0,
            "persistent_fragility_count": 0,
            "persistent_overheating_count": 0,
            "persistent_contagion_count": 0,
            "recovery_count": 0,
            "structural_replay_score": 0.0,
            "replay_health_state": "insufficient_history",
            "replay_transition_warning": False,
            "explainability_payload": {"warnings": ["Insufficient historical records for replay trend analysis."]},
            "status": "success",
        }

    ft = _normalize_delta(_to_float(earliest.get("structural_fragility_score")), _to_float(latest.get("structural_fragility_score")))
    ot = _normalize_delta(_to_float(earliest.get("overheating_score")), _to_float(latest.get("overheating_score")))
    ct = _normalize_delta(_to_float(earliest.get("contagion_pressure_score")), _to_float(latest.get("contagion_pressure_score")))
    st = _normalize_delta(_to_float(earliest.get("structural_stability_score")), _to_float(latest.get("structural_stability_score")))
    fragmt = _normalize_delta(_to_float(earliest.get("fragmentation_score")), _to_float(latest.get("fragmentation_score")))

    regime_transition_count = sum(1 for a, b in zip(ordered, ordered[1:]) if str(a.get("regime_state", "")) != str(b.get("regime_state", "")))
    drift_reversal_count = sum(1 for a, b in zip(ordered, ordered[1:]) if {str(a.get("drift_direction", "")).lower(), str(b.get("drift_direction", "")).lower()} == {"improving", "deteriorating"})
    contagion_state_change_count = sum(1 for a, b in zip(ordered, ordered[1:]) if str(a.get("contagion_risk_state", "")) != str(b.get("contagion_risk_state", "")))

    persistent_fragility_count = sum(1 for a, b in zip(ordered, ordered[1:]) if _is_fragile(a) and _is_fragile(b))
    persistent_overheating_count = sum(1 for a, b in zip(ordered, ordered[1:]) if _is_overheated(a) and _is_overheated(b))
    persistent_contagion_count = sum(1 for a, b in zip(ordered, ordered[1:]) if _is_contagious(a) and _is_contagious(b))

    def _risky(x: Dict[str, Any]) -> bool:
        return _is_fragile(x) or _is_overheated(x) or _is_contagious(x)

    recovery_count = sum(1 for a, b in zip(ordered, ordered[1:]) if _risky(a) and _is_recovery_state(b))

    deterioration_score = _clip01((ft + ot + ct + fragmt) / 4.0)
    improvement_score = _clip01(st)
    persistence_intensity = _clip01((persistent_fragility_count + persistent_overheating_count + persistent_contagion_count) / max(1, (n - 1) * 3))
    transition_intensity = _clip01((regime_transition_count + drift_reversal_count + contagion_state_change_count) / max(1, (n - 1) * 3))
    latest_risk = _clip01((_to_float(latest.get("structural_fragility_score")) + _to_float(latest.get("overheating_score")) + _to_float(latest.get("contagion_pressure_score"))) / 3.0)

    structural_replay_score = _clip01((0.30 * deterioration_score) + (0.20 * transition_intensity) + (0.20 * persistence_intensity) + (0.20 * latest_risk) + (0.10 * (1.0 - improvement_score)))

    stable_count = sum(1 for r in ordered if str(r.get("regime_state", "")).lower() == "stable")
    if stable_count >= max(2, n // 2) and latest_risk < 0.35 and max(peaks.values()) < 0.65:
        health = "historically_stable"
    elif persistent_fragility_count >= max(persistent_overheating_count, persistent_contagion_count) and persistent_fragility_count >= 2:
        health = "historically_fragile"
    elif persistent_overheating_count > persistent_contagion_count and persistent_overheating_count >= 2:
        health = "historically_overheated"
    elif persistent_contagion_count >= 2:
        health = "historically_contagious"
    elif deterioration_score >= improvement_score + 0.05:
        health = "historically_deteriorating"
    elif improvement_score > deterioration_score + 0.1:
        health = "historically_improving"
    else:
        health = "historically_mixed"

    warning = transition_intensity >= 0.55 or persistence_intensity >= 0.50
    drivers = []
    if ft > 0.1:
        drivers.append("fragility_trend_score")
    if ot > 0.1:
        drivers.append("overheating_trend_score")
    if ct > 0.1:
        drivers.append("contagion_trend_score")
    if fragmt > 0.1:
        drivers.append("fragmentation_trend_score")
    if st > 0.1:
        drivers.append("stability_trend_score")

    return {
        **base,
        **{k: round(v, 6) for k, v in peaks.items()},
        "fragility_trend_score": round(ft, 6),
        "overheating_trend_score": round(ot, 6),
        "contagion_trend_score": round(ct, 6),
        "stability_trend_score": round(st, 6),
        "fragmentation_trend_score": round(fragmt, 6),
        "regime_transition_count": regime_transition_count,
        "drift_reversal_count": drift_reversal_count,
        "contagion_state_change_count": contagion_state_change_count,
        "persistent_fragility_count": persistent_fragility_count,
        "persistent_overheating_count": persistent_overheating_count,
        "persistent_contagion_count": persistent_contagion_count,
        "recovery_count": recovery_count,
        "structural_replay_score": round(structural_replay_score, 6),
        "replay_health_state": health,
        "replay_transition_warning": warning,
        "explainability_payload": {
            "replay_rationale": ["Deterministic replay compares earliest vs latest structural metrics with bounded normalization."],
            "historical_peak_explanations": [f"Peaks reflect max fragility={peaks['historical_fragility_peak']:.3f}, overheating={peaks['historical_overheating_peak']:.3f}, contagion={peaks['historical_contagion_peak']:.3f}."],
            "trend_explanations": [f"Trend deltas: fragility={ft:.3f}, overheating={ot:.3f}, contagion={ct:.3f}, stability={st:.3f}, fragmentation={fragmt:.3f}."],
            "transition_explanations": [f"Transitions regime={regime_transition_count}, drift_reversals={drift_reversal_count}, contagion_changes={contagion_state_change_count}."],
            "persistence_explanations": [f"Persistent fragile={persistent_fragility_count}, overheated={persistent_overheating_count}, contagious={persistent_contagion_count}."],
            "recovery_explanations": [f"Recovery transitions counted={recovery_count}."],
            "latest_vs_earliest_comparison": {"earliest": earliest, "latest": latest},
            "warnings": ["Replay transition warning active."] if warning else [],
            "dominant_historical_drivers": sorted(drivers),
        },
        "status": "success",
    }


def _sample_history() -> List[Dict[str, Any]]:
    return [
        {"run_date_sgt": "2026-05-14", "regime_state": "stable", "drift_direction": "stable", "contagion_risk_state": "contained", "structural_fragility_score": 0.22, "overheating_score": 0.20, "contagion_pressure_score": 0.19, "fragmentation_score": 0.25, "structural_stability_score": 0.77},
        {"run_date_sgt": "2026-05-15", "regime_state": "transitioning", "drift_direction": "deteriorating", "contagion_risk_state": "spreading", "structural_fragility_score": 0.54, "overheating_score": 0.48, "contagion_pressure_score": 0.55, "fragmentation_score": 0.47, "structural_stability_score": 0.44},
        {"run_date_sgt": "2026-05-16", "regime_state": "fragile", "drift_direction": "deteriorating", "contagion_risk_state": "fragile", "structural_fragility_score": 0.68, "overheating_score": 0.61, "contagion_pressure_score": 0.70, "fragmentation_score": 0.61, "structural_stability_score": 0.31},
    ]


def main() -> None:
    records = _sample_history()
    summary = build_historical_structural_replay(records)
    out_path = Path("logs/tier3i_historical_replay_summary.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(
        f"[tier3i] replay_health_state={summary['replay_health_state']} "
        f"replay_score={summary['structural_replay_score']:.6f} "
        f"transitions={summary['regime_transition_count']} "
        f"window={summary['replay_window_size']} status=success"
    )


if __name__ == "__main__":
    main()
