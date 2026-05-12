#!/usr/bin/env python3
"""
Phase 2D.2 — Historical Reconstruction Engine

PASS 2 UPDATED:
- Migrated source loading from monolithic client.get(... limit=50000)
  to paginated streaming retrieval.
- Uses utils/paginated_rest_loader.py from Pass 1.
- Uses utils/streaming_observation_loader.py for source-aware normalization.
- Preserves output tables, checkpoint style, telemetry style and validation
  compatibility.

Schema-aligned target tables:
    1. structural_theme_momentum_history
    2. structural_theme_regime_history
    3. structural_theme_propagation_history
    4. structural_theme_evidence_intensity_history

Design:
    - Python only
    - Supabase REST API only
    - No Supabase Python SDK
    - Additive-only
    - Idempotent upserts
    - Restart-safe checkpointing
    - Chunked historical reconstruction
    - Page-safe source loading
    - GitHub Actions compatible
"""

from __future__ import annotations

import json
import math
import os
import sys
import time
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests


# ============================================================
# IMPORT PATH SETUP
# ============================================================

THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parents[2] if len(THIS_FILE.parents) >= 3 else Path.cwd()

for candidate in (REPO_ROOT, REPO_ROOT / "utils", Path.cwd()):
    if str(candidate) not in sys.path:
        sys.path.append(str(candidate))

from utils.paginated_rest_loader import (  # noqa: E402
    PaginationConfig,
    SupabaseRangeRestClient,
)
from utils.streaming_observation_loader import (  # noqa: E402
    CANDIDATE_SOURCE_TABLES,
    HistoricalObservation,
    SourceTableConfig,
    StreamingObservationLoader,
)


# ============================================================
# CONFIG
# ============================================================

PIPELINE_NAME = "AI_TRANSMISSION_PHASE_2D2_HISTORICAL_RECONSTRUCTION"

THEME_NAME = os.getenv("THEME_NAME", "ai")
LOOKBACK_DAYS = int(os.getenv("RECONSTRUCTION_LOOKBACK_DAYS", "365"))
CHUNK_DAYS = int(os.getenv("RECONSTRUCTION_CHUNK_DAYS", "30"))
ROLLING_WINDOW = int(os.getenv("RECONSTRUCTION_ROLLING_WINDOW", "30"))
BATCH_SIZE = int(os.getenv("RECONSTRUCTION_BATCH_SIZE", "500"))
SLEEP_SECONDS = float(os.getenv("RECONSTRUCTION_SLEEP_SECONDS", "0.15"))

# Keep enough prior history for 30d momentum + acceleration.
RECONSTRUCTION_HISTORY_BUFFER_DAYS = int(
    os.getenv("RECONSTRUCTION_HISTORY_BUFFER_DAYS", str(ROLLING_WINDOW + 35))
)

SGT = timezone(timedelta(hours=8))


# ============================================================
# BASIC HELPERS
# ============================================================

def now_sgt() -> datetime:
    return datetime.now(SGT)


def today_sgt() -> date:
    return now_sgt().date()


def parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    text = str(value).strip()
    if not text:
        return None

    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except Exception:
        pass

    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except Exception:
        return None


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
    return max(low, min(high, value))


def date_chunks(start_date: date, end_date: date, chunk_days: int) -> List[Tuple[date, date]]:
    chunks: List[Tuple[date, date]] = []
    cursor = start_date

    while cursor <= end_date:
        chunk_end = min(cursor + timedelta(days=chunk_days - 1), end_date)
        chunks.append((cursor, chunk_end))
        cursor = chunk_end + timedelta(days=1)

    return chunks


def regime_from_score(score: float) -> str:
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
    if score >= 75:
        return "high_evidence_intensity"
    if score >= 50:
        return "moderate_evidence_intensity"
    if score >= 25:
        return "low_evidence_intensity"
    return "minimal_evidence_intensity"


