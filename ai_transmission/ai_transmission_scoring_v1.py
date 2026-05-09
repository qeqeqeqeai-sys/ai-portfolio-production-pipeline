#!/usr/bin/env python3
"""
ai_transmission_scoring_v1.py

Revision
--------
2026-05-10: Updated FMP market confirmation to use stable historical-price-eod/light endpoint.

Purpose
-------
Build v1 AI transmission scores from ai_transmission_map and write results into
public.ai_transmission_scores using Supabase REST API.

This v1 is intentionally explainable and production-safe:

    ai_transmission_map
        -> structural transmission prior
        -> optional market confirmation
        -> optional evidence/sentiment placeholders
        -> ai_transmission_scores

Designed for:
- GitHub Actions
- Supabase REST API
- No supabase Python package required
- Daily production pipeline use

Required environment variables
------------------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional environment variables
------------------------------
FMP_API_KEY

Notes
-----
This v1 does NOT require Tavily/OpenAI/HuggingFace yet.
It leaves evidence/sentiment as neutral placeholders unless you later extend them.
"""

import os
import sys
import math
import time
import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests


# ============================================================
# CONFIG
# ============================================================

PIPELINE_NAME = "AI_TRANSMISSION_SCORING_V1"
SOURCE = "PYTHON_TRANSMISSION_V1"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
FMP_API_KEY = os.getenv("FMP_API_KEY", "")

MAP_TABLE = "ai_transmission_map"
SCORES_TABLE = "ai_transmission_scores"

REQUEST_TIMEOUT = 30
MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 2

# Scoring weights
WEIGHT_BASE_STRENGTH = 0.30
WEIGHT_EVIDENCE = 0.25
WEIGHT_SENTIMENT = 0.20
WEIGHT_MARKET_CONFIRMATION = 0.15
WEIGHT_CONFIDENCE = 0.10

# Neutral defaults
DEFAULT_EVIDENCE_SCORE = 50.0
DEFAULT_SENTIMENT_SCORE = 50.0
DEFAULT_MARKET_CONFIRMATION_SCORE = 50.0
DEFAULT_CONFIDENCE_SCORE = 50.0

# Market confirmation parameters
PRICE_LOOKBACK_DAYS = 20
MARKET_CONFIRMATION_ENABLED = bool(FMP_API_KEY)


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
    """Return current Singapore time."""
    return datetime.now(timezone.utc) + timedelta(hours=8)


def today_sgt_str() -> str:
    """Return today's date in Singapore timezone as YYYY-MM-DD."""
    return now_sgt().date().isoformat()


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


def clamp_score(value: Optional[float], default: float = 50.0) -> float:
    """Clamp numeric score to 0-100."""
    if value is None:
        return default

    try:
        value = float(value)
    except Exception:
        return default

    if math.isnan(value) or math.isinf(value):
        return default

    return max(0.0, min(100.0, value))


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


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout: int = REQUEST_TIMEOUT,
) -> requests.Response:
    """HTTP request wrapper with basic retries."""
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
        },
    )

    logger.info("Loaded %s active transmission mapping row(s)", len(rows))
    return rows


# ============================================================
# MARKET CONFIRMATION
# ============================================================

def fetch_fmp_historical_prices(
    ticker: str,
    *,
    lookback_days: int = PRICE_LOOKBACK_DAYS + 10,
) -> List[Dict[str, Any]]:
    """
    Fetch recent daily prices from the current FMP stable endpoint.

    Uses:
        https://financialmodelingprep.com/stable/historical-price-eod/light

    This replaces the legacy endpoint:
        /api/v3/historical-price-full/{symbol}

    Returns recent prices sorted ascending by date.
    Expected FMP stable light response shape is usually a list of rows:
        [
            {"symbol": "AAPL", "date": "2026-05-08", "price": 123.45, "volume": 123456},
            ...
        ]

    The parser is defensive and also accepts dict payloads containing
    historical/data/results arrays, because FMP response shapes can vary by plan.
    """
    if not FMP_API_KEY:
        return []

    if not ticker:
        return []

    symbol = ticker.strip().upper()

    # Pull a slightly wider calendar window because weekends/holidays reduce trading days.
    to_date = datetime.utcnow().date()
    from_date = to_date - timedelta(days=max(45, lookback_days * 3))

    url = "https://financialmodelingprep.com/stable/historical-price-eod/light"

    params = {
        "symbol": symbol,
        "from": from_date.isoformat(),
        "to": to_date.isoformat(),
        "apikey": FMP_API_KEY,
    }

    response = request_with_retries("GET", url, params=params)

    if response.status_code >= 400:
        logger.warning(
            "FMP stable historical price failed for %s: HTTP %s - %s",
            symbol,
            response.status_code,
            response.text[:300],
        )
        return []

    try:
        payload = response.json()
    except Exception as exc:
        logger.warning("FMP response for %s was not valid JSON: %s", symbol, exc)
        return []

    historical: Any

    if isinstance(payload, list):
        historical = payload
    elif isinstance(payload, dict):
        historical = (
            payload.get("historical")
            or payload.get("data")
            or payload.get("results")
            or []
        )
    else:
        historical = []

    if not isinstance(historical, list):
        logger.warning("Unexpected FMP payload shape for %s. Using neutral score.", symbol)
        return []

    clean: List[Dict[str, Any]] = []

    for row in historical:
        if not isinstance(row, dict):
            continue

        # stable light commonly uses price. stable full may use close/adjClose.
        close = (
            safe_float(row.get("price"))
            or safe_float(row.get("close"))
            or safe_float(row.get("adjClose"))
            or safe_float(row.get("adj_close"))
        )
        volume = safe_float(row.get("volume"))
        date = row.get("date")

        if date and close is not None:
            clean.append(
                {
                    "date": str(date),
                    "close": close,
                    "volume": volume,
                }
            )

    clean.sort(key=lambda x: x["date"])

    # Keep only the latest N trading rows to avoid old data affecting confirmation.
    if len(clean) > lookback_days:
        clean = clean[-lookback_days:]

    return clean


