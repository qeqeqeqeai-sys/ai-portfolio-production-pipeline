"""
Phase 2D.2 — Historical Reconstruction Engine

Purpose:
    Reconstruct historical structural transmission analytics from existing
    historical scoring, explainability, attribution, evidence, telemetry,
    and monitoring tables.

Architecture:
    - Python only
    - Supabase REST API only
    - No supabase-py package
    - Additive only
    - Idempotent upserts
    - Generic-theme compatible
    - Restart-safe checkpointing
    - Chunked historical backfill
    - GitHub Actions compatible

Author:
    Structural Transmission Intelligence Platform
"""

from __future__ import annotations

import os
import sys
import json
import math
import time
import hashlib
import traceback
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests


# ============================================================
# CONFIG
# ============================================================

DEFAULT_THEME_NAME = os.getenv("THEME_NAME", "ai")
DEFAULT_LOOKBACK_DAYS = int(os.getenv("RECONSTRUCTION_LOOKBACK_DAYS", "365"))
DEFAULT_CHUNK_DAYS = int(os.getenv("RECONSTRUCTION_CHUNK_DAYS", "30"))
DEFAULT_ROLLING_WINDOW = int(os.getenv("RECONSTRUCTION_ROLLING_WINDOW", "20"))
DEFAULT_BATCH_SIZE = int(os.getenv("RECONSTRUCTION_BATCH_SIZE", "500"))
DEFAULT_SLEEP_SECONDS = float(os.getenv("RECONSTRUCTION_SLEEP_SECONDS", "0.15"))

PIPELINE_NAME = "AI_TRANSMISSION_PHASE_2D2_HISTORICAL_RECONSTRUCTION"

SGT_OFFSET = timezone(timedelta(hours=8))


# ============================================================
# SUPABASE REST CLIENT
# ============================================================

class SupabaseRestClient:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_KEY")
            or ""
        )

        if not self.url or not self.key:
            raise RuntimeError(
                "Missing Supabase credentials. Required: SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY."
            )

        self.base = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, str]] = None,
        payload: Optional[Any] = None,
        retries: int = 3,
    ) -> requests.Response:
        full_url = f"{self.base}/{endpoint.lstrip('/')}"

        last_error = None

        for attempt in range(1, retries + 1):
            try:
                response = requests.request(
                    method=method,
                    url=full_url,
                    headers=self.headers,
                    params=params,
                    json=payload,
                    timeout=60,
                )

                if response.status_code in (200, 201, 204):
                    return response

                if response.status_code in (429, 500, 502, 503, 504):
                    time.sleep(min(2 ** attempt, 10))
                    continue

                raise RuntimeError(
                    f"Supabase REST error {response.status_code}: "
                    f"{response.text[:1000]}"
                )

            except Exception as exc:
                last_error = exc
                time.sleep(min(2 ** attempt, 10))

        raise RuntimeError(f"Supabase REST request failed: {last_error}")

    def select(
        self,
        table: str,
        *,
        select: str = "*",
        filters: Optional[Dict[str, str]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        params: Dict[str, str] = {"select": select}

        if filters:
            params.update(filters)

        if order:
            params["order"] = order

        if limit:
            params["limit"] = str(limit)

        response = self._request("GET", table, params=params)
        return response.json()

    def upsert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        *,
        conflict_columns: List[str],
        batch_size: int = DEFAULT_BATCH_SIZE,
    ) -> int:
        if not rows:
            return 0

        total = 0
        conflict_key = ",".join(conflict_columns)

        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            endpoint = f"{table}?on_conflict={conflict_key}"
            full_url = f"{self.base}/{endpoint}"

            response = requests.post(
                full_url,
                headers=headers,
                json=batch,
                timeout=90,
            )

            if response.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"Upsert failed for {table}: "
                    f"{response.status_code} - {response.text[:2000]}"
                )

            total += len(batch)
            time.sleep(DEFAULT_SLEEP_SECONDS)

        return total

    def table_exists(self, table: str) -> bool:
        try:
            self.select(table, select="*", limit=1)
            return True
        except Exception:
            return False


