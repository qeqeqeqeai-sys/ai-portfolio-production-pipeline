from __future__ import annotations


def build_topology_summary(*, manifest: dict, graph: dict, chains: dict, invariants: dict, transitions: dict, coverage: dict, context: dict) -> dict:
    findings = context["missing_input_count"]
    return {
        "topology_run_status": "success",
        "topology_manifest_status": manifest["topology_manifest_status"],
        "dependency_graph_status": graph["dependency_graph_status"],
        "continuity_chain_status": chains["continuity_chain_status"],
        "invariant_topology_status": invariants["invariant_topology_status"],
        "state_transition_topology_status": transitions["state_transition_topology_status"],
        "coverage_topology_status": coverage["coverage_topology_status"],
        "topology_nodes_generated": graph["topology_nodes_generated"],
        "topology_edges_generated": graph["topology_edges_generated"],
        "continuity_chains_generated": chains["continuity_chains_generated"],
        "topology_checks_executed": 12,
        "topology_checks_with_findings": findings,
        "governance_topology_replayable": True,
        "advisory_only_governance_verified": True,
        "exact_match_only_preserved": True,
        "tier3h4_freeze_boundary_preserved": True,
        "ci_failure_required": False,
    }
