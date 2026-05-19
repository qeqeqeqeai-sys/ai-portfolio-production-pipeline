from __future__ import annotations

from typing import Any


def build_coverage_graph_export(context: dict[str, Any]) -> dict[str, Any]:
    return {
        "phase_coverage": context["phase_coverage"],
        "artifact_coverage": context["artifact_coverage"],
        "covered_phase_count": sum(1 for v in context["phase_coverage"].values() if v),
        "total_phase_count": len(context["phase_coverage"]),
    }
