#!/usr/bin/env python3
"""
utils/paginated_rest_loader.py

PASS 1 — Institutional Pagination Infrastructure
================================================

Generic Supabase REST pagination infrastructure.

Scope:
- HTTP Range pagination
- Generator-based page streaming
- Retry integration via api_retry_utils.request_with_retries when available
- Configurable page size and throttling
- Selective column retrieval
- Checkpoint-aware offset resume
- Pagination telemetry
- Pagination validation hooks

Deliberately NOT included in Pass 1:
- streaming normalization
- observation loader migration
- reconstruction engine refactor
- rolling aggregators

Architecture:
- Python only
- Supabase REST API only
- No Supabase Python SDK
- Additive-only
- Idempotent
- Restart-safe
- GitHub Actions compatible
"""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Generator, Iterable, List, Optional, Sequence, Tuple

import requests

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


# ---------------------------------------------------------------------
# Import retry wrapper safely
# ---------------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[1] if len(THIS_FILE.parents) > 1 else Path.cwd()
SCRIPT_DIR = THIS_FILE.parent

for candidate in (SCRIPT_DIR, PROJECT_ROOT, PROJECT_ROOT / "scripts"):
    if str(candidate) not in sys.path:
        sys.path.append(str(candidate))

try:
    from api_retry_utils import request_with_retries  # type: ignore
except Exception:
    request_with_retries = None


# ---------------------------------------------------------------------
# Time helpers
# ---------------------------------------------------------------------

SGT = timezone(timedelta(hours=8))


def now_sgt() -> datetime:
    return datetime.now(SGT)


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


# ---------------------------------------------------------------------
# Data contracts
# ---------------------------------------------------------------------

@dataclass
class PaginationConfig:
    """
    Runtime pagination tuning.

    Default env names are intentionally generic so the same loader can be used
    by future structural themes, not only AI transmission.
    """

    page_size: int = field(default_factory=lambda: env_int("PAGINATION_PAGE_SIZE", 1000))
    throttle_seconds: float = field(default_factory=lambda: env_float("PAGINATION_THROTTLE_SECONDS", 0.10))
    request_timeout_seconds: int = field(default_factory=lambda: env_int("PAGINATION_REQUEST_TIMEOUT_SECONDS", 90))
    max_pages: Optional[int] = None
    max_rows: Optional[int] = None

    retry_max_attempts: int = field(default_factory=lambda: env_int("PAGINATION_RETRY_MAX_ATTEMPTS", 3))
    retry_base_sleep_seconds: float = field(default_factory=lambda: env_float("PAGINATION_RETRY_BASE_SLEEP_SECONDS", 2.0))

    validate_pages: bool = field(default_factory=lambda: env_bool("PAGINATION_VALIDATE_PAGES", True))
    fail_on_validation_error: bool = field(default_factory=lambda: env_bool("PAGINATION_FAIL_ON_VALIDATION_ERROR", True))
    checkpoint_every_pages: int = field(default_factory=lambda: env_int("PAGINATION_CHECKPOINT_EVERY_PAGES", 1))

    # Ordering is strongly recommended. Supabase/PostgREST pagination is safest
    # with deterministic ordering.
    default_order_column: Optional[str] = os.getenv("PAGINATION_DEFAULT_ORDER_COLUMN", "").strip() or None
    default_order_direction: str = os.getenv("PAGINATION_DEFAULT_ORDER_DIRECTION", "asc").strip().lower()


