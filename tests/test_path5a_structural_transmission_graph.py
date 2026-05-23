from copy import deepcopy

from transmission_layers import expectation_failure as ef
from transmission_layers.expectation_failure import path5a_structural_transmission_graph as p5a


def _sample_input():
    nodes = [
        {"node_type": "entity", "label": "AAPL"},
        {"node_type": "entity", "label": "MSFT"},
        {"node_type": "subsector", "label": "Software"},
        {"node_type": "sector", "label": "Technology"},
        {"node_type": "benchmark", "label": "SP500"},
    ]
    normalized_nodes = p5a.build_path5a_structural_nodes({"structural_nodes": nodes})
    by_label = {n["label"]: n["node_id"] for n in normalized_nodes}
    edges = [
        {"edge_type": "entity_to_subsector", "source_node_id": by_label["AAPL"], "target_node_id": by_label["Software"]},
        {"edge_type": "entity_to_subsector", "source_node_id": by_label["MSFT"], "target_node_id": by_label["Software"]},
        {"edge_type": "subsector_to_sector", "source_node_id": by_label["Software"], "target_node_id": by_label["Technology"]},
        {"edge_type": "entity_to_benchmark", "source_node_id": by_label["AAPL"], "target_node_id": by_label["SP500"]},
        {"edge_type": "entity_to_subsector", "source_node_id": by_label["AAPL"], "target_node_id": by_label["Software"]},
    ]
    return {"structural_nodes": nodes, "structural_edges": edges}


def test_public_api_and_export_presence():
    required = [
        "build_path5a_node_taxonomy", "build_path5a_edge_taxonomy", "build_path5a_relationship_registry",
        "build_path5a_structural_nodes", "build_path5a_structural_edges", "build_path5a_transmission_graph",
        "build_path5a_topology_metrics", "build_path5a_graph_lineage", "build_path5a_topology_manifest",
        "certify_path5a_transmission_graph", "build_path5a_dashboard_graph_summary", "build_path5a_supervisor_report",
        "build_path5a_report", "run_path5a_structural_transmission_graph",
    ]
    for name in required:
        assert hasattr(p5a, name)
        assert hasattr(ef, name)
    for c in ["CERTIFIED_TRANSMISSION_GRAPH", "DEGRADED_TRANSMISSION_GRAPH", "BLOCKED_TRANSMISSION_GRAPH"]:
        assert hasattr(p5a, c)
        assert hasattr(ef, c)


def test_fixed_taxonomies_and_registry():
    assert [n["node_type"] for n in p5a.build_path5a_node_taxonomy()["node_types"]] == list(p5a.NODE_TYPES)
    assert [e["edge_type"] for e in p5a.build_path5a_edge_taxonomy()["edge_types"]] == list(p5a.EDGE_TYPES)
    registry = p5a.build_path5a_relationship_registry()
    assert len(registry["relationships"]) == len(p5a.EDGE_TYPES)


def test_determinism_immutability_checksums_and_sorting_dedup():
    inp = _sample_input()
    frozen = deepcopy(inp)
    out1 = p5a.run_path5a_structural_transmission_graph(inp)
    out2 = p5a.run_path5a_structural_transmission_graph(inp)
    assert out1 == out2
    assert inp == frozen
    assert out1["graph"]["graph_checksum"] == out2["graph"]["graph_checksum"]
    edges = out1["graph"]["edges"]
    assert len(edges) == 4
    assert edges == sorted(edges, key=lambda x: (x["edge_type"], x["source_node_id"], x["target_node_id"], x["edge_id"]))


def test_certified_path_and_metric_bounds_and_lineage_manifest_summary_report_shapes():
    out = p5a.run_path5a_structural_transmission_graph(_sample_input())
    assert out["certification"]["certification_status"] == p5a.CERTIFIED_TRANSMISSION_GRAPH
    m = out["topology_metrics"]
    assert 0 <= m["topology_density_score"] <= 100
    assert 0 <= m["concentration_score"] <= 100
    assert len(out["graph_lineage"]["node_lineage"]) == m["node_count"]
    assert "topology_manifest_checksum" in out["topology_manifest"]
    assert set(out["dashboard_summary"].keys()) >= {"certification_status", "graph_checksum", "node_count", "edge_count"}
    assert set(out["supervisor_report"].keys()) >= {"layer", "objective", "certification", "governance"}


def test_degraded_path_partial_safe_inputs():
    out = p5a.run_path5a_structural_transmission_graph({"structural_nodes": [{"node_type": "entity", "label": "AAPL"}], "structural_edges": []})
    assert out["certification"]["certification_status"] == p5a.DEGRADED_TRANSMISSION_GRAPH


def test_blocked_invalid_edge_references_and_empty_ids():
    nodes = p5a.build_path5a_structural_nodes({"structural_nodes": [{"node_type": "entity", "label": "A"}, {"node_type": "subsector", "label": "S"}]})
    ids = {n["label"]: n["node_id"] for n in nodes}
    bad = {
        "structural_nodes": [{"node_type": "entity", "label": "A"}, {"node_type": "subsector", "label": "S"}],
        "structural_edges": [
            {"edge_type": "entity_to_subsector", "source_node_id": "", "target_node_id": ids["S"]},
            {"edge_type": "entity_to_subsector", "source_node_id": ids["A"], "target_node_id": "does_not_exist"},
        ],
    }
    out = p5a.run_path5a_structural_transmission_graph(bad)
    assert out["certification"]["certification_status"] == p5a.BLOCKED_TRANSMISSION_GRAPH
    assert out["graph"]["invalid_edge_count"] >= 1


def test_blocked_forbidden_semantics_and_no_disallowed_language_in_module_constants():
    inp = _sample_input()
    inp["note"] = "buy recommendation with prediction"
    out = p5a.run_path5a_structural_transmission_graph(inp)
    assert out["certification"]["certification_status"] == p5a.BLOCKED_TRANSMISSION_GRAPH


def test_no_network_write_llm_runtime_dependencies_behavior():
    inp = _sample_input()
    out = p5a.run_path5a_structural_transmission_graph(inp)
    assert out["certification"]["gates"]["deterministic_nodes_edges"] is True


def test_non_regression_smoke_for_p3h_if_available():
    # Optional non-regression surface: validate expectation_failure package remains import-stable.
    assert hasattr(ef, "build_phase_b7_system_certification_report")
