"""
Phase 5A.2 — Structural Intermediary Detection
Canonical Integration Fix V5

Fix:
- Reads canonicalized edges from Phase 5A.4:
  structural_theme_graph_canonical_edge_view_materialized
- Also reads Phase 5A.3 seeded edges:
  structural_theme_graph_directed_seed_edges
- Falls back to raw structural_theme_graph_edges if canonical/seed edges are unavailable.

Runtime marker:
5A2_CANONICAL_INTEGRATED_V5
"""

from __future__ import annotations

import os
import re
import json
import time
import hashlib
import requests
from datetime import datetime, timezone
from collections import defaultdict


RAW_EDGE_TABLE = "structural_theme_graph_edges"
CANONICAL_EDGE_TABLE = "structural_theme_graph_canonical_edge_view_materialized"
SEED_EDGE_TABLE = "structural_theme_graph_directed_seed_edges"

INTERMEDIARY_TABLE = "structural_theme_graph_intermediaries"
INTERMEDIARY_SCORE_TABLE = "structural_theme_graph_intermediary_scores"
INTERMEDIARY_SNAPSHOT_TABLE = "structural_theme_graph_intermediary_snapshots"
INTERMEDIARY_TELEMETRY_TABLE = "structural_theme_graph_intermediary_telemetry"
INTERMEDIARY_VALIDATION_TABLE = "structural_theme_graph_intermediary_validation"

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

MIN_INBOUND = int(os.getenv("INTERMEDIARY_MIN_INBOUND", "1"))
MIN_OUTBOUND = int(os.getenv("INTERMEDIARY_MIN_OUTBOUND", "1"))

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def normalize_node_key(value: str) -> str:
    if not value:
        return ""

    value = str(value).lower().strip()
    value = value.replace("&", " and ")
    value = value.replace("-", " ")
    value = value.replace("/", " ")
    value = value.replace("_", " ")
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    phrase_map = {
        "artificial intelligence": "ai",
        "generative ai": "generative_ai",
        "gen ai": "genai",
        "data centers": "data_center",
        "data center": "data_center",
        "data centres": "data_center",
        "data centre": "data_center",
        "power grid": "power_grid",
        "electric grid": "power_grid",
        "electric utilities": "utility",
        "electric utility": "utility",
        "utility companies": "utility",
        "utilities": "utility",
        "power demand": "electricity_demand",
        "electricity load": "electricity_demand",
        "copper demand": "copper",
        "copper supply": "copper",
    }

    value = phrase_map.get(value, value)
    return value.replace(" ", "_")


def classify_intermediary(node_key: str) -> str:
    node = node_key.lower()

    rules = {
        "compute": ["gpu", "compute", "server", "ai_compute", "cloud"],
        "semiconductor": ["semiconductor", "chip", "wafer", "foundry"],
        "energy": ["power", "grid", "utility", "electric", "energy", "electricity"],
        "infrastructure": ["data_center", "infrastructure", "fiber", "network", "cooling"],
        "industrial": ["industrial", "factory", "automation"],
        "logistics": ["shipping", "logistics", "freight", "transport"],
        "supply_chain": ["supply", "materials", "mining", "copper", "rare_earth"],
        "capital_flow": ["capital", "financing", "liquidity", "credit", "funding", "capex"],
        "policy": ["regulation", "policy", "government", "export_control"],
        "demand_transmission": ["demand", "consumption", "adoption"],
    }

    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword in node:
                return category

    return "general"


def stable_hash(*parts: str) -> str:
    raw = "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def supabase_headers(prefer: str | None = None) -> dict:
    if not SUPABASE_URL:
        raise RuntimeError("Missing SUPABASE_URL environment variable.")
    if not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY environment variable.")

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    if prefer:
        headers["Prefer"] = prefer

    return headers


