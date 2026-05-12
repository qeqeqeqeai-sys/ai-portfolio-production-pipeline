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

Design:
- Additive-only
- Deterministic
- Restart-safe when used by checkpointed reconstruction engines
- Compatible with GitHub Actions
- Compatible with observations from utils/streaming_observation_loader.py

Primary facade:
    RollingReconstructionAggregators
"""

from __future__ import annotations

import math
import os
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


# ============================================================
# ENV / CONFIG HELPERS
# ============================================================

def env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default

    try:
        return int(float(raw))
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default

    try:
        return float(raw)
    except Exception:
        return default


def env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or str(raw).strip() == "":
        return default

    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass(frozen=True)
class RollingAggregationConfig:
    """
    Centralized tuning for rolling reconstruction analytics.

    These defaults preserve the existing Phase 2D.2 behavior while making the
    logic reusable across future themes.
    """

    stability_window: int = env_int("ROLLING_AGGREGATION_STABILITY_WINDOW", 30)

    momentum_short_lag: int = env_int("ROLLING_AGGREGATION_MOMENTUM_SHORT_LAG", 7)
    momentum_long_lag: int = env_int("ROLLING_AGGREGATION_MOMENTUM_LONG_LAG", 30)

    evidence_short_window: int = env_int("ROLLING_AGGREGATION_EVIDENCE_SHORT_WINDOW", 7)
    evidence_long_window: int = env_int("ROLLING_AGGREGATION_EVIDENCE_LONG_WINDOW", 30)

    momentum_base_score: float = env_float("ROLLING_AGGREGATION_MOMENTUM_BASE_SCORE", 50.0)
    momentum_short_weight: float = env_float("ROLLING_AGGREGATION_MOMENTUM_SHORT_WEIGHT", 3.0)
    momentum_long_weight: float = env_float("ROLLING_AGGREGATION_MOMENTUM_LONG_WEIGHT", 1.5)
    acceleration_short_weight: float = env_float("ROLLING_AGGREGATION_ACCELERATION_SHORT_WEIGHT", 2.0)
    max_persistence_bonus: int = env_int("ROLLING_AGGREGATION_MAX_PERSISTENCE_BONUS", 30)

    enable_telemetry: bool = env_bool("ROLLING_AGGREGATION_ENABLE_TELEMETRY", True)


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


def rounded(value: Any, digits: int = 4) -> float:
    return round(safe_float(value), digits)


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


@dataclass
class RollingAggregationTelemetry:
    """
    Lightweight telemetry object for optional engine-level logging.
    """

    theme_dates_processed: int = 0
    momentum_rows_generated: int = 0
    regime_rows_generated: int = 0
    pathway_rows_generated: int = 0
    evidence_rows_generated: int = 0
    max_stability_window: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "theme_dates_processed": self.theme_dates_processed,
            "momentum_rows_generated": self.momentum_rows_generated,
            "regime_rows_generated": self.regime_rows_generated,
            "pathway_rows_generated": self.pathway_rows_generated,
            "evidence_rows_generated": self.evidence_rows_generated,
            "max_stability_window": self.max_stability_window,
        }


# ============================================================
# ROLLING SERIES ENGINE
# ============================================================

class RollingSeries:
    """
    A date-indexed numeric series with safe lag/window access.

    Missing lag values fall back to the current index score. This preserves the
    existing reconstruction behavior and avoids early-window NaN explosions.
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

        window = max(1, int(window))
        start = max(0, idx - window + 1)
        end = min(idx + 1, len(self.values))

        return self.values[start:end]

    def rolling_mean(self, idx: int, window: int) -> float:
        return mean(self.window_values(idx, window))

    def rolling_stddev(self, idx: int, window: int) -> float:
        return stddev(self.window_values(idx, window))

    def to_pairs(self) -> List[Tuple[date, float]]:
        return list(zip(self.dates, self.values))


# ============================================================
# AGGREGATORS
# ============================================================

