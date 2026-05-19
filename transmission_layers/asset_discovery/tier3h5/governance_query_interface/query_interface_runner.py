from __future__ import annotations

from pathlib import Path
from typing import Any

from .artifact_inspection import build_artifact_inspection
from .deterministic_query_engine import execute_queries
from .invariant_inspection import build_invariant_inspection
from .lineage_inspection import build_lineage_inspection
from .operator_inspection_surfaces import build_operator_inspection_surfaces
from .phase_inspection import build_phase_inspection
from .query_catalog import QUERY_TYPES, build_query_catalog
from .query_context import load_query_context, stable_json_dumps
from .query_interface_summary import build_query_interface_summary


def _write(path: str, payload: dict[str, Any]) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(stable_json_dumps(payload), encoding="utf-8")


def run_governance_query_interface() -> dict[str, Any]:
    context = load_query_context()
    catalog = build_query_catalog()
    default_queries = [{"query_type": qt, "params": {}} for qt in QUERY_TYPES]
    results = execute_queries(context, default_queries)
    inspection = build_operator_inspection_surfaces(context, results)
    invariant = build_invariant_inspection(results)
    artifact = build_artifact_inspection(results)
    phase = build_phase_inspection(results)
    lineage = build_lineage_inspection(results)
    summary = build_query_interface_summary(catalog, results, inspection, invariant, artifact, phase, lineage)

    _write("logs/tier3h5_query_interface_context.json", context)
    _write("logs/tier3h5_governance_query_catalog.json", catalog)
    _write("logs/tier3h5_governance_query_results.json", results)
    _write("logs/tier3h5_operator_inspection_surfaces.json", inspection)
    _write("logs/tier3h5_invariant_inspection_summary.json", invariant)
    _write("logs/tier3h5_artifact_inspection_summary.json", artifact)
    _write("logs/tier3h5_phase_inspection_summary.json", phase)
    _write("logs/tier3h5_lineage_inspection_summary.json", lineage)
    _write("logs/tier3h5_phase5i_query_interface_summary.json", summary)
    return summary