@dataclass
class PaginationCheckpoint:
    """
    Checkpoint state for restart-safe page traversal.

    Store this inside your existing checkpoint table's details JSON.
    No schema migration is required for Pass 1 if details is json/jsonb.
    """

    table_name: str
    pipeline_name: str
    theme_name: Optional[str] = None
    source_name: Optional[str] = None
    last_page: int = -1
    last_offset: int = 0
    next_offset: int = 0
    rows_loaded: int = 0
    pages_loaded: int = 0
    completed: bool = False
    last_range_start: Optional[int] = None
    last_range_end: Optional[int] = None
    started_at_sgt: Optional[str] = None
    updated_at_sgt: Optional[str] = None

    @classmethod
    def from_dict(cls, raw: Optional[Dict[str, Any]]) -> "PaginationCheckpoint":
        raw = raw or {}
        return cls(
            table_name=str(raw.get("table_name") or raw.get("table") or ""),
            pipeline_name=str(raw.get("pipeline_name") or ""),
            theme_name=raw.get("theme_name"),
            source_name=raw.get("source_name"),
            last_page=int(raw.get("last_page", -1) or -1),
            last_offset=int(raw.get("last_offset", 0) or 0),
            next_offset=int(raw.get("next_offset", 0) or 0),
            rows_loaded=int(raw.get("rows_loaded", 0) or 0),
            pages_loaded=int(raw.get("pages_loaded", 0) or 0),
            completed=bool(raw.get("completed", False)),
            last_range_start=raw.get("last_range_start"),
            last_range_end=raw.get("last_range_end"),
            started_at_sgt=raw.get("started_at_sgt"),
            updated_at_sgt=raw.get("updated_at_sgt"),
        )

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class PageTelemetry:
    table_name: str
    page_index: int
    range_start: int
    range_end: int
    rows_loaded: int
    runtime_seconds: float
    retry_count: int = 0
    status: str = "OK"
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data["rows_per_second"] = (
            round(self.rows_loaded / self.runtime_seconds, 4)
            if self.runtime_seconds > 0
            else 0.0
        )
        return data


@dataclass
class PaginationTelemetry:
    table_name: str
    started_at_sgt: str
    ended_at_sgt: Optional[str] = None
    pages_loaded: int = 0
    rows_loaded: int = 0
    retry_count: int = 0
    pagination_runtime: float = 0.0
    max_page_size: int = 0
    status: str = "RUNNING"
    validation_errors: List[str] = field(default_factory=list)
    validation_warnings: List[str] = field(default_factory=list)
    page_telemetry: List[Dict[str, Any]] = field(default_factory=list)

    def finish(self, status: str = "SUCCESS") -> None:
        self.status = status
        self.ended_at_sgt = now_sgt().isoformat()

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
class PaginatedPage:
    table_name: str
    rows: List[Dict[str, Any]]
    page_index: int
    range_start: int
    range_end: int
    requested_page_size: int
    returned_row_count: int
    is_terminal_page: bool
    telemetry: PageTelemetry
    checkpoint: PaginationCheckpoint


@dataclass
class ValidationResult:
    ok: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def raise_if_failed(self) -> None:
        if not self.ok:
            raise RuntimeError("Pagination validation failed: " + " | ".join(self.errors))


# ---------------------------------------------------------------------
# REST client
# ---------------------------------------------------------------------

