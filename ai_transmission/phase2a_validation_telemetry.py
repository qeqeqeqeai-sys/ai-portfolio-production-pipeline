import os
import sys
import time
import json
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, Any, List, Optional


# =====================================================
# CONFIG
# =====================================================

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

THEME_NAME = os.getenv("THEME_NAME", "ai")
PIPELINE_NAME = os.getenv("PIPELINE_NAME", "AI_TRANSMISSION_PHASE2A")

SGT = ZoneInfo("Asia/Singapore")


if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY / SUPABASE_KEY."
    )


HEADERS = {
    "apikey": SUPABASE_SERVICE_ROLE_KEY,
    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation",
}


# =====================================================
# SUPABASE REST HELPERS
# =====================================================

def supabase_get(table: str, params: Optional[Dict[str, str]] = None) -> List[Dict[str, Any]]:
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = requests.get(url, headers=HEADERS, params=params or {}, timeout=45)

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase GET failed for {table}: "
            f"{response.status_code} - {response.text}"
        )

    return response.json()


def supabase_insert(table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows:
        return []

    url = f"{SUPABASE_URL}/rest/v1/{table}"
    response = requests.post(url, headers=HEADERS, data=json.dumps(rows), timeout=45)

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase INSERT failed for {table}: "
            f"{response.status_code} - {response.text}"
        )

    return response.json()


# =====================================================
# DATE HELPERS
# =====================================================

def today_sgt_date() -> str:
    return datetime.now(SGT).date().isoformat()


def now_sgt_iso() -> str:
    return datetime.now(SGT).isoformat()


def github_metadata() -> Dict[str, Optional[str]]:
    return {
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
    }


# =====================================================
# VALIDATION RESULT HELPER
# =====================================================

def result(
    validation_name: str,
    severity: str,
    status: str,
    observed_value: Any = None,
    expected_value: Any = None,
    message: str = "",
) -> Dict[str, Any]:
    return {
        "run_timestamp_sgt": now_sgt_iso(),
        "run_date_sgt": today_sgt_date(),
        "pipeline_name": PIPELINE_NAME,
        "theme_name": THEME_NAME,
        "validation_name": validation_name,
        "severity": severity,
        "status": status,
        "observed_value": None if observed_value is None else str(observed_value),
        "expected_value": None if expected_value is None else str(expected_value),
        "message": message,
    }


# =====================================================
# DATA LOADERS
# =====================================================

def load_today_scores() -> List[Dict[str, Any]]:
    params = {
        "run_date_sgt": f"eq.{today_sgt_date()}",
        "theme_name": f"eq.{THEME_NAME}",
        "select": "*",
    }

    try:
        return supabase_get("structural_theme_scores", params)
    except Exception:
        # fallback for older schema if theme_name not present
        params = {
            "run_date_sgt": f"eq.{today_sgt_date()}",
            "select": "*",
        }
        return supabase_get("structural_theme_scores", params)


def load_recent_scores(days: int = 30) -> List[Dict[str, Any]]:
    params = {
        "theme_name": f"eq.{THEME_NAME}",
        "select": "*",
        "order": "run_date_sgt.desc",
        "limit": "5000",
    }

    try:
        return supabase_get("structural_theme_scores", params)
    except Exception:
        params = {
            "select": "*",
            "order": "run_date_sgt.desc",
            "limit": "5000",
        }
        return supabase_get("structural_theme_scores", params)


def load_today_observations() -> List[Dict[str, Any]]:
    params = {
        "run_date_sgt": f"eq.{today_sgt_date()}",
        "select": "*",
    }

    try:
        return supabase_get("ai_transmission_observations", params)
    except Exception:
        return []


# =====================================================
# FIELD DETECTION
# =====================================================

def get_score_value(row: Dict[str, Any]) -> Optional[float]:
    for col in ["final_score", "score", "composite_score", "theme_score"]:
        value = row.get(col)
        if value is not None:
            try:
                return float(value)
            except Exception:
                return None
    return None


def get_confidence_value(row: Dict[str, Any]) -> Optional[float]:
    for col in ["confidence_score", "confidence", "evidence_confidence"]:
        value = row.get(col)
        if value is not None:
            try:
                return float(value)
            except Exception:
                return None
    return None


