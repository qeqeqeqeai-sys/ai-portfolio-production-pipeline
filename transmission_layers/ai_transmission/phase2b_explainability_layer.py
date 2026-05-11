#!/usr/bin/env python3
"""
phase2b_explainability_layer.py

Purpose
-------
Phase 2B explainability layer for the AI Transmission platform.

Reads:
    public.ai_transmission_scores
    public.ai_transmission_observations
    public.ai_transmission_map
    public.structural_theme_scores

Writes:
    public.structural_theme_component_scores
    public.structural_theme_evidence_attribution
    public.structural_theme_explanations
    optionally patches public.structural_theme_scores explainability jsonb fields

Design
------
This is intentionally additive and low-risk:
- It does NOT replace your existing scoring engine.
- It runs AFTER ai_transmission_scoring_v2_phase1_refactor_built.py.
- It uses Supabase REST API only.
- It preserves legacy ai_transmission_scores and Phase 1 dual-write.

Required environment variables
------------------------------
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY

Optional environment variables
------------------------------
STRUCTURAL_THEME_NAME=ai
THEME_VERSION=v1
RUN_DATE_SGT=YYYY-MM-DD
PATCH_STRUCTURAL_THEME_SCORES=true
"""

from __future__ import annotations

import os
import sys
import json
import time
import math
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests


# ============================================================
# CONFIG
# ============================================================

PIPELINE_NAME = "AI_TRANSMISSION_PHASE2B_EXPLAINABILITY"
EXPLAINABILITY_VERSION = "phase2b_v1"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "") or os.getenv("SUPABASE_KEY", "")

THEME_NAME = os.getenv("STRUCTURAL_THEME_NAME", os.getenv("THEME_NAME", "ai"))
THEME_VERSION = os.getenv("THEME_VERSION", "v1")
RUN_DATE_SGT = os.getenv("RUN_DATE_SGT", "").strip()

PATCH_STRUCTURAL_THEME_SCORES = (
    os.getenv("PATCH_STRUCTURAL_THEME_SCORES", "true").strip().lower()
    not in ("0", "false", "no", "off")
)

REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "45"))
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "3"))
RETRY_SLEEP_SECONDS = int(os.getenv("RETRY_SLEEP_SECONDS", "2"))

# Must match your current scoring engine weights.
WEIGHT_EXPOSURE = 0.30
WEIGHT_EVIDENCE = 0.25
WEIGHT_SENTIMENT = 0.20
WEIGHT_MARKET_CONFIRMATION = 0.15
WEIGHT_CONFIDENCE = 0.10

# Evidence quality subweights. These mirror the observation scoring philosophy.
WEIGHT_OBS_AI_RELEVANCE = 0.40
WEIGHT_OBS_IMPACT = 0.30
WEIGHT_OBS_CONFIDENCE = 0.20
WEIGHT_OBS_DIRECTIONAL_SENTIMENT = 0.10

DEFAULT_SCORE = 50.0

COMPONENT_TABLE = "structural_theme_component_scores"
ATTRIBUTION_TABLE = "structural_theme_evidence_attribution"
EXPLANATION_TABLE = "structural_theme_explanations"
STRUCTURAL_SCORES_TABLE = "structural_theme_scores"
LEGACY_SCORES_TABLE = "ai_transmission_scores"
OBS_TABLE = "ai_transmission_observations"
MAP_TABLE = "ai_transmission_map"
RUNS_TABLE = "structural_theme_runs"


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


def now_sgt_iso() -> str:
    return now_sgt().isoformat()


def today_sgt_str() -> str:
    return now_sgt().date().isoformat()


def run_date_sgt() -> str:
    return RUN_DATE_SGT or today_sgt_str()


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
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    if value is None:
        return default
    try:
        f = float(value)
        if math.isnan(f) or math.isinf(f):
            return default
        return f
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(value)
    except Exception:
        return default


def clamp_score(value: Any, default: float = DEFAULT_SCORE) -> float:
    f = safe_float(value, default)
    if f is None:
        f = default
    return max(0.0, min(100.0, f))


