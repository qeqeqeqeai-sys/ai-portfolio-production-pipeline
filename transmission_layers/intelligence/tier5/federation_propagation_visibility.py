from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_propagation_visibility_diagnostics(contagion_paths: list[dict[str, Any]]) -> dict[str, Any]:
    ordered = sorted(contagion_paths, key=lambda p: (str(p.get("source", "")), str(p.get("target", "")), str(p.get("path_id", ""))))
    contained = sum(1 for p in ordered if bool(p.get("contained", False)))
    score = clamp_score((contained / len(ordered)) if ordered else 0.0)
    result = {"federation_propagation_visibility_score": score}
    result["federation_propagation_visibility_checksum"] = observability_checksum(result, "tier5e_propagation_visibility")
    return result
