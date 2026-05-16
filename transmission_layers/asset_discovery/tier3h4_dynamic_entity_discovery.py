from __future__ import annotations
import json, os
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
import requests

TABLE_NAME = "tier3h_dynamic_entity_discovery"
LOG_DIR = Path("logs")
SUMMARY_PATH = LOG_DIR / "tier3h4_dynamic_entity_discovery_summary.json"
VALIDATION_PATH = LOG_DIR / "tier3h4_dynamic_entity_discovery_validation.json"

SUPABASE_UPSTREAM_SOURCES = [
    {"table": "tier3h_transmission_candidates", "order": "run_date_sgt.desc", "limit": 400},
    {"table": "structural_theme_graph_single_hop_propagation", "order": "run_date_sgt.desc", "limit": 400},
]

WEIGHTS = {"evidence_count_score": 0.30, "thematic_relevance_score": 0.25, "source_quality_score": 0.20, "entity_resolution_score": 0.15, "cross_source_score": 0.10}


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


def _supabase_get_rows(table: str, order: str, limit: int) -> list[dict[str, Any]]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key: return []
    try:
        r = requests.get(f"{url}/rest/v1/{table}", headers={"apikey": key, "Authorization": f"Bearer {key}"}, params={"select": "*", "order": order, "limit": str(limit)}, timeout=60)
        payload = r.json() if r.status_code < 400 else []
        return [x for x in payload if isinstance(x, dict)] if isinstance(payload, list) else []
    except Exception:
        return []


def load_upstream_context() -> tuple[list[DiscoverySeed], dict[str, int], bool]:
    seeds: list[DiscoverySeed] = []
    counts: dict[str, int] = {}
    for source in SUPABASE_UPSTREAM_SOURCES:
        rows = _supabase_get_rows(source["table"], source["order"], source["limit"])
        counts[source["table"]] = len(rows)
        for row in rows[:100]:
            seeds.append(DiscoverySeed(theme_name=str(row.get("discovery_theme") or row.get("theme_name") or row.get("anchor_theme_name") or "unknown_theme"), source_node=str(row.get("linked_from_node") or row.get("source_node_key") or "unknown_source"), target_node=str(row.get("target_node_key") or row.get("candidate_symbol") or "unknown_target"), propagation_context_id=str(row.get("propagation_key") or row.get("snapshot_id") or "") or None))
    if seeds: return seeds, counts, False
    fallback = [
        DiscoverySeed("ai_power_demand", "data_center_load", "grid_resilience", "tier3h4a-mock-ctx-1"),
        DiscoverySeed("semiconductor_capacity", "fab_utilization", "tooling_backlog", "tier3h4a-mock-ctx-2"),
    ]
    return fallback, counts, True


def generate_mock_evidence(seed: DiscoverySeed) -> list[dict[str, Any]]:
    return [
        {"source": "structural_graph", "quality": 72, "signal": f"{seed.source_node}->{seed.target_node}"},
        {"source": "tier3h_candidates", "quality": 68, "signal": seed.theme_name},
    ]


def compute_candidate_score(evidence_count_score: float, source_quality_score: float, thematic_relevance_score: float, entity_resolution_score: float, cross_source_score: float) -> float:
    return round(
        WEIGHTS["evidence_count_score"] * evidence_count_score
        + WEIGHTS["thematic_relevance_score"] * thematic_relevance_score
        + WEIGHTS["source_quality_score"] * source_quality_score
        + WEIGHTS["entity_resolution_score"] * entity_resolution_score
        + WEIGHTS["cross_source_score"] * cross_source_score,
        4,
    )


