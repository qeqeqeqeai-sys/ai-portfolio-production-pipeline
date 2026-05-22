from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from math import sqrt
from statistics import median
from typing import Any, Dict, List, Mapping, Sequence, Tuple

ALPHA_CLASSIFICATIONS: Tuple[str, ...] = (
    "strong_positive_efficacy",
    "moderate_positive_efficacy",
    "weak_positive_efficacy",
    "neutral_efficacy",
    "weak_negative_efficacy",
    "moderate_negative_efficacy",
    "strong_negative_efficacy",
    "insufficient_data",
    "invalid_input",
)

FORWARD_WINDOWS: Tuple[str, ...] = ("5d", "20d", "60d")
MIN_SAMPLE_SIZE = 5
MIN_DECILE_SAMPLE_SIZE = 10


@dataclass(frozen=True)
class ForwardWindowPoint:
    timestamp: str
    asset_id: str
    signal_value: float
    forward_return: float


def _safe_sorted_records(records: Sequence[Mapping[str, Any]]) -> List[Mapping[str, Any]]:
    return sorted(records, key=lambda row: (str(row.get("timestamp", "")), str(row.get("asset_id", ""))))


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float:
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    varx = sum((x - mx) ** 2 for x in xs)
    vary = sum((y - my) ** 2 for y in ys)
    denom = sqrt(varx * vary)
    return 0.0 if denom == 0 else cov / denom


def _rank(values: Sequence[float]) -> List[float]:
    indexed = sorted(enumerate(values), key=lambda p: p[1])
    ranks: List[float] = [0.0] * len(values)
    i = 0
    while i < len(indexed):
        j = i
        while j + 1 < len(indexed) and indexed[j + 1][1] == indexed[i][1]:
            j += 1
        avg_rank = (i + j + 2) / 2.0
        for k in range(i, j + 1):
            ranks[indexed[k][0]] = avg_rank
        i = j + 1
    return ranks


def build_forward_return_windows(records: Sequence[Mapping[str, Any]], window: str) -> List[ForwardWindowPoint]:
    if window not in FORWARD_WINDOWS:
        return []
    points: List[ForwardWindowPoint] = []
    return_key = f"forward_return_{window}"
    for row in _safe_sorted_records(records):
        ts = row.get("timestamp")
        signal = row.get("signal")
        fr = row.get(return_key)
        if ts is None or not isinstance(signal, (int, float)) or not isinstance(fr, (int, float)):
            continue
        points.append(
            ForwardWindowPoint(
                timestamp=str(ts),
                asset_id=str(row.get("asset_id", "")),
                signal_value=float(signal),
                forward_return=float(fr),
            )
        )
    return points


def compute_information_coefficient(points: Sequence[ForwardWindowPoint]) -> float:
    return _pearson([p.signal_value for p in points], [p.forward_return for p in points])


def compute_rank_information_coefficient(points: Sequence[ForwardWindowPoint]) -> float:
    return _pearson(_rank([p.signal_value for p in points]), _rank([p.forward_return for p in points]))


def compute_forward_return_separation(points: Sequence[ForwardWindowPoint]) -> float:
    if len(points) < 2:
        return 0.0
    ordered = sorted(points, key=lambda p: (p.signal_value, p.asset_id, p.timestamp))
    half = len(ordered) // 2
    if half == 0:
        return 0.0
    top = ordered[-half:]
    bottom = ordered[:half]
    return (sum(p.forward_return for p in top) / len(top)) - (sum(p.forward_return for p in bottom) / len(bottom))


def compute_decile_spread(points: Sequence[ForwardWindowPoint]) -> float:
    if len(points) < MIN_DECILE_SAMPLE_SIZE:
        return 0.0
    ordered = sorted(points, key=lambda p: (p.signal_value, p.asset_id, p.timestamp))
    bucket = len(ordered) // 10
    top = ordered[-bucket:]
    bottom = ordered[:bucket]
    return (sum(p.forward_return for p in top) / len(top)) - (sum(p.forward_return for p in bottom) / len(bottom))


def compute_hit_rate(points: Sequence[ForwardWindowPoint]) -> float:
    if not points:
        return 0.0
    hits = sum(
        1
        for p in points
        if (p.signal_value > 0 and p.forward_return > 0)
        or (p.signal_value < 0 and p.forward_return < 0)
        or (p.signal_value == 0 and p.forward_return == 0)
    )
    return hits / len(points)


def compute_factor_stability(records: Sequence[Mapping[str, Any]]) -> float:
    by_ts: Dict[str, List[float]] = {}
    for row in records:
        signal = row.get("signal")
        ts = row.get("timestamp")
        if isinstance(signal, (int, float)) and ts is not None:
            by_ts.setdefault(str(ts), []).append(float(signal))
    if len(by_ts) < 2:
        return 0.0
    medians = [median(by_ts[k]) for k in sorted(by_ts)]
    avg_diff = sum(abs(medians[i] - medians[i - 1]) for i in range(1, len(medians))) / (len(medians) - 1)
    return 1.0 / (1.0 + avg_diff)


