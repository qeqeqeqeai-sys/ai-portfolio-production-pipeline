from __future__ import annotations

from typing import Any

from .federation_common import clamp_score
from .federation_observability_signatures import observability_checksum


def federation_lineage_diagnostics(dependencies: list[dict[str, Any]], replay_snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    dep_pairs = sorted((str(d.get("source", "")), str(d.get("target", ""))) for d in dependencies)
    unique_ratio = (len(set(dep_pairs)) / len(dep_pairs)) if dep_pairs else 0.0
    chron_ids = [str(s.get("snapshot_id", "")) for s in replay_snapshots]
    chronology = 1.0 if chron_ids == sorted(chron_ids) else 0.0
    score = clamp_score((unique_ratio + chronology) / 2.0)
    result = {"federation_lineage_score": score}
    result["federation_lineage_checksum"] = observability_checksum(result, "tier5e_lineage")
    return result
