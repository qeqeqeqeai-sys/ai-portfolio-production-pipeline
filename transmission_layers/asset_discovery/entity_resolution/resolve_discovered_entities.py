from __future__ import annotations
import json, os, sys
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    from .audit_writer import fetch_table_rows_with_fallback, write_audit_rows, write_evidence_rows
    from .canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
    from .ticker_normalizer import normalize_ticker
    from .exchange_normalizer import normalize_exchange
    from .confidence_scoring import compute_confidence
    from .disambiguation_rules import apply_rules
    from .duplicate_consolidator import apply_duplicate_sizes
    from .canonical_registry import lookup_by_ticker, lookup_by_name, lookup_by_alias
    from ..security_identifier_extraction import extract_security_identifier, extract_security_identifiers_from_evidence
except ImportError:
    from transmission_layers.asset_discovery.entity_resolution.audit_writer import fetch_table_rows_with_fallback, write_audit_rows, write_evidence_rows
    from transmission_layers.asset_discovery.entity_resolution.canonical_normalizer import normalize_name, guess_asset_type, is_generic_name
    from transmission_layers.asset_discovery.entity_resolution.ticker_normalizer import normalize_ticker
    from transmission_layers.asset_discovery.entity_resolution.exchange_normalizer import normalize_exchange
    from transmission_layers.asset_discovery.entity_resolution.confidence_scoring import compute_confidence
    from transmission_layers.asset_discovery.entity_resolution.disambiguation_rules import apply_rules
    from transmission_layers.asset_discovery.entity_resolution.duplicate_consolidator import apply_duplicate_sizes
    from transmission_layers.asset_discovery.entity_resolution.canonical_registry import lookup_by_ticker, lookup_by_name, lookup_by_alias
    from transmission_layers.asset_discovery.security_identifier_extraction import extract_security_identifier, extract_security_identifiers_from_evidence

LOG_PATH = Path("logs/tier3h4c_entity_resolution_summary.json")
CANDIDATE_TABLES = ["tier3h_dynamic_entity_discovery", "tier3h4_dynamic_entity_discovery", "tier3h_entity_discovery"]
EVIDENCE_TABLES = ["tier3h_dynamic_entity_evidence", "tier3h4_dynamic_entity_evidence", "tier3h_dynamic_discovery_evidence", "tier3h_entity_evidence"]
EMBEDDED_EVIDENCE_KEYS = ["evidence_url", "source_url", "source_domain", "evidence_snippet", "source_title", "tavily_response", "evidence_sources", "source_count"]


def _force_fresh_evidence_enabled() -> bool:
    raw = str(os.getenv("TIER3H4_FORCE_FRESH_EVIDENCE", "")).strip().lower()
    return raw in {"1", "true", "yes", "on"}


def _normalize_value(value: object) -> str:
    return " ".join(str(value or "").strip().split())

def _get_nested(payload: dict[str, object], dotted_key: str) -> object:
    current: object = payload
    for part in dotted_key.split("."):
        if not isinstance(current, dict):
            return None
        current = current.get(part)
    return current

def extract_deterministic_title(payload: dict[str, object] | None) -> tuple[str, str | None]:
    if not isinstance(payload, dict):
        return "", None
    title_keys = [
        "source_title", "title", "page_title", "pageTitle", "metadata.title",
        "metadata.page_title", "raw.title", "raw.page_title",
    ]
    for key in title_keys:
        value = _normalize_value(_get_nested(payload, key))
        if value:
            return value, key
    return "", None

def extract_deterministic_snippet(payload: dict[str, object] | None) -> tuple[str, str | None]:
    if not isinstance(payload, dict):
        return "", None
    snippet_keys = [
        "source_snippet", "snippet", "content", "summary", "text", "raw_content", "rawContent", "description",
        "metadata.description", "metadata.snippet", "raw.snippet", "raw.content", "raw.raw_content",
    ]
    for key in snippet_keys:
        value = _normalize_value(_get_nested(payload, key))
        if value:
            return value, key
    return "", None


