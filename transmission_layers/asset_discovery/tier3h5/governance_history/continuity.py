from __future__ import annotations

from collections import Counter
from typing import Any

from .hashing import stable_hash

HIGH_SEVERITY = {"governance_risk", "governance_review_recommended", "critical_governance_instability"}


def classify_historical_continuity(incident_history: list[dict[str, Any]]) -> dict[str, Any]:
    entries = [e for e in incident_history if isinstance(e, dict)]
    depth = len(entries)
    if depth < 2:
        status = "insufficient_governance_history"
    else:
        keys = [str(e.get("incident_key") or e.get("category")) for e in entries]
        counts = Counter(keys)
        high = [e for e in entries if e.get("severity") in HIGH_SEVERITY]
        if high and len(high) == depth:
            status = "persistent_governance_risk"
        elif any(v >= 2 for v in counts.values()):
            status = "recurring_governance_risk"
        elif high and entries[-1].get("severity") not in HIGH_SEVERITY:
            status = "stabilizing_governance_risk"
        elif high:
            status = "unresolved_governance_risk"
        else:
            status = "transient_governance_risk"
    out = {
        "historical_continuity_status": status,
        "governance_history_depth": depth,
        "persistent_incident_count": sum(1 for _, v in Counter(str(e.get("incident_key") or e.get("category")) for e in entries).items() if v >= 2),
        "recurring_incident_count": sum(v for v in Counter(str(e.get("incident_key") or e.get("category")) for e in entries).values() if v >= 2),
        "transient_incident_count": sum(1 for e in entries if e.get("severity") not in HIGH_SEVERITY),
        "replay_mode": "advisory_only",
        "enforcement_enabled": False,
    }
    out["continuity_hash"] = stable_hash(out)
    return out