def supabase_request(method: str, endpoint: str, payload=None, prefer: str | None = None):
    base_url = SUPABASE_URL.rstrip("/")
    url = f"{base_url}/rest/v1/{endpoint}"
    method = method.upper()
    headers = supabase_headers(prefer=prefer)

    if method == "GET":
        response = requests.get(url, headers=headers, timeout=60)
    elif method == "POST":
        response = requests.post(url, headers=headers, json=payload, timeout=120)
    else:
        raise ValueError(f"Unsupported method: {method}")

    if response.status_code >= 400:
        raise RuntimeError(
            f"Supabase request failed: {method} {endpoint} "
            f"status={response.status_code} body={response.text}"
        )

    if not response.text:
        return None

    try:
        return response.json()
    except Exception:
        return response.text


def supabase_upsert(table_name: str, rows: list[dict], on_conflict: str):
    if not rows:
        return None

    return supabase_request(
        "POST",
        f"{table_name}?on_conflict={on_conflict}",
        payload=rows,
        prefer="resolution=merge-duplicates,return=minimal",
    )


def safe_get(endpoint: str) -> list[dict]:
    try:
        rows = supabase_request("GET", endpoint)
        if not rows:
            return []
        if not isinstance(rows, list):
            return []
        return rows
    except Exception as exc:
        print(f"WARNING: failed to load {endpoint}: {exc}")
        return []


def load_canonical_edges() -> list[dict]:
    rows = safe_get(
        f"{CANONICAL_EDGE_TABLE}"
        "?select=canonical_source_node_key,canonical_target_node_key"
    )

    edges = []
    for row in rows:
        source = normalize_node_key(row.get("canonical_source_node_key"))
        target = normalize_node_key(row.get("canonical_target_node_key"))
        if source and target and source != target:
            edges.append(
                {
                    "source_node_key": source,
                    "target_node_key": target,
                    "edge_source": "canonical_view",
                }
            )

    return edges


def load_seed_edges() -> list[dict]:
    rows = safe_get(
        f"{SEED_EDGE_TABLE}"
        "?select=source_node_key,target_node_key"
    )

    edges = []
    for row in rows:
        source = normalize_node_key(row.get("source_node_key"))
        target = normalize_node_key(row.get("target_node_key"))
        if source and target and source != target:
            edges.append(
                {
                    "source_node_key": source,
                    "target_node_key": target,
                    "edge_source": "directed_seed",
                }
            )

    return edges


def load_raw_edges() -> list[dict]:
    rows = safe_get(
        f"{RAW_EDGE_TABLE}"
        "?select=source_node_key,target_node_key"
    )

    edges = []
    for row in rows:
        source = normalize_node_key(row.get("source_node_key"))
        target = normalize_node_key(row.get("target_node_key"))
        if source and target and source != target:
            edges.append(
                {
                    "source_node_key": source,
                    "target_node_key": target,
                    "edge_source": "raw_edge",
                }
            )

    return edges


def load_graph_edges() -> tuple[list[dict], dict]:
    canonical_edges = load_canonical_edges()
    seed_edges = load_seed_edges()

    combined = canonical_edges + seed_edges

    if not combined:
        raw_edges = load_raw_edges()
        combined = raw_edges
    else:
        raw_edges = []

    deduped = {}
    for edge in combined:
        key = (edge["source_node_key"], edge["target_node_key"])
        deduped[key] = edge

    return list(deduped.values()), {
        "canonical_edges_loaded": len(canonical_edges),
        "seed_edges_loaded": len(seed_edges),
        "raw_edges_loaded": len(raw_edges),
        "deduped_edges_loaded": len(deduped),
    }


