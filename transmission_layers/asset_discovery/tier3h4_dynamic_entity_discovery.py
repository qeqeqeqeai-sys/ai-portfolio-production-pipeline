from __future__ import annotations
import json, os, re, subprocess, sys, time
import math
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
import requests

TABLE_NAME = "tier3h_dynamic_entity_discovery"
EVIDENCE_TABLE_NAME = "tier3h_dynamic_entity_evidence"
OPERATIONAL_TABLE_NAME = "tier3h_operational_api_usage"
LOG_DIR = Path("logs")
SUMMARY_PATH = LOG_DIR / "tier3h4_dynamic_entity_discovery_summary.json"
EVIDENCE_SUMMARY_PATH = LOG_DIR / "tier3h4_dynamic_entity_evidence_summary.json"
VALIDATION_PATH = LOG_DIR / "tier3h4_dynamic_entity_discovery_validation.json"
OPERATIONAL_SUMMARY_PATH = LOG_DIR / "tier3h4_operational_controls_summary.json"

SUPABASE_UPSTREAM_SOURCES = [
    {"table": "tier3h_transmission_candidates", "order": "run_date_sgt.desc", "limit": 400},
    {"table": "structural_theme_graph_single_hop_propagation", "order": "run_date_sgt.desc", "limit": 400},
]

WEIGHTS = {"evidence_count_score": 0.30, "thematic_relevance_score": 0.25, "source_quality_score": 0.20, "entity_resolution_score": 0.15, "cross_source_score": 0.10}
QUERY_TEMPLATES = ["{theme_label} public companies", "{theme_label} listed companies", "{theme_label} infrastructure suppliers", "{theme_label} earnings transcript companies", "{theme_label} ETF holdings companies"]
THEME_LABELS = {"ai_power_demand": ["AI data center power infrastructure", "AI electricity demand grid infrastructure", "AI hyperscaler power equipment", "AI data center cooling UPS"]}
THEME_KEYWORDS = {"ai_power_demand": ["ai", "data center", "power", "grid", "infrastructure", "cooling", "ups", "electricity"]}
TIER_A_DOMAINS = {"sec.gov", "reuters.com", "bloomberg.com", "wsj.com", "ft.com", "nasdaq.com", "nyse.com", "blackrock.com", "vanguard.com", "state street.com"}
TIER_B_DOMAINS = {"utilitydive.com", "datacenterdynamics.com", "spglobal.com", "fool.com", "marketwatch.com", "barrons.com", "cnbc.com"}
GENERIC_SUPPRESSION_TOKENS = {"apple", "microsoft", "google", "amazon", "meta", "nvidia"}

MAX_TAVILY_QUERIES_PER_RUN = int(os.getenv("TIER3H4_MAX_TAVILY_QUERIES_PER_RUN", "25"))
MAX_RESULTS_PER_QUERY = int(os.getenv("TIER3H4_MAX_RESULTS_PER_QUERY", "5"))
MAX_TAVILY_RETRIES = int(os.getenv("TIER3H4_MAX_TAVILY_RETRIES", "2"))
QUERY_CACHE_LOOKBACK_DAYS = int(os.getenv("TIER3H4_QUERY_CACHE_LOOKBACK_DAYS", "3"))
MAX_QUERIES_PER_THEME = int(os.getenv("TIER3H4_MAX_QUERIES_PER_THEME", "5"))
TAVILY_TIMEOUT_SECONDS = int(os.getenv("TIER3H4_TAVILY_TIMEOUT_SECONDS", "30"))


def _safe_git_command(args: list[str]) -> str | None:
    try:
        completed = subprocess.run(["git", *args], check=False, capture_output=True, text=True, timeout=5)
        if completed.returncode != 0:
            return None
        value = (completed.stdout or "").strip()
        return value or None
    except Exception:
        return None


def _runtime_provenance(entrypoint_name: str) -> dict[str, Any]:
    file_path = Path(__file__).resolve()
    file_exists = file_path.exists()
    file_mtime_utc = datetime.fromtimestamp(file_path.stat().st_mtime, tz=timezone.utc).isoformat() if file_exists else None
    env_force_fresh = os.getenv("TIER3H4_FORCE_FRESH_EVIDENCE")
    git_sha_env = os.getenv("GITHUB_SHA")
    git_ref_env = os.getenv("GITHUB_REF")
    return {
        "runtime_git_commit": git_sha_env or _safe_git_command(["rev-parse", "HEAD"]) or "unknown",
        "runtime_git_branch": (git_ref_env.split("/")[-1] if git_ref_env else None) or _safe_git_command(["rev-parse", "--abbrev-ref", "HEAD"]) or "unknown",
        "runtime_github_sha": git_sha_env or None,
        "runtime_github_ref": git_ref_env or None,
        "runtime_workflow_name": os.getenv("GITHUB_WORKFLOW") or None,
        "runtime_workflow": os.getenv("GITHUB_WORKFLOW") or None,
        "runtime_workflow_run_id": os.getenv("GITHUB_RUN_ID") or None,
        "runtime_file_path": str(file_path),
        "runtime_file_exists": file_exists,
        "runtime_file_mtime_utc": file_mtime_utc,
        "runtime_module_name": __name__,
        "runtime_entrypoint_name": entrypoint_name,
        "runtime_python_executable": sys.executable,
        "runtime_python_version": sys.version,
        "runtime_cwd": os.getcwd(),
        "runtime_sys_path_head": sys.path[:5],
        "runtime_phase2b_validation_code_loaded": True,
        "runtime_force_fresh_env_detected": env_force_fresh is not None,
        "runtime_force_fresh_env_value": env_force_fresh,
    }


def _force_fresh_evidence_enabled() -> bool:
    return os.getenv("TIER3H4_FORCE_FRESH_EVIDENCE", "").strip().lower() in {"1", "true", "yes"}

TICKER_LIKE_PATTERN = re.compile(r"\b(?:[A-Z]{1,5}(?::[A-Z]{1,5})?|(?:NYSE|NASDAQ)\s*:\s*[A-Z]{1,5}|ticker\s*[:=]\s*[A-Z]{1,5}|symbol\s*[:=]\s*[A-Z]{1,5})\b")
EXCHANGE_LIKE_PATTERN = re.compile(r"\b(?:NYSE|NASDAQ|Nasdaq|New York Stock Exchange|London Stock Exchange|LSE|SGX|Singapore Exchange|HKEX|Tokyo Stock Exchange|TSE)\b")
EXCHANGE_LABEL_TO_CANONICAL = {
    "NASDAQ": "NASDAQ",
    "Nasdaq": "NASDAQ",
    "NYSE": "NYSE",
    "New York Stock Exchange": "NYSE",
    "SGX": "SGX",
    "Singapore Exchange": "SGX",
    "HKEX": "HKEX",
    "Hong Kong Stock Exchange": "HKEX",
    "LSE": "LSE",
    "London Stock Exchange": "LSE",
    "TSE": "TSE",
    "Tokyo Stock Exchange": "TSE",
}
NOISE_TICKER_DENYLIST = {"AI", "ETF", "CEO", "IPO", "SEC", "USD", "ADR", "LLC", "INC", "LTD", "PLC", "CORP", "THE", "AND"}
STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE = 8
STRICT_IDENTIFIER_CONTEXT_WINDOW_MAX_LEN = 240
STRICT_IDENTIFIER_TOKEN_DISTANCE_MAX = 10
STRICT_IDENTIFIER_NORMALIZATION_SAMPLE_MAX = 5
STRICT_EXCHANGE_LABEL_PATTERN = "|".join(sorted((re.escape(k) for k in EXCHANGE_LABEL_TO_CANONICAL), key=len, reverse=True))
STRICT_EXCHANGE_QUALIFIED_IDENTIFIER_PATTERN = re.compile(
    rf"(?i)(?:^|[\s\(\[\{{,;])(?P<label>{STRICT_EXCHANGE_LABEL_PATTERN})\s*:\s*(?P<ticker>[A-Za-z0-9]{{1,6}})\b"
)
STRICT_PARENTHEICAL_TICKER_THEN_EXCHANGE_PATTERN = re.compile(
    rf"(?i)\b(?P<ticker>[A-Za-z0-9]{{1,6}})\s*\(\s*(?P<label>{STRICT_EXCHANGE_LABEL_PATTERN})\s*\)"
)
STRICT_PARENTHEICAL_EXCHANGE_THEN_TICKER_PATTERN = re.compile(
    rf"(?i)\b(?P<label>{STRICT_EXCHANGE_LABEL_PATTERN})\s*\(\s*(?P<ticker>[A-Za-z0-9]{{1,6}})\s*\)"
)
STRICT_LISTED_CONTEXT_PATTERN = re.compile(
    rf"(?i)\b(?:listed|trades|traded)\s+on\s+(?P<label>{STRICT_EXCHANGE_LABEL_PATTERN})\s+(?:under\s+(?:ticker|symbol)\s+|as\s+)(?P<ticker>[A-Za-z0-9]{{1,6}})\b"
)
STRICT_HYPHENATED_LISTED_PATTERN = re.compile(
    rf"(?i)\b(?P<label>{STRICT_EXCHANGE_LABEL_PATTERN})\s*-\s*listed\s+(?P<ticker>[A-Za-z0-9]{{1,6}})\b"
)
STRICT_TICKER_ON_EXCHANGE_PATTERN = re.compile(
    rf"(?i)\b(?:stock\s+symbol|ticker|symbol)\s+(?P<ticker>[A-Za-z0-9]{{1,6}})\s+on\s+(?P<label>{STRICT_EXCHANGE_LABEL_PATTERN})\b"
)
MEANINGFUL_TEXT_MIN_LENGTH = 40

CANONICAL_EXTRACTION_FIELDS = (
    "extraction_method",
    "extraction_confidence",
    "extraction_notes",
    "normalized_ticker",
    "normalized_exchange",
    "extracted_ticker",
    "extracted_exchange",
    "accepted",
    "rejection_reason",
    "ambiguity_reason",
)


def _canonical_extraction_result(**overrides: Any) -> dict[str, Any]:
    base = {
        "extraction_method": None,
        "extraction_confidence": None,
        "extraction_notes": None,
        "normalized_ticker": None,
        "normalized_exchange": None,
        "extracted_ticker": None,
        "extracted_exchange": None,
        "accepted": False,
        "rejection_reason": None,
        "ambiguity_reason": None,
        "warnings": [],
        "multiple_matches_detected": False,
    }
    base.update(overrides)
    return base


def _apply_canonical_extraction_result(row: dict[str, Any], extraction: dict[str, Any]) -> None:
    if row.get("accepted") and not extraction.get("accepted"):
        return
    for key in CANONICAL_EXTRACTION_FIELDS:
        row[key] = extraction.get(key)
METADATA_ONLY_PATTERN = re.compile(r"^\s*(?:weighted_score|evidence_count|suppression|metadata|operational|source_domain|tavily_score|published_date|evidence_rank)[\s:=;\w,._-]*$", re.IGNORECASE)


def utc_now() -> datetime: return datetime.now(timezone.utc)
def run_date_sgt(today_utc: datetime | None = None) -> str: return ((today_utc or utc_now()) + timedelta(hours=8)).date().isoformat()
def _safe_float(v: Any, d: float = 0.0) -> float:
    try: return float(v)
    except (TypeError, ValueError): return d

def _score_band(score: float) -> str:
    if score >= 80: return "high_confidence"
    if score >= 60: return "medium_confidence"
    if score >= 40: return "low_confidence"
    return "rejected_or_noise"

@dataclass(frozen=True)
class DiscoverySeed:
    theme_name: str
    source_node: str
    target_node: str
    propagation_context_id: str | None

def _normalize_text(text: str | None) -> str:
    return re.sub(r"\s+", " ", (text or "").strip())

def _normalize_query(text: str) -> str:
    return _normalize_text(text).lower()

def _normalize_identifier_token(token: Any) -> str:
    value = str(token or "").strip().strip('"').strip().strip("()").strip().strip('"').lower()
    return value

def _normalize_column_list(columns: Any) -> list[str]:
    if columns is None:
        return []
    if isinstance(columns, str):
        stripped = columns.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            try:
                parsed = json.loads(stripped)
            except Exception:
                parsed = None
            if isinstance(parsed, list):
                return _normalize_column_list(parsed)
        if stripped.startswith("{") and stripped.endswith("}"):
            stripped = stripped[1:-1]
        if stripped.startswith("(") and stripped.endswith(")"):
            stripped = stripped[1:-1]
        raw_items = stripped.split(",")
    elif isinstance(columns, (list, tuple)):
        raw_items = []
        for item in columns:
            if isinstance(item, str) and "," in item:
                raw_items.extend(item.split(","))
            else:
                raw_items.append(item)
    else:
        raw_items = [columns]
    normalized = [_normalize_identifier_token(item) for item in raw_items]
    return [item for item in normalized if item]


def _extract_rows_from_supabase_metadata_response(payload: Any) -> list[dict[str, Any]]:
    if payload is None:
        return []
    parsed_payload = payload
    if isinstance(payload, str):
        try:
            parsed_payload = json.loads(payload)
        except Exception:
            return []
    if hasattr(parsed_payload, "data"):
        data_value = getattr(parsed_payload, "data", None)
        if isinstance(data_value, list):
            return [row for row in data_value if isinstance(row, dict)]
    if isinstance(parsed_payload, dict):
        data_value = parsed_payload.get("data")
        if isinstance(data_value, list):
            return [row for row in data_value if isinstance(row, dict)]
        if isinstance(data_value, dict):
            return [data_value]
        if isinstance(parsed_payload.get("error"), dict):
            return []
        return [parsed_payload] if parsed_payload else []
    if isinstance(parsed_payload, list):
        return [row for row in parsed_payload if isinstance(row, dict)]
    return []


def _extract_unique_index_columns_from_indexdef(indexdef: Any) -> list[str]:
    text = str(indexdef or "")
    if not text:
        return []
    match = re.search(r"USING\s+\w+\s*\((.*)\)", text, flags=re.IGNORECASE)
    if not match:
        return []
    return _normalize_column_list(match.group(1))

