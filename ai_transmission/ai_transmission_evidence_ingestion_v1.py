#!/usr/bin/env python3
"""
ai_transmission_evidence_ingestion_v1.py

Purpose
-------
Collect recent evidence for AI transmission mappings and write observations into:

    public.ai_transmission_observations

Reads:
    public.ai_transmission_map

Writes:
    public.ai_transmission_observations

Required environment variables
------------------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional environment variables
------------------------------
TAVILY_API_KEY
OPENAI_API_KEY
OPENAI_MODEL

Optional tuning environment variables
-------------------------------------
MAX_TRANSMISSION_MAP_ROWS          default 100
MAX_EVIDENCE_RESULTS_PER_MAP       default 3
TAVILY_SEARCH_DAYS                 default 30
SLEEP_BETWEEN_MAPS_SECONDS         default 0.5

Notes
-----
- Uses Supabase REST API only. No supabase Python package required.
- Uses Tavily for search when TAVILY_API_KEY exists.
- Uses OpenAI for evidence scoring when OPENAI_API_KEY exists.
- If OpenAI is unavailable, uses deterministic keyword fallback scoring.
- If Tavily is unavailable, writes diagnostic NO_EVIDENCE_FOUND rows so coverage is visible.
"""

from __future__ import annotations

import os
import re
import sys
import json
import time
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import requests


# ============================================================
# CONFIG
# ============================================================

PIPELINE_NAME = "AI_TRANSMISSION_EVIDENCE_INGESTION_V1"
SOURCE = "PYTHON_TRANSMISSION_EVIDENCE_V1"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAP_TABLE = "ai_transmission_map"
OBS_TABLE = "ai_transmission_observations"

REQUEST_TIMEOUT = 45
MAX_RETRIES = 3
RETRY_SLEEP_SECONDS = 2

MAX_MAP_ROWS = int(os.getenv("MAX_TRANSMISSION_MAP_ROWS", "100"))
MAX_RESULTS_PER_MAP = int(os.getenv("MAX_EVIDENCE_RESULTS_PER_MAP", "3"))
TAVILY_SEARCH_DAYS = int(os.getenv("TAVILY_SEARCH_DAYS", "30"))
SLEEP_BETWEEN_MAPS_SECONDS = float(os.getenv("SLEEP_BETWEEN_MAPS_SECONDS", "0.5"))

DEFAULT_AI_RELEVANCE_SCORE = 50.0
DEFAULT_IMPACT_MAGNITUDE_SCORE = 50.0
DEFAULT_SENTIMENT_SCORE = 50.0
DEFAULT_CONFIDENCE_SCORE = 50.0


# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(PIPELINE_NAME)


# ============================================================
# HELPERS
# ============================================================

def now_sgt() -> datetime:
    return datetime.now(timezone.utc) + timedelta(hours=8)


def today_sgt_str() -> str:
    return now_sgt().date().isoformat()


def utc_iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def require_env() -> None:
    missing = []
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_SERVICE_ROLE_KEY")
    if missing:
        raise RuntimeError("Missing required environment variable(s): " + ", ".join(missing))


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


def clean_text(value: Any, max_len: int = 4000) -> str:
    if value is None:
        return ""
    text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_len:
        text = text[: max_len - 3].rstrip() + "..."
    return text


def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
    timeout: int = REQUEST_TIMEOUT,
) -> requests.Response:
    last_error: Optional[Exception] = None

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
                raise RuntimeError(f"Transient HTTP {response.status_code}: {response.text[:300]}")

            return response

        except Exception as exc:
            last_error = exc
            logger.warning("Request failed attempt %s/%s: %s", attempt, MAX_RETRIES, str(exc))
            if attempt < MAX_RETRIES:
                time.sleep(RETRY_SLEEP_SECONDS * attempt)

    raise RuntimeError(f"Request failed after retries: {last_error}")


# ============================================================
# SUPABASE REST
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


def supabase_select(table: str, *, select: str = "*", params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    query_params = {"select": select}
    if params:
        query_params.update(params)

    response = request_with_retries("GET", url, headers=supabase_headers(), params=query_params)

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase SELECT failed for {table}: HTTP {response.status_code} - {response.text}"
        )

    return response.json()