def detect_intermediaries(edges: list[dict]) -> list[dict]:
    inbound_counts = defaultdict(int)
    outbound_counts = defaultdict(int)
    inbound_sources = defaultdict(set)
    outbound_targets = defaultdict(set)

    for row in edges:
        source = normalize_node_key(row.get("source_node_key", ""))
        target = normalize_node_key(row.get("target_node_key", ""))

        if not source or not target or source == target:
            continue

        outbound_counts[source] += 1
        inbound_counts[target] += 1
        outbound_targets[source].add(target)
        inbound_sources[target].add(source)

    all_nodes = set(list(inbound_counts.keys()) + list(outbound_counts.keys()))
    intermediary_rows = []

    for node_key in all_nodes:
        inbound = inbound_counts[node_key]
        outbound = outbound_counts[node_key]

        if inbound < MIN_INBOUND:
            continue
        if outbound < MIN_OUTBOUND:
            continue

        continuity_reuse_frequency = min(inbound, outbound)
        propagation_participation = inbound + outbound
        regime_stability = continuity_reuse_frequency / max(1, propagation_participation)
        evidence_density = len(inbound_sources[node_key]) + len(outbound_targets[node_key])

        intermediary_activation_score = (
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
                "intermediary_hash": stable_hash(node_key),
                "classification": classify_intermediary(node_key),
                "inbound_edge_count": inbound,
                "outbound_edge_count": outbound,
                "continuity_reuse_frequency": continuity_reuse_frequency,
                "propagation_participation": propagation_participation,
                "regime_stability": round(regime_stability, 4),
                "evidence_density": evidence_density,
                "intermediary_activation_score": round(intermediary_activation_score, 4),
                "upstream_source_count": len(inbound_sources[node_key]),
                "downstream_target_count": len(outbound_targets[node_key]),
                "created_at": utc_now_iso(),
            }
        )

    return sorted(
        intermediary_rows,
        key=lambda row: row["intermediary_activation_score"],
        reverse=True,
    )


def build_score_rows(intermediary_rows: list[dict]) -> list[dict]:
    return [
        {
            "run_id": RUN_ID,
            "node_key": row["node_key"],
            "intermediary_hash": row["intermediary_hash"],
            "inbound_connectivity_score": row["inbound_edge_count"],
            "outbound_connectivity_score": row["outbound_edge_count"],
            "continuity_reuse_score": row["continuity_reuse_frequency"],
            "propagation_participation_score": row["propagation_participation"],
            "regime_stability_score": row["regime_stability"],
            "evidence_density_score": row["evidence_density"],
            "overall_intermediary_score": row["intermediary_activation_score"],
            "created_at": utc_now_iso(),
        }
        for row in intermediary_rows
    ]


def build_snapshot_rows(intermediary_rows: list[dict]) -> list[dict]:
    return [
        {
            "run_id": RUN_ID,
            "node_key": row["node_key"],
            "snapshot_type": "daily",
            "snapshot_payload": row,
            "created_at": utc_now_iso(),
        }
        for row in intermediary_rows
    ]


def persist_intermediaries(rows: list[dict]) -> int:
    if not rows:
        return 0
    supabase_upsert(INTERMEDIARY_TABLE, rows, on_conflict="intermediary_hash")
    return len(rows)


def persist_scores(rows: list[dict]) -> int:
    if not rows:
        return 0
    supabase_upsert(INTERMEDIARY_SCORE_TABLE, rows, on_conflict="run_id,node_key")
    return len(rows)


def persist_snapshots(rows: list[dict]) -> int:
    if not rows:
        return 0
    supabase_upsert(INTERMEDIARY_SNAPSHOT_TABLE, rows, on_conflict="run_id,node_key,snapshot_type")
    return len(rows)


def build_telemetry_payload(
    status: str,
    edges_loaded: int,
    candidate_nodes_loaded: int,
    intermediaries_detected: int,
    intermediaries_persisted: int,
    validation_failures: int,
    runtime_seconds: float,
    error_message: str | None = None,
    details: dict | None = None,
) -> dict:
    return {
        "run_id": RUN_ID,
        "status": status,
        "edges_loaded": int(edges_loaded or 0),
        "candidate_nodes_loaded": int(candidate_nodes_loaded or 0),
        "intermediaries_detected": int(intermediaries_detected or 0),
        "intermediaries_persisted": int(intermediaries_persisted or 0),
        "validation_failures": int(validation_failures or 0),
        "runtime_seconds": round(float(runtime_seconds or 0), 4),
        "error_message": error_message,
        "details": details or {},
        "created_at": utc_now_iso(),
    }