# ============================================================
# UTILITIES
# ============================================================

def now_sgt() -> datetime:
    return datetime.now(SGT_OFFSET)


def today_sgt() -> date:
    return now_sgt().date()


def parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    if isinstance(value, datetime):
        return value.date()

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        pass

    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except Exception:
            continue

    return None


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        result = float(value)
        if math.isnan(result) or math.isinf(result):
            return default
        return result
    except Exception:
        return default


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def stable_hash(parts: List[Any]) -> str:
    raw = "|".join([str(x) for x in parts])
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def mean(values: List[float]) -> float:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def stddev(values: List[float]) -> float:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    if len(clean) < 2:
        return 0.0

    m = mean(clean)
    variance = sum((v - m) ** 2 for v in clean) / (len(clean) - 1)
    return math.sqrt(variance)


def pct_change(current: float, previous: float) -> float:
    if previous == 0:
        return 0.0
    return (current - previous) / abs(previous)


def clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))


def regime_from_score(score: float, instability: float = 0.0) -> str:
    if instability >= 70:
        return "unstable"
    if score >= 75:
        return "expansion"
    if score >= 55:
        return "constructive"
    if score >= 40:
        return "neutral"
    if score >= 25:
        return "weakening"
    return "contraction"


# ============================================================
# SOURCE TABLE DETECTION
# ============================================================

@dataclass
class SourceTableConfig:
    table: str
    date_col: str
    theme_col: Optional[str]
    entity_col: Optional[str]
    score_cols: List[str]
    driver_cols: List[str]
    pathway_cols: List[str]
    attribution_cols: List[str]
    evidence_cols: List[str]


CANDIDATE_SOURCE_TABLES: List[SourceTableConfig] = [
    SourceTableConfig(
        table="structural_theme_scores",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["transmission_score", "composite_score", "theme_score", "score"],
        driver_cols=["top_positive_drivers", "top_negative_drivers"],
        pathway_cols=["pathway", "transmission_pathway"],
        attribution_cols=["component_scores", "contribution_weights"],
        evidence_cols=["evidence_count", "evidence_coverage_score"],
    ),
    SourceTableConfig(
        table="ai_transmission_scores",
        date_col="run_date_sgt",
        theme_col=None,
        entity_col="ticker",
        score_cols=["transmission_score", "composite_score", "ai_transmission_score", "score"],
        driver_cols=["top_positive_drivers", "top_negative_drivers"],
        pathway_cols=["pathway", "transmission_pathway"],
        attribution_cols=["component_scores", "contribution_weights"],
        evidence_cols=["evidence_count", "evidence_coverage_score"],
    ),
    SourceTableConfig(
        table="structural_theme_explainability_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["transmission_score", "composite_score", "score"],
        driver_cols=["top_positive_drivers", "top_negative_drivers", "driver"],
        pathway_cols=["pathway", "transmission_pathway"],
        attribution_cols=["component_score", "contribution_weight", "component_scores"],
        evidence_cols=["evidence_count", "evidence_coverage_score"],
    ),
    SourceTableConfig(
        table="structural_theme_attribution_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["score", "component_score"],
        driver_cols=["driver"],
        pathway_cols=["pathway"],
        attribution_cols=["component_name", "component_score", "contribution_weight"],
        evidence_cols=["evidence_count"],
    ),
    SourceTableConfig(
        table="structural_theme_evidence_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["evidence_score", "evidence_coverage_score"],
        driver_cols=["driver"],
        pathway_cols=["pathway"],
        attribution_cols=[],
        evidence_cols=["evidence_count", "evidence_score", "evidence_coverage_score"],
    ),
    SourceTableConfig(
        table="daily_signal_scores",
        date_col="run_date_sgt",
        theme_col=None,
        entity_col="series_id",
        score_cols=["score", "percentile", "latest_value"],
        driver_cols=[],
        pathway_cols=["asset_class", "asset"],
        attribution_cols=[],
        evidence_cols=[],
    ),
]