def supabase_insert(table: str, rows: List[Dict[str, Any]]) -> None:
    if not rows:
        logger.info("No rows to insert into %s", table)
        return

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = request_with_retries(
        "POST",
        url,
        headers=supabase_headers(prefer="return=minimal"),
        json_body=rows,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase INSERT failed for {table}: HTTP {response.status_code} - {response.text}"
        )

    logger.info("Inserted %s row(s) into %s", len(rows), table)


# ============================================================
# DATA LOADERS
# ============================================================

def load_active_transmission_map() -> List[Dict[str, Any]]:
    logger.info("Loading active transmission map rows")

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
            "exposure_description,"
            "transmission_thesis,"
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

    logger.info("Loaded %s active transmission map row(s)", len(rows))
    return rows


# ============================================================
# SEARCH QUERY BUILDER
# ============================================================

def build_search_query(row: Dict[str, Any]) -> str:
    ai_subsector = clean_text(row.get("ai_subsector"), 80).replace("_", " ")
    affected_sector = clean_text(row.get("affected_sector"), 80).replace("_", " ")
    affected_subsector = clean_text(row.get("affected_subsector"), 80).replace("_", " ")
    ticker = clean_text(row.get("affected_ticker"), 20)
    company = clean_text(row.get("affected_company"), 120)
    direction = clean_text(row.get("transmission_direction"), 40)
    thesis = clean_text(row.get("transmission_thesis"), 220)

    target = company or ticker or affected_subsector or affected_sector

    if direction == "POSITIVE":
        impact_terms = "benefit revenue demand growth investment capex"
    elif direction == "NEGATIVE":
        impact_terms = "risk disruption automation pressure demand decline margin pressure"
    else:
        impact_terms = "impact transformation adoption productivity disruption"

    query = (
        f"{target} AI {ai_subsector} {affected_sector} {affected_subsector} "
        f"{impact_terms} {thesis}"
    )

    return clean_text(query, 450)


# ============================================================
# TAVILY SEARCH
# ============================================================

def tavily_search(query: str) -> List[Dict[str, Any]]:
    if not TAVILY_API_KEY:
        logger.warning("TAVILY_API_KEY not set. Evidence search will be skipped.")
        return []

    url = "https://api.tavily.com/search"

    payload = {
        "api_key": TAVILY_API_KEY,
        "query": query,
        "search_depth": "advanced",
        "topic": "news",
        "days": TAVILY_SEARCH_DAYS,
        "max_results": MAX_RESULTS_PER_MAP,
        "include_answer": False,
        "include_raw_content": False,
    }

    response = request_with_retries(
        "POST",
        url,
        headers={"Content-Type": "application/json"},
        json_body=payload,
    )

    if response.status_code >= 400:
        logger.warning("Tavily search failed: HTTP %s - %s", response.status_code, response.text[:500])
        return []

    payload = response.json()
    results = payload.get("results", [])

    if not isinstance(results, list):
        return []

    cleaned = []
    for item in results:
        cleaned.append(
            {
                "title": clean_text(item.get("title"), 500),
                "url": clean_text(item.get("url"), 1000),
                "content": clean_text(item.get("content"), 3000),
                "score": safe_float(item.get("score"), None),
                "raw": item,
            }
        )

    return cleaned


# ============================================================
# OPENAI SCORING
# ============================================================

def extract_json_from_text(text: str) -> Dict[str, Any]:
    if not text:
        return {}

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if not match:
        return {}

    try:
        return json.loads(match.group(0))
    except Exception:
        return {}