def persist_telemetry(payload: dict) -> None:
    supabase_upsert(INTERMEDIARY_TELEMETRY_TABLE, [payload], on_conflict="run_id")


def persist_validation(status: str, message: str, observed_value: int, details: dict | None = None) -> None:
    payload = {
        "run_id": RUN_ID,
        "validation_name": "intermediary_detection",
        "validation_status": status,
        "message": message,
        "observed_value": observed_value,
        "details": details or {},
        "created_at": utc_now_iso(),
    }

    supabase_upsert(
        INTERMEDIARY_VALIDATION_TABLE,
        [payload],
        on_conflict="run_id,validation_name",
    )


def main() -> None:
    started = time.time()

    print("=" * 80)
    print("PHASE 5A.2 — STRUCTURAL INTERMEDIARY DETECTION")
    print("RUNTIME MARKER: 5A2_CANONICAL_INTEGRATED_V5")
    print("=" * 80)

    edges_loaded = 0
    intermediaries_detected = 0
    rows_persisted = 0
    scores_written = 0
    snapshots_written = 0
    validation_failures = 0
    load_details = {}

    try:
        edges, load_details = load_graph_edges()
        edges_loaded = len(edges)

        print(f"edges_loaded={edges_loaded}")
        print(f"load_details={load_details}")

        intermediary_rows = detect_intermediaries(edges)
        intermediaries_detected = len(intermediary_rows)

        print(f"intermediaries_detected={intermediaries_detected}")

        score_rows = build_score_rows(intermediary_rows)
        snapshot_rows = build_snapshot_rows(intermediary_rows)

        rows_persisted = persist_intermediaries(intermediary_rows)
        scores_written = persist_scores(score_rows)
        snapshots_written = persist_snapshots(snapshot_rows)

        if intermediaries_detected == 0:
            validation_failures = 1
            status = "warning"
            persist_validation(
                status="warning",
                message="No intermediary nodes detected after canonical/seed integration.",
                observed_value=0,
                details=load_details,
            )
        else:
            status = "success"
            persist_validation(
                status="passed",
                message="Intermediary nodes detected using canonical/seed integrated graph.",
                observed_value=intermediaries_detected,
                details=load_details,
            )

        runtime_seconds = time.time() - started

        persist_telemetry(
            build_telemetry_payload(
                status=status,
                edges_loaded=edges_loaded,
                candidate_nodes_loaded=intermediaries_detected,
                intermediaries_detected=intermediaries_detected,
                intermediaries_persisted=rows_persisted,
                validation_failures=validation_failures,
                runtime_seconds=runtime_seconds,
                details={
                    **load_details,
                    "scores_written": scores_written,
                    "snapshots_written": snapshots_written,
                    "min_inbound": MIN_INBOUND,
                    "min_outbound": MIN_OUTBOUND,
                    "runtime_marker": "5A2_CANONICAL_INTEGRATED_V5",
                },
            )
        )

        print(f"rows_persisted={rows_persisted}")
        print(f"scores_written={scores_written}")
        print(f"snapshots_written={snapshots_written}")
        print(f"status={status}")

    except Exception as exc:
        runtime_seconds = time.time() - started
        error_message = str(exc)
        print(f"ERROR: {error_message}")

        try:
            persist_telemetry(
                build_telemetry_payload(
                    status="failed",
                    edges_loaded=edges_loaded,
                    candidate_nodes_loaded=intermediaries_detected,
                    intermediaries_detected=intermediaries_detected,
                    intermediaries_persisted=rows_persisted,
                    validation_failures=max(1, validation_failures),
                    runtime_seconds=runtime_seconds,
                    error_message=error_message,
                    details={
                        **load_details,
                        "runtime_marker": "5A2_CANONICAL_INTEGRATED_V5",
                    },
                )
            )
        except Exception as telemetry_exc:
            print(f"WARNING: failed to persist failure telemetry: {telemetry_exc}")

        raise

    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
