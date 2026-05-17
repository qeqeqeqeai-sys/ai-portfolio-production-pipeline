from __future__ import annotations
import json, os, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from .audit_writer import fetch_table_rows_with_fallback, write_audit_rows
    from .canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
    from .ticker_normalizer import normalize_ticker
    from .exchange_normalizer import normalize_exchange
    from .confidence_scoring import compute_confidence
    from .disambiguation_rules import apply_rules
    from .duplicate_consolidator import apply_duplicate_sizes
    from .canonical_registry import lookup_by_ticker, lookup_by_name, lookup_by_alias
    from ..security_identifier_extraction import extract_security_identifier
except ImportError:
    from transmission_layers.asset_discovery.entity_resolution.audit_writer import fetch_table_rows_with_fallback, write_audit_rows
    from transmission_layers.asset_discovery.entity_resolution.canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
    from transmission_layers.asset_discovery.entity_resolution.ticker_normalizer import normalize_ticker
    from transmission_layers.asset_discovery.entity_resolution.exchange_normalizer import normalize_exchange
    from transmission_layers.asset_discovery.entity_resolution.confidence_scoring import compute_confidence
    from transmission_layers.asset_discovery.entity_resolution.disambiguation_rules import apply_rules
    from transmission_layers.asset_discovery.entity_resolution.duplicate_consolidator import apply_duplicate_sizes
    from transmission_layers.asset_discovery.entity_resolution.canonical_registry import lookup_by_ticker, lookup_by_name, lookup_by_alias
    from transmission_layers.asset_discovery.security_identifier_extraction import extract_security_identifier

LOG_PATH = Path("logs/tier3h4c_entity_resolution_summary.json")
CANDIDATE_TABLES = ["tier3h_dynamic_entity_discovery", "tier3h4_dynamic_entity_discovery", "tier3h_entity_discovery"]
EVIDENCE_TABLES = ["tier3h_dynamic_entity_evidence", "tier3h4_dynamic_entity_evidence", "tier3h_dynamic_discovery_evidence", "tier3h_entity_evidence"]
EMBEDDED_EVIDENCE_KEYS = ["evidence_url", "source_url", "source_domain", "evidence_snippet", "source_title", "tavily_response", "evidence_sources", "source_count"]

def _extract_embedded_evidence(row: dict) -> tuple[list[str], int]:
    urls = []
    if row.get("evidence_url"):
        urls.append(str(row.get("evidence_url")))
    if row.get("source_url"):
        urls.append(str(row.get("source_url")))
    sources = row.get("evidence_sources")
    if isinstance(sources, list):
        for item in sources:
            if isinstance(item, dict) and item.get("source_url"):
                urls.append(str(item.get("source_url")))
    unique_urls = list(dict.fromkeys([u for u in urls if u]))
    explicit_count = row.get("source_count") or row.get("evidence_count")
    source_count = int(explicit_count) if isinstance(explicit_count, int) else len(unique_urls)
    return unique_urls, max(source_count, len(unique_urls))

