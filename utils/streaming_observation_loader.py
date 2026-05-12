#!/usr/bin/env python3
"""
utils/streaming_observation_loader.py

PASS 2 — Streaming Observation Loader
====================================

Purpose:
- Convert paginated Supabase REST rows into normalized reconstruction observations.
- Avoid monolithic client.get(... limit=50000) retrievals.
- Avoid full source-table retrieval.
- Provide page-wise telemetry and chunk-safe source loading.
- Keep pagination utilities generic and theme-agnostic.

Hotfix:
- daily_signal_scores is intentionally disabled as an active source table because
  the live schema does not currently expose the assumed series_id column.
- This avoids non-critical enrichment-source errors during reconstruction.
"""

from __future__ import annotations

import math
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Generator, Iterable, List, Optional, Sequence, Tuple


THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1] if len(THIS_FILE.parents) > 1 else Path.cwd()

for candidate in (PROJECT_ROOT, PROJECT_ROOT / "utils", Path.cwd()):
    if str(candidate) not in sys.path:
        sys.path.append(str(candidate))

from utils.paginated_rest_loader import (  # noqa: E402
    PaginatedRestLoader,
    PaginationConfig,
    SupabaseRangeRestClient,
)


SGT = timezone(timedelta(hours=8))


def now_sgt() -> datetime:
    return datetime.now(SGT)


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


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(float(value))
    except Exception:
        return default


def safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def mean(values: Iterable[float]) -> float:
    clean = [safe_float(v) for v in values if v is not None]
    if not clean:
        return 0.0
    return sum(clean) / len(clean)


def first_present(row: Dict[str, Any], cols: Sequence[str], default: Any = None) -> Any:
    for col in cols:
        if col in row and row[col] is not None:
            return row[col]
    return default


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
    active: bool = True

    def required_columns(self) -> List[str]:
        cols: List[str] = [self.date_col]

        if self.theme_col:
            cols.append(self.theme_col)

        if self.entity_col:
            cols.append(self.entity_col)

        cols.extend(self.score_cols)
        cols.extend(self.driver_cols)
        cols.extend(self.pathway_cols)
        cols.extend(self.attribution_cols)
        cols.extend(self.evidence_cols)

        clean: List[str] = []
        seen = set()

        for col in cols:
            if not col:
                continue
            col = str(col).strip()
            if not col or col in seen:
                continue
            clean.append(col)
            seen.add(col)

        return clean


@dataclass
class HistoricalObservation:
    run_date: date
    theme_name: str
    entity: str
    source_table: str
    score: float
    driver_key: str
    pathway_name: str
    attribution_strength: float
    evidence_count: int
    evidence_strength: float
    raw_payload: Dict[str, Any]


@dataclass
class StreamingLoadTelemetry:
    source_table: str
    pages_loaded: int = 0
    rows_loaded: int = 0
    observations_emitted: int = 0
    rows_filtered: int = 0
    retry_count: int = 0
    max_page_size: int = 0
    pagination_runtime: float = 0.0
    normalization_runtime: float = 0.0
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)

    @property
    def rows_per_second(self) -> float:
        if self.pagination_runtime <= 0:
            return 0.0
        return round(self.rows_loaded / self.pagination_runtime, 4)

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["rows_per_second"] = self.rows_per_second
        return data


@dataclass
class ChunkStreamingTelemetry:
    chunk_start: str
    chunk_end: str
    fetch_start: str
    pages_loaded: int = 0
    rows_loaded: int = 0
    observations_emitted: int = 0
    rows_filtered: int = 0
    retry_count: int = 0
    max_page_size: int = 0
    pagination_runtime: float = 0.0
    normalization_runtime: float = 0.0
    source_tables: Dict[str, Dict[str, Any]] = field(default_factory=dict)

    @property
    def rows_per_second(self) -> float:
        if self.pagination_runtime <= 0:
            return 0.0
        return round(self.rows_loaded / self.pagination_runtime, 4)

    def add_source(self, source_name: str, telemetry: StreamingLoadTelemetry) -> None:
        data = telemetry.to_dict()
        self.source_tables[source_name] = data

        self.pages_loaded += telemetry.pages_loaded
        self.rows_loaded += telemetry.rows_loaded
        self.observations_emitted += telemetry.observations_emitted
        self.rows_filtered += telemetry.rows_filtered
        self.retry_count += telemetry.retry_count
        self.max_page_size = max(self.max_page_size, telemetry.max_page_size)
        self.pagination_runtime += telemetry.pagination_runtime
        self.normalization_runtime += telemetry.normalization_runtime

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["rows_per_second"] = self.rows_per_second
        data["pagination_runtime"] = round(self.pagination_runtime, 6)
        data["normalization_runtime"] = round(self.normalization_runtime, 6)
        return data


