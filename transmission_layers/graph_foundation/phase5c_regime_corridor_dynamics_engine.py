#!/usr/bin/env python3
"""
Phase 5C — Regime-Aware Corridor Dynamics

Deterministic corridor dynamics engine for the modular structural transmission research platform.
Consumes Phase 5B propagation corridors and converts static corridor intelligence into replay-safe
regime-aware time dynamics.

No graph ML, embeddings, networkx centrality, Neo4j, vector DBs, stochastic agents, or autonomous mutation.
"""

from __future__ import annotations

import json
import math
import os
import statistics
import time
import uuid
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

PIPELINE_NAME = "PHASE5C_REGIME_AWARE_CORRIDOR_DYNAMICS"
SINGAPORE_TZ = timezone(timedelta(hours=8))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "180"))
MIN_CURRENT_SCORE = float(os.getenv("MIN_CURRENT_SCORE", "0.0"))
TRANSITION_DELTA_THRESHOLD = float(os.getenv("TRANSITION_DELTA_THRESHOLD", "0.08"))
DORMANCY_GAP_DAYS = int(os.getenv("DORMANCY_GAP_DAYS", "7"))


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


def numeric_delta(current: Any, previous: Any) -> Optional[float]:
    c = safe_float(current)
    p = safe_float(previous)
    if c is None or p is None:
        return None
    return c - p


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
            params = {"on_conflict": conflict}
            headers = dict(self.headers)
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
            endpoint = f"{self.url}/rest/v1/{table}"
            response = requests.post(endpoint, headers=headers, params=params, json=chunk, timeout=60)
            if response.status_code not in (200, 201, 204):
                raise RuntimeError(f"Supabase upsert {table} failed: {response.status_code}: {response.text[:1000]}")
            total += len(chunk)
        return total