def _run_date_sgt() -> str:
    return os.getenv("RUN_DATE_SGT") or (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()

def main() -> int:
    run_date, theme = _run_date_sgt(), os.getenv("THEME_NAME", "ai")
    workflow_run_id = os.getenv("WORKFLOW_RUN_ID") or os.getenv("GITHUB_RUN_ID")
    warnings, errors = [], []

    candidates, cand_meta = fetch_table_rows_with_fallback(CANDIDATE_TABLES, run_date, theme)
    evidence, ev_meta = fetch_table_rows_with_fallback(EVIDENCE_TABLES, run_date, theme)
    if cand_meta.get("warning"): warnings.append(cand_meta["warning"])
    warnings.extend([w for w in ev_meta.get("warnings", []) if w])

    by_asset = {}
    for e in evidence:
        by_asset.setdefault(str(e.get("candidate_asset_id") or e.get("candidate_name") or ""), []).append(e)

    has_embedded_fields = any(any(k in c for k in EMBEDDED_EVIDENCE_KEYS) for c in candidates)
    evidence_source_mode = "separate_table" if evidence else ("embedded_candidate_fields" if has_embedded_fields else "unavailable")
    evidence_selected_reason = "separate evidence table rows found" if evidence else ("candidate rows contain embedded evidence-like fields" if has_embedded_fields else "no evidence rows or embedded fields found")

    stats = Counter()
    audit_rows = []
    for c in candidates:
        raw_name = c.get("candidate_name")
        identifier = extract_security_identifier(c)
        nt, suspicious = normalize_ticker(identifier.extracted_ticker or c.get("ticker") or c.get("candidate_ticker"))
        ne_raw = normalize_exchange(identifier.raw_exchange or c.get("exchange") or c.get("candidate_exchange"))
        nn = normalize_name(raw_name)

        ticker_matches = lookup_by_ticker(nt)
        name_matches = lookup_by_name(nn)
        alias_matches = lookup_by_alias(nn)
        registry_matches = ticker_matches or name_matches or alias_matches

        inferred_exchange = ticker_matches[0].exchange if (not ne_raw and len(ticker_matches) == 1) else None
        normalized_exchange = ne_raw or inferred_exchange
        if inferred_exchange: stats["exchange_inferred_from_registry_count"] += 1
        if registry_matches: stats["registry_matched_count"] += 1

        ev = by_asset.get(str(c.get("candidate_asset_id") or c.get("candidate_name") or ""), [])
        urls = [x.get("source_url") for x in ev if x.get("source_url")]
        source_count = len({u for u in urls})
        if not urls:
            urls, source_count = _extract_embedded_evidence(c)
        asset_type = identifier.security_type if identifier.security_type != "unknown" else guess_asset_type(raw_name, nt, c)
        flags = {
            "has_ticker": bool(nt), "has_exchange": bool(normalized_exchange), "has_name": bool(nn),
            "asset_type_known": asset_type != "unknown", "source_count": source_count,
            "has_evidence_urls": bool(urls), "suspicious_ticker": suspicious, "generic_name": is_generic_name(nn),
            "missing_ticker": not bool(nt), "etf_company_conflict": ("etf" in (raw_name or "").lower()) and asset_type == "equity",
            "registry_ticker_match": len(ticker_matches) == 1,
            "registry_name_or_alias_match": bool(name_matches or alias_matches),
            "exchange_inferred_from_registry": bool(inferred_exchange),
            "missing_exchange_without_registry": bool(nt) and not bool(normalized_exchange),
        }
        score = compute_confidence(flags)
        rules, suppression_reason, status = apply_rules(flags, score)
        if flags["missing_exchange_without_registry"]: stats["unresolved_due_to_missing_exchange_count"] += 1
        if suppression_reason: stats["hard_suppressed_count"] += 1
        if flags["missing_exchange_without_registry"] and status != "suppressed": stats["downgraded_missing_exchange_count"] += 1

        identifier_rules_payload = {
            "identifier_method": identifier.identifier_method,
            "identifier_source": identifier.identifier_source,
            "identifier_status": identifier.identifier_status,
            "identifier_confidence": identifier.identifier_confidence,
            "identifier_explanation": identifier.identifier_explanation,
            "identifier_warnings": list(identifier.identifier_warnings or []),
        }
        rules_payload = list(rules or [])
        rules_payload.append({"deterministic_identifier": identifier_rules_payload})

        canonical_entity_id = None
        if identifier.canonical_security_id:
            canonical_entity_id = identifier.canonical_security_id
        elif len(ticker_matches) == 1:
            canonical_entity_id = ticker_matches[0].ticker

        audit_rows.append({
            "run_date_sgt": run_date, "workflow_run_id": workflow_run_id, "theme_name": theme,
            "raw_entity_name": raw_name, "normalized_name": nn,
            "candidate_ticker": identifier.extracted_ticker or c.get("ticker") or c.get("candidate_ticker"), "normalized_ticker": nt,
            "candidate_exchange": identifier.raw_exchange or c.get("exchange") or c.get("candidate_exchange"), "normalized_exchange": identifier.normalized_exchange or normalized_exchange,
            "asset_type_guess": asset_type, "canonical_entity_id": canonical_entity_id,
            "resolution_status": status, "resolution_confidence": score,
            "rules_fired": rules_payload, "suppression_reason": suppression_reason,
            "evidence_urls": list(urls or []), "source_count": int(source_count or 0),
            "duplicate_group_size": 1,
        })

    audit_rows = apply_duplicate_sizes(audit_rows)
    for r in audit_rows:
        r.setdefault("run_date_sgt", run_date)
        r.setdefault("resolution_status", "unresolved_review")
        r.setdefault("rules_fired", [])
        r.setdefault("evidence_urls", [])
        r.setdefault("source_count", 0)
        r.setdefault("duplicate_group_size", 1)
    write_result = write_audit_rows(audit_rows)
    write_status = write_result.get("status", "unknown")
    if write_status.startswith("write_"): errors.append(write_status)
    elif write_status.startswith("skipped"): warnings.append(write_status)

    counts = Counter(r["resolution_status"] for r in audit_rows)
    summary = {
        "run_date_sgt": run_date, "workflow_run_id": workflow_run_id, "theme_name": theme,
        "candidate_table_selected": cand_meta.get("table_selected"), "evidence_table_selected": ev_meta.get("table_selected"),
        "evidence_source_mode": evidence_source_mode, "evidence_selected_reason": evidence_selected_reason,
        "failed_evidence_table_attempts": ev_meta.get("warnings", []),
        "candidate_tables_attempted": cand_meta.get("tables_attempted", []), "evidence_tables_attempted": ev_meta.get("tables_attempted", []),
        "candidate_read_warning": cand_meta.get("warning"), "evidence_read_warning": ev_meta.get("warning"),
        "sample_candidate_keys": sorted(list((candidates[0].keys() if candidates else [])))[:25],
        "sample_candidate_fields_present": [k for k in EMBEDDED_EVIDENCE_KEYS if candidates and k in candidates[0]],
        "sample_audit_row_keys": sorted(list((audit_rows[0].keys() if audit_rows else []))),
        "audit_payload_column_count": len(audit_rows[0].keys()) if audit_rows else 0,
        "candidate_table_columns_detected": sorted(list({k for c in candidates for k in c.keys()}))[:120],
        "evidence_table_columns_detected": sorted(list({k for e in evidence for k in e.keys()}))[:120],
        "candidate_rows_read": cand_meta.get("rows_read", 0), "evidence_rows_read": ev_meta.get("rows_read", 0),
        "evidence_join_rows_used": sum(len(v) for v in by_asset.values()),
        "input_rows": len(candidates), "audit_rows_written": len(audit_rows) if write_status == "written" else 0,
        "rows_with_evidence": sum(1 for r in audit_rows if r.get("source_count", 0) > 0), "rows_without_evidence": sum(1 for r in audit_rows if r.get("source_count", 0) == 0),
        "rows_with_ticker": sum(1 for r in audit_rows if r.get("normalized_ticker")), "rows_without_ticker": sum(1 for r in audit_rows if not r.get("normalized_ticker")),
        "rows_with_exchange": sum(1 for r in audit_rows if r.get("normalized_exchange")), "rows_without_exchange": sum(1 for r in audit_rows if not r.get("normalized_exchange")),
        "resolved_high_confidence_count": counts.get("resolved_high_confidence", 0), "resolved_medium_confidence_count": counts.get("resolved_medium_confidence", 0),
        "unresolved_review_count": counts.get("unresolved_review", 0), "suppressed_count": counts.get("suppressed", 0),
        "duplicate_groups_count": len({r.get("duplicate_group_key") for r in audit_rows}), "missing_exchange_count": sum(1 for r in audit_rows if not r.get("normalized_exchange")),
        "registry_matched_count": stats["registry_matched_count"], "exchange_inferred_from_registry_count": stats["exchange_inferred_from_registry_count"],
        "downgraded_missing_exchange_count": stats["downgraded_missing_exchange_count"], "hard_suppressed_count": stats["hard_suppressed_count"],
        "unresolved_due_to_missing_exchange_count": stats["unresolved_due_to_missing_exchange_count"],
        "status": "ok" if not errors else "warning", "warnings": warnings, "errors": errors,
        "write_error_code": write_result.get("write_error_code"),
        "write_error_message": write_result.get("write_error_message"),
        "write_error_details": write_result.get("write_error_details"),
        "write_error_hint": write_result.get("write_error_hint"),
    }
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
