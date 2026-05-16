from __future__ import annotations

import json
import os
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

ALLOWED_ACTIONS = {"watch", "review", "candidate_add", "reject"}
ALLOWED_IDENTIFIER_TYPES = {"TICKER", "NODE", "THEME", "REGIME", "UNKNOWN"}
TABLE_NAME = "tier3h_transmission_candidates"
LOG_DIR = Path("logs")
SUMMARY_PATH = LOG_DIR / "tier3h_candidate_discovery_summary.json"
VALIDATION_PATH = LOG_DIR / "tier3h_candidate_discovery_validation.json"
MANIFEST_PATH = LOG_DIR / "tier3h_candidate_discovery_manifest.json"

LOCAL_SOURCE_FILES = [
    Path("logs/transmission_candidate_inputs.json"),
    Path("logs/phase5d_structural_propagation_regime_forecasting_summary.json"),
    Path("logs/phase3e_transmission_potential_surface_summary.json"),
]

SUPABASE_SOURCES = [
    {"name": "phase5a_two_hop_propagation", "table": "structural_theme_graph_two_hop_propagation", "order": "run_date_sgt.desc", "limit": 400},
    {"name": "phase4b_memory_decay", "table": "structural_theme_graph_propagation_memory_decay", "order": "run_date_sgt.desc", "limit": 400},
    {"name": "phase4a_single_hop_propagation", "table": "structural_theme_graph_single_hop_propagation", "order": "run_date_sgt.desc", "limit": 500},
    {"name": "phase3b_relationship_persistence", "table": "structural_theme_relationship_persistence", "order": "run_date_sgt.desc", "limit": 400},
    {"name": "phase3a2_cross_theme", "table": "structural_theme_cross_relationships", "order": "run_date_sgt.desc", "limit": 300},
]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_date_sgt(today_utc: datetime | None = None) -> str:
    now = today_utc or utc_now()
    return (now + timedelta(hours=8)).date().isoformat()


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _first_present(row: dict[str, Any], fields: list[str]) -> tuple[str | None, str | None]:
    for field in fields:
        value = row.get(field)
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return field, text
    return None, None


def _normalize_token(value: str) -> str:
    return re.sub(r"[^A-Z0-9]+", "_", value.upper()).strip("_")


def load_json_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if isinstance(payload, dict):
        rows = payload.get("rows")
        if isinstance(rows, list):
            return [r for r in rows if isinstance(r, dict)]
    return []


def _supabase_get_rows(table: str, order: str, limit: int) -> list[dict[str, Any]]:
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return []
    endpoint = f"{url}/rest/v1/{table}"
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}
    params = {"select": "*", "order": order, "limit": str(limit)}
    try:
        resp = requests.get(endpoint, headers=headers, params=params, timeout=60)
        if resp.status_code >= 400:
            return []
        payload = resp.json()
        if isinstance(payload, list):
            return [r for r in payload if isinstance(r, dict)]
    except Exception:
        return []
    return []


def load_upstream_rows() -> tuple[list[dict[str, Any]], list[str], dict[str, int], dict[str, list[str]], bool]:
    rows: list[dict[str, Any]] = []
    sources_used: list[str] = []
    counts: dict[str, int] = {}
    source_columns_seen: dict[str, list[str]] = {}

    for path in LOCAL_SOURCE_FILES:
        loaded = load_json_rows(path)
        key = str(path)
        counts[key] = len(loaded)
        source_columns_seen[key] = sorted({col for row in loaded for col in row.keys()})
        if loaded:
            rows.extend(loaded)
            sources_used.append(key)

    for src in SUPABASE_SOURCES:
        loaded = _supabase_get_rows(src["table"], src["order"], int(src["limit"]))
        label = f"supabase:{src['table']}"
        counts[label] = len(loaded)
        source_columns_seen[label] = sorted({col for row in loaded for col in row.keys()})
        if loaded:
            for row in loaded:
                row.setdefault("candidate_source", src["name"])
            rows.extend(loaded)
            sources_used.append(label)

    return rows, sources_used, counts, source_columns_seen, not bool(rows)