def compute_market_confirmation_score(
    ticker: Optional[str],
    direction: str,
) -> float:
    """
    Convert simple price/volume behaviour into a 0-100 confirmation score.

    Logic:
    - Positive transmission: rising price trend confirms thesis.
    - Negative transmission: falling price trend confirms thesis.
    - Mixed/uncertain: neutral by default.
    """
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
        safe_float(x.get("volume")) for x in prices if safe_float(x.get("volume")) is not None
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

    # Convert direction-adjusted return into score
    if direction == "POSITIVE":
        directional_return = return_pct
    elif direction == "NEGATIVE":
        directional_return = -return_pct
    else:
        directional_return = 0.0

    # 0% directional return = 50
    # +10% directional return roughly = 75
    # -10% directional return roughly = 25
    score = 50.0 + (directional_return * 2.5) + volume_boost

    return clamp_score(score, DEFAULT_MARKET_CONFIRMATION_SCORE)


# ============================================================
# EVIDENCE + SENTIMENT PLACEHOLDERS
# ============================================================

def compute_evidence_score(row: Dict[str, Any]) -> float:
    """
    v1 placeholder.

    Later extension:
    - Pull recent AI-related headlines
    - Count source evidence
    - Score evidence quality
    - Write raw evidence into ai_transmission_observations
    """
    return DEFAULT_EVIDENCE_SCORE


def compute_sentiment_score(row: Dict[str, Any]) -> float:
    """
    v1 placeholder.

    Later extension:
    - Apply FinBERT/HuggingFace/OpenAI sentiment to evidence summaries
    """
    direction = row.get("transmission_direction")

    # Keep MIXED/UNCERTAIN neutral.
    if direction in ("MIXED", "UNCERTAIN"):
        return DEFAULT_SENTIMENT_SCORE

    return DEFAULT_SENTIMENT_SCORE


# ============================================================
# SCORING LOGIC
# ============================================================

def compute_transmission_score(row: Dict[str, Any]) -> Dict[str, Any]:
    base_strength_score = clamp_score(
        safe_float(row.get("base_strength_score")),
        default=DEFAULT_EVIDENCE_SCORE,
    )

    evidence_score = compute_evidence_score(row)
    sentiment_score = compute_sentiment_score(row)

    market_confirmation_score = compute_market_confirmation_score(
        row.get("affected_ticker"),
        row.get("transmission_direction"),
    )

    confidence_score = clamp_score(
        safe_float(row.get("confidence_score")),
        default=DEFAULT_CONFIDENCE_SCORE,
    )

    transmission_score = (
        WEIGHT_BASE_STRENGTH * base_strength_score
        + WEIGHT_EVIDENCE * evidence_score
        + WEIGHT_SENTIMENT * sentiment_score
        + WEIGHT_MARKET_CONFIRMATION * market_confirmation_score
        + WEIGHT_CONFIDENCE * confidence_score
    )

    transmission_score = clamp_score(transmission_score)

    regime = classify_regime(transmission_score)
    signal_label = build_signal_label(
        direction=row.get("transmission_direction"),
        score=transmission_score,
        regime=regime,
    )

    return {
        "exposure_score": round(base_strength_score, 4),
        "evidence_score": round(evidence_score, 4),
        "sentiment_score": round(sentiment_score, 4),
        "market_confirmation_score": round(market_confirmation_score, 4),
        "confidence_score": round(confidence_score, 4),
        "transmission_score": round(transmission_score, 4),
        "transmission_regime": regime,
        "signal_label": signal_label,
    }


