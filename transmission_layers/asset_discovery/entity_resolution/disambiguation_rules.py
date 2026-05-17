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
        if flags.get("has_ticker"):
            status = "unresolved_review"
        elif status.startswith("resolved"):
            status = "unresolved_review"

    if flags.get("missing_exchange_without_registry"):
        rules.append("missing_exchange_without_registry")
        if flags.get("has_ticker") and not flags.get("registry_ticker_match"):
            status = "unresolved_review"

    if flags.get("exchange_inferred_from_registry"):
        rules.append("exchange_inferred_from_registry")

    if flags.get("missing_ticker"):
        rules.append("missing_ticker")
    return rules, suppression_reason, status