def compact_text(value: Any, max_len: int = 220) -> str:
    if value is None:
        return ""
    text = " ".join(str(value).split())
    if len(text) <= max_len:
        return text
    return text[: max_len - 3] + "..."


def direction_sign(direction: Optional[str]) -> int:
    d = str(direction or "").upper()
    if d == "POSITIVE":
        return 1
    if d == "NEGATIVE":
        return -1
    return 0


def contribution_direction(direction: Optional[str]) -> str:
    sign = direction_sign(direction)
    if sign > 0:
        return "POSITIVE"
    if sign < 0:
        return "NEGATIVE"
    return "MIXED_OR_UNCERTAIN"


def direction_adjusted_sentiment(raw_sentiment: Any, direction: Optional[str]) -> float:
    raw = clamp_score(raw_sentiment, DEFAULT_SCORE)
    d = str(direction or "").upper()

    if d == "POSITIVE":
        return raw
    if d == "NEGATIVE":
        return clamp_score(100.0 - raw, DEFAULT_SCORE)

    # Same logic style as scoring engine: compress mixed/uncertain toward neutral.
    return clamp_score(50.0 + ((raw - 50.0) * 0.50), DEFAULT_SCORE)


def build_pathway(score_row: Dict[str, Any]) -> str:
    parts = [
        score_row.get("ai_subsector"),
        score_row.get("affected_sector"),
        score_row.get("affected_subsector"),
        score_row.get("affected_ticker"),
    ]
    clean = [str(p).strip() for p in parts if p]
    return " -> ".join(clean)


def github_metadata() -> Dict[str, Optional[str]]:
    return {
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
    }


# ============================================================
# HTTP / SUPABASE REST HELPERS
# ============================================================

def request_with_retries(
    method: str,
    url: str,
    *,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_body: Optional[Any] = None,
) -> requests.Response:
    last_exc: Optional[Exception] = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                timeout=REQUEST_TIMEOUT,
            )

            if response.status_code < 500:
                return response

            logger.warning(
                "HTTP %s attempt %s/%s returned %s for %s",
                method,
                attempt,
                MAX_RETRIES,
                response.status_code,
                url,
            )

        except Exception as exc:
            last_exc = exc
            logger.warning(
                "HTTP %s attempt %s/%s failed for %s: %s",
                method,
                attempt,
                MAX_RETRIES,
                url,
                exc,
            )

        if attempt < MAX_RETRIES:
            time.sleep(RETRY_SLEEP_SECONDS * attempt)

    if last_exc:
        raise last_exc

    return response  # type: ignore[name-defined]


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
            f"Supabase INSERT failed for {table}: "
            f"HTTP {response.status_code} - {response.text}"
        )

    logger.info("Inserted %s row(s) into %s", len(rows), table)


def supabase_patch(
    table: str,
    payload: Dict[str, Any],
    *,
    params: Dict[str, Any],
) -> None:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = request_with_retries(
        "PATCH",
        url,
        headers=supabase_headers(prefer="return=minimal"),
        params=params,
        json_body=payload,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase PATCH failed for {table}: "
            f"HTTP {response.status_code} - {response.text}"
        )


# ============================================================
# DATA LOADERS
# ============================================================

def load_today_scores(date_sgt: str) -> List[Dict[str, Any]]:
    rows = supabase_select(
        LEGACY_SCORES_TABLE,
        params={
            "run_date_sgt": f"eq.{date_sgt}",
            "select": "*",
            "limit": "5000",
        },
    )
    logger.info("Loaded %s ai_transmission_scores row(s)", len(rows))
    return rows


def load_today_observations(date_sgt: str) -> List[Dict[str, Any]]:
    rows = supabase_select(
        OBS_TABLE,
        params={
            "run_date_sgt": f"eq.{date_sgt}",
            "select": "*",
            "limit": "10000",
        },
    )
    logger.info("Loaded %s ai_transmission_observations row(s)", len(rows))
    return rows


