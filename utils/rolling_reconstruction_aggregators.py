#!/usr/bin/env python3
"""
utils/rolling_reconstruction_aggregators.py

PASS 3 — Rolling Aggregation Infrastructure
===========================================

Reusable rolling analytics infrastructure for structural transmission
historical reconstruction.

Purpose:
- Extract rolling calculations out of reconstruction engine orchestration.
- Make momentum, acceleration, persistence, regime duration, evidence intensity,
  and pathway stability reusable across future themes.
- Keep implementation Python-only, deterministic, additive, and GitHub Actions safe.

This module is intentionally pure-Python and has no Supabase dependency.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================
# BASIC NUMERIC HELPERS
# ============================================================

def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return x
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def mean(values: Iterable[float]) -> float:
    clean = [safe_float(v) for v in values if v is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def stddev(values: Iterable[float]) -> float:
    clean = [safe_float(v) for v in values if v is not None]
    if len(clean) < 2:
        return 0.0
    m = mean(clean)
    return math.sqrt(sum((x - m) ** 2 for x in clean) / (len(clean) - 1))


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, safe_float(value)))


# ============================================================
# REGIME HELPERS
# ============================================================

def regime_from_score(score: float) -> str:
    score = safe_float(score)

    if score >= 75:
        return "expansion"
    if score >= 55:
        return "constructive"
    if score >= 40:
        return "neutral"
    if score >= 25:
        return "weakening"
    return "contraction"


def transition_type(previous: Optional[str], current: str) -> str:
    if previous is None:
        return "initial_state"
    if previous == current:
        return "no_change"

    rank = {
        "contraction": 1,
        "weakening": 2,
        "neutral": 3,
        "constructive": 4,
        "expansion": 5,
    }

    prev_rank = rank.get(previous, 3)
    curr_rank = rank.get(current, 3)

    if curr_rank > prev_rank:
        return "improvement"
    if curr_rank < prev_rank:
        return "deterioration"
    return "state_change"


def evidence_regime_from_score(score: float) -> str:
    score = safe_float(score)

    if score >= 75:
        return "high_evidence_intensity"
    if score >= 50:
        return "moderate_evidence_intensity"
    if score >= 25:
        return "low_evidence_intensity"
    return "minimal_evidence_intensity"


def momentum_regime_from_score(score: float) -> str:
    score = safe_float(score)

    if score >= 70:
        return "positive_momentum"
    if score >= 55:
        return "constructive_momentum"
    if score >= 45:
        return "neutral_momentum"
    if score >= 30:
        return "weakening_momentum"
    return "negative_momentum"


# ============================================================
# DATA CONTRACTS
# ============================================================

@dataclass(frozen=True)
class RollingMomentumMetrics:
    current_score: float
    previous_score: float
    momentum_7d: float
    momentum_30d: float
    acceleration_7d: float
    acceleration_30d: float
    persistence_days: int
    structural_momentum_score: float
    momentum_regime: str


@dataclass(frozen=True)
class RollingRegimeMetrics:
    previous_regime: Optional[str]
    current_regime: str
    regime_changed: bool
    regime_duration_days: int
    transition_type: str


@dataclass(frozen=True)
class RollingEvidenceMetrics:
    evidence_count: int
    high_confidence_evidence_count: int
    avg_evidence_strength: float
    rolling_evidence_7d: float
    rolling_evidence_30d: float
    evidence_spike_score: float
    evidence_regime: str


@dataclass(frozen=True)
class RollingPathwayMetrics:
    propagation_score: float
    previous_score: float
    score_change: float
    momentum_7d: float
    momentum_30d: float
    acceleration_7d: float
    acceleration_30d: float
    evidence_intensity: float
    attribution_strength: float
    pathway_stability_score: float
    regime: str


# ============================================================
# ROLLING SERIES ENGINE
# ============================================================

class RollingSeries:
    """
    A date-indexed numeric series with safe lag/window access.

    Missing lag values fall back to the current index score. This mirrors the
    legacy reconstruction behavior and avoids early-window NaN explosions.
    """

    def __init__(self, dates: Sequence[date], values: Sequence[float]) -> None:
        if len(dates) != len(values):
            raise ValueError("dates and values must have the same length")

        paired = sorted(zip(dates, values), key=lambda x: x[0])
        self.dates: List[date] = [x[0] for x in paired]
        self.values: List[float] = [safe_float(x[1]) for x in paired]

    def __len__(self) -> int:
        return len(self.values)

    def value_at(self, idx: int) -> float:
        if not self.values:
            return 0.0

        idx = max(0, min(idx, len(self.values) - 1))
        return self.values[idx]

    def lag(self, idx: int, periods: int) -> float:
        return self.value_at(idx - periods)

    def window_values(self, idx: int, window: int) -> List[float]:
        if not self.values:
            return []

        start = max(0, idx - window + 1)
        end = min(idx + 1, len(self.values))
        return self.values[start:end]

    def rolling_mean(self, idx: int, window: int) -> float:
        return mean(self.window_values(idx, window))

    def rolling_stddev(self, idx: int, window: int) -> float:
        return stddev(self.window_values(idx, window))


class RollingMomentumAggregator:
    def compute(self, series: RollingSeries, idx: int) -> RollingMomentumMetrics:
        current_score = series.value_at(idx)

        previous_score = series.lag(idx, 1)
        score_7d_ago = series.lag(idx, 7)
        score_8d_ago = series.lag(idx, 8)
        score_30d_ago = series.lag(idx, 30)
        score_31d_ago = series.lag(idx, 31)

        momentum_7d = current_score - score_7d_ago
        momentum_30d = current_score - score_30d_ago

        previous_momentum_7d = previous_score - score_8d_ago
        previous_momentum_30d = previous_score - score_31d_ago

        acceleration_7d = momentum_7d - previous_momentum_7d
        acceleration_30d = momentum_30d - previous_momentum_30d

        persistence_days = 0
        for j in range(idx, 0, -1):
            today_score = series.value_at(j)
            yesterday_score = series.value_at(j - 1)

            if today_score >= yesterday_score:
                persistence_days += 1
            else:
                break

        structural_momentum_score = clamp(
            50
            + momentum_7d * 3
            + momentum_30d * 1.5
            + acceleration_7d * 2
            + min(persistence_days, 30)
        )

        return RollingMomentumMetrics(
            current_score=round(current_score, 4),
            previous_score=round(previous_score, 4),
            momentum_7d=round(momentum_7d, 4),
            momentum_30d=round(momentum_30d, 4),
            acceleration_7d=round(acceleration_7d, 4),
            acceleration_30d=round(acceleration_30d, 4),
            persistence_days=int(persistence_days),
            structural_momentum_score=round(structural_momentum_score, 4),
            momentum_regime=momentum_regime_from_score(structural_momentum_score),
        )


class RollingRegimeAggregator:
    def compute_series(self, scores: Sequence[float]) -> List[RollingRegimeMetrics]:
        rows: List[RollingRegimeMetrics] = []
        previous_regime: Optional[str] = None
        current_duration = 0

        for score in scores:
            current_regime = regime_from_score(score)
            changed = bool(previous_regime is not None and previous_regime != current_regime)

            if previous_regime is None or changed:
                current_duration = 1
            else:
                current_duration += 1

            rows.append(
                RollingRegimeMetrics(
                    previous_regime=previous_regime,
                    current_regime=current_regime,
                    regime_changed=changed,
                    regime_duration_days=int(current_duration),
                    transition_type=transition_type(previous_regime, current_regime),
                )
            )

            previous_regime = current_regime

        return rows


class RollingEvidenceAggregator:
    def compute(
        self,
        *,
        current_strengths: Sequence[float],
        current_counts: Sequence[int],
        current_scores: Sequence[float],
        historical_strength_series: Sequence[float],
    ) -> RollingEvidenceMetrics:
        evidence_count = sum(safe_int(x) for x in current_counts)
        avg_strength = mean(current_strengths)

        rolling_7 = mean(list(historical_strength_series)[-7:])
        rolling_30 = mean(list(historical_strength_series)[-30:])

        spike_score = 0.0
        hist = list(historical_strength_series)

        if len(hist) >= 3:
            baseline_values = hist[:-1]
            baseline = mean(baseline_values)
            baseline_std = stddev(baseline_values)

            if baseline_std > 0:
                spike_score = clamp(50 + ((avg_strength - baseline) / baseline_std) * 10)
            else:
                spike_score = clamp(50 + avg_strength - baseline)

        high_conf_count = sum(
            1 for strength, score in zip(current_strengths, current_scores)
            if safe_float(strength) >= 70 or safe_float(score) >= 70
        )

        return RollingEvidenceMetrics(
            evidence_count=int(evidence_count),
            high_confidence_evidence_count=int(high_conf_count),
            avg_evidence_strength=round(avg_strength, 4),
            rolling_evidence_7d=round(rolling_7, 4),
            rolling_evidence_30d=round(rolling_30, 4),
            evidence_spike_score=round(spike_score, 4),
            evidence_regime=evidence_regime_from_score(avg_strength),
        )


class RollingPathwayAggregator:
    def compute(
        self,
        *,
        pathway_series: RollingSeries,
        idx: int,
        current_scores: Sequence[float],
        current_evidence_strengths: Sequence[float],
        current_attribution_strengths: Sequence[float],
        stability_window: int,
    ) -> RollingPathwayMetrics:
        current_score = mean(current_scores)
        previous_score = pathway_series.lag(idx, 1)

        score_7d_ago = pathway_series.lag(idx, 7)
        score_8d_ago = pathway_series.lag(idx, 8)
        score_30d_ago = pathway_series.lag(idx, 30)
        score_31d_ago = pathway_series.lag(idx, 31)

        momentum_7d = current_score - score_7d_ago
        momentum_30d = current_score - score_30d_ago

        prev_momentum_7d = previous_score - score_8d_ago
        prev_momentum_30d = previous_score - score_31d_ago

        acceleration_7d = momentum_7d - prev_momentum_7d
        acceleration_30d = momentum_30d - prev_momentum_30d

        pathway_stability_score = clamp(100 - pathway_series.rolling_stddev(idx, stability_window))

        return RollingPathwayMetrics(
            propagation_score=round(current_score, 4),
            previous_score=round(previous_score, 4),
            score_change=round(current_score - previous_score, 4),
            momentum_7d=round(momentum_7d, 4),
            momentum_30d=round(momentum_30d, 4),
            acceleration_7d=round(acceleration_7d, 4),
            acceleration_30d=round(acceleration_30d, 4),
            evidence_intensity=round(mean(current_evidence_strengths), 4),
            attribution_strength=round(mean(current_attribution_strengths), 4),
            pathway_stability_score=round(pathway_stability_score, 4),
            regime=regime_from_score(current_score),
        )


# ============================================================
# GROUPED OBSERVATION HELPERS
# ============================================================

def score_by_date(grouped: Dict[date, Sequence[Any]]) -> Tuple[List[date], List[float]]:
    """
    Convert grouped observations into date series of mean scores.

    Observation objects only need a `.score` attribute.
    """
    dates = sorted(grouped.keys())
    scores: List[float] = []

    for d in dates:
        observations = grouped[d]
        scores.append(mean([safe_float(getattr(x, "score", 0.0)) for x in observations]))

    return dates, scores


def pathway_keys_for_date(observations: Sequence[Any]) -> List[Tuple[str, str, str]]:
    keys = []

    for obs in observations:
        source_entity = "theme"
        target_entity = getattr(obs, "entity", None) or "theme"
        pathway_name = getattr(obs, "pathway_name", None) or "theme_pathway"
        keys.append((source_entity, target_entity, pathway_name))

    return sorted(set(keys))


def filter_pathway_observations(
    observations: Sequence[Any],
    *,
    target_entity: str,
    pathway_name: str,
) -> List[Any]:
    return [
        obs for obs in observations
        if (getattr(obs, "entity", None) or "theme") == target_entity
        and (getattr(obs, "pathway_name", None) or "theme_pathway") == pathway_name
    ]


def build_pathway_series(
    grouped: Dict[date, Sequence[Any]],
    *,
    target_entity: str,
    pathway_name: str,
) -> RollingSeries:
    dates = sorted(grouped.keys())
    values: List[float] = []

    for d in dates:
        obs_list = filter_pathway_observations(
            grouped[d],
            target_entity=target_entity,
            pathway_name=pathway_name,
        )
        values.append(mean([safe_float(getattr(x, "score", 0.0)) for x in obs_list]) if obs_list else 0.0)

    return RollingSeries(dates, values)


def historical_evidence_strength_series(
    grouped: Dict[date, Sequence[Any]],
    dates: Sequence[date],
    *,
    idx: int,
    entity: str,
    pathway_name: str,
) -> List[float]:
    values: List[float] = []

    for j in range(0, idx + 1):
        d = dates[j]
        obs_list = filter_pathway_observations(
            grouped[d],
            target_entity=entity,
            pathway_name=pathway_name,
        )
        if obs_list:
            values.append(mean([safe_float(getattr(x, "evidence_strength", 0.0)) for x in obs_list]))

    return values


# ============================================================
# ONE-STOP FACADE
# ============================================================

class RollingReconstructionAggregators:
    """
    Facade used by reconstruction engines.

    Keeps the engine simple and makes rolling logic reusable by other future
    transmission themes.
    """

    def __init__(self, *, stability_window: int = 30) -> None:
        self.stability_window = stability_window
        self.momentum = RollingMomentumAggregator()
        self.regime = RollingRegimeAggregator()
        self.evidence = RollingEvidenceAggregator()
        self.pathway = RollingPathwayAggregator()

    def theme_series(self, grouped: Dict[date, Sequence[Any]]) -> Tuple[List[date], RollingSeries]:
        dates, scores = score_by_date(grouped)
        return dates, RollingSeries(dates, scores)

    def theme_momentum_metrics(self, grouped: Dict[date, Sequence[Any]]) -> List[Tuple[date, RollingMomentumMetrics]]:
        dates, series = self.theme_series(grouped)
        return [(d, self.momentum.compute(series, idx)) for idx, d in enumerate(dates)]

    def theme_regime_metrics(self, grouped: Dict[date, Sequence[Any]]) -> List[Tuple[date, RollingRegimeMetrics]]:
        dates, scores = score_by_date(grouped)
        regimes = self.regime.compute_series(scores)
        return list(zip(dates, regimes))

    def pathway_metrics(
        self,
        grouped: Dict[date, Sequence[Any]],
        *,
        run_date: date,
        idx: int,
        target_entity: str,
        pathway_name: str,
        obs_list: Sequence[Any],
    ) -> RollingPathwayMetrics:
        series = build_pathway_series(
            grouped,
            target_entity=target_entity,
            pathway_name=pathway_name,
        )

        return self.pathway.compute(
            pathway_series=series,
            idx=idx,
            current_scores=[safe_float(getattr(x, "score", 0.0)) for x in obs_list],
            current_evidence_strengths=[
                safe_float(getattr(x, "evidence_strength", 0.0)) for x in obs_list
            ],
            current_attribution_strengths=[
                safe_float(getattr(x, "attribution_strength", 0.0)) for x in obs_list
            ],
            stability_window=self.stability_window,
        )

    def evidence_metrics(
        self,
        grouped: Dict[date, Sequence[Any]],
        *,
        dates: Sequence[date],
        idx: int,
        entity: str,
        pathway_name: str,
        obs_list: Sequence[Any],
    ) -> RollingEvidenceMetrics:
        hist_strengths = historical_evidence_strength_series(
            grouped,
            dates,
            idx=idx,
            entity=entity,
            pathway_name=pathway_name,
        )

        return self.evidence.compute(
            current_strengths=[
                safe_float(getattr(x, "evidence_strength", 0.0)) for x in obs_list
            ],
            current_counts=[
                safe_int(getattr(x, "evidence_count", 0)) for x in obs_list
            ],
            current_scores=[
                safe_float(getattr(x, "score", 0.0)) for x in obs_list
            ],
            historical_strength_series=hist_strengths,
        )
