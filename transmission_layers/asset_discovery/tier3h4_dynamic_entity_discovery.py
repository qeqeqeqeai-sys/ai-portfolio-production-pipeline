from __future__ import annotations
import json, os, re, time
from collections import Counter
from dataclasses import dataclass
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

def _normalize_domain(url: str) -> str:
    host = urlparse(url).netloc.lower().replace("www.", "")
    return host

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
            url = str(item.get("url") or "").strip()
            if not url:
                continue
            out.append({"query_text": query_text, "source_title": _normalize_text(item.get("title")), "source_url": url, "source_snippet": _normalize_text(item.get("content") or item.get("snippet")), "source_domain": _normalize_domain(url), "source_rank": i, "retrieved_at": utc_now().isoformat(), "cache_reused": False})
        return out, None
    except Exception as exc:
        reason = "timeout" if "timeout" in str(exc).lower() else "provider_unavailable"
        return [], reason

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

def upsert_supabase(rows: list[dict[str, Any]], table_name: str, on_conflict: str) -> str:
    if not rows: return "skipped:no_rows"
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key: return "skipped:missing_supabase_env"
    try:
        r = requests.post(f"{url}/rest/v1/{table_name}", headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}, params={"on_conflict": on_conflict}, json=rows, timeout=60)
        return "upserted" if r.status_code < 400 else f"upsert_failed:{r.status_code}"
    except Exception as exc:
        return f"upsert_exception:{type(exc).__name__}"