def load_map_rows() -> Dict[int, Dict[str, Any]]:
    rows = supabase_select(
        MAP_TABLE,
        params={
            "select": "*",
            "limit": "5000",
        },
    )
    out: Dict[int, Dict[str, Any]] = {}
    for row in rows:
        map_id = safe_int(row.get("id"), default=-1)
        if map_id >= 0:
            out[map_id] = row
    logger.info("Loaded %s ai_transmission_map row(s)", len(out))
    return out


def load_structural_scores(date_sgt: str) -> Dict[str, Dict[str, Any]]:
    rows = supabase_select(
        STRUCTURAL_SCORES_TABLE,
        params={
            "run_date_sgt": f"eq.{date_sgt}",
            "theme_name": f"eq.{THEME_NAME}",
            "theme_version": f"eq.{THEME_VERSION}",
            "select": "*",
            "limit": "5000",
        },
    )
    out: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        ticker = str(row.get("ticker") or "").upper().strip()
        if ticker:
            out[ticker] = row
    logger.info("Loaded %s structural_theme_scores row(s)", len(out))
    return out


# ============================================================
# EXPLAINABILITY BUILDERS
# ============================================================

def build_component_rows(
    score_rows: List[Dict[str, Any]],
    date_sgt: str,
) -> List[Dict[str, Any]]:
    component_specs = [
        ("exposure_score", "exposure", WEIGHT_EXPOSURE),
        ("evidence_score", "evidence", WEIGHT_EVIDENCE),
        ("sentiment_score", "sentiment", WEIGHT_SENTIMENT),
        ("market_confirmation_score", "market_confirmation", WEIGHT_MARKET_CONFIRMATION),
        ("confidence_score", "confidence", WEIGHT_CONFIDENCE),
    ]

    rows: List[Dict[str, Any]] = []

    for score_row in score_rows:
        ticker = str(score_row.get("affected_ticker") or "").upper().strip()
        if not ticker:
            continue

        final_score = clamp_score(score_row.get("transmission_score"), DEFAULT_SCORE)

        component_items = []
        for source_col, component_name, weight in component_specs:
            component_score = clamp_score(score_row.get(source_col), DEFAULT_SCORE)
            weighted_contribution = component_score * weight
            contribution_pct = (
                (weighted_contribution / final_score) * 100.0
                if final_score and final_score > 0
                else None
            )
            component_items.append(
                {
                    "source_col": source_col,
                    "component_name": component_name,
                    "component_score": round(component_score, 4),
                    "component_weight": weight,
                    "weighted_contribution": round(weighted_contribution, 4),
                    "contribution_pct": round(contribution_pct, 4) if contribution_pct is not None else None,
                }
            )

        ranked = sorted(
            component_items,
            key=lambda x: safe_float(x.get("weighted_contribution"), 0.0) or 0.0,
            reverse=True,
        )
        rank_lookup = {item["component_name"]: idx + 1 for idx, item in enumerate(ranked)}

        for item in component_items:
            rows.append(
                {
                    "run_timestamp_sgt": now_sgt_iso(),
                    "run_date_sgt": date_sgt,
                    "theme_name": THEME_NAME,
                    "theme_version": THEME_VERSION,
                    "ticker": ticker,
                    "company": score_row.get("affected_company"),
                    "sector": score_row.get("affected_sector"),
                    "subsector": score_row.get("affected_subsector"),
                    "map_id": score_row.get("map_id"),
                    "component_name": item["component_name"],
                    "component_score": item["component_score"],
                    "component_weight": item["component_weight"],
                    "weighted_contribution": item["weighted_contribution"],
                    "contribution_pct": item["contribution_pct"],
                    "component_rank": rank_lookup.get(item["component_name"]),
                    "metadata": {
                        "source_column": item["source_col"],
                        "final_transmission_score": final_score,
                        "ai_subsector": score_row.get("ai_subsector"),
                        "transmission_direction": score_row.get("transmission_direction"),
                        "transmission_type": score_row.get("transmission_type"),
                        "pathway": build_pathway(score_row),
                        "explainability_version": EXPLAINABILITY_VERSION,
                    },
                }
            )

    logger.info("Built %s component score row(s)", len(rows))
    return rows


