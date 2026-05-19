from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_query_interface import run_governance_query_interface
from transmission_layers.asset_discovery.tier3h5.governance_query_interface.deterministic_query_engine import execute_queries
from transmission_layers.asset_discovery.tier3h5.governance_query_interface.query_catalog import build_query_catalog
from transmission_layers.asset_discovery.tier3h5.governance_query_interface.query_context import load_query_context


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_phase5h_inputs() -> None:
    _write("logs/tier3h5_governance_graph_node_inventory.json", {"nodes": [{"node_id": "phase5a"}, {"node_id": "artifact:a"}, {"node_id": "invariant:x"}]})
    _write("logs/tier3h5_governance_graph_edge_inventory.json", {"edges": [{"from_node_id": "phase5a", "to_node_id": "phase5b", "edge_type": "phase_depends_on_phase"}, {"from_node_id": "artifact:a", "to_node_id": "invariant:x", "edge_type": "artifact_verifies_invariant"}]})
    _write("logs/tier3h5_invariant_dependency_surface.json", {"invariants": [{"invariant_id": "invariant:x"}]})
    _write("logs/tier3h5_governance_coverage_graph_export.json", {"phases": [{"phase": "phase5a"}], "phase_artifacts": [{"phase": "phase5a", "artifact": "artifact:a"}]})
    _write("logs/tier3h5_governance_traversal_surfaces.json", {"lineage_paths": [{"from": "phase5a", "to": "phase5b"}]})
    _write("logs/tier3h5_governance_reachability_summary.json", {"records": [{"node_id": "phase5a"}]})
    _write("logs/tier3h5_phase5h_knowledge_graph_summary.json", {"ok": True})


def test_phase5i_missing_optional_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_governance_query_interface()
    assert out["query_interface_run_status"] == "success"


def test_query_catalog_deterministic_and_exact_types(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    a = build_query_catalog()
    b = build_query_catalog()
    assert a == b
    assert a["exact_query_type_matching_only"] is True


def test_invalid_query_type_and_exact_lookup_and_bounded_traversal(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5h_inputs()
    ctx = load_query_context()
    results = execute_queries(ctx, [
        {"query_type": "invalid", "params": {}},
        {"query_type": "inspect_artifact", "params": {"artifact_id": "artifact:a"}},
        {"query_type": "inspect_artifact", "params": {"artifact_id": "artifact"}},
        {"query_type": "list_lineage_paths", "params": {}},
    ])
    assert results["results"][0]["status"] == "invalid_query_type"
    assert results["results"][1]["result"] == "artifact:a"
    assert results["results"][2]["result"] is None
    assert results["max_traversal_depth"] == 2


def test_no_fuzzy_or_semantic_matching_and_summary_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5h_inputs()
    out = run_governance_query_interface()
    assert out["governance_invariants"]["semantic_querying_absent"] is True
    assert out["governance_invariants"]["fuzzy_matching_absent"] is True
    assert out["governance_invariants"]["llm_driven_query_answering_absent"] is True
    assert out["governance_invariants"]["tier3h4_freeze_boundary_preserved"] is True


def test_outputs_and_regression_guards(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5h_inputs()
    out = run_governance_query_interface()
    assert out["governance_invariants"]["advisory_only_governance_verified"] is True
    assert out["governance_invariants"]["ci_failure_required"] is False
    for p in [
        "logs/tier3h5_query_interface_context.json",
        "logs/tier3h5_governance_query_catalog.json",
        "logs/tier3h5_governance_query_results.json",
        "logs/tier3h5_operator_inspection_surfaces.json",
        "logs/tier3h5_invariant_inspection_summary.json",
        "logs/tier3h5_artifact_inspection_summary.json",
        "logs/tier3h5_phase_inspection_summary.json",
        "logs/tier3h5_lineage_inspection_summary.json",
        "logs/tier3h5_phase5i_query_interface_summary.json",
    ]:
        assert Path(p).exists()
