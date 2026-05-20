from __future__ import annotations
from .cascade_signatures import compute_cascade_boundary_checksum

def _bound01(v: float) -> float:
    return max(0.0, min(1.0, round(float(v), 6)))

def score_cascade_boundaries(suppressed_ratio: float, failed_ratio: float, systemic_score: float) -> dict:
    boundary = _bound01(0.45 * suppressed_ratio + 0.35 * failed_ratio + 0.2 * systemic_score)
    out = {
        "cascade_boundary_weakness_score": boundary,
        "local_to_systemic_destabilization_score": _bound01(0.6 * boundary + 0.4 * systemic_score),
        "survivability_continuity_score": _bound01(1.0 - boundary),
    }
    out["cascade_boundary_checksum"] = compute_cascade_boundary_checksum(out)
    return out