def compute_factor_decay(records: Sequence[Mapping[str, Any]]) -> float:
    return compute_information_coefficient(build_forward_return_windows(records, "5d")) - compute_information_coefficient(
        build_forward_return_windows(records, "60d")
    )


def _classify(ic: float, rank_ic: float, separation: float, decile_spread: float, hit_rate: float) -> str:
    efficacy_score = (0.35 * ic) + (0.35 * rank_ic) + (0.15 * separation) + (0.10 * decile_spread) + (0.05 * (hit_rate - 0.5))
    if efficacy_score >= 0.35:
        return "strong_positive_efficacy"
    if efficacy_score >= 0.20:
        return "moderate_positive_efficacy"
    if efficacy_score >= 0.05:
        return "weak_positive_efficacy"
    if efficacy_score > -0.05:
        return "neutral_efficacy"
    if efficacy_score > -0.20:
        return "weak_negative_efficacy"
    if efficacy_score > -0.35:
        return "moderate_negative_efficacy"
    return "strong_negative_efficacy"


def _invariants() -> Dict[str, bool]:
    return {
        "deterministic_output": True,
        "replay_compatible": True,
        "immutable_input_safe": True,
        "no_runtime_mutation": True,
        "no_adaptive_control": True,
        "no_black_box_ml": True,
        "no_trading_execution": True,
    }


def _fingerprint(payload: Mapping[str, Any]) -> str:
    return sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def run_alpha_layer_a_predictive_validation(*, signal_name: str, window: str, records: Sequence[Mapping[str, Any]], regime_tag: str = "all_regimes") -> Dict[str, Any]:
    base: Dict[str, Any] = {"signal_name": str(signal_name), "window": str(window), "regime_tag": str(regime_tag), "invariants": _invariants()}
    if not signal_name or window not in FORWARD_WINDOWS or not isinstance(records, Sequence):
        payload = {**base, "classification": "invalid_input", "explanation": "Predictive validation invalid_input: verify signal_name, window, and record schema.", "sample_count": 0, "metrics": {}}
        payload["replay_metadata"] = {"schema_version": "alpha_layer_a_v1", "fingerprint_sha256": _fingerprint(payload)}
        return payload

    points = build_forward_return_windows(records, window)
    if len(points) < MIN_SAMPLE_SIZE:
        payload = {**base, "classification": "insufficient_data", "explanation": "Predictive validation insufficient_data: minimum deterministic sample threshold not met.", "sample_count": len(points), "metrics": {}}
        payload["replay_metadata"] = {"schema_version": "alpha_layer_a_v1", "fingerprint_sha256": _fingerprint(payload)}
        return payload

    ic = compute_information_coefficient(points)
    rank_ic = compute_rank_information_coefficient(points)
    separation = compute_forward_return_separation(points)
    decile_spread = compute_decile_spread(points)
    hit_rate = compute_hit_rate(points)
    stability = compute_factor_stability(records)
    decay = compute_factor_decay(records)
    classification = _classify(ic, rank_ic, separation, decile_spread, hit_rate)

    metrics: Dict[str, float] = {
        "information_coefficient": round(ic, 8),
        "rank_information_coefficient": round(rank_ic, 8),
        "forward_return_separation": round(separation, 8),
        "decile_spread": round(decile_spread, 8),
        "hit_rate": round(hit_rate, 8),
        "factor_stability": round(stability, 8),
        "factor_decay": round(decay, 8),
    }
    payload: Dict[str, Any] = {
        **base,
        "sample_count": len(points),
        "classification": classification,
        "metrics": metrics,
        "window_points": [asdict(p) for p in points],
        "explanation": (
            "Predictive validation for signal={signal} window={window} samples={samples} IC={ic:.6f} "
            "RankIC={rank_ic:.6f} Separation={sep:.6f} DecileSpread={ds:.6f} HitRate={hr:.6f} "
            "Stability={stability:.6f} Decay={decay:.6f} classification={classification}."
        ).format(signal=signal_name, window=window, samples=len(points), ic=metrics["information_coefficient"], rank_ic=metrics["rank_information_coefficient"], sep=metrics["forward_return_separation"], ds=metrics["decile_spread"], hr=metrics["hit_rate"], stability=metrics["factor_stability"], decay=metrics["factor_decay"], classification=classification),
    }
    payload["replay_metadata"] = {"schema_version": "alpha_layer_a_v1", "fingerprint_sha256": _fingerprint(payload)}
    return payload
