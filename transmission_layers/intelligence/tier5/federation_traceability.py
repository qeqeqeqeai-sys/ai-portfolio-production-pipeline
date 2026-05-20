from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_traceability_diagnostics(contagion_paths: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(contagion_paths, key=lambda p: str(p.get("path_id", "")))
    complete = sum(1 for p in ordered if p.get("source") and p.get("target") and p.get("path_id"))
    score = clamp_score((complete / len(ordered)) if ordered else 0.0)
    result = {"federation_traceability_score": score}
    result["federation_traceability_checksum"] = observability_checksum(result, "tier5e_traceability")
    return result