CANDIDATE_SOURCE_TABLES: List[SourceTableConfig] = [
    SourceTableConfig(
        table="structural_theme_scores",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="ticker",
        score_cols=["theme_score", "interaction_score", "confidence_score"],
        driver_cols=["positive_drivers", "negative_drivers"],
        pathway_cols=["sector", "subsector"],
        attribution_cols=["score_components"],
        evidence_cols=["evidence_count"],
        active=True,
    ),
    SourceTableConfig(
        table="historical_ai_transmission_scores",
        date_col="run_date_sgt",
        theme_col=None,
        entity_col="affected_ticker",
        score_cols=["transmission_score", "confidence_score"],
        driver_cols=["ai_subsector", "affected_sector", "affected_subsector"],
        pathway_cols=["ai_subsector", "affected_sector", "affected_subsector"],
        attribution_cols=[
            "reconstructed_momentum_score",
            "reconstructed_factor_score",
            "reconstructed_observation_score",
            "persistence_score",
        ],
        evidence_cols=["reconstructed_observation_score", "confidence_score"],
        active=True,
    ),
    SourceTableConfig(
        table="structural_theme_explainability_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["transmission_score", "composite_score", "theme_score", "score"],
        driver_cols=["top_positive_drivers", "top_negative_drivers", "driver"],
        pathway_cols=["pathway_name", "pathway", "transmission_pathway"],
        attribution_cols=["component_scores", "component_score", "contribution_weights", "contribution_weight"],
        evidence_cols=["evidence_count", "evidence_coverage_score"],
        active=True,
    ),
    SourceTableConfig(
        table="structural_theme_attribution_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["component_score", "score"],
        driver_cols=["driver", "component_name"],
        pathway_cols=["pathway_name", "pathway"],
        attribution_cols=["component_name", "component_score", "contribution_weight"],
        evidence_cols=["evidence_count"],
        active=True,
    ),
    SourceTableConfig(
        table="structural_theme_evidence_history",
        date_col="run_date_sgt",
        theme_col="theme_name",
        entity_col="entity",
        score_cols=["evidence_score", "evidence_coverage_score", "score"],
        driver_cols=["driver"],
        pathway_cols=["pathway_name", "pathway"],
        attribution_cols=[],
        evidence_cols=["evidence_count", "evidence_score", "evidence_coverage_score"],
        active=True,
    ),

    # Disabled for now.
    # The live table raised:
    #   column daily_signal_scores.series_id does not exist
    # Keep this config documented but inactive until the exact live schema is confirmed.
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
        active=False,
    ),
]


def active_source_tables() -> List[SourceTableConfig]:
    return [cfg for cfg in CANDIDATE_SOURCE_TABLES if cfg.active]


def extract_attribution_strength(row: Dict[str, Any], cfg: SourceTableConfig) -> float:
    for col in cfg.attribution_cols:
        if col not in row or row[col] is None:
            continue

        value = row[col]

        if isinstance(value, (int, float)):
            return safe_float(value)

        if isinstance(value, dict):
            vals = [safe_float(v) for v in value.values() if isinstance(v, (int, float))]
            return mean(vals)

        if isinstance(value, list):
            vals = []
            for item in value:
                if isinstance(item, dict):
                    vals.extend([
                        safe_float(v)
                        for v in item.values()
                        if isinstance(v, (int, float))
                    ])
                elif isinstance(item, (int, float)):
                    vals.append(safe_float(item))
            return mean(vals)

    return 0.0


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

    pathway_name = safe_text(
        first_present(row, cfg.pathway_cols, "theme_pathway"),
        "theme_pathway",
    )

    evidence_raw = first_present(row, cfg.evidence_cols, 0)
    evidence_count = safe_int(evidence_raw, 0)
    evidence_strength = safe_float(evidence_raw, 0.0)

    attribution_strength = extract_attribution_strength(row, cfg)

    return HistoricalObservation(
        run_date=run_date,
        theme_name=theme_name,
        entity=entity,
        source_table=cfg.table,
        score=score,
        driver_key=driver_key,
        pathway_name=pathway_name,
        attribution_strength=attribution_strength,
        evidence_count=evidence_count,
        evidence_strength=evidence_strength,
        raw_payload=row,
    )