class SupabaseRangeRestClient:
    """
    Minimal Supabase REST client using requests only.

    This is intentionally separate from the reconstruction engine's
    SupabaseRestClient so Pass 1 remains additive-only.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ) -> None:
        self.supabase_url = (supabase_url or os.getenv("SUPABASE_URL", "")).rstrip("/")
        self.supabase_key = (
            supabase_key
            or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or os.getenv("SUPABASE_KEY")
            or ""
        )

        if not self.supabase_url or not self.supabase_key:
            raise RuntimeError(
                "Missing Supabase credentials. Required: SUPABASE_URL and "
                "SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY."
            )

        self.base_url = f"{self.supabase_url}/rest/v1"

    def headers(self, prefer: Optional[str] = None) -> Dict[str, str]:
        h = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json",
        }
        if prefer:
            h["Prefer"] = prefer
        return h

    def table_url(self, table_name: str) -> str:
        return f"{self.base_url}/{table_name}"

    def get_range(
        self,
        *,
        table_name: str,
        params: Dict[str, str],
        range_start: int,
        range_end: int,
        timeout_seconds: int,
        retry_max_attempts: int,
        retry_base_sleep_seconds: float,
        service_name: Optional[str] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        headers = self.headers()
        headers["Range-Unit"] = "items"
        headers["Range"] = f"{range_start}-{range_end}"

        retry_count = 0
        url = self.table_url(table_name)

        if request_with_retries is not None:
            response = request_with_retries(
                "GET",
                url,
                headers=headers,
                params=params,
                timeout=timeout_seconds,
                max_attempts=retry_max_attempts,
                base_sleep_seconds=retry_base_sleep_seconds,
                service_name=service_name or f"Supabase paginated GET {table_name}",
            )
        else:
            # Fallback retry implementation if api_retry_utils.py is not importable.
            last_exc: Optional[Exception] = None
            response = None
            for attempt in range(1, retry_max_attempts + 1):
                try:
                    response = requests.get(
                        url,
                        headers=headers,
                        params=params,
                        timeout=timeout_seconds,
                    )
                    if response.status_code < 500 and response.status_code != 429:
                        break
                except Exception as exc:
                    last_exc = exc

                retry_count += 1
                time.sleep(retry_base_sleep_seconds * attempt)

            if response is None:
                raise RuntimeError(f"GET failed for {table_name}: {last_exc}")

        if response.status_code == 404:
            raise RuntimeError(f"Supabase table not found or unavailable: {table_name}")

        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase paginated GET failed for {table_name}: "
                f"{response.status_code} - {response.text[:2000]}"
            )

        if not response.text:
            return [], retry_count

        payload = response.json()
        if not isinstance(payload, list):
            raise RuntimeError(
                f"Expected list payload from {table_name}, got {type(payload).__name__}"
            )

        return payload, retry_count

    def post_insert_minimal(
        self,
        *,
        table_name: str,
        rows: Sequence[Dict[str, Any]],
        timeout_seconds: int = 90,
    ) -> int:
        if not rows:
            return 0

        response = requests.post(
            self.table_url(table_name),
            headers=self.headers("return=minimal"),
            data=json.dumps(list(rows), default=str),
            timeout=timeout_seconds,
        )

        if response.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Supabase insert failed for {table_name}: "
                f"{response.status_code} - {response.text[:2000]}"
            )

        return len(rows)

    def upsert_minimal(
        self,
        *,
        table_name: str,
        rows: Sequence[Dict[str, Any]],
        conflict_columns: Sequence[str],
        timeout_seconds: int = 90,
    ) -> int:
        if not rows:
            return 0

        conflict_key = ",".join(conflict_columns)
        url = f"{self.table_url(table_name)}?on_conflict={conflict_key}"

        response = requests.post(
            url,
            headers=self.headers("resolution=merge-duplicates,return=minimal"),
            data=json.dumps(list(rows), default=str),
            timeout=timeout_seconds,
        )

        if response.status_code not in (200, 201, 204):
            raise RuntimeError(
                f"Supabase upsert failed for {table_name}: "
                f"{response.status_code} - {response.text[:2000]}"
            )

        return len(rows)


# ---------------------------------------------------------------------
# Validation hooks
# ---------------------------------------------------------------------

class PaginationValidator:
    """
    Page traversal validator.

    Validates:
    - duplicate page detection
    - missing page detection
    - monotonic traversal
    - overlap detection
    - checkpoint continuity
    """

    def __init__(self) -> None:
        self.seen_ranges: set[Tuple[int, int]] = set()
        self.seen_page_indexes: set[int] = set()
        self.previous_range_end: Optional[int] = None
        self.previous_page_index: Optional[int] = None

    def validate_page(
        self,
        *,
        page_index: int,
        range_start: int,
        range_end: int,
        rows: Sequence[Dict[str, Any]],
        checkpoint: Optional[PaginationCheckpoint] = None,
    ) -> ValidationResult:
        errors: List[str] = []
        warnings: List[str] = []

        if page_index in self.seen_page_indexes:
            errors.append(f"Duplicate page detected: page_index={page_index}")

        range_key = (range_start, range_end)
        if range_key in self.seen_ranges:
            errors.append(f"Duplicate page range detected: {range_start}-{range_end}")

        if range_start > range_end:
            errors.append(f"Invalid range: range_start={range_start} > range_end={range_end}")

        if self.previous_range_end is not None:
            expected_start = self.previous_range_end + 1

            if range_start < expected_start:
                errors.append(
                    f"Page overlap detected: previous_end={self.previous_range_end}, "
                    f"current_start={range_start}"
                )

            if range_start > expected_start:
                errors.append(
                    f"Missing page gap detected: expected_start={expected_start}, "
                    f"current_start={range_start}"
                )

        if self.previous_page_index is not None:
            expected_page_index = self.previous_page_index + 1
            if page_index != expected_page_index:
                errors.append(
                    f"Non-monotonic page traversal: expected_page_index={expected_page_index}, "
                    f"actual_page_index={page_index}"
                )

        if checkpoint is not None and checkpoint.completed:
            warnings.append(
                "Checkpoint says pagination already completed. "
                "Loader continued because caller explicitly invoked traversal."
            )

        if checkpoint is not None and checkpoint.next_offset:
            if page_index == checkpoint.last_page + 1 and range_start != checkpoint.next_offset:
                errors.append(
                    f"Checkpoint continuity violation: checkpoint.next_offset={checkpoint.next_offset}, "
                    f"actual_range_start={range_start}"
                )

        self.seen_page_indexes.add(page_index)
        self.seen_ranges.add(range_key)
        self.previous_range_end = range_end
        self.previous_page_index = page_index

        return ValidationResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)


def validate_checkpoint_continuity(
    checkpoint: Optional[PaginationCheckpoint],
    *,
    requested_start_offset: int,
) -> ValidationResult:
    if checkpoint is None:
        return ValidationResult(ok=True)

    errors: List[str] = []
    warnings: List[str] = []

    if checkpoint.completed:
        warnings.append("Existing checkpoint is completed; caller may be intentionally re-running.")

    if checkpoint.next_offset and requested_start_offset < checkpoint.next_offset:
        warnings.append(
            f"Requested start offset {requested_start_offset} is before checkpoint next_offset "
            f"{checkpoint.next_offset}. This may be a deliberate replay."
        )

    if checkpoint.next_offset and requested_start_offset > checkpoint.next_offset:
        errors.append(
            f"Requested start offset {requested_start_offset} skips checkpoint next_offset "
            f"{checkpoint.next_offset}."
        )

    return ValidationResult(ok=(len(errors) == 0), errors=errors, warnings=warnings)


# ---------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------

def build_select_param(columns: Optional[Sequence[str]]) -> str:
    if not columns:
        return "*"

    clean = []
    for col in columns:
        text = str(col).strip()
        if text:
            clean.append(text)

    return ",".join(clean) if clean else "*"


def build_order_param(order_by: Optional[Sequence[Tuple[str, str]]], config: PaginationConfig) -> Optional[str]:
    pieces: List[str] = []

    if order_by:
        for col, direction in order_by:
            col = str(col).strip()
            direction = str(direction or "asc").strip().lower()
            if not col:
                continue
            if direction not in {"asc", "desc"}:
                direction = "asc"
            pieces.append(f"{col}.{direction}")

    elif config.default_order_column:
        direction = config.default_order_direction if config.default_order_direction in {"asc", "desc"} else "asc"
        pieces.append(f"{config.default_order_column}.{direction}")

    return ",".join(pieces) if pieces else None


def build_rest_params(
    *,
    select_columns: Optional[Sequence[str]] = None,
    filters: Optional[Dict[str, str]] = None,
    order_by: Optional[Sequence[Tuple[str, str]]] = None,
    config: Optional[PaginationConfig] = None,
) -> Dict[str, str]:
    cfg = config or PaginationConfig()
    params: Dict[str, str] = {}
    params["select"] = build_select_param(select_columns)

    if filters:
        for key, value in filters.items():
            if value is not None:
                params[str(key)] = str(value)

    order_param = build_order_param(order_by, cfg)
    if order_param:
        params["order"] = order_param

    return params


# ---------------------------------------------------------------------
# Checkpoint persistence helpers
# ---------------------------------------------------------------------

def load_pagination_checkpoint_from_details(
    details: Optional[Dict[str, Any]],
    *,
    table_name: str,
    pipeline_name: str,
    theme_name: Optional[str] = None,
    source_name: Optional[str] = None,
) -> PaginationCheckpoint:
    details = details or {}
    raw = details.get("pagination_state") or details.get("pagination") or {}

    checkpoint = PaginationCheckpoint.from_dict(raw)
    checkpoint.table_name = checkpoint.table_name or table_name
    checkpoint.pipeline_name = checkpoint.pipeline_name or pipeline_name
    checkpoint.theme_name = checkpoint.theme_name or theme_name
    checkpoint.source_name = checkpoint.source_name or source_name

    return checkpoint


def merge_pagination_checkpoint_into_details(
    existing_details: Optional[Dict[str, Any]],
    checkpoint: PaginationCheckpoint,
    telemetry: Optional[PaginationTelemetry] = None,
) -> Dict[str, Any]:
    details = dict(existing_details or {})
    details["pagination_state"] = checkpoint.to_dict()
    if telemetry is not None:
        details["pagination_telemetry"] = telemetry.to_dict()
    return details


# ---------------------------------------------------------------------
# Main loader
# ---------------------------------------------------------------------

class PaginatedRestLoader:
    """
    Generic range-based Supabase REST loader.

    Usage:
        client = SupabaseRangeRestClient()
        loader = PaginatedRestLoader(client)

        for page in loader.stream_pages(
            table_name="historical_ai_transmission_scores",
            select_columns=["run_date_sgt", "affected_ticker", "transmission_score"],
            filters={"run_date_sgt": "gte.2026-01-01"},
            order_by=[("run_date_sgt", "asc"), ("affected_ticker", "asc")],
        ):
            process(page.rows)
    """

    def __init__(
        self,
        client: Optional[SupabaseRangeRestClient] = None,
        config: Optional[PaginationConfig] = None,
    ) -> None:
        self.client = client or SupabaseRangeRestClient()
        self.config = config or PaginationConfig()
        self.validator = PaginationValidator()

    def stream_pages(
        self,
        *,
        table_name: str,
        select_columns: Optional[Sequence[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        order_by: Optional[Sequence[Tuple[str, str]]] = None,
        checkpoint: Optional[PaginationCheckpoint] = None,
        start_offset: Optional[int] = None,
        page_size: Optional[int] = None,
        checkpoint_callback: Optional[Callable[[PaginationCheckpoint, PaginationTelemetry], None]] = None,
        telemetry_callback: Optional[Callable[[PageTelemetry, PaginationTelemetry], None]] = None,
    ) -> Generator[PaginatedPage, None, PaginationTelemetry]:
        cfg = self.config
        effective_page_size = int(page_size or cfg.page_size)

        if effective_page_size <= 0:
            raise ValueError("page_size must be positive.")

        if checkpoint is None:
            checkpoint = PaginationCheckpoint(
                table_name=table_name,
                pipeline_name=os.getenv("PIPELINE_NAME", "PAGINATED_REST_LOADER"),
                started_at_sgt=now_sgt().isoformat(),
            )

        if start_offset is None:
            start_offset = int(checkpoint.next_offset or 0)

        continuity = validate_checkpoint_continuity(checkpoint, requested_start_offset=start_offset)
        if continuity.errors and cfg.fail_on_validation_error:
            continuity.raise_if_failed()

        telemetry = PaginationTelemetry(
            table_name=table_name,
            started_at_sgt=now_sgt().isoformat(),
            validation_warnings=list(continuity.warnings),
            validation_errors=list(continuity.errors),
        )

        params = build_rest_params(
            select_columns=select_columns,
            filters=filters,
            order_by=order_by,
            config=cfg,
        )

        offset = start_offset
        page_index = checkpoint.last_page + 1 if checkpoint.last_page >= 0 and offset == checkpoint.next_offset else 0
        traversal_start = time.perf_counter()

        while True:
            if cfg.max_pages is not None and telemetry.pages_loaded >= cfg.max_pages:
                telemetry.validation_warnings.append(f"Stopped at configured max_pages={cfg.max_pages}")
                break

            if cfg.max_rows is not None and telemetry.rows_loaded >= cfg.max_rows:
                telemetry.validation_warnings.append(f"Stopped at configured max_rows={cfg.max_rows}")
                break

            range_start = offset
            range_end = offset + effective_page_size - 1
            page_start = time.perf_counter()

            rows, retries = self.client.get_range(
                table_name=table_name,
                params=params,
                range_start=range_start,
                range_end=range_end,
                timeout_seconds=cfg.request_timeout_seconds,
                retry_max_attempts=cfg.retry_max_attempts,
                retry_base_sleep_seconds=cfg.retry_base_sleep_seconds,
                service_name=f"Supabase paginated GET {table_name} page {page_index}",
            )

            runtime = time.perf_counter() - page_start
            row_count = len(rows)
            is_terminal = row_count < effective_page_size

            page_telemetry = PageTelemetry(
                table_name=table_name,
                page_index=page_index,
                range_start=range_start,
                range_end=range_end,
                rows_loaded=row_count,
                runtime_seconds=round(runtime, 6),
                retry_count=retries,
            )

            if cfg.validate_pages:
                validation = self.validator.validate_page(
                    page_index=page_index,
                    range_start=range_start,
                    range_end=range_end,
                    rows=rows,
                    checkpoint=checkpoint,
                )
                telemetry.validation_errors.extend(validation.errors)
                telemetry.validation_warnings.extend(validation.warnings)
                if validation.errors and cfg.fail_on_validation_error:
                    telemetry.finish("FAILED_VALIDATION")
                    raise RuntimeError(" | ".join(validation.errors))

            telemetry.pages_loaded += 1 if row_count > 0 else 0
            telemetry.rows_loaded += row_count
            telemetry.retry_count += retries
            telemetry.max_page_size = max(telemetry.max_page_size, row_count)
            telemetry.page_telemetry.append(page_telemetry.to_dict())

            checkpoint.table_name = table_name
            checkpoint.last_page = page_index
            checkpoint.last_offset = range_start
            checkpoint.next_offset = range_start + row_count
            checkpoint.rows_loaded += row_count
            checkpoint.pages_loaded += 1 if row_count > 0 else 0
            checkpoint.last_range_start = range_start
            checkpoint.last_range_end = range_end
            checkpoint.completed = is_terminal
            checkpoint.updated_at_sgt = now_sgt().isoformat()

            telemetry.pagination_runtime = round(time.perf_counter() - traversal_start, 6)

            if telemetry_callback is not None:
                telemetry_callback(page_telemetry, telemetry)

            if checkpoint_callback is not None and cfg.checkpoint_every_pages > 0:
                if row_count > 0 and checkpoint.pages_loaded % cfg.checkpoint_every_pages == 0:
                    checkpoint_callback(checkpoint, telemetry)

            if row_count == 0:
                checkpoint.completed = True
                if checkpoint_callback is not None:
                    checkpoint_callback(checkpoint, telemetry)
                break

            yield PaginatedPage(
                table_name=table_name,
                rows=rows,
                page_index=page_index,
                range_start=range_start,
                range_end=range_end,
                requested_page_size=effective_page_size,
                returned_row_count=row_count,
                is_terminal_page=is_terminal,
                telemetry=page_telemetry,
                checkpoint=checkpoint,
            )

            if is_terminal:
                if checkpoint_callback is not None:
                    checkpoint_callback(checkpoint, telemetry)
                break

            offset += effective_page_size
            page_index += 1

            if cfg.throttle_seconds > 0:
                time.sleep(cfg.throttle_seconds)

        telemetry.pagination_runtime = round(time.perf_counter() - traversal_start, 6)
        telemetry.finish("SUCCESS" if not telemetry.validation_errors else "FAILED_VALIDATION")
        return telemetry

    def fetch_all_pages_materialized(
        self,
        *,
        table_name: str,
        select_columns: Optional[Sequence[str]] = None,
        filters: Optional[Dict[str, str]] = None,
        order_by: Optional[Sequence[Tuple[str, str]]] = None,
        checkpoint: Optional[PaginationCheckpoint] = None,
        start_offset: Optional[int] = None,
        page_size: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], PaginationTelemetry]:
        """
        Convenience method for compatibility with old code.

        Not recommended for very large historical reconstruction, but useful
        for small validation queries and tests.
        """

        rows: List[Dict[str, Any]] = []
        telemetry = PaginationTelemetry(table_name=table_name, started_at_sgt=now_sgt().isoformat())

        generator = self.stream_pages(
            table_name=table_name,
            select_columns=select_columns,
            filters=filters,
            order_by=order_by,
            checkpoint=checkpoint,
            start_offset=start_offset,
            page_size=page_size,
        )

        try:
            while True:
                page = next(generator)
                rows.extend(page.rows)
        except StopIteration as done:
            if done.value is not None:
                telemetry = done.value

        return rows, telemetry


# ---------------------------------------------------------------------
# Optional telemetry persistence
# ---------------------------------------------------------------------

def write_pagination_telemetry_to_production_runs(
    client: SupabaseRangeRestClient,
    *,
    telemetry: PaginationTelemetry,
    pipeline_name: str,
    rows_written: Optional[int] = None,
    error_message: Optional[str] = None,
) -> None:
    """
    Best-effort telemetry persistence into production_pipeline_runs.

    This does not require schema changes. Pagination fields are encoded in
    error_message if failed, and signal_rows/runtime_seconds are mapped to
    existing columns commonly used in the user's platform.

    For richer pagination telemetry, store telemetry.to_dict() inside the
    checkpoint details JSON using merge_pagination_checkpoint_into_details().
    """

    row = {
        "run_timestamp_sgt": now_sgt().isoformat(),
        "run_date_sgt": now_sgt().date().isoformat(),
        "pipeline_name": pipeline_name,
        "status": telemetry.status,
        "runtime_seconds": round(telemetry.pagination_runtime, 4),
        "signal_rows": rows_written if rows_written is not None else telemetry.rows_loaded,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "error_message": (error_message or json.dumps({
            "pagination": {
                "pages_loaded": telemetry.pages_loaded,
                "rows_loaded": telemetry.rows_loaded,
                "rows_per_second": telemetry.rows_per_second,
                "retry_count": telemetry.retry_count,
                "pagination_runtime": telemetry.pagination_runtime,
                "max_page_size": telemetry.max_page_size,
                "validation_errors": telemetry.validation_errors[:10],
                "validation_warnings": telemetry.validation_warnings[:10],
            }
        }, default=str))[:1000],
    }

    try:
        client.post_insert_minimal(
            table_name="production_pipeline_runs",
            rows=[row],
            timeout_seconds=90,
        )
    except Exception as exc:
        print(f"[WARN] Pagination telemetry insert skipped: {exc}", flush=True)


# ---------------------------------------------------------------------
# Smoke-test entrypoint
# ---------------------------------------------------------------------

def main() -> None:
    """
    Optional smoke test.

    Example:
        PAGINATION_TEST_TABLE=historical_ai_transmission_scores \
        PAGINATION_TEST_SELECT=run_date_sgt,affected_ticker,transmission_score \
        PAGINATION_PAGE_SIZE=250 \
        python utils/paginated_rest_loader.py
    """

    table_name = os.getenv("PAGINATION_TEST_TABLE", "").strip()
    if not table_name:
        raise RuntimeError("Set PAGINATION_TEST_TABLE to run the pagination smoke test.")

    select_raw = os.getenv("PAGINATION_TEST_SELECT", "*").strip()
    select_columns = None if select_raw == "*" else [x.strip() for x in select_raw.split(",") if x.strip()]

    order_raw = os.getenv("PAGINATION_TEST_ORDER", "").strip()
    order_by = None
    if order_raw:
        parts = []
        for piece in order_raw.split(","):
            token = piece.strip()
            if not token:
                continue
            if "." in token:
                col, direction = token.rsplit(".", 1)
            else:
                col, direction = token, "asc"
            parts.append((col, direction))
        order_by = parts

    client = SupabaseRangeRestClient()
    loader = PaginatedRestLoader(client)

    total_rows = 0
    final_telemetry: Optional[PaginationTelemetry] = None
    generator = loader.stream_pages(
        table_name=table_name,
        select_columns=select_columns,
        order_by=order_by,
    )

    try:
        while True:
            page = next(generator)
            total_rows += page.returned_row_count
            print(
                f"[{now_sgt().isoformat()}] page={page.page_index} "
                f"range={page.range_start}-{page.range_end} rows={page.returned_row_count}",
                flush=True,
            )
    except StopIteration as done:
        final_telemetry = done.value

    print(json.dumps({
        "total_rows": total_rows,
        "telemetry": final_telemetry.to_dict() if final_telemetry else None,
    }, indent=2, default=str))


if __name__ == "__main__":
    main()