def compute_evidence_quality(obs: Dict[str, Any], direction: Optional[str]) -> Dict[str, float]:
    ai_relevance = clamp_score(obs.get("ai_relevance_score"), DEFAULT_SCORE)
    impact = clamp_score(obs.get("impact_magnitude_score"), DEFAULT_SCORE)
    confidence = clamp_score(obs.get("confidence_score"), DEFAULT_SCORE)
    adjusted_sentiment = direction_adjusted_sentiment(obs.get("sentiment_score"), direction)

    quality = (
        WEIGHT_OBS_AI_RELEVANCE * ai_relevance
        + WEIGHT_OBS_IMPACT * impact
        + WEIGHT_OBS_CONFIDENCE * confidence
        + WEIGHT_OBS_DIRECTIONAL_SENTIMENT * adjusted_sentiment
    )

    return {
        "ai_relevance_score": round(ai_relevance, 4),
        "impact_magnitude_score": round(impact, 4),
        "confidence_score": round(confidence, 4),
        "direction_adjusted_sentiment_score": round(adjusted_sentiment, 4),
        "evidence_quality_score": round(clamp_score(quality), 4),
    }


def build_evidence_attribution_rows(
    score_rows: List[Dict[str, Any]],
    observation_rows: List[Dict[str, Any]],
    date_sgt: str,
) -> List[Dict[str, Any]]:
    scores_by_map: Dict[int, Dict[str, Any]] = {}
    for row in score_rows:
        map_id = safe_int(row.get("map_id"), default=-1)
        if map_id >= 0:
            scores_by_map[map_id] = row

    obs_by_map: Dict[int, List[Dict[str, Any]]] = {}
    for obs in observation_rows:
        if obs.get("evidence_source") == "NO_EVIDENCE_FOUND":
            continue
        map_id = safe_int(obs.get("map_id"), default=-1)
        if map_id >= 0:
            obs_by_map.setdefault(map_id, []).append(obs)

    rows: List[Dict[str, Any]] = []

    for map_id, obs_list in obs_by_map.items():
        score_row = scores_by_map.get(map_id)
        if not score_row:
            continue

        ticker = str(score_row.get("affected_ticker") or "").upper().strip()
        if not ticker:
            continue

        direction = score_row.get("transmission_direction")
        sign = direction_sign(direction)
        pathway = build_pathway(score_row)

        enriched = []
        for obs in obs_list:
            q = compute_evidence_quality(obs, direction)
            enriched.append((obs, q))

        total_quality = sum(q["evidence_quality_score"] for _, q in enriched)
        if total_quality <= 0:
            total_quality = float(len(enriched)) or 1.0

        evidence_component_score = clamp_score(score_row.get("evidence_score"), DEFAULT_SCORE)

        for obs, q in enriched:
            weight = q["evidence_quality_score"] / total_quality if total_quality > 0 else 0.0
            contribution_score = weight * evidence_component_score
            signed_contribution = contribution_score * sign

            rows.append(
                {
                    "run_timestamp_sgt": now_sgt_iso(),
                    "run_date_sgt": date_sgt,
                    "theme_name": THEME_NAME,
                    "theme_version": THEME_VERSION,
                    "ticker": ticker,
                    "company": score_row.get("affected_company"),
                    "sector": score_row.get("affected_sector"),
                    "subsector": score_row.get("affected_subsector"),
                    "map_id": map_id,
                    "observation_id": obs.get("id"),
                    "ai_subsector": score_row.get("ai_subsector"),
                    "transmission_direction": direction,
                    "transmission_type": score_row.get("transmission_type"),
                    "evidence_source": obs.get("evidence_source"),
                    "evidence_title": compact_text(obs.get("evidence_title"), 300),
                    "evidence_url": obs.get("evidence_url"),
                    "evidence_summary": compact_text(obs.get("evidence_summary"), 1000),
                    "ai_relevance_score": q["ai_relevance_score"],
                    "impact_magnitude_score": q["impact_magnitude_score"],
                    "sentiment_score": clamp_score(obs.get("sentiment_score"), DEFAULT_SCORE),
                    "confidence_score": q["confidence_score"],
                    "direction_adjusted_sentiment_score": q["direction_adjusted_sentiment_score"],
                    "evidence_quality_score": q["evidence_quality_score"],
                    "evidence_weight": round(weight, 6),
                    "contribution_score": round(contribution_score, 4),
                    "signed_contribution_score": round(signed_contribution, 4),
                    "contribution_direction": contribution_direction(direction),
                    "pathway": pathway,
                    "metadata": {
                        "evidence_component_score": evidence_component_score,
                        "total_quality_for_map": round(total_quality, 4),
                        "final_transmission_score": score_row.get("transmission_score"),
                        "transmission_regime": score_row.get("transmission_regime"),
                        "signal_label": score_row.get("signal_label"),
                        "quality_weights": {
                            "ai_relevance": WEIGHT_OBS_AI_RELEVANCE,
                            "impact_magnitude": WEIGHT_OBS_IMPACT,
                            "confidence": WEIGHT_OBS_CONFIDENCE,
                            "directional_sentiment": WEIGHT_OBS_DIRECTIONAL_SENTIMENT,
                        },
                        "explainability_version": EXPLAINABILITY_VERSION,
                    },
                }
            )

    logger.info("Built %s evidence attribution row(s)", len(rows))
    return rows


