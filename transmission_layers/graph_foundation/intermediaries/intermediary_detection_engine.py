"""
Phase 5A.2 — Structural Intermediary Formation
FULL REVISED intermediary_detection_engine.py

Fixes included:
1. Removed duplicate headers injection
2. Added GitHub Actions safe repo-root bootstrap import logic
3. Compatible with standalone execution
4. Replay-safe deterministic intermediary generation
"""

from __future__ import annotations

import os
import re
import sys
import json
import hashlib

from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict


# ============================================================
# REPO ROOT BOOTSTRAP
# ============================================================

CURRENT_FILE = Path(__file__).resolve()

# intermediary_detection_engine.py
# -> intermediaries
# -> graph_foundation
# -> transmission_layers
# -> repo root

REPO_ROOT = CURRENT_FILE.parents[3]

sys.path.append(str(REPO_ROOT))


# ============================================================
# SHARED SUPABASE IMPORT
# ============================================================

from transmission_layers.shared.supabase_rest import supabase_request


# ============================================================
# CONFIG
# ============================================================

EDGE_TABLE = "structural_theme_graph_edges"

INTERMEDIARY_TABLE = "structural_theme_graph_intermediaries"

INTERMEDIARY_SCORE_TABLE = (
    "structural_theme_graph_intermediary_scores"
)

INTERMEDIARY_SNAPSHOT_TABLE = (
    "structural_theme_graph_intermediary_snapshots"
)

INTERMEDIARY_TELEMETRY_TABLE = (
    "structural_theme_graph_intermediary_telemetry"
)

INTERMEDIARY_VALIDATION_TABLE = (
    "structural_theme_graph_intermediary_validation"
)

RUN_ID = datetime.now(timezone.utc).strftime(
    "%Y%m%d_%H%M%S"
)

MIN_INBOUND = int(
    os.getenv("INTERMEDIARY_MIN_INBOUND", "1")
)

MIN_OUTBOUND = int(
    os.getenv("INTERMEDIARY_MIN_OUTBOUND", "1")
)


# ============================================================
# NORMALIZATION
# ============================================================

def normalize_node_key(value: str) -> str:

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
        "utilities": "utility",
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
        "compute": [
            "gpu",
            "compute",
            "server",
            "ai_compute"
        ],
        "semiconductor": [
            "semiconductor",
            "chip",
            "wafer"
        ],
        "energy": [
            "power",
            "grid",
            "utility",
            "electric"
        ],
        "infrastructure": [
            "data_center",
            "infrastructure"
        ],
        "industrial": [
            "industrial",
            "factory"
        ],
        "logistics": [
            "shipping",
            "logistics",
            "freight"
        ],
        "supply_chain": [
            "supply",
            "materials",
            "mining"
        ],
        "capital_flow": [
            "capital",
            "financing",
            "liquidity"
        ],
        "policy": [
            "regulation",
            "policy",
            "government"
        ],
    }

    for category, keywords in rules.items():

        for keyword in keywords:

            if keyword in node:
                return category

    return "general"


# ============================================================
# STABLE HASH
# ============================================================

def stable_intermediary_hash(node_key: str) -> str:

    return hashlib.sha256(
        node_key.encode("utf-8")
    ).hexdigest()


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
        endpoint
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

    all_nodes = set(
        list(inbound_counts.keys())
        + list(outbound_counts.keys())
    )

    intermediary_rows = []

    for node_key in all_nodes:

        inbound = inbound_counts[node_key]
        outbound = outbound_counts[node_key]

        if inbound < MIN_INBOUND:
            continue

        if outbound < MIN_OUTBOUND:
            continue

        continuity_reuse_frequency = min(
            inbound,
            outbound
        )

        propagation_participation = (
            inbound + outbound
        )

        regime_stability = (
            continuity_reuse_frequency
            / max(1, propagation_participation)
        )

        evidence_density = (
            len(inbound_sources[node_key])
            + len(outbound_targets[node_key])
        )

        intermediary_score = (
            (inbound * 0.20)
            + (outbound * 0.20)
            + (continuity_reuse_frequency * 0.25)
            + (propagation_participation * 0.15)
            + (regime_stability * 0.10)
            + (evidence_density * 0.10)
        )

        intermediary_rows.append(
            {
                "run_id": RUN_ID,
                "node_key": node_key,
                "intermediary_hash": stable_intermediary_hash(
                    node_key
                ),
                "classification": classify_intermediary(
                    node_key
                ),
                "inbound_edge_count": inbound,
                "outbound_edge_count": outbound,
                "continuity_reuse_frequency": (
                    continuity_reuse_frequency
                ),
                "propagation_participation": (
                    propagation_participation
                ),
                "regime_stability": round(
                    regime_stability,
                    4
                ),
                "evidence_density": evidence_density,
                "intermediary_activation_score": round(
                    intermediary_score,
                    4
                ),
                "upstream_source_count": len(
                    inbound_sources[node_key]
                ),
                "downstream_target_count": len(
                    outbound_targets[node_key]
                ),
                "created_at": datetime.utcnow().isoformat(),
            }
        )

    intermediary_rows = sorted(
        intermediary_rows,
        key=lambda x: (
            x["intermediary_activation_score"]
        ),
        reverse=True
    )

    return intermediary_rows


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

    supabase_request(
        "POST",
        endpoint,
        rows
    )

    return len(rows)


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

    supabase_request(
        "POST",
        endpoint,
        snapshot_rows
    )

    return len(snapshot_rows)


# ============================================================
# TELEMETRY
# ============================================================

def persist_telemetry(payload):

    endpoint = (
        f"{INTERMEDIARY_TELEMETRY_TABLE}"
        "?on_conflict=run_id"
    )

    supabase_request(
        "POST",
        endpoint,
        [payload]
    )


# ============================================================
# VALIDATION
# ============================================================

def persist_validation(
    status,
    message,
    observed_value
):

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
    print(
        "PHASE 5A.2 — STRUCTURAL INTERMEDIARY DETECTION"
    )
    print("=" * 80)

    edges = load_graph_edges()

    edges_loaded = len(edges)

    print(f"edges_loaded={edges_loaded}")

    intermediary_rows = detect_intermediaries(
        edges
    )

    intermediaries_detected = len(
        intermediary_rows
    )

    print(
        f"intermediaries_detected="
        f"{intermediaries_detected}"
    )

    rows_persisted = persist_intermediaries(
        intermediary_rows
    )

    snapshots_written = persist_snapshots(
        intermediary_rows
    )

    telemetry_payload = {
        "run_id": RUN_ID,
        "edges_loaded": edges_loaded,
        "intermediaries_detected": (
            intermediaries_detected
        ),
        "rows_persisted": rows_persisted,
        "snapshots_written": snapshots_written,
        "created_at": datetime.utcnow().isoformat(),
    }

    persist_telemetry(
        telemetry_payload
    )

    if intermediaries_detected == 0:

        persist_validation(
            status="warning",
            message=(
                "No intermediary nodes detected."
            ),
            observed_value=0,
        )

    else:

        persist_validation(
            status="passed",
            message=(
                "Intermediary nodes successfully "
                "detected."
            ),
            observed_value=(
                intermediaries_detected
            ),
        )

    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