class StreamingObservationLoader:
    def __init__(
        self,
        *,
        rest_client: Optional[SupabaseRangeRestClient] = None,
        pagination_config: Optional[PaginationConfig] = None,
    ) -> None:
        self.rest_client = rest_client or SupabaseRangeRestClient()
        self.pagination_config = pagination_config or PaginationConfig()
        self.loader = PaginatedRestLoader(
            client=self.rest_client,
            config=self.pagination_config,
        )

    def stream_observations(
        self,
        cfg: SourceTableConfig,
        *,
        start_date: date,
        end_date: date,
        theme_name: str,
    ) -> Generator[Tuple[HistoricalObservation, StreamingLoadTelemetry], None, StreamingLoadTelemetry]:
        telemetry = StreamingLoadTelemetry(source_table=cfg.table)

        filters: Dict[str, str] = {
            "and": f"({cfg.date_col}.gte.{start_date.isoformat()},{cfg.date_col}.lte.{end_date.isoformat()})"
        }

        if cfg.theme_col:
            filters[cfg.theme_col] = f"eq.{theme_name}"

        select_columns = cfg.required_columns()

        page_generator = self.loader.stream_pages(
            table_name=cfg.table,
            select_columns=select_columns,
            filters=filters,
            order_by=[(cfg.date_col, "asc")],
        )

        try:
            while True:
                page = next(page_generator)

                telemetry.pages_loaded += 1
                telemetry.rows_loaded += page.returned_row_count
                telemetry.retry_count += page.telemetry.retry_count
                telemetry.max_page_size = max(telemetry.max_page_size, page.returned_row_count)
                telemetry.pagination_runtime += page.telemetry.runtime_seconds

                for row in page.rows:
                    normalize_start = time.perf_counter()

                    row_date = parse_date(row.get(cfg.date_col))
                    if not row_date or row_date < start_date or row_date > end_date:
                        telemetry.rows_filtered += 1
                        telemetry.normalization_runtime += time.perf_counter() - normalize_start
                        continue

                    if cfg.theme_col and row.get(cfg.theme_col):
                        if safe_text(row.get(cfg.theme_col)).lower() != theme_name.lower():
                            telemetry.rows_filtered += 1
                            telemetry.normalization_runtime += time.perf_counter() - normalize_start
                            continue

                    obs = normalise_row(row, cfg, theme_name)
                    telemetry.normalization_runtime += time.perf_counter() - normalize_start

                    if obs is None:
                        telemetry.rows_filtered += 1
                        continue

                    telemetry.observations_emitted += 1
                    yield obs, telemetry

        except StopIteration as done:
            final_pagination_telemetry = done.value
            if final_pagination_telemetry is not None:
                telemetry.validation_errors.extend(final_pagination_telemetry.validation_errors)
                telemetry.validation_warnings.extend(final_pagination_telemetry.validation_warnings)

        telemetry.pagination_runtime = round(telemetry.pagination_runtime, 6)
        telemetry.normalization_runtime = round(telemetry.normalization_runtime, 6)
        return telemetry

    def load_grouped_observations_for_window(
        self,
        source_tables: Sequence[SourceTableConfig],
        *,
        fetch_start: date,
        fetch_end: date,
        theme_name: str,
    ) -> Tuple[Dict[date, List[HistoricalObservation]], ChunkStreamingTelemetry]:
        chunk_telemetry = ChunkStreamingTelemetry(
            chunk_start=fetch_start.isoformat(),
            chunk_end=fetch_end.isoformat(),
            fetch_start=fetch_start.isoformat(),
        )

        grouped: Dict[date, List[HistoricalObservation]] = {}

        for cfg in source_tables:
            if not getattr(cfg, "active", True):
                print(f"  {cfg.table}: skipped inactive source config", flush=True)
                continue

            source_telemetry = StreamingLoadTelemetry(source_table=cfg.table)

            try:
                gen = self.stream_observations(
                    cfg,
                    start_date=fetch_start,
                    end_date=fetch_end,
                    theme_name=theme_name,
                )

                try:
                    while True:
                        obs, running_telemetry = next(gen)
                        grouped.setdefault(obs.run_date, []).append(obs)
                        source_telemetry = running_telemetry

                except StopIteration as done:
                    if done.value is not None:
                        source_telemetry = done.value

                print(
                    f"  {cfg.table}: observations={source_telemetry.observations_emitted}, "
                    f"pages={source_telemetry.pages_loaded}, rows={source_telemetry.rows_loaded}, "
                    f"retries={source_telemetry.retry_count}",
                    flush=True,
                )

            except Exception as exc:
                source_telemetry.validation_errors.append(f"{type(exc).__name__}: {exc}")
                print(f"  WARNING: failed to stream {cfg.table}: {exc}", flush=True)

            chunk_telemetry.add_source(cfg.table, source_telemetry)

        grouped = dict(sorted(grouped.items(), key=lambda item: item[0]))
        return grouped, chunk_telemetry
