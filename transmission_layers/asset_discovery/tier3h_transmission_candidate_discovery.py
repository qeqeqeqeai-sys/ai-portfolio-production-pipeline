from __future__ import annotations

import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import requests

ALLOWED_ACTIONS = {"watch", "review", "candidate_add", "reject"}
TABLE_NAME = "tier3h_transmission_candidates"
LOG_DIR = Path("logs")
SUMMARY_PATH = LOG_DIR / "tier3h_candidate_discovery_summary.json"
VALIDATION_PATH = LOG_DIR / "tier3h_candidate_discovery_validation.json"
MANIFEST_PATH = LOG_DIR / "tier3h_candidate_discovery_manifest.json"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def run_date_sgt(today_utc: datetime | None = None) -> str:
    now = today_utc or utc_now()
    return (now + timedelta(hours=8)).date().isoformat()


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


def discover_candidates(rows: list[dict[str, Any]], sgt_date: str) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for row in rows:
        symbol = str(row.get("candidate_symbol") or row.get("symbol") or "").strip().upper()
        if not symbol:
            continue
        theme = str(row.get("discovery_theme") or row.get("theme") or "unknown_theme").strip()
        source = str(row.get("candidate_source") or row.get("source") or "local_transmission_inputs").strip()

        pos = float(row.get("positive_transmission_score") or row.get("positive_score") or row.get("transmission_score") or 0)
        neg = float(row.get("negative_transmission_score") or row.get("negative_score") or 0)
        evid = int(row.get("evidence_count") or 1)

        key = (symbol, theme, source)
        item = grouped.setdefault(
            key,
            {
                "run_date_sgt": sgt_date,
                "candidate_symbol": symbol,
                "candidate_name": row.get("candidate_name") or row.get("name") or symbol,
                "asset_class": row.get("asset_class") or "equity",
                "discovery_theme": theme,
                "candidate_source": source,
                "positive_transmission_score": 0.0,
                "negative_transmission_score": 0.0,
                "evidence_count": 0,
                "snapshot_id": str(row.get("snapshot_id") or f"tier3h-{sgt_date}"),
            },
        )
        item["positive_transmission_score"] += max(pos, 0.0)
        item["negative_transmission_score"] += max(neg, 0.0)
        item["evidence_count"] += max(evid, 0)

    output: list[dict[str, Any]] = []
    for item in grouped.values():
        net = item["positive_transmission_score"] - item["negative_transmission_score"]
        strength = min(abs(net) / 5.0, 1.0)
        evidence_factor = min(item["evidence_count"] / 8.0, 1.0)
        confidence = round((0.6 * strength) + (0.4 * evidence_factor), 4)

        if net >= 3 and item["evidence_count"] >= 4:
            action = "candidate_add"
        elif net >= 1.5 and item["evidence_count"] >= 2:
            action = "review"
        elif net >= 0.3:
            action = "watch"
        else:
            action = "reject"

        output.append(
            {
                **item,
                "positive_transmission_score": round(item["positive_transmission_score"], 4),
                "negative_transmission_score": round(item["negative_transmission_score"], 4),
                "net_transmission_score": round(net, 4),
                "confidence_score": confidence,
                "discovery_reason": (
                    f"Deterministic advisory scoring from local transmission evidence; net={round(net,4)}, "
                    f"evidence_count={item['evidence_count']}"
                ),
                "recommended_action": action,
                "status": "advisory_only",
            }
        )
    return sorted(output, key=lambda r: (r["recommended_action"], -r["confidence_score"], r["candidate_symbol"]))


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
    search_paths = [
        Path("logs/transmission_candidate_inputs.json"),
        Path("logs/phase5d_structural_propagation_regime_forecasting_summary.json"),
        Path("logs/phase3e_transmission_potential_surface_summary.json"),
    ]
    upstream_rows: list[dict[str, Any]] = []
    used_sources: list[str] = []
    for p in search_paths:
        rows = load_json_rows(p)
        if rows:
            upstream_rows.extend(rows)
            used_sources.append(str(p))

    candidates = discover_candidates(upstream_rows, sgt_date) if upstream_rows else []
    supabase_result = upsert_supabase(candidates)

    validation = {
        "allowed_actions": sorted(ALLOWED_ACTIONS),
        "all_actions_valid": all(c["recommended_action"] in ALLOWED_ACTIONS for c in candidates),
        "advisory_only_status": all(c["status"] == "advisory_only" for c in candidates),
        "candidate_count": len(candidates),
        "upstream_present": bool(upstream_rows),
        "notes": "No main universe writes/updates/deletes are performed by Tier 3H.",
    }
    summary = {
        "module": "tier3h_transmission_candidate_discovery",
        "run_timestamp_utc": utc_now().isoformat(),
        "run_date_sgt": sgt_date,
        "upstream_sources_used": used_sources,
        "upstream_row_count": len(upstream_rows),
        "candidate_count": len(candidates),
        "supabase_upsert": supabase_result,
        "advisory_only": True,
        "soft_failure": not bool(upstream_rows),
        "message": "No upstream data available; advisory run completed with zero candidates."
        if not upstream_rows
        else "Advisory candidate discovery completed.",
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
