#!/usr/bin/env python3
"""
ai_transmission_scoring_v2.py

Purpose
-------
Evidence-aware AI transmission scoring engine.

Reads:
    public.ai_transmission_map
    public.ai_transmission_observations

Writes:
    public.ai_transmission_scores

Compared with v1
----------------
v1 used placeholder evidence_score and sentiment_score.

v2 uses recent observation data:

    evidence_score =
        40% avg ai_relevance_score
        30% avg impact_magnitude_score
        20% avg observation confidence_score
        10% evidence count score

    sentiment_score =
        avg observation sentiment_score,
        direction-adjusted for NEGATIVE transmission

    confidence_score =
        60% map confidence_score
        40% avg observation confidence_score

Final transmission score:
    30% exposure_score
    25% evidence_score
    20% sentiment_score
    15% market_confirmation_score
    10% confidence_score

Designed for:
- GitHub Actions
- Supabase REST API
- FMP stable endpoint for market confirmation
- No supabase Python package required

Required environment variables
------------------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional environment variables
------------------------------
FMP_API_KEY
OBS_LOOKBACK_DAYS
PRICE_LOOKBACK_DAYS
"""

from __future__ import annotations

import os
import sys
import math
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import requests


# ============================================================
# CONFIG
# ============================================================

PIPELINE_NAME = "AI_TRANSMISSION_SCORING_V2"
SOURCE = "PYTHON_TRANSMISSION_V2"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

MAP_TABLE = "ai_transmission_map"
OBS_TABLE = "ai_transmission_observations"
SCORES_TABLE = "ai_transmission_scores"

REQUEST_TIMEOUT = 45
MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 2

MAX_MAP_ROWS = int(os.getenv("MAX_TRANSMISSION_MAP_ROWS", "500"))
OBS_LOOKBACK_DAYS = int(os.getenv("OBS_LOOKBACK_DAYS", "14"))
PRICE_LOOKBACK_DAYS = int(os.getenv("PRICE_LOOKBACK_DAYS", "30"))

MARKET_CONFIRMATION_ENABLED = bool(FMP_API_KEY)

# Final score weights
WEIGHT_EXPOSURE = 0.30
WEIGHT_EVIDENCE = 0.25
WEIGHT_SENTIMENT = 0.20
WEIGHT_MARKET_CONFIRMATION = 0.15
WEIGHT_CONFIDENCE = 0.10

# Evidence score subweights
WEIGHT_OBS_AI_RELEVANCE = 0.40
WEIGHT_OBS_IMPACT = 0.30
WEIGHT_OBS_CONFIDENCE = 0.20
WEIGHT_OBS_COUNT = 0.10

# Confidence blend
WEIGHT_MAP_CONFIDENCE = 0.60
WEIGHT_OBS_CONFIDENCE_BLEND = 0.40

# Defaults
DEFAULT_EVIDENCE_SCORE = 50.0
DEFAULT_SENTIMENT_SCORE = 50.0
DEFAULT_MARKET_CONFIRMATION_SCORE = 50.0
DEFAULT_CONFIDENCE_SCORE = 50.0
DEFAULT_EXPOSURE_SCORE = 50.0

# Evidence count normalization
# 0 evidence = 0
# 1 evidence = 35
# 2 evidence = 65
# 3+ evidence = 100
TARGET_OBSERVATIONS_PER_MAP = 3


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(PIPELINE_NAME)


# ============================================================
# DATE HELPERS
# ============================================================

def now_sgt() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)


def today_sgt_str() -> str:
    return now_sgt().date().isoformat()


def lookback_date_sgt_str(days: int) -> str:
    return (now_sgt().date() - timedelta(days=days)).isoformat()


# ============================================================
# GENERAL HELPERS
# ============================================================

def require_env() -> None:
    missing = []

    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")

    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")

    if missing:
        raise RuntimeError(
            "Missing required environment variable(s): " + ", ".join(missing)
        )


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    try:
        if value is None:
            return default
        value = float(value)
        if math.isnan(value) or math.isinf(value):
            return default
        return value
    except Exception:
        return default