# ============================================================
# SUPABASE REST CLIENT FOR WRITES / SMALL METADATA READS
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
        }

    def get(
        self,
        table: str,
        params: Optional[Dict[str, str]] = None,
        *,
        timeout: int = 60,
    ) -> List[Dict[str, Any]]:
        response = requests.get(
            f"{self.base}/{table}",
            headers=self.headers,
            params=params or {},
            timeout=timeout,
        )

        if response.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Supabase GET failed for {table}: "
                f"{response.status_code} - {response.text[:2000]}"
            )

        if response.status_code == 204 or not response.text:
            return []

        payload = response.json()
        return payload if isinstance(payload, list) else []

    def post_insert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        *,
        batch_size: int = BATCH_SIZE,
    ) -> int:
        if not rows:
            return 0

        total = 0
        headers = dict(self.headers)
        headers["Prefer"] = "return=minimal"

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            response = requests.post(
                f"{self.base}/{table}",
                headers=headers,
                json=batch,
                timeout=90,
            )

            if response.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"Supabase INSERT failed for {table}: "
                    f"{response.status_code} - {response.text[:3000]}"
                )

            total += len(batch)
            time.sleep(SLEEP_SECONDS)

        return total

    def table_exists(self, table: str) -> bool:
        try:
            self.get(table, {"select": "*", "limit": "1"})
            return True
        except Exception:
            return False

    def upsert(
        self,
        table: str,
        rows: List[Dict[str, Any]],
        *,
        conflict_columns: List[str],
        batch_size: int = BATCH_SIZE,
    ) -> int:
        if not rows:
            return 0

        conflict_key = ",".join(conflict_columns)
        total = 0

        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=minimal"

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i + batch_size]

            response = requests.post(
                f"{self.base}/{table}?on_conflict={conflict_key}",
                headers=headers,
                json=batch,
                timeout=90,
            )

            if response.status_code not in (200, 201, 204):
                raise RuntimeError(
                    f"Supabase UPSERT failed for {table}: "
                    f"{response.status_code} - {response.text[:3000]}"
                )

            total += len(batch)
            time.sleep(SLEEP_SECONDS)

        return total


# ============================================================
# SOURCE TABLE DETECTION
# ============================================================

def detect_source_tables(client: SupabaseRestClient) -> List[SourceTableConfig]:
    available: List[SourceTableConfig] = []

    for cfg in CANDIDATE_SOURCE_TABLES:
        if client.table_exists(cfg.table):
            available.append(cfg)

    if not available:
        raise RuntimeError("No compatible historical source tables detected.")

    return available


# ============================================================
# RECONSTRUCTION ENGINE
# ============================================================

