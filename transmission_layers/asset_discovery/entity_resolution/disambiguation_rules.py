from __future__ import annotations
from .confidence_scoring import status_from_score


def apply_rules(flags: dict, score: int) -> tuple[list[str], str | None, str]:
    rules: list[str] = []
    suppression_reason = None
    status = status_from_score(score)
    if flags.get("generic_name"):
        rules.append("generic_name")
        suppression_reason = suppression_reason or "generic_name"
        status = "suppressed"
    if flags.get("suspicious_ticker"):
        rules.append("suspicious_ticker")
        suppression_reason = suppression_reason or "suspicious_ticker"
        status = "suppressed"
    if flags.get("etf_company_conflict"):
        rules.append("etf_company_conflict")
        suppression_reason = suppression_reason or "etf_company_conflict"
        status = "suppressed"
    if flags.get("source_count", 0) == 0:
        rules.append("zero_evidence_sources")
        if status.startswith("resolved"):
            status = "unresolved_review"
    if flags.get("missing_exchange_for_ambiguous"):
        rules.append("missing_exchange_for_ambiguous_ticker")
        if status == "resolved_high_confidence":
            status = "resolved_medium_confidence"
    if flags.get("missing_ticker"):
        rules.append("missing_ticker")
    return rules, suppression_reason, status