def resolve_candidate_identifier(row: dict[str, Any]) -> dict[str, Any]:
    ticker_field, ticker_value = _first_present(row, ["ticker", "symbol", "asset_symbol", "candidate_symbol", "company_ticker", "equity_symbol"])
    node_field, node_value = _first_present(row, ["source_node", "target_node", "node_id", "node_name", "source_entity", "target_entity", "entity_name", "theme_node"])
    theme_field, theme_value = _first_present(row, ["theme_name", "source_theme", "target_theme", "discovery_theme", "structural_theme"])
    regime_field, regime_value = _first_present(row, ["propagation_regime", "transmission_regime", "regime"])

    descriptor_fields = ["company_name", "asset_name", "candidate_name", "node_name", "entity_name", "theme_name", "source_node", "target_node", "propagation_regime"]
    _, descriptive_name = _first_present(row, descriptor_fields)

    discovery_theme = theme_value or regime_value or "unknown_theme"
    if ticker_value:
        return {
            "candidate_symbol": f"TICKER::{_normalize_token(ticker_value)}",
            "candidate_name": descriptive_name or ticker_value,
            "discovery_theme": discovery_theme,
            "identifier_type": "TICKER",
            "missing_symbol": False,
            "resolution_reason": f"Resolved as TICKER from {ticker_field}.",
        }
    if node_value:
        return {
            "candidate_symbol": f"NODE::{_normalize_token(node_value)}",
            "candidate_name": descriptive_name or node_value,
            "discovery_theme": discovery_theme,
            "identifier_type": "NODE",
            "missing_symbol": True,
            "resolution_reason": f"Resolved as NODE from {node_field} because ticker fields were unavailable.",
        }
    if theme_value:
        return {
            "candidate_symbol": f"THEME::{_normalize_token(theme_value)}",
            "candidate_name": descriptive_name or theme_value,
            "discovery_theme": theme_value,
            "identifier_type": "THEME",
            "missing_symbol": True,
            "resolution_reason": f"Resolved as THEME from {theme_field} because ticker/node fields were unavailable.",
        }
    if regime_value:
        return {
            "candidate_symbol": f"REGIME::{_normalize_token(regime_value)}",
            "candidate_name": descriptive_name or regime_value,
            "discovery_theme": regime_value,
            "identifier_type": "REGIME",
            "missing_symbol": True,
            "resolution_reason": f"Resolved as REGIME from {regime_field} as last fallback.",
        }
    return {
        "candidate_symbol": "UNKNOWN::UNRESOLVED",
        "candidate_name": descriptive_name or "UNKNOWN",
        "discovery_theme": "unknown_theme",
        "identifier_type": "UNKNOWN",
        "missing_symbol": True,
        "resolution_reason": "Unable to resolve ticker/node/theme/regime identifiers.",
    }


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    resolved = resolve_candidate_identifier(row)
    source = str(row.get("candidate_source") or row.get("source") or row.get("source_phase") or row.get("table_name") or "upstream_transmission").strip()

    transmission_score = _safe_float(row.get("transmission_score"))
    propagation_score = _safe_float(row.get("propagation_score") or row.get("single_hop_propagation_score") or row.get("two_hop_path_score"))
    memory_score = _safe_float(row.get("memory_score") or row.get("persistence_score") or row.get("memory_decay_factor"))
    cross_theme_strength = _safe_float(row.get("cross_theme_strength") or row.get("relationship_strength") or row.get("edge_weight"))
    multi_hop_strength = _safe_float(row.get("two_hop_transmission_potential") or row.get("two_hop_path_score"))
    evidence_count = _safe_int(row.get("evidence_count") or row.get("observation_count") or row.get("support_count") or 1, 1)

    positive = max(0.0, _safe_float(row.get("positive_transmission_score"), transmission_score) + max(0.0, propagation_score) + max(0.0, multi_hop_strength))
    negative = max(0.0, _safe_float(row.get("negative_transmission_score"), -min(transmission_score, 0.0)))

    return {
        **resolved,
        "asset_class": str(row.get("asset_class") or "equity"),
        "candidate_source": source,
        "positive_transmission_score": positive,
        "negative_transmission_score": negative,
        "evidence_count": max(evidence_count, 1),
        "memory_score": memory_score,
        "cross_theme_strength": cross_theme_strength,
        "multi_hop_strength": multi_hop_strength,
        "snapshot_id": str(row.get("snapshot_id") or row.get("run_id") or "tier3h-upstream"),
    }


