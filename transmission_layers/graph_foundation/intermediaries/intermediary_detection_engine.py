"""
Phase 5A.2 — Structural Intermediary Formation
Revised intermediary_detection_engine.py

Key Fix:
- Removed duplicate `headers=headers` injections when calling
  shared Supabase helper utilities.

This version assumes your shared helper already injects:
- apikey
- Authorization
- Content-Type

Compatible with:
- semantic-key graph architecture
- replay-safe regeneration
- GitHub Actions
- Supabase REST
"""

from __future__ import annotations

import os
import re
import json
import hashlib
from datetime import datetime, timezone
from collections import defaultdict

# ============================================================
# SHARED HELPERS
# ============================================================

try:
    from shared.supabase_rest import supabase_request
except Exception:
    # fallback local import pattern
    from transmission_layers.shared.supabase_rest import supabase_request


# ============================================================
# CONFIG
# ============================================================

EDGE_TABLE = "structural_theme_graph_edges"

INTERMEDIARY_TABLE = "structural_theme_graph_intermediaries"
INTERMEDIARY_SCORE_TABLE = "structural_theme_graph_intermediary_scores"
INTERMEDIARY_SNAPSHOT_TABLE = "structural_theme_graph_intermediary_snapshots"
INTERMEDIARY_TELEMETRY_TABLE = "structural_theme_graph_intermediary_telemetry"
INTERMEDIARY_VALIDATION_TABLE = "structural_theme_graph_intermediary_validation"

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

MIN_INBOUND = int(os.getenv("INTERMEDIARY_MIN_INBOUND", "1"))
MIN_OUTBOUND = int(os.getenv("INTERMEDIARY_MIN_OUTBOUND", "1"))


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_node_key(value: str) -> str:
    """
    Deterministic normalization for semantic graph keys.
    """

    if not value:
        return ""

    value = value.lower().strip()

    value = value.replace("-", " ")
    value = value.replace("_", " ")

    value = re.sub(r"\s+", " ", value)

    synonym_map = {
        "data centers": "data_center",
        "data center": "data_center",
        "datacenters": "data_center",
        "power grid": "power_grid",
        "power-grid": "power_grid",
    }

    value = synonym_map.get(value, value)

    value = value.replace(" ", "_")

    return value


# ============================================================
# CLASSIFICATION
# ============================================================

def classify_intermediary(node_key: str) -> str:

    node = node_key.lower()

    rules = {
        "compute": ["gpu", "compute", "server"],
        "semiconductor": ["semiconductor", "chip", "wafer"],
        "energy": ["power", "grid", "utility", "electric"],
        "infrastructure": ["data_center", "infrastructure"],
        "industrial": ["industrial", "factory"],
        "logistics": ["shipping", "logistics", "freight"],
        "supply_chain": ["supply", "materials"],
        "capital_flow": ["capital", "financing", "liquidity"],
    }

    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword in node:
                return category

    return "general"


# ============================================================
# HASH IDENTITY
# ============================================================

def stable_intermediary_hash(node_key: str) -> str:

    return hashlib.sha256(node_key.encode("utf-8")).hexdigest()


# ============================================================
# LOAD GRAPH EDGES
# ============================================================

def load_graph_edges():

    endpoint = (
        f"{EDGE_TABLE}"
        "?select=source_node_key,target_node_key"
    )

    rows = supabase_request(
        "GET",
        endpoint,
    )

    if not rows:
        return []

    return rows


# ============================================================
# DETECT INTERMEDIARIES
# ============================================================