class RollingMomentumAggregator:
    def __init__(self, config: Optional[RollingAggregationConfig] = None) -> None:
        self.config = config or RollingAggregationConfig()

    def compute(self, series: RollingSeries, idx: int) -> RollingMomentumMetrics:
        cfg = self.config

        short_lag = max(1, int(cfg.momentum_short_lag))
        long_lag = max(short_lag + 1, int(cfg.momentum_long_lag))

        current_score = series.value_at(idx)

        previous_score = series.lag(idx, 1)
        score_short_ago = series.lag(idx, short_lag)
        score_short_plus_ago = series.lag(idx, short_lag + 1)
        score_long_ago = series.lag(idx, long_lag)
        score_long_plus_ago = series.lag(idx, long_lag + 1)

        momentum_short = current_score - score_short_ago
        momentum_long = current_score - score_long_ago

        previous_momentum_short = previous_score - score_short_plus_ago
        previous_momentum_long = previous_score - score_long_plus_ago

        acceleration_short = momentum_short - previous_momentum_short
        acceleration_long = momentum_long - previous_momentum_long

        persistence_days = self.compute_persistence_days(series, idx)

        structural_momentum_score = clamp(
            cfg.momentum_base_score
            + momentum_short * cfg.momentum_short_weight
            + momentum_long * cfg.momentum_long_weight
            + acceleration_short * cfg.acceleration_short_weight
            + min(persistence_days, cfg.max_persistence_bonus)
        )

        return RollingMomentumMetrics(
            current_score=rounded(current_score),
            previous_score=rounded(previous_score),
            momentum_7d=rounded(momentum_short),
            momentum_30d=rounded(momentum_long),
            acceleration_7d=rounded(acceleration_short),
            acceleration_30d=rounded(acceleration_long),
            persistence_days=int(persistence_days),
            structural_momentum_score=rounded(structural_momentum_score),
            momentum_regime=momentum_regime_from_score(structural_momentum_score),
        )

    @staticmethod
    def compute_persistence_days(series: RollingSeries, idx: int) -> int:
        persistence_days = 0

        for j in range(idx, 0, -1):
            today_score = series.value_at(j)
            yesterday_score = series.value_at(j - 1)

            if today_score >= yesterday_score:
                persistence_days += 1
            else:
                break

        return int(persistence_days)


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
    def __init__(self, config: Optional[RollingAggregationConfig] = None) -> None:
        self.config = config or RollingAggregationConfig()

    def compute(
        self,
        *,
        current_strengths: Sequence[float],
        current_counts: Sequence[int],
        current_scores: Sequence[float],
        historical_strength_series: Sequence[float],
    ) -> RollingEvidenceMetrics:
        cfg = self.config

        evidence_count = sum(safe_int(x) for x in current_counts)
        avg_strength = mean(current_strengths)

        hist = [safe_float(x) for x in historical_strength_series]

        rolling_short = mean(hist[-max(1, cfg.evidence_short_window):])
        rolling_long = mean(hist[-max(1, cfg.evidence_long_window):])

        spike_score = self.compute_spike_score(avg_strength, hist)

        high_conf_count = sum(
            1
            for strength, score in zip(current_strengths, current_scores)
            if safe_float(strength) >= 70 or safe_float(score) >= 70
        )

        return RollingEvidenceMetrics(
            evidence_count=int(evidence_count),
            high_confidence_evidence_count=int(high_conf_count),
            avg_evidence_strength=rounded(avg_strength),
            rolling_evidence_7d=rounded(rolling_short),
            rolling_evidence_30d=rounded(rolling_long),
            evidence_spike_score=rounded(spike_score),
            evidence_regime=evidence_regime_from_score(avg_strength),
        )

    @staticmethod
    def compute_spike_score(current_strength: float, historical_strengths: Sequence[float]) -> float:
        hist = [safe_float(x) for x in historical_strengths]

        if len(hist) < 3:
            return 0.0

        baseline_values = hist[:-1]
        baseline = mean(baseline_values)
        baseline_std = stddev(baseline_values)

        if baseline_std > 0:
            return clamp(50 + ((safe_float(current_strength) - baseline) / baseline_std) * 10)

        return clamp(50 + safe_float(current_strength) - baseline)


class RollingPathwayAggregator:
    def __init__(self, config: Optional[RollingAggregationConfig] = None) -> None:
        self.config = config or RollingAggregationConfig()

    def compute(
        self,
        *,
        pathway_series: RollingSeries,
        idx: int,
        current_scores: Sequence[float],
        current_evidence_strengths: Sequence[float],
        current_attribution_strengths: Sequence[float],
        stability_window: Optional[int] = None,
    ) -> RollingPathwayMetrics:
        cfg = self.config

        short_lag = max(1, int(cfg.momentum_short_lag))
        long_lag = max(short_lag + 1, int(cfg.momentum_long_lag))
        effective_stability_window = int(stability_window or cfg.stability_window)

        current_score = mean(current_scores)
        previous_score = pathway_series.lag(idx, 1)

        score_short_ago = pathway_series.lag(idx, short_lag)
        score_short_plus_ago = pathway_series.lag(idx, short_lag + 1)
        score_long_ago = pathway_series.lag(idx, long_lag)
        score_long_plus_ago = pathway_series.lag(idx, long_lag + 1)

        momentum_short = current_score - score_short_ago
        momentum_long = current_score - score_long_ago

        prev_momentum_short = previous_score - score_short_plus_ago
        prev_momentum_long = previous_score - score_long_plus_ago

        acceleration_short = momentum_short - prev_momentum_short
        acceleration_long = momentum_long - prev_momentum_long

        pathway_stability_score = clamp(
            100 - pathway_series.rolling_stddev(idx, effective_stability_window)
        )

        return RollingPathwayMetrics(
            propagation_score=rounded(current_score),
            previous_score=rounded(previous_score),
            score_change=rounded(current_score - previous_score),
            momentum_7d=rounded(momentum_short),
            momentum_30d=rounded(momentum_long),
            acceleration_7d=rounded(acceleration_short),
            acceleration_30d=rounded(acceleration_long),
            evidence_intensity=rounded(mean(current_evidence_strengths)),
            attribution_strength=rounded(mean(current_attribution_strengths)),
            pathway_stability_score=rounded(pathway_stability_score),
            regime=regime_from_score(current_score),
        )


