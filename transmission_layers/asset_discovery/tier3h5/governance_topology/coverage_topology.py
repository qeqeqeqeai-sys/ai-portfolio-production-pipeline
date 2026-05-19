from __future__ import annotations


def build_coverage_topology(context: dict[str, object]) -> dict[str, object]:
    covered = [k for k, v in context["phase_coverage"].items() if v]
    uncovered = [k for k, v in context["phase_coverage"].items() if not v]
    return {
        "coverage_topology_status": "generated",
        "covered_phases": sorted(covered),
        "uncovered_phases": sorted(uncovered),
        "coverage_ratio": f"{len(covered)}/{len(context['phase_coverage'])}",
    }
