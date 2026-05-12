from typing import Dict, List, Any


def validate_graph_rows(nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors = []
    warnings = []

    node_keys = {node.get("node_key") for node in nodes}

    if not nodes:
        errors.append("No graph nodes produced.")

    if not edges:
        errors.append("No graph edges produced.")

    for node in nodes:
        if not node.get("node_key"):
            errors.append("Node missing node_key.")
        if not node.get("node_type"):
            errors.append(f"Node missing node_type: {node}")
        if not node.get("node_label"):
            errors.append(f"Node missing node_label: {node}")

    for edge in edges:
        source_key = edge.get("source_node_key")
        target_key = edge.get("target_node_key")

        if not edge.get("edge_key"):
            errors.append("Edge missing edge_key.")

        if source_key not in node_keys:
            errors.append(f"Edge source_node_key not found in nodes: {source_key}")

        if target_key not in node_keys:
            errors.append(f"Edge target_node_key not found in nodes: {target_key}")

        if source_key == target_key:
            warnings.append(f"Self-edge detected: {edge.get('edge_key')}")

        for metric in [
            "edge_strength",
            "confidence_score",
            "evidence_intensity",
            "persistence_score",
        ]:
            value = float(edge.get(metric, 0))
            if value < 0 or value > 1:
                errors.append(f"{metric} out of range for edge {edge.get('edge_key')}: {value}")

        directional_strength = float(edge.get("directional_strength", 0))
        if directional_strength < -1 or directional_strength > 1:
            errors.append(
                f"directional_strength out of range for edge {edge.get('edge_key')}: {directional_strength}"
            )

    validation_status = "passed"
    if errors:
        validation_status = "failed"
    elif warnings:
        validation_status = "warning"

    return {
        "validation_status": validation_status,
        "errors": errors,
        "warnings": warnings,
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