def build_records(seeds: list[DiscoverySeed], sgt_date: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, seed in enumerate(seeds, start=1):
        evidence = generate_mock_evidence(seed)
        evidence_count = len(evidence)
        evidence_count_score = min(100.0, evidence_count * 30.0)
        source_quality_score = round(sum(_safe_float(e.get("quality"), 0) for e in evidence) / max(1, evidence_count), 4)
        thematic_relevance_score = 75.0 if "ai" in seed.theme_name else 62.0
        entity_resolution_score = 70.0
        cross_source_score = 65.0 if evidence_count > 1 else 35.0
        confidence = compute_candidate_score(evidence_count_score, source_quality_score, thematic_relevance_score, entity_resolution_score, cross_source_score)
        band = _score_band(confidence)
        advisory_status = "advisory_review" if band != "rejected_or_noise" else "advisory_rejected"
        candidate_asset_id = f"MOCK::{seed.theme_name.upper()}::{idx}"
        rows.append({
            "run_date_sgt": sgt_date,
            "theme_name": seed.theme_name,
            "source_node": seed.source_node,
            "target_node": seed.target_node,
            "propagation_context_id": seed.propagation_context_id,
            "candidate_asset_id": candidate_asset_id,
            "candidate_name": candidate_asset_id,
            "candidate_type": "equity_candidate",
            "ticker": None,
            "exchange": None,
            "discovery_method": "tier3h4a_deterministic_scaffold",
            "evidence_sources": evidence,
            "evidence_count": evidence_count,
            "source_quality_score": source_quality_score,
            "thematic_relevance_score": thematic_relevance_score,
            "entity_resolution_score": entity_resolution_score,
            "cross_source_score": cross_source_score,
            "candidate_confidence_score": confidence,
            "candidate_confidence_band": band,
            "confidence_explanation": f"weighted_score={confidence}; evidence_count={evidence_count}; method=deterministic_mock",
            "advisory_status": advisory_status,
            "rejection_reason": "score_below_threshold" if advisory_status == "advisory_rejected" else None,
            "llm_used": False,
            "llm_model": None,
            "llm_classification_json": None,
        })
    return rows


def upsert_supabase(rows: list[dict[str, Any]]) -> str:
    if not rows: return "skipped:no_rows"
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key: return "skipped:missing_supabase_env"
    try:
        r = requests.post(f"{url}/rest/v1/{TABLE_NAME}", headers={"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json", "Prefer": "resolution=merge-duplicates,return=minimal"}, params={"on_conflict": "run_date_sgt,theme_name,candidate_asset_id,discovery_method"}, json=rows, timeout=60)
        return "upserted" if r.status_code < 400 else f"upsert_failed:{r.status_code}"
    except Exception as exc:
        return f"upsert_exception:{type(exc).__name__}"


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    sgt_date = run_date_sgt()
    seeds, source_counts, soft_fallback = load_upstream_context()
    records = build_records(seeds, sgt_date)
    upsert_status = upsert_supabase(records)
    summary = {
        "module": "tier3h4_dynamic_entity_discovery",
        "run_timestamp_utc": utc_now().isoformat(),
        "run_date_sgt": sgt_date,
        "seed_count": len(seeds),
        "record_count": len(records),
        "source_counts": source_counts,
        "soft_fallback_used": soft_fallback,
        "upsert_status": upsert_status,
        "confidence_band_counts": dict(Counter(r["candidate_confidence_band"] for r in records)),
        "advisory_status_counts": dict(Counter(r["advisory_status"] for r in records)),
        "advisory_only": True,
        "llm_used": False,
        "preview": records[:10],
    }
    validation = {
        "all_rows_llm_used_false": all(r["llm_used"] is False for r in records),
        "all_rows_advisory_only": all(r["advisory_status"] in {"advisory_review", "advisory_rejected"} for r in records),
        "no_monitored_universe_writes_attempted": True,
        "idempotency_fields_present": all(all(k in r for k in ["run_date_sgt", "theme_name", "candidate_asset_id", "discovery_method"]) for r in records),
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    print(f"[tier3h4] run_date_sgt={sgt_date} records={len(records)} upsert_status={upsert_status} soft_fallback={soft_fallback}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