def build_records(seeds: list[DiscoverySeed], sgt_date: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
    candidate_rows: list[dict[str, Any]] = []
    evidence_rows: list[dict[str, Any]] = []
    ops = {"generated_queries": 0, "deduplicated_queries": 0, "executed_queries": 0, "skipped_duplicate_queries": 0, "cache_hits": 0, "cache_misses": 0, "retry_events": 0, "rate_limit_events": 0, "quota_exhaustion_events": 0, "failure_count": 0, "success_count": 0, "fallback_events": 0, "evidence_rows_reused": 0}
    api_key = os.getenv("TAVILY_API_KEY", "")
    tavily_enabled = bool(api_key) and _tavily_enabled()
    fallback_mode = not tavily_enabled
    quota_exhausted = False
    seen_urls: set[tuple[str, str, str, str]] = set()
    executed_query_keys: set[str] = set()
    lookback_start = (date.fromisoformat(sgt_date) - timedelta(days=QUERY_CACHE_LOOKBACK_DAYS)).isoformat()
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
            if cached:
                ops["cache_hits"] += 1
                ops["evidence_rows_reused"] += len(cached)
                items = cached
                err = None
            else:
                ops["cache_misses"] += 1
                items, err = [], None
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
                    ops["fallback_events"] += 1
                    items = generate_mock_evidence(seed, query)
            for item in items:
                key = (sgt_date, seed.theme_name, query, item.get("source_url", ""))
                if key in seen_urls: continue
                seen_urls.add(key)
                text = f"{item.get('source_title', '')} {item.get('source_snippet', '')}".lower()
                matches = _entity_match_terms(seed, text)
                thematic_matches = [k for k in THEME_KEYWORDS.get(seed.theme_name, []) if k in text]
                evidence_quality = _evidence_quality_score(item, seed.theme_name)
                suppression_flags = []
                if len(thematic_matches) < 1: suppression_flags.append("weak_thematic_overlap")
                if any(tok in text for tok in GENERIC_SUPPRESSION_TOKENS) and len(matches) < 1: suppression_flags.append("generic_megacap_contamination")
                row = {"run_date_sgt": sgt_date, "theme_name": seed.theme_name, "source_node": seed.source_node, "target_node": seed.target_node, "query_text": query, "candidate_asset_id": f"MOCK::{seed.theme_name.upper()}::{idx}", "candidate_name": f"MOCK::{seed.theme_name.upper()}::{idx}", "candidate_ticker": None, "source_url": item["source_url"], "source_domain": _normalize_domain(item.get("source_url", "")), "source_title": _normalize_text(item.get("source_title")), "source_snippet": _normalize_text(item.get("source_snippet")), "source_rank": item.get("source_rank"), "retrieved_at": item.get("retrieved_at"), "discovery_method": "tavily_search" if tavily_enabled else "deterministic_fallback", "evidence_quality_score": evidence_quality, "thematic_keyword_matches": thematic_matches, "matched_entity_terms": matches, "suppression_flags": suppression_flags, "cache_reused": bool(item.get("cache_reused", False))}
                evidence_rows.append(row)
                seed_evidence.append(row)
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
        candidate_rows.append({"run_date_sgt": sgt_date, "theme_name": seed.theme_name, "source_node": seed.source_node, "target_node": seed.target_node, "propagation_context_id": seed.propagation_context_id, "candidate_asset_id": f"MOCK::{seed.theme_name.upper()}::{idx}", "candidate_name": f"MOCK::{seed.theme_name.upper()}::{idx}", "candidate_type": "equity_candidate", "ticker": None, "exchange": None, "discovery_method": "tier3h4b_evidence_aware" if tavily_enabled else "tier3h4a_deterministic_scaffold", "evidence_sources": [{"query_text": e["query_text"], "source_url": e["source_url"], "source_domain": e["source_domain"], "quality": e["evidence_quality_score"], "cache_reused": e.get("cache_reused", False)} for e in seed_evidence], "evidence_count": evidence_count, "source_quality_score": avg_quality, "thematic_relevance_score": thematic_relevance_score, "entity_resolution_score": entity_resolution_score, "cross_source_score": cross_source_score, "candidate_confidence_score": confidence, "candidate_confidence_band": band, "confidence_explanation": f"weighted_score={confidence}; evidence_count={evidence_count}; domains={domain_count}; suppression={','.join(suppression) if suppression else 'none'}", "advisory_status": advisory_status, "rejection_reason": ",".join(suppression) if advisory_status == "advisory_rejected" else None, "llm_used": False, "llm_model": None, "llm_classification_json": None})
    evidence_summary = {"tavily_enabled": tavily_enabled, "fallback_mode": fallback_mode, "queries_generated": ops["generated_queries"], "queries_deduplicated": ops["deduplicated_queries"], "queries_executed": ops["executed_queries"], "evidence_rows_collected": len(evidence_rows), "failure_count": ops["failure_count"], "quota_exhausted": quota_exhausted}
    return candidate_rows, evidence_rows, evidence_summary, ops

def main() -> int:
    start = time.time()
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    sgt_date = run_date_sgt()
    seeds, source_counts, soft_fallback = load_upstream_context()
    records, evidence_rows, evidence_summary, ops = build_records(seeds, sgt_date)
    upsert_status = upsert_supabase(records, TABLE_NAME, "run_date_sgt,theme_name,candidate_asset_id,discovery_method")
    evidence_upsert_status = upsert_supabase(evidence_rows, EVIDENCE_TABLE_NAME, "run_date_sgt,theme_name,query_text,source_url")
    elapsed = round(time.time() - start, 3)
    telemetry_row = {"run_date_sgt": sgt_date, "workflow_name": "tier3h4_dynamic_entity_discovery", "provider": "tavily", "api_calls_attempted": ops["executed_queries"], "api_calls_executed": ops["executed_queries"], "cache_hits": ops["cache_hits"], "cache_misses": ops["cache_misses"], "fallback_events": ops["fallback_events"], "rate_limit_events": ops["rate_limit_events"], "quota_exhaustion_events": ops["quota_exhaustion_events"], "retry_events": ops["retry_events"], "success_count": ops["success_count"], "failure_count": ops["failure_count"], "estimated_cost": None, "execution_seconds": elapsed, "metadata": {"fallback_mode": evidence_summary["fallback_mode"], "tavily_enabled": evidence_summary["tavily_enabled"], "soft_fallback_used": soft_fallback}}
    telemetry_status = upsert_supabase([telemetry_row], OPERATIONAL_TABLE_NAME, "run_date_sgt,workflow_name,provider")
    summary = {"module": "tier3h4_dynamic_entity_discovery", "run_timestamp_utc": utc_now().isoformat(), "run_date_sgt": sgt_date, "seed_count": len(seeds), "record_count": len(records), "source_counts": source_counts, "soft_fallback_used": soft_fallback, "upsert_status": upsert_status, "confidence_band_counts": dict(Counter(r["candidate_confidence_band"] for r in records)), "advisory_status_counts": dict(Counter(r["advisory_status"] for r in records)), "advisory_only": True, "llm_used": False, "preview": records[:10]}
    evidence_summary_full = {"run_date_sgt": sgt_date, **evidence_summary, "evidence_rows_persisted": len(evidence_rows) if evidence_upsert_status == "upserted" else 0, "candidates_scored": len(records), "candidates_suppressed": sum(1 for r in records if r["advisory_status"] == "advisory_rejected"), "top_domains": dict(Counter(e.get("source_domain") for e in evidence_rows).most_common(10)), "upsert_status": evidence_upsert_status, "telemetry_upsert_status": telemetry_status}
    validation = {"all_rows_llm_used_false": all(r["llm_used"] is False for r in records), "all_rows_advisory_only": all(r["advisory_status"] in {"advisory_review", "advisory_rejected"} for r in records), "no_monitored_universe_writes_attempted": True, "idempotency_fields_present": all(all(k in r for k in ["run_date_sgt", "theme_name", "candidate_asset_id", "discovery_method"]) for r in records)}
    operational_summary = {"generated_queries": ops["generated_queries"], "deduplicated_queries": ops["deduplicated_queries"], "executed_queries": ops["executed_queries"], "skipped_duplicate_queries": ops["skipped_duplicate_queries"], "cache_hits": ops["cache_hits"], "cache_misses": ops["cache_misses"], "tavily_enabled": evidence_summary["tavily_enabled"], "fallback_mode": evidence_summary["fallback_mode"], "quota_exhausted": evidence_summary["quota_exhausted"], "retry_events": ops["retry_events"], "rate_limit_events": ops["rate_limit_events"], "evidence_rows_reused": ops["evidence_rows_reused"], "evidence_rows_collected": len(evidence_rows), "execution_seconds": elapsed}
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    EVIDENCE_SUMMARY_PATH.write_text(json.dumps(evidence_summary_full, indent=2), encoding="utf-8")
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    OPERATIONAL_SUMMARY_PATH.write_text(json.dumps(operational_summary, indent=2), encoding="utf-8")
    print(f"[tier3h4] run_date_sgt={sgt_date} records={len(records)} evidence_rows={len(evidence_rows)} cache_hits={ops['cache_hits']} fallback={evidence_summary['fallback_mode']} upsert={upsert_status}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