def openai_score_evidence(row: Dict[str, Any], result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if not OPENAI_API_KEY:
        return None

    url = "https://api.openai.com/v1/chat/completions"

    title = clean_text(result.get("title"), 500)
    content = clean_text(result.get("content"), 2500)
    evidence_url = clean_text(result.get("url"), 1000)

    context = {
        "ai_subsector": row.get("ai_subsector"),
        "affected_sector": row.get("affected_sector"),
        "affected_subsector": row.get("affected_subsector"),
        "affected_ticker": row.get("affected_ticker"),
        "affected_company": row.get("affected_company"),
        "transmission_direction": row.get("transmission_direction"),
        "transmission_type": row.get("transmission_type"),
        "exposure_description": row.get("exposure_description"),
        "transmission_thesis": row.get("transmission_thesis"),
        "evidence_title": title,
        "evidence_url": evidence_url,
        "evidence_content": content,
    }

    system_prompt = (
        "You are an investment research scoring assistant. "
        "Score whether a piece of evidence supports an AI transmission thesis. "
        "Return JSON only. No markdown."
    )

    user_prompt = f"""
Evaluate the evidence against the AI transmission thesis.

Scoring definitions:
- ai_relevance_score: 0-100. How directly the evidence relates to AI.
- impact_magnitude_score: 0-100. How material the evidence appears for the affected sector/company.
- sentiment_score: 0-100. For the affected company/sector, 0 is very negative, 50 neutral, 100 very positive.
- confidence_score: 0-100. Confidence that the evidence supports the stated transmission thesis.

Also produce a concise evidence_summary in one sentence.

Return strict JSON with exactly these keys:
{{
  "ai_relevance_score": number,
  "impact_magnitude_score": number,
  "sentiment_score": number,
  "confidence_score": number,
  "evidence_summary": "string"
}}

Context:
{json.dumps(context, ensure_ascii=False)}
""".strip()

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.1,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    response = request_with_retries(
        "POST",
        url,
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json",
        },
        json_body=payload,
    )

    if response.status_code >= 400:
        logger.warning("OpenAI scoring failed: HTTP %s - %s", response.status_code, response.text[:500])
        return None

    payload = response.json()
    content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
    parsed = extract_json_from_text(content)

    if not parsed:
        return None

    return {
        "ai_relevance_score": clamp_score(parsed.get("ai_relevance_score"), DEFAULT_AI_RELEVANCE_SCORE),
        "impact_magnitude_score": clamp_score(parsed.get("impact_magnitude_score"), DEFAULT_IMPACT_MAGNITUDE_SCORE),
        "sentiment_score": clamp_score(parsed.get("sentiment_score"), DEFAULT_SENTIMENT_SCORE),
        "confidence_score": clamp_score(parsed.get("confidence_score"), DEFAULT_CONFIDENCE_SCORE),
        "evidence_summary": clean_text(parsed.get("evidence_summary"), 1200),
        "model_used": OPENAI_MODEL,
    }


# ============================================================
# FALLBACK SCORING
# ============================================================