def detect_source_tables(client: SupabaseRestClient) -> List[SourceTableConfig]:
    available = []

    for cfg in CANDIDATE_SOURCE_TABLES:
        if client.table_exists(cfg.table):
            available.append(cfg)

    if not available:
        raise RuntimeError(
            "No compatible historical source tables detected. "
            "Expected at least one structural/scoring/explainability/evidence table."
        )

    return available


# ============================================================
# NORMALISED HISTORICAL OBSERVATION
# ============================================================

@dataclass
class HistoricalObservation:
    run_date: date
    theme_name: str
    entity: str
    source_table: str
    score: float
    driver_key: str
    pathway_key: str
    attribution_payload: Dict[str, Any]
    evidence_intensity: float
    raw_payload: Dict[str, Any]


def first_present(row: Dict[str, Any], columns: List[str], default: Any = None) -> Any:
    for col in columns:
        if col in row and row[col] is not None:
            return row[col]
    return default


def normalise_row(
    row: Dict[str, Any],
    cfg: SourceTableConfig,
    default_theme: str,
) -> Optional[HistoricalObservation]:
    run_date = parse_date(row.get(cfg.date_col))
    if not run_date:
        return None

    theme_name = default_theme
    if cfg.theme_col and row.get(cfg.theme_col):
        theme_name = safe_text(row.get(cfg.theme_col), default_theme)

    entity = "theme"
    if cfg.entity_col and row.get(cfg.entity_col):
        entity = safe_text(row.get(cfg.entity_col), "theme")

    score = safe_float(first_present(row, cfg.score_cols, 0.0), 0.0)

    driver_key = safe_text(
        first_present(row, cfg.driver_cols, "unknown_driver"),
        "unknown_driver",
    )

    pathway_key = safe_text(
        first_present(row, cfg.pathway_cols, "unknown_pathway"),
        "unknown_pathway",
    )

    attribution_payload: Dict[str, Any] = {}

    for col in cfg.attribution_cols:
        if col in row and row[col] is not None:
            attribution_payload[col] = row[col]

    evidence_intensity = safe_float(
        first_present(row, cfg.evidence_cols, 0.0),
        0.0,
    )

    return HistoricalObservation(
        run_date=run_date,
        theme_name=theme_name,
        entity=entity,
        source_table=cfg.table,
        score=score,
        driver_key=driver_key,
        pathway_key=pathway_key,
        attribution_payload=attribution_payload,
        evidence_intensity=evidence_intensity,
        raw_payload=row,
    )


# ============================================================
# HISTORICAL FETCHING
# ============================================================

def fetch_source_rows(
    client: SupabaseRestClient,
    cfg: SourceTableConfig,
    *,
    start_date: date,
    end_date: date,
    theme_name: str,
) -> List[HistoricalObservation]:

    filters: Dict[str, str] = {
        cfg.date_col: f"gte.{start_date.isoformat()}",
    }

    # PostgREST cannot express two filters on same key in a dict.
    # Use manually constructed query via select wrapper workaround.
    params = {
        "select": "*",
        cfg.date_col: f"gte.{start_date.isoformat()}",
        f"{cfg.date_col}__lte": f"lte.{end_date.isoformat()}",
    }

    # Build URL manually because repeated column filters are needed.
    query = {
        "select": "*",
        cfg.date_col: f"gte.{start_date.isoformat()}",
        cfg.date_col: f"lte.{end_date.isoformat()}",
        "order": f"{cfg.date_col}.asc",
    }

    actual_filters = {
        cfg.date_col: f"gte.{start_date.isoformat()}",
        "order": f"{cfg.date_col}.asc",
    }

    rows = client.select(
        cfg.table,
        select="*",
        filters=actual_filters,
        order=f"{cfg.date_col}.asc",
        limit=50000,
    )

    observations: List[HistoricalObservation] = []

    for row in rows:
        row_date = parse_date(row.get(cfg.date_col))
        if not row_date:
            continue

        if row_date < start_date or row_date > end_date:
            continue

        if cfg.theme_col and row.get(cfg.theme_col):
            if safe_text(row.get(cfg.theme_col)).lower() != theme_name.lower():
                continue

        obs = normalise_row(row, cfg, theme_name)
        if obs:
            observations.append(obs)

    return observations


