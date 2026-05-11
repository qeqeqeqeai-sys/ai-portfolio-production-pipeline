"""
Phase 2D.2 — Historical Reconstruction Engine

Corrected version:
- Python only
- Supabase REST API only
- No supabase-py
- Additive and idempotent
- Restart-safe checkpointing
- Corrected structural_theme_momentum_history schema compatibility

Important correction:
    structural_theme_momentum_history uses:
        run_date_sgt, theme_name, entity,
        theme_score,
        momentum_7d, momentum_30d,
        acceleration_7d, acceleration_30d,
        momentum_persistence_days,
        structural_momentum_score,
        momentum_regime,
        created_at, updated_at

    unique key:
        (run_date_sgt, theme_name, entity)
"""

from __future__ import annotations

import os
import sys
import math
import time
import json
import traceback
from dataclasses import dataclass
from datetime import datetime, date, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests


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


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def mean(values: List[float]) -> float:
    clean = [safe_float(v) for v in values if v is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def stddev(values: List[float]) -> float:
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

        return response.json()

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
        driver_cols=["top_positive_drivers", "top_negative_drivers", "driver"],
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
        driver_cols=["top_positive_drivers", "top_negative_drivers", "driver"],
        pathway_cols=["pathway", "transmission_pathway"],
        attribution_cols=["component_scores", "contribution_weights"],
        evidence_cols=["evidence_count", "evidence_coverage_score"],
    ),
    SourceTableConfig(
        table="structural_theme_explainability_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["transmission_score", "composite_score", "theme_score", "score"],
        driver_cols=["top_positive_drivers", "top_negative_drivers", "driver"],
        pathway_cols=["pathway", "transmission_pathway"],
        attribution_cols=["component_scores", "component_score", "contribution_weights", "contribution_weight"],
        evidence_cols=["evidence_count", "evidence_coverage_score"],
    ),
    SourceTableConfig(
        table="structural_theme_attribution_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["component_score", "score"],
        driver_cols=["driver", "component_name"],
        pathway_cols=["pathway"],
        attribution_cols=["component_name", "component_score", "contribution_weight"],
        evidence_cols=["evidence_count"],
    ),
    SourceTableConfig(
        table="structural_theme_evidence_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["evidence_score", "evidence_coverage_score", "score"],
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
    available: List[SourceTableConfig] = []

    for cfg in CANDIDATE_SOURCE_TABLES:
        if client.table_exists(cfg.table):
            available.append(cfg)

    if not available:
        raise RuntimeError("No compatible historical source tables detected.")

    return available


# ============================================================
# OBSERVATION NORMALISATION
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


def first_present(row: Dict[str, Any], cols: List[str], default: Any = None) -> Any:
    for col in cols:
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
        first_present(row, cfg.driver_cols, "theme_driver"),
        "theme_driver",
    )

    pathway_key = safe_text(
        first_present(row, cfg.pathway_cols, "theme_pathway"),
        "theme_pathway",
    )

    attribution_payload: Dict[str, Any] = {}
    for col in cfg.attribution_cols:
        if col in row and row[col] is not None:
            attribution_payload[col] = row[col]

    evidence_intensity = safe_float(first_present(row, cfg.evidence_cols, 0.0), 0.0)

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