def detect_intermediaries(edges):

    inbound_counts = defaultdict(int)
    outbound_counts = defaultdict(int)

    inbound_sources = defaultdict(set)
    outbound_targets = defaultdict(set)

    for row in edges:

        source = normalize_node_key(
            row.get("source_node_key", "")
        )

        target = normalize_node_key(
            row.get("target_node_key", "")
        )

        if not source or not target:
            continue

        outbound_counts[source] += 1
        inbound_counts[target] += 1

        outbound_targets[source].add(target)
        inbound_sources[target].add(source)

    intermediary_rows = []

    for node_key in set(list(inbound_counts.keys()) + list(outbound_counts.keys())):

        inbound = inbound_counts[node_key]
        outbound = outbound_counts[node_key]

        if inbound < MIN_INBOUND:
            continue

        if outbound < MIN_OUTBOUND:
            continue

        continuity_reuse_frequency = min(inbound, outbound)

        intermediary_score = (
            (inbound * 0.35)
            + (outbound * 0.35)
            + (continuity_reuse_frequency * 0.30)
        )

        intermediary_rows.append(
            {
                "run_id": RUN_ID,
                "node_key": node_key,
                "intermediary_hash": stable_intermediary_hash(node_key),
                "classification": classify_intermediary(node_key),
                "inbound_edge_count": inbound,
                "outbound_edge_count": outbound,
                "continuity_reuse_frequency": continuity_reuse_frequency,
                "intermediary_activation_score": round(intermediary_score, 4),
                "upstream_source_count": len(inbound_sources[node_key]),
                "downstream_target_count": len(outbound_targets[node_key]),
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    intermediary_rows = sorted(
        intermediary_rows,
        key=lambda x: x["intermediary_activation_score"],
        reverse=True
    )

    return intermediary_rows


# ============================================================
# SNAPSHOTS
# ============================================================

def persist_snapshots(rows):

    if not rows:
        return 0

    snapshot_rows = []

    for row in rows:

        snapshot_rows.append(
            {
                "run_id": RUN_ID,
                "node_key": row["node_key"],
                "snapshot_type": "daily",
                "snapshot_payload": json.dumps(row),
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    endpoint = (
        f"{INTERMEDIARY_SNAPSHOT_TABLE}"
        "?on_conflict=run_id,node_key,snapshot_type"
    )

    # FIXED:
    # removed headers=headers
    supabase_request(
        "POST",
        endpoint,
        snapshot_rows
    )

    return len(snapshot_rows)


# ============================================================
# PERSIST INTERMEDIARIES
# ============================================================

def persist_intermediaries(rows):

    if not rows:
        return 0

    endpoint = (
        f"{INTERMEDIARY_TABLE}"
        "?on_conflict=intermediary_hash"
    )

    # FIXED:
    # removed headers=headers
    supabase_request(
        "POST",
        endpoint,
        rows
    )

    return len(rows)


# ============================================================
# TELEMETRY
# ============================================================

def persist_telemetry(payload):

    endpoint = (
        f"{INTERMEDIARY_TELEMETRY_TABLE}"
        "?on_conflict=run_id"
    )

    # FIXED:
    # removed headers=headers
    supabase_request(
        "POST",
        endpoint,
        [payload]
    )


# ============================================================
# VALIDATION
# ============================================================

def persist_validation(status, message, observed_value):

    payload = {
        "run_id": RUN_ID,
        "validation_name": "intermediary_detection",
        "validation_status": status,
        "message": message,
        "observed_value": observed_value,
        "created_at": datetime.utcnow().isoformat(),
    }

    endpoint = (
        f"{INTERMEDIARY_VALIDATION_TABLE}"
        "?on_conflict=run_id,validation_name"
    )

    supabase_request(
        "POST",
        endpoint,
        [payload]
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print("=" * 80)
    print("PHASE 5A.2 — STRUCTURAL INTERMEDIARY DETECTION")
    print("=" * 80)

    edges = load_graph_edges()

    edges_loaded = len(edges)

    print(f"edges_loaded={edges_loaded}")

    intermediary_rows = detect_intermediaries(edges)

    intermediaries_detected = len(intermediary_rows)

    print(f"intermediaries_detected={intermediaries_detected}")

    persisted = persist_intermediaries(intermediary_rows)

    snapshots = persist_snapshots(intermediary_rows)

    telemetry_payload = {
        "run_id": RUN_ID,
        "edges_loaded": edges_loaded,
        "intermediaries_detected": intermediaries_detected,
        "rows_persisted": persisted,
        "snapshots_written": snapshots,
        "created_at": datetime.utcnow().isoformat(),
    }

    persist_telemetry(telemetry_payload)

    if intermediaries_detected == 0:

        persist_validation(
            status="warning",
            message="No intermediary nodes detected.",
            observed_value=0,
        )

    else:

        persist_validation(
            status="passed",
            message="Intermediary nodes successfully detected.",
            observed_value=intermediaries_detected,
        )

    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