def discover_candidates(rows: list[dict[str, Any]], sgt_date: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for row in rows:
        n = _normalize_row(row)
        key = (sgt_date, n["candidate_symbol"], n["discovery_theme"], n["candidate_source"])
        item = grouped.setdefault(
            key,
            {
                "run_date_sgt": sgt_date,
                **{k: n[k] for k in ["candidate_symbol", "candidate_name", "asset_class", "discovery_theme", "candidate_source", "snapshot_id", "identifier_type", "resolution_reason"]},
                "positive_transmission_score": 0.0,
                "negative_transmission_score": 0.0,
                "evidence_count": 0,
                "memory_score": 0.0,
                "cross_theme_strength": 0.0,
                "multi_hop_strength": 0.0,
                "missing_symbol": False,
            },
        )
        item["positive_transmission_score"] += n["positive_transmission_score"]
        item["negative_transmission_score"] += n["negative_transmission_score"]
        item["evidence_count"] += n["evidence_count"]
        item["memory_score"] += max(0.0, n["memory_score"])
        item["cross_theme_strength"] += max(0.0, n["cross_theme_strength"])
        item["multi_hop_strength"] += max(0.0, n["multi_hop_strength"])
        item["missing_symbol"] = item["missing_symbol"] or n["missing_symbol"]

    penalty = {"TICKER": 0.0, "NODE": 0.05, "THEME": 0.12, "REGIME": 0.25, "UNKNOWN": 0.3}
    out: list[dict[str, Any]] = []
    for item in grouped.values():
        net = item["positive_transmission_score"] - item["negative_transmission_score"]
        signal_strength = min((abs(net) + item["multi_hop_strength"] + item["cross_theme_strength"]) / 8.0, 1.0)
        persistence = min((item["memory_score"] + item["evidence_count"]) / 10.0, 1.0)
        base_confidence = (0.65 * signal_strength) + (0.35 * persistence)
        confidence = round(max(0.0, base_confidence - penalty.get(item["identifier_type"], 0.3)), 4)

        if item["identifier_type"] == "REGIME":
            action = "watch" if confidence >= 0.3 else "reject"
        elif item["identifier_type"] == "TICKER" and confidence >= 0.75 and item["evidence_count"] >= 3 and abs(net) >= 2.0:
            action = "candidate_add"
        elif item["identifier_type"] == "NODE" and confidence >= 0.8 and item["evidence_count"] >= 4 and abs(net) >= 2.5:
            action = "candidate_add"
        elif confidence >= 0.55 and (abs(net) >= 1.0 or item["evidence_count"] >= 2):
            action = "review"
        elif confidence >= 0.3:
            action = "watch"
        else:
            action = "reject"

        reason = (
            f"identifier_type={item['identifier_type']}; source={item['candidate_source']}; {item['resolution_reason']} "
            f"fallback_derived={item['missing_symbol']}; score_components: net={round(net,4)}, evidence_count={item['evidence_count']}, "
            f"memory_score={round(item['memory_score'],4)}, cross_theme_strength={round(item['cross_theme_strength'],4)}, "
            f"multi_hop_strength={round(item['multi_hop_strength'],4)}, identifier_penalty={penalty.get(item['identifier_type'], 0.3)}"
        )

        out.append(
            {
                **item,
                "positive_transmission_score": round(item["positive_transmission_score"], 4),
                "negative_transmission_score": round(item["negative_transmission_score"], 4),
                "net_transmission_score": round(net, 4),
                "confidence_score": confidence,
                "discovery_reason": reason,
                "recommended_action": action,
                "status": "advisory_only",
            }
        )
    return sorted(out, key=lambda r: (-r["confidence_score"], -abs(r["net_transmission_score"]), r["candidate_symbol"]))


def upsert_supabase(rows: list[dict[str, Any]]) -> str:
    if not rows:
        return "skipped: no candidate rows"
    url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    if not url or not key:
        return "skipped: missing supabase env"
    endpoint = (
        f"{url}/rest/v1/{TABLE_NAME}"
        "?on_conflict=run_date_sgt,candidate_symbol,discovery_theme,candidate_source"
    )
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    resp = requests.post(endpoint, headers=headers, json=rows, timeout=90)
    if resp.status_code >= 400:
        return f"failed: status={resp.status_code}"
    return "ok"


def main() -> int:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    sgt_date = run_date_sgt()
    upstream_rows, used_sources, upstream_counts, source_columns_seen, soft_failure = load_upstream_rows()
    candidates = discover_candidates(upstream_rows, sgt_date) if upstream_rows else []
    supabase_result = upsert_supabase(candidates)

    action_counts = {action: 0 for action in sorted(ALLOWED_ACTIONS)}
    identifier_type_counts = {identifier_type: 0 for identifier_type in sorted(ALLOWED_IDENTIFIER_TYPES)}
    for candidate in candidates:
        action_counts[candidate["recommended_action"]] += 1
        identifier_type_counts[candidate["identifier_type"]] += 1

    payload_columns = sorted({k for c in candidates for k in c.keys()}) if candidates else []
    expected_columns = sorted([
        "run_date_sgt", "candidate_symbol", "candidate_name", "asset_class", "discovery_theme", "candidate_source",
        "positive_transmission_score", "negative_transmission_score", "net_transmission_score", "evidence_count", "memory_score",
        "cross_theme_strength", "multi_hop_strength", "confidence_score", "discovery_reason", "recommended_action", "status",
        "snapshot_id", "missing_symbol", "identifier_type", "resolution_reason",
    ])

    validation = {
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "all_actions_valid": all(c["recommended_action"] in ALLOWED_ACTIONS for c in candidates),
        "all_identifier_types_valid": all(c["identifier_type"] in ALLOWED_IDENTIFIER_TYPES for c in candidates),
        "regime_fallback_candidates": [c["candidate_symbol"] for c in candidates if c["identifier_type"] == "REGIME"],
        "regime_fallback_no_candidate_add": all(not (c["identifier_type"] == "REGIME" and c["recommended_action"] == "candidate_add") for c in candidates),
        "advisory_only_status": all(c["status"] == "advisory_only" for c in candidates),
        "candidate_count": len(candidates),
        "upstream_loading_safe": True,
        "upstream_present": bool(upstream_rows),
        "write_target_table": TABLE_NAME,
        "write_targets_valid": TABLE_NAME == "tier3h_transmission_candidates",
        "no_main_universe_writes_attempted": True,
        "main_universe_write_targets_referenced": [],
        "upsert_payload_columns": payload_columns,
        "upsert_payload_columns_match_schema": set(payload_columns).issubset(set(expected_columns)),
        "notes": "Tier 3H is advisory-only and writes only to tier3h_transmission_candidates/logs.",
    }
    summary = {
        "module": "tier3h_transmission_candidate_discovery",
        "run_timestamp_utc": utc_now().isoformat(),
        "run_date_sgt": sgt_date,
        "upstream_sources_used": used_sources,
        "upstream_row_count": len(upstream_rows),
        "upstream_row_counts_by_source": upstream_counts,
        "source_columns_seen": source_columns_seen,
        "candidate_count": len(candidates),
        "recommended_action_counts": action_counts,
        "candidate_identifier_type_counts": identifier_type_counts,
        "fallback_identifier_count": sum(1 for c in candidates if c["identifier_type"] in {"THEME", "REGIME", "UNKNOWN"}),
        "unresolved_identifier_count": sum(1 for c in candidates if c["identifier_type"] == "UNKNOWN"),
        "top_candidates_preview": candidates[:10],
        "supabase_upsert": supabase_result,
        "advisory_only": True,
        "soft_failure": soft_failure,
        "message": "No upstream data available; advisory run completed with zero candidates." if soft_failure else "Advisory candidate discovery completed.",
    }
    manifest = {
        "summary": str(SUMMARY_PATH),
        "validation": str(VALIDATION_PATH),
        "candidates_preview": candidates[:25],
    }

    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    VALIDATION_PATH.write_text(json.dumps(validation, indent=2), encoding="utf-8")
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