# ============================================================
# GROUPED OBSERVATION HELPERS
# ============================================================

def score_by_date(grouped: Dict[date, Sequence[Any]]) -> Tuple[List[date], List[float]]:
    """
    Convert grouped observations into a date series of mean scores.

    Observation objects only need a `.score` attribute.
    """

    dates = sorted(grouped.keys())
    scores: List[float] = []

    for d in dates:
        observations = grouped[d]
        scores.append(mean([safe_float(getattr(x, "score", 0.0)) for x in observations]))

    return dates, scores


def pathway_keys_for_date(observations: Sequence[Any]) -> List[Tuple[str, str, str]]:
    keys: List[Tuple[str, str, str]] = []

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
        obs
        for obs in observations
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

        if obs_list:
            values.append(mean([safe_float(getattr(x, "score", 0.0)) for x in obs_list]))
        else:
            values.append(0.0)

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
            values.append(
                mean([safe_float(getattr(x, "evidence_strength", 0.0)) for x in obs_list])
            )

    return values


def pathway_group_map(observations: Sequence[Any]) -> Dict[Tuple[str, str, str], List[Any]]:
    """
    Build the pathway grouping used by reconstruction propagation outputs.
    """

    groups: Dict[Tuple[str, str, str], List[Any]] = {}

    for obs in observations:
        source_entity = "theme"
        target_entity = getattr(obs, "entity", None) or "theme"
        pathway_name = getattr(obs, "pathway_name", None) or "theme_pathway"

        key = (source_entity, target_entity, pathway_name)
        groups.setdefault(key, []).append(obs)

    return groups


def evidence_group_map(observations: Sequence[Any]) -> Dict[Tuple[str, str], List[Any]]:
    """
    Build the evidence grouping used by reconstruction evidence outputs.
    """

    groups: Dict[Tuple[str, str], List[Any]] = {}

    for obs in observations:
        entity = getattr(obs, "entity", None) or "theme"
        pathway_name = getattr(obs, "pathway_name", None) or "theme_pathway"

        groups.setdefault((entity, pathway_name), []).append(obs)

    return groups


# ============================================================
# ONE-STOP FACADE
# ============================================================

