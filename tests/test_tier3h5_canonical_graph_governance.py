import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.canonical_graph_governance import govern_canonical_graph_edges


def test_security_level_canonical_node_identity_preferred() -> None:
    out = govern_canonical_graph_edges(
        nodes=[{"candidate_asset_id": "a", "canonical_security_id": "sec_a", "canonical_issuer_id": "iss_a", "registry_resolution_status": "accepted"}],
        edges=[],
    )
    node = out["nodes"][0]
    assert node["canonical_graph_node_id"] == "CANONICAL_SECURITY::sec_a"
    assert node["graph_identity_mode"] == "canonical_registry_security"


def test_issuer_level_used_when_security_unavailable() -> None:
    out = govern_canonical_graph_edges(nodes=[{"candidate_asset_id": "i", "canonical_issuer_id": "iss_i", "registry_resolution_status": "accepted"}], edges=[])
    assert out["nodes"][0]["canonical_graph_node_id"] == "CANONICAL_ISSUER::iss_i"
    assert out["nodes"][0]["graph_identity_mode"] == "canonical_registry_issuer"


def test_legacy_preserved_when_canonical_unavailable() -> None:
    out = govern_canonical_graph_edges(nodes=[{"candidate_asset_id": "legacy"}], edges=[])
    assert out["nodes"][0]["canonical_graph_node_id"] == "legacy"
    assert out["nodes"][0]["graph_identity_mode"] == "legacy_candidate_asset_id"


def test_canonical_edge_id_deterministic() -> None:
    nodes = [
        {"candidate_asset_id": "a", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sa", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "b", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sb", "registry_resolution_status": "accepted"},
    ]
    edges = [{"source_asset_id": "a", "target_asset_id": "b"}]
    assert govern_canonical_graph_edges(nodes, edges) == govern_canonical_graph_edges(nodes, edges)


def test_duplicate_legacy_edges_mapping_to_same_canonical_collapsed_deterministically() -> None:
    nodes = [
        {"candidate_asset_id": "a1", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sa", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "a2", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sa", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "b", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sb", "registry_resolution_status": "accepted"},
    ]
    edges = [{"source_asset_id": "a1", "target_asset_id": "b"}, {"source_asset_id": "a2", "target_asset_id": "b"}]
    out = govern_canonical_graph_edges(nodes, edges, collapse_duplicates=True)
    assert len(out["edges"]) == 1
    assert out["diagnostics"]["duplicate_canonical_edges_collapsed"] == 1


def test_canonicalization_created_self_loop_prevented() -> None:
    nodes = [
        {"candidate_asset_id": "a1", "canonical_propagation_asset_id": "CANONICAL_ISSUER::iss_a", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "a2", "canonical_propagation_asset_id": "CANONICAL_ISSUER::iss_a", "registry_resolution_status": "accepted"},
    ]
    out = govern_canonical_graph_edges(nodes, [{"source_asset_id": "a1", "target_asset_id": "a2"}])
    assert out["edges"][0]["edge_governance_status"] == "self_loop_prevented"


def test_conflict_registry_status_preserves_legacy_edge() -> None:
    nodes = [{"candidate_asset_id": "a", "registry_resolution_status": "conflict"}, {"candidate_asset_id": "b", "registry_resolution_status": "accepted"}]
    out = govern_canonical_graph_edges(nodes, [{"source_asset_id": "a", "target_asset_id": "b"}])
    assert out["edges"][0]["edge_governance_status"] == "conflict_preserved_legacy"


def test_invalid_input_preserves_legacy_edge_identity() -> None:
    nodes = [{"candidate_asset_id": "a", "registry_resolution_status": "invalid_input"}, {"candidate_asset_id": "b", "registry_resolution_status": "accepted"}]
    out = govern_canonical_graph_edges(nodes, [{"source_asset_id": "a", "target_asset_id": "b"}])
    assert out["edges"][0]["edge_governance_status"] == "invalid_input_preserved_legacy"


def test_diagnostics_counters_are_deterministic() -> None:
    nodes = [{"candidate_asset_id": "a", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sa", "registry_resolution_status": "accepted"}, {"candidate_asset_id": "b"}]
    edges = [{"source_asset_id": "a", "target_asset_id": "b"}]
    a = govern_canonical_graph_edges(nodes, edges)
    b = govern_canonical_graph_edges(nodes, edges)
    assert a["diagnostics"] == b["diagnostics"]


def test_mixed_canonical_and_legacy_edge_behavior_safe() -> None:
    nodes = [
        {"candidate_asset_id": "a", "canonical_propagation_asset_id": "CANONICAL_SECURITY::sa", "registry_resolution_status": "accepted"},
        {"candidate_asset_id": "b"},
    ]
    out = govern_canonical_graph_edges(nodes, [{"source_asset_id": "a", "target_asset_id": "b"}])
    edge = out["edges"][0]
    assert edge["graph_identity_mode"] == "canonical_mixed"
    assert edge["edge_governance_status"] == "canonical_edge_accepted"