def build_enriched_evidence_text(source_title: object, source_snippet: object, structured_metadata: dict[str, object] | None, operational_metadata: dict[str, object] | None) -> str:
    parts: list[str] = []
    title = _normalize_value(source_title)
    snippet = _normalize_value(source_snippet)
    if title:
        parts.append(f"Title: {title}")
    if snippet:
        parts.append(f"Snippet: {snippet}")

    metadata_tokens: list[str] = []
    for key, value in (structured_metadata or {}).items():
        v = _normalize_value(value)
        if v:
            metadata_tokens.append(f"{key}={v}")
    if metadata_tokens:
        parts.append(f"Metadata: {'; '.join(metadata_tokens)}")

    operational_tokens: list[str] = []
    for key, value in (operational_metadata or {}).items():
        v = _normalize_value(value)
        if v:
            operational_tokens.append(f"{key}={v}")
    if operational_tokens:
        parts.append(f"Operational: {'; '.join(operational_tokens)}")
    return "\n\n".join(parts)


def compose_enriched_evidence_payload(candidate: dict, source: dict, base: dict, evidence_rank: int, evidence_type: str) -> dict:
    source_title, _ = extract_deterministic_title(source)
    if not source_title:
        source_title, _ = extract_deterministic_title(candidate)
    source_snippet, _ = extract_deterministic_snippet(source)
    if not source_snippet:
        source_snippet, _ = extract_deterministic_snippet(candidate)
    source_url = source.get("source_url") or source.get("url") or candidate.get("source_url") or candidate.get("evidence_url")
    source_domain = source.get("source_domain") or candidate.get("source_domain")
    if not source_domain and source_url:
        source_domain = str(source_url).split("://", 1)[-1].split("/", 1)[0].lower()
    structured_metadata = {
        "source_type": source.get("source_type") or source.get("type") or candidate.get("discovery_method"),
        "evidence_rank": source.get("source_rank") or source.get("rank") or evidence_rank,
        "tavily_score": source.get("tavily_score") or source.get("score"),
        "published_date": source.get("published_date") or source.get("published"),
        "retrieved_at": source.get("retrieved_at"),
        "cache_reused": source.get("cache_reused"),
        "candidate_ticker": source.get("candidate_ticker"),
        "candidate_exchange": source.get("candidate_exchange"),
    }
    operational_metadata = {
        "candidate_name": candidate.get("candidate_name"),
        "theme_name": base.get("theme_name"),
        "discovery_method": candidate.get("discovery_method"),
        "weighted_score": candidate.get("candidate_confidence_score"),
        "suppression": candidate.get("rejection_reason") or "none",
        "confidence_band": candidate.get("candidate_confidence_band"),
        "advisory_status": candidate.get("advisory_status"),
        "domains": candidate.get("cross_source_score"),
    }
    evidence_text = build_enriched_evidence_text(source_title, source_snippet, structured_metadata, operational_metadata)
    return {
        **base,
        "evidence_text": evidence_text or candidate.get("confidence_explanation") or candidate.get("rejection_reason"),
        "source_url": source_url,
        "source_title": source_title or None,
        "source_domain": source_domain,
        "evidence_type": evidence_type,
        "evidence_rank": evidence_rank,
        "evidence_confidence": source.get("quality") or candidate.get("source_quality_score"),
        "raw_evidence": {
            "source_result": source,
            "candidate_context": {
                "source_node": candidate.get("source_node"),
                "target_node": candidate.get("target_node"),
                "llm_classification_json": candidate.get("llm_classification_json"),
                "confidence_explanation": candidate.get("confidence_explanation"),
                "rejection_reason": candidate.get("rejection_reason"),
            },
        },
    }

def _normalize_embedded_evidence_rows(candidate: dict, run_date: str, workflow_run_id: str | None, theme: str) -> list[dict]:
    base = {
        "run_date_sgt": run_date,
        "workflow_run_id": workflow_run_id,
        "theme_name": theme,
        "candidate_id": candidate.get("candidate_id"),
        "candidate_asset_id": candidate.get("candidate_asset_id"),
        "candidate_name": candidate.get("candidate_name"),
        "extracted_ticker": candidate.get("ticker") or candidate.get("candidate_ticker"),
        "extracted_exchange": candidate.get("exchange") or candidate.get("candidate_exchange"),
        "extraction_method": "embedded_candidate_fields",
        "extraction_confidence": None,
        "extraction_notes": {},
    }
    rows: list[dict] = []
    sources = candidate.get("evidence_sources")
    if isinstance(sources, list) and sources:
        for i, src in enumerate(sources, start=1):
            if not isinstance(src, dict):
                continue
            rows.append(compose_enriched_evidence_payload(candidate, src, base, i, "evidence_sources"))
    elif any(candidate.get(k) for k in ("source_url", "evidence_url", "confidence_explanation", "rejection_reason")):
        rows.append(compose_enriched_evidence_payload(candidate, candidate, base, 1, "embedded_candidate_fields"))
    return rows

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