def component_decomposition_for_ticker(component_rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    compact = []
    for row in sorted(component_rows, key=lambda x: safe_int(x.get("component_rank"), 999)):
        compact.append(
            {
                "component": row.get("component_name"),
                "score": row.get("component_score"),
                "weight": row.get("component_weight"),
                "weighted_contribution": row.get("weighted_contribution"),
                "contribution_pct": row.get("contribution_pct"),
                "rank": row.get("component_rank"),
                "map_id": row.get("map_id"),
            }
        )
    return compact


def driver_from_attribution(row: Dict[str, Any]) -> Dict[str, Any]:
    title = row.get("evidence_title") or "Evidence item"
    source = row.get("evidence_source") or "unknown source"
    summary = row.get("evidence_summary") or ""

    return {
        "driver": compact_text(title, 180),
        "source": source,
        "pathway": row.get("pathway"),
        "ai_subsector": row.get("ai_subsector"),
        "transmission_direction": row.get("transmission_direction"),
        "transmission_type": row.get("transmission_type"),
        "contribution_score": row.get("contribution_score"),
        "signed_contribution_score": row.get("signed_contribution_score"),
        "evidence_weight": row.get("evidence_weight"),
        "quality_score": row.get("evidence_quality_score"),
        "url": row.get("evidence_url"),
        "summary": compact_text(summary, 280),
    }


def fallback_driver_from_score(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "driver": compact_text(
            f"{row.get('ai_subsector')} transmission to {row.get('affected_ticker')}",
            180,
        ),
        "source": "structural_transmission_map",
        "pathway": build_pathway(row),
        "ai_subsector": row.get("ai_subsector"),
        "transmission_direction": row.get("transmission_direction"),
        "transmission_type": row.get("transmission_type"),
        "contribution_score": row.get("transmission_score"),
        "signed_contribution_score": (
            clamp_score(row.get("transmission_score"), DEFAULT_SCORE)
            * direction_sign(row.get("transmission_direction"))
        ),
        "evidence_weight": None,
        "quality_score": None,
        "url": None,
        "summary": compact_text(row.get("signal_label"), 280),
    }


def build_explanation_rows(
    score_rows: List[Dict[str, Any]],
    component_rows: List[Dict[str, Any]],
    attribution_rows: List[Dict[str, Any]],
    structural_scores: Dict[str, Dict[str, Any]],
    date_sgt: str,
) -> List[Dict[str, Any]]:
    scores_by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    components_by_ticker: Dict[str, List[Dict[str, Any]]] = {}
    attribution_by_ticker: Dict[str, List[Dict[str, Any]]] = {}

    for row in score_rows:
        ticker = str(row.get("affected_ticker") or "").upper().strip()
        if ticker:
            scores_by_ticker.setdefault(ticker, []).append(row)

    for row in component_rows:
        ticker = str(row.get("ticker") or "").upper().strip()
        if ticker:
            components_by_ticker.setdefault(ticker, []).append(row)

    for row in attribution_rows:
        ticker = str(row.get("ticker") or "").upper().strip()
        if ticker:
            attribution_by_ticker.setdefault(ticker, []).append(row)

    explanation_rows: List[Dict[str, Any]] = []

    for ticker, ticker_scores in scores_by_ticker.items():
        ranked_scores = sorted(
            ticker_scores,
            key=lambda x: safe_float(x.get("transmission_score"), 0.0) or 0.0,
            reverse=True,
        )
        headline = ranked_scores[0]
        structural = structural_scores.get(ticker, {})

        ticker_attr = attribution_by_ticker.get(ticker, [])

        positive_attr = [
            r for r in ticker_attr
            if str(r.get("contribution_direction") or "").upper() == "POSITIVE"
        ]
        negative_attr = [
            r for r in ticker_attr
            if str(r.get("contribution_direction") or "").upper() == "NEGATIVE"
        ]

        positive_drivers = [
            driver_from_attribution(r)
            for r in sorted(
                positive_attr,
                key=lambda x: safe_float(x.get("contribution_score"), 0.0) or 0.0,
                reverse=True,
            )[:5]
        ]

        negative_drivers = [
            driver_from_attribution(r)
            for r in sorted(
                negative_attr,
                key=lambda x: safe_float(x.get("contribution_score"), 0.0) or 0.0,
                reverse=True,
            )[:5]
        ]

        # Fallback when there is no evidence attribution yet.
        if not positive_drivers:
            positive_drivers = [
                fallback_driver_from_score(r)
                for r in ranked_scores
                if str(r.get("transmission_direction") or "").upper() == "POSITIVE"
            ][:5]

        if not negative_drivers:
            negative_drivers = [
                fallback_driver_from_score(r)
                for r in ranked_scores
                if str(r.get("transmission_direction") or "").upper() == "NEGATIVE"
            ][:5]

        pathways = []
        seen_pathways = set()
        for r in ranked_scores:
            pathway = build_pathway(r)
            if not pathway or pathway in seen_pathways:
                continue
            seen_pathways.add(pathway)
            pathways.append(
                {
                    "map_id": r.get("map_id"),
                    "pathway": pathway,
                    "ai_subsector": r.get("ai_subsector"),
                    "affected_sector": r.get("affected_sector"),
                    "affected_subsector": r.get("affected_subsector"),
                    "transmission_direction": r.get("transmission_direction"),
                    "transmission_type": r.get("transmission_type"),
                    "transmission_score": r.get("transmission_score"),
                    "confidence_score": r.get("confidence_score"),
                    "regime": r.get("transmission_regime"),
                }
            )

        evidence_count = len(ticker_attr)
        relationship_count = len(ticker_scores)
        final_score = safe_float(
            structural.get("theme_score"),
            safe_float(headline.get("transmission_score"), DEFAULT_SCORE),
        )
        confidence_score = safe_float(
            structural.get("confidence_score"),
            safe_float(headline.get("confidence_score"), DEFAULT_SCORE),
        )

        if evidence_count > 0:
            top_sources = sorted(
                {str(r.get("evidence_source") or "unknown") for r in ticker_attr}
            )[:5]
            evidence_summary = (
                f"{ticker} has {evidence_count} attributed evidence item(s) across "
                f"{relationship_count} transmission relationship(s). Top source(s): "
                + ", ".join(top_sources)
                + "."
            )
        else:
            evidence_summary = (
                f"{ticker} has no attributed evidence item for this run. "
                f"Explanation falls back to structural transmission map relationships."
            )

        explanation_rows.append(
            {
                "run_timestamp_sgt": now_sgt_iso(),
                "run_date_sgt": date_sgt,
                "theme_name": THEME_NAME,
                "theme_version": THEME_VERSION,
                "ticker": ticker,
                "company": headline.get("affected_company") or structural.get("company"),
                "sector": headline.get("affected_sector") or structural.get("sector"),
                "subsector": headline.get("affected_subsector") or structural.get("subsector"),
                "final_score": round(clamp_score(final_score, DEFAULT_SCORE), 4),
                "confidence_score": round(clamp_score(confidence_score, DEFAULT_SCORE), 4),
                "evidence_count": evidence_count,
                "relationship_count": relationship_count,
                "top_positive_drivers": positive_drivers,
                "top_negative_drivers": negative_drivers,
                "component_decomposition": component_decomposition_for_ticker(
                    components_by_ticker.get(ticker, [])
                ),
                "transmission_pathways": pathways[:20],
                "evidence_summary": evidence_summary,
                "explainability_version": EXPLAINABILITY_VERSION,
                "metadata": {
                    "source_pipeline": PIPELINE_NAME,
                    "legacy_score_table": LEGACY_SCORES_TABLE,
                    "legacy_granularity": "relationship_level_map_id",
                    "generic_granularity": "ticker_level_theme_score",
                    "patch_structural_theme_scores": PATCH_STRUCTURAL_THEME_SCORES,
                    "github": github_metadata(),
                },
            }
        )

    explanation_rows.sort(
        key=lambda x: safe_float(x.get("final_score"), 0.0) or 0.0,
        reverse=True,
    )

    logger.info("Built %s explanation row(s)", len(explanation_rows))
    return explanation_rows


# ============================================================
# OPTIONAL PATCH BACK INTO structural_theme_scores
# ============================================================

def patch_structural_theme_scores(explanation_rows: List[Dict[str, Any]]) -> int:
    if not PATCH_STRUCTURAL_THEME_SCORES:
        logger.info("Skipping structural_theme_scores patch by env setting.")
        return 0

    patched = 0

    for row in explanation_rows:
        ticker = row.get("ticker")
        if not ticker:
            continue

        payload = {
            "positive_drivers": row.get("top_positive_drivers") or [],
            "negative_drivers": row.get("top_negative_drivers") or [],
            "positive_driver_count": len(row.get("top_positive_drivers") or []),
            "negative_driver_count": len(row.get("top_negative_drivers") or []),
            "evidence_count": row.get("evidence_count"),
            "score_components": {
                "phase2b_component_decomposition": row.get("component_decomposition") or [],
                "phase2b_transmission_pathways": row.get("transmission_pathways") or [],
                "phase2b_evidence_summary": row.get("evidence_summary"),
                "explainability_version": EXPLAINABILITY_VERSION,
            },
            "metadata": {
                "phase2b_explainability_applied": True,
                "explainability_version": EXPLAINABILITY_VERSION,
                "phase2b_updated_at_sgt": now_sgt_iso(),
                "source_pipeline": PIPELINE_NAME,
            },
            "updated_at": now_sgt_iso(),
        }

        params = {
            "run_date_sgt": f"eq.{row.get('run_date_sgt')}",
            "theme_name": f"eq.{THEME_NAME}",
            "theme_version": f"eq.{THEME_VERSION}",
            "ticker": f"eq.{ticker}",
        }

        supabase_patch(STRUCTURAL_SCORES_TABLE, payload, params=params)
        patched += 1

    logger.info("Patched %s structural_theme_scores row(s)", patched)
    return patched


# ============================================================
# STRUCTURAL RUN TELEMETRY
# ============================================================

def write_structural_run(
    *,
    date_sgt: str,
    status: str,
    runtime_seconds: float,
    rows_processed: int,
    rows_written: int,
    evidence_rows: int,
    score_rows: int,
    error_message: Optional[str] = None,
) -> None:
    payload = {
        "run_timestamp_sgt": now_sgt_iso(),
        "run_date_sgt": date_sgt,
        "pipeline_name": PIPELINE_NAME,
        "theme_name": THEME_NAME,
        "theme_version": THEME_VERSION,
        "status": status,
        "runtime_seconds": round(runtime_seconds, 4),
        "rows_processed": rows_processed,
        "rows_written": rows_written,
        "evidence_rows": evidence_rows,
        "score_rows": score_rows,
        "error_message": error_message,
        "metadata": {
            "explainability_version": EXPLAINABILITY_VERSION,
            "component_table": COMPONENT_TABLE,
            "attribution_table": ATTRIBUTION_TABLE,
            "explanation_table": EXPLANATION_TABLE,
            "patch_structural_theme_scores": PATCH_STRUCTURAL_THEME_SCORES,
        },
        **github_metadata(),
    }

    # structural_theme_runs status check constraint allows SUCCESS, FAILED, WARNING, SKIPPED.
    if status not in ("SUCCESS", "FAILED", "WARNING", "SKIPPED"):
        payload["status"] = "WARNING"

    supabase_insert(RUNS_TABLE, [payload])


# ============================================================
# MAIN
# ============================================================

def run_phase2b_explainability() -> None:
    require_env()
    start = time.time()
    date_sgt = run_date_sgt()

    score_rows: List[Dict[str, Any]] = []
    observation_rows: List[Dict[str, Any]] = []

    try:
        logger.info("Starting Phase 2B explainability for run_date_sgt=%s", date_sgt)

        score_rows = load_today_scores(date_sgt)
        if not score_rows:
            runtime = time.time() - start
            logger.warning("No ai_transmission_scores found. Skipping explainability run.")
            write_structural_run(
                date_sgt=date_sgt,
                status="SKIPPED",
                runtime_seconds=runtime,
                rows_processed=0,
                rows_written=0,
                evidence_rows=0,
                score_rows=0,
                error_message="No ai_transmission_scores found for run date.",
            )
            return

        observation_rows = load_today_observations(date_sgt)
        structural_scores = load_structural_scores(date_sgt)

        component_rows = build_component_rows(score_rows, date_sgt)
        attribution_rows = build_evidence_attribution_rows(score_rows, observation_rows, date_sgt)
        explanation_rows = build_explanation_rows(
            score_rows=score_rows,
            component_rows=component_rows,
            attribution_rows=attribution_rows,
            structural_scores=structural_scores,
            date_sgt=date_sgt,
        )

        supabase_upsert(
            COMPONENT_TABLE,
            component_rows,
            on_conflict="run_date_sgt,theme_name,theme_version,ticker,map_id,component_name",
        )
        supabase_upsert(
            ATTRIBUTION_TABLE,
            attribution_rows,
            on_conflict="run_date_sgt,theme_name,theme_version,observation_id",
        )
        supabase_upsert(
            EXPLANATION_TABLE,
            explanation_rows,
            on_conflict="run_date_sgt,theme_name,theme_version,ticker",
        )

        patched_count = patch_structural_theme_scores(explanation_rows)

        runtime = time.time() - start
        total_written = len(component_rows) + len(attribution_rows) + len(explanation_rows) + patched_count

        write_structural_run(
            date_sgt=date_sgt,
            status="SUCCESS",
            runtime_seconds=runtime,
            rows_processed=len(score_rows) + len(observation_rows),
            rows_written=total_written,
            evidence_rows=len(attribution_rows),
            score_rows=len(score_rows),
            error_message=None,
        )

        logger.info("Phase 2B explainability completed successfully.")
        logger.info("Component rows: %s", len(component_rows))
        logger.info("Evidence attribution rows: %s", len(attribution_rows))
        logger.info("Explanation rows: %s", len(explanation_rows))
        logger.info("Patched structural_theme_scores rows: %s", patched_count)

    except Exception as exc:
        runtime = time.time() - start
        error_message = str(exc)
        logger.exception("Phase 2B explainability failed: %s", error_message)

        try:
            write_structural_run(
                date_sgt=date_sgt,
                status="FAILED",
                runtime_seconds=runtime,
                rows_processed=len(score_rows) + len(observation_rows),
                rows_written=0,
                evidence_rows=len(observation_rows),
                score_rows=len(score_rows),
                error_message=error_message,
            )
        except Exception as telemetry_exc:
            logger.error("Failed to write failure telemetry: %s", telemetry_exc)

        raise


if __name__ == "__main__":
    run_phase2b_explainability()