class RollingReconstructionAggregators:
    """
    Facade used by reconstruction engines.

    Keeps the engine simple and makes rolling logic reusable by other future
    transmission themes.
    """

    def __init__(
        self,
        *,
        stability_window: Optional[int] = None,
        config: Optional[RollingAggregationConfig] = None,
    ) -> None:
        self.config = config or RollingAggregationConfig()

        if stability_window is not None:
            self.config = RollingAggregationConfig(
                stability_window=int(stability_window),
                momentum_short_lag=self.config.momentum_short_lag,
                momentum_long_lag=self.config.momentum_long_lag,
                evidence_short_window=self.config.evidence_short_window,
                evidence_long_window=self.config.evidence_long_window,
                momentum_base_score=self.config.momentum_base_score,
                momentum_short_weight=self.config.momentum_short_weight,
                momentum_long_weight=self.config.momentum_long_weight,
                acceleration_short_weight=self.config.acceleration_short_weight,
                max_persistence_bonus=self.config.max_persistence_bonus,
                enable_telemetry=self.config.enable_telemetry,
            )

        self.momentum = RollingMomentumAggregator(self.config)
        self.regime = RollingRegimeAggregator()
        self.evidence = RollingEvidenceAggregator(self.config)
        self.pathway = RollingPathwayAggregator(self.config)
        self.telemetry = RollingAggregationTelemetry(
            max_stability_window=self.config.stability_window
        )

    @property
    def stability_window(self) -> int:
        return self.config.stability_window

    def theme_series(self, grouped: Dict[date, Sequence[Any]]) -> Tuple[List[date], RollingSeries]:
        dates, scores = score_by_date(grouped)
        return dates, RollingSeries(dates, scores)

    def theme_momentum_metrics(
        self,
        grouped: Dict[date, Sequence[Any]],
    ) -> List[Tuple[date, RollingMomentumMetrics]]:
        dates, series = self.theme_series(grouped)

        rows = [(d, self.momentum.compute(series, idx)) for idx, d in enumerate(dates)]

        self.telemetry.theme_dates_processed = max(
            self.telemetry.theme_dates_processed,
            len(dates),
        )
        self.telemetry.momentum_rows_generated += len(rows)

        return rows

    def theme_regime_metrics(
        self,
        grouped: Dict[date, Sequence[Any]],
    ) -> List[Tuple[date, RollingRegimeMetrics]]:
        dates, scores = score_by_date(grouped)
        regimes = self.regime.compute_series(scores)
        rows = list(zip(dates, regimes))

        self.telemetry.theme_dates_processed = max(
            self.telemetry.theme_dates_processed,
            len(dates),
        )
        self.telemetry.regime_rows_generated += len(rows)

        return rows

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

        metrics = self.pathway.compute(
            pathway_series=series,
            idx=idx,
            current_scores=[safe_float(getattr(x, "score", 0.0)) for x in obs_list],
            current_evidence_strengths=[
                safe_float(getattr(x, "evidence_strength", 0.0)) for x in obs_list
            ],
            current_attribution_strengths=[
                safe_float(getattr(x, "attribution_strength", 0.0)) for x in obs_list
            ],
            stability_window=self.config.stability_window,
        )

        self.telemetry.pathway_rows_generated += 1

        return metrics

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

        metrics = self.evidence.compute(
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

        self.telemetry.evidence_rows_generated += 1

        return metrics

    def pathway_groups_for_date(
        self,
        observations: Sequence[Any],
    ) -> Dict[Tuple[str, str, str], List[Any]]:
        return pathway_group_map(observations)

    def evidence_groups_for_date(
        self,
        observations: Sequence[Any],
    ) -> Dict[Tuple[str, str], List[Any]]:
        return evidence_group_map(observations)

    def telemetry_dict(self) -> Dict[str, Any]:
        return self.telemetry.to_dict()


# ============================================================
# LOCAL SMOKE TEST
# ============================================================

def _smoke_test() -> None:
    from dataclasses import dataclass
    from datetime import timedelta

    @dataclass
    class Obs:
        score: float
        entity: str = "AAPL"
        pathway_name: str = "ai_subsector"
        evidence_strength: float = 50.0
        evidence_count: int = 1
        attribution_strength: float = 25.0

    start = date(2026, 1, 1)
    grouped: Dict[date, List[Obs]] = {}

    for i in range(40):
        d = start + timedelta(days=i)
        grouped[d] = [
            Obs(
                score=50 + i * 0.5,
                evidence_strength=40 + i * 0.2,
                evidence_count=1,
                attribution_strength=25 + i * 0.1,
            )
        ]

    agg = RollingReconstructionAggregators(stability_window=30)

    momentum = agg.theme_momentum_metrics(grouped)
    regime = agg.theme_regime_metrics(grouped)

    assert len(momentum) == 40
    assert len(regime) == 40
    assert momentum[-1][1].momentum_7d > 0
    assert momentum[-1][1].structural_momentum_score > 50

    dates = sorted(grouped.keys())
    pathway_groups = agg.pathway_groups_for_date(grouped[dates[-1]])

    assert pathway_groups

    for (_, target_entity, pathway_name), obs_list in pathway_groups.items():
        pathway_metrics = agg.pathway_metrics(
            grouped,
            run_date=dates[-1],
            idx=len(dates) - 1,
            target_entity=target_entity,
            pathway_name=pathway_name,
            obs_list=obs_list,
        )
        assert pathway_metrics.propagation_score > 0

    evidence_groups = agg.evidence_groups_for_date(grouped[dates[-1]])

    assert evidence_groups

    for (entity, pathway_name), obs_list in evidence_groups.items():
        evidence_metrics = agg.evidence_metrics(
            grouped,
            dates=dates,
            idx=len(dates) - 1,
            entity=entity,
            pathway_name=pathway_name,
            obs_list=obs_list,
        )
        assert evidence_metrics.evidence_count > 0

    print("PASS 3 rolling aggregator smoke test passed.")
    print(
        {
            "latest_date": momentum[-1][0].isoformat(),
            "latest_momentum_7d": momentum[-1][1].momentum_7d,
            "latest_momentum_regime": momentum[-1][1].momentum_regime,
            "latest_current_regime": regime[-1][1].current_regime,
            "telemetry": agg.telemetry_dict(),
        }
    )


if __name__ == "__main__":
    _smoke_test()