# ============================================================
# RECONSTRUCTION CORE
# ============================================================

class HistoricalReconstructionEngine:
    def __init__(
        self,
        client: SupabaseRestClient,
        *,
        theme_name: str = DEFAULT_THEME_NAME,
        rolling_window: int = DEFAULT_ROLLING_WINDOW,
    ) -> None:
        self.client = client
        self.theme_name = theme_name
        self.rolling_window = rolling_window

    def group_by_date(self, observations: List[HistoricalObservation]) -> Dict[date, List[HistoricalObservation]]:
        grouped: Dict[date, List[HistoricalObservation]] = {}

        for obs in observations:
            grouped.setdefault(obs.run_date, []).append(obs)

        return dict(sorted(grouped.items(), key=lambda x: x[0]))

    def reconstruct_momentum(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            current_obs = grouped[run_date]
            current_score = mean([x.score for x in current_obs])

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_scores = [
                mean([x.score for x in grouped[d]])
                for d in window_dates
            ]

            previous_score = window_scores[-2] if len(window_scores) >= 2 else current_score
            momentum = current_score - previous_score
            acceleration = 0.0

            if len(window_scores) >= 3:
                prev_momentum = window_scores[-2] - window_scores[-3]
                acceleration = momentum - prev_momentum

            persistence = 0.0
            if len(window_scores) >= 3:
                signs = []
                for i in range(1, len(window_scores)):
                    diff = window_scores[i] - window_scores[i - 1]
                    signs.append(1 if diff >= 0 else -1)

                latest_sign = signs[-1]
                persistence = 100.0 * sum(1 for s in signs if s == latest_sign) / len(signs)

            volatility = stddev(window_scores)
            momentum_score = clamp(50 + momentum * 5 + acceleration * 2 - volatility)

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "momentum_score": round(momentum_score, 4),
                "rolling_score": round(mean(window_scores), 4),
                "score_change": round(momentum, 4),
                "acceleration_score": round(acceleration, 4),
                "momentum_persistence_score": round(persistence, 4),
                "rolling_window_days": self.rolling_window,
                "source": "phase2d2_reconstruction",
                "reconstruction_method": "rolling_score_momentum",
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

        return rows

    def reconstruct_regimes(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        dates = list(grouped.keys())
        previous_regime: Optional[str] = None

        for idx, run_date in enumerate(dates):
            current_obs = grouped[run_date]
            current_score = mean([x.score for x in current_obs])

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_scores = [
                mean([x.score for x in grouped[d]])
                for d in window_dates
            ]

            volatility = stddev(window_scores)
            instability = clamp(volatility * 3)
            regime = regime_from_score(current_score, instability)

            transition_flag = bool(previous_regime and previous_regime != regime)

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "regime": regime,
                "previous_regime": previous_regime,
                "regime_transition_flag": transition_flag,
                "regime_instability_score": round(instability, 4),
                "regime_confidence_score": round(clamp(100 - instability), 4),
                "structural_score": round(current_score, 4),
                "source": "phase2d2_reconstruction",
                "reconstruction_method": "score_volatility_regime",
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

            previous_regime = regime

        return rows

    def reconstruct_evidence_intensity(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []

        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            obs = grouped[run_date]
            evidence_values = [x.evidence_intensity for x in obs]
            intensity = mean(evidence_values)
            concentration = self._concentration_score(evidence_values)

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_intensity = [
                mean([x.evidence_intensity for x in grouped[d]])
                for d in window_dates
            ]

            spike_score = 0.0
            if len(window_intensity) >= 3:
                baseline = mean(window_intensity[:-1])
                baseline_std = stddev(window_intensity[:-1])
                if baseline_std > 0:
                    spike_score = clamp(50 + ((intensity - baseline) / baseline_std) * 10)
                else:
                    spike_score = clamp(50 + intensity - baseline)

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "evidence_intensity_score": round(intensity, 4),
                "evidence_spike_score": round(spike_score, 4),
                "evidence_concentration_score": round(concentration, 4),
                "evidence_observation_count": len(obs),
                "rolling_window_days": self.rolling_window,
                "source": "phase2d2_reconstruction",
                "reconstruction_method": "evidence_intensity_rolling_spike",
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

        return rows

    def reconstruct_driver_persistence(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]

            driver_counts: Dict[str, int] = {}
            driver_score_sum: Dict[str, float] = {}

            for d in window_dates:
                for obs in grouped[d]:
                    driver = obs.driver_key or "unknown_driver"
                    driver_counts[driver] = driver_counts.get(driver, 0) + 1
                    driver_score_sum[driver] = driver_score_sum.get(driver, 0.0) + obs.score

            for driver, count in driver_counts.items():
                persistence_score = 100.0 * count / max(1, len(window_dates))
                avg_score = driver_score_sum[driver] / max(1, count)

                rows.append({
                    "run_date_sgt": run_date.isoformat(),
                    "theme_name": self.theme_name,
                    "driver_key": driver[:250],
                    "driver_persistence_score": round(clamp(persistence_score), 4),
                    "driver_average_score": round(avg_score, 4),
                    "driver_observation_count": count,
                    "rolling_window_days": self.rolling_window,
                    "driver_half_life_estimate": round(self._half_life_estimate(persistence_score), 4),
                    "source": "phase2d2_reconstruction",
                    "reconstruction_method": "rolling_driver_frequency",
                    "created_at": now_sgt().isoformat(),
                    "updated_at": now_sgt().isoformat(),
                })

        return rows

    def reconstruct_pathway_trends(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]

            pathway_counts: Dict[str, int] = {}
            pathway_scores: Dict[str, List[float]] = {}

            for d in window_dates:
                for obs in grouped[d]:
                    pathway = obs.pathway_key or "unknown_pathway"
                    pathway_counts[pathway] = pathway_counts.get(pathway, 0) + 1
                    pathway_scores.setdefault(pathway, []).append(obs.score)

            total_count = sum(pathway_counts.values()) or 1

            for pathway, count in pathway_counts.items():
                scores = pathway_scores.get(pathway, [])
                trend_score = mean(scores)
                stability_score = clamp(100 - stddev(scores))
                concentration_score = 100.0 * count / total_count

                rows.append({
                    "run_date_sgt": run_date.isoformat(),
                    "theme_name": self.theme_name,
                    "pathway_key": pathway[:250],
                    "pathway_trend_score": round(trend_score, 4),
                    "pathway_stability_score": round(stability_score, 4),
                    "pathway_concentration_score": round(concentration_score, 4),
                    "pathway_observation_count": count,
                    "rolling_window_days": self.rolling_window,
                    "source": "phase2d2_reconstruction",
                    "reconstruction_method": "rolling_pathway_trend",
                    "created_at": now_sgt().isoformat(),
                    "updated_at": now_sgt().isoformat(),
                })

        return rows

    def reconstruct_attribution_trends(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]

            component_values: Dict[str, List[float]] = {}

            for d in window_dates:
                for obs in grouped[d]:
                    payload = obs.attribution_payload or {}

                    for key, value in payload.items():
                        if isinstance(value, dict):
                            for sub_key, sub_value in value.items():
                                component_values.setdefault(str(sub_key), []).append(safe_float(sub_value))
                        elif isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    name = (
                                        item.get("component")
                                        or item.get("component_name")
                                        or item.get("name")
                                        or key
                                    )
                                    val = (
                                        item.get("score")
                                        or item.get("value")
                                        or item.get("weight")
                                        or 0
                                    )
                                    component_values.setdefault(str(name), []).append(safe_float(val))
                        else:
                            component_values.setdefault(str(key), []).append(safe_float(value))

            for component, values in component_values.items():
                if not values:
                    continue

                drift = 0.0
                if len(values) >= 2:
                    drift = values[-1] - values[0]

                rows.append({
                    "run_date_sgt": run_date.isoformat(),
                    "theme_name": self.theme_name,
                    "component_key": component[:250],
                    "attribution_trend_score": round(mean(values), 4),
                    "attribution_drift_score": round(drift, 4),
                    "attribution_volatility_score": round(stddev(values), 4),
                    "component_observation_count": len(values),
                    "rolling_window_days": self.rolling_window,
                    "source": "phase2d2_reconstruction",
                    "reconstruction_method": "rolling_component_attribution",
                    "created_at": now_sgt().isoformat(),
                    "updated_at": now_sgt().isoformat(),
                })

        return rows

    def reconstruct_propagation_history(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            obs = grouped[run_date]
            scores = [x.score for x in obs]
            current_score = mean(scores)

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_scores = [
                mean([x.score for x in grouped[d]])
                for d in window_dates
            ]

            previous_score = window_scores[-2] if len(window_scores) >= 2 else current_score
            acceleration = 0.0

            if len(window_scores) >= 3:
                acceleration = (
                    window_scores[-1] - window_scores[-2]
                ) - (
                    window_scores[-2] - window_scores[-3]
                )

            concentration = self._concentration_score(scores)
            instability = clamp(stddev(window_scores) * 3)

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "propagation_score": round(current_score, 4),
                "propagation_change": round(current_score - previous_score, 4),
                "propagation_acceleration": round(acceleration, 4),
                "propagation_concentration_score": round(concentration, 4),
                "propagation_instability_score": round(instability, 4),
                "structural_decomposition_score": round(clamp(current_score - instability + concentration * 0.1), 4),
                "observation_count": len(obs),
                "rolling_window_days": self.rolling_window,
                "source": "phase2d2_reconstruction",
                "reconstruction_method": "rolling_structural_propagation",
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

        return rows

    def _concentration_score(self, values: List[float]) -> float:
        clean = [abs(v) for v in values if v is not None]
        if not clean:
            return 0.0

        total = sum(clean)
        if total == 0:
            return 0.0

        shares = [v / total for v in clean]
        hhi = sum(s ** 2 for s in shares)
        return clamp(hhi * 100)

    def _half_life_estimate(self, persistence_score: float) -> float:
        if persistence_score <= 0:
            return 0.0
        if persistence_score >= 100:
            return float(self.rolling_window)
        decay_rate = max(0.01, 1 - persistence_score / 100)
        return min(float(self.rolling_window), math.log(0.5) / math.log(1 - decay_rate))


# ============================================================
# CHECKPOINTING
# ============================================================

def ensure_checkpoint_table(client: SupabaseRestClient) -> None:
    """
    This function does not create the table automatically because REST cannot
    safely run DDL unless an RPC function already exists.

    Required table SQL is provided below this file.
    """
    if not client.table_exists("structural_theme_reconstruction_checkpoints"):
        print(
            "WARNING: checkpoint table structural_theme_reconstruction_checkpoints "
            "does not exist. Engine will still run, but resumability is reduced."
        )


def load_checkpoint(
    client: SupabaseRestClient,
    *,
    theme_name: str,
) -> Optional[date]:
    if not client.table_exists("structural_theme_reconstruction_checkpoints"):
        return None

    rows = client.select(
        "structural_theme_reconstruction_checkpoints",
        select="*",
        filters={
            "theme_name": f"eq.{theme_name}",
            "pipeline_name": f"eq.{PIPELINE_NAME}",
        },
        order="last_completed_date.desc",
        limit=1,
    )

    if not rows:
        return None

    return parse_date(rows[0].get("last_completed_date"))


def write_checkpoint(
    client: SupabaseRestClient,
    *,
    theme_name: str,
    completed_date: date,
    status: str,
    details: Dict[str, Any],
) -> None:
    if not client.table_exists("structural_theme_reconstruction_checkpoints"):
        return

    row = {
        "pipeline_name": PIPELINE_NAME,
        "theme_name": theme_name,
        "last_completed_date": completed_date.isoformat(),
        "status": status,
        "details": details,
        "updated_at": now_sgt().isoformat(),
    }

    client.upsert(
        "structural_theme_reconstruction_checkpoints",
        [row],
        conflict_columns=["pipeline_name", "theme_name"],
    )


# ============================================================
# TELEMETRY
# ============================================================

def write_telemetry(
    client: SupabaseRestClient,
    *,
    status: str,
    runtime_seconds: float,
    rows_written: int,
    start_date: date,
    end_date: date,
    error_message: Optional[str] = None,
) -> None:
    telemetry_tables = [
        "production_pipeline_runs",
        "structural_theme_pipeline_runs",
    ]

    payload = {
        "run_timestamp_sgt": now_sgt().isoformat(),
        "run_date_sgt": today_sgt().isoformat(),
        "pipeline_name": PIPELINE_NAME,
        "status": status,
        "runtime_seconds": round(runtime_seconds, 4),
        "signal_rows": rows_written,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "error_message": error_message,
    }

    for table in telemetry_tables:
        if client.table_exists(table):
            try:
                client.upsert(
                    table,
                    [payload],
                    conflict_columns=["pipeline_name", "run_date_sgt", "github_run_id"],
                )
                return
            except Exception as exc:
                print(f"Telemetry write failed for {table}: {exc}")

    print("No compatible telemetry table found. Telemetry skipped.")


# ============================================================
# ORCHESTRATION
# ============================================================

def date_chunks(start_date: date, end_date: date, chunk_days: int) -> List[Tuple[date, date]]:
    chunks = []
    cursor = start_date

    while cursor <= end_date:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end_date)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)

    return chunks


def run_reconstruction() -> None:
    started = time.time()
    client = SupabaseRestClient()

    theme_name = DEFAULT_THEME_NAME
    lookback_days = DEFAULT_LOOKBACK_DAYS
    chunk_days = DEFAULT_CHUNK_DAYS

    end_date = today_sgt()
    start_date = end_date - timedelta(days=lookback_days)

    ensure_checkpoint_table(client)

    checkpoint = load_checkpoint(client, theme_name=theme_name)
    if checkpoint and checkpoint >= start_date:
        start_date = checkpoint + timedelta(days=1)

    if start_date > end_date:
        print("Reconstruction already complete based on checkpoint.")
        write_telemetry(
            client,
            status="SUCCESS_NOOP",
            runtime_seconds=time.time() - started,
            rows_written=0,
            start_date=start_date,
            end_date=end_date,
        )
        return

    source_tables = detect_source_tables(client)
    print("Detected source tables:")
    for cfg in source_tables:
        print(f" - {cfg.table}")

    engine = HistoricalReconstructionEngine(
        client,
        theme_name=theme_name,
        rolling_window=DEFAULT_ROLLING_WINDOW,
    )

    total_rows_written = 0

    try:
        for chunk_start, chunk_end in date_chunks(start_date, end_date, chunk_days):
            print(f"\nProcessing reconstruction chunk: {chunk_start} → {chunk_end}")

            observations: List[HistoricalObservation] = []

            # Add rolling buffer before chunk start for correct rolling reconstruction.
            fetch_start = max(
                end_date - timedelta(days=lookback_days),
                chunk_start - timedelta(days=DEFAULT_ROLLING_WINDOW * 2),
            )

            for cfg in source_tables:
                try:
                    source_obs = fetch_source_rows(
                        client,
                        cfg,
                        start_date=fetch_start,
                        end_date=chunk_end,
                        theme_name=theme_name,
                    )
                    observations.extend(source_obs)
                    print(f"   {cfg.table}: {len(source_obs)} observations")
                except Exception as exc:
                    print(f"   WARNING: failed to fetch {cfg.table}: {exc}")

            if not observations:
                print("   No observations found for chunk. Skipping.")
                write_checkpoint(
                    client,
                    theme_name=theme_name,
                    completed_date=chunk_end,
                    status="SKIPPED_NO_DATA",
                    details={"chunk_start": chunk_start.isoformat(), "chunk_end": chunk_end.isoformat()},
                )
                continue

            grouped_all = engine.group_by_date(observations)

            # Restrict writes to actual chunk dates only.
            grouped_chunk = {
                d: v
                for d, v in grouped_all.items()
                if chunk_start <= d <= chunk_end
            }

            if not grouped_chunk:
                print("   No grouped observations inside chunk write window.")
                continue

            momentum_rows = engine.reconstruct_momentum(grouped_chunk)
            regime_rows = engine.reconstruct_regimes(grouped_chunk)
            evidence_rows = engine.reconstruct_evidence_intensity(grouped_chunk)
            driver_rows = engine.reconstruct_driver_persistence(grouped_chunk)
            pathway_rows = engine.reconstruct_pathway_trends(grouped_chunk)
            attribution_rows = engine.reconstruct_attribution_trends(grouped_chunk)
            propagation_rows = engine.reconstruct_propagation_history(grouped_chunk)

            write_plan = [
                (
                    "structural_theme_momentum_history",
                    momentum_rows,
                    ["run_date_sgt", "theme_name"],
                ),
                (
                    "structural_theme_regime_history",
                    regime_rows,
                    ["run_date_sgt", "theme_name"],
                ),
                (
                    "structural_theme_evidence_intensity_history",
                    evidence_rows,
                    ["run_date_sgt", "theme_name"],
                ),
                (
                    "structural_theme_driver_persistence_history",
                    driver_rows,
                    ["run_date_sgt", "theme_name", "driver_key"],
                ),
                (
                    "structural_theme_pathway_trend_history",
                    pathway_rows,
                    ["run_date_sgt", "theme_name", "pathway_key"],
                ),
                (
                    "structural_theme_attribution_trend_history",
                    attribution_rows,
                    ["run_date_sgt", "theme_name", "component_key"],
                ),
                (
                    "structural_theme_propagation_history",
                    propagation_rows,
                    ["run_date_sgt", "theme_name"],
                ),
            ]

            chunk_rows_written = 0

            for table, rows, conflict_cols in write_plan:
                if not client.table_exists(table):
                    print(f"   WARNING: target table missing, skipped: {table}")
                    continue

                written = client.upsert(
                    table,
                    rows,
                    conflict_columns=conflict_cols,
                    batch_size=DEFAULT_BATCH_SIZE,
                )
                chunk_rows_written += written
                print(f"   Upserted {written} rows into {table}")

            total_rows_written += chunk_rows_written

            write_checkpoint(
                client,
                theme_name=theme_name,
                completed_date=chunk_end,
                status="SUCCESS",
                details={
                    "chunk_start": chunk_start.isoformat(),
                    "chunk_end": chunk_end.isoformat(),
                    "rows_written": chunk_rows_written,
                    "source_observations": len(observations),
                },
            )

        runtime = time.time() - started

        write_telemetry(
            client,
            status="SUCCESS",
            runtime_seconds=runtime,
            rows_written=total_rows_written,
            start_date=start_date,
            end_date=end_date,
        )

        print("\nPhase 2D.2 reconstruction complete.")
        print(f"Rows written: {total_rows_written}")
        print(f"Runtime seconds: {round(runtime, 2)}")

    except Exception as exc:
        runtime = time.time() - started
        error_message = f"{type(exc).__name__}: {exc}"

        print("\nERROR during reconstruction:")
        print(error_message)
        traceback.print_exc()

        write_telemetry(
            client,
            status="FAILED",
            runtime_seconds=runtime,
            rows_written=total_rows_written,
            start_date=start_date,
            end_date=end_date,
            error_message=error_message[:1000],
        )

        raise


if __name__ == "__main__":
    run_reconstruction()
