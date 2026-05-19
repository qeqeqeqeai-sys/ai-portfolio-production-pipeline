from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_knowledge_graph import run_governance_knowledge_graph
from transmission_layers.asset_discovery.tier3h5.governance_knowledge_graph.graph_surface_builder import ALLOWED_EDGE_TYPES


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_minimum_inputs() -> None:
    _write("logs/tier3h5_phase5a_orchestration_summary.json", {"ok": True})
    _write("logs/tier3h5_governance_invariant_registry.json", {"advisory_only": True})
    _write("logs/tier3h5_governance_lineage_manifest.json", {"items": []})


def test_missing_optional_inputs_handled(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_governance_knowledge_graph()
    assert out["knowledge_graph_run_status"] == "success"


def test_deterministic_generation_and_replay_safe(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_minimum_inputs()
    a = run_governance_knowledge_graph()
    b = run_governance_knowledge_graph()
    assert a["graph_nodes_generated"] == b["graph_nodes_generated"]
    manifest = json.loads(Path("logs/tier3h5_governance_knowledge_graph_manifest.json").read_text())
    assert manifest["governance_graph_replayable"] is True


def test_edge_types_and_no_semantic_fuzzy_inference(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_minimum_inputs()
    run_governance_knowledge_graph()
    edges = json.loads(Path("logs/tier3h5_governance_graph_edge_inventory.json").read_text())["edges"]
    assert all(e["edge_type"] in ALLOWED_EDGE_TYPES for e in edges)
    out = json.loads(Path("logs/tier3h5_phase5h_knowledge_graph_summary.json").read_text())
    assert out["semantic_inference_absent"] is True
    assert out["fuzzy_matching_absent"] is True


def test_traversal_invariant_reachability_and_boundaries(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_minimum_inputs()
    out = run_governance_knowledge_graph()
    traversal = json.loads(Path("logs/tier3h5_governance_traversal_surfaces.json").read_text())
    invariant = json.loads(Path("logs/tier3h5_invariant_dependency_surface.json").read_text())
    reachability = json.loads(Path("logs/tier3h5_governance_reachability_summary.json").read_text())
    assert traversal["max_depth"] == 2
    assert traversal["exact_match_only"] is True
    assert invariant["advisory_only_governance_verified"] is True
    assert out["tier3h4_freeze_boundary_preserved"] is True
    assert reachability["reachability_records_generated"] >= 1


def test_outputs_present_and_regression_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_minimum_inputs()
    out = run_governance_knowledge_graph()
    assert out["advisory_only_governance_verified"] is True
    assert out["ci_failure_required"] is False
    for path in [
        "logs/tier3h5_knowledge_graph_context.json",
        "logs/tier3h5_governance_knowledge_graph_manifest.json",
        "logs/tier3h5_governance_graph_node_inventory.json",
        "logs/tier3h5_governance_graph_edge_inventory.json",
        "logs/tier3h5_governance_traversal_surfaces.json",
        "logs/tier3h5_invariant_dependency_surface.json",
        "logs/tier3h5_governance_reachability_summary.json",
        "logs/tier3h5_governance_coverage_graph_export.json",
        "logs/tier3h5_phase5h_knowledge_graph_summary.json",
    ]:
        assert Path(path).exists()