def classify_regime(score: float) -> str:
    """
    Must match table CHECK constraint:
    LOW, MODERATE, HIGH, EXTREME, UNCERTAIN

    Note:
    The earlier suggested VERY_HIGH label is intentionally folded into EXTREME
    unless you alter your table constraint.
    """
    score = clamp_score(score)

    if score < 20:
        return "LOW"
    if score < 40:
        return "MODERATE"
    if score < 70:
        return "HIGH"

    return "EXTREME"


def build_signal_label(direction: Optional[str], score: float, regime: str) -> str:
    direction = direction or "UNCERTAIN"

    if direction == "POSITIVE":
        if score >= 70:
            return "STRONG_POSITIVE_TRANSMISSION"
        if score >= 50:
            return "POSITIVE_TRANSMISSION"
        return "WEAK_POSITIVE_TRANSMISSION"

    if direction == "NEGATIVE":
        if score >= 70:
            return "STRONG_NEGATIVE_TRANSMISSION"
        if score >= 50:
            return "NEGATIVE_TRANSMISSION"
        return "WEAK_NEGATIVE_TRANSMISSION"

    if direction == "MIXED":
        if score >= 70:
            return "STRONG_MIXED_TRANSMISSION"
        return "MIXED_TRANSMISSION"

    return f"UNCERTAIN_TRANSMISSION_{regime}"


def build_score_rows(
    map_rows: List[Dict[str, Any]],
    run_date_sgt: str,
) -> List[Dict[str, Any]]:
    rows = []

    for idx, row in enumerate(map_rows, start=1):
        map_id = row.get("id")
        ticker = row.get("affected_ticker")

        logger.info(
            "Scoring %s/%s | map_id=%s | ticker=%s | direction=%s",
            idx,
            len(map_rows),
            map_id,
            ticker,
            row.get("transmission_direction"),
        )

        scores = compute_transmission_score(row)

        rows.append(
            {
                "run_date_sgt": run_date_sgt,
                "map_id": map_id,

                "ai_subsector": row.get("ai_subsector"),
                "affected_sector": row.get("affected_sector"),
                "affected_subsector": row.get("affected_subsector"),
                "affected_ticker": ticker,
                "affected_company": row.get("affected_company"),

                "transmission_direction": row.get("transmission_direction"),
                "transmission_type": row.get("transmission_type"),

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
    """Mutate rows in place with overall and sector ranks."""
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

def print_summary(rows: List[Dict[str, Any]]) -> None:
    if not rows:
        logger.warning("No score rows produced.")
        return

    sorted_rows = sorted(
        rows,
        key=lambda x: safe_float(x.get("transmission_score"), 0.0) or 0.0,
        reverse=True,
    )

    logger.info("========== AI TRANSMISSION SCORING SUMMARY ==========")
    logger.info("Rows scored: %s", len(rows))

    logger.info("Top 10 transmission scores:")
    for row in sorted_rows[:10]:
        logger.info(
            "#%s | %s | %s | %s | score=%s | %s",
            row.get("rank_overall"),
            row.get("affected_ticker") or "NO_TICKER",
            row.get("affected_company"),
            row.get("transmission_direction"),
            row.get("transmission_score"),
            row.get("signal_label"),
        )

    regimes: Dict[str, int] = {}
    for row in rows:
        regime = row.get("transmission_regime") or "UNKNOWN"
        regimes[regime] = regimes.get(regime, 0) + 1

    logger.info("Regime counts: %s", json.dumps(regimes, sort_keys=True))
    logger.info("=====================================================")


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

        if MARKET_CONFIRMATION_ENABLED:
            logger.info("FMP_API_KEY detected. Market confirmation is enabled.")
        else:
            logger.info("FMP_API_KEY not detected. Market confirmation uses neutral score.")

        map_rows = load_active_transmission_map()

        if not map_rows:
            logger.warning("No active transmission mappings found. Nothing to score.")
            return 0

        score_rows = build_score_rows(map_rows, run_date)

        supabase_upsert(
            SCORES_TABLE,
            score_rows,
            on_conflict="run_date_sgt,map_id",
        )

        print_summary(score_rows)

        elapsed = time.time() - started
        logger.info("%s completed successfully in %.2f seconds", PIPELINE_NAME, elapsed)

        return 0

    except Exception as exc:
        logger.exception("%s failed: %s", PIPELINE_NAME, str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