def clamp_score(value: Any, default: float = 50.0) -> float:
    value = safe_float(value, default)
    if value is None:
        value = default
    return max(0.0, min(100.0, float(value)))


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout: int = REQUEST_TIMEOUT,
) -> requests.Response:
    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=timeout,
            )

            if response.status_code in (429, 500, 502, 503, 504):
                raise RuntimeError(
                    f"Transient HTTP {response.status_code}: {response.text[:300]}"
                )

            return response

        except Exception as exc:
            last_error = exc
            logger.warning(
                "Request failed attempt %s/%s: %s",
                attempt,
                MAX_RETRIES,
                str(exc),
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS * attempt)

    raise RuntimeError(f"Request failed after retries: {last_error}")


# ============================================================
# SUPABASE REST HELPERS
# ============================================================

def supabase_headers(prefer: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    if prefer:
        headers["Prefer"] = prefer

    return headers


def supabase_select(
    table: str,
    *,
    select: str = "*",
    params: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/{table}"

    query_params = {"select": select}
    if params:
        query_params.update(params)

    response = request_with_retries(
        "GET",
        url,
        headers=supabase_headers(),
        params=query_params,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase SELECT failed for {table}: "
            f"HTTP {response.status_code} - {response.text}"
        )

    return response.json()


def supabase_upsert(
    table: str,
    rows: List[Dict[str, Any]],
    *,
    on_conflict: str,
) -> None:
    if not rows:
        logger.info("No rows to upsert into %s", table)
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    params = {"on_conflict": on_conflict}

    response = request_with_retries(
        "POST",
        url,
        headers=supabase_headers(prefer="resolution=merge-duplicates,return=minimal"),
        params=params,
        json_body=rows,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase UPSERT failed for {table}: "
            f"HTTP {response.status_code} - {response.text}"
        )

    logger.info("Upserted %s row(s) into %s", len(rows), table)


# ============================================================
# DATA LOADERS
# ============================================================

def load_active_transmission_map() -> List[Dict[str, Any]]:
    logger.info("Loading active rows from %s", MAP_TABLE)

    rows = supabase_select(
        MAP_TABLE,
        select=(
            "id,"
            "ai_subsector,"
            "affected_sector,"
            "affected_subsector,"
            "affected_ticker,"
            "affected_company,"
            "transmission_direction,"
            "transmission_type,"
            "base_strength_score,"
            "confidence_score,"
            "is_active"
        ),
        params={
            "is_active": "eq.true",
            "order": "id.asc",
            "limit": str(MAX_MAP_ROWS),
        },
    )

    logger.info("Loaded %s active transmission mapping row(s)", len(rows))
    return rows


def load_recent_observations() -> List[Dict[str, Any]]:
    start_date = lookback_date_sgt_str(OBS_LOOKBACK_DAYS)

    logger.info(
        "Loading observations from %s where run_date_sgt >= %s",
        OBS_TABLE,
        start_date,
    )

    rows = supabase_select(
        OBS_TABLE,
        select=(
            "id,"
            "run_date_sgt,"
            "map_id,"
            "affected_ticker,"
            "affected_company,"
            "evidence_source,"
            "ai_relevance_score,"
            "impact_magnitude_score,"
            "sentiment_score,"
            "confidence_score,"
            "created_at"
        ),
        params={
            "run_date_sgt": f"gte.{start_date}",
            "order": "run_date_sgt.desc,created_at.desc",
            "limit": "10000",
        },
    )

    logger.info("Loaded %s recent observation row(s)", len(rows))
    return rows


# ============================================================
# OBSERVATION AGGREGATION
# ============================================================

def aggregate_observations(
    obs_rows: List[Dict[str, Any]],
) -> Dict[int, Dict[str, Any]]:
    grouped: Dict[int, List[Dict[str, Any]]] = {}

    for row in obs_rows:
        map_id = row.get("map_id")
        if map_id is None:
            continue

        try:
            map_id_int = int(map_id)
        except Exception:
            continue

        # Exclude diagnostic no-evidence rows from averages
        if row.get("evidence_source") == "NO_EVIDENCE_FOUND":
            continue

        grouped.setdefault(map_id_int, []).append(row)

    aggregates: Dict[int, Dict[str, Any]] = {}

    for map_id, rows in grouped.items():
        ai_vals = [
            safe_float(r.get("ai_relevance_score"))
            for r in rows
            if safe_float(r.get("ai_relevance_score")) is not None
        ]
        impact_vals = [
            safe_float(r.get("impact_magnitude_score"))
            for r in rows
            if safe_float(r.get("impact_magnitude_score")) is not None
        ]
        sentiment_vals = [
            safe_float(r.get("sentiment_score"))
            for r in rows
            if safe_float(r.get("sentiment_score")) is not None
        ]
        confidence_vals = [
            safe_float(r.get("confidence_score"))
            for r in rows
            if safe_float(r.get("confidence_score")) is not None
        ]

        def avg(values: List[float], default: float) -> float:
            if not values:
                return default
            return sum(values) / len(values)

        observation_count = len(rows)

        avg_ai_relevance = clamp_score(avg(ai_vals, DEFAULT_EVIDENCE_SCORE))
        avg_impact = clamp_score(avg(impact_vals, DEFAULT_EVIDENCE_SCORE))
        avg_sentiment = clamp_score(avg(sentiment_vals, DEFAULT_SENTIMENT_SCORE))
        avg_confidence = clamp_score(avg(confidence_vals, DEFAULT_CONFIDENCE_SCORE))

        count_score = compute_evidence_count_score(observation_count)

        evidence_score = (
            WEIGHT_OBS_AI_RELEVANCE * avg_ai_relevance
            + WEIGHT_OBS_IMPACT * avg_impact
            + WEIGHT_OBS_CONFIDENCE * avg_confidence
            + WEIGHT_OBS_COUNT * count_score
        )

        aggregates[map_id] = {
            "observation_count": observation_count,
            "avg_ai_relevance_score": round(avg_ai_relevance, 4),
            "avg_impact_magnitude_score": round(avg_impact, 4),
            "avg_observation_sentiment_score": round(avg_sentiment, 4),
            "avg_observation_confidence_score": round(avg_confidence, 4),
            "evidence_count_score": round(count_score, 4),
            "evidence_score": round(clamp_score(evidence_score), 4),
        }

    logger.info("Aggregated observations for %s map_id(s)", len(aggregates))
    return aggregates


def compute_evidence_count_score(count: int) -> float:
    if count <= 0:
        return 0.0

    if count >= TARGET_OBSERVATIONS_PER_MAP:
        return 100.0

    return clamp_score((count / TARGET_OBSERVATIONS_PER_MAP) * 100.0, 0.0)


# ============================================================
# MARKET CONFIRMATION - FMP STABLE ENDPOINT
# ============================================================

def fetch_fmp_historical_prices(
    ticker: str,
    *,
    lookback_days: int = PRICE_LOOKBACK_DAYS,
) -> List[Dict[str, Any]]:
    """
    Fetch recent daily prices using FMP stable endpoint.

    Endpoint:
        /stable/historical-price-eod/light

    Expected fields commonly include:
        date, price, volume

    Returns prices sorted ascending by date.
    """
    if not FMP_API_KEY or not ticker:
        return []

    url = "https://financialmodelingprep.com/stable/historical-price-eod/light"

    params = {
        "symbol": ticker,
        "apikey": FMP_API_KEY,
    }

    response = request_with_retries("GET", url, params=params)

    if response.status_code >= 400:
        logger.warning(
            "FMP stable historical price failed for %s: HTTP %s - %s",
            ticker,
            response.status_code,
            response.text[:300],
        )
        return []

    payload = response.json()

    if not isinstance(payload, list):
        logger.warning("Unexpected FMP payload for %s: %s", ticker, str(payload)[:200])
        return []

    clean = []

    for row in payload:
        if not isinstance(row, dict):
            continue

        date = row.get("date")
        price = safe_float(
            row.get("price")
            if row.get("price") is not None
            else row.get("close")
        )
        volume = safe_float(row.get("volume"))

        if date and price is not None:
            clean.append(
                {
                    "date": date,
                    "close": price,
                    "volume": volume,
                }
            )

    clean.sort(key=lambda x: x["date"])

    if lookback_days and len(clean) > lookback_days:
        clean = clean[-lookback_days:]

    return clean


def compute_market_confirmation_score(
    ticker: Optional[str],
    direction: str,
) -> float:
    if not MARKET_CONFIRMATION_ENABLED:
        return DEFAULT_MARKET_CONFIRMATION_SCORE

    if not ticker:
        return DEFAULT_MARKET_CONFIRMATION_SCORE

    if direction not in ("POSITIVE", "NEGATIVE"):
        return DEFAULT_MARKET_CONFIRMATION_SCORE

    prices = fetch_fmp_historical_prices(ticker)

    if len(prices) < 8:
        logger.warning(
            "Insufficient price history for %s. Using neutral market score.",
            ticker,
        )
        return DEFAULT_MARKET_CONFIRMATION_SCORE

    latest_close = safe_float(prices[-1].get("close"))
    first_close = safe_float(prices[0].get("close"))

    if not latest_close or not first_close or first_close <= 0:
        return DEFAULT_MARKET_CONFIRMATION_SCORE

    return_pct = (latest_close / first_close - 1.0) * 100.0

    recent_volumes = [
        safe_float(x.get("volume"))
        for x in prices
        if safe_float(x.get("volume")) is not None
    ]

    volume_boost = 0.0

    if len(recent_volumes) >= 8:
        latest_volume = recent_volumes[-1]
        avg_volume = sum(recent_volumes[:-1]) / max(1, len(recent_volumes[:-1]))

        if avg_volume > 0:
            volume_ratio = latest_volume / avg_volume

            if volume_ratio >= 1.5:
                volume_boost = 7.5
            elif volume_ratio >= 1.2:
                volume_boost = 4.0

    if direction == "POSITIVE":
        directional_return = return_pct
    elif direction == "NEGATIVE":
        directional_return = -return_pct
    else:
        directional_return = 0.0

    score = 50.0 + (directional_return * 2.5) + volume_boost

    return clamp_score(score, DEFAULT_MARKET_CONFIRMATION_SCORE)


# ============================================================
# SCORING LOGIC
# ============================================================

def compute_sentiment_component(
    *,
    direction: str,
    raw_sentiment_score: float,
    has_evidence: bool,
) -> float:
    """
    Convert observation sentiment into transmission-supportive sentiment.

    For POSITIVE transmission:
        high sentiment is supportive.

    For NEGATIVE transmission:
        low sentiment for the affected company/sector supports the disruption thesis.
        Example: BPO company negative sentiment -> stronger negative transmission.

    For MIXED/UNCERTAIN:
        use neutral-ish raw sentiment, slightly compressed around 50.
    """
    raw = clamp_score(raw_sentiment_score, DEFAULT_SENTIMENT_SCORE)

    if not has_evidence:
        return DEFAULT_SENTIMENT_SCORE

    if direction == "POSITIVE":
        return raw

    if direction == "NEGATIVE":
        return clamp_score(100.0 - raw, DEFAULT_SENTIMENT_SCORE)

    # Compress mixed/uncertain toward neutral to avoid overclaiming
    return clamp_score(50.0 + ((raw - 50.0) * 0.50), DEFAULT_SENTIMENT_SCORE)


def compute_confidence_component(
    *,
    map_confidence_score: float,
    obs_confidence_score: float,
    has_evidence: bool,
) -> float:
    map_conf = clamp_score(map_confidence_score, DEFAULT_CONFIDENCE_SCORE)

    if not has_evidence:
        return map_conf

    obs_conf = clamp_score(obs_confidence_score, DEFAULT_CONFIDENCE_SCORE)

    return clamp_score(
        WEIGHT_MAP_CONFIDENCE * map_conf
        + WEIGHT_OBS_CONFIDENCE_BLEND * obs_conf,
        DEFAULT_CONFIDENCE_SCORE,
    )


def compute_score_for_row(
    map_row: Dict[str, Any],
    obs_agg: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    direction = map_row.get("transmission_direction") or "UNCERTAIN"

    exposure_score = clamp_score(
        safe_float(map_row.get("base_strength_score")),
        DEFAULT_EXPOSURE_SCORE,
    )

    map_confidence = clamp_score(
        safe_float(map_row.get("confidence_score")),
        DEFAULT_CONFIDENCE_SCORE,
    )

    has_evidence = obs_agg is not None and int(obs_agg.get("observation_count", 0)) > 0

    if has_evidence:
        evidence_score = clamp_score(obs_agg.get("evidence_score"), DEFAULT_EVIDENCE_SCORE)
        raw_sentiment_score = clamp_score(
            obs_agg.get("avg_observation_sentiment_score"),
            DEFAULT_SENTIMENT_SCORE,
        )
        obs_confidence = clamp_score(
            obs_agg.get("avg_observation_confidence_score"),
            DEFAULT_CONFIDENCE_SCORE,
        )
        observation_count = int(obs_agg.get("observation_count", 0))
    else:
        evidence_score = DEFAULT_EVIDENCE_SCORE
        raw_sentiment_score = DEFAULT_SENTIMENT_SCORE
        obs_confidence = DEFAULT_CONFIDENCE_SCORE
        observation_count = 0

    sentiment_score = compute_sentiment_component(
        direction=direction,
        raw_sentiment_score=raw_sentiment_score,
        has_evidence=has_evidence,
    )

    confidence_score = compute_confidence_component(
        map_confidence_score=map_confidence,
        obs_confidence_score=obs_confidence,
        has_evidence=has_evidence,
    )

    market_confirmation_score = compute_market_confirmation_score(
        map_row.get("affected_ticker"),
        direction,
    )

    transmission_score = (
        WEIGHT_EXPOSURE * exposure_score
        + WEIGHT_EVIDENCE * evidence_score
        + WEIGHT_SENTIMENT * sentiment_score
        + WEIGHT_MARKET_CONFIRMATION * market_confirmation_score
        + WEIGHT_CONFIDENCE * confidence_score
    )

    transmission_score = clamp_score(transmission_score)

    regime = classify_regime(transmission_score)

    signal_label = build_signal_label(
        direction=direction,
        score=transmission_score,
        regime=regime,
        has_evidence=has_evidence,
    )

    return {
        "exposure_score": round(exposure_score, 4),
        "evidence_score": round(evidence_score, 4),
        "sentiment_score": round(sentiment_score, 4),
        "raw_observation_sentiment_score": round(raw_sentiment_score, 4),
        "market_confirmation_score": round(market_confirmation_score, 4),
        "confidence_score": round(confidence_score, 4),
        "transmission_score": round(transmission_score, 4),
        "transmission_regime": regime,
        "signal_label": signal_label,
        "observation_count": observation_count,
        "has_evidence": has_evidence,
        "obs_agg": obs_agg or {},
    }


def classify_regime(score: float) -> str:
    """
    Must match table CHECK constraint:
    LOW, MODERATE, HIGH, EXTREME, UNCERTAIN
    """
    score = clamp_score(score)

    if score < 20:
        return "LOW"
    if score < 40:
        return "MODERATE"
    if score < 70:
        return "HIGH"

    return "EXTREME"


def build_signal_label(
    *,
    direction: str,
    score: float,
    regime: str,
    has_evidence: bool,
) -> str:
    evidence_prefix = "EVIDENCE_AWARE" if has_evidence else "STRUCTURAL_ONLY"

    if direction == "POSITIVE":
        if score >= 70:
            return f"{evidence_prefix}_STRONG_POSITIVE_TRANSMISSION"
        if score >= 50:
            return f"{evidence_prefix}_POSITIVE_TRANSMISSION"
        return f"{evidence_prefix}_WEAK_POSITIVE_TRANSMISSION"

    if direction == "NEGATIVE":
        if score >= 70:
            return f"{evidence_prefix}_STRONG_NEGATIVE_TRANSMISSION"
        if score >= 50:
            return f"{evidence_prefix}_NEGATIVE_TRANSMISSION"
        return f"{evidence_prefix}_WEAK_NEGATIVE_TRANSMISSION"

    if direction == "MIXED":
        if score >= 70:
            return f"{evidence_prefix}_STRONG_MIXED_TRANSMISSION"
        return f"{evidence_prefix}_MIXED_TRANSMISSION"

    return f"{evidence_prefix}_UNCERTAIN_TRANSMISSION_{regime}"


def build_score_rows(
    map_rows: List[Dict[str, Any]],
    obs_aggs: Dict[int, Dict[str, Any]],
    run_date_sgt: str,
) -> List[Dict[str, Any]]:
    rows = []

    for idx, map_row in enumerate(map_rows, start=1):
        map_id = int(map_row.get("id"))
        ticker = map_row.get("affected_ticker")

        logger.info(
            "Scoring %s/%s | map_id=%s | ticker=%s | direction=%s",
            idx,
            len(map_rows),
            map_id,
            ticker,
            map_row.get("transmission_direction"),
        )

        obs_agg = obs_aggs.get(map_id)
        scores = compute_score_for_row(map_row, obs_agg)

        raw_payload = {
            "source": SOURCE,
            "obs_lookback_days": OBS_LOOKBACK_DAYS,
            "observation_count": scores["observation_count"],
            "has_evidence": scores["has_evidence"],
            "raw_observation_sentiment_score": scores["raw_observation_sentiment_score"],
            "observation_aggregate": scores["obs_agg"],
            "score_weights": {
                "exposure": WEIGHT_EXPOSURE,
                "evidence": WEIGHT_EVIDENCE,
                "sentiment": WEIGHT_SENTIMENT,
                "market_confirmation": WEIGHT_MARKET_CONFIRMATION,
                "confidence": WEIGHT_CONFIDENCE,
            },
        }

        # ai_transmission_scores does not currently have raw_payload.
        # Store payload only if you later add a jsonb column.
        # For now, keep output aligned with your existing table schema.

        rows.append(
            {
                "run_date_sgt": run_date_sgt,
                "map_id": map_id,

                "ai_subsector": map_row.get("ai_subsector"),
                "affected_sector": map_row.get("affected_sector"),
                "affected_subsector": map_row.get("affected_subsector"),
                "affected_ticker": ticker,
                "affected_company": map_row.get("affected_company"),

                "transmission_direction": map_row.get("transmission_direction"),
                "transmission_type": map_row.get("transmission_type"),

                "exposure_score": scores["exposure_score"],
                "evidence_score": scores["evidence_score"],
                "sentiment_score": scores["sentiment_score"],
                "market_confirmation_score": scores["market_confirmation_score"],
                "confidence_score": scores["confidence_score"],

                "transmission_score": scores["transmission_score"],
                "transmission_regime": scores["transmission_regime"],
                "signal_label": scores["signal_label"],

                "rank_overall": None,
                "rank_sector": None,

                "source": SOURCE,
            }
        )

    add_ranks(rows)
    return rows


def add_ranks(rows: List[Dict[str, Any]]) -> None:
    sorted_overall = sorted(
        rows,
        key=lambda x: safe_float(x.get("transmission_score"), 0.0) or 0.0,
        reverse=True,
    )

    for rank, row in enumerate(sorted_overall, start=1):
        row["rank_overall"] = rank

    sector_groups: Dict[str, List[Dict[str, Any]]] = {}

    for row in rows:
        sector = row.get("affected_sector") or "UNKNOWN"
        sector_groups.setdefault(sector, []).append(row)

    for sector, sector_rows in sector_groups.items():
        sorted_sector = sorted(
            sector_rows,
            key=lambda x: safe_float(x.get("transmission_score"), 0.0) or 0.0,
            reverse=True,
        )

        for rank, row in enumerate(sorted_sector, start=1):
            row["rank_sector"] = rank


# ============================================================
# SUMMARY OUTPUT
# ============================================================

def print_summary(rows: List[Dict[str, Any]], obs_aggs: Dict[int, Dict[str, Any]]) -> None:
    if not rows:
        logger.warning("No score rows produced.")
        return

    sorted_rows = sorted(
        rows,
        key=lambda x: safe_float(x.get("transmission_score"), 0.0) or 0.0,
        reverse=True,
    )

    logger.info("========== AI TRANSMISSION SCORING V2 SUMMARY ==========")
    logger.info("Rows scored: %s", len(rows))
    logger.info("Map IDs with evidence aggregates: %s", len(obs_aggs))
    logger.info("Observation lookback days: %s", OBS_LOOKBACK_DAYS)

    logger.info("Top 10 transmission scores:")
    for row in sorted_rows[:10]:
        logger.info(
            "#%s | %s | %s | %s | score=%s | evidence=%s | sentiment=%s | %s",
            row.get("rank_overall"),
            row.get("affected_ticker") or "NO_TICKER",
            row.get("affected_company"),
            row.get("transmission_direction"),
            row.get("transmission_score"),
            row.get("evidence_score"),
            row.get("sentiment_score"),
            row.get("signal_label"),
        )

    regimes: Dict[str, int] = {}
    sources: Dict[str, int] = {}

    for row in rows:
        regime = row.get("transmission_regime") or "UNKNOWN"
        regimes[regime] = regimes.get(regime, 0) + 1

        source = row.get("source") or "UNKNOWN"
        sources[source] = sources.get(source, 0) + 1

    logger.info("Regime counts: %s", json.dumps(regimes, sort_keys=True))
    logger.info("Source counts: %s", json.dumps(sources, sort_keys=True))
    logger.info("========================================================")


# ============================================================
# MAIN
# ============================================================

def main() -> int:
    started = time.time()

    try:
        require_env()

        run_date = today_sgt_str()

        logger.info("Starting %s", PIPELINE_NAME)
        logger.info("Run date SGT: %s", run_date)
        logger.info("Observation lookback days: %s", OBS_LOOKBACK_DAYS)

        if MARKET_CONFIRMATION_ENABLED:
            logger.info("FMP_API_KEY detected. Market confirmation is enabled.")
        else:
            logger.info("FMP_API_KEY not detected. Market confirmation uses neutral score.")

        map_rows = load_active_transmission_map()

        if not map_rows:
            logger.warning("No active transmission mappings found. Nothing to score.")
            return 0

        obs_rows = load_recent_observations()
        obs_aggs = aggregate_observations(obs_rows)

        score_rows = build_score_rows(map_rows, obs_aggs, run_date)

        supabase_upsert(
            SCORES_TABLE,
            score_rows,
            on_conflict="run_date_sgt,map_id",
        )

        print_summary(score_rows, obs_aggs)

        elapsed = time.time() - started
        logger.info("%s completed successfully in %.2f seconds", PIPELINE_NAME, elapsed)

        return 0

    except Exception as exc:
        logger.exception("%s failed: %s", PIPELINE_NAME, str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
