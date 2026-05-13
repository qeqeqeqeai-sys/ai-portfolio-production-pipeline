#!/usr/bin/env python3
"""
Phase 5D — Structural Propagation Regime Forecasting

Deterministic, replay-safe forecasting layer for the modular structural transmission research platform.
Consumes Phase 5C corridor dynamics and produces structural continuation, instability, transition,
fragility, dominance, and confidence scores.

This is not ML prediction. It is explainable structural continuation scoring.
No graph ML, embeddings, networkx centrality, Neo4j, vector DBs, stochastic agents, or autonomous mutation.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import time
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

PIPELINE_NAME = "PHASE5D_STRUCTURAL_PROPAGATION_REGIME_FORECASTING"
SINGAPORE_TZ = timezone(timedelta(hours=8))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "180"))
FORECAST_HORIZON_DAYS = int(os.getenv("FORECAST_HORIZON_DAYS", "30"))
PRIORITY_THRESHOLD = float(os.getenv("PRIORITY_THRESHOLD", "0.62"))
TRANSITION_WATCH_THRESHOLD = float(os.getenv("TRANSITION_WATCH_THRESHOLD", "0.58"))
INSTABILITY_WATCH_THRESHOLD = float(os.getenv("INSTABILITY_WATCH_THRESHOLD", "0.58"))
CONTINUATION_WATCH_THRESHOLD = float(os.getenv("CONTINUATION_WATCH_THRESHOLD", "0.66"))


def today_sgt() -> str:
    return datetime.now(SINGAPORE_TZ).date().isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def parse_date(value: Any) -> Optional[date]:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


def clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
    try:
        x = float(value if value is not None else 0.0)
    except Exception:
        x = 0.0
    if math.isnan(x) or math.isinf(x):
        x = 0.0
    return max(low, min(high, x))


def safe_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except Exception:
        return None


def safe_avg(values: Iterable[Optional[float]]) -> Optional[float]:
    vals = [float(v) for v in values if v is not None]
    return sum(vals) / len(vals) if vals else None


def bool_score(value: Any) -> float:
    return 1.0 if bool(value) else 0.0


class SupabaseClient:
    def __init__(self, url: str, key: str):
        if not url or not key:
            raise RuntimeError("Missing SUPABASE_URL or Supabase key environment variable")
        self.url = url
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, method: str, table: str, params: Optional[Dict[str, str]] = None, payload: Any = None) -> Any:
        endpoint = f"{self.url}/rest/v1/{table}"
        last_error = None
        for attempt in range(4):
            try:
                response = requests.request(method, endpoint, headers=self.headers, params=params, json=payload, timeout=60)
                if response.status_code in (200, 201, 204):
                    if not response.text:
                        return []
                    return response.json()
                last_error = f"{response.status_code}: {response.text[:800]}"
            except Exception as exc:
                last_error = str(exc)
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Supabase {method} {table} failed: {last_error}")

    def fetch_all(self, table: str, params: Optional[Dict[str, str]] = None, page_size: int = 1000) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        offset = 0
        while True:
            q = dict(params or {})
            q["limit"] = str(page_size)
            q["offset"] = str(offset)
            batch = self._request("GET", table, q)
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        return rows

    def upsert(self, table: str, rows: List[Dict[str, Any]], conflict: str, chunk_size: int = 200) -> int:
        if not rows:
            return 0
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            endpoint = f"{self.url}/rest/v1/{table}"
            headers = dict(self.headers)
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
            response = requests.post(endpoint, headers=headers, params={"on_conflict": conflict}, json=chunk, timeout=60)
            if response.status_code not in (200, 201, 204):
                raise RuntimeError(f"Supabase upsert {table} failed: {response.status_code}: {response.text[:1000]}")
            total += len(chunk)
        return total


class StructuralPropagationRegimeForecastingEngine:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.run_id = f"phase5d_{today_sgt()}_{uuid.uuid4().hex[:10]}"
        self.run_date_sgt = today_sgt()
        self.started = time.time()
        self.stats: Dict[str, int] = defaultdict(int)
        self.validation_rows: List[Dict[str, Any]] = []

    def fetch_dynamics(self) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        since = (datetime.now(SINGAPORE_TZ).date() - timedelta(days=LOOKBACK_DAYS)).isoformat()
        historical = self.db.fetch_all(
            "structural_theme_graph_corridor_dynamics",
            {"select": "*", "run_date_sgt": f"gte.{since}", "order": "run_date_sgt.desc,created_at.desc"},
        )
        self.stats["historical_dynamics_loaded"] = len(historical)
        if not historical:
            return self.run_date_sgt, [], [], []

        latest_date = max((r.get("run_date_sgt") or "") for r in historical)
        latest = [r for r in historical if r.get("run_date_sgt") == latest_date]
        current_by_hash: Dict[str, Dict[str, Any]] = {}
        for row in sorted(latest, key=lambda r: (r.get("created_at") or "", r.get("id") or 0), reverse=True):
            h = row.get("corridor_hash")
            if h and h not in current_by_hash:
                current_by_hash[h] = row
        current = list(current_by_hash.values())
        self.stats["dynamics_loaded"] = len(current)

        summaries = self.db.fetch_all(
            "structural_theme_graph_regime_corridor_dynamics_summary",
            {"select": "*", "run_date_sgt": f"eq.{latest_date}", "order": "created_at.desc"},
        )
        # Deduplicate summaries by regime.
        seen = set()
        clean_summaries = []
        for row in summaries:
            key = row.get("regime_sensitivity") or "unknown"
            if key not in seen:
                clean_summaries.append(row)
                seen.add(key)
        self.stats["regime_summaries_loaded"] = len(clean_summaries)
        return latest_date, current, historical, clean_summaries

    def history_by_corridor(self, historical: List[Dict[str, Any]], current_date: str) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        for row in historical:
            h = row.get("corridor_hash")
            d = row.get("run_date_sgt")
            if not h or not d or d >= current_date:
                continue
            existing = grouped[h].get(d)
            if existing is None or (str(row.get("created_at") or ""), int(row.get("id") or 0)) > (str(existing.get("created_at") or ""), int(existing.get("id") or 0)):
                grouped[h][d] = row
        return {h: sorted(rows.values(), key=lambda r: r.get("run_date_sgt") or "") for h, rows in grouped.items()}

    def trend_score(self, history: List[Dict[str, Any]], current: Dict[str, Any], field: str) -> float:
        values = [safe_float(r.get(field)) for r in history[-5:]] + [safe_float(current.get(field))]
        vals = [v for v in values if v is not None]
        if len(vals) < 2:
            return 0.50
        slope = vals[-1] - vals[0]
        return clamp(0.50 + slope)

    def persistence_ratio(self, history: List[Dict[str, Any]], current_date_str: str) -> float:
        dates = sorted({r.get("run_date_sgt") for r in history if r.get("run_date_sgt")} | {current_date_str})
        if not dates:
            return 0.0
        first = parse_date(dates[0]) or parse_date(current_date_str) or datetime.now(SINGAPORE_TZ).date()
        current = parse_date(current_date_str) or datetime.now(SINGAPORE_TZ).date()
        elapsed = max(1, (current - first).days + 1)
        return clamp(len(dates) / min(LOOKBACK_DAYS, elapsed))

    def regime_context_map(self, summaries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        return {r.get("regime_sensitivity") or "unknown": r for r in summaries}

    def classify_forecast(self, forecast_score: float, transition: float, instability: float, continuation: float, confidence: float) -> Tuple[str, str]:
        if transition >= 0.68 and instability >= 0.58:
            return "transition_pressure_forecast", "regime_transition_watch"
        if instability >= 0.68:
            return "instability_buildup_forecast", "instability_watch"
        if continuation >= 0.72 and confidence >= 0.58:
            return "structural_continuation_forecast", "continuation_watch"
        if forecast_score >= PRIORITY_THRESHOLD:
            return "priority_structural_forecast", "priority_watch"
        if forecast_score >= 0.48:
            return "moderate_structural_forecast", "monitor"
        return "low_signal_forecast", "neutral"

    def build_forecast_row(
        self,
        current: Dict[str, Any],
        history: List[Dict[str, Any]],
        current_date_str: str,
        regime_context: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        regime = current.get("regime_sensitivity") or "unknown"
        summary = regime_context.get(regime, {})

        current_score = clamp(current.get("current_corridor_intelligence_score"))
        drift = clamp(current.get("corridor_drift_score"))
        mutation = clamp(current.get("corridor_mutation_score"))
        stress = clamp(current.get("stress_accumulation_score"))
        survivability = clamp(current.get("corridor_survivability_score"))
        bottleneck = clamp(current.get("bottleneck_score"))
        reuse_frequency = int(current.get("reuse_frequency") or 0)
        reuse_score = clamp(reuse_frequency / 10.0)
        dominance = bool_score(current.get("dominant_pathway_flag"))
        transition_flag = bool_score(current.get("regime_transition_flag"))

        persistence = self.persistence_ratio(history, current_date_str)
        score_trend = self.trend_score(history, current, "current_corridor_intelligence_score")
        stress_trend = self.trend_score(history, current, "stress_accumulation_score")
        drift_trend = self.trend_score(history, current, "corridor_drift_score")
        survivability_trend = self.trend_score(history, current, "corridor_survivability_score")

        regime_avg_stress = clamp(summary.get("avg_stress_accumulation_score"))
        regime_avg_drift = clamp(summary.get("avg_corridor_drift_score"))
        regime_avg_survival = clamp(summary.get("avg_survivability_score"))
        regime_transition_density = clamp((summary.get("transition_flag_count") or 0) / max(1, (summary.get("corridor_count") or 1)))

        continuation = clamp(
            0.25 * survivability
            + 0.20 * persistence
            + 0.20 * current_score
            + 0.15 * survivability_trend
            + 0.10 * reuse_score
            + 0.10 * (1.0 - mutation)
        )
        instability = clamp(
            0.30 * stress
            + 0.20 * drift
            + 0.15 * mutation
            + 0.15 * bottleneck
            + 0.10 * stress_trend
            + 0.10 * regime_avg_stress
        )
        transition = clamp(
            0.25 * transition_flag
            + 0.20 * drift
            + 0.20 * regime_transition_density
            + 0.15 * mutation
            + 0.10 * drift_trend
            + 0.10 * regime_avg_drift
        )
        fragility = clamp(
            0.30 * bottleneck
            + 0.25 * (1.0 - survivability)
            + 0.20 * stress
            + 0.15 * mutation
            + 0.10 * (1.0 - persistence)
        )
        dominance_forecast = clamp(
            0.25 * dominance
            + 0.25 * current_score
            + 0.20 * reuse_score
            + 0.15 * bottleneck
            + 0.15 * continuation
        )
        confidence = clamp(
            0.30 * persistence
            + 0.20 * survivability
            + 0.20 * regime_avg_survival
            + 0.15 * min(1.0, len(history) / 5.0)
            + 0.15 * (1.0 - mutation * 0.50)
        )

        forecast_score = clamp(
            0.24 * continuation
            + 0.22 * instability
            + 0.20 * transition
            + 0.14 * fragility
            + 0.12 * dominance_forecast
            + 0.08 * confidence
        )
        classification, signal = self.classify_forecast(forecast_score, transition, instability, continuation, confidence)

        row = {
            "run_id": self.run_id,
            "run_date_sgt": current_date_str,
            "corridor_hash": current.get("corridor_hash"),
            "corridor_key": current.get("corridor_key"),
            "corridor_type": current.get("corridor_type") or "unknown",
            "corridor_classification": current.get("corridor_classification") or "unknown",
            "source_node_key": current.get("source_node_key"),
            "target_node_key": current.get("target_node_key"),
            "intermediary_node_keys": current.get("intermediary_node_keys") or [],
            "path_nodes": current.get("path_nodes") or [],
            "hop_count": int(current.get("hop_count") or 2),
            "regime_sensitivity": regime,
            "activation_state": current.get("activation_state") or "unknown",
            "dynamics_classification": current.get("dynamics_classification") or "unknown",
            "regime_transition_signal": current.get("regime_transition_signal") or "none",
            "bottleneck_node_key": current.get("bottleneck_node_key"),
            "current_corridor_intelligence_score": current_score,
            "corridor_drift_score": drift,
            "corridor_mutation_score": mutation,
            "stress_accumulation_score": stress,
            "corridor_survivability_score": survivability,
            "bottleneck_score": bottleneck,
            "reuse_frequency": reuse_frequency,
            "continuation_probability_score": continuation,
            "instability_pressure_score": instability,
            "regime_transition_likelihood_score": transition,
            "structural_fragility_score": fragility,
            "pathway_dominance_forecast_score": dominance_forecast,
            "forecast_confidence_score": confidence,
            "propagation_regime_forecast_score": forecast_score,
            "forecast_horizon_days": FORECAST_HORIZON_DAYS,
            "forecast_classification": classification,
            "forecast_signal": signal,
            "priority_flag": forecast_score >= PRIORITY_THRESHOLD,
            "transition_watch_flag": transition >= TRANSITION_WATCH_THRESHOLD,
            "instability_watch_flag": instability >= INSTABILITY_WATCH_THRESHOLD,
            "continuation_watch_flag": continuation >= CONTINUATION_WATCH_THRESHOLD,
            "evidence_summary": {
                "source_phase": "phase5c_corridor_dynamics",
                "regime_summary_used": bool(summary),
                "history_observations": len(history),
                "deterministic_forecast_only": True,
            },
            "component_scores": {
                "continuation_probability_score": continuation,
                "instability_pressure_score": instability,
                "regime_transition_likelihood_score": transition,
                "structural_fragility_score": fragility,
                "pathway_dominance_forecast_score": dominance_forecast,
                "forecast_confidence_score": confidence,
                "persistence_ratio": persistence,
                "score_trend": score_trend,
                "stress_trend": stress_trend,
                "drift_trend": drift_trend,
                "survivability_trend": survivability_trend,
                "regime_avg_stress": regime_avg_stress,
                "regime_avg_drift": regime_avg_drift,
                "regime_transition_density": regime_transition_density,
            },
            "metadata": {
                "engine_version": "phase5d_v1",
                "forecast_method": "deterministic_structural_continuation_scoring",
                "forecast_horizon_days": FORECAST_HORIZON_DAYS,
                "lookback_days": LOOKBACK_DAYS,
                "source_dynamics_id": current.get("id"),
                "created_at_utc": now_iso(),
            },
        }
        return row

    def build_forecasts(self, current_date: str, current: List[Dict[str, Any]], historical: List[Dict[str, Any]], summaries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped_history = self.history_by_corridor(historical, current_date)
        regime_context = self.regime_context_map(summaries)
        rows: List[Dict[str, Any]] = []
        for dyn in current:
            h = dyn.get("corridor_hash")
            if not h:
                continue
            row = self.build_forecast_row(dyn, grouped_history.get(h, []), current_date, regime_context)
            if row.get("corridor_hash") and row.get("source_node_key") and row.get("target_node_key"):
                rows.append(row)
        rows.sort(key=lambda r: r["propagation_regime_forecast_score"], reverse=True)
        self.stats["forecasts_generated"] = len(rows)
        self.stats["priority_forecasts_detected"] = sum(1 for r in rows if r.get("priority_flag"))
        self.stats["transition_watch_detected"] = sum(1 for r in rows if r.get("transition_watch_flag"))
        self.stats["instability_watch_detected"] = sum(1 for r in rows if r.get("instability_watch_flag"))
        self.stats["continuation_watch_detected"] = sum(1 for r in rows if r.get("continuation_watch_flag"))
        return rows

    def classify_regime_forecast(self, rows: List[Dict[str, Any]]) -> Tuple[str, str]:
        if not rows:
            return "empty_regime_forecast", "neutral"
        avg_transition = safe_avg([r.get("regime_transition_likelihood_score") for r in rows]) or 0.0
        avg_instability = safe_avg([r.get("instability_pressure_score") for r in rows]) or 0.0
        avg_continuation = safe_avg([r.get("continuation_probability_score") for r in rows]) or 0.0
        avg_score = safe_avg([r.get("propagation_regime_forecast_score") for r in rows]) or 0.0
        signals = Counter([r.get("forecast_signal") or "neutral" for r in rows])
        dominant_signal = signals.most_common(1)[0][0]
        if avg_transition >= 0.60 and avg_instability >= 0.55:
            return "regime_transition_pressure_forecast", "regime_transition_watch"
        if avg_instability >= 0.62:
            return "regime_instability_buildup_forecast", "instability_watch"
        if avg_continuation >= 0.68:
            return "regime_structural_continuation_forecast", "continuation_watch"
        if avg_score >= 0.55:
            return "regime_priority_monitor_forecast", dominant_signal
        return "regime_low_signal_forecast", dominant_signal

    def build_summaries(self, forecasts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in forecasts:
            grouped[row.get("regime_sensitivity") or "unknown"].append(row)
        summaries: List[Dict[str, Any]] = []
        for regime, rows in sorted(grouped.items()):
            classification, signal = self.classify_regime_forecast(rows)
            top = sorted(rows, key=lambda r: r.get("propagation_regime_forecast_score") or 0, reverse=True)[:5]
            summaries.append({
                "run_id": self.run_id,
                "run_date_sgt": self.run_date_sgt,
                "regime_sensitivity": regime,
                "forecast_horizon_days": FORECAST_HORIZON_DAYS,
                "forecast_count": len(rows),
                "priority_forecast_count": sum(1 for r in rows if r.get("priority_flag")),
                "transition_watch_count": sum(1 for r in rows if r.get("transition_watch_flag")),
                "instability_watch_count": sum(1 for r in rows if r.get("instability_watch_flag")),
                "continuation_watch_count": sum(1 for r in rows if r.get("continuation_watch_flag")),
                "high_confidence_forecast_count": sum(1 for r in rows if (r.get("forecast_confidence_score") or 0) >= 0.60),
                "avg_continuation_probability_score": clamp(safe_avg([r.get("continuation_probability_score") for r in rows]) or 0),
                "avg_instability_pressure_score": clamp(safe_avg([r.get("instability_pressure_score") for r in rows]) or 0),
                "avg_regime_transition_likelihood_score": clamp(safe_avg([r.get("regime_transition_likelihood_score") for r in rows]) or 0),
                "avg_structural_fragility_score": clamp(safe_avg([r.get("structural_fragility_score") for r in rows]) or 0),
                "avg_pathway_dominance_forecast_score": clamp(safe_avg([r.get("pathway_dominance_forecast_score") for r in rows]) or 0),
                "avg_forecast_confidence_score": clamp(safe_avg([r.get("forecast_confidence_score") for r in rows]) or 0),
                "avg_propagation_regime_forecast_score": clamp(safe_avg([r.get("propagation_regime_forecast_score") for r in rows]) or 0),
                "max_propagation_regime_forecast_score": clamp(max([safe_float(r.get("propagation_regime_forecast_score")) or 0 for r in rows] or [0])),
                "regime_forecast_classification": classification,
                "dominant_forecast_signal": signal,
                "top_corridor_hashes": [r.get("corridor_hash") for r in top],
                "metadata": {"engine_version": "phase5d_v1", "created_at_utc": now_iso()},
            })
        return summaries

    def add_validation(self, name: str, passed: bool, observed: Optional[float], threshold: Optional[float], message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.validation_rows.append({
            "run_id": self.run_id,
            "run_date_sgt": self.run_date_sgt,
            "validation_name": name,
            "validation_status": "PASS" if passed else "FAIL",
            "observed_value": observed,
            "threshold_value": threshold,
            "message": message,
            "details": details or {},
        })

    def validate(self, current: List[Dict[str, Any]], summaries: List[Dict[str, Any]], forecasts: List[Dict[str, Any]], forecast_summaries: List[Dict[str, Any]]) -> int:
        self.add_validation("phase5c_dynamics_available", len(current) > 0, len(current), 1, "Current Phase 5C dynamics are available" if current else "No current Phase 5C dynamics found")
        self.add_validation("forecasts_generated_for_dynamics", len(forecasts) == len(current), len(forecasts), len(current), "Forecast generated for every current corridor dynamic" if len(forecasts) == len(current) else "Some dynamics rows did not produce forecasts")
        self.add_validation("regime_context_available", len(summaries) > 0 if current else True, len(summaries), 1 if current else 0, "Regime summaries are available" if summaries else "No regime summaries found; forecasts used corridor-level context only")
        invalid_scores = sum(1 for r in forecasts if not (0 <= float(r.get("propagation_regime_forecast_score") or 0) <= 1) or not (0 <= float(r.get("forecast_confidence_score") or 0) <= 1))
        self.add_validation("forecast_score_range_check", invalid_scores == 0, invalid_scores, 0, "All forecast scores are within [0,1]" if invalid_scores == 0 else "Some forecast scores are outside [0,1]")
        self.add_validation("forecast_summaries_generated", len(forecast_summaries) > 0 if forecasts else True, len(forecast_summaries), 1 if forecasts else 0, "Forecast summaries generated" if forecast_summaries else "No forecast summaries generated")
        failures = sum(1 for r in self.validation_rows if r["validation_status"] == "FAIL")
        self.stats["validation_failures"] = failures
        return failures

    def persist_telemetry(self, status: str, error_message: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        row = {
            "run_id": self.run_id,
            "run_date_sgt": self.run_date_sgt,
            "pipeline_name": PIPELINE_NAME,
            "status": status,
            "dynamics_loaded": self.stats.get("dynamics_loaded", 0),
            "regime_summaries_loaded": self.stats.get("regime_summaries_loaded", 0),
            "historical_dynamics_loaded": self.stats.get("historical_dynamics_loaded", 0),
            "forecasts_generated": self.stats.get("forecasts_generated", 0),
            "forecasts_persisted": self.stats.get("forecasts_persisted", 0),
            "summaries_persisted": self.stats.get("summaries_persisted", 0),
            "priority_forecasts_detected": self.stats.get("priority_forecasts_detected", 0),
            "transition_watch_detected": self.stats.get("transition_watch_detected", 0),
            "instability_watch_detected": self.stats.get("instability_watch_detected", 0),
            "continuation_watch_detected": self.stats.get("continuation_watch_detected", 0),
            "validation_failures": self.stats.get("validation_failures", 0),
            "runtime_seconds": round(time.time() - self.started, 3),
            "error_message": error_message,
            "details": details or {"engine_version": "phase5d_v1", "forecast_horizon_days": FORECAST_HORIZON_DAYS, "lookback_days": LOOKBACK_DAYS},
        }
        self.db.upsert("structural_theme_graph_regime_forecast_telemetry", [row], "run_id")

    def run(self) -> Dict[str, Any]:
        try:
            current_date, current, historical, summaries = self.fetch_dynamics()
            forecasts = self.build_forecasts(current_date, current, historical, summaries)
            forecast_summaries = self.build_summaries(forecasts)
            self.validate(current, summaries, forecasts, forecast_summaries)

            self.stats["forecasts_persisted"] = self.db.upsert(
                "structural_theme_graph_corridor_regime_forecasts",
                forecasts,
                "run_date_sgt,corridor_hash,forecast_horizon_days",
            )
            self.stats["summaries_persisted"] = self.db.upsert(
                "structural_theme_graph_regime_forecast_summary",
                forecast_summaries,
                "run_date_sgt,regime_sensitivity,forecast_horizon_days",
            )
            self.db.upsert("structural_theme_graph_regime_forecast_validation", self.validation_rows, "run_id,validation_name")

            status = "SUCCESS" if self.stats.get("validation_failures", 0) == 0 else "WARNING"
            self.persist_telemetry(status)
            result = {
                "status": status,
                "run_id": self.run_id,
                "run_date_sgt": current_date,
                "dynamics_loaded": self.stats.get("dynamics_loaded", 0),
                "regime_summaries_loaded": self.stats.get("regime_summaries_loaded", 0),
                "historical_dynamics_loaded": self.stats.get("historical_dynamics_loaded", 0),
                "forecasts_generated": self.stats.get("forecasts_generated", 0),
                "forecasts_persisted": self.stats.get("forecasts_persisted", 0),
                "summaries_persisted": self.stats.get("summaries_persisted", 0),
                "priority_forecasts_detected": self.stats.get("priority_forecasts_detected", 0),
                "transition_watch_detected": self.stats.get("transition_watch_detected", 0),
                "instability_watch_detected": self.stats.get("instability_watch_detected", 0),
                "continuation_watch_detected": self.stats.get("continuation_watch_detected", 0),
                "validation_failures": self.stats.get("validation_failures", 0),
            }
            print(json.dumps(result, indent=2, sort_keys=False))
            return result
        except Exception as exc:
            self.stats["validation_failures"] = self.stats.get("validation_failures", 0) + 1
            try:
                self.persist_telemetry("FAILED", str(exc), {"engine_version": "phase5d_v1"})
            finally:
                print(json.dumps({"status": "FAILED", "run_id": self.run_id, "error": str(exc)}, indent=2))
            raise


def main() -> None:
    db = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or "")
    engine = StructuralPropagationRegimeForecastingEngine(db)
    engine.run()


if __name__ == "__main__":
    main()