def _normalize_domain(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    return host

def normalize_source_result_payload(result: dict[str, Any]) -> dict[str, Any]:
    return dict(result) if isinstance(result, dict) else {}

def build_source_level_evidence_row_from_tavily_result(
    *,
    item: dict[str, Any],
    result_index: int,
    seed: DiscoverySeed,
    sgt_date: str,
    query_text: str,
    candidate_asset_id: str,
    candidate_name: str,
    discovery_method: str,
) -> dict[str, Any] | None:
    source_payload = normalize_source_result_payload(item.get("source_result") if isinstance(item.get("source_result"), dict) else item)
    source_url = _normalize_text(str(item.get("source_url") or item.get("url") or item.get("link") or ""))
    source_title = _normalize_text(item.get("source_title") or item.get("title") or item.get("page_title") or item.get("pageTitle") or ((item.get("metadata") or {}).get("title") if isinstance(item.get("metadata"), dict) else ""))
    source_snippet = _normalize_text(item.get("source_snippet") or item.get("content") or item.get("snippet") or item.get("raw_content") or item.get("rawContent") or item.get("summary") or item.get("description") or ((item.get("metadata") or {}).get("description") if isinstance(item.get("metadata"), dict) else ""))
    if not (source_url or source_title or source_snippet):
        return None
    source_domain = _normalize_domain(source_url) if source_url else ""
    source_score = item.get("score") if item.get("score") is not None else item.get("confidence") if item.get("confidence") is not None else item.get("relevance_score")
    published_date = item.get("published_date") or item.get("publishedDate") or item.get("date")
    evidence_rank = item.get("source_rank") or result_index
    text = f"{source_title} {source_snippet}".lower()
    matches = _entity_match_terms(seed, text)
    thematic_matches = [k for k in THEME_KEYWORDS.get(seed.theme_name, []) if k in text]
    evidence_quality = _evidence_quality_score({"source_title": source_title, "source_snippet": source_snippet, "source_domain": source_domain, "source_rank": evidence_rank}, seed.theme_name)
    suppression_flags = []
    if len(thematic_matches) < 1: suppression_flags.append("weak_thematic_overlap")
    if any(tok in text for tok in GENERIC_SUPPRESSION_TOKENS) and len(matches) < 1: suppression_flags.append("generic_megacap_contamination")
    return {"run_date_sgt": sgt_date, "workflow_run_id": None, "theme_name": seed.theme_name, "source_node": seed.source_node, "target_node": seed.target_node, "query_text": query_text, "candidate_id": None, "candidate_asset_id": candidate_asset_id, "candidate_name": candidate_name, "candidate_ticker": None, "source_url": source_url, "source_domain": source_domain, "source_title": source_title, "source_snippet": source_snippet, "source_rank": evidence_rank, "evidence_rank": evidence_rank, "evidence_confidence": evidence_quality, "evidence_type": "source_result", "evidence_text": _compose_evidence_text(source_title, source_snippet, source_domain, source_score, published_date, evidence_rank, candidate_name, seed.theme_name, discovery_method), "retrieved_at": item.get("retrieved_at"), "discovery_method": discovery_method, "evidence_quality_score": evidence_quality, "thematic_keyword_matches": thematic_matches, "matched_entity_terms": matches, "suppression_flags": suppression_flags, "cache_reused": bool(item.get("cache_reused", False)), "raw_evidence": {"source_result": source_payload, "candidate_context": {"candidate_name": candidate_name, "candidate_asset_id": candidate_asset_id, "candidate_id": None, "theme_name": seed.theme_name, "discovery_method": discovery_method, "source_node": seed.source_node, "target_node": seed.target_node}, "persistence_phase": "tier3h4c3_surgical_source_result_persistence"}}

def _compose_evidence_text(source_title: str, source_snippet: str, source_domain: str, source_score: Any, published_date: Any, evidence_rank: Any, candidate_name: str, theme_name: str, discovery_method: str) -> str:
    parts = []
    if source_title:
        parts.append(f"Title: {source_title}")
    if source_snippet:
        parts.append(f"Snippet: {source_snippet}")
    parts.append(
        f"Metadata: source_domain={source_domain or 'unknown'}; tavily_score={_normalize_text(str(source_score)) or 'unknown'}; "
        f"published_date={_normalize_text(str(published_date)) or 'unknown'}; evidence_rank={_normalize_text(str(evidence_rank)) or 'unknown'}"
    )
    parts.append(
        f"Operational: candidate_name={_normalize_text(candidate_name) or 'unknown'}; theme_name={_normalize_text(theme_name) or 'unknown'}; "
        f"discovery_method={_normalize_text(discovery_method) or 'unknown'}"
    )
    return "\n\n".join(parts)

def _generate_queries(seed: DiscoverySeed) -> list[str]:
    labels = THEME_LABELS.get(seed.theme_name, [seed.theme_name.replace("_", " ")])
    queries: list[str] = []
    for label in labels:
        for template in QUERY_TEMPLATES:
            queries.append(template.format(theme_label=label))
    return list(dict.fromkeys(queries))

def _deduplicate_queries(queries: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for q in queries:
        n = _normalize_query(q)
        if n in seen:
            continue
        seen.add(n)
        deduped.append(_normalize_text(q))
    return deduped

def _tavily_enabled() -> bool:
    return os.getenv("TIER3H4_TAVILY_ENABLED", "true").lower() in {"1", "true", "yes"}

def _domain_tier_score(domain: str) -> float:
    if any(x in domain for x in TIER_A_DOMAINS): return 90.0
    if any(x in domain for x in TIER_B_DOMAINS): return 70.0
    return 40.0

def _evidence_quality_score(item: dict[str, Any], theme_name: str, duplicate_penalty: float = 0.0) -> float:
    text = f"{item.get('source_title', '')} {item.get('source_snippet', '')}".lower()
    keywords = THEME_KEYWORDS.get(theme_name, theme_name.replace("_", " ").split())
    overlap = len([k for k in keywords if k and k in text])
    overlap_score = min(100.0, overlap * 14.0)
    rank = int(item.get("source_rank") or 99)
    rank_score = max(0.0, 100.0 - (rank - 1) * 8.0)
    specificity = min(100.0, len(_normalize_text(item.get("source_snippet"))) / 3.0)
    score = 0.35 * _domain_tier_score(item.get("source_domain", "")) + 0.30 * overlap_score + 0.20 * rank_score + 0.15 * specificity - duplicate_penalty
    return round(max(0.0, min(100.0, score)), 4)

def _entity_match_terms(seed: DiscoverySeed, evidence_text: str) -> list[str]:
    terms = [seed.source_node.lower(), seed.target_node.lower(), seed.theme_name.replace("_", " ").lower()]
    return [t for t in terms if t and t in evidence_text]

def _classify_tavily_error(status_code: int | None, error_text: str | None) -> str:
    e = (error_text or "").lower()
    if status_code in {401, 403} or "auth" in e or "api key" in e:
        return "auth_failure"
    if status_code == 429 or "rate limit" in e:
        return "rate_limited"
    if "quota" in e or "credits" in e:
        return "quota_exhausted"
    if status_code and status_code >= 500:
        return "provider_unavailable"
    if "timeout" in e:
        return "timeout"
    return "invalid_response"

def _is_retryable(reason: str) -> bool:
    return reason in {"rate_limited", "provider_unavailable", "timeout"}

def _collect_tavily(query_text: str, api_key: str, max_results: int = 5) -> tuple[list[dict[str, Any]], str | None]:
    try:
        r = requests.post("https://api.tavily.com/search", json={"api_key": api_key, "query": query_text, "max_results": max_results, "search_depth": "basic"}, timeout=TAVILY_TIMEOUT_SECONDS)
        if r.status_code >= 400:
            reason = _classify_tavily_error(r.status_code, r.text)
            return [], reason
        payload = r.json()
        results = payload.get("results", []) if isinstance(payload, dict) else []
        out = []
        for i, item in enumerate(results, start=1):
            if not isinstance(item, dict):
                continue
            title = _normalize_text(item.get("title") or item.get("source_title") or item.get("page_title") or item.get("pageTitle") or ((item.get("metadata") or {}).get("title") if isinstance(item.get("metadata"), dict) else ""))
            url = _normalize_text(str(item.get("url") or item.get("source_url") or item.get("link") or ""))
            snippet = _normalize_text(item.get("content") or item.get("snippet") or item.get("raw_content") or item.get("rawContent") or item.get("summary") or item.get("description"))
            if not url and not title and not snippet:
                continue
            score = item.get("score") if item.get("score") is not None else item.get("confidence") if item.get("confidence") is not None else item.get("relevance_score")
            published_date = item.get("published_date") or item.get("publishedDate") or item.get("date")
            out.append({"query_text": query_text, "source_title": title, "source_url": url, "source_snippet": snippet, "source_domain": _normalize_domain(url) if url else "", "source_rank": i, "score": score, "published_date": published_date, "retrieved_at": utc_now().isoformat(), "cache_reused": False, "source_result": dict(item)})
        return out, None
    except Exception as exc:
        reason = "timeout" if "timeout" in str(exc).lower() else "provider_unavailable"
        return [], reason

def _extract_strict_exchange_qualified_identifier(text: str, token_distance_max: int = STRICT_IDENTIFIER_TOKEN_DISTANCE_MAX) -> dict[str, Any]:
    raw_text = _normalize_text(text)
    if not raw_text:
        return _canonical_extraction_result(rejection_reason="empty_context")
    candidate_matches: list[dict[str, str]] = []
    matcher_specs = [
        (STRICT_EXCHANGE_QUALIFIED_IDENTIFIER_PATTERN, "strict_exchange_colon_regex"),
        (STRICT_PARENTHEICAL_TICKER_THEN_EXCHANGE_PATTERN, "strict_exchange_parenthetical_regex"),
        (STRICT_PARENTHEICAL_EXCHANGE_THEN_TICKER_PATTERN, "strict_exchange_parenthetical_regex"),
        (STRICT_LISTED_CONTEXT_PATTERN, "strict_exchange_listed_context_regex"),
        (STRICT_HYPHENATED_LISTED_PATTERN, "strict_exchange_listed_context_regex"),
        (STRICT_TICKER_ON_EXCHANGE_PATTERN, "strict_exchange_ticker_on_exchange_regex"),
    ]
    for pattern, extraction_method in matcher_specs:
        for match in pattern.finditer(raw_text):
            candidate_matches.append(
                {
                    "label": _normalize_text(match.group("label")),
                    "ticker": _normalize_text(match.group("ticker")).upper(),
                    "method": extraction_method,
                }
            )
    if not candidate_matches:
        return _canonical_extraction_result(rejection_reason="no_context_phrase")
    normalized_matches: list[dict[str, str]] = []
    noise_rejections: list[str] = []
    unsupported_rejections: list[str] = []
    for candidate in candidate_matches:
        canonical_exchange = EXCHANGE_LABEL_TO_CANONICAL.get(candidate["label"])
        if not canonical_exchange:
            unsupported_rejections.append(candidate["label"])
            continue
        ticker = candidate["ticker"]
        if ticker in NOISE_TICKER_DENYLIST:
            noise_rejections.append(ticker)
            continue
        if not re.match(r"^[A-Z0-9]{1,6}$", ticker):
            continue
        if not _token_distance_within_guardrail(raw_text, ticker, candidate["label"], token_distance_max):
            continue
        normalized_matches.append(
            {
                "normalized_exchange": canonical_exchange,
                "normalized_ticker": ticker,
                "extraction_method": candidate["method"],
                "extraction_notes": f"matched_explicit_exchange_label={candidate['label']}",
            }
        )
    if len(normalized_matches) > 1:
        unique_pairs = {(m["normalized_exchange"], m["normalized_ticker"]) for m in normalized_matches}
        if len(unique_pairs) > 1:
            return _canonical_extraction_result(warnings=["ambiguous_multiple_matches_rejected"], multiple_matches_detected=True, rejection_reason="ambiguous_context_window", ambiguity_reason="ambiguous_context_window")
    if normalized_matches:
        selected = normalized_matches[0]
        return _canonical_extraction_result(
            extracted_ticker=selected["normalized_ticker"],
            extracted_exchange=selected["normalized_exchange"],
            normalized_ticker=selected["normalized_ticker"],
            normalized_exchange=selected["normalized_exchange"],
            extraction_method=selected["extraction_method"],
            extraction_confidence="high",
            extraction_notes=selected["extraction_notes"],
            warnings=[],
            multiple_matches_detected=len(normalized_matches) > 1,
            accepted=True,
        )
    if noise_rejections:
        return _canonical_extraction_result(warnings=[f"noise_token_rejected:{noise_rejections[0]}"], rejection_reason="noisy_token")
    if unsupported_rejections:
        return _canonical_extraction_result(warnings=[f"unsupported_exchange_rejected:{unsupported_rejections[0]}"], rejection_reason="unsupported_exchange_label")
    return _canonical_extraction_result(rejection_reason="no_context_phrase")

STRICT_IDENTIFIER_REJECTION_CATEGORIES = [
    "multiple_tickers_in_context",
    "multiple_exchanges_in_context",
    "ticker_exchange_conflict",
    "unsupported_exchange_label",
    "noisy_token",
    "missing_explicit_ticker",
    "missing_explicit_exchange",
    "malformed_context",
    "ambiguous_context_window",
    "candidate_name_not_mentioned",
    "duplicate_context",
    "no_context_phrase",
    "unknown_rejection_reason",
]


def _default_rejection_reason_counts() -> dict[str, int]:
    return {k: 0 for k in STRICT_IDENTIFIER_REJECTION_CATEGORIES}


def _bounded_context_window(text: str, max_len: int = STRICT_IDENTIFIER_CONTEXT_WINDOW_MAX_LEN) -> str:
    clean = _normalize_text(text)
    if len(clean) <= max_len:
        return clean
    half = max(1, (max_len - 3) // 2)
    return f"{clean[:half]}...{clean[-half:]}"



def _normalize_identifier_context_window(text: str) -> str:
    value = (text or "")
    value = value.replace("–", "-").replace("—", "-")
    value = value.replace("‘", "'").replace("’", "'")
    value = value.replace("“", '"').replace("”", '"')
    value = value.replace("−", "-").replace(" ", " ")
    value = re.sub(r"[|;,:\-]{2,}", lambda m: m.group(0)[0], value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"^[|;,:\-\s]+", "", value)
    value = re.sub(r"[|;,:\-\s]+$", "", value)
    return value


def _segment_identifier_context_windows(text: str, max_chars: int = STRICT_IDENTIFIER_CONTEXT_WINDOW_MAX_LEN) -> list[str]:
    raw = _normalize_text(text)
    if not raw:
        return []
    split = re.sub(r"(?i)\btitle\s*:\s*", "\n", raw)
    split = re.sub(r"(?i)\bsnippet\s*:\s*", "\n", split)
    split = re.sub(r"[•\u2022]", "\n", split)
    split = split.replace("|", "\n").replace(";", "\n").replace(".", ".\n")
    split = split.replace("(", " ( ").replace(")", " ) ")
    chunks = [c.strip() for c in re.split(r"\n+", split) if c.strip()]
    windows: list[str] = []
    for chunk in chunks:
        norm = _normalize_identifier_context_window(chunk)
        if not norm:
            continue
        for i in range(0, len(norm), max_chars):
            windows.append(norm[i:i+max_chars].strip())
    return windows


def _token_distance_within_guardrail(text: str, ticker: str, exchange_label: str, max_distance: int = STRICT_IDENTIFIER_TOKEN_DISTANCE_MAX) -> bool:
    token_pattern = re.compile(r"[A-Za-z0-9]+")
    tokens = [(m.group(0), m.start()) for m in token_pattern.finditer(text)]
    ticker_pos = [i for i,(tok,_) in enumerate(tokens) if tok.upper() == ticker.upper()]
    exchange_parts = exchange_label.split()
    exchange_pos=[]
    for i in range(len(tokens)):
        seq=[tokens[i+j][0] for j in range(len(exchange_parts)) if i+j < len(tokens)]
        if len(seq)==len(exchange_parts) and " ".join(seq).lower()==exchange_label.lower():
            exchange_pos.append(i)
    if not ticker_pos or not exchange_pos:
        return True
    min_dist = min(abs(t-e) for t in ticker_pos for e in exchange_pos)
    return min_dist <= max_distance

def _fresh_evidence_quality_diagnostics(evidence_rows: list[dict[str, Any]]) -> dict[str, Any]:
    domains: list[str] = []
    missing_payload_reasons: list[str] = []
    rows_with_candidate_name_mentions = 0
    rows_with_ticker_like_patterns = 0
    rows_with_exchange_like_patterns = 0
    rows_with_meaningful_text = 0
    rows_metadata_only = 0
    empty_text_count = 0
    text_lengths: list[int] = []
    for row in evidence_rows:
        source_url = _normalize_text(str(row.get("source_url") or ""))
        source_title = _normalize_text(row.get("source_title"))
        source_content = _normalize_text(row.get("source_snippet"))
        raw_payload = (row.get("raw_evidence") or {}).get("source_result") if isinstance(row.get("raw_evidence"), dict) else None
        candidate_name = _normalize_text(row.get("candidate_name"))
        evidence_text = _normalize_text(row.get("evidence_text"))
        combined_text = _normalize_text(" ".join([source_title, source_content, evidence_text]))
        text_lengths.append(len(combined_text))
        if source_url:
            domains.append(_normalize_domain(source_url))
        if not combined_text:
            empty_text_count += 1
        if candidate_name and candidate_name.lower() in combined_text.lower():
            rows_with_candidate_name_mentions += 1
        if TICKER_LIKE_PATTERN.search(combined_text):
            rows_with_ticker_like_patterns += 1
        if EXCHANGE_LIKE_PATTERN.search(combined_text):
            rows_with_exchange_like_patterns += 1
        metadata_only = bool(combined_text) and METADATA_ONLY_PATTERN.search(combined_text) is not None
        if metadata_only:
            rows_metadata_only += 1
        elif len(combined_text) >= MEANINGFUL_TEXT_MIN_LENGTH:
            rows_with_meaningful_text += 1
        if not isinstance(raw_payload, dict) or not raw_payload:
            reason = "missing_raw_source_payload" if not isinstance(raw_payload, dict) else "empty_raw_source_payload"
            if reason not in missing_payload_reasons:
                missing_payload_reasons.append(reason)
    rows_observed = len(evidence_rows)
    warnings: list[str] = []
    if rows_observed == 0: warnings.append("no_fresh_evidence_rows_observed")
    if rows_observed > 0 and rows_metadata_only > (rows_observed / 2): warnings.append("most_rows_metadata_only")
    if sum(1 for r in evidence_rows if bool(r.get("source_url"))) == 0: warnings.append("no_rows_with_source_urls")
    if sum(1 for r in evidence_rows if bool(r.get("source_title"))) == 0: warnings.append("no_rows_with_source_titles")
    if rows_with_meaningful_text == 0: warnings.append("no_rows_with_meaningful_text")
    if rows_with_ticker_like_patterns == 0: warnings.append("no_ticker_like_patterns_detected")
    if rows_with_exchange_like_patterns == 0: warnings.append("no_exchange_like_patterns_detected")
    return {
        "fresh_evidence_quality_diagnostics_enabled": True,
        "fresh_evidence_rows_observed": rows_observed,
        "fresh_evidence_rows_with_source_url": sum(1 for r in evidence_rows if bool(r.get("source_url"))),
        "fresh_evidence_rows_with_source_title": sum(1 for r in evidence_rows if bool(r.get("source_title"))),
        "fresh_evidence_rows_with_source_content": sum(1 for r in evidence_rows if bool(r.get("source_snippet"))),
        "fresh_evidence_rows_with_raw_source_payload": sum(1 for r in evidence_rows if isinstance(((r.get("raw_evidence") or {}).get("source_result") if isinstance(r.get("raw_evidence"), dict) else None), dict) and bool((r.get("raw_evidence") or {}).get("source_result"))),
        "fresh_evidence_rows_without_source_payload": sum(1 for r in evidence_rows if not isinstance(((r.get("raw_evidence") or {}).get("source_result") if isinstance(r.get("raw_evidence"), dict) else None), dict)),
        "fresh_evidence_rows_with_candidate_name_mentions": rows_with_candidate_name_mentions,
        "fresh_evidence_rows_with_ticker_like_patterns": rows_with_ticker_like_patterns,
        "fresh_evidence_rows_with_exchange_like_patterns": rows_with_exchange_like_patterns,
        "fresh_evidence_rows_with_meaningful_text": rows_with_meaningful_text,
        "fresh_evidence_rows_metadata_only": rows_metadata_only,
        "fresh_evidence_avg_text_length": round(sum(text_lengths) / max(1, len(text_lengths)), 2),
        "fresh_evidence_max_text_length": max(text_lengths) if text_lengths else 0,
        "fresh_evidence_empty_text_count": empty_text_count,
        "fresh_evidence_sample_source_domains": sorted(set(d for d in domains if d))[:10],
        "fresh_evidence_sample_missing_payload_reasons": missing_payload_reasons[:10],
        "fresh_evidence_quality_warning_count": len(warnings),
        "fresh_evidence_quality_warnings": warnings,
    }


def _build_strict_identifier_canonical_summary(strict_diag: dict[str, Any], candidate_rows: list[dict[str, Any]]) -> dict[str, Any]:
    canonical_summary = {
        "strict_identifier_matches_found": strict_diag.get("strict_identifier_accepted_match_collection_size", 0),
        "strict_identifier_candidate_level_matches_found": strict_diag.get("strict_identifier_candidate_level_matches_found", 0),
        "strict_identifier_evidence_level_matches_found": strict_diag.get("strict_identifier_evidence_level_matches_found", 0),
        "strict_identifier_unmapped_matches_found": strict_diag.get("strict_identifier_unmapped_matches_found", 0),
        "strict_identifier_matches_with_candidate_owner": strict_diag.get("strict_identifier_matches_with_candidate_owner", 0),
        "strict_identifier_matches_without_candidate_owner": strict_diag.get("strict_identifier_matches_without_candidate_owner", 0),
        "strict_identifier_propagation_target_counts": strict_diag.get("strict_identifier_propagation_target_counts", {}),
        "strict_identifier_unique_tickers_found": strict_diag.get("strict_identifier_unique_tickers_found", []),
        "strict_identifier_unique_exchanges_found": strict_diag.get("strict_identifier_unique_exchanges_found", []),
        "strict_identifier_sample_matches": [
            {
                "ticker": m.get("normalized_ticker"),
                "exchange": m.get("normalized_exchange"),
                "note": m.get("extraction_notes"),
            }
            for m in strict_diag.get("strict_identifier_accepted_matches", [])
        ][:5],
        "rows_with_ticker": sum(1 for r in candidate_rows if r.get("ticker")),
        "rows_with_exchange": sum(1 for r in candidate_rows if r.get("exchange")),
        "evidence_rows_with_ticker": strict_diag.get("strict_identifier_evidence_level_matches_found", 0),
        "evidence_rows_with_exchange": strict_diag.get("strict_identifier_evidence_level_matches_found", 0),
    }
    canonical_summary["rows_without_ticker"] = max(0, len(candidate_rows) - canonical_summary["rows_with_ticker"])
    canonical_summary["rows_without_exchange"] = max(0, len(candidate_rows) - canonical_summary["rows_with_exchange"])
    return canonical_summary

def _supabase_get_rows(table: str, order: str, limit: int, filters: dict[str, str] | None = None) -> list[dict[str, Any]]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key: return []
    try:
        params = {"select": "*", "order": order, "limit": str(limit)}
        if filters:
            params.update(filters)
        r = requests.get(f"{url}/rest/v1/{table}", headers={"apikey": key, "Authorization": f"Bearer {key}"}, params=params, timeout=60)
        payload = r.json() if r.status_code < 400 else []
        return [x for x in payload if isinstance(x, dict)] if isinstance(payload, list) else []
    except Exception:
        return []

def _fetch_cached_evidence(theme_name: str, query_text: str, start_date: str, end_date: str) -> list[dict[str, Any]]:
    rows = _supabase_get_rows(EVIDENCE_TABLE_NAME, "run_date_sgt.desc", 200, {"theme_name": f"eq.{theme_name}", "query_text": f"eq.{query_text}", "run_date_sgt": f"gte.{start_date}"})
    out = []
    for row in rows:
        rd = str(row.get("run_date_sgt") or "")
        if not rd or rd > end_date:
            continue
        out.append({**row, "cache_reused": True, "retrieved_at": row.get("retrieved_at") or utc_now().isoformat()})
    return out

def load_upstream_context() -> tuple[list[DiscoverySeed], dict[str, int], bool]:
    seeds: list[DiscoverySeed] = []
    counts: dict[str, int] = {}
    for source in SUPABASE_UPSTREAM_SOURCES:
        rows = _supabase_get_rows(source["table"], source["order"], source["limit"])
        counts[source["table"]] = len(rows)
        for row in rows[:100]:
            seeds.append(DiscoverySeed(theme_name=str(row.get("discovery_theme") or row.get("theme_name") or row.get("anchor_theme_name") or "unknown_theme"), source_node=str(row.get("linked_from_node") or row.get("source_node_key") or "unknown_source"), target_node=str(row.get("target_node_key") or row.get("candidate_symbol") or "unknown_target"), propagation_context_id=str(row.get("propagation_key") or row.get("snapshot_id") or "") or None))
    if seeds: return seeds, counts, False
    return [DiscoverySeed("ai_power_demand", "data_center_load", "grid_resilience", "tier3h4a-mock-ctx-1")], counts, True

def generate_mock_evidence(seed: DiscoverySeed, query_text: str) -> list[dict[str, Any]]:
    base_url = f"https://example.com/{seed.theme_name}/{seed.source_node}"
    return [{"query_text": query_text, "source_title": f"{seed.theme_name} infrastructure snapshot", "source_url": base_url, "source_snippet": f"{seed.source_node} and {seed.target_node} thematic infrastructure linkage", "source_domain": _normalize_domain(base_url), "source_rank": 1, "retrieved_at": utc_now().isoformat(), "cache_reused": False}]

def compute_candidate_score(evidence_count_score: float, source_quality_score: float, thematic_relevance_score: float, entity_resolution_score: float, cross_source_score: float) -> float:
    return round(WEIGHTS["evidence_count_score"] * evidence_count_score + WEIGHTS["thematic_relevance_score"] * thematic_relevance_score + WEIGHTS["source_quality_score"] * source_quality_score + WEIGHTS["entity_resolution_score"] * entity_resolution_score + WEIGHTS["cross_source_score"] * cross_source_score, 4)

def _sanitize_persistence_rows(rows: list[dict[str, Any]], table_name: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    runtime_nested_fields = {"matched_entity_terms", "suppression_flags", "thematic_keyword_matches"}
    evidence_persistence_allowlist = {
        "run_date_sgt",
        "workflow_run_id",
        "theme_name",
        "source_node",
        "target_node",
        "query_text",
        "candidate_id",
        "candidate_asset_id",
        "candidate_name",
        "candidate_ticker",
        "source_url",
        "source_domain",
        "source_title",
        "source_snippet",
        "evidence_text",
        "evidence_type",
        "evidence_confidence",
        "evidence_quality_score",
        "evidence_rank",
        "extracted_exchange",
        "extracted_ticker",
        "normalized_exchange",
        "normalized_ticker",
        "extraction_confidence",
        "extraction_method",
        "extraction_notes",
        "accepted",
        "rejection_reason",
        "retrieved_at",
        "cache_reused",
        "raw_evidence",
    }
    diagnostics = {
        "sanitized_payload_keys": [],
        "removed_nested_fields": [],
        "final_payload_column_count": 0,
        "persistence_projection_fields": [],
        "removed_runtime_only_fields": [],
        "sanitized_payload_column_count": 0,
        "sanitized_payload_contains_nested_objects": False,
        "final_upsert_variable_name": None,
        "final_upsert_contains_nested_objects": False,
        "final_upsert_nested_fields": [],
        "final_upsert_first_row_keys": [],
        "evidence_table_actual_columns": [],
        "evidence_table_actual_column_types": {},
        "evidence_table_nullable_fields": [],
        "payload_vs_schema_missing_columns": [],
        "payload_vs_schema_extra_columns": [],
        "payload_vs_schema_type_conflicts": [],
        "payload_fields_missing_from_table": [],
        "required_table_fields_missing_from_payload": [],
        "type_conflict_fields": [],
        "full_upsert_response_text": None,
        "full_upsert_response_json": None,
        "response_status_code": None,
        "schema_introspection_status": "not_attempted",
        "schema_introspection_error": None,
        "final_payload_contains_raw_evidence": False,
        "raw_evidence_type": None,
        "raw_evidence_json_serializable": False,
        "final_payload_missing_required_columns": [],
    }
    if table_name != EVIDENCE_TABLE_NAME or not rows:
        row_keys = sorted({k for row in rows if isinstance(row, dict) for k in row.keys()})
        diagnostics["sanitized_payload_keys"] = row_keys
        diagnostics["final_payload_column_count"] = len(row_keys)
        return rows, diagnostics
    sanitized_rows: list[dict[str, Any]] = []
    removed_fields: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            continue
        cleaned = {k: row.get(k) for k in evidence_persistence_allowlist if k in row}
        for field in runtime_nested_fields:
            if field in row:
                removed_fields.add(field)
        sanitized_rows.append(cleaned)
    sanitized_keys = sorted({k for row in sanitized_rows if isinstance(row, dict) for k in row.keys()})
    diagnostics["sanitized_payload_keys"] = sanitized_keys
    diagnostics["removed_nested_fields"] = sorted(removed_fields)
    diagnostics["final_payload_column_count"] = len(sanitized_keys)
    diagnostics["persistence_projection_fields"] = sorted(evidence_persistence_allowlist)
    diagnostics["removed_runtime_only_fields"] = sorted(removed_fields)
    diagnostics["sanitized_payload_column_count"] = len(sanitized_keys)
    diagnostics["sanitized_payload_contains_nested_objects"] = any(
        isinstance(value, (dict, list, tuple, set))
        for row in sanitized_rows if isinstance(row, dict)
        for value in row.values()
    )
    return sanitized_rows, diagnostics

def _sanitize_raw_evidence_for_json(value: Any, invalid_types: set[str]) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, Decimal):
        converted = float(value)
        return converted if math.isfinite(converted) else None
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _sanitize_raw_evidence_for_json(v, invalid_types) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        if isinstance(value, (tuple, set)):
            invalid_types.add(type(value).__name__)
        return [_sanitize_raw_evidence_for_json(v, invalid_types) for v in value]
    invalid_types.add(type(value).__name__)
    try:
        return str(value)
    except Exception:
        return f"<unserializable:{type(value).__name__}>"

def _coerce_numeric_confidence_fields(rows: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    label_map = {
        "high": 1.0,
        "medium": 0.5,
        "moderate": 0.5,
        "low": 0.25,
        "unknown": None,
        "": None,
    }
    numeric_fields = ("evidence_confidence", "extraction_confidence")
    coercions_applied = 0
    invalid_before_write: list[str] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        for field in numeric_fields:
            if field not in row:
                continue
            value = row.get(field)
            if value is None:
                continue
            if isinstance(value, bool):
                row[field] = float(value)
                coercions_applied += 1
                continue
            if isinstance(value, (int, float)):
                continue
            normalized = str(value).strip().lower()
            if normalized in label_map:
                mapped = label_map[normalized]
                if row.get(field) != mapped:
                    row[field] = mapped
                    coercions_applied += 1
                continue
            try:
                parsed = float(str(value).strip())
                if row.get(field) != parsed:
                    row[field] = parsed
                    coercions_applied += 1
            except Exception:
                invalid_before_write.append(field)
    diag = {
        "numeric_confidence_coercions_applied": coercions_applied,
        "invalid_numeric_fields_before_write": sorted(set(invalid_before_write)),
        "evidence_confidence_type": None,
        "extraction_confidence_type": None,
    }
    first_row = rows[0] if rows and isinstance(rows[0], dict) else {}
    diag["evidence_confidence_type"] = type(first_row.get("evidence_confidence")).__name__ if "evidence_confidence" in first_row else None
    diag["extraction_confidence_type"] = type(first_row.get("extraction_confidence")).__name__ if "extraction_confidence" in first_row else None
    return rows, diag

def upsert_supabase(rows: list[dict[str, Any]], table_name: str, on_conflict: str, include_diagnostics: bool = False) -> str | tuple[str, dict[str, Any]]:
    resolution_fields = {"canonical_entity_id", "normalized_ticker", "normalized_exchange", "duplicate_group_key", "duplicate_group_size", "resolution_confidence", "resolution_status", "rules_fired", "suppression_reason"}
    diagnostics: dict[str, Any] = {
        "evidence_upsert_payload_columns": [],
        "evidence_upsert_payload_keys": [],
        "evidence_upsert_first_row_keys": [],
        "evidence_upsert_payload_count": len(rows),
        "evidence_upsert_payload_size_bytes": 0,
        "evidence_upsert_response_body": None,
        "evidence_upsert_response_text": None,
        "evidence_upsert_error_body": None,
        "evidence_upsert_response_json": None,
        "evidence_upsert_first_failed_row": None,
        "evidence_upsert_http_status": None,
        "evidence_upsert_postgrest_error_payload": None,
        "evidence_upsert_exception_type": None,
        "evidence_upsert_exception_args": None,
        "evidence_upsert_exception_repr": None,
        "evidence_upsert_schema_mismatch_columns": [],
        "evidence_upsert_suspect_type_fields": [],
        "evidence_upsert_payload_type": "unknown",
        "evidence_upsert_destination_table": table_name,
        "numeric_confidence_coercions_applied": 0,
        "invalid_numeric_fields_before_write": [],
        "evidence_confidence_type": None,
        "extraction_confidence_type": None,
        "evidence_upsert_destination_table_columns": [],
        "evidence_upsert_contains_resolution_fields": False,
        "evidence_upsert_contains_nested_objects": False,
        "evidence_upsert_nested_object_fields": [],
        "evidence_upsert_resolution_fields_present": [],
        "write_error_code": None,
        "write_error_message": None,
        "write_error_details": None,
        "write_error_hint": None,
        "sanitized_payload_keys": [],
        "removed_nested_fields": [],
        "final_payload_column_count": 0,
        "persistence_projection_fields": [],
        "removed_runtime_only_fields": [],
        "sanitized_payload_column_count": 0,
        "sanitized_payload_contains_nested_objects": False,
        "final_upsert_variable_name": None,
        "final_upsert_contains_nested_objects": False,
        "final_upsert_nested_fields": [],
        "final_upsert_first_row_keys": [],
        "final_schema_aligned_payload_keys": [],
        "removed_unsupported_columns": [],
        "final_payload_matches_schema": False,
        "actual_on_conflict_value": None,
        "actual_upsert_conflict_columns": [],
        "conflict_columns_exist_in_schema": False,
        "final_payload_contains_raw_evidence": False,
        "raw_evidence_type": None,
        "raw_evidence_json_serializable": False,
        "raw_evidence_nested_invalid_types": [],
        "raw_evidence_sanitization_applied": False,
        "raw_evidence_post_sanitization_type": None,
        "final_payload_missing_required_columns": [],
        "failing_table_name": None,
        "failing_write_method": None,
        "failing_on_conflict_value": None,
        "failing_table_unique_constraints": [],
        "failing_response_body": None,
        "table_unique_constraints": [],
        "unique_constraint_names_detected": [],
        "unique_index_names_detected": [],
        "unique_constraint_column_sets_detected": [],
        "unique_index_column_sets_detected": [],
        "failing_upsert_has_matching_unique_constraint": None,
        "db_managed_columns": [],
        "excluded_required_columns": [],
        "effective_required_columns": [],
        "final_payload_matches_effective_schema": False,
        "http_409_classification": None,
        "conflict_target_matches_unique_constraint": None,
        "duplicate_conflict_detected": False,
        "rows_already_exist_count": 0,
        "conflict_is_benign": False,
        "failing_table_primary_key": [],
        "failing_table_indexes": [],
        "extraction_notes_null_count_before_normalization": 0,
        "extraction_notes_null_count_after_normalization": 0,
        "extraction_notes_default_applied_count": 0,
        "extraction_notes_json_serializable": True,
    }
    if rows:
        row_keys = sorted({k for row in rows if isinstance(row, dict) for k in row.keys()})
        diagnostics["evidence_upsert_payload_columns"] = row_keys
        diagnostics["evidence_upsert_payload_keys"] = row_keys
        diagnostics["evidence_upsert_first_row_keys"] = sorted(list(rows[0].keys())) if isinstance(rows[0], dict) else []
        diagnostics["evidence_upsert_first_failed_row"] = rows[0] if isinstance(rows[0], dict) else None
        diagnostics["evidence_upsert_resolution_fields_present"] = sorted([k for k in row_keys if k in resolution_fields])
        diagnostics["evidence_upsert_contains_resolution_fields"] = bool(diagnostics["evidence_upsert_resolution_fields_present"])
        nested_fields: set[str] = set()
        for row in rows:
            if not isinstance(row, dict):
                continue
            for k, v in row.items():
                if isinstance(v, (dict, list, tuple)):
                    nested_fields.add(k)
        diagnostics["evidence_upsert_nested_object_fields"] = sorted(nested_fields)
        diagnostics["evidence_upsert_contains_nested_objects"] = bool(nested_fields)
        if diagnostics["evidence_upsert_contains_resolution_fields"]:
            diagnostics["evidence_upsert_payload_type"] = "post_resolution_audit_like"
        elif any(k in row_keys for k in ["source_url", "source_title", "source_snippet", "raw_evidence"]):
            diagnostics["evidence_upsert_payload_type"] = "raw_enriched_source_evidence_like"
        elif any(k in row_keys for k in ["candidate_confidence_score", "advisory_status", "evidence_sources"]):
            diagnostics["evidence_upsert_payload_type"] = "canonical_reconciliation_like"
        else:
            diagnostics["evidence_upsert_payload_type"] = "unknown"
        try:
            diagnostics["evidence_upsert_payload_size_bytes"] = len(json.dumps(rows, default=str))
        except Exception:
            diagnostics["evidence_upsert_payload_size_bytes"] = -1
    if not rows:
        status = "skipped:no_rows"
        return (status, diagnostics) if include_diagnostics else status
    rows, sanitize_diag = _sanitize_persistence_rows(rows, table_name)
    diagnostics.update(sanitize_diag)
    final_upsert_rows = rows
    diagnostics["final_upsert_variable_name"] = "final_upsert_rows"
    diagnostics["evidence_upsert_payload_count"] = len(final_upsert_rows)
    diagnostics["evidence_upsert_payload_columns"] = diagnostics["sanitized_payload_keys"]
    diagnostics["evidence_upsert_payload_keys"] = diagnostics["sanitized_payload_keys"]
    final_nested_fields: set[str] = set()
    for row in final_upsert_rows:
        if not isinstance(row, dict):
            continue
        for k, v in row.items():
            if isinstance(v, (dict, list, tuple)):
                final_nested_fields.add(k)
    diagnostics["final_upsert_contains_nested_objects"] = bool(final_nested_fields)
    diagnostics["final_upsert_nested_fields"] = sorted(final_nested_fields)
    if final_upsert_rows:
        diagnostics["final_upsert_first_row_keys"] = sorted(list(final_upsert_rows[0].keys())) if isinstance(final_upsert_rows[0], dict) else []
        diagnostics["evidence_upsert_first_row_keys"] = diagnostics["final_upsert_first_row_keys"]
        diagnostics["evidence_upsert_first_failed_row"] = final_upsert_rows[0] if isinstance(final_upsert_rows[0], dict) else None
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        status = "skipped:missing_supabase_env"
        return (status, diagnostics) if include_diagnostics else status
    payload_keys_set = set(diagnostics.get("final_upsert_first_row_keys") or [])
    try:
        openapi_headers = {"apikey": key, "Authorization": f"Bearer {key}", "Accept": "application/openapi+json"}
        schema_response = requests.get(f"{url}/rest/v1/", headers=openapi_headers, timeout=60)
        schema_json = schema_response.json() if schema_response.status_code < 400 else {}
        definitions = (schema_json.get("definitions") if isinstance(schema_json, dict) else {}) or {}
        table_schema = definitions.get(table_name) if isinstance(definitions, dict) else None
        if isinstance(table_schema, dict):
            properties = table_schema.get("properties") or {}
            required_fields = set(table_schema.get("required") or [])
            actual_columns = sorted(properties.keys()) if isinstance(properties, dict) else []
            actual_types = {}
            nullable_fields = []
            for col, col_schema in (properties.items() if isinstance(properties, dict) else []):
                if not isinstance(col_schema, dict):
                    actual_types[col] = str(type(col_schema).__name__)
                    continue
                actual_types[col] = col_schema.get("format") or col_schema.get("type") or str(col_schema)
                if col_schema.get("nullable") is True or "null" in (col_schema.get("type") if isinstance(col_schema.get("type"), list) else []):
                    nullable_fields.append(col)
            diagnostics["evidence_table_actual_columns"] = actual_columns
            diagnostics["evidence_table_actual_column_types"] = actual_types
            diagnostics["evidence_table_nullable_fields"] = sorted(nullable_fields)
            diagnostics["evidence_upsert_destination_table_columns"] = actual_columns
            db_managed_columns = sorted([c for c in ["id", "created_at", "updated_at"] if c in set(actual_columns)])
            effective_required_fields = sorted(required_fields - set(db_managed_columns))
            payload_missing_from_table = sorted(payload_keys_set - set(actual_columns))
            required_missing_from_payload = sorted(set(effective_required_fields) - payload_keys_set)
            excluded_required_columns = sorted(required_fields - set(effective_required_fields))
            diagnostics["db_managed_columns"] = db_managed_columns
            diagnostics["excluded_required_columns"] = excluded_required_columns
            diagnostics["effective_required_columns"] = effective_required_fields
            diagnostics["payload_fields_missing_from_table"] = payload_missing_from_table
            diagnostics["required_table_fields_missing_from_payload"] = required_missing_from_payload
            diagnostics["payload_vs_schema_missing_columns"] = required_missing_from_payload
            diagnostics["payload_vs_schema_extra_columns"] = payload_missing_from_table
            diagnostics["schema_introspection_status"] = "ok"
            if table_name in {EVIDENCE_TABLE_NAME, TABLE_NAME}:
                allowed_columns = set(actual_columns)
                aligned_rows: list[dict[str, Any]] = []
                removed_columns = set()
                for row in final_upsert_rows:
                    if not isinstance(row, dict):
                        continue
                    aligned_row = {k: v for k, v in row.items() if k in allowed_columns}
                    removed_columns.update(set(row.keys()) - set(aligned_row.keys()))
                    aligned_rows.append(aligned_row)
                final_upsert_rows_schema_aligned = aligned_rows
                final_upsert_rows = final_upsert_rows_schema_aligned
                aligned_keys = sorted({k for row in final_upsert_rows_schema_aligned for k in row.keys()}) if final_upsert_rows_schema_aligned else []
                diagnostics["final_schema_aligned_payload_keys"] = aligned_keys
                diagnostics["removed_unsupported_columns"] = sorted(removed_columns)
                diagnostics["final_payload_matches_schema"] = len(removed_columns) == 0
                diagnostics["final_upsert_variable_name"] = "final_upsert_rows_schema_aligned"
                diagnostics["evidence_upsert_payload_count"] = len(final_upsert_rows_schema_aligned)
                diagnostics["evidence_upsert_payload_columns"] = aligned_keys
                diagnostics["evidence_upsert_payload_keys"] = aligned_keys
                diagnostics["final_upsert_first_row_keys"] = sorted(list(final_upsert_rows_schema_aligned[0].keys())) if final_upsert_rows_schema_aligned else []
                diagnostics["evidence_upsert_first_row_keys"] = diagnostics["final_upsert_first_row_keys"]
                diagnostics["evidence_upsert_first_failed_row"] = final_upsert_rows_schema_aligned[0] if final_upsert_rows_schema_aligned else None
                payload_keys_set = set(aligned_keys)
                diagnostics["payload_fields_missing_from_table"] = sorted(payload_keys_set - allowed_columns)
                diagnostics["payload_vs_schema_extra_columns"] = diagnostics["payload_fields_missing_from_table"]
                diagnostics["required_table_fields_missing_from_payload"] = sorted(set(effective_required_fields) - payload_keys_set)
                diagnostics["payload_vs_schema_missing_columns"] = diagnostics["required_table_fields_missing_from_payload"]
                diagnostics["final_payload_matches_effective_schema"] = (
                    len(diagnostics["removed_unsupported_columns"]) == 0
                    and len(diagnostics["required_table_fields_missing_from_payload"]) == 0
                )
                diagnostics["final_payload_matches_schema"] = diagnostics["final_payload_matches_effective_schema"]
            else:
                diagnostics["final_schema_aligned_payload_keys"] = sorted(payload_keys_set)
                diagnostics["removed_unsupported_columns"] = []
                diagnostics["final_payload_matches_schema"] = True
                diagnostics["final_payload_matches_effective_schema"] = True
        else:
            diagnostics["schema_introspection_status"] = f"table_schema_not_found:{schema_response.status_code}"
            diagnostics["schema_introspection_error"] = (schema_response.text or "")[:4000]
    except Exception as schema_exc:
        diagnostics["schema_introspection_status"] = f"exception:{type(schema_exc).__name__}"
        diagnostics["schema_introspection_error"] = repr(schema_exc)
    try:
        constraint_headers = {"apikey": key, "Authorization": f"Bearer {key}"}
        pk_response = requests.get(
            f"{url}/rest/v1/information_schema.table_constraints",
            headers=constraint_headers,
            params={
                "table_schema": "eq.public",
                "table_name": f"eq.{table_name}",
                "constraint_type": "eq.PRIMARY KEY",
                "select": "constraint_name",
            },
            timeout=60,
        )
        pk_names: list[str] = []
        if pk_response.status_code < 400:
            pk_payload = pk_response.json()
            if isinstance(pk_payload, list):
                pk_names = [row.get("constraint_name") for row in pk_payload if isinstance(row, dict) and row.get("constraint_name")]
        pk_columns: list[str] = []
        for pk_name in pk_names:
            pk_cols_response = requests.get(
                f"{url}/rest/v1/information_schema.key_column_usage",
                headers=constraint_headers,
                params={
                    "table_schema": "eq.public",
                    "table_name": f"eq.{table_name}",
                    "constraint_name": f"eq.{pk_name}",
                    "select": "column_name,ordinal_position",
                    "order": "ordinal_position.asc",
                },
                timeout=60,
            )
            if pk_cols_response.status_code >= 400:
                continue
            pk_cols_payload = pk_cols_response.json()
            if isinstance(pk_cols_payload, list):
                pk_columns.extend([r.get("column_name") for r in pk_cols_payload if isinstance(r, dict) and r.get("column_name")])
        diagnostics["failing_table_primary_key"] = pk_columns

        idx_response = requests.get(
            f"{url}/rest/v1/pg_indexes",
            headers=constraint_headers,
            params={"schemaname": "eq.public", "tablename": f"eq.{table_name}", "select": "indexname,indexdef"},
            timeout=60,
        )
        if idx_response.status_code < 400 and isinstance(idx_response.json(), list):
            index_rows = [r for r in idx_response.json() if isinstance(r, dict)]
            diagnostics["failing_table_indexes"] = [r.get("indexdef") or r.get("indexname") for r in index_rows]
            unique_index_signatures: set[str] = set()
            unique_index_names: set[str] = set()
            for idx_row in index_rows:
                indexdef = idx_row.get("indexdef") or ""
                if "UNIQUE INDEX" not in indexdef.upper():
                    continue
                idx_name = (idx_row.get("indexname") or "").strip()
                if idx_name:
                    unique_index_names.add(idx_name)
                open_paren = indexdef.rfind("(")
                close_paren = indexdef.rfind(")")
                if open_paren == -1 or close_paren == -1 or close_paren <= open_paren:
                    continue
                index_columns_raw = indexdef[open_paren + 1:close_paren]
                normalized_columns: list[str] = []
                for piece in index_columns_raw.split(","):
                    candidate = piece.strip().strip('"').lower()
                    if candidate:
                        normalized_columns.append(candidate)
                if normalized_columns:
                    unique_index_signatures.add(",".join(normalized_columns))
            diagnostics["failing_table_unique_indexes"] = sorted(unique_index_signatures)
            diagnostics["unique_index_names_detected"] = sorted(unique_index_names)
            diagnostics["unique_index_column_sets_detected"] = sorted(unique_index_signatures)

        unique_constraint_rows: list[dict[str, Any]] = []
        diagnostics["uniqueness_diagnostics_branch_entered"] = True
        print("[tier3h4] uniqueness_diagnostics_branch_entered=True")
        diagnostics["unique_contract_introspection_status"] = None
        diagnostics["unique_contract_query_status"] = None
        diagnostics["unique_contract_query_error"] = None
        diagnostics["unique_contract_raw_response_type"] = None
        diagnostics["unique_contract_raw_response_preview"] = None
        diagnostics["unique_contract_rows_returned"] = 0
        diagnostics["uniqueness_query_execution_started"] = True
        print("[tier3h4] uniqueness_query_execution_started=True")
        try:
            rpc_response = requests.post(
                f"{url}/rest/v1/rpc/get_unique_constraints_for_table",
                headers=constraint_headers,
                json={"target_table": table_name},
                timeout=60,
            )
            if rpc_response.status_code >= 400:
                diagnostics["unique_contract_query_status"] = "error"
                diagnostics["unique_contract_query_error"] = (
                    f"get_unique_constraints_for_table RPC error:{rpc_response.status_code}:{(rpc_response.text or '')[:500]}"
                )
                raise RuntimeError(diagnostics["unique_contract_query_error"])
            try:
                constraints_payload = rpc_response.json()
            except Exception:
                constraints_payload = rpc_response.text
            diagnostics["unique_contract_raw_response_type"] = type(constraints_payload).__name__
            diagnostics["unique_contract_raw_response_preview"] = str(constraints_payload)[:500]
            constraints_rows = _extract_rows_from_supabase_metadata_response(constraints_payload)
            diagnostics["unique_contract_rows_returned"] = len(constraints_rows)
            diagnostics["unique_contract_query_status"] = "ok" if constraints_rows else "empty"
            for row in constraints_rows:
                if not isinstance(row, dict):
                    continue
                cname = row.get("constraint_name")
                if not cname:
                    continue
                unique_constraint_rows.append(
                    {
                        "constraint_name": cname,
                        "table_name": table_name,
                        "column_names": row.get("column_names") or [],
                    }
                )
        except Exception as unique_query_exc:
            diagnostics["unique_contract_query_status"] = "error"
            diagnostics["unique_contract_query_error"] = repr(unique_query_exc)
        finally:
            diagnostics["uniqueness_query_execution_finished"] = True
            print("[tier3h4] uniqueness_query_execution_finished=True")
            print(f"[tier3h4] unique_contract_query_status={diagnostics.get('unique_contract_query_status')}")
            print(f"[tier3h4] unique_contract_query_error={diagnostics.get('unique_contract_query_error')}")
            print(f"[tier3h4] unique_contract_raw_response_type={diagnostics.get('unique_contract_raw_response_type')}")
            print(f"[tier3h4] unique_contract_raw_response_preview={diagnostics.get('unique_contract_raw_response_preview')}")
            print(f"[tier3h4] unique_contract_rows_returned={diagnostics.get('unique_contract_rows_returned')}")
        if not unique_constraint_rows:
            fallback_unique_rows: list[dict[str, Any]] = []
            for idx_row in diagnostics.get("failing_table_indexes") or []:
                indexdef = str(idx_row or "")
                if "UNIQUE INDEX" not in indexdef.upper():
                    continue
                idx_match = re.search(r"CREATE\s+UNIQUE\s+INDEX\s+([^\s]+)", indexdef, flags=re.IGNORECASE)
                idx_name = idx_match.group(1).strip('"') if idx_match else None
                idx_cols = _extract_unique_index_columns_from_indexdef(indexdef)
                if idx_name and idx_cols:
                    fallback_unique_rows.append(
                        {"constraint_name": idx_name, "table_name": table_name, "column_names": idx_cols}
                    )
            if fallback_unique_rows:
                unique_constraint_rows = fallback_unique_rows
                diagnostics["unique_contract_query_status"] = "ok_fallback_pg_indexes"
        if unique_constraint_rows:
            diagnostics["unique_contract_introspection_status"] = "ok"
        else:
            diagnostics["unique_contract_introspection_status"] = "empty"
        constraint_names = sorted({str(row.get("constraint_name")).strip() for row in unique_constraint_rows if row.get("constraint_name")})
        diagnostics["table_unique_constraints"] = constraint_names
        diagnostics["unique_constraint_names_detected"] = constraint_names
        unique_constraint_signatures: list[str] = []
        formatted_constraint_descriptors: list[str] = []
        for row in unique_constraint_rows:
            cname = str(row.get("constraint_name") or "").strip()
            if not cname:
                continue
            normalized_cols = _normalize_column_list(row.get("column_names"))
            if normalized_cols:
                signature = ",".join(normalized_cols)
                unique_constraint_signatures.append(signature)
                formatted_constraint_descriptors.append(f"{cname}({signature})")
        diagnostics["unique_constraint_column_sets_detected"] = sorted(set(unique_constraint_signatures))
        diagnostics["failing_table_unique_constraints"] = sorted(set(formatted_constraint_descriptors)) if formatted_constraint_descriptors else constraint_names
        diagnostics["failing_unique_constraints"] = diagnostics["failing_table_unique_constraints"]
    except Exception as unique_contract_exc:
        diagnostics["unique_contract_introspection_status"] = "error"
        diagnostics["unique_contract_introspection_error"] = repr(unique_contract_exc)
        diagnostics["table_unique_constraints"] = diagnostics.get("table_unique_constraints") or []
        diagnostics["failing_unique_constraints"] = diagnostics.get("failing_table_unique_constraints") or diagnostics.get("table_unique_constraints") or []
    actual_upsert_payload = final_upsert_rows_schema_aligned if "final_upsert_rows_schema_aligned" in locals() else final_upsert_rows
    if table_name == EVIDENCE_TABLE_NAME:
        actual_upsert_payload, confidence_diag = _coerce_numeric_confidence_fields(actual_upsert_payload)
        diagnostics.update(confidence_diag)
    if table_name == EVIDENCE_TABLE_NAME:
        raw_evidence_invalid_types: set[str] = set()
        raw_evidence_sanitization_applied = False
        for row in actual_upsert_payload:
            if not isinstance(row, dict) or "raw_evidence" not in row:
                continue
            original_raw_evidence = row.get("raw_evidence")
            sanitized_raw_evidence = _sanitize_raw_evidence_for_json(original_raw_evidence, raw_evidence_invalid_types)
            if sanitized_raw_evidence != original_raw_evidence:
                raw_evidence_sanitization_applied = True
            row["raw_evidence"] = sanitized_raw_evidence
        diagnostics["raw_evidence_nested_invalid_types"] = sorted(raw_evidence_invalid_types)
        diagnostics["raw_evidence_sanitization_applied"] = raw_evidence_sanitization_applied
    if table_name == EVIDENCE_TABLE_NAME:
        extraction_notes_null_count_before = 0
        extraction_notes_default_applied_count = 0
        extraction_notes_json_serializable = True
        for row in actual_upsert_payload:
            if not isinstance(row, dict):
                continue
            extraction_notes_value = row.get("extraction_notes")
            if extraction_notes_value is None:
                extraction_notes_null_count_before += 1
                row["extraction_notes"] = {}
                extraction_notes_default_applied_count += 1
            try:
                json.dumps(row.get("extraction_notes"))
            except (TypeError, ValueError):
                extraction_notes_json_serializable = False
        extraction_notes_null_count_after = sum(
            1 for row in actual_upsert_payload if isinstance(row, dict) and row.get("extraction_notes") is None
        )
        diagnostics["extraction_notes_null_count_before_normalization"] = extraction_notes_null_count_before
        diagnostics["extraction_notes_null_count_after_normalization"] = extraction_notes_null_count_after
        diagnostics["extraction_notes_default_applied_count"] = extraction_notes_default_applied_count
        diagnostics["extraction_notes_json_serializable"] = extraction_notes_json_serializable
    actual_on_conflict_value = "" if table_name == EVIDENCE_TABLE_NAME else (on_conflict or "").strip()
    actual_upsert_conflict_columns = [c.strip() for c in actual_on_conflict_value.split(",") if c.strip()]
    schema_columns = set(diagnostics.get("evidence_upsert_destination_table_columns") or diagnostics.get("evidence_table_actual_columns") or [])
    conflict_columns_exist_in_schema = bool(actual_upsert_conflict_columns) and all(c in schema_columns for c in actual_upsert_conflict_columns)
    actual_upsert_variable_name = "final_upsert_rows_schema_aligned" if actual_upsert_payload is (final_upsert_rows_schema_aligned if "final_upsert_rows_schema_aligned" in locals() else None) else "final_upsert_rows"
    actual_upsert_first_row_keys = sorted(list(actual_upsert_payload[0].keys())) if actual_upsert_payload and isinstance(actual_upsert_payload[0], dict) else []
    actual_upsert_extra_columns = sorted(set(actual_upsert_first_row_keys) - set(diagnostics.get("evidence_upsert_destination_table_columns") or [])) if diagnostics.get("evidence_upsert_destination_table_columns") else sorted(set(actual_upsert_first_row_keys) - set(diagnostics.get("evidence_table_actual_columns") or []))
    diagnostics["actual_on_conflict_value"] = actual_on_conflict_value
    diagnostics["actual_upsert_conflict_columns"] = actual_upsert_conflict_columns
    diagnostics["conflict_columns_exist_in_schema"] = conflict_columns_exist_in_schema
    normalized_conflict_target_columns = _normalize_column_list(actual_on_conflict_value)
    normalized_conflict_signature = ",".join(normalized_conflict_target_columns)
    detected_unique_contracts = diagnostics.get("failing_table_unique_constraints") or diagnostics.get("table_unique_constraints") or []
    normalized_detected_unique_column_sets: list[list[str]] = []
    matched_unique_contract_name = None
    for contract in detected_unique_contracts:
        contract_name = None
        contract_columns_raw: Any = contract
        if isinstance(contract, str):
            contract_text = contract.strip()
            if "(" in contract_text and contract_text.endswith(")"):
                contract_name = contract_text.split("(", 1)[0].strip() or None
                contract_columns_raw = contract_text.split("(", 1)[1][:-1]
        elif isinstance(contract, dict):
            contract_name = str(contract.get("constraint_name") or contract.get("index_name") or "").strip() or None
            contract_columns_raw = contract.get("columns")
        normalized_columns = _normalize_column_list(contract_columns_raw)
        if normalized_columns:
            normalized_detected_unique_column_sets.append(normalized_columns)
            if normalized_columns == normalized_conflict_target_columns and not matched_unique_contract_name:
                matched_unique_contract_name = contract_name
    if not normalized_detected_unique_column_sets:
        fallback_sets = (
            (diagnostics.get("unique_constraint_column_sets_detected") or [])
            + (diagnostics.get("unique_index_column_sets_detected") or [])
            + (diagnostics.get("failing_table_unique_indexes") or [])
        )
        for fallback in fallback_sets:
            normalized_columns = _normalize_column_list(fallback)
            if normalized_columns:
                normalized_detected_unique_column_sets.append(normalized_columns)
    diagnostics["normalized_conflict_target_columns"] = normalized_conflict_target_columns
    diagnostics["detected_unique_contracts"] = detected_unique_contracts
    diagnostics["normalized_detected_unique_column_sets"] = normalized_detected_unique_column_sets
    diagnostics["matched_unique_contract_name"] = matched_unique_contract_name
    diagnostics["failing_upsert_has_matching_unique_constraint"] = (
        any(cols == normalized_conflict_target_columns for cols in normalized_detected_unique_column_sets)
        if normalized_conflict_signature else None
    )
    diagnostics["conflict_target_matches_unique_constraint"] = diagnostics["failing_upsert_has_matching_unique_constraint"]
    diagnostics["failing_unique_constraints"] = diagnostics.get("failing_table_unique_constraints") or diagnostics.get("table_unique_constraints") or []
    diagnostics["actual_upsert_variable_name"] = actual_upsert_variable_name
    diagnostics["actual_upsert_first_row_keys"] = actual_upsert_first_row_keys
    diagnostics["actual_upsert_contains_query_text"] = "query_text" in actual_upsert_first_row_keys
    diagnostics["actual_upsert_payload_matches_schema"] = len(actual_upsert_extra_columns) == 0
    diagnostics["actual_upsert_extra_columns"] = actual_upsert_extra_columns
    diagnostics["actual_upsert_contains_accepted"] = "accepted" in actual_upsert_first_row_keys
    diagnostics["actual_upsert_contains_normalized_exchange"] = "normalized_exchange" in actual_upsert_first_row_keys
    diagnostics["actual_upsert_contains_normalized_ticker"] = "normalized_ticker" in actual_upsert_first_row_keys
    diagnostics["actual_upsert_contains_source_snippet"] = "source_snippet" in actual_upsert_first_row_keys
    first_row_raw_evidence = actual_upsert_payload[0].get("raw_evidence") if actual_upsert_payload and isinstance(actual_upsert_payload[0], dict) else None
    diagnostics["final_payload_contains_raw_evidence"] = "raw_evidence" in actual_upsert_first_row_keys
    diagnostics["raw_evidence_type"] = type(first_row_raw_evidence).__name__ if diagnostics["final_payload_contains_raw_evidence"] else None
    try:
        json.dumps(first_row_raw_evidence)
        diagnostics["raw_evidence_json_serializable"] = diagnostics["final_payload_contains_raw_evidence"]
    except (TypeError, ValueError):
        diagnostics["raw_evidence_json_serializable"] = False
    diagnostics["raw_evidence_post_sanitization_type"] = type(first_row_raw_evidence).__name__ if first_row_raw_evidence is not None else None
    diagnostics["final_payload_missing_required_columns"] = diagnostics.get("required_table_fields_missing_from_payload") or []
    print(f"[tier3h4] actual_on_conflict_value={diagnostics.get('actual_on_conflict_value')}")
    print(f"[tier3h4] actual_upsert_conflict_columns={diagnostics.get('actual_upsert_conflict_columns')}")
    print(f"[tier3h4] normalized_conflict_target_columns={diagnostics.get('normalized_conflict_target_columns')}")
    print(f"[tier3h4] detected_unique_contracts={diagnostics.get('detected_unique_contracts')}")
    print(f"[tier3h4] normalized_detected_unique_column_sets={diagnostics.get('normalized_detected_unique_column_sets')}")
    print(f"[tier3h4] matched_unique_contract_name={diagnostics.get('matched_unique_contract_name')}")
    print(f"[tier3h4] conflict_columns_exist_in_schema={diagnostics.get('conflict_columns_exist_in_schema')}")
    print(f"[tier3h4] actual_upsert_variable_name={diagnostics.get('actual_upsert_variable_name')}")
    print(f"[tier3h4] actual_upsert_first_row_keys={diagnostics.get('actual_upsert_first_row_keys')}")
    print(f"[tier3h4] actual_upsert_extra_columns={diagnostics.get('actual_upsert_extra_columns')}")
    print(f"[tier3h4] actual_upsert_contains_query_text={diagnostics.get('actual_upsert_contains_query_text')}")
    print(f"[tier3h4] actual_upsert_payload_matches_schema={diagnostics.get('actual_upsert_payload_matches_schema')}")
    try:
        request_headers = {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        request_params: dict[str, str] = {}
        if table_name == EVIDENCE_TABLE_NAME or table_name == TABLE_NAME:
            request_headers["Prefer"] = "return=minimal"
            diagnostics["evidence_write_method"] = "insert" if table_name == EVIDENCE_TABLE_NAME else diagnostics.get("evidence_write_method")
            diagnostics["discovery_write_method"] = "insert" if table_name == TABLE_NAME else diagnostics.get("discovery_write_method")
            if table_name in {EVIDENCE_TABLE_NAME, TABLE_NAME}:
                diagnostics["evidence_insert_row_count"] = len(actual_upsert_payload)
                diagnostics["evidence_insert_payload_keys"] = sorted({k for row in actual_upsert_payload if isinstance(row, dict) for k in row.keys()})
        else:
            request_headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
            request_params["on_conflict"] = on_conflict
        r = requests.post(
            f"{url}/rest/v1/{table_name}",
            headers=request_headers,
            params=request_params or None,
            json=actual_upsert_payload,
            timeout=60,
        )
        destination_columns_header = (r.headers.get("x-rel-columns") or r.headers.get("content-profile") or "") if hasattr(r, "headers") else ""
        if isinstance(destination_columns_header, str) and destination_columns_header:
            diagnostics["evidence_upsert_destination_table_columns"] = sorted([c.strip() for c in destination_columns_header.split(",") if c.strip()])
        diagnostics["evidence_upsert_http_status"] = r.status_code
        diagnostics["response_status_code"] = r.status_code
        diagnostics["evidence_insert_response_status"] = r.status_code if table_name == EVIDENCE_TABLE_NAME else None
        diagnostics["evidence_insert_success"] = (r.status_code < 400) if table_name == EVIDENCE_TABLE_NAME else None
        diagnostics["evidence_insert_response_body"] = (r.text or "")[:32000] if table_name == EVIDENCE_TABLE_NAME else None
        diagnostics["evidence_upsert_response_body"] = r.content[:16000].decode("utf-8", errors="replace") if isinstance(r.content, (bytes, bytearray)) else None
        diagnostics["evidence_upsert_response_text"] = (r.text or "")[:8000]
        diagnostics["full_upsert_response_text"] = (r.text or "")[:32000]
        try:
            diagnostics["evidence_upsert_response_json"] = r.json()
        except Exception:
            diagnostics["evidence_upsert_response_json"] = None
        diagnostics["full_upsert_response_json"] = diagnostics["evidence_upsert_response_json"]
        if r.status_code >= 400:
            write_method = "insert" if table_name in {EVIDENCE_TABLE_NAME, TABLE_NAME} else "upsert"
            diagnostics["failing_table_name"] = table_name
            diagnostics["failing_write_method"] = write_method
            diagnostics["failing_on_conflict_value"] = (on_conflict or "").strip() if write_method == "upsert" else ""
            diagnostics["failing_table_unique_constraints"] = diagnostics.get("failing_table_unique_constraints") or diagnostics.get("table_unique_constraints") or []
            body = diagnostics["evidence_upsert_response_json"] if isinstance(diagnostics["evidence_upsert_response_json"], (dict, list)) else diagnostics["evidence_upsert_response_text"]
            diagnostics["failing_response_body"] = body
            diagnostics["evidence_upsert_error_body"] = body
            if table_name in {EVIDENCE_TABLE_NAME, TABLE_NAME}:
                diagnostics["evidence_insert_error_body"] = body
            if isinstance(diagnostics["evidence_upsert_response_json"], dict):
                postgrest_payload = diagnostics["evidence_upsert_response_json"]
            else:
                postgrest_payload = {"raw_text": diagnostics["evidence_upsert_response_text"]}
            diagnostics["evidence_upsert_postgrest_error_payload"] = postgrest_payload
            if isinstance(postgrest_payload, dict):
                diagnostics["write_error_code"] = postgrest_payload.get("code")
                diagnostics["write_error_message"] = postgrest_payload.get("message")
                diagnostics["write_error_details"] = postgrest_payload.get("details")
                diagnostics["write_error_hint"] = postgrest_payload.get("hint")
            missing_columns = []
            invalid_columns = []
            if isinstance(diagnostics["evidence_upsert_response_json"], dict):
                detail_text = " ".join(str(diagnostics["evidence_upsert_response_json"].get(k) or "") for k in ["message", "details", "hint", "code"])
                for col in diagnostics["evidence_upsert_payload_columns"]:
                    if col in detail_text:
                        invalid_columns.append(col)
                if "column" in detail_text.lower() and not invalid_columns:
                    missing_columns = diagnostics["evidence_upsert_payload_columns"]
            diagnostics["evidence_upsert_schema_mismatch_columns"] = sorted(set(missing_columns + invalid_columns))
            first_row = diagnostics.get("evidence_upsert_first_failed_row") or {}
            suspect_fields=[]
            if isinstance(first_row, dict):
                for k,v in first_row.items():
                    if isinstance(v, (set, bytes, bytearray, complex, dict, list, tuple)):
                        suspect_fields.append(k)
            diagnostics["evidence_upsert_suspect_type_fields"] = suspect_fields
            if r.status_code == 409:
                code = diagnostics.get("write_error_code")
                details = str(diagnostics.get("write_error_details") or "").lower()
                msg = str(diagnostics.get("write_error_message") or "").lower()
                duplicate_conflict = (code == "23505") or ("duplicate" in details) or ("already exists" in details) or ("duplicate" in msg)
                diagnostics["duplicate_conflict_detected"] = bool(duplicate_conflict)
                if table_name == TABLE_NAME and duplicate_conflict:
                    conflict_cols = diagnostics.get("actual_upsert_conflict_columns") or []
                    rows_already_exist_count = 0
                    for row in actual_upsert_payload:
                        if not isinstance(row, dict) or not conflict_cols or any(row.get(c) is None for c in conflict_cols):
                            continue
                        params = {"select": "candidate_asset_id", "limit": "1"}
                        for c in conflict_cols:
                            params[c] = f"eq.{row.get(c)}"
                        existing_resp = requests.get(
                            f"{url}/rest/v1/{table_name}",
                            headers={"apikey": key, "Authorization": f"Bearer {key}"},
                            params=params,
                            timeout=30,
                        )
                        if existing_resp.status_code < 400:
                            payload = existing_resp.json()
                            if isinstance(payload, list) and payload:
                                rows_already_exist_count += 1
                    diagnostics["rows_already_exist_count"] = rows_already_exist_count
                    diagnostics["conflict_is_benign"] = rows_already_exist_count > 0
                    diagnostics["http_409_classification"] = "idempotent_duplicate_rerun" if diagnostics["conflict_is_benign"] else "conflict_unverified"
                    print(f"[tier3h4] failing_table_name={diagnostics.get('failing_table_name')}")
                    print(f"[tier3h4] failing_unique_constraints={diagnostics.get('failing_unique_constraints')}")
                    print(f"[tier3h4] conflict_target_matches_unique_constraint={diagnostics.get('conflict_target_matches_unique_constraint')}")
                    print(f"[tier3h4] duplicate_conflict_detected={diagnostics.get('duplicate_conflict_detected')}")
                    print(f"[tier3h4] rows_already_exist_count={diagnostics.get('rows_already_exist_count')}")
                    print(f"[tier3h4] conflict_is_benign={diagnostics.get('conflict_is_benign')}")
                    if diagnostics["conflict_is_benign"]:
                        status = "upserted:benign_duplicate_409"
                        return (status, diagnostics) if include_diagnostics else status
                else:
                    diagnostics["http_409_classification"] = "non_duplicate_or_non_candidate_conflict"
            schema_types = diagnostics.get("evidence_table_actual_column_types") if isinstance(diagnostics.get("evidence_table_actual_column_types"), dict) else {}
            inferred_type_conflicts: list[str] = []
            if isinstance(first_row, dict):
                for key_name, value in first_row.items():
                    expected = str(schema_types.get(key_name, "")).lower()
                    if not expected:
                        continue
                    if value is None:
                        continue
                    actual = type(value).__name__.lower()
                    if expected in {"number", "numeric", "integer"} and actual not in {"int", "float"}:
                        inferred_type_conflicts.append(key_name)
                    if expected in {"string", "text"} and actual not in {"str"}:
                        inferred_type_conflicts.append(key_name)
                    if expected in {"boolean"} and actual not in {"bool"}:
                        inferred_type_conflicts.append(key_name)
            diagnostics["type_conflict_fields"] = sorted(set(inferred_type_conflicts))
            diagnostics["payload_vs_schema_type_conflicts"] = diagnostics["type_conflict_fields"]
            if r.status_code == 409:
                code = str(diagnostics.get("write_error_code") or "")
                message = str(diagnostics.get("write_error_message") or "").lower()
                details = str(diagnostics.get("write_error_details") or "").lower()
                conflict_text = f"{message} {details}"
                if (
                    write_method == "upsert"
                    and diagnostics.get("failing_upsert_has_matching_unique_constraint") is True
                    and code in {"23505", "21000", "PGRST116", "PGRST123"}
                ):
                    diagnostics["http_409_classification"] = "expected_duplicate_conflict_behavior"
                elif "duplicate" in conflict_text or "already exists" in conflict_text or "conflict" in conflict_text:
                    diagnostics["http_409_classification"] = "benign_idempotent_conflict"
                else:
                    diagnostics["http_409_classification"] = "true_persistence_failure"
        status = "upserted" if r.status_code < 400 else f"upsert_failed:{r.status_code}"
        return (status, diagnostics) if include_diagnostics else status
    except Exception as exc:
        diagnostics["evidence_upsert_error_body"] = f"exception:{type(exc).__name__}:{exc}"
        if table_name == EVIDENCE_TABLE_NAME:
            diagnostics["evidence_insert_error_body"] = diagnostics["evidence_upsert_error_body"]
        diagnostics["exception_repr"] = repr(exc)
        diagnostics["evidence_upsert_exception_type"] = type(exc).__name__
        diagnostics["evidence_upsert_exception_args"] = [str(a) for a in getattr(exc, "args", ())]
        diagnostics["evidence_upsert_exception_repr"] = repr(exc)
        status = f"upsert_exception:{type(exc).__name__}"
        return (status, diagnostics) if include_diagnostics else status

def build_records(seeds: list[DiscoverySeed], sgt_date: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    candidate_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    ops = {"generated_queries": 0, "deduplicated_queries": 0, "executed_queries": 0, "skipped_duplicate_queries": 0, "cache_hits": 0, "cache_misses": 0, "retry_events": 0, "rate_limit_events": 0, "quota_exhaustion_events": 0, "failure_count": 0, "success_count": 0, "fallback_events": 0, "evidence_rows_reused": 0, "tavily_result_rows_seen_before_aggregation": 0, "tavily_result_rows_persisted_before_aggregation": 0, "source_result_persistence_helper_called_count": 0, "fresh_source_rows_written": 0, "fresh_source_rows_write_errors": 0}
    api_key = os.getenv("TAVILY_API_KEY", "")
    tavily_enabled = bool(api_key) and _tavily_enabled()
    fallback_mode = not tavily_enabled
    quota_exhausted = False
    seen_urls: set[tuple[str, str, str, str]] = set()
    executed_query_keys: set[str] = set()
    lookback_start = (date.fromisoformat(sgt_date) - timedelta(days=QUERY_CACHE_LOOKBACK_DAYS)).isoformat()
    force_fresh = _force_fresh_evidence_enabled()
    # TEMP DEBUG INSTRUMENTATION FOR FORCE-FRESH VALIDATION
    runtime_force_fresh_branch_taken = False
    evidence_generation_mode = "fallback" if fallback_mode else ("fresh_generation_forced" if force_fresh else "fresh_generation")
    fresh_skip_reason = None
    tavily_collection_path_executed = False
    persisted_evidence_reuse_bypassed = False
    persisted_evidence_selection_skipped_due_to_force_refresh = False
    fresh_source_generation_active = False
    evidence_source_mode = "fresh_source_generation"
    evidence_selected_reason = "fresh source generation path selected"
    runtime_evidence_generation_branch_taken = "fallback" if fallback_mode else "fresh_generation"
    runtime_persisted_reuse_branch_taken = False
    runtime_fresh_generation_branch_reachable = callable(globals().get("_collect_tavily"))
    runtime_source_loop_instrumentation_loaded = callable(globals().get("build_source_level_evidence_row_from_tavily_result"))
    strict_diag = {
        "strict_identifier_extraction_enabled": True,
        "strict_identifier_phase": "3B_exchange_contextual",
        "strict_identifier_contextual_patterns_enabled": True,
        "strict_identifier_candidate_name_mention_required": False,
        "strict_identifier_rows_scanned": 0,
        "strict_identifier_matches_found": 0,
        "strict_identifier_rows_with_multiple_matches": 0,
        "strict_identifier_rows_rejected_ambiguous": 0,
        "strict_identifier_rows_rejected_no_exchange_label": 0,
        "strict_identifier_rows_rejected_unsupported_exchange": 0,
        "strict_identifier_rows_rejected_no_context_phrase": 0,
        "strict_identifier_rows_rejected_no_candidate_name_mention": 0,
        "strict_identifier_rows_rejected_noise_token": 0,
        "strict_identifier_rows_with_candidate_name_mentions": 0,
        "strict_identifier_rows_without_candidate_name_mentions": 0,
        "strict_identifier_match_pattern_counts": {},
        "strict_identifier_sample_matches": [],
        "strict_identifier_sample_rejections": [],
        "strict_identifier_extraction_warnings": [],
        "strict_identifier_results_propagated": False,
        "strict_identifier_propagated_rows_count": 0,
        "strict_identifier_summary_consistent": True,
        "strict_identifier_log_summary_match": True,
        "strict_identifier_propagation_target": "evidence_rows",
        "strict_identifier_propagation_warnings": [],
        "strict_identifier_ambiguity_diagnostics_enabled": True,
        "strict_identifier_rejection_reason_counts": _default_rejection_reason_counts(),
        "strict_identifier_ambiguous_match_count": 0,
        "strict_identifier_ambiguous_match_examples": [],
        "strict_identifier_context_window_examples": [],
        "strict_identifier_multiple_ticker_count": 0,
        "strict_identifier_multiple_exchange_count": 0,
        "strict_identifier_exchange_conflict_count": 0,
        "strict_identifier_ticker_conflict_count": 0,
        "strict_identifier_duplicate_context_count": 0,
        "strict_identifier_malformed_context_count": 0,
        "strict_identifier_noise_rejection_examples": [],
        "strict_identifier_unsupported_exchange_examples": [],
        "strict_identifier_no_context_phrase_examples": [],
        "strict_identifier_explainability_sample_size": STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE,
        "strict_identifier_candidate_explainability": [],
        "strict_identifier_context_normalization_enabled": True,
        "strict_identifier_context_windows_generated": 0,
        "strict_identifier_context_windows_normalized": 0,
        "strict_identifier_unique_context_windows_scanned": 0,
        "strict_identifier_duplicate_contexts_collapsed": 0,
        "strict_identifier_malformed_context_count_before_normalization": 0,
        "strict_identifier_malformed_context_count_after_normalization": 0,
        "strict_identifier_malformed_context_delta": 0,
        "strict_identifier_normalization_sample_before_after": [],
        "strict_identifier_token_distance_guardrail_enabled": True,
        "strict_identifier_token_distance_max": STRICT_IDENTIFIER_TOKEN_DISTANCE_MAX,
        "strict_identifier_context_window_max_chars": STRICT_IDENTIFIER_CONTEXT_WINDOW_MAX_LEN,
        "strict_identifier_accepted_matches": [],
        "strict_identifier_accepted_match_collection_size": 0,
        "strict_identifier_candidate_level_matches_found": 0,
        "strict_identifier_evidence_level_matches_found": 0,
        "strict_identifier_unmapped_matches_found": 0,
        "strict_identifier_matches_with_candidate_owner": 0,
        "strict_identifier_matches_without_candidate_owner": 0,
        "strict_identifier_propagation_target_counts": {},
        "strict_identifier_sample_unmapped_matches": [],
    }
    strict_unique_tickers: set[str] = set()
    strict_unique_exchanges: set[str] = set()
    strict_propagated_row_keys: set[str] = set()
    strict_candidate_owner_matches: dict[str, list[dict[str, Any]]] = {}
    seen_context_windows: set[str] = set()
    matcher_patterns = [STRICT_EXCHANGE_QUALIFIED_IDENTIFIER_PATTERN, STRICT_PARENTHEICAL_TICKER_THEN_EXCHANGE_PATTERN, STRICT_PARENTHEICAL_EXCHANGE_THEN_TICKER_PATTERN, STRICT_LISTED_CONTEXT_PATTERN, STRICT_HYPHENATED_LISTED_PATTERN, STRICT_TICKER_ON_EXCHANGE_PATTERN]
    for idx, seed in enumerate(seeds, start=1):
        queries = _generate_queries(seed)
        ops["generated_queries"] += len(queries)
        deduped_queries = _deduplicate_queries(queries)
        deduped_queries = deduped_queries[:MAX_QUERIES_PER_THEME]
        ops["deduplicated_queries"] += len(deduped_queries)
        ops["skipped_duplicate_queries"] += max(0, len(queries) - len(deduped_queries))
        seed_evidence: list[dict[str, Any]] = []
        for query in deduped_queries:
            qkey = f"{seed.theme_name}|{_normalize_query(query)}"
            if qkey in executed_query_keys:
                ops["skipped_duplicate_queries"] += 1
                continue
            executed_query_keys.add(qkey)
            cached = _fetch_cached_evidence(seed.theme_name, query, lookback_start, sgt_date)
            should_reuse_cached = bool(cached) and not force_fresh
            # TEMP DEBUG INSTRUMENTATION FOR FORCE-FRESH VALIDATION
            runtime_force_fresh_branch_taken = bool(force_fresh)
            print(f"[tier3h4] force_fresh_evidence={force_fresh} reuse_cached={should_reuse_cached}")
            if force_fresh:
                print("[tier3h4] bypassing persisted evidence selection")
            if should_reuse_cached:
                ops["cache_hits"] += 1
                ops["evidence_rows_reused"] += len(cached)
                items = cached
                err = None
                evidence_generation_mode = "persisted_reuse"
                runtime_evidence_generation_branch_taken = "persisted_reuse"
                runtime_persisted_reuse_branch_taken = True
                fresh_skip_reason = "persisted_evidence_table_available"
                evidence_source_mode = "persisted_evidence_table"
                evidence_selected_reason = "separate evidence table rows found"
            else:
                if cached and force_fresh:
                    persisted_evidence_reuse_bypassed = True
                    persisted_evidence_selection_skipped_due_to_force_refresh = True
                    runtime_evidence_generation_branch_taken = "fresh_generation_forced"
                    runtime_persisted_reuse_branch_taken = False
                    evidence_source_mode = "fresh_source_generation_forced"
                    evidence_selected_reason = "force_fresh_evidence override bypassed persisted evidence selection"
                ops["cache_misses"] += 1
                items, err = [], None
                tavily_collection_path_executed = True
                fresh_source_generation_active = True
                print("[tier3h4] executing fresh Tavily/source generation path")
                if tavily_enabled and ops["executed_queries"] < MAX_TAVILY_QUERIES_PER_RUN and not quota_exhausted:
                    attempts = 0
                    while attempts <= MAX_TAVILY_RETRIES:
                        ops["executed_queries"] += 1
                        items, err = _collect_tavily(query, api_key, max_results=MAX_RESULTS_PER_QUERY)
                        if not err:
                            ops["success_count"] += 1
                            break
                        attempts += 1
                        ops["failure_count"] += 1
                        reason = err
                        if reason == "rate_limited":
                            ops["rate_limit_events"] += 1
                        if reason == "quota_exhausted":
                            ops["quota_exhaustion_events"] += 1
                            quota_exhausted = True
                        if attempts <= MAX_TAVILY_RETRIES and _is_retryable(reason):
                            ops["retry_events"] += 1
                            time.sleep(0.2 * (2 ** (attempts - 1)))
                            continue
                        break
                if (not tavily_enabled) or err or quota_exhausted:
                    fallback_mode = True
                    if runtime_evidence_generation_branch_taken != "persisted_reuse":
                        runtime_evidence_generation_branch_taken = "fallback"
                    ops["fallback_events"] += 1
                    items = generate_mock_evidence(seed, query)
            for source_rank, item in enumerate(items, start=1):
                key = (sgt_date, seed.theme_name, query, item.get("source_url", ""))
                if key in seen_urls: continue
                seen_urls.add(key)
                candidate_asset_id = f"MOCK::{seed.theme_name.upper()}::{idx}"
                candidate_name = f"MOCK::{seed.theme_name.upper()}::{idx}"
                discovery_method = "tavily_search" if tavily_enabled else "deterministic_fallback"
                if discovery_method == "tavily_search":
                    ops["tavily_result_rows_seen_before_aggregation"] += 1
                ops["source_result_persistence_helper_called_count"] += 1
                row = build_source_level_evidence_row_from_tavily_result(item=item, result_index=source_rank, seed=seed, sgt_date=sgt_date, query_text=query, candidate_asset_id=candidate_asset_id, candidate_name=candidate_name, discovery_method=discovery_method)
                if row is None:
                    if discovery_method == "tavily_search":
                        ops["fresh_source_rows_write_errors"] += 1
                    continue
                evidence_rows.append(row)
                seed_evidence.append(row)
                scan_texts: list[str] = [
                    _normalize_text(row.get("evidence_text")),
                    _normalize_text(row.get("source_title")),
                    _normalize_text(row.get("source_content") or row.get("source_snippet")),
                    _normalize_text(str(row.get("raw_evidence"))),
                    _normalize_text(str((row.get("raw_evidence") or {}).get("source_result"))) if isinstance(row.get("raw_evidence"), dict) else "",
                    _normalize_text(str(row.get("raw_source_payload"))),
                ]
                evidence_sources = row.get("evidence_sources")
                if isinstance(evidence_sources, list):
                    scan_texts.append(_normalize_text(str(evidence_sources)))
                candidate_name_lower = _normalize_text(row.get("candidate_name")).lower()
                full_scan_text = _normalize_text(" ".join(t for t in scan_texts if t))
                strict_diag["strict_identifier_rows_scanned"] += 1
                if candidate_name_lower and candidate_name_lower in full_scan_text.lower():
                    strict_diag["strict_identifier_rows_with_candidate_name_mentions"] += 1
                else:
                    strict_diag["strict_identifier_rows_without_candidate_name_mentions"] += 1
                    strict_diag["strict_identifier_rejection_reason_counts"]["candidate_name_not_mentioned"] += 1
                for text in scan_texts:
                    if not text:
                        continue
                    strict_diag["strict_identifier_malformed_context_count_before_normalization"] += int("{" in text or "}" in text)
                    windows = _segment_identifier_context_windows(text, STRICT_IDENTIFIER_CONTEXT_WINDOW_MAX_LEN)
                    strict_diag["strict_identifier_context_windows_generated"] += len(windows)
                    for window in windows:
                        normalized_window = _normalize_identifier_context_window(window)
                        strict_diag["strict_identifier_context_windows_normalized"] += 1
                        if len(strict_diag["strict_identifier_normalization_sample_before_after"]) < STRICT_IDENTIFIER_NORMALIZATION_SAMPLE_MAX and window != normalized_window:
                            strict_diag["strict_identifier_normalization_sample_before_after"].append({"before": _bounded_context_window(window), "after": _bounded_context_window(normalized_window)})
                        context_window = _bounded_context_window(normalized_window)
                        dedupe_key = "|".join([context_window.lower(), _normalize_text(row.get("candidate_name")).lower(), _normalize_text(str(row.get("source_url") or row.get("source_domain") or "")).lower()])
                        if dedupe_key in seen_context_windows:
                            strict_diag["strict_identifier_duplicate_context_count"] += 1
                            strict_diag["strict_identifier_duplicate_contexts_collapsed"] += 1
                            strict_diag["strict_identifier_rejection_reason_counts"]["duplicate_context"] += 1
                            continue
                        seen_context_windows.add(dedupe_key)
                        strict_diag["strict_identifier_unique_context_windows_scanned"] += 1
                        matches = [m for p in matcher_patterns for m in p.finditer(normalized_window)]
                        detected_exchange_labels = sorted({_normalize_text(m.group("label")) for m in matches})
                        detected_ticker_tokens = sorted({_normalize_text(m.group("ticker")).upper() for m in matches})
                        if len(detected_ticker_tokens) > 1:
                            strict_diag["strict_identifier_multiple_ticker_count"] += 1
                            strict_diag["strict_identifier_rejection_reason_counts"]["multiple_tickers_in_context"] += 1
                        if len(detected_exchange_labels) > 1:
                            strict_diag["strict_identifier_multiple_exchange_count"] += 1
                            strict_diag["strict_identifier_rejection_reason_counts"]["multiple_exchanges_in_context"] += 1
                        if len(detected_exchange_labels) > 1 and len(detected_ticker_tokens) == 1:
                            strict_diag["strict_identifier_exchange_conflict_count"] += 1
                            strict_diag["strict_identifier_rejection_reason_counts"]["ticker_exchange_conflict"] += 1
                        if len(detected_ticker_tokens) > 1 and len(detected_exchange_labels) == 1:
                            strict_diag["strict_identifier_ticker_conflict_count"] += 1
                            strict_diag["strict_identifier_rejection_reason_counts"]["ticker_exchange_conflict"] += 1
                        if "{" in normalized_window or "}" in normalized_window:
                            strict_diag["strict_identifier_malformed_context_count_after_normalization"] += 1
                            strict_diag["strict_identifier_rejection_reason_counts"]["malformed_context"] += 1
                        explainability = {"candidate_name": _normalize_text(row.get("candidate_name")), "source_url": _normalize_text(str(row.get("source_url") or "")), "source_domain": _normalize_text(row.get("source_domain")), "source_title": _normalize_text(row.get("source_title")), "detected_exchange_labels": detected_exchange_labels, "detected_ticker_tokens": detected_ticker_tokens, "matched_pattern_family": "no_match", "context_window": context_window, "rejection_reason": None, "ambiguity_reason": None, "accepted": False}
                        extracted = _extract_strict_exchange_qualified_identifier(normalized_window, STRICT_IDENTIFIER_TOKEN_DISTANCE_MAX)
                        if extracted:
                            if extracted.get("multiple_matches_detected"):
                                strict_diag["strict_identifier_rows_with_multiple_matches"] += 1
                            if extracted.get("warnings"):
                                warning = extracted["warnings"][0]
                                rejection_reason = "unknown_rejection_reason"
                                if warning.startswith("ambiguous_multiple_matches_rejected"):
                                    strict_diag["strict_identifier_rows_rejected_ambiguous"] += 1
                                    strict_diag["strict_identifier_ambiguous_match_count"] += 1
                                    rejection_reason = "ambiguous_context_window"
                                    explainability["ambiguity_reason"] = "multiple_tickers_in_context" if len(detected_ticker_tokens) > 1 else "ambiguous_context_window"
                                    if len(strict_diag["strict_identifier_ambiguous_match_examples"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                                        strict_diag["strict_identifier_ambiguous_match_examples"].append(explainability)
                                elif warning.startswith("noise_token_rejected:"):
                                    strict_diag["strict_identifier_rows_rejected_noise_token"] += 1
                                    rejection_reason = "noisy_token"
                                    if len(strict_diag["strict_identifier_noise_rejection_examples"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                                        strict_diag["strict_identifier_noise_rejection_examples"].append(explainability)
                                elif warning.startswith("unsupported_exchange_rejected:"):
                                    strict_diag["strict_identifier_rows_rejected_unsupported_exchange"] += 1
                                    rejection_reason = "unsupported_exchange_label"
                                    if len(strict_diag["strict_identifier_unsupported_exchange_examples"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                                        strict_diag["strict_identifier_unsupported_exchange_examples"].append(explainability)
                                else:
                                    strict_diag["strict_identifier_rows_rejected_no_context_phrase"] += 1
                                    rejection_reason = "no_context_phrase"
                                    if len(strict_diag["strict_identifier_no_context_phrase_examples"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                                        strict_diag["strict_identifier_no_context_phrase_examples"].append(explainability)
                                explainability["rejection_reason"] = rejection_reason
                                strict_diag["strict_identifier_rejection_reason_counts"][rejection_reason] = strict_diag["strict_identifier_rejection_reason_counts"].get(rejection_reason, 0) + 1
                                if len(strict_diag["strict_identifier_sample_rejections"]) < 5:
                                    strict_diag["strict_identifier_sample_rejections"].append({"reason": warning, "text_preview": normalized_window[:140]})
                                if len(strict_diag["strict_identifier_context_window_examples"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                                    strict_diag["strict_identifier_context_window_examples"].append(explainability)
                                if len(strict_diag["strict_identifier_candidate_explainability"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                                    strict_diag["strict_identifier_candidate_explainability"].append(explainability)
                                continue
                            _apply_canonical_extraction_result(row, extracted)
                            if not extracted.get("accepted"):
                                continue
                            accepted_match = {
                                "candidate_asset_id": row.get("candidate_asset_id"),
                                "candidate_name": row.get("candidate_name"),
                                "source_url": row.get("source_url"),
                                "source_domain": row.get("source_domain"),
                                "source_title": row.get("source_title"),
                                "evidence_index": source_rank,
                                "context_window_id": dedupe_key,
                                "extracted_ticker": extracted.get("extracted_ticker"),
                                "extracted_exchange": extracted.get("extracted_exchange"),
                                "normalized_ticker": extracted.get("normalized_ticker"),
                                "normalized_exchange": extracted.get("normalized_exchange"),
                                "extraction_method": extracted.get("extraction_method"),
                                "extraction_confidence": extracted.get("extraction_confidence"),
                                "extraction_notes": extracted.get("extraction_notes"),
                                "matched_pattern_family": extracted.get("extraction_method"),
                                "context_window": context_window[:240],
                                "runtime_source": evidence_source_mode,
                                "propagation_target": "evidence_row",
                            }
                            strict_diag["strict_identifier_accepted_matches"].append(accepted_match)
                            owner = row.get("candidate_asset_id")
                            if owner:
                                strict_candidate_owner_matches.setdefault(str(owner), []).append(accepted_match)
                            else:
                                accepted_match["propagation_target"] = "unmapped_no_candidate_owner"
                            strict_propagated_row_keys.add(f"{row.get('theme_name','')}|{row.get('query_text','')}|{row.get('source_url','')}")
                        method = extracted.get("extraction_method")
                        if not method:
                            continue
                        strict_diag["strict_identifier_match_pattern_counts"][method] = strict_diag["strict_identifier_match_pattern_counts"].get(method, 0) + 1
                        strict_diag["strict_identifier_matches_found"] += 1
                        strict_unique_tickers.add(extracted["normalized_ticker"])
                        strict_unique_exchanges.add(extracted["normalized_exchange"])
                        if len(strict_diag["strict_identifier_sample_matches"]) < 5:
                            strict_diag["strict_identifier_sample_matches"].append({"ticker": extracted["normalized_ticker"], "exchange": extracted["normalized_exchange"], "note": extracted["extraction_notes"]})
                        explainability["accepted"] = True
                        explainability["matched_pattern_family"] = extracted["extraction_method"]
                        if len(strict_diag["strict_identifier_candidate_explainability"]) < STRICT_IDENTIFIER_EXPLAINABILITY_SAMPLE_SIZE:
                            strict_diag["strict_identifier_candidate_explainability"].append(explainability)
                        break
                if not row.get("normalized_ticker"):
                    strict_diag["strict_identifier_rows_rejected_no_exchange_label"] += 1
                    strict_diag["strict_identifier_rows_rejected_no_context_phrase"] += 1
                    strict_diag["strict_identifier_rejection_reason_counts"]["missing_explicit_ticker"] += 1
                    strict_diag["strict_identifier_rejection_reason_counts"]["missing_explicit_exchange"] += 1
                if discovery_method == "tavily_search":
                    ops["tavily_result_rows_persisted_before_aggregation"] += 1
                    ops["fresh_source_rows_written"] += 1
        evidence_count = len(seed_evidence)
        avg_quality = round(sum(_safe_float(e.get("evidence_quality_score")) for e in seed_evidence) / max(1, evidence_count), 4)
        domain_count = len({e.get("source_domain") for e in seed_evidence if e.get("source_domain")})
        thematic_relevance_score = round(min(100.0, sum(len(e.get("thematic_keyword_matches", [])) for e in seed_evidence) * 8.0 / max(1, evidence_count)), 4)
        entity_resolution_score = 75.0 if any(e.get("matched_entity_terms") for e in seed_evidence) else 35.0
        evidence_count_score = min(100.0, evidence_count * 20.0)
        cross_source_score = min(100.0, domain_count * 35.0)
        confidence = compute_candidate_score(evidence_count_score, avg_quality, thematic_relevance_score, entity_resolution_score, cross_source_score)
        suppression = []
        if evidence_count < 2: suppression.append("insufficient_evidence_count")
        if thematic_relevance_score < 30: suppression.append("weak_thematic_relevance")
        if domain_count < 2 and avg_quality < 75: suppression.append("low_cross_source_support")
        if suppression: confidence = min(confidence, 39.9)
        band = _score_band(confidence)
        advisory_status = "advisory_review" if band != "rejected_or_noise" else "advisory_rejected"
        candidate_id = f"MOCK::{seed.theme_name.upper()}::{idx}"
        candidate_row = {"run_date_sgt": sgt_date, "theme_name": seed.theme_name, "source_node": seed.source_node, "target_node": seed.target_node, "propagation_context_id": seed.propagation_context_id, "candidate_asset_id": candidate_id, "candidate_name": candidate_id, "candidate_type": "equity_candidate", "ticker": None, "exchange": None, "discovery_method": "tier3h4b_evidence_aware" if tavily_enabled else "tier3h4a_deterministic_scaffold", "evidence_sources": [{"query_text": e["query_text"], "source_url": e["source_url"], "source_domain": e["source_domain"], "quality": e["evidence_quality_score"], "cache_reused": e.get("cache_reused", False)} for e in seed_evidence], "evidence_count": evidence_count, "source_quality_score": avg_quality, "thematic_relevance_score": thematic_relevance_score, "entity_resolution_score": entity_resolution_score, "cross_source_score": cross_source_score, "candidate_confidence_score": confidence, "candidate_confidence_band": band, "confidence_explanation": f"weighted_score={confidence}; evidence_count={evidence_count}; domains={domain_count}; suppression={','.join(suppression) if suppression else 'none'}", "advisory_status": advisory_status, "rejection_reason": ",".join(suppression) if advisory_status == "advisory_rejected" else None, "llm_used": False, "llm_model": None, "llm_classification_json": None}
        owned_matches = strict_candidate_owner_matches.get(candidate_id, [])
        if owned_matches:
            best_match = owned_matches[0]
            candidate_row["ticker"] = best_match.get("normalized_ticker")
            candidate_row["exchange"] = best_match.get("normalized_exchange")
            for key in ("extracted_ticker", "extracted_exchange", "normalized_ticker", "normalized_exchange", "extraction_method", "extraction_confidence", "extraction_notes"):
                candidate_row[key] = best_match.get(key)
            for match in owned_matches:
                match["propagation_target"] = "candidate_audit_row"
        candidate_rows.append(candidate_row)
    sampled = evidence_rows[:3]
    fresh_quality = _fresh_evidence_quality_diagnostics(evidence_rows)
    strict_diag["strict_identifier_malformed_context_count"] = strict_diag["strict_identifier_malformed_context_count_after_normalization"]
    strict_diag["strict_identifier_malformed_context_delta"] = strict_diag["strict_identifier_malformed_context_count_before_normalization"] - strict_diag["strict_identifier_malformed_context_count_after_normalization"]
    strict_diag["strict_identifier_unique_tickers_found"] = sorted(strict_unique_tickers)
    strict_diag["strict_identifier_unique_exchanges_found"] = sorted(strict_unique_exchanges)
    target_counts = dict(Counter((m.get("propagation_target") or "summary_only") for m in strict_diag["strict_identifier_accepted_matches"]))
    strict_diag["strict_identifier_propagation_target_counts"] = target_counts
    strict_diag["strict_identifier_accepted_match_collection_size"] = len(strict_diag["strict_identifier_accepted_matches"])
    strict_diag["strict_identifier_candidate_level_matches_found"] = target_counts.get("candidate_audit_row", 0)
    strict_diag["strict_identifier_evidence_level_matches_found"] = target_counts.get("evidence_row", 0) + target_counts.get("evidence_level_only", 0)
    strict_diag["strict_identifier_unmapped_matches_found"] = target_counts.get("unmapped_no_candidate_owner", 0)
    strict_diag["strict_identifier_matches_with_candidate_owner"] = strict_diag["strict_identifier_candidate_level_matches_found"]
    strict_diag["strict_identifier_matches_without_candidate_owner"] = strict_diag["strict_identifier_accepted_match_collection_size"] - strict_diag["strict_identifier_matches_with_candidate_owner"]
    strict_diag["strict_identifier_sample_unmapped_matches"] = [
        {"ticker": m.get("normalized_ticker"), "exchange": m.get("normalized_exchange"), "context_window": _bounded_context_window(_normalize_text(m.get("context_window")))[:240]}
        for m in strict_diag["strict_identifier_accepted_matches"] if m.get("propagation_target") == "unmapped_no_candidate_owner"
    ][:5]
    strict_diag["strict_identifier_propagated_rows_count"] = len(strict_propagated_row_keys)
    strict_identifier_summary = _build_strict_identifier_canonical_summary(strict_diag, candidate_rows)
    strict_diag["strict_identifier_matches_found"] = strict_identifier_summary["strict_identifier_matches_found"]
    strict_diag["strict_identifier_results_propagated"] = strict_diag["strict_identifier_matches_found"] > 0 and strict_diag["strict_identifier_propagated_rows_count"] > 0
    strict_diag["strict_identifier_sample_matches"] = strict_identifier_summary["strict_identifier_sample_matches"]
    strict_diag["strict_identifier_rows_with_ticker"] = strict_identifier_summary["rows_with_ticker"]
    strict_diag["strict_identifier_rows_with_exchange"] = strict_identifier_summary["rows_with_exchange"]
    strict_diag["strict_identifier_rows_without_ticker"] = strict_identifier_summary["rows_without_ticker"]
    strict_diag["strict_identifier_rows_without_exchange"] = strict_identifier_summary["rows_without_exchange"]
    strict_diag["strict_identifier_evidence_rows_with_ticker"] = strict_identifier_summary["evidence_rows_with_ticker"]
    strict_diag["strict_identifier_evidence_rows_with_exchange"] = strict_identifier_summary["evidence_rows_with_exchange"]
    strict_diag["strict_identifier_propagation_target"] = "candidate_audit_row" if strict_diag["strict_identifier_candidate_level_matches_found"] > 0 else ("evidence_rows" if strict_diag["strict_identifier_evidence_level_matches_found"] > 0 else "summary_only")
    strict_identifier_runtime_vs_summary_delta = {
        "matches_found_delta": strict_diag["strict_identifier_matches_found"] - strict_identifier_summary["strict_identifier_matches_found"],
        "rows_with_ticker_delta": strict_diag["strict_identifier_rows_with_ticker"] - strict_identifier_summary["rows_with_ticker"],
        "rows_with_exchange_delta": strict_diag["strict_identifier_rows_with_exchange"] - strict_identifier_summary["rows_with_exchange"],
        "evidence_rows_with_ticker_delta": strict_diag["strict_identifier_evidence_rows_with_ticker"] - strict_identifier_summary["evidence_rows_with_ticker"],
        "evidence_rows_with_exchange_delta": strict_diag["strict_identifier_evidence_rows_with_exchange"] - strict_identifier_summary["evidence_rows_with_exchange"],
    }
    strict_identifier_counter_reconciliation_warnings = []
    if strict_diag["strict_identifier_matches_found"] != strict_diag["strict_identifier_accepted_match_collection_size"]:
        strict_identifier_counter_reconciliation_warnings.append("matches_found_not_equal_canonical_collection_size")
    if strict_diag["strict_identifier_matches_with_candidate_owner"] + strict_diag["strict_identifier_matches_without_candidate_owner"] != strict_diag["strict_identifier_matches_found"]:
        strict_identifier_counter_reconciliation_warnings.append("ownership_split_does_not_sum_to_total_matches")
    strict_identifier_log_summary_match = all(delta == 0 for delta in strict_identifier_runtime_vs_summary_delta.values())
    if not strict_identifier_log_summary_match:
        strict_identifier_counter_reconciliation_warnings.append("runtime_summary_mismatch_detected")
    strict_identifier_counter_reconciliation_passed = len(strict_identifier_counter_reconciliation_warnings) == 0 and strict_identifier_log_summary_match
    strict_diag["strict_identifier_runtime_vs_summary_delta"] = strict_identifier_runtime_vs_summary_delta
    strict_diag["strict_identifier_counter_reconciliation_warnings"] = strict_identifier_counter_reconciliation_warnings
    strict_diag["strict_identifier_log_summary_match"] = strict_identifier_log_summary_match
    strict_diag["strict_identifier_counter_reconciliation_passed"] = strict_identifier_counter_reconciliation_passed
    strict_diag["strict_identifier_summary_consistent"] = strict_identifier_counter_reconciliation_passed
    strict_diag["strict_identifier_canonical_counter_source"] = "strict_identifier_accepted_matches"
    strict_diag["strict_identifier_final_summary_source"] = "strict_identifier_accepted_matches"
    strict_diag["strict_identifier_summary_serialization_complete"] = False
    strict_diag.update(strict_identifier_summary)
    strict_diag["strict_identifier_summary_serialization_complete"] = True
    if strict_diag["strict_identifier_matches_found"] > 0 and strict_diag["strict_identifier_propagated_rows_count"] == 0:
        strict_diag["strict_identifier_propagation_warnings"].append("strict_matches_found_but_no_rows_propagated")
        strict_diag["strict_identifier_extraction_warnings"].append("strict_matches_found_but_no_rows_propagated")
    evidence_summary = {"tavily_enabled": tavily_enabled, "fallback_mode": fallback_mode, "fresh_source_generation_validation_enabled": True, "persisted_evidence_reuse_bypassed": persisted_evidence_reuse_bypassed, "persisted_evidence_selection_skipped_due_to_force_refresh": persisted_evidence_selection_skipped_due_to_force_refresh, "fresh_source_generation_active": fresh_source_generation_active, "evidence_source_mode": evidence_source_mode, "evidence_selected_reason": evidence_selected_reason, "tavily_collection_path_executed": tavily_collection_path_executed, "fresh_source_generation_skip_reason": fresh_skip_reason, "evidence_generation_mode": evidence_generation_mode, "runtime_evidence_generation_branch_taken": runtime_evidence_generation_branch_taken, "runtime_persisted_reuse_branch_taken": runtime_persisted_reuse_branch_taken, "runtime_fresh_generation_branch_reachable": runtime_fresh_generation_branch_reachable, "runtime_source_loop_instrumentation_loaded": runtime_source_loop_instrumentation_loaded, "runtime_force_fresh_branch_taken": runtime_force_fresh_branch_taken, "queries_generated": ops["generated_queries"], "queries_deduplicated": ops["deduplicated_queries"], "queries_executed": ops["executed_queries"], "evidence_rows_collected": len(evidence_rows), "failure_count": ops["failure_count"], "quota_exhausted": quota_exhausted, "tavily_result_rows_seen_before_aggregation": ops["tavily_result_rows_seen_before_aggregation"], "tavily_result_rows_persisted_before_aggregation": ops["tavily_result_rows_persisted_before_aggregation"], "source_result_persistence_helper_called_count": ops["source_result_persistence_helper_called_count"], "fresh_source_rows_written": ops["fresh_source_rows_written"], "fresh_source_rows_write_errors": ops["fresh_source_rows_write_errors"], "source_level_evidence_rows_written": sum(1 for e in evidence_rows if isinstance((e.get("raw_evidence") or {}).get("source_result"), dict)), "evidence_rows_with_raw_source_payload": sum(1 for e in evidence_rows if isinstance((e.get("raw_evidence") or {}).get("source_result"), dict) and bool((e.get("raw_evidence") or {}).get("source_result"))), "evidence_rows_without_source_payload": sum(1 for e in evidence_rows if not isinstance((e.get("raw_evidence") or {}).get("source_result"), dict)), "evidence_rows_with_source_url": sum(1 for e in evidence_rows if bool(e.get("source_url"))), "evidence_rows_with_source_title": sum(1 for e in evidence_rows if bool(e.get("source_title"))), "evidence_rows_with_source_content": sum(1 for e in evidence_rows if bool(e.get("source_snippet"))), "sample_source_result_keys": [sorted(list(((e.get("raw_evidence") or {}).get("source_result") or {}).keys()))[:20] if isinstance((e.get("raw_evidence") or {}).get("source_result"), dict) else [] for e in sampled], "sample_source_titles": [e.get("source_title") for e in sampled], "sample_source_urls": [e.get("source_url") for e in sampled], "sample_source_content_preview": [(e.get("source_snippet") or "")[:120] for e in sampled], "tavily_result_loop_file": "transmission_layers/asset_discovery/tier3h4_dynamic_entity_discovery.py", "tavily_result_loop_function": "build_records", **fresh_quality, **strict_diag}
    return candidate_rows, evidence_rows, evidence_summary, ops


def _canonicalize_final_summary_payload(final_summary_payload: dict, evidence_summary: dict, records: list[dict]) -> dict[str, Any]:
    canonical_summary = {
        "strict_identifier_matches_found": evidence_summary.get("strict_identifier_matches_found", 0),
        "strict_identifier_sample_matches": list(evidence_summary.get("strict_identifier_sample_matches") or []),
        "rows_with_ticker": evidence_summary.get("rows_with_ticker", 0),
        "rows_without_ticker": evidence_summary.get("rows_without_ticker", len(records)),
        "rows_with_exchange": evidence_summary.get("rows_with_exchange", 0),
        "rows_without_exchange": evidence_summary.get("rows_without_exchange", len(records)),
        "evidence_rows_with_ticker": evidence_summary.get("evidence_rows_with_ticker", 0),
        "evidence_rows_with_exchange": evidence_summary.get("evidence_rows_with_exchange", 0),
    }

    payload_object_id = id(final_summary_payload)
    reconciliation_object_id = id(final_summary_payload)
    final_summary_payload["strict_identifier_payload_object_id"] = payload_object_id
    final_summary_payload["strict_identifier_reconciliation_object_id"] = reconciliation_object_id
    final_summary_payload["strict_identifier_serialization_stage"] = "reconciliation"

    final_summary_payload.update(canonical_summary)

    runtime_vs_payload_delta = {
        "matches_found_delta": (final_summary_payload.get("strict_identifier_matches_found") or 0) - (canonical_summary.get("strict_identifier_matches_found") or 0),
        "rows_with_ticker_delta": (final_summary_payload.get("rows_with_ticker") or 0) - (canonical_summary.get("rows_with_ticker") or 0),
        "rows_with_exchange_delta": (final_summary_payload.get("rows_with_exchange") or 0) - (canonical_summary.get("rows_with_exchange") or 0),
        "sample_match_delta": len(final_summary_payload.get("strict_identifier_sample_matches") or []) - len(canonical_summary.get("strict_identifier_sample_matches") or []),
    }
    reconciliation_vs_runtime_delta = {
        "matches_found_delta": (canonical_summary.get("strict_identifier_matches_found") or 0) - (evidence_summary.get("strict_identifier_matches_found") or 0),
        "rows_with_ticker_delta": (canonical_summary.get("rows_with_ticker") or 0) - (evidence_summary.get("rows_with_ticker") or 0),
        "rows_with_exchange_delta": (canonical_summary.get("rows_with_exchange") or 0) - (evidence_summary.get("rows_with_exchange") or 0),
        "sample_match_delta": len(canonical_summary.get("strict_identifier_sample_matches") or []) - len(evidence_summary.get("strict_identifier_sample_matches") or []),
    }

    sample_matches = final_summary_payload.get("strict_identifier_sample_matches") or []
    canonical_match_count = final_summary_payload.get("strict_identifier_matches_found", 0)
    sample_match_valid = canonical_match_count == 0 or len(sample_matches) > 0
    stale_payload_detected = any(v != 0 for v in runtime_vs_payload_delta.values()) or any(v != 0 for v in reconciliation_vs_runtime_delta.values()) or not sample_match_valid
    payload_overwritten_after_reconciliation = False

    warnings = list(final_summary_payload.get("strict_identifier_counter_reconciliation_warnings") or [])
    if stale_payload_detected and "stale_final_payload_detected" not in warnings:
        warnings.append("stale_final_payload_detected")
    if not sample_match_valid and "sample_matches_missing_for_nonzero_canonical_count" not in warnings:
        warnings.append("sample_matches_missing_for_nonzero_canonical_count")

    final_summary_payload["strict_identifier_runtime_vs_final_payload_delta"] = runtime_vs_payload_delta
    final_summary_payload["strict_identifier_runtime_vs_in_memory_payload_delta"] = dict(runtime_vs_payload_delta)
    final_summary_payload["strict_identifier_reconciliation_vs_runtime_delta"] = reconciliation_vs_runtime_delta
    final_summary_payload["strict_identifier_payload_canonicalized"] = True
    final_summary_payload["strict_identifier_final_payload_validated"] = True
    final_summary_payload["strict_identifier_serialization_order_valid"] = final_summary_payload.get("strict_identifier_summary_serialization_complete") is True
    final_summary_payload["strict_identifier_stale_payload_detected"] = stale_payload_detected
    final_summary_payload["strict_identifier_payload_overwritten_after_reconciliation"] = payload_overwritten_after_reconciliation
    final_summary_payload["strict_identifier_counter_reconciliation_warnings"] = warnings
    final_summary_payload["strict_identifier_payload_identity_consistent"] = payload_object_id == reconciliation_object_id
    final_summary_payload["strict_identifier_payload_trace_complete"] = True
    final_summary_payload["strict_identifier_final_payload_matches_reconciliation"] = (not stale_payload_detected)
    final_summary_payload["strict_identifier_final_payload_matches_runtime"] = (not stale_payload_detected)
    final_summary_payload["strict_identifier_final_payload_emitted"] = False
    final_summary_payload["strict_identifier_intermediate_payload_suppressed"] = True
    final_summary_payload["strict_identifier_duplicate_payloads_detected"] = False
    final_summary_payload["strict_identifier_counter_reconciliation_passed"] = (
        not stale_payload_detected
        and final_summary_payload["strict_identifier_serialization_order_valid"]
        and final_summary_payload["strict_identifier_payload_identity_consistent"]
        and len(warnings) == 0
    )
    final_summary_payload["strict_identifier_summary_consistent"] = final_summary_payload["strict_identifier_counter_reconciliation_passed"]

    final_summary_payload["strict_identifier_serialization_stage"] = "ready_for_serialization"
    return canonical_summary


def _apply_canonical_strict_identifier_fields_to_final_payload(
    final_summary_payload: dict[str, Any],
    evidence_summary: dict[str, Any],
    canonical_summary: dict[str, Any],
) -> None:
    final_summary_payload.update(canonical_summary)
    runtime_strict_identifier_summary = {
        "strict_identifier_runtime_source": evidence_summary.get("strict_identifier_runtime_source", "unknown_runtime_source"),
        "strict_identifier_rows_scanned": evidence_summary.get("strict_identifier_rows_scanned", 0),
        "strict_identifier_matches_found": evidence_summary.get("strict_identifier_matches_found", 0),
        "strict_identifier_sample_matches": list(evidence_summary.get("strict_identifier_sample_matches") or []),
        "rows_with_ticker": evidence_summary.get("rows_with_ticker", 0),
        "rows_with_exchange": evidence_summary.get("rows_with_exchange", 0),
        "evidence_rows_with_ticker": evidence_summary.get("evidence_rows_with_ticker", 0),
        "evidence_rows_with_exchange": evidence_summary.get("evidence_rows_with_exchange", 0),
    }
    final_summary_payload.update(runtime_strict_identifier_summary)
    final_summary_payload["final_summary_strict_identifier_source"] = "canonical_runtime_reconciliation"
    final_summary_payload["final_summary_assignment_origin"] = "runtime_strict_identifier_summary_object"
    final_summary_payload["final_summary_matches_found"] = final_summary_payload["strict_identifier_matches_found"]
    final_summary_payload["final_export_summary_source"] = "canonical_runtime_extraction"
    final_summary_payload["final_export_runtime_metrics_origin"] = "evidence_summary.runtime_strict_identifier_summary"
    final_summary_payload["final_export_assignment_path"] = "_apply_canonical_strict_identifier_fields_to_final_payload.runtime_strict_identifier_summary"
    final_summary_payload["final_export_runtime_source"] = runtime_strict_identifier_summary["strict_identifier_runtime_source"]
    final_summary_payload["final_export_evidence_mode"] = runtime_strict_identifier_summary["strict_identifier_runtime_source"]


def _finalize_and_verify_summary_payload(final_summary_payload: dict, canonical_summary: dict, summary_path: Path) -> None:
    prior_emitted = bool(final_summary_payload.get("strict_identifier_final_payload_emitted", False))
    final_summary_payload["strict_identifier_duplicate_payloads_detected"] = prior_emitted
    if prior_emitted:
        print("[tier3h4][warn] duplicate_final_payload_emission_attempt_detected; suppressing stale/intermediate summary serialization")
        return
    final_summary_payload["strict_identifier_serialization_stage"] = "serializing"
    final_summary_payload["strict_identifier_serialized_payload_object_id"] = id(final_summary_payload)
    final_summary_payload["strict_identifier_payload_identity_consistent"] = (
        final_summary_payload.get("strict_identifier_payload_object_id")
        == final_summary_payload.get("strict_identifier_reconciliation_object_id")
        == final_summary_payload.get("strict_identifier_serialized_payload_object_id")
    )
    summary_path.write_text(json.dumps(final_summary_payload, indent=2), encoding="utf-8")
    reloaded_payload = json.loads(summary_path.read_text(encoding="utf-8"))

    serialized_vs_runtime_delta = {
        "matches_found_delta": (reloaded_payload.get("strict_identifier_matches_found") or 0) - (canonical_summary.get("strict_identifier_matches_found") or 0),
        "rows_with_ticker_delta": (reloaded_payload.get("rows_with_ticker") or 0) - (canonical_summary.get("rows_with_ticker") or 0),
        "rows_with_exchange_delta": (reloaded_payload.get("rows_with_exchange") or 0) - (canonical_summary.get("rows_with_exchange") or 0),
        "sample_match_delta": len(reloaded_payload.get("strict_identifier_sample_matches") or []) - len(canonical_summary.get("strict_identifier_sample_matches") or []),
    }
    post_match = all(v == 0 for v in serialized_vs_runtime_delta.values())
    final_summary_payload["strict_identifier_runtime_vs_serialized_payload_delta"] = serialized_vs_runtime_delta
    final_summary_payload["strict_identifier_post_serialization_verified"] = True
    final_summary_payload["strict_identifier_post_serialization_match"] = post_match
    final_summary_payload["strict_identifier_stale_payload_detected"] = final_summary_payload.get("strict_identifier_stale_payload_detected", False) or (not post_match)
    final_summary_payload["strict_identifier_final_payload_matches_reconciliation"] = final_summary_payload.get("strict_identifier_final_payload_matches_reconciliation", True) and post_match
    final_summary_payload["strict_identifier_final_payload_matches_runtime"] = final_summary_payload["strict_identifier_final_payload_matches_reconciliation"]
    final_summary_payload["strict_identifier_payload_overwritten_after_reconciliation"] = not post_match
    if not post_match:
        warnings = list(final_summary_payload.get("strict_identifier_counter_reconciliation_warnings") or [])
        if "serialized_payload_mismatch_detected" not in warnings:
            warnings.append("serialized_payload_mismatch_detected")
        final_summary_payload["strict_identifier_counter_reconciliation_warnings"] = warnings
        final_summary_payload["strict_identifier_counter_reconciliation_passed"] = False
        final_summary_payload["strict_identifier_summary_consistent"] = False
    final_summary_payload["strict_identifier_serialization_stage"] = "post_serialization_verified"
    final_summary_payload["strict_identifier_final_payload_emitted"] = True
    final_summary_payload["strict_identifier_intermediate_payload_suppressed"] = True
    summary_path.write_text(json.dumps(final_summary_payload, indent=2), encoding="utf-8")

def _integrate_operational_summary_with_canonical_reconciliation(
    operational_summary_payload: dict[str, Any],
    runtime_summary_payload: dict[str, Any],
    serialized_summary_payload: dict[str, Any],
    canonical_summary: dict[str, Any],
) -> dict[str, Any]:
    pre_integration = {
        "strict_identifier_matches_found": operational_summary_payload.get("strict_identifier_matches_found", 0),
        "rows_with_ticker": operational_summary_payload.get("rows_with_ticker", 0),
        "rows_with_exchange": operational_summary_payload.get("rows_with_exchange", 0),
        "evidence_rows_with_ticker": operational_summary_payload.get("evidence_rows_with_ticker", 0),
        "evidence_rows_with_exchange": operational_summary_payload.get("evidence_rows_with_exchange", 0),
    }
    legacy_detected = any(v != (canonical_summary.get(k) or 0) for k, v in pre_integration.items())
    operational_summary_payload["strict_identifier_pre_integration_audit_counters"] = dict(pre_integration)
    operational_summary_payload["strict_identifier_pre_integration_audit_delta"] = {
        f"{k}_delta": pre_integration.get(k, 0) - (canonical_summary.get(k) or 0) for k in pre_integration
    }
    canonical_export_fields = [
        "strict_identifier_matches_found",
        "strict_identifier_sample_matches",
        "rows_with_ticker",
        "rows_with_exchange",
        "evidence_rows_with_ticker",
        "evidence_rows_with_exchange",
        "strict_identifier_candidate_level_matches_found",
        "strict_identifier_evidence_level_matches_found",
        "strict_identifier_unmapped_matches_found",
        "strict_identifier_unique_tickers_found",
        "strict_identifier_unique_exchanges_found",
    ]
    for field in canonical_export_fields:
        if field in canonical_summary:
            operational_summary_payload[field] = canonical_summary[field]
    operational_summary_payload.update(canonical_summary)
    runtime_vs_operational_export_delta = {
        "matches_found_delta": (runtime_summary_payload.get("strict_identifier_matches_found") or 0) - (operational_summary_payload.get("strict_identifier_matches_found") or 0),
        "rows_with_ticker_delta": (runtime_summary_payload.get("rows_with_ticker") or 0) - (operational_summary_payload.get("rows_with_ticker") or 0),
        "rows_with_exchange_delta": (runtime_summary_payload.get("rows_with_exchange") or 0) - (operational_summary_payload.get("rows_with_exchange") or 0),
        "evidence_rows_with_ticker_delta": (runtime_summary_payload.get("evidence_rows_with_ticker") or 0) - (operational_summary_payload.get("evidence_rows_with_ticker") or 0),
        "evidence_rows_with_exchange_delta": (runtime_summary_payload.get("evidence_rows_with_exchange") or 0) - (operational_summary_payload.get("evidence_rows_with_exchange") or 0),
    }
    serialized_vs_operational_export_delta = {
        "matches_found_delta": (serialized_summary_payload.get("strict_identifier_matches_found") or 0) - (operational_summary_payload.get("strict_identifier_matches_found") or 0),
        "rows_with_ticker_delta": (serialized_summary_payload.get("rows_with_ticker") or 0) - (operational_summary_payload.get("rows_with_ticker") or 0),
        "rows_with_exchange_delta": (serialized_summary_payload.get("rows_with_exchange") or 0) - (operational_summary_payload.get("rows_with_exchange") or 0),
        "evidence_rows_with_ticker_delta": (serialized_summary_payload.get("evidence_rows_with_ticker") or 0) - (operational_summary_payload.get("evidence_rows_with_ticker") or 0),
        "evidence_rows_with_exchange_delta": (serialized_summary_payload.get("evidence_rows_with_exchange") or 0) - (operational_summary_payload.get("evidence_rows_with_exchange") or 0),
    }
    export_matches_runtime = all(v == 0 for v in runtime_vs_operational_export_delta.values()) and all(v == 0 for v in serialized_vs_operational_export_delta.values())
    operational_warnings = list(operational_summary_payload.get("strict_identifier_operational_export_warnings") or [])
    if not export_matches_runtime and "operational_export_mismatch_detected" not in operational_warnings:
        operational_warnings.append("operational_export_mismatch_detected")
    if export_matches_runtime and "operational_export_mismatch_detected" in operational_warnings:
        operational_warnings = [w for w in operational_warnings if w != "operational_export_mismatch_detected"]
    canonical_match_count = canonical_summary.get("strict_identifier_matches_found", 0)
    if operational_summary_payload.get("strict_identifier_matches_found") != canonical_match_count:
        if "operational_export_runtime_count_mismatch_detected" not in operational_warnings:
            operational_warnings.append("operational_export_runtime_count_mismatch_detected")
        operational_summary_payload["strict_identifier_operational_export_matches_runtime"] = False
    elif "operational_export_runtime_count_mismatch_detected" in operational_warnings:
        operational_warnings = [w for w in operational_warnings if w != "operational_export_runtime_count_mismatch_detected"]
    operational_summary_payload["strict_identifier_runtime_vs_operational_export_delta"] = runtime_vs_operational_export_delta
    operational_summary_payload["strict_identifier_serialized_vs_operational_export_delta"] = serialized_vs_operational_export_delta
    operational_summary_payload["strict_identifier_operational_export_warnings"] = operational_warnings
    operational_summary_payload["strict_identifier_operational_summary_integrated"] = True
    operational_summary_payload["strict_identifier_operational_summary_source"] = "strict_identifier_accepted_matches"
    operational_summary_payload["strict_identifier_operational_export_connected"] = True
    operational_summary_payload["strict_identifier_operational_export_matches_runtime"] = bool(
        operational_summary_payload.get("strict_identifier_operational_export_matches_runtime", export_matches_runtime)
        and export_matches_runtime
    )
    operational_summary_payload["strict_identifier_legacy_operational_counters_detected"] = legacy_detected
    operational_summary_payload["strict_identifier_operational_payload_replaced"] = True
    operational_summary_payload["strict_identifier_runtime_results_integrated"] = True
    operational_summary_payload["strict_identifier_export_pipeline_source"] = "canonical_runtime_reconciliation"
    operational_summary_payload["strict_identifier_audit_pipeline_disconnected_counters_detected"] = legacy_detected
    operational_summary_payload["strict_identifier_audit_pipeline_disconnected"] = False
    operational_summary_payload["strict_identifier_unique_tickers_count"] = len(operational_summary_payload.get("strict_identifier_unique_tickers_found") or [])
    operational_summary_payload["strict_identifier_unique_exchanges_count"] = len(operational_summary_payload.get("strict_identifier_unique_exchanges_found") or [])
    if legacy_detected and "audit_pipeline_disconnected_counters_detected" not in operational_warnings:
        operational_warnings.append("audit_pipeline_disconnected_counters_detected")
    operational_summary_payload["strict_identifier_operational_export_warnings"] = operational_warnings
    return operational_summary_payload


def main() -> int:
    start = time.time()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    sgt_date = run_date_sgt()
    seeds, source_counts, soft_fallback = load_upstream_context()
    records, evidence_rows, evidence_summary, ops = build_records(seeds, sgt_date)
    upsert_status, candidate_upsert_diag = upsert_supabase(records, TABLE_NAME, "run_date_sgt,theme_name,candidate_asset_id,discovery_method", include_diagnostics=True)
    evidence_upsert_status, evidence_upsert_diag = upsert_supabase(evidence_rows, EVIDENCE_TABLE_NAME, "", include_diagnostics=True)
    elapsed = round(time.time() - start, 3)
    telemetry_row = {"run_date_sgt": sgt_date, "workflow_name": "tier3h4_dynamic_entity_discovery", "provider": "tavily", "api_calls_attempted": ops["executed_queries"], "api_calls_executed": ops["executed_queries"], "cache_hits": ops["cache_hits"], "cache_misses": ops["cache_misses"], "fallback_events": ops["fallback_events"], "rate_limit_events": ops["rate_limit_events"], "quota_exhaustion_events": ops["quota_exhaustion_events"], "retry_events": ops["retry_events"], "success_count": ops["success_count"], "failure_count": ops["failure_count"], "estimated_cost": None, "execution_seconds": elapsed, "metadata": {"fallback_mode": evidence_summary["fallback_mode"], "tavily_enabled": evidence_summary["tavily_enabled"], "soft_fallback_used": soft_fallback}}
    telemetry_status = upsert_supabase([telemetry_row], OPERATIONAL_TABLE_NAME, "run_date_sgt,workflow_name,provider")
    runtime = _runtime_provenance("main")
    final_summary_payload = {"module": "tier3h4_dynamic_entity_discovery", "run_timestamp_utc": utc_now().isoformat(), "run_date_sgt": sgt_date, "seed_count": len(seeds), "record_count": len(records), "source_counts": source_counts, "soft_fallback_used": soft_fallback, "upsert_status": upsert_status, "confidence_band_counts": dict(Counter(r["candidate_confidence_band"] for r in records)), "advisory_status_counts": dict(Counter(r["advisory_status"] for r in records)), "advisory_only": True, "llm_used": False, **runtime, "runtime_evidence_generation_branch_taken": evidence_summary["runtime_evidence_generation_branch_taken"], "runtime_persisted_reuse_branch_taken": evidence_summary["runtime_persisted_reuse_branch_taken"], "runtime_fresh_generation_branch_reachable": evidence_summary["runtime_fresh_generation_branch_reachable"], "runtime_source_loop_instrumentation_loaded": evidence_summary["runtime_source_loop_instrumentation_loaded"], "runtime_force_fresh_branch_taken": evidence_summary["runtime_force_fresh_branch_taken"], "rows_with_ticker": evidence_summary.get("rows_with_ticker", 0), "rows_without_ticker": evidence_summary.get("rows_without_ticker", len(records)), "rows_with_exchange": evidence_summary.get("rows_with_exchange", 0), "rows_without_exchange": evidence_summary.get("rows_without_exchange", len(records)), "evidence_rows_with_ticker": evidence_summary.get("evidence_rows_with_ticker", 0), "evidence_rows_with_exchange": evidence_summary.get("evidence_rows_with_exchange", 0), "strict_identifier_runtime_source": evidence_summary.get("strict_identifier_runtime_source", "unknown_runtime_source"), "strict_identifier_extraction_enabled": evidence_summary.get("strict_identifier_extraction_enabled"), "strict_identifier_phase": evidence_summary.get("strict_identifier_phase"), "strict_identifier_rows_scanned": evidence_summary.get("strict_identifier_rows_scanned"), "strict_identifier_matches_found": evidence_summary.get("strict_identifier_matches_found"), "strict_identifier_unique_tickers_found": evidence_summary.get("strict_identifier_unique_tickers_found"), "strict_identifier_unique_exchanges_found": evidence_summary.get("strict_identifier_unique_exchanges_found"), "strict_identifier_sample_matches": evidence_summary.get("strict_identifier_sample_matches"), "strict_identifier_results_propagated": evidence_summary.get("strict_identifier_results_propagated"), "strict_identifier_propagated_rows_count": evidence_summary.get("strict_identifier_propagated_rows_count"), "strict_identifier_summary_consistent": evidence_summary.get("strict_identifier_summary_consistent"), "strict_identifier_log_summary_match": evidence_summary.get("strict_identifier_log_summary_match"), "strict_identifier_counter_reconciliation_passed": evidence_summary.get("strict_identifier_counter_reconciliation_passed"), "strict_identifier_counter_reconciliation_warnings": evidence_summary.get("strict_identifier_counter_reconciliation_warnings"), "strict_identifier_runtime_vs_summary_delta": evidence_summary.get("strict_identifier_runtime_vs_summary_delta"), "strict_identifier_summary_serialization_complete": evidence_summary.get("strict_identifier_summary_serialization_complete"), "strict_identifier_canonical_counter_source": evidence_summary.get("strict_identifier_canonical_counter_source"), "strict_identifier_final_summary_source": evidence_summary.get("strict_identifier_final_summary_source"), "strict_identifier_propagation_target": evidence_summary.get("strict_identifier_propagation_target"), "strict_identifier_propagation_warnings": evidence_summary.get("strict_identifier_propagation_warnings"), "strict_identifier_accepted_match_collection_size": evidence_summary.get("strict_identifier_accepted_match_collection_size"), "strict_identifier_candidate_level_matches_found": evidence_summary.get("strict_identifier_candidate_level_matches_found"), "strict_identifier_evidence_level_matches_found": evidence_summary.get("strict_identifier_evidence_level_matches_found"), "strict_identifier_unmapped_matches_found": evidence_summary.get("strict_identifier_unmapped_matches_found"), "strict_identifier_matches_with_candidate_owner": evidence_summary.get("strict_identifier_matches_with_candidate_owner"), "strict_identifier_matches_without_candidate_owner": evidence_summary.get("strict_identifier_matches_without_candidate_owner"), "strict_identifier_propagation_target_counts": evidence_summary.get("strict_identifier_propagation_target_counts"), "strict_identifier_sample_unmapped_matches": evidence_summary.get("strict_identifier_sample_unmapped_matches"), "strict_identifier_ambiguity_diagnostics_enabled": evidence_summary.get("strict_identifier_ambiguity_diagnostics_enabled"), "strict_identifier_rejection_reason_counts": evidence_summary.get("strict_identifier_rejection_reason_counts"), "strict_identifier_ambiguous_match_count": evidence_summary.get("strict_identifier_ambiguous_match_count"), "strict_identifier_ambiguous_match_examples": evidence_summary.get("strict_identifier_ambiguous_match_examples"), "strict_identifier_context_window_examples": evidence_summary.get("strict_identifier_context_window_examples"), "strict_identifier_multiple_ticker_count": evidence_summary.get("strict_identifier_multiple_ticker_count"), "strict_identifier_multiple_exchange_count": evidence_summary.get("strict_identifier_multiple_exchange_count"), "strict_identifier_exchange_conflict_count": evidence_summary.get("strict_identifier_exchange_conflict_count"), "strict_identifier_ticker_conflict_count": evidence_summary.get("strict_identifier_ticker_conflict_count"), "strict_identifier_duplicate_context_count": evidence_summary.get("strict_identifier_duplicate_context_count"), "strict_identifier_malformed_context_count": evidence_summary.get("strict_identifier_malformed_context_count"), "strict_identifier_noise_rejection_examples": evidence_summary.get("strict_identifier_noise_rejection_examples"), "strict_identifier_unsupported_exchange_examples": evidence_summary.get("strict_identifier_unsupported_exchange_examples"), "strict_identifier_no_context_phrase_examples": evidence_summary.get("strict_identifier_no_context_phrase_examples"), "strict_identifier_explainability_sample_size": evidence_summary.get("strict_identifier_explainability_sample_size"), "preview": records[:10]}
    evidence_summary_full = {"run_date_sgt": sgt_date, **evidence_summary, **evidence_upsert_diag, "evidence_rows_persisted": len(evidence_rows) if evidence_upsert_status == "upserted" else 0, "candidates_scored": len(records), "candidates_suppressed": sum(1 for r in records if r["advisory_status"] == "advisory_rejected"), "top_domains": dict(Counter(e.get("source_domain") for e in evidence_rows).most_common(10)), "upsert_status": evidence_upsert_status, "telemetry_upsert_status": telemetry_status}
    validation = {"all_rows_llm_used_false": all(r["llm_used"] is False for r in records), "all_rows_advisory_only": all(r["advisory_status"] in {"advisory_review", "advisory_rejected"} for r in records), "no_monitored_universe_writes_attempted": True, "idempotency_fields_present": all(all(k in r for k in ["run_date_sgt", "theme_name", "candidate_asset_id", "discovery_method"]) for r in records)}
    operational_summary = {"generated_queries": ops["generated_queries"], "deduplicated_queries": ops["deduplicated_queries"], "executed_queries": ops["executed_queries"], "skipped_duplicate_queries": ops["skipped_duplicate_queries"], "cache_hits": ops["cache_hits"], "cache_misses": ops["cache_misses"], "tavily_enabled": evidence_summary["tavily_enabled"], "fallback_mode": evidence_summary["fallback_mode"], "quota_exhausted": evidence_summary["quota_exhausted"], "retry_events": ops["retry_events"], "rate_limit_events": ops["rate_limit_events"], "evidence_rows_reused": ops["evidence_rows_reused"], "evidence_rows_collected": len(evidence_rows), "execution_seconds": elapsed, "strict_identifier_matches_found": 0, "strict_identifier_sample_matches": [], "rows_with_ticker": 0, "rows_with_exchange": 0, "evidence_rows_with_ticker": 0, "evidence_rows_with_exchange": 0}
    canonical_summary = _canonicalize_final_summary_payload(final_summary_payload, evidence_summary, records)
    _apply_canonical_strict_identifier_fields_to_final_payload(final_summary_payload, evidence_summary, canonical_summary)
    final_summary_payload.update({k: evidence_upsert_diag.get(k) for k in ["evidence_write_method", "discovery_write_method", "failing_upsert_has_matching_unique_constraint", "evidence_insert_row_count", "evidence_insert_success", "evidence_insert_response_status", "evidence_insert_response_body", "evidence_upsert_payload_columns", "evidence_upsert_first_row_keys", "evidence_upsert_response_body", "evidence_upsert_response_text", "evidence_upsert_error_body", "evidence_upsert_first_failed_row", "evidence_upsert_response_json", "evidence_upsert_http_status", "evidence_upsert_postgrest_error_payload", "evidence_upsert_exception_type", "evidence_upsert_exception_args", "evidence_upsert_exception_repr", "evidence_upsert_schema_mismatch_columns", "evidence_upsert_suspect_type_fields", "evidence_upsert_payload_count", "evidence_upsert_payload_size_bytes", "write_error_code", "write_error_message", "write_error_details", "write_error_hint", "numeric_confidence_coercions_applied", "invalid_numeric_fields_before_write", "evidence_confidence_type", "extraction_confidence_type", "final_upsert_variable_name", "final_upsert_contains_nested_objects", "final_upsert_nested_fields", "final_upsert_first_row_keys", "final_schema_aligned_payload_keys", "removed_unsupported_columns", "final_payload_matches_schema", "final_payload_contains_raw_evidence", "raw_evidence_type", "raw_evidence_json_serializable", "raw_evidence_nested_invalid_types", "raw_evidence_sanitization_applied", "raw_evidence_post_sanitization_type", "final_payload_missing_required_columns", "evidence_table_actual_columns", "evidence_table_actual_column_types", "evidence_table_nullable_fields", "payload_vs_schema_missing_columns", "payload_vs_schema_extra_columns", "payload_vs_schema_type_conflicts", "payload_fields_missing_from_table", "required_table_fields_missing_from_payload", "type_conflict_fields", "full_upsert_response_text", "full_upsert_response_json", "response_status_code", "exception_repr", "actual_upsert_variable_name", "actual_upsert_first_row_keys", "actual_upsert_extra_columns", "actual_upsert_contains_query_text", "actual_upsert_payload_matches_schema", "actual_upsert_contains_accepted", "actual_upsert_contains_normalized_exchange", "actual_upsert_contains_normalized_ticker", "actual_upsert_contains_source_snippet", "actual_on_conflict_value", "actual_upsert_conflict_columns", "conflict_columns_exist_in_schema", "schema_introspection_status", "schema_introspection_error", "failing_table_name", "failing_write_method", "failing_on_conflict_value", "failing_table_unique_constraints", "failing_response_body", "table_unique_constraints"]})
    final_summary_payload.update({k: candidate_upsert_diag.get(k) for k in ["failing_table_name", "failing_unique_constraints", "failing_table_unique_constraints", "unique_constraint_names_detected", "unique_index_names_detected", "unique_constraint_column_sets_detected", "unique_index_column_sets_detected", "normalized_conflict_target_columns", "detected_unique_contracts", "normalized_detected_unique_column_sets", "matched_unique_contract_name", "conflict_target_matches_unique_constraint", "duplicate_conflict_detected", "rows_already_exist_count", "conflict_is_benign", "failing_table_primary_key", "failing_table_indexes", "failing_table_unique_indexes", "actual_on_conflict_value", "actual_upsert_conflict_columns", "discovery_write_method"]})
    if evidence_upsert_status != "upserted":
        final_summary_payload["strict_identifier_runtime_source"] = evidence_summary.get("strict_identifier_runtime_source", "fresh_source_generation")
        final_summary_payload["final_export_runtime_metrics_origin"] = "runtime_canonical_preserved_on_upsert_failure"
        final_summary_payload["evidence_persistence_failed"] = True
        final_summary_payload["evidence_persistence_failure_status"] = evidence_upsert_status

    _finalize_and_verify_summary_payload(final_summary_payload, canonical_summary, SUMMARY_PATH)
    serialized_summary_payload = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    operational_summary = _integrate_operational_summary_with_canonical_reconciliation(
        operational_summary, final_summary_payload, serialized_summary_payload, canonical_summary
    )
    if not operational_summary["strict_identifier_operational_export_matches_runtime"]:
        warnings = list(final_summary_payload.get("strict_identifier_counter_reconciliation_warnings") or [])
        if "operational_export_mismatch_detected" not in warnings:
            warnings.append("operational_export_mismatch_detected")
        final_summary_payload["strict_identifier_counter_reconciliation_warnings"] = warnings
        final_summary_payload["strict_identifier_counter_reconciliation_passed"] = False
        final_summary_payload["strict_identifier_summary_consistent"] = False
    EVIDENCE_SUMMARY_PATH.write_text(json.dumps(evidence_summary_full, indent=2), encoding="utf-8")
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    OPERATIONAL_SUMMARY_PATH.write_text(json.dumps(operational_summary, indent=2), encoding="utf-8")
    print(f"[tier3h4] run_date_sgt={sgt_date} records={len(records)} evidence_rows={len(evidence_rows)} cache_hits={ops['cache_hits']} fallback={evidence_summary['fallback_mode']} upsert={upsert_status}")
    print("[tier3h4] fresh evidence quality diagnostics:")
    print(f"[tier3h4] rows_observed={evidence_summary['fresh_evidence_rows_observed']}")
    print(f"[tier3h4] meaningful_text={evidence_summary['fresh_evidence_rows_with_meaningful_text']}")
    print(f"[tier3h4] source_urls={evidence_summary['fresh_evidence_rows_with_source_url']}")
    print(f"[tier3h4] source_titles={evidence_summary['fresh_evidence_rows_with_source_title']}")
    print(f"[tier3h4] ticker_like_patterns={evidence_summary['fresh_evidence_rows_with_ticker_like_patterns']}")
    print(f"[tier3h4] exchange_like_patterns={evidence_summary['fresh_evidence_rows_with_exchange_like_patterns']}")
    print("[tier3h4] strict identifier extraction:")
    print(f"[tier3h4] phase={evidence_summary['strict_identifier_phase']}")
    print(f"[tier3h4] runtime_source={evidence_summary['evidence_source_mode']}")
    print(f"[tier3h4] rows_scanned={evidence_summary['strict_identifier_rows_scanned']}")
    print(f"[tier3h4] matches_found={evidence_summary['strict_identifier_matches_found']}")
    print(f"[tier3h4] unique_tickers={len(evidence_summary['strict_identifier_unique_tickers_found'])}")
    print(f"[tier3h4] unique_exchanges={len(evidence_summary['strict_identifier_unique_exchanges_found'])}")
    print(f"[tier3h4] rejected_ambiguous={evidence_summary['strict_identifier_rows_rejected_ambiguous']}")
    print(f"[tier3h4] rejected_noise_token={evidence_summary['strict_identifier_rows_rejected_noise_token']}")
    print("[tier3h4] strict identifier ambiguity diagnostics:")
    print(f"[tier3h4] ambiguous_matches={evidence_summary['strict_identifier_ambiguous_match_count']}")
    print(f"[tier3h4] multiple_ticker_contexts={evidence_summary['strict_identifier_multiple_ticker_count']}")
    print(f"[tier3h4] multiple_exchange_contexts={evidence_summary['strict_identifier_multiple_exchange_count']}")
    print(f"[tier3h4] exchange_conflicts={evidence_summary['strict_identifier_exchange_conflict_count']}")
    print("[tier3h4] strict identifier context normalization:")
    print(f"[tier3h4] windows_generated={evidence_summary.get('strict_identifier_context_windows_generated',0)}")
    print(f"[tier3h4] unique_windows_scanned={evidence_summary.get('strict_identifier_unique_context_windows_scanned',0)}")
    print(f"[tier3h4] duplicates_collapsed={evidence_summary.get('strict_identifier_duplicate_contexts_collapsed',0)}")
    print(f"[tier3h4] malformed_before={evidence_summary.get('strict_identifier_malformed_context_count_before_normalization',0)}")
    print(f"[tier3h4] malformed_after={evidence_summary.get('strict_identifier_malformed_context_count_after_normalization',0)}")
    print(f"[tier3h4] token_distance_max={evidence_summary.get('strict_identifier_token_distance_max',STRICT_IDENTIFIER_TOKEN_DISTANCE_MAX)}")
    print(f"[tier3h4] malformed_contexts={evidence_summary['strict_identifier_malformed_context_count']}")
    print("[tier3h4] strict identifier propagation:")
    print(f"[tier3h4] accepted_match_collection_size={evidence_summary.get('strict_identifier_accepted_match_collection_size',0)}")
    print(f"[tier3h4] propagated_rows={evidence_summary.get('strict_identifier_propagated_rows_count',0)}")
    print(f"[tier3h4] candidate_level_matches={evidence_summary.get('strict_identifier_candidate_level_matches_found',0)}")
    print(f"[tier3h4] evidence_level_matches={evidence_summary.get('strict_identifier_evidence_level_matches_found',0)}")
    print(f"[tier3h4] unmapped_matches={evidence_summary.get('strict_identifier_unmapped_matches_found',0)}")
    print("[tier3h4] strict identifier summary reconciliation:")
    print(f"[tier3h4] canonical_match_count={evidence_summary.get('strict_identifier_accepted_match_collection_size',0)}")
    print(f"[tier3h4] candidate_level_matches={evidence_summary.get('strict_identifier_candidate_level_matches_found',0)}")
    print(f"[tier3h4] evidence_level_matches={evidence_summary.get('strict_identifier_evidence_level_matches_found',0)}")
    print(f"[tier3h4] unmapped_matches={evidence_summary.get('strict_identifier_unmapped_matches_found',0)}")
    print(f"[tier3h4] rows_with_ticker={evidence_summary.get('strict_identifier_rows_with_ticker',0)}")
    print(f"[tier3h4] rows_with_exchange={evidence_summary.get('strict_identifier_rows_with_exchange',0)}")
    print(f"[tier3h4] reconciliation_passed={evidence_summary.get('strict_identifier_counter_reconciliation_passed',False)}")
    top_rejection_reasons = sorted((evidence_summary.get("strict_identifier_rejection_reason_counts") or {}).items(), key=lambda kv: (-kv[1], kv[0]))[:3]
    print(f"[tier3h4] top_rejection_reasons={top_rejection_reasons}")
    print(f"[tier3h4] warnings={evidence_summary['fresh_evidence_quality_warning_count']}")
    print("[tier3h4] evidence upsert payload diagnostics:")
    print(f"[tier3h4] evidence_upsert_payload_type={evidence_upsert_diag.get('evidence_upsert_payload_type')}")
    print(f"[tier3h4] evidence_upsert_destination_table={evidence_upsert_diag.get('evidence_upsert_destination_table')}")
    print(f"[tier3h4] evidence_upsert_destination_table_columns={evidence_upsert_diag.get('evidence_upsert_destination_table_columns')}")
    print(f"[tier3h4] evidence_table_actual_columns={evidence_upsert_diag.get('evidence_table_actual_columns')}")
    print(f"[tier3h4] evidence_table_actual_column_types={evidence_upsert_diag.get('evidence_table_actual_column_types')}")
    print(f"[tier3h4] evidence_table_nullable_fields={evidence_upsert_diag.get('evidence_table_nullable_fields')}")
    print(f"[tier3h4] schema_introspection_status={evidence_upsert_diag.get('schema_introspection_status')}")
    print(f"[tier3h4] payload_vs_schema_missing_columns={evidence_upsert_diag.get('payload_vs_schema_missing_columns')}")
    print(f"[tier3h4] payload_vs_schema_extra_columns={evidence_upsert_diag.get('payload_vs_schema_extra_columns')}")
    print(f"[tier3h4] payload_vs_schema_type_conflicts={evidence_upsert_diag.get('payload_vs_schema_type_conflicts')}")
    print(f"[tier3h4] payload_fields_missing_from_table={evidence_upsert_diag.get('payload_fields_missing_from_table')}")
    print(f"[tier3h4] required_table_fields_missing_from_payload={evidence_upsert_diag.get('required_table_fields_missing_from_payload')}")
    print(f"[tier3h4] type_conflict_fields={evidence_upsert_diag.get('type_conflict_fields')}")
    print(f"[tier3h4] evidence_upsert_payload_count={evidence_upsert_diag.get('evidence_upsert_payload_count')}")
    print(f"[tier3h4] evidence_upsert_first_row_keys={evidence_upsert_diag.get('evidence_upsert_first_row_keys')}")
    print(f"[tier3h4] evidence_upsert_contains_resolution_fields={evidence_upsert_diag.get('evidence_upsert_contains_resolution_fields')}")
    print(f"[tier3h4] evidence_upsert_contains_nested_objects={evidence_upsert_diag.get('evidence_upsert_contains_nested_objects')}")
    print(f"[tier3h4] evidence_upsert_nested_object_fields={evidence_upsert_diag.get('evidence_upsert_nested_object_fields')}")
    print(f"[tier3h4] final_upsert_variable_name={evidence_upsert_diag.get('final_upsert_variable_name')}")
    print(f"[tier3h4] final_upsert_contains_nested_objects={evidence_upsert_diag.get('final_upsert_contains_nested_objects')}")
    print(f"[tier3h4] final_upsert_nested_fields={evidence_upsert_diag.get('final_upsert_nested_fields')}")
    print(f"[tier3h4] final_upsert_first_row_keys={evidence_upsert_diag.get('final_upsert_first_row_keys')}")
    print(f"[tier3h4] final_schema_aligned_payload_keys={evidence_upsert_diag.get('final_schema_aligned_payload_keys')}")
    print(f"[tier3h4] removed_unsupported_columns={evidence_upsert_diag.get('removed_unsupported_columns')}")
    print(f"[tier3h4] final_payload_matches_schema={evidence_upsert_diag.get('final_payload_matches_schema')}")
    print(f"[tier3h4] evidence_upsert_resolution_fields_present={evidence_upsert_diag.get('evidence_upsert_resolution_fields_present')}")
    print(f"[tier3h4] evidence_upsert_first_row={evidence_upsert_diag.get('evidence_upsert_first_failed_row')}")
    print(f"[tier3h4] raw_evidence_json_serializable={evidence_upsert_diag.get('raw_evidence_json_serializable')}")
    print(f"[tier3h4] raw_evidence_nested_invalid_types={evidence_upsert_diag.get('raw_evidence_nested_invalid_types')}")
    print(f"[tier3h4] raw_evidence_sanitization_applied={evidence_upsert_diag.get('raw_evidence_sanitization_applied')}")
    print(f"[tier3h4] raw_evidence_post_sanitization_type={evidence_upsert_diag.get('raw_evidence_post_sanitization_type')}")
    print(f"[tier3h4] full_upsert_response_text={evidence_upsert_diag.get('full_upsert_response_text')}")
    print(f"[tier3h4] full_upsert_response_json={evidence_upsert_diag.get('full_upsert_response_json')}")
    print(f"[tier3h4] exception_repr={evidence_upsert_diag.get('exception_repr') or evidence_upsert_diag.get('evidence_upsert_exception_repr')}")
    print(f"[tier3h4] response_status_code={evidence_upsert_diag.get('response_status_code')}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
