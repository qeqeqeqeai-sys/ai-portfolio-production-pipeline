from __future__ import annotations


def compute_confidence(flags: dict) -> int:
    score = 0
    score += 25 if flags.get("has_ticker") else -20
    score += 15 if flags.get("has_exchange") else -10
    score += 15 if flags.get("has_name") else 0
    score += 10 if flags.get("asset_type_known") else 0
    score += 10 if flags.get("source_count", 0) >= 2 else 0
    score += 10 if flags.get("has_evidence_urls") else 0
    score -= 40 if flags.get("etf_company_conflict") else 0
    score -= 30 if flags.get("suspicious_ticker") else 0
    score -= 35 if flags.get("generic_name") else 0
    return max(0, min(100, int(score)))


def status_from_score(score: int) -> str:
    if score >= 80:
        return "resolved_high_confidence"
    if score >= 60:
        return "resolved_medium_confidence"
    if score >= 40:
        return "unresolved_review"
    return "suppressed"