def _aggregate_evidence_identifiers(evidence_rows: list[dict]) -> tuple[dict, bool]:
    seen = {(r.get("normalized_ticker"), r.get("normalized_exchange")) for r in evidence_rows if r.get("normalized_ticker")}
    seen = {x for x in seen if x[0]}
    if not seen:
        return {"candidate_ticker": None, "normalized_ticker": None, "candidate_exchange": None, "normalized_exchange": None}, False
    if len(seen) > 1:
        return {"candidate_ticker": None, "normalized_ticker": None, "candidate_exchange": None, "normalized_exchange": None}, True
    nt, ne = next(iter(seen))
    sample = next((r for r in evidence_rows if r.get("normalized_ticker") == nt and r.get("normalized_exchange") == ne), {})
    return {"candidate_ticker": sample.get("extracted_ticker"), "normalized_ticker": nt, "candidate_exchange": sample.get("extracted_exchange"), "normalized_exchange": ne}, False

def _run_date_sgt() -> str:
    return os.getenv("RUN_DATE_SGT") or (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()

def main() -> int:
    run_date, theme = _run_date_sgt(), os.getenv("THEME_NAME", "ai")
    workflow_run_id = os.getenv("WORKFLOW_RUN_ID") or os.getenv("GITHUB_RUN_ID")
    warnings, errors = [], []

    candidates, cand_meta = fetch_table_rows_with_fallback(CANDIDATE_TABLES, run_date, theme)
    persisted_rows_to_write = []
    for candidate in candidates:
        persisted_rows_to_write.extend(_normalize_embedded_evidence_rows(candidate, run_date, workflow_run_id, theme))
    write_evidence_result = write_evidence_rows(persisted_rows_to_write)
    evidence_table_created_or_available = write_evidence_result.get("status") in {"written", "skipped:no_rows", "skipped:missing_supabase_env"}

    force_fresh_evidence = _force_fresh_evidence_enabled()
    if force_fresh_evidence:
        evidence, ev_meta = [], {
            "rows_read": 0,
            "table_selected": None,
            "tables_attempted": [],
            "warnings": [],
            "warning": None,
            "read_skipped_due_to_force_fresh": True,
        }
    else:
        evidence, ev_meta = fetch_table_rows_with_fallback(EVIDENCE_TABLES, run_date, theme)
    if cand_meta.get("warning"): warnings.append(cand_meta["warning"])
    warnings.extend([w for w in ev_meta.get("warnings", []) if w])

    strict_identifier_runtime_source = "persisted_evidence_rows" if evidence else ("embedded_in_memory_evidence" if persisted_rows_to_write else "none")
    strict_identifier_rows_scanned = 0
    strict_identifier_matches_found = 0
    strict_identifier_sample_matches: list[dict] = []
    strict_evidence_runtime_rows = evidence if evidence else persisted_rows_to_write

    by_asset = {}
    for e in strict_evidence_runtime_rows:
        strict_identifier_rows_scanned += 1
        extracted = extract_security_identifiers_from_evidence(e.get("evidence_text"), e.get("source_title"), e.get("source_url"), e.get("raw_evidence"), e.get("candidate_ticker"), e.get("candidate_exchange"))
        if extracted.get("normalized_ticker") and extracted.get("normalized_exchange"):
            strict_identifier_matches_found += 1
            if len(strict_identifier_sample_matches) < 5:
                strict_identifier_sample_matches.append({
                    "ticker": extracted.get("normalized_ticker"),
                    "exchange": extracted.get("normalized_exchange"),
                    "source_url": e.get("source_url"),
                    "extraction_method": extracted.get("extraction_method"),
                })
        e.update(extracted)
        by_asset.setdefault(str(e.get("candidate_asset_id") or e.get("candidate_name") or ""), []).append(e)

    has_embedded_fields = any(any(k in c for k in EMBEDDED_EVIDENCE_KEYS) for c in candidates)
    evidence_source_mode = "persisted_evidence_table" if evidence else ("embedded_candidate_fields" if has_embedded_fields else "unavailable")
    evidence_selected_reason = "separate evidence table rows found" if evidence else ("candidate rows contain embedded evidence-like fields" if has_embedded_fields else "no evidence rows or embedded fields found")

    stats = Counter()
    audit_rows = []
    for c in candidates:
        raw_name = c.get("candidate_name")
        identifier = extract_security_identifier(c)
        join_key = str(c.get("candidate_asset_id") or c.get("candidate_name") or "")
        evidence_for_candidate = by_asset.get(join_key, [])
        agg, conflict = _aggregate_evidence_identifiers(evidence_for_candidate)
        nt, suspicious = normalize_ticker(agg.get("candidate_ticker") or identifier.extracted_ticker or c.get("ticker") or c.get("candidate_ticker"))
        ne_raw = normalize_exchange(agg.get("candidate_exchange") or identifier.raw_exchange or c.get("exchange") or c.get("candidate_exchange"))
        nn = normalize_name(raw_name)

        ticker_matches = lookup_by_ticker(nt)
        name_matches = lookup_by_name(nn)
        alias_matches = lookup_by_alias(nn)
        registry_matches = ticker_matches or name_matches or alias_matches

        inferred_exchange = ticker_matches[0].exchange if (not ne_raw and len(ticker_matches) == 1) else None
        normalized_exchange = ne_raw or inferred_exchange
        if inferred_exchange: stats["exchange_inferred_from_registry_count"] += 1
        if registry_matches: stats["registry_matched_count"] += 1

        urls = [x.get("source_url") for x in evidence_for_candidate if x.get("source_url")]
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
        if conflict:
            rules_payload.append({"evidence_identifier_ambiguity": True})
            suppression_reason = suppression_reason or "ambiguous_evidence_identifiers"
            status = "suppressed"

        canonical_entity_id = None
        if identifier.canonical_security_id:
            canonical_entity_id = identifier.canonical_security_id
        elif len(ticker_matches) == 1:
            canonical_entity_id = ticker_matches[0].ticker

        audit_rows.append({
            "run_date_sgt": run_date, "workflow_run_id": workflow_run_id, "theme_name": theme,
            "raw_entity_name": raw_name, "normalized_name": nn,
            "candidate_ticker": agg.get("candidate_ticker") or identifier.extracted_ticker or c.get("ticker") or c.get("candidate_ticker"), "normalized_ticker": agg.get("normalized_ticker") or nt,
            "candidate_exchange": agg.get("candidate_exchange") or identifier.raw_exchange or c.get("exchange") or c.get("candidate_exchange"), "normalized_exchange": agg.get("normalized_exchange") or identifier.normalized_exchange or normalized_exchange,
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
    def _text_has_tag(e: dict, tag: str) -> bool:
        return f"{tag}:" in str(e.get("evidence_text") or "")

    sampled_evidence = evidence[:3]
    summary = {
        "run_date_sgt": run_date, "workflow_run_id": workflow_run_id, "theme_name": theme,
        "evidence_table_created_or_available": evidence_table_created_or_available,
        "candidate_table_selected": cand_meta.get("table_selected"), "evidence_table_selected": ev_meta.get("table_selected"),
        "evidence_source_mode": evidence_source_mode, "evidence_selected_reason": evidence_selected_reason,
        "force_fresh_evidence": force_fresh_evidence,
        "evidence_table_read_skipped_due_to_force_fresh": bool(ev_meta.get("read_skipped_due_to_force_fresh")),
        "evidence_rows_written": write_evidence_result.get("rows_written", 0),
        "evidence_fallback_used": not bool(evidence),
        "evidence_candidate_join_key_used": "candidate_asset_id_or_candidate_name",
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
        "strict_identifier_extraction_enabled": True,
        "strict_identifier_runtime_source": strict_identifier_runtime_source,
        "strict_identifier_rows_scanned": strict_identifier_rows_scanned,
        "strict_identifier_matches_found": strict_identifier_matches_found,
        "strict_identifier_sample_matches": strict_identifier_sample_matches,
        "input_rows": len(candidates), "audit_rows_written": len(audit_rows) if write_status == "written" else 0,
        "rows_with_evidence": sum(1 for r in audit_rows if r.get("source_count", 0) > 0), "rows_without_evidence": sum(1 for r in audit_rows if r.get("source_count", 0) == 0),
        "rows_with_ticker": sum(1 for r in audit_rows if r.get("normalized_ticker")), "rows_without_ticker": sum(1 for r in audit_rows if not r.get("normalized_ticker")),
        "rows_with_exchange": sum(1 for r in audit_rows if r.get("normalized_exchange")), "rows_without_exchange": sum(1 for r in audit_rows if not r.get("normalized_exchange")),
        "evidence_rows_with_ticker": sum(1 for e in evidence if e.get("normalized_ticker")),
        "evidence_rows_with_exchange": sum(1 for e in evidence if e.get("normalized_exchange")),
        "evidence_rows_with_title": sum(1 for e in evidence if _normalize_value(e.get("source_title")) or _text_has_tag(e, "Title")),
        "evidence_rows_with_snippet": sum(1 for e in evidence if _text_has_tag(e, "Snippet")),
        "evidence_rows_with_long_text": sum(1 for e in evidence if len(_normalize_value(e.get("evidence_text"))) >= 120),
        "enriched_evidence_rows_written": sum(1 for e in evidence if _text_has_tag(e, "Title") or _text_has_tag(e, "Snippet")),
        "evidence_rows_missing_textual_content": sum(1 for e in evidence if not _normalize_value(e.get("evidence_text"))),
        "evidence_rows_with_structured_metadata": sum(1 for e in evidence if "Metadata:" in str(e.get("evidence_text") or "")),
        "evidence_rows_with_candidate_name_mentions": sum(1 for e in evidence if _normalize_value(e.get("candidate_name", "")).lower() in _normalize_value(e.get("evidence_text", "")).lower() and _normalize_value(e.get("candidate_name", ""))),
        "sample_raw_evidence_keys": [sorted(list((e.get("raw_evidence") or {}).keys()))[:20] if isinstance(e.get("raw_evidence"), dict) else [] for e in sampled_evidence],
        "source_level_evidence_rows_written": sum(1 for e in evidence if isinstance(e.get("raw_evidence"), dict) and isinstance((e.get("raw_evidence") or {}).get("source_result"), dict)),
        "candidate_metadata_only_evidence_rows": sum(1 for e in evidence if isinstance(e.get("raw_evidence"), dict) and not isinstance((e.get("raw_evidence") or {}).get("source_result"), dict)),
        "evidence_rows_with_source_url": sum(1 for e in evidence if _normalize_value(e.get("source_url"))),
        "evidence_rows_with_source_title": sum(1 for e in evidence if _normalize_value(e.get("source_title"))),
        "evidence_rows_with_source_content": sum(1 for e in evidence if _text_has_tag(e, "Snippet")),
        "evidence_rows_with_raw_source_payload": sum(1 for e in evidence if isinstance((e.get("raw_evidence") or {}).get("source_result"), dict) and bool((e.get("raw_evidence") or {}).get("source_result"))),
        "evidence_rows_without_source_payload": sum(1 for e in evidence if not isinstance((e.get("raw_evidence") or {}).get("source_result"), dict)),
        "sample_source_result_keys": [sorted(list(((e.get("raw_evidence") or {}).get("source_result") or {}).keys()))[:20] if isinstance((e.get("raw_evidence") or {}).get("source_result"), dict) else [] for e in sampled_evidence],
        "sample_detected_title_fields": [extract_deterministic_title((e.get("raw_evidence") or {}).get("source_result") if isinstance(e.get("raw_evidence"), dict) else {})[1] for e in sampled_evidence],
        "sample_detected_content_fields": [extract_deterministic_snippet((e.get("raw_evidence") or {}).get("source_result") if isinstance(e.get("raw_evidence"), dict) else {})[1] for e in sampled_evidence],
        "sample_source_titles": [_normalize_value(e.get("source_title")) for e in sampled_evidence],
        "sample_source_urls": [_normalize_value(e.get("source_url")) for e in sampled_evidence],
        "sample_source_content_preview": [extract_deterministic_snippet((e.get("raw_evidence") or {}).get("source_result") if isinstance(e.get("raw_evidence"), dict) else {})[0][:120] for e in sampled_evidence],
        "sample_enriched_evidence_text": [_normalize_value(e.get("evidence_text"))[:240] for e in sampled_evidence],
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