class RegimeCorridorDynamicsEngine:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.run_id = f"phase5c_{today_sgt()}_{uuid.uuid4().hex[:10]}"
        self.run_date_sgt = today_sgt()
        self.started = time.time()
        self.stats: Dict[str, int] = defaultdict(int)
        self.validation_rows: List[Dict[str, Any]] = []

    def fetch_corridors(self) -> Tuple[str, List[Dict[str, Any]], List[Dict[str, Any]]]:
        since = (datetime.now(SINGAPORE_TZ).date() - timedelta(days=LOOKBACK_DAYS)).isoformat()
        historical = self.db.fetch_all(
            "structural_theme_graph_propagation_corridors",
            {
                "select": "*",
                "run_date_sgt": f"gte.{since}",
                "order": "run_date_sgt.desc,created_at.desc",
            },
        )
        self.stats["historical_corridors_loaded"] = len(historical)
        if not historical:
            return self.run_date_sgt, [], []

        latest_date = max((r.get("run_date_sgt") or "") for r in historical)
        current = [r for r in historical if r.get("run_date_sgt") == latest_date]

        # If multiple same-day runs exist, keep the newest row per corridor hash.
        current_by_hash: Dict[str, Dict[str, Any]] = {}
        for row in sorted(current, key=lambda r: (r.get("created_at") or "", r.get("id") or 0), reverse=True):
            h = row.get("corridor_hash")
            if h and h not in current_by_hash:
                score = clamp(row.get("corridor_intelligence_score"))
                if score >= MIN_CURRENT_SCORE:
                    current_by_hash[h] = row

        current_rows = list(current_by_hash.values())
        self.stats["current_corridors_loaded"] = len(current_rows)
        return latest_date, current_rows, historical

    def history_by_corridor(self, historical: List[Dict[str, Any]], current_date: str) -> Dict[str, List[Dict[str, Any]]]:
        grouped: Dict[str, Dict[str, Dict[str, Any]]] = defaultdict(dict)
        for row in historical:
            h = row.get("corridor_hash")
            d = row.get("run_date_sgt")
            if not h or not d or d >= current_date:
                continue
            # Deduplicate same-day rows by latest created_at/id.
            existing = grouped[h].get(d)
            if existing is None or (str(row.get("created_at") or ""), int(row.get("id") or 0)) > (str(existing.get("created_at") or ""), int(existing.get("id") or 0)):
                grouped[h][d] = row
        return {h: sorted(rows.values(), key=lambda r: r.get("run_date_sgt") or "") for h, rows in grouped.items()}

    def rolling_average(self, history: List[Dict[str, Any]], current_date: date, days: int, field: str) -> Optional[float]:
        cutoff = current_date - timedelta(days=days)
        vals: List[float] = []
        for row in history:
            d = parse_date(row.get("run_date_sgt"))
            if d and cutoff <= d < current_date:
                val = safe_float(row.get(field))
                if val is not None:
                    vals.append(val)
        return safe_avg(vals)

    def classify_activation(self, current: Dict[str, Any], previous: Optional[Dict[str, Any]], score_delta: Optional[float], gap_days: Optional[int]) -> str:
        score = clamp(current.get("corridor_intelligence_score"))
        if previous is None:
            return "emerging"
        if gap_days is not None and gap_days >= DORMANCY_GAP_DAYS and score_delta is not None and score_delta > TRANSITION_DELTA_THRESHOLD:
            return "reactivating"
        if score < 0.20 and (gap_days is not None and gap_days >= DORMANCY_GAP_DAYS):
            return "dormant"
        if score_delta is not None and score_delta <= -TRANSITION_DELTA_THRESHOLD:
            return "decaying"
        if score_delta is not None and score_delta >= TRANSITION_DELTA_THRESHOLD:
            return "accelerating"
        if score >= 0.45 and score_delta is not None and abs(score_delta) < 0.03:
            return "stable_active"
        return "active"

    def classify_dynamics(self, row: Dict[str, Any]) -> str:
        state = row["activation_state"]
        drift = clamp(row["corridor_drift_score"])
        stress = clamp(row["stress_accumulation_score"])
        survival = clamp(row["corridor_survivability_score"])
        if state == "emerging" and stress >= 0.55:
            return "emerging_high_stress_corridor"
        if state == "reactivating":
            return "reactivating_corridor"
        if state == "decaying" and stress >= 0.50:
            return "decaying_stress_corridor"
        if drift >= 0.55:
            return "high_drift_corridor"
        if survival >= 0.70 and stress >= 0.50:
            return "durable_stress_corridor"
        if survival >= 0.70:
            return "durable_corridor"
        if state == "dormant":
            return "dormant_corridor"
        return "normal_corridor_dynamics"

    def transition_signal(self, current: Dict[str, Any], previous: Optional[Dict[str, Any]], score_delta: Optional[float], drift: float, stress: float) -> Tuple[str, bool]:
        if previous is None:
            return "new_corridor_observation", False
        curr_regime = current.get("regime_sensitivity") or "unknown"
        prev_regime = previous.get("regime_sensitivity") or "unknown"
        if curr_regime != prev_regime:
            return "regime_sensitivity_shift", True
        if score_delta is not None and score_delta >= TRANSITION_DELTA_THRESHOLD and stress >= 0.55:
            return "corridor_stress_acceleration", True
        if score_delta is not None and score_delta <= -TRANSITION_DELTA_THRESHOLD:
            return "corridor_degradation", True
        if drift >= 0.55:
            return "corridor_drift_breakout", True
        return "none", False

    def build_dynamics_row(self, current: Dict[str, Any], history: List[Dict[str, Any]], current_date_str: str) -> Dict[str, Any]:
        current_date = parse_date(current_date_str) or datetime.now(SINGAPORE_TZ).date()
        previous = history[-1] if history else None
        previous_date = parse_date(previous.get("run_date_sgt")) if previous else None
        gap_days = (current_date - previous_date).days if previous_date else None

        current_score = clamp(current.get("corridor_intelligence_score"))
        previous_score = safe_float(previous.get("corridor_intelligence_score")) if previous else None
        rolling_7d = self.rolling_average(history, current_date, 7, "corridor_intelligence_score")
        rolling_30d = self.rolling_average(history, current_date, 30, "corridor_intelligence_score")

        score_delta_previous = numeric_delta(current_score, previous_score)
        score_delta_7d = numeric_delta(current_score, rolling_7d)
        score_delta_30d = numeric_delta(current_score, rolling_30d)
        strength_delta = numeric_delta(current.get("corridor_strength"), previous.get("corridor_strength") if previous else None)
        persistence_delta = numeric_delta(current.get("corridor_persistence"), previous.get("corridor_persistence") if previous else None)
        stability_delta = numeric_delta(current.get("corridor_stability"), previous.get("corridor_stability") if previous else None)
        reuse_delta_raw = numeric_delta(current.get("reuse_frequency"), previous.get("reuse_frequency") if previous else None)
        reuse_delta = reuse_delta_raw / 20.0 if reuse_delta_raw is not None else None

        historical_scores = [safe_float(r.get("corridor_intelligence_score")) for r in history]
        score_series = [v for v in historical_scores if v is not None] + [current_score]
        volatility = clamp(statistics.pstdev(score_series) if len(score_series) > 1 else 0.0)

        delta_components = [
            abs(v) for v in [score_delta_previous, score_delta_7d, score_delta_30d, strength_delta, persistence_delta, stability_delta, reuse_delta] if v is not None
        ]
        drift_score = clamp((safe_avg(delta_components) or 0.0) + 0.50 * volatility)

        mutation_components = []
        if previous:
            mutation_components.append(1.0 if current.get("corridor_classification") != previous.get("corridor_classification") else 0.0)
            mutation_components.append(1.0 if current.get("regime_sensitivity") != previous.get("regime_sensitivity") else 0.0)
            mutation_components.append(1.0 if current.get("bottleneck_node_key") != previous.get("bottleneck_node_key") else 0.0)
            mutation_components.append(1.0 if json.dumps(current.get("path_nodes", []), sort_keys=True) != json.dumps(previous.get("path_nodes", []), sort_keys=True) else 0.0)
        mutation_score = clamp((safe_avg(mutation_components) or 0.0) * 0.75 + drift_score * 0.25)

        observation_dates = sorted({r.get("run_date_sgt") for r in history if r.get("run_date_sgt")} | {current_date_str})
        first_seen = observation_dates[0] if observation_dates else current_date_str
        days_observed = max(1, len(observation_dates))
        elapsed_days = max(1, ((current_date - (parse_date(first_seen) or current_date)).days + 1))
        continuity_ratio = clamp(days_observed / min(max(1, LOOKBACK_DAYS), elapsed_days))

        score_increase_component = clamp((score_delta_previous or 0.0 + 0.20) / 0.40) if score_delta_previous is not None else 0.50
        regime_sensitive_component = 1.0 if current.get("regime_sensitivity") == "regime_sensitive" else 0.45 if current.get("regime_sensitivity") == "mixed_regime_sensitivity" else 0.25
        stress_accumulation = clamp(
            0.30 * clamp(current.get("bottleneck_score"))
            + 0.25 * clamp(current.get("corridor_reuse_score"))
            + 0.20 * score_increase_component
            + 0.15 * regime_sensitive_component
            + 0.10 * clamp(current.get("avg_evidence_intensity"))
        )

        survivability = clamp(
            0.30 * continuity_ratio
            + 0.25 * clamp(current.get("corridor_persistence"))
            + 0.20 * clamp(current.get("corridor_stability"))
            + 0.15 * clamp(current.get("avg_confidence_score"))
            + 0.10 * (1.0 - volatility)
        )

        activation_state = self.classify_activation(current, previous, score_delta_previous, gap_days)
        signal, transition_flag = self.transition_signal(current, previous, score_delta_previous, drift_score, stress_accumulation)

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
            "regime_sensitivity": current.get("regime_sensitivity") or "unknown",
            "current_corridor_intelligence_score": current_score,
            "previous_corridor_intelligence_score": previous_score,
            "rolling_7d_corridor_intelligence_score": rolling_7d,
            "rolling_30d_corridor_intelligence_score": rolling_30d,
            "score_delta_previous": score_delta_previous,
            "score_delta_7d": score_delta_7d,
            "score_delta_30d": score_delta_30d,
            "strength_delta_previous": strength_delta,
            "persistence_delta_previous": persistence_delta,
            "stability_delta_previous": stability_delta,
            "reuse_delta_previous": reuse_delta_raw,
            "observation_count": len(history) + 1,
            "days_observed": days_observed,
            "first_seen_run_date_sgt": first_seen,
            "previous_seen_run_date_sgt": previous.get("run_date_sgt") if previous else None,
            "last_seen_run_date_sgt": current_date_str,
            "days_since_previous_seen": gap_days,
            "corridor_volatility_score": volatility,
            "corridor_drift_score": drift_score,
            "corridor_mutation_score": mutation_score,
            "stress_accumulation_score": stress_accumulation,
            "corridor_survivability_score": survivability,
            "activation_state": activation_state,
            "dynamics_classification": "pending",
            "regime_transition_signal": signal,
            "regime_transition_flag": transition_flag,
            "dominant_pathway_flag": bool(current.get("dominant_pathway_flag")),
            "bottleneck_node_key": current.get("bottleneck_node_key"),
            "bottleneck_score": clamp(current.get("bottleneck_score")),
            "reuse_frequency": int(current.get("reuse_frequency") or 0),
            "metadata": {
                "engine_version": "phase5c_v1",
                "source_phase": "phase5b_propagation_corridors",
                "lookback_days": LOOKBACK_DAYS,
                "current_corridor_id": current.get("id"),
                "created_at_utc": now_iso(),
            },
            "component_scores": {
                "continuity_ratio": continuity_ratio,
                "volatility": volatility,
                "drift_score": drift_score,
                "mutation_score": mutation_score,
                "stress_accumulation": stress_accumulation,
                "survivability": survivability,
                "score_delta_previous": score_delta_previous,
                "score_delta_7d": score_delta_7d,
                "score_delta_30d": score_delta_30d,
            },
        }
        row["dynamics_classification"] = self.classify_dynamics(row)
        return row

    def build_dynamics(self, current_date: str, current: List[Dict[str, Any]], historical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped_history = self.history_by_corridor(historical, current_date)
        rows = []
        for corridor in current:
            h = corridor.get("corridor_hash")
            if not h:
                continue
            row = self.build_dynamics_row(corridor, grouped_history.get(h, []), current_date)
            if row.get("corridor_hash") and row.get("corridor_key") and row.get("source_node_key") and row.get("target_node_key"):
                rows.append(row)
        self.stats["dynamics_generated"] = len(rows)
        self.stats["transition_flags_detected"] = sum(1 for r in rows if r.get("regime_transition_flag"))
        self.stats["decaying_corridors_detected"] = sum(1 for r in rows if r.get("activation_state") == "decaying")
        self.stats["reactivating_corridors_detected"] = sum(1 for r in rows if r.get("activation_state") == "reactivating")
        return sorted(rows, key=lambda r: r["stress_accumulation_score"], reverse=True)

    def classify_regime_summary(self, rows: List[Dict[str, Any]]) -> str:
        if not rows:
            return "empty_regime"
        avg_stress = safe_avg([r.get("stress_accumulation_score") for r in rows]) or 0.0
        avg_drift = safe_avg([r.get("corridor_drift_score") for r in rows]) or 0.0
        transition_ratio = sum(1 for r in rows if r.get("regime_transition_flag")) / max(1, len(rows))
        decaying_ratio = sum(1 for r in rows if r.get("activation_state") == "decaying") / max(1, len(rows))
        if avg_stress >= 0.60 and transition_ratio >= 0.25:
            return "regime_transition_pressure"
        if avg_drift >= 0.45:
            return "regime_corridor_drift"
        if decaying_ratio >= 0.35:
            return "regime_corridor_degradation"
        if avg_stress >= 0.50:
            return "regime_stress_accumulation"
        return "regime_corridor_stable"

    def build_regime_summaries(self, dynamics_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for row in dynamics_rows:
            grouped[row.get("regime_sensitivity") or "unknown"].append(row)

        summaries: List[Dict[str, Any]] = []
        for regime, rows in sorted(grouped.items()):
            states = [r.get("activation_state") for r in rows]
            summary = {
                "run_id": self.run_id,
                "run_date_sgt": self.run_date_sgt,
                "regime_sensitivity": regime,
                "corridor_count": len(rows),
                "dominant_corridor_count": sum(1 for r in rows if r.get("dominant_pathway_flag")),
                "transition_flag_count": sum(1 for r in rows if r.get("regime_transition_flag")),
                "active_corridor_count": sum(1 for s in states if s in ("active", "stable_active", "accelerating")),
                "emerging_corridor_count": sum(1 for s in states if s == "emerging"),
                "decaying_corridor_count": sum(1 for s in states if s == "decaying"),
                "dormant_corridor_count": sum(1 for s in states if s == "dormant"),
                "reactivating_corridor_count": sum(1 for s in states if s == "reactivating"),
                "avg_corridor_intelligence_score": clamp(safe_avg([r.get("current_corridor_intelligence_score") for r in rows]) or 0.0),
                "avg_score_delta_previous": safe_avg([r.get("score_delta_previous") for r in rows]),
                "avg_corridor_drift_score": clamp(safe_avg([r.get("corridor_drift_score") for r in rows]) or 0.0),
                "avg_stress_accumulation_score": clamp(safe_avg([r.get("stress_accumulation_score") for r in rows]) or 0.0),
                "avg_survivability_score": clamp(safe_avg([r.get("corridor_survivability_score") for r in rows]) or 0.0),
                "max_stress_accumulation_score": clamp(max([safe_float(r.get("stress_accumulation_score")) or 0.0 for r in rows] or [0.0])),
                "regime_dynamics_classification": self.classify_regime_summary(rows),
                "metadata": {
                    "engine_version": "phase5c_v1",
                    "top_corridors_by_stress": [r.get("corridor_hash") for r in sorted(rows, key=lambda x: x.get("stress_accumulation_score") or 0, reverse=True)[:5]],
                    "created_at_utc": now_iso(),
                },
            }
            summaries.append(summary)
        return summaries

    def add_validation(self, name: str, passed: bool, observed: Optional[float], threshold: Optional[float], message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.validation_rows.append(
            {
                "run_id": self.run_id,
                "run_date_sgt": self.run_date_sgt,
                "validation_name": name,
                "validation_status": "PASS" if passed else "FAIL",
                "observed_value": observed,
                "threshold_value": threshold,
                "message": message,
                "details": details or {},
            }
        )

    def validate(self, current: List[Dict[str, Any]], historical: List[Dict[str, Any]], dynamics_rows: List[Dict[str, Any]], summaries: List[Dict[str, Any]]) -> int:
        self.add_validation(
            "phase5b_corridors_available",
            len(current) > 0,
            len(current),
            1,
            "Current Phase 5B corridors are available" if current else "No current Phase 5B corridors found",
        )
        self.add_validation(
            "historical_context_available",
            len(historical) >= len(current),
            len(historical),
            len(current),
            "Historical corridor context loaded" if len(historical) >= len(current) else "Historical context is thinner than current corridor set",
        )
        self.add_validation(
            "dynamics_generated_for_current_corridors",
            len(dynamics_rows) == len(current),
            len(dynamics_rows),
            len(current),
            "Dynamics generated for every current corridor" if len(dynamics_rows) == len(current) else "Some current corridors did not produce dynamics rows",
        )
        invalid_scores = sum(
            1
            for r in dynamics_rows
            if not (0 <= float(r.get("current_corridor_intelligence_score") or 0) <= 1)
            or not (0 <= float(r.get("corridor_drift_score") or 0) <= 1)
            or not (0 <= float(r.get("stress_accumulation_score") or 0) <= 1)
            or not (0 <= float(r.get("corridor_survivability_score") or 0) <= 1)
        )
        self.add_validation(
            "score_range_check",
            invalid_scores == 0,
            invalid_scores,
            0,
            "All dynamics scores are within [0,1]" if invalid_scores == 0 else "Some dynamics scores are outside [0,1]",
        )
        self.add_validation(
            "regime_summaries_generated",
            len(summaries) > 0 if dynamics_rows else True,
            len(summaries),
            1 if dynamics_rows else 0,
            "Regime summaries generated" if summaries or not dynamics_rows else "No regime summaries generated",
        )
        failures = sum(1 for r in self.validation_rows if r["validation_status"] != "PASS")
        self.stats["validation_failures"] = failures
        return failures

    def write_telemetry(self, status: str, error_message: Optional[str] = None) -> None:
        runtime = round(time.time() - self.started, 3)
        row = {
            "run_id": self.run_id,
            "run_date_sgt": self.run_date_sgt,
            "pipeline_name": PIPELINE_NAME,
            "status": status,
            "current_corridors_loaded": self.stats.get("current_corridors_loaded", 0),
            "historical_corridors_loaded": self.stats.get("historical_corridors_loaded", 0),
            "dynamics_generated": self.stats.get("dynamics_generated", 0),
            "dynamics_persisted": self.stats.get("dynamics_persisted", 0),
            "regime_summaries_persisted": self.stats.get("regime_summaries_persisted", 0),
            "transition_flags_detected": self.stats.get("transition_flags_detected", 0),
            "decaying_corridors_detected": self.stats.get("decaying_corridors_detected", 0),
            "reactivating_corridors_detected": self.stats.get("reactivating_corridors_detected", 0),
            "validation_failures": self.stats.get("validation_failures", 0),
            "runtime_seconds": runtime,
            "error_message": error_message,
            "details": dict(self.stats),
        }
        self.db.upsert("structural_theme_graph_corridor_dynamics_telemetry", [row], "run_id")

    def run(self) -> Dict[str, Any]:
        try:
            current_date, current, historical = self.fetch_corridors()
            self.run_date_sgt = current_date or self.run_date_sgt
            dynamics_rows = self.build_dynamics(current_date, current, historical)
            summaries = self.build_regime_summaries(dynamics_rows)
            failures = self.validate(current, historical, dynamics_rows, summaries)

            if self.validation_rows:
                self.db.upsert("structural_theme_graph_corridor_dynamics_validation", self.validation_rows, "run_id,validation_name")
            if dynamics_rows:
                self.stats["dynamics_persisted"] = self.db.upsert("structural_theme_graph_corridor_dynamics", dynamics_rows, "run_date_sgt,corridor_hash")
            if summaries:
                self.stats["regime_summaries_persisted"] = self.db.upsert("structural_theme_graph_regime_corridor_dynamics_summary", summaries, "run_date_sgt,regime_sensitivity")

            status = "SUCCESS" if failures == 0 else "SUCCESS_WITH_VALIDATION_WARNINGS"
            self.write_telemetry(status)
            return {
                "status": status,
                "run_id": self.run_id,
                "run_date_sgt": self.run_date_sgt,
                "current_corridors_loaded": self.stats.get("current_corridors_loaded", 0),
                "historical_corridors_loaded": self.stats.get("historical_corridors_loaded", 0),
                "dynamics_generated": self.stats.get("dynamics_generated", 0),
                "dynamics_persisted": self.stats.get("dynamics_persisted", 0),
                "regime_summaries_persisted": self.stats.get("regime_summaries_persisted", 0),
                "transition_flags_detected": self.stats.get("transition_flags_detected", 0),
                "decaying_corridors_detected": self.stats.get("decaying_corridors_detected", 0),
                "reactivating_corridors_detected": self.stats.get("reactivating_corridors_detected", 0),
                "validation_failures": failures,
            }
        except Exception as exc:
            self.stats["validation_failures"] = max(1, self.stats.get("validation_failures", 0))
            try:
                self.write_telemetry("FAILED", str(exc))
            except Exception:
                pass
            raise


def main() -> None:
    db = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or "")
    engine = RegimeCorridorDynamicsEngine(db)
    result = engine.run()
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
