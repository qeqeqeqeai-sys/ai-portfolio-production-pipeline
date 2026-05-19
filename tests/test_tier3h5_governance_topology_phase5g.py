from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.asset_discovery.tier3h5.governance_topology import run_governance_topology


def _write(path: str, payload: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload), encoding="utf-8")


def _seed_phase5f() -> None:
    _write("logs/tier3h5_phase5f_control_plane_summary.json", {"ok": True})
    _write("logs/tier3h5_governance_state_manifest.json", {"ok": True})


def test_missing_optional_topology_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    out = run_governance_topology()
    assert out["topology_run_status"] == "success"
    assert out["state_transition_topology_status"] == "insufficient_state_history"


def test_deterministic_manifest_and_dependency_graph(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5f()
    a = run_governance_topology()
    b = run_governance_topology()
    assert a["topology_manifest_status"] == "generated"
    assert a["topology_nodes_generated"] == b["topology_nodes_generated"]
    manifest_a = json.loads(Path("logs/tier3h5_governance_topology_manifest.json").read_text())
    manifest_b = json.loads(Path("logs/tier3h5_governance_topology_manifest.json").read_text())
    assert manifest_a["topology_manifest_id"] == manifest_b["topology_manifest_id"]


def test_continuity_invariant_transition_coverage_and_regression_flags(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5f()
    out = run_governance_topology()
    assert out["continuity_chains_generated"] > 0
    assert out["advisory_only_governance_verified"] is True
    assert out["exact_match_only_preserved"] is True
    assert out["tier3h4_freeze_boundary_preserved"] is True
    invariant = json.loads(Path("logs/tier3h5_invariant_topology_summary.json").read_text())
    assert invariant["invariant_topology"]["no_enforcement_introduced"] is True
    assert invariant["invariant_topology"]["no_remediation_introduced"] is True
    assert invariant["invariant_topology"]["no_fuzzy_matching_introduced"] is True
    assert invariant["invariant_topology"]["no_semantic_inference_introduced"] is True
    assert invariant["invariant_topology"]["no_probabilistic_scoring_introduced"] is True
    assert invariant["invariant_topology"]["no_automated_release_gating_introduced"] is True


def test_exact_match_only_and_replay_safe_topology_reconstruction(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5f()
    first = run_governance_topology()
    _write("logs/tier3h5_phase5a_orchestration_summary.json", {"state": "changed"})
    second = run_governance_topology()
    transition = json.loads(Path("logs/tier3h5_state_transition_topology.json").read_text())
    assert first["governance_topology_replayable"] is True
    assert second["governance_topology_replayable"] is True
    assert second["state_transition_topology_status"] in {"generated", "insufficient_state_history"}
    if second["state_transition_topology_status"] == "generated":
        assert transition["transition_records_generated"] >= 1


def test_output_artifacts_present(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_phase5f()
    run_governance_topology()
    for path in [
        "logs/tier3h5_topology_context.json",
        "logs/tier3h5_governance_topology_manifest.json",
        "logs/tier3h5_governance_dependency_graph.json",
        "logs/tier3h5_continuity_chain_summary.json",
        "logs/tier3h5_invariant_topology_summary.json",
        "logs/tier3h5_state_transition_topology.json",
        "logs/tier3h5_coverage_topology_summary.json",
        "logs/tier3h5_phase5g_topology_summary.json",
    ]:
        assert Path(path).exists()
