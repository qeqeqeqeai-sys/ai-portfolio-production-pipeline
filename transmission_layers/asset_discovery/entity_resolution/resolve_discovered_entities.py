from __future__ import annotations
import json, os, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from .audit_writer import fetch_table_rows, write_audit_rows
    from .canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
    from .ticker_normalizer import normalize_ticker
    from .exchange_normalizer import normalize_exchange
    from .confidence_scoring import compute_confidence
    from .disambiguation_rules import apply_rules
    from .duplicate_consolidator import apply_duplicate_sizes
except ImportError:
    from transmission_layers.asset_discovery.entity_resolution.audit_writer import fetch_table_rows, write_audit_rows
    from transmission_layers.asset_discovery.entity_resolution.canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
    from transmission_layers.asset_discovery.entity_resolution.ticker_normalizer import normalize_ticker
    from transmission_layers.asset_discovery.entity_resolution.exchange_normalizer import normalize_exchange
    from transmission_layers.asset_discovery.entity_resolution.confidence_scoring import compute_confidence
    from transmission_layers.asset_discovery.entity_resolution.disambiguation_rules import apply_rules
    from transmission_layers.asset_discovery.entity_resolution.duplicate_consolidator import apply_duplicate_sizes

LOG_PATH = Path("logs/tier3h4c_entity_resolution_summary.json")


def _run_date_sgt() -> str:
    env = os.getenv("RUN_DATE_SGT")
    if env:
        return env
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()


def main() -> int:
    run_date = _run_date_sgt()
    theme = os.getenv("THEME_NAME", "ai")
    workflow_run_id = os.getenv("WORKFLOW_RUN_ID") or os.getenv("GITHUB_RUN_ID")
    warnings, errors = [], []

    candidates, err1 = fetch_table_rows("tier3h_dynamic_entity_discovery", run_date, theme)
    evidence, err2 = fetch_table_rows("tier3h_dynamic_entity_evidence", run_date, theme)
    if err1: warnings.append(err1)
    if err2: warnings.append(err2)

    by_asset = {}
    for e in evidence:
        key = str(e.get("candidate_asset_id") or e.get("candidate_name") or "")
        by_asset.setdefault(key, []).append(e)

    audit_rows = []
    for c in candidates:
        raw_name = c.get("candidate_name")
        nt, suspicious = normalize_ticker(c.get("ticker") or c.get("candidate_ticker"))
        ne = normalize_exchange(c.get("exchange") or c.get("candidate_exchange"))
        nn = normalize_name(raw_name)
        asset_type = guess_asset_type(raw_name, nt, c)
        ev = by_asset.get(str(c.get("candidate_asset_id") or c.get("candidate_name") or ""), [])
        urls = [x.get("source_url") for x in ev if x.get("source_url")]
        source_count = len({u for u in urls})
        flags = {
            "has_ticker": bool(nt), "has_exchange": bool(ne), "has_name": bool(nn), "asset_type_known": asset_type != "unknown",
            "source_count": source_count, "has_evidence_urls": bool(urls), "suspicious_ticker": suspicious,
            "generic_name": is_generic_name(nn), "missing_ticker": not bool(nt),
            "missing_exchange_for_ambiguous": bool(nt) and not bool(ne) and len(nt) <= 4,
            "etf_company_conflict": ("etf" in (raw_name or "").lower()) and asset_type == "equity",
        }
        score = compute_confidence(flags)
        rules, suppression_reason, status = apply_rules(flags, score)
        audit_rows.append({
            "run_date_sgt": run_date, "workflow_run_id": workflow_run_id, "theme_name": theme,
            "raw_entity_name": raw_name, "normalized_name": nn,
            "candidate_ticker": c.get("ticker") or c.get("candidate_ticker"), "normalized_ticker": nt,
            "candidate_exchange": c.get("exchange") or c.get("candidate_exchange"), "normalized_exchange": ne,
            "asset_type_guess": asset_type, "canonical_entity_id": None,
            "resolution_status": status, "resolution_confidence": score,
            "rules_fired": rules, "suppression_reason": suppression_reason,
            "evidence_urls": urls, "source_count": source_count,
        })

    audit_rows = apply_duplicate_sizes(audit_rows)
    write_status = write_audit_rows(audit_rows)
    if write_status.startswith("write_"):
        errors.append(write_status)
    elif write_status.startswith("skipped"):
        warnings.append(write_status)

    counts = Counter(r["resolution_status"] for r in audit_rows)
    summary = {
        "run_date_sgt": run_date, "workflow_run_id": workflow_run_id, "theme_name": theme,
        "input_rows": len(candidates), "audit_rows_written": len(audit_rows) if write_status == "written" else 0,
        "resolved_high_confidence_count": counts.get("resolved_high_confidence", 0),
        "resolved_medium_confidence_count": counts.get("resolved_medium_confidence", 0),
        "unresolved_review_count": counts.get("unresolved_review", 0),
        "suppressed_count": counts.get("suppressed", 0),
        "duplicate_groups_count": len({r.get("duplicate_group_key") for r in audit_rows}),
        "ambiguous_count": sum(1 for r in audit_rows if "missing_exchange_for_ambiguous_ticker" in r.get("rules_fired", [])),
        "generic_name_suppressed_count": sum(1 for r in audit_rows if r.get("suppression_reason") == "generic_name"),
        "suspicious_ticker_count": sum(1 for r in audit_rows if "suspicious_ticker" in r.get("rules_fired", [])),
        "missing_exchange_count": sum(1 for r in audit_rows if not r.get("normalized_exchange")),
        "status": "ok" if not errors else "warning",
        "warnings": warnings,
        "errors": errors,
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