def fetch_source_rows(
    client: SupabaseRestClient,
    cfg: SourceTableConfig,
    *,
    start_date: date,
    end_date: date,
    theme_name: str,
) -> List[HistoricalObservation]:
    # Fetch by lower bound, then filter upper bound locally.
    # This avoids PostgREST duplicate-key dict issues for date gte/lte.
    params = {
        "select": "*",
        cfg.date_col: f"gte.{start_date.isoformat()}",
        "order": f"{cfg.date_col}.asc",
        "limit": "50000",
    }

    rows = client.get(cfg.table, params=params, timeout=90)

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

    def group_by_date(self, observations: List[HistoricalObservation]) -> Dict[date, List[HistoricalObservation]]:
        grouped: Dict[date, List[HistoricalObservation]] = {}

        for obs in observations:
            grouped.setdefault(obs.run_date, []).append(obs)

        return dict(sorted(grouped.items(), key=lambda item: item[0]))

    # ------------------------------------------------------------
    # Corrected for your existing schema:
    # public.structural_theme_momentum_history
    # ------------------------------------------------------------
    def reconstruct_momentum(
        self,
        grouped: Dict[date, List[HistoricalObservation]],
    ) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            current_obs = grouped[run_date]
            current_score = mean([x.score for x in current_obs])

            def score_n_days_ago(n: int) -> float:
                target_idx = max(0, idx - n)
                target_date = dates[target_idx]
                return mean([x.score for x in grouped[target_date]])

            score_1d_ago = score_n_days_ago(1)
            score_7d_ago = score_n_days_ago(7)
            score_8d_ago = score_n_days_ago(8)
            score_30d_ago = score_n_days_ago(30)
            score_31d_ago = score_n_days_ago(31)

            momentum_7d = current_score - score_7d_ago
            momentum_30d = current_score - score_30d_ago

            previous_momentum_7d = score_1d_ago - score_8d_ago
            previous_momentum_30d = score_1d_ago - score_31d_ago

            acceleration_7d = momentum_7d - previous_momentum_7d
            acceleration_30d = momentum_30d - previous_momentum_30d

            persistence_days = 0
            for j in range(idx, 0, -1):
                today_score = mean([x.score for x in grouped[dates[j]]])
                yesterday_score = mean([x.score for x in grouped[dates[j - 1]]])

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

    # ------------------------------------------------------------
    # Other reconstructors are schema-tolerant and write only if
    # matching target tables exist and accept the columns.
    # If your other Phase 2D tables have different schemas, the
    # engine skips those writes rather than failing the whole job.
    # ------------------------------------------------------------

    def reconstruct_regimes(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())
        previous_regime: Optional[str] = None

        for idx, run_date in enumerate(dates):
            scores = [x.score for x in grouped[run_date]]
            theme_score = mean(scores)

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_scores = [mean([x.score for x in grouped[d]]) for d in window_dates]

            volatility = stddev(window_scores)
            instability_score = clamp(volatility * 3)

            if instability_score >= 70:
                regime = "unstable"
            elif theme_score >= 75:
                regime = "expansion"
            elif theme_score >= 55:
                regime = "constructive"
            elif theme_score >= 40:
                regime = "neutral"
            elif theme_score >= 25:
                regime = "weakening"
            else:
                regime = "contraction"

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "entity": "theme",
                "theme_score": round(theme_score, 4),
                "regime": regime,
                "previous_regime": previous_regime,
                "regime_transition_flag": bool(previous_regime and previous_regime != regime),
                "regime_instability_score": round(instability_score, 4),
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

            previous_regime = regime

        return rows

    def reconstruct_propagation(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            scores = [x.score for x in grouped[run_date]]
            current_score = mean(scores)

            previous_score = current_score
            if idx > 0:
                previous_score = mean([x.score for x in grouped[dates[idx - 1]]])

            change = current_score - previous_score

            acceleration = 0.0
            if idx > 1:
                prev_prev_score = mean([x.score for x in grouped[dates[idx - 2]]])
                previous_change = previous_score - prev_prev_score
                acceleration = change - previous_change

            abs_scores = [abs(x) for x in scores]
            total_abs = sum(abs_scores)
            concentration = 0.0
            if total_abs > 0:
                shares = [x / total_abs for x in abs_scores]
                concentration = clamp(sum(s ** 2 for s in shares) * 100)

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_scores = [mean([x.score for x in grouped[d]]) for d in window_dates]
            instability = clamp(stddev(window_scores) * 3)

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "entity": "theme",
                "propagation_score": round(current_score, 4),
                "propagation_change": round(change, 4),
                "propagation_acceleration": round(acceleration, 4),
                "propagation_concentration_score": round(concentration, 4),
                "propagation_instability_score": round(instability, 4),
                "observation_count": len(scores),
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
            })

        return rows

    def reconstruct_evidence(self, grouped: Dict[date, List[HistoricalObservation]]) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        dates = list(grouped.keys())

        for idx, run_date in enumerate(dates):
            values = [x.evidence_intensity for x in grouped[run_date]]
            intensity = mean(values)

            window_dates = dates[max(0, idx - self.rolling_window + 1):idx + 1]
            window_values = [
                mean([x.evidence_intensity for x in grouped[d]])
                for d in window_dates
            ]

            spike_score = 0.0
            if len(window_values) >= 3:
                baseline = mean(window_values[:-1])
                baseline_std = stddev(window_values[:-1])
                if baseline_std > 0:
                    spike_score = clamp(50 + ((intensity - baseline) / baseline_std) * 10)
                else:
                    spike_score = clamp(50 + intensity - baseline)

            rows.append({
                "run_date_sgt": run_date.isoformat(),
                "theme_name": self.theme_name,
                "entity": "theme",
                "evidence_intensity_score": round(intensity, 4),
                "evidence_spike_score": round(spike_score, 4),
                "evidence_observation_count": len(values),
                "created_at": now_sgt().isoformat(),
                "updated_at": now_sgt().isoformat(),
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

def write_telemetry(
    client: SupabaseRestClient,
    *,
    status: str,
    runtime_seconds: float,
    rows_written: int,
    error_message: Optional[str] = None,
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
        "error_message": error_message[:1000] if error_message else None,
    }

    try:
        client.upsert(
            table,
            [row],
            conflict_columns=["pipeline_name", "run_date_sgt", "github_run_id"],
        )
    except Exception as exc:
        print(f"Telemetry write skipped due to schema/conflict mismatch: {exc}")


# ============================================================
# SAFE TARGET WRITES
# ============================================================

def safe_upsert_target(
    client: SupabaseRestClient,
    *,
    table: str,
    rows: List[Dict[str, Any]],
    conflict_columns: List[str],
    critical: bool = False,
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
        print("Skipping non-critical target table due to schema mismatch.")
        return 0


# ============================================================
# MAIN ORCHESTRATION
# ============================================================

def run_reconstruction() -> None:
    start_ts = time.time()
    client = SupabaseRestClient()

    end_date = today_sgt()
    start_date = end_date - timedelta(days=LOOKBACK_DAYS)

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

    total_rows_written = 0

    try:
        for chunk_start, chunk_end in date_chunks(start_date, end_date, CHUNK_DAYS):
            print(f"\nProcessing chunk: {chunk_start} to {chunk_end}")

            fetch_start = max(
                end_date - timedelta(days=LOOKBACK_DAYS),
                chunk_start - timedelta(days=ROLLING_WINDOW + 35),
            )

            observations: List[HistoricalObservation] = []

            for cfg in source_tables:
                try:
                    obs = fetch_source_rows(
                        client,
                        cfg,
                        start_date=fetch_start,
                        end_date=chunk_end,
                        theme_name=THEME_NAME,
                    )
                    observations.extend(obs)
                    print(f"  {cfg.table}: {len(obs)} observations")
                except Exception as exc:
                    print(f"  WARNING: failed to fetch {cfg.table}: {exc}")

            if not observations:
                print("  No observations found. Skipping chunk.")
                write_checkpoint(
                    client,
                    theme_name=THEME_NAME,
                    completed_date=chunk_end,
                    status="SKIPPED_NO_DATA",
                    details={
                        "chunk_start": chunk_start.isoformat(),
                        "chunk_end": chunk_end.isoformat(),
                    },
                )
                continue

            grouped_all = engine.group_by_date(observations)

            # Build reconstruction using buffered history, but only write current chunk dates.
            grouped_chunk = {
                d: v
                for d, v in grouped_all.items()
                if chunk_start <= d <= chunk_end
            }

            if not grouped_chunk:
                print("  No grouped observations inside chunk write window.")
                continue

            momentum_rows = engine.reconstruct_momentum(grouped_chunk)
            regime_rows = engine.reconstruct_regimes(grouped_chunk)
            propagation_rows = engine.reconstruct_propagation(grouped_chunk)
            evidence_rows = engine.reconstruct_evidence(grouped_chunk)

            # Critical table fixed to your exact schema.
            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_momentum_history",
                rows=momentum_rows,
                conflict_columns=["run_date_sgt", "theme_name", "entity"],
                critical=True,
            )

            # Non-critical tables may have schema variations from your existing Phase 2D files.
            # These writes will be attempted, but skipped safely if their schemas differ.
            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_regime_history",
                rows=regime_rows,
                conflict_columns=["run_date_sgt", "theme_name", "entity"],
                critical=False,
            )

            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_propagation_history",
                rows=propagation_rows,
                conflict_columns=["run_date_sgt", "theme_name", "entity"],
                critical=False,
            )

            total_rows_written += safe_upsert_target(
                client,
                table="structural_theme_evidence_intensity_history",
                rows=evidence_rows,
                conflict_columns=["run_date_sgt", "theme_name", "entity"],
                critical=False,
            )

            write_checkpoint(
                client,
                theme_name=THEME_NAME,
                completed_date=chunk_end,
                status="SUCCESS",
                details={
                    "chunk_start": chunk_start.isoformat(),
                    "chunk_end": chunk_end.isoformat(),
                    "rows_written_so_far": total_rows_written,
                    "observations": len(observations),
                },
            )

        runtime = time.time() - start_ts

        write_telemetry(
            client,
            status="SUCCESS",
            runtime_seconds=runtime,
            rows_written=total_rows_written,
        )

        print("\nPhase 2D.2 historical reconstruction completed successfully.")
        print(f"Total rows written: {total_rows_written}")
        print(f"Runtime seconds: {round(runtime, 2)}")

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
            )
        except Exception:
            pass

        raise


if __name__ == "__main__":
    run_reconstruction()
