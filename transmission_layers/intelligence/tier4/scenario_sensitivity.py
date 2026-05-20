from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List

from .scenario_semantics import clamp_score


def _checksum(payload: Dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def compute_node_sensitivity(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    baseline_nodes = {str(x) for x in baseline.get("stressed_nodes", [])}
    candidate_nodes = {str(x) for x in candidate.get("stressed_nodes", [])}
    nodes = sorted(baseline_nodes | candidate_nodes)
    out = []
    for nid in nodes:
        b = 1.0 if nid in baseline_nodes else 0.0
        c = 1.0 if nid in candidate_nodes else 0.0
        out.append({"node_id": nid, "sensitivity_score": clamp_score(abs(c - b))})
    return sorted(out, key=lambda x: (-x["sensitivity_score"], x["node_id"]))


def compute_corridor_sensitivity(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> List[Dict[str, Any]]:
    b = sorted({str(x) for x in (baseline.get("degraded_corridors", []) + baseline.get("suppressed_corridors", []) + baseline.get("failed_corridors", []))})
    c = sorted({str(x) for x in (candidate.get("degraded_corridors", []) + candidate.get("suppressed_corridors", []) + candidate.get("failed_corridors", []))})
    corridors = sorted(set(b + c))
    out = []
    for cid in corridors:
        out.append({"corridor_id": cid, "sensitivity_score": clamp_score(abs((1.0 if cid in c else 0.0) - (1.0 if cid in b else 0.0)))})
    return sorted(out, key=lambda x: (-x["sensitivity_score"], x["corridor_id"]))


def compute_structural_sensitivity_summary(baseline: Dict[str, Any], candidate: Dict[str, Any]) -> Dict[str, Any]:
    nodes = compute_node_sensitivity(baseline, candidate)
    corridors = compute_corridor_sensitivity(baseline, candidate)
    ns = nodes[0]["sensitivity_score"] if nodes else 0.0
    cs = corridors[0]["sensitivity_score"] if corridors else 0.0
    out = {
        "sensitive_nodes": [n["node_id"] for n in nodes if n["sensitivity_score"] > 0.0],
        "sensitive_corridors": [c["corridor_id"] for c in corridors if c["sensitivity_score"] > 0.0],
        "dominant_sensitivity_factor": "nodes" if ns >= cs else "corridors",
        "sensitivity_score": clamp_score(max(ns, cs)),
    }
    out["sensitivity_checksum"] = _checksum(out)
    return out