def fallback_score_evidence(row: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    title = clean_text(result.get("title"), 500)
    content = clean_text(result.get("content"), 3000)
    combined = f" {title} {content} ".lower()

    ai_keywords = [
        "artificial intelligence",
        " ai ",
        "generative ai",
        "genai",
        "machine learning",
        "large language model",
        "llm",
        "gpu",
        "data center",
        "datacenter",
        "automation",
        "cloud ai",
    ]

    positive_keywords = [
        "benefit",
        "growth",
        "demand",
        "opportunity",
        "investment",
        "expansion",
        "boost",
        "productivity",
        "revenue",
        "capex",
    ]

    negative_keywords = [
        "risk",
        "pressure",
        "decline",
        "disruption",
        "automation risk",
        "replace",
        "margin pressure",
        "job cuts",
        "weakness",
        "threat",
    ]

    ai_hits = sum(1 for kw in ai_keywords if kw in combined)
    pos_hits = sum(1 for kw in positive_keywords if kw in combined)
    neg_hits = sum(1 for kw in negative_keywords if kw in combined)

    ai_relevance_score = clamp_score(35 + ai_hits * 12, DEFAULT_AI_RELEVANCE_SCORE)
    impact_magnitude_score = clamp_score(40 + (pos_hits + neg_hits) * 6, DEFAULT_IMPACT_MAGNITUDE_SCORE)

    direction = row.get("transmission_direction")

    if direction == "POSITIVE":
        sentiment_score = 50 + pos_hits * 7 - neg_hits * 5
    elif direction == "NEGATIVE":
        sentiment_score = 50 - neg_hits * 7 + pos_hits * 4
    else:
        sentiment_score = 50 + pos_hits * 4 - neg_hits * 4

    confidence_score = 40
    if title:
        confidence_score += 10
    if content:
        confidence_score += 10
    if ai_hits:
        confidence_score += min(25, ai_hits * 8)
    if result.get("score") is not None:
        confidence_score += 5

    return {
        "ai_relevance_score": clamp_score(ai_relevance_score, DEFAULT_AI_RELEVANCE_SCORE),
        "impact_magnitude_score": clamp_score(impact_magnitude_score, DEFAULT_IMPACT_MAGNITUDE_SCORE),
        "sentiment_score": clamp_score(sentiment_score, DEFAULT_SENTIMENT_SCORE),
        "confidence_score": clamp_score(confidence_score, DEFAULT_CONFIDENCE_SCORE),
        "evidence_summary": clean_text(content or title, 1200),
        "model_used": "fallback_keyword_v1",
    }


# ============================================================
# OBSERVATION BUILDERS
# ============================================================

def build_observation_row(
    *,
    run_date_sgt: str,
    map_row: Dict[str, Any],
    result: Dict[str, Any],
    scored: Dict[str, Any],
    search_query: str,
) -> Dict[str, Any]:
    raw_payload = {
        "source": SOURCE,
        "search_query": search_query,
        "ingested_at_utc": utc_iso_now(),
        "tavily_score": result.get("score"),
        "model_used": scored.get("model_used"),
        "raw_result": result.get("raw"),
    }

    return {
        "run_date_sgt": run_date_sgt,
        "map_id": map_row.get("id"),
        "affected_ticker": map_row.get("affected_ticker"),
        "affected_company": map_row.get("affected_company"),
        "evidence_source": "TAVILY_NEWS" if TAVILY_API_KEY else "NO_SEARCH_PROVIDER",
        "evidence_title": clean_text(result.get("title"), 500),
        "evidence_url": clean_text(result.get("url"), 1000),
        "evidence_summary": clean_text(scored.get("evidence_summary"), 1200),
        "ai_relevance_score": clamp_score(scored.get("ai_relevance_score"), DEFAULT_AI_RELEVANCE_SCORE),
        "impact_magnitude_score": clamp_score(scored.get("impact_magnitude_score"), DEFAULT_IMPACT_MAGNITUDE_SCORE),
        "sentiment_score": clamp_score(scored.get("sentiment_score"), DEFAULT_SENTIMENT_SCORE),
        "confidence_score": clamp_score(scored.get("confidence_score"), DEFAULT_CONFIDENCE_SCORE),
        "raw_payload": raw_payload,
    }


def build_no_evidence_observation(
    *,
    run_date_sgt: str,
    map_row: Dict[str, Any],
    search_query: str,
) -> Dict[str, Any]:
    raw_payload = {
        "source": SOURCE,
        "search_query": search_query,
        "ingested_at_utc": utc_iso_now(),
        "note": "No evidence found or search provider unavailable.",
    }

    return {
        "run_date_sgt": run_date_sgt,
        "map_id": map_row.get("id"),
        "affected_ticker": map_row.get("affected_ticker"),
        "affected_company": map_row.get("affected_company"),
        "evidence_source": "NO_EVIDENCE_FOUND",
        "evidence_title": None,
        "evidence_url": None,
        "evidence_summary": "No recent evidence found for this mapping in the current ingestion run.",
        "ai_relevance_score": 0,
        "impact_magnitude_score": 0,
        "sentiment_score": 50,
        "confidence_score": 0,
        "raw_payload": raw_payload,
    }


# ============================================================
# MAIN INGESTION LOGIC
# ============================================================

def process_map_row(map_row: Dict[str, Any], run_date_sgt: str) -> List[Dict[str, Any]]:
    map_id = map_row.get("id")
    ticker = map_row.get("affected_ticker")
    company = map_row.get("affected_company")
    direction = map_row.get("transmission_direction")

    search_query = build_search_query(map_row)

    logger.info(
        "Processing map_id=%s | ticker=%s | company=%s | direction=%s",
        map_id,
        ticker,
        company,
        direction,
    )

    results = tavily_search(search_query)
    observations: List[Dict[str, Any]] = []

    if not results:
        logger.warning("No evidence found for map_id=%s", map_id)
        observations.append(
            build_no_evidence_observation(
                run_date_sgt=run_date_sgt,
                map_row=map_row,
                search_query=search_query,
            )
        )
        return observations

    for result in results:
        scored = openai_score_evidence(map_row, result)
        if scored is None:
            scored = fallback_score_evidence(map_row, result)

        observation = build_observation_row(
            run_date_sgt=run_date_sgt,
            map_row=map_row,
            result=result,
            scored=scored,
            search_query=search_query,
        )
        observations.append(observation)

    return observations


def print_summary(rows: List[Dict[str, Any]]) -> None:
    logger.info("========== AI TRANSMISSION EVIDENCE SUMMARY ==========")
    logger.info("Observation rows created: %s", len(rows))

    if not rows:
        logger.info("No observations created.")
        logger.info("======================================================")
        return

    source_counts: Dict[str, int] = {}
    for row in rows:
        source = row.get("evidence_source") or "UNKNOWN"
        source_counts[source] = source_counts.get(source, 0) + 1

    logger.info("Evidence source counts: %s", json.dumps(source_counts, sort_keys=True))

    scored_rows = [
        r for r in rows
        if safe_float(r.get("confidence_score"), 0) and safe_float(r.get("confidence_score"), 0) > 0
    ]

    if scored_rows:
        avg_ai = sum(float(r["ai_relevance_score"]) for r in scored_rows) / len(scored_rows)
        avg_impact = sum(float(r["impact_magnitude_score"]) for r in scored_rows) / len(scored_rows)
        avg_sentiment = sum(float(r["sentiment_score"]) for r in scored_rows) / len(scored_rows)
        avg_conf = sum(float(r["confidence_score"]) for r in scored_rows) / len(scored_rows)

        logger.info("Average AI relevance: %.2f", avg_ai)
        logger.info("Average impact magnitude: %.2f", avg_impact)
        logger.info("Average sentiment: %.2f", avg_sentiment)
        logger.info("Average confidence: %.2f", avg_conf)

    logger.info("======================================================")


def main() -> int:
    started = time.time()

    try:
        require_env()
        run_date = today_sgt_str()

        logger.info("Starting %s", PIPELINE_NAME)
        logger.info("Run date SGT: %s", run_date)

        if TAVILY_API_KEY:
            logger.info("TAVILY_API_KEY detected. Evidence search enabled.")
        else:
            logger.warning("TAVILY_API_KEY missing. Search will be skipped.")

        if OPENAI_API_KEY:
            logger.info("OPENAI_API_KEY detected. OpenAI evidence scoring enabled.")
            logger.info("OPENAI_MODEL: %s", OPENAI_MODEL)
        else:
            logger.warning("OPENAI_API_KEY missing. Using fallback keyword scoring.")

        map_rows = load_active_transmission_map()

        if not map_rows:
            logger.warning("No active map rows found. Nothing to ingest.")
            return 0

        all_observations: List[Dict[str, Any]] = []

        for idx, map_row in enumerate(map_rows, start=1):
            logger.info("Map row %s/%s", idx, len(map_rows))
            observations = process_map_row(map_row, run_date)
            all_observations.extend(observations)

            if SLEEP_BETWEEN_MAPS_SECONDS > 0 and idx < len(map_rows):
                time.sleep(SLEEP_BETWEEN_MAPS_SECONDS)

        supabase_insert(OBS_TABLE, all_observations)
        print_summary(all_observations)

        elapsed = time.time() - started
        logger.info("%s completed successfully in %.2f seconds", PIPELINE_NAME, elapsed)
        return 0

    except Exception as exc:
        logger.exception("%s failed: %s", PIPELINE_NAME, str(exc))
        return 1


if __name__ == "__main__":
    sys.exit(main())