class HistoricalReconstructionEngine:
    def __init__(
        self,
        client: SupabaseRestClient,
        *,
        theme_name: str,
        rolling_window: int,
    ) -> None:
        self.client = client
        self.theme_name = theme_name
        self.rolling_window = rolling_window

    def _score_on_date(self, grouped: Dict[date, List[HistoricalObservation]], dates: List[date], idx: int) -> float:
        idx = max(0, min(idx, len(dates) - 1))
        return mean([x.score for x in grouped[dates[idx]]])

    def reconstruct_momentum(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            current_score = self._score_on_date(grouped, dates, idx)

            score_1d_ago = self._score_on_date(grouped, dates, idx - 1)
            score_7d_ago = self._score_on_date(grouped, dates, idx - 7)
            score_8d_ago = self._score_on_date(grouped, dates, idx - 8)
            score_30d_ago = self._score_on_date(grouped, dates, idx - 30)
            score_31d_ago = self._score_on_date(grouped, dates, idx - 31)

            momentum_7d = current_score - score_7d_ago
            momentum_30d = current_score - score_30d_ago

            previous_momentum_7d = score_1d_ago - score_8d_ago
            previous_momentum_30d = score_1d_ago - score_31d_ago

            acceleration_7d = momentum_7d - previous_momentum_7d
            acceleration_30d = momentum_30d - previous_momentum_30d

            persistence_days = 0
            for j in range(idx, 0, -1):
                today_score = self._score_on_date(grouped, dates, j)
                yesterday_score = self._score_on_date(grouped, dates, j - 1)

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

            if structural_momentum_score >= 70:
                momentum_regime = "positive_momentum"
            elif structural_momentum_score >= 55:
                momentum_regime = "constructive_momentum"
            elif structural_momentum_score >= 45:
                momentum_regime = "neutral_momentum"
            elif structural_momentum_score >= 30:
                momentum_regime = "weakening_momentum"
            else:
                momentum_regime = "negative_momentum"

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "entity": "theme",
                "theme_score": round(current_score, 4),
                "momentum_7d": round(momentum_7d, 4),
                "momentum_30d": round(momentum_30d, 4),
                "acceleration_7d": round(acceleration_7d, 4),
                "acceleration_30d": round(acceleration_30d, 4),
                "momentum_persistence_days": int(persistence_days),
                "structural_momentum_score": round(structural_momentum_score, 4),
                "momentum_regime": momentum_regime,
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

        return rows

    def reconstruct_regime(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        previous_regime: Optional[str] = None
        current_duration = 0

        for idx, run_date in enumerate(dates):
            current_score = self._score_on_date(grouped, dates, idx)
            current_regime = regime_from_score(current_score)

            changed = bool(previous_regime is not None and previous_regime != current_regime)

            if previous_regime is None or changed:
                current_duration = 1
            else:
                current_duration += 1

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "entity": "theme",
                "previous_regime": previous_regime,
                "current_regime": current_regime,
                "regime_changed": changed,
                "regime_duration_days": int(current_duration),
                "transition_type": transition_type(previous_regime, current_regime),
                "created_at": now_sgt().isoformat(),
            })

            previous_regime = current_regime

        return rows

    def reconstruct_propagation(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            observations = grouped[run_date]
            pathway_groups: Dict[Tuple[str, str, str], List[HistoricalObservation]] = {}

            for obs in observations:
                source_entity = "theme"
                target_entity = obs.entity or "theme"
                pathway_name = obs.pathway_name or "theme_pathway"
                key = (source_entity, target_entity, pathway_name)
                pathway_groups.setdefault(key, []).append(obs)

            for (source_entity, target_entity, pathway_name), obs_list in pathway_groups.items():
                current_score = mean([x.score for x in obs_list])

                previous_score = current_score
                if idx > 0:
                    prev_obs = [
                        x for x in grouped[dates[idx - 1]]
                        if (x.entity or "theme") == target_entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if prev_obs:
                        previous_score = mean([x.score for x in prev_obs])

                score_change = current_score - previous_score

                score_7d_ago = current_score
                score_30d_ago = current_score
                score_8d_ago = previous_score
                score_31d_ago = previous_score

                if idx >= 7:
                    d7_obs = [
                        x for x in grouped[dates[idx - 7]]
                        if (x.entity or "theme") == target_entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if d7_obs:
                        score_7d_ago = mean([x.score for x in d7_obs])

                if idx >= 30:
                    d30_obs = [
                        x for x in grouped[dates[idx - 30]]
                        if (x.entity or "theme") == target_entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if d30_obs:
                        score_30d_ago = mean([x.score for x in d30_obs])

                if idx >= 8:
                    d8_obs = [
                        x for x in grouped[dates[idx - 8]]
                        if (x.entity or "theme") == target_entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if d8_obs:
                        score_8d_ago = mean([x.score for x in d8_obs])

                if idx >= 31:
                    d31_obs = [
                        x for x in grouped[dates[idx - 31]]
                        if (x.entity or "theme") == target_entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if d31_obs:
                        score_31d_ago = mean([x.score for x in d31_obs])

                momentum_7d = current_score - score_7d_ago
                momentum_30d = current_score - score_30d_ago
                prev_momentum_7d = previous_score - score_8d_ago
                prev_momentum_30d = previous_score - score_31d_ago
                acceleration_7d = momentum_7d - prev_momentum_7d
                acceleration_30d = momentum_30d - prev_momentum_30d

                evidence_intensity = mean([x.evidence_strength for x in obs_list])
                attribution_strength = mean([x.attribution_strength for x in obs_list])

                pathway_window_scores: List[float] = []
                window_start = max(0, idx - self.rolling_window + 1)

                for j in range(window_start, idx + 1):
                    historical_obs = [
                        x for x in grouped[dates[j]]
                        if (x.entity or "theme") == target_entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if historical_obs:
                        pathway_window_scores.append(mean([x.score for x in historical_obs]))

                pathway_stability_score = clamp(100 - stddev(pathway_window_scores))

                rows.append({
                    "run_date_sgt": run_date.isoformat(),
                    "theme_name": self.theme_name,
                    "source_entity": source_entity,
                    "target_entity": target_entity,
                    "pathway_name": pathway_name,
                    "propagation_score": round(current_score, 4),
                    "previous_score": round(previous_score, 4),
                    "score_change": round(score_change, 4),
                    "momentum_7d": round(momentum_7d, 4),
                    "momentum_30d": round(momentum_30d, 4),
                    "acceleration_7d": round(acceleration_7d, 4),
                    "acceleration_30d": round(acceleration_30d, 4),
                    "evidence_intensity": round(evidence_intensity, 4),
                    "attribution_strength": round(attribution_strength, 4),
                    "pathway_stability_score": round(pathway_stability_score, 4),
                    "regime": regime_from_score(current_score),
                    "created_at": now_sgt().isoformat(),
                })

        return rows

    def reconstruct_evidence(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            evidence_groups: Dict[Tuple[str, str], List[HistoricalObservation]] = {}

            for obs in grouped[run_date]:
                entity = obs.entity or "theme"
                pathway_name = obs.pathway_name or "theme_pathway"
                evidence_groups.setdefault((entity, pathway_name), []).append(obs)

            for (entity, pathway_name), obs_list in evidence_groups.items():
                evidence_count = sum([x.evidence_count for x in obs_list])
                avg_strength = mean([x.evidence_strength for x in obs_list])

                rolling_7_values: List[float] = []
                rolling_30_values: List[float] = []

                for j in range(max(0, idx - 6), idx + 1):
                    day_obs = [
                        x for x in grouped[dates[j]]
                        if (x.entity or "theme") == entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if day_obs:
                        rolling_7_values.append(mean([x.evidence_strength for x in day_obs]))

                for j in range(max(0, idx - 29), idx + 1):
                    day_obs = [
                        x for x in grouped[dates[j]]
                        if (x.entity or "theme") == entity
                        and (x.pathway_name or "theme_pathway") == pathway_name
                    ]
                    if day_obs:
                        rolling_30_values.append(mean([x.evidence_strength for x in day_obs]))

                rolling_7 = mean(rolling_7_values)
                rolling_30 = mean(rolling_30_values)

                spike_score = 0.0
                if len(rolling_30_values) >= 3:
                    baseline = mean(rolling_30_values[:-1])
                    baseline_std = stddev(rolling_30_values[:-1])
                    if baseline_std > 0:
                        spike_score = clamp(50 + ((avg_strength - baseline) / baseline_std) * 10)
                    else:
                        spike_score = clamp(50 + avg_strength - baseline)

                high_conf_count = sum(
                    1 for x in obs_list
                    if x.evidence_strength >= 70 or x.score >= 70
                )

                rows.append({
                    "run_date_sgt": run_date.isoformat(),
                    "theme_name": self.theme_name,
                    "entity": entity,
                    "pathway_name": pathway_name,
                    "evidence_count": int(evidence_count),
                    "high_confidence_evidence_count": int(high_conf_count),
                    "avg_evidence_strength": round(avg_strength, 4),
                    "rolling_evidence_7d": round(rolling_7, 4),
                    "rolling_evidence_30d": round(rolling_30, 4),
                    "evidence_spike_score": round(spike_score, 4),
                    "evidence_regime": evidence_regime_from_score(avg_strength),
                    "created_at": now_sgt().isoformat(),
                })

        return rows


# ============================================================
# CHECKPOINTING
# ============================================================

def load_checkpoint(client: SupabaseRestClient, theme_name: str) -> Optional[date]:
    table = "structural_theme_reconstruction_checkpoints"

    if not client.table_exists(table):
        print("Checkpoint table not found. Continuing without checkpoint resume.")
        return None

    rows = client.get(
        table,
        {
            "select": "*",
            "pipeline_name": f"eq.{PIPELINE_NAME}",
            "theme_name": f"eq.{theme_name}",
            "order": "last_completed_date.desc",
            "limit": "1",
        },
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
    table = "structural_theme_reconstruction_checkpoints"

    if not client.table_exists(table):
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
        table,
        [row],
        conflict_columns=["pipeline_name", "theme_name"],
    )


# ============================================================
# TELEMETRY
# ============================================================

def compact_error_payload(base_message: Optional[str], payload: Optional[Dict[str, Any]] = None) -> Optional[str]:
    if not base_message and not payload:
        return None

    data = {
        "message": base_message,
        "payload": payload or {},
    }

    text = json.dumps(data, default=str)
    return text[:1000]


def write_telemetry(
    client: SupabaseRestClient,
    *,
    status: str,
    runtime_seconds: float,
    rows_written: int,
    error_message: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> None:
    table = "production_pipeline_runs"

    if not client.table_exists(table):
        print("Telemetry table production_pipeline_runs not found. Skipping telemetry.")
        return

    row = {
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
        "error_message": compact_error_payload(error_message, extra_payload),
    }

    try:
        client.post_insert(table, [row])
    except Exception as exc:
        print(f"Telemetry insert skipped: {exc}")


# ============================================================
# SAFE TARGET WRITES
# ============================================================

def safe_upsert_target(
    client: SupabaseRestClient,
    *,
    table: str,
    rows: List[Dict[str, Any]],
    conflict_columns: List[str],
    critical: bool = True,
) -> int:
    if not rows:
        return 0

    if not client.table_exists(table):
        msg = f"Target table does not exist: {table}"
        if critical:
            raise RuntimeError(msg)
        print(f"WARNING: {msg}. Skipping.")
        return 0

    try:
        written = client.upsert(
            table,
            rows,
            conflict_columns=conflict_columns,
            batch_size=BATCH_SIZE,
        )
        print(f"Upserted {written} rows into {table}")
        return written

    except Exception as exc:
        msg = f"Failed to upsert {table}: {exc}"
        if critical:
            raise RuntimeError(msg)

        print(f"WARNING: {msg}")
        return 0


# ============================================================
# MAIN ORCHESTRATION
# ============================================================

def run_reconstruction() -> None:
    start_ts = time.time()
    client = SupabaseRestClient()

    end_date = today_sgt()
    original_start_date = end_date - timedelta(days=LOOKBACK_DAYS)
    start_date = original_start_date

    checkpoint_date = load_checkpoint(client, THEME_NAME)
    if checkpoint_date and checkpoint_date >= start_date:
        start_date = checkpoint_date + timedelta(days=1)

    if start_date > end_date:
        print("No reconstruction required. Checkpoint is already current.")
        write_telemetry(
            client,
            status="SUCCESS_NOOP",
            runtime_seconds=time.time() - start_ts,
            rows_written=0,
        )
        return

    source_tables = detect_source_tables(client)

    print("Detected source tables:")
    for cfg in source_tables:
        print(f" - {cfg.table}")

    engine = HistoricalReconstructionEngine(
        client,
        theme_name=THEME_NAME,
        rolling_window=ROLLING_WINDOW,
    )

    streaming_loader = StreamingObservationLoader(
        rest_client=SupabaseRangeRestClient(),
        pagination_config=PaginationConfig(),
    )

    total_rows_written = 0
    windows_processed = 0
    total_pages_loaded = 0
    total_rows_loaded = 0
    total_retry_count = 0
    total_pagination_runtime = 0.0
    total_normalization_runtime = 0.0
    max_page_size = 0
    chunk_telemetry_records: List[Dict[str, Any]] = []

    try:
        for chunk_start, chunk_end in date_chunks(start_date, end_date, CHUNK_DAYS):
            chunk_ts = time.time()
            print(f"\nProcessing chunk: {chunk_start} to {chunk_end}")

            fetch_start = max(
                original_start_date,
                chunk_start - timedelta(days=RECONSTRUCTION_HISTORY_BUFFER_DAYS),
            )

            grouped_all, chunk_telemetry = streaming_loader.load_grouped_observations_for_window(
                source_tables,
                fetch_start=fetch_start,
                fetch_end=chunk_end,
                theme_name=THEME_NAME,
            )

            total_pages_loaded += chunk_telemetry.pages_loaded
            total_rows_loaded += chunk_telemetry.rows_loaded
            total_retry_count += chunk_telemetry.retry_count
            total_pagination_runtime += chunk_telemetry.pagination_runtime
            total_normalization_runtime += chunk_telemetry.normalization_runtime
            max_page_size = max(max_page_size, chunk_telemetry.max_page_size)

            if not grouped_all:
                print("  No observations found. Skipping chunk.")
                write_checkpoint(
                    client,
                    theme_name=THEME_NAME,
                    completed_date=chunk_end,
                    status="SKIPPED_NO_DATA",
                    details={
                        "chunk_start": chunk_start.isoformat(),
                        "chunk_end": chunk_end.isoformat(),
                        "fetch_start": fetch_start.isoformat(),
                        "pagination": chunk_telemetry.to_dict(),
                    },
                )
                continue

            grouped_chunk = {
                d: v
                for d, v in grouped_all.items()
                if chunk_start <= d <= chunk_end
            }

            if not grouped_chunk:
                print("  No grouped observations inside chunk write window.")
                write_checkpoint(
                    client,
                    theme_name=THEME_NAME,
                    completed_date=chunk_end,
                    status="SKIPPED_NO_CHUNK_DATES",
                    details={
                        "chunk_start": chunk_start.isoformat(),
                        "chunk_end": chunk_end.isoformat(),
                        "fetch_start": fetch_start.isoformat(),
                        "pagination": chunk_telemetry.to_dict(),
                    },
                )
                continue

            momentum_rows = engine.reconstruct_momentum(grouped_chunk)
            regime_rows = engine.reconstruct_regime(grouped_chunk)
            propagation_rows = engine.reconstruct_propagation(grouped_chunk)
            evidence_rows = engine.reconstruct_evidence(grouped_chunk)

            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_momentum_history",
                rows=momentum_rows,
                conflict_columns=["run_date_sgt", "theme_name", "entity"],
                critical=True,
            )

            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_regime_history",
                rows=regime_rows,
                conflict_columns=["run_date_sgt", "theme_name", "entity"],
                critical=True,
            )

            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_propagation_history",
                rows=propagation_rows,
                conflict_columns=[
                    "run_date_sgt",
                    "theme_name",
                    "source_entity",
                    "target_entity",
                    "pathway_name",
                ],
                critical=True,
            )

            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_evidence_intensity_history",
                rows=evidence_rows,
                conflict_columns=[
                    "run_date_sgt",
                    "theme_name",
                    "entity",
                    "pathway_name",
                ],
                critical=True,
            )

            windows_processed += 1
            chunk_runtime = time.time() - chunk_ts

            chunk_record = chunk_telemetry.to_dict()
            chunk_record.update({
                "chunk_runtime": round(chunk_runtime, 4),
                "windows_processed": windows_processed,
                "grouped_dates_loaded": len(grouped_all),
                "grouped_chunk_dates": len(grouped_chunk),
                "rows_written_so_far": total_rows_written,
            })
            chunk_telemetry_records.append(chunk_record)

            write_checkpoint(
                client,
                theme_name=THEME_NAME,
                completed_date=chunk_end,
                status="SUCCESS",
                details={
                    "chunk_start": chunk_start.isoformat(),
                    "chunk_end": chunk_end.isoformat(),
                    "fetch_start": fetch_start.isoformat(),
                    "rows_written_so_far": total_rows_written,
                    "windows_processed": windows_processed,
                    "grouped_dates_loaded": len(grouped_all),
                    "grouped_chunk_dates": len(grouped_chunk),
                    "pagination": chunk_record,
                },
            )

            print(
                f"  Chunk completed: runtime={round(chunk_runtime, 2)}s, "
                f"pages={chunk_telemetry.pages_loaded}, "
                f"source_rows={chunk_telemetry.rows_loaded}, "
                f"observations={chunk_telemetry.observations_emitted}",
                flush=True,
            )

        runtime = time.time() - start_ts

        aggregate_payload = {
            "pages_loaded": total_pages_loaded,
            "rows_loaded": total_rows_loaded,
            "rows_per_second": round(total_rows_loaded / total_pagination_runtime, 4)
            if total_pagination_runtime > 0 else 0.0,
            "retry_count": total_retry_count,
            "windows_processed": windows_processed,
            "max_page_size": max_page_size,
            "pagination_runtime": round(total_pagination_runtime, 4),
            "normalization_runtime": round(total_normalization_runtime, 4),
            "chunk_count": len(chunk_telemetry_records),
        }

        write_telemetry(
            client,
            status="SUCCESS",
            runtime_seconds=runtime,
            rows_written=total_rows_written,
            extra_payload=aggregate_payload,
        )

        print("\nPhase 2D.2 historical reconstruction completed successfully.")
        print(f"Total rows written: {total_rows_written}")
        print(f"Runtime seconds: {round(runtime, 2)}")
        print("Pagination telemetry:")
        print(json.dumps(aggregate_payload, indent=2, default=str))

    except Exception as exc:
        runtime = time.time() - start_ts
        error_message = f"{type(exc).__name__}: {exc}"

        print("\nPhase 2D.2 reconstruction failed.")
        print(error_message)
        traceback.print_exc()

        try:
            write_telemetry(
                client,
                status="FAILED",
                runtime_seconds=runtime,
                rows_written=total_rows_written,
                error_message=error_message,
                extra_payload={
                    "pages_loaded": total_pages_loaded,
                    "rows_loaded": total_rows_loaded,
                    "retry_count": total_retry_count,
                    "windows_processed": windows_processed,
                    "max_page_size": max_page_size,
                    "pagination_runtime": round(total_pagination_runtime, 4),
                    "normalization_runtime": round(total_normalization_runtime, 4),
                },
            )
        except Exception:
            pass

        raise


if __name__ == "__main__":
    run_reconstruction()