def get_regime(row: Dict[str, Any]) -> Optional[str]:
    for col in ["regime", "score_regime", "transmission_regime"]:
        value = row.get(col)
        if value:
            return str(value).lower()
    return None


def get_ticker(row: Dict[str, Any]) -> Optional[str]:
    return row.get("ticker") or row.get("symbol")


# =====================================================
# VALIDATION GATES
# =====================================================

def validate_score_rows(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not scores:
        return result(
            "score_rows_exist",
            "HARD_FAIL",
            "FAIL",
            observed_value=0,
            expected_value="> 0",
            message="No structural_theme_scores rows found for today's run.",
        )

    return result(
        "score_rows_exist",
        "HARD_FAIL",
        "PASS",
        observed_value=len(scores),
        expected_value="> 0",
        message="Score rows found.",
    )


def validate_duplicate_ticker_theme_day(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    seen = {}
    duplicates = []

    for row in scores:
        ticker = get_ticker(row)
        theme = row.get("theme_name", THEME_NAME)
        run_date = row.get("run_date_sgt", today_sgt_date())
        key = (run_date, theme, ticker)

        seen[key] = seen.get(key, 0) + 1

    for key, count in seen.items():
        if count > 1:
            duplicates.append({"key": key, "count": count})

    if duplicates:
        return result(
            "duplicate_ticker_theme_day",
            "HARD_FAIL",
            "FAIL",
            observed_value=json.dumps(duplicates[:10]),
            expected_value="0 duplicates",
            message="Duplicate ticker/theme/date rows detected.",
        )

    return result(
        "duplicate_ticker_theme_day",
        "HARD_FAIL",
        "PASS",
        observed_value=0,
        expected_value="0 duplicates",
        message="No duplicate ticker/theme/date rows detected.",
    )


def validate_null_scores(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    null_count = sum(1 for row in scores if get_score_value(row) is None)

    if null_count > 0:
        return result(
            "null_score_detection",
            "HARD_FAIL",
            "FAIL",
            observed_value=null_count,
            expected_value=0,
            message="Null or unreadable score values detected.",
        )

    return result(
        "null_score_detection",
        "HARD_FAIL",
        "PASS",
        observed_value=0,
        expected_value=0,
        message="No null scores detected.",
    )


def validate_score_range(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    bad = []

    for row in scores:
        score = get_score_value(row)
        ticker = get_ticker(row)

        if score is None or score < 0 or score > 100:
            bad.append({"ticker": ticker, "score": score})

    if bad:
        return result(
            "score_range_validation",
            "HARD_FAIL",
            "FAIL",
            observed_value=json.dumps(bad[:20]),
            expected_value="0 <= score <= 100",
            message="Scores outside expected 0-100 range detected.",
        )

    return result(
        "score_range_validation",
        "HARD_FAIL",
        "PASS",
        observed_value="all scores valid",
        expected_value="0 <= score <= 100",
        message="All scores are within expected range.",
    )


def validate_confidence_range(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    confidence_values = [get_confidence_value(row) for row in scores]
    confidence_values = [v for v in confidence_values if v is not None]

    if not confidence_values:
        return result(
            "confidence_score_sanity",
            "WARNING",
            "WARN",
            observed_value="no confidence column/value detected",
            expected_value="0 <= confidence <= 100",
            message="No confidence score detected. This is acceptable for now but should be added in Phase 2B.",
        )

    bad = [v for v in confidence_values if v < 0 or v > 100]

    if bad:
        return result(
            "confidence_score_sanity",
            "HARD_FAIL",
            "FAIL",
            observed_value=json.dumps(bad[:20]),
            expected_value="0 <= confidence <= 100",
            message="Confidence scores outside expected range detected.",
        )

    return result(
        "confidence_score_sanity",
        "HARD_FAIL",
        "PASS",
        observed_value="all confidence scores valid",
        expected_value="0 <= confidence <= 100",
        message="Confidence scores are within expected range.",
    )


def validate_regime_distribution(scores: List[Dict[str, Any]]) -> Dict[str, Any]:
    regimes = [get_regime(row) for row in scores]
    regimes = [r for r in regimes if r]

    if not regimes:
        return result(
            "regime_distribution",
            "WARNING",
            "WARN",
            observed_value="no regime column/value detected",
            expected_value="regime distribution available",
            message="No regime values detected. Add regime output later for stronger monitoring.",
        )

    total = len(regimes)
    counts = {}

    for r in regimes:
        counts[r] = counts.get(r, 0) + 1

    max_share = max(counts.values()) / total if total else 0

    if total >= 10 and max_share >= 0.95:
        return result(
            "regime_distribution",
            "WARNING",
            "WARN",
            observed_value=json.dumps(counts),
            expected_value="no single regime > 95%",
            message="Regime distribution is unusually concentrated.",
        )

    return result(
        "regime_distribution",
        "WARNING",
        "PASS",
        observed_value=json.dumps(counts),
        expected_value="balanced enough",
        message="Regime distribution looks acceptable.",
    )


def validate_score_drift(
    today_scores: List[Dict[str, Any]],
    recent_scores: List[Dict[str, Any]],
) -> Dict[str, Any]:
    today_values = [get_score_value(row) for row in today_scores]
    today_values = [v for v in today_values if v is not None]

    recent_values = [
        get_score_value(row)
        for row in recent_scores
        if row.get("run_date_sgt") != today_sgt_date()
    ]
    recent_values = [v for v in recent_values if v is not None]

    if not today_values or len(recent_values) < 20:
        return result(
            "score_drift_anomaly",
            "WARNING",
            "WARN",
            observed_value=f"today={len(today_values)}, history={len(recent_values)}",
            expected_value="sufficient history",
            message="Insufficient history for reliable score drift validation.",
        )

    today_avg = sum(today_values) / len(today_values)
    recent_avg = sum(recent_values) / len(recent_values)
    drift = abs(today_avg - recent_avg)

    if drift > 20:
        return result(
            "score_drift_anomaly",
            "WARNING",
            "WARN",
            observed_value=round(drift, 4),
            expected_value="<= 20",
            message=f"Large average score drift detected. Today avg={today_avg:.2f}, recent avg={recent_avg:.2f}.",
        )

    return result(
        "score_drift_anomaly",
        "WARNING",
        "PASS",
        observed_value=round(drift, 4),
        expected_value="<= 20",
        message=f"Score drift acceptable. Today avg={today_avg:.2f}, recent avg={recent_avg:.2f}.",
    )


def validate_observation_coverage(
    scores: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
) -> Dict[str, Any]:
    if not observations:
        return result(
            "evidence_coverage",
            "WARNING",
            "WARN",
            observed_value=0,
            expected_value="> 0",
            message="No AI transmission observations found for today. Pipeline can continue, but confidence may be reduced.",
        )

    ratio = len(observations) / max(len(scores), 1)

    if ratio < 0.25:
        return result(
            "evidence_coverage",
            "WARNING",
            "WARN",
            observed_value=round(ratio, 4),
            expected_value=">= 0.25 observations per score row",
            message="Evidence coverage appears thin relative to score rows.",
        )

    return result(
        "evidence_coverage",
        "WARNING",
        "PASS",
        observed_value=round(ratio, 4),
        expected_value=">= 0.25 observations per score row",
        message="Evidence coverage looks acceptable.",
    )


# =====================================================
# TELEMETRY
# =====================================================

def build_telemetry(
    status: str,
    runtime_seconds: float,
    scores: List[Dict[str, Any]],
    observations: List[Dict[str, Any]],
    validation_results: List[Dict[str, Any]],
    error_message: Optional[str] = None,
) -> Dict[str, Any]:
    score_values = [get_score_value(row) for row in scores]
    score_values = [v for v in score_values if v is not None]

    confidence_values = [get_confidence_value(row) for row in scores]
    confidence_values = [v for v in confidence_values if v is not None]

    regimes = [get_regime(row) for row in scores]
    regimes = [r for r in regimes if r]

    bullish_count = sum(1 for r in regimes if "bull" in r or "positive" in r)
    bearish_count = sum(1 for r in regimes if "bear" in r or "negative" in r)
    neutral_count = sum(1 for r in regimes if "neutral" in r)

    failures = sum(
        1 for r in validation_results
        if r["severity"] == "HARD_FAIL" and r["status"] == "FAIL"
    )

    warnings = sum(
        1 for r in validation_results
        if r["status"] == "WARN"
    )

    payload = {
        "run_timestamp_sgt": now_sgt_iso(),
        "run_date_sgt": today_sgt_date(),
        "pipeline_name": PIPELINE_NAME,
        "theme_name": THEME_NAME,
        "status": status,

        "runtime_seconds": round(runtime_seconds, 4),
        "score_rows": len(scores),
        "observation_rows": len(observations),
        "validation_failures": failures,
        "validation_warnings": warnings,

        "avg_score": round(sum(score_values) / len(score_values), 4) if score_values else None,
        "min_score": round(min(score_values), 4) if score_values else None,
        "max_score": round(max(score_values), 4) if score_values else None,
        "avg_confidence": round(sum(confidence_values) / len(confidence_values), 4) if confidence_values else None,

        "bullish_count": bullish_count,
        "bearish_count": bearish_count,
        "neutral_count": neutral_count,

        "error_message": error_message,
    }

    payload.update(github_metadata())
    return payload


# =====================================================
# MAIN
# =====================================================

def run_phase2a_validation_telemetry() -> None:
    start = time.time()
    scores = []
    observations = []
    validation_results = []

    try:
        print("[INFO] Loading today's structural theme scores...")
        scores = load_today_scores()
        print(f"[INFO] Score rows loaded: {len(scores)}")

        print("[INFO] Loading recent structural theme scores...")
        recent_scores = load_recent_scores()
        print(f"[INFO] Recent score rows loaded: {len(recent_scores)}")

        print("[INFO] Loading today's AI transmission observations...")
        observations = load_today_observations()
        print(f"[INFO] Observation rows loaded: {len(observations)}")

        print("[INFO] Running validation gates...")

        validation_results = [
            validate_score_rows(scores),
            validate_duplicate_ticker_theme_day(scores),
            validate_null_scores(scores),
            validate_score_range(scores),
            validate_confidence_range(scores),
            validate_regime_distribution(scores),
            validate_score_drift(scores, recent_scores),
            validate_observation_coverage(scores, observations),
        ]

        print("[INFO] Writing validation results...")
        supabase_insert("structural_theme_validation_results", validation_results)

        hard_failures = [
            r for r in validation_results
            if r["severity"] == "HARD_FAIL" and r["status"] == "FAIL"
        ]

        runtime_seconds = time.time() - start

        if hard_failures:
            status = "FAILED_VALIDATION"
            error_message = "; ".join([r["message"] for r in hard_failures])
        else:
            status = "SUCCESS"
            error_message = None

        telemetry = build_telemetry(
            status=status,
            runtime_seconds=runtime_seconds,
            scores=scores,
            observations=observations,
            validation_results=validation_results,
            error_message=error_message,
        )

        print("[INFO] Writing telemetry...")
        supabase_insert("structural_theme_pipeline_telemetry", [telemetry])

        print("[INFO] Validation Summary:")
        for r in validation_results:
            print(
                f" - {r['validation_name']}: "
                f"{r['status']} / {r['severity']} / {r['message']}"
            )

        if hard_failures:
            raise RuntimeError(f"Hard validation failures detected: {error_message}")

        print("[SUCCESS] Phase 2A validation + telemetry completed successfully.")

    except Exception as exc:
        runtime_seconds = time.time() - start
        error_message = str(exc)

        print(f"[ERROR] Phase 2A failed: {error_message}")

        telemetry = build_telemetry(
            status="ERROR",
            runtime_seconds=runtime_seconds,
            scores=scores,
            observations=observations,
            validation_results=validation_results,
            error_message=error_message,
        )

        try:
            supabase_insert("structural_theme_pipeline_telemetry", [telemetry])
        except Exception as telemetry_exc:
            print(f"[ERROR] Failed to write error telemetry: {telemetry_exc}")

        raise


if __name__ == "__main__":
    run_phase2a_validation_telemetry()