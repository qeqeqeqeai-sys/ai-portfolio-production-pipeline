"""
Phase 5A.3 — Directed Intermediary Seeding Layer

Purpose:
- Deterministically seed A -> B and B -> C edges from explicit bridge rules.
- Convert shallow star-like graph structure into reusable intermediary topology.
- Keep the system replay-safe, auditable, and SQL/Supabase compatible.

Runtime marker:
5A3_DIRECTED_INTERMEDIARY_SEEDING_V1
"""

from __future__ import annotations

import os
import re
import time
import hashlib
import requests
from datetime import datetime, timezone
from collections import defaultdict


EDGE_TABLE = "structural_theme_graph_edges"
SEED_RULE_TABLE = "structural_theme_graph_directed_seed_rules"
SEED_EDGE_TABLE = "structural_theme_graph_directed_seed_edges"
SEED_TELEMETRY_TABLE = "structural_theme_graph_directed_seed_telemetry"
SEED_VALIDATION_TABLE = "structural_theme_graph_directed_seed_validation"

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

MIN_CONFIDENCE_SCORE = float(os.getenv("DIRECTED_SEED_MIN_CONFIDENCE", "0.60"))
PERSIST_TO_MAIN_EDGE_TABLE = os.getenv("DIRECTED_SEED_WRITE_MAIN_EDGES", "false").lower() == "true"


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def normalize_node_key(value: str) -> str:
    if not value:
        return ""

    value = str(value).lower().strip()
    value = value.replace("-", " ")
    value = value.replace("_", " ")
    value = re.sub(r"\s+", " ", value)

    synonym_map = {
        "data centers": "data_center",
        "data center": "data_center",
        "datacenters": "data_center",
        "power grid": "power_grid",
        "utilities": "utility",
        "electric utilities": "utility",
        "semiconductors": "semiconductor",
        "chips": "chip",
    }

    value = synonym_map.get(value, value)
    return value.replace(" ", "_")


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


def stable_hash(*parts: str) -> str:
    raw = "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def load_existing_edges() -> list[dict]:
    endpoint = f"{EDGE_TABLE}?select=source_node_key,target_node_key"
    rows = supabase_request("GET", endpoint)
    if not rows:
        return []
    if not isinstance(rows, list):
        raise RuntimeError(f"Expected edge list, got {type(rows)}")
    return rows


def load_active_seed_rules() -> list[dict]:
    endpoint = (
        f"{SEED_RULE_TABLE}"
        "?select=rule_id,rule_name,source_node_key,intermediary_node_key,target_node_key,"
        "edge_1_relation,edge_2_relation,seed_category,confidence_score,evidence_basis"
        "&is_active=eq.true"
    )
    rows = supabase_request("GET", endpoint)
    if not rows:
        return []
    if not isinstance(rows, list):
        raise RuntimeError(f"Expected seed rule list, got {type(rows)}")

    filtered = []
    for row in rows:
        confidence = float(row.get("confidence_score") or 0)
        if confidence >= MIN_CONFIDENCE_SCORE:
            filtered.append(row)

    return filtered


def build_edge_index(edges: list[dict]) -> set[tuple[str, str]]:
    edge_pairs = set()
    for row in edges:
        source = normalize_node_key(row.get("source_node_key", ""))
        target = normalize_node_key(row.get("target_node_key", ""))
        if source and target:
            edge_pairs.add((source, target))
    return edge_pairs


def generate_seed_edges(
    seed_rules: list[dict],
    existing_edge_pairs: set[tuple[str, str]],
) -> list[dict]:
    seed_edges = []

    for rule in seed_rules:
        rule_id = str(rule["rule_id"])
        source = normalize_node_key(rule["source_node_key"])
        intermediary = normalize_node_key(rule["intermediary_node_key"])
        target = normalize_node_key(rule["target_node_key"])

        confidence = float(rule.get("confidence_score") or 0)
        evidence_basis = rule.get("evidence_basis")
        seed_category = rule.get("seed_category") or "structural_intermediary"

        if not source or not intermediary or not target:
            continue

        # Deterministic gate:
        # seed only if the source already has at least one relevant graph connection,
        # or if the source->intermediary edge already exists.
        source_is_present = any(pair[0] == source or pair[1] == source for pair in existing_edge_pairs)
        source_to_intermediary_exists = (source, intermediary) in existing_edge_pairs

        if not source_is_present and not source_to_intermediary_exists:
            continue

        edge_specs = [
            {
                "source_node_key": source,
                "target_node_key": intermediary,
                "edge_role": "source_to_intermediary",
                "relation_type": rule.get("edge_1_relation") or "directed_seed",
            },
            {
                "source_node_key": intermediary,
                "target_node_key": target,
                "edge_role": "intermediary_to_target",
                "relation_type": rule.get("edge_2_relation") or "directed_seed",
            },
        ]

        for edge in edge_specs:
            edge_hash = stable_hash(
                rule_id,
                edge["source_node_key"],
                edge["target_node_key"],
                edge["edge_role"],
            )

            seed_edges.append(
                {
                    "run_id": RUN_ID,
                    "rule_id": rule_id,
                    "source_node_key": edge["source_node_key"],
                    "target_node_key": edge["target_node_key"],
                    "intermediary_node_key": intermediary,
                    "edge_role": edge["edge_role"],
                    "relation_type": edge["relation_type"],
                    "confidence_score": confidence,
                    "evidence_basis": evidence_basis,
                    "seed_hash": edge_hash,
                    "created_at": utc_now_iso(),
                }
            )

    # Dedupe within run by seed_hash
    deduped = {}
    for row in seed_edges:
        deduped[row["seed_hash"]] = row

    return list(deduped.values())


def build_main_edge_rows(seed_edges: list[dict]) -> list[dict]:
    """
    Optional compatibility output for structural_theme_graph_edges.

    This is deliberately conservative because your edge table schema may differ.
    Enable only after confirming structural_theme_graph_edges accepts these columns.
    """
    rows = []

    for row in seed_edges:
        edge_hash = stable_hash(
            "phase5a3_main_edge",
            row["source_node_key"],
            row["target_node_key"],
        )

        rows.append(
            {
                "source_node_key": row["source_node_key"],
                "target_node_key": row["target_node_key"],
                "edge_type": "directed_intermediary_seed",
                "relationship_type": row["relation_type"],
                "confidence_score": row["confidence_score"],
                "evidence_basis": row["evidence_basis"],
                "edge_hash": edge_hash,
                "created_at": utc_now_iso(),
            }
        )

    return rows


def persist_seed_edges(seed_edges: list[dict]) -> int:
    if not seed_edges:
        return 0

    supabase_upsert(
        SEED_EDGE_TABLE,
        seed_edges,
        on_conflict="seed_hash",
    )

    return len(seed_edges)


def persist_main_edges_if_enabled(seed_edges: list[dict]) -> int:
    if not PERSIST_TO_MAIN_EDGE_TABLE or not seed_edges:
        return 0

    main_edge_rows = build_main_edge_rows(seed_edges)

    # Only enable after checking your main edge table has compatible columns.
    supabase_upsert(
        EDGE_TABLE,
        main_edge_rows,
        on_conflict="edge_hash",
    )

    return len(main_edge_rows)


def persist_validation(
    validation_name: str,
    validation_status: str,
    observed_value: int | float,
    threshold_value: int | float | None,
    message: str,
    details: dict | None = None,
) -> None:
    payload = {
        "run_id": RUN_ID,
        "validation_name": validation_name,
        "validation_status": validation_status,
        "observed_value": observed_value,
        "threshold_value": threshold_value,
        "message": message,
        "details": details or {},
        "created_at": utc_now_iso(),
    }

    supabase_upsert(
        SEED_VALIDATION_TABLE,
        [payload],
        on_conflict="run_id,validation_name",
    )


def build_telemetry_payload(
    status: str,
    active_rules_loaded: int,
    source_edges_loaded: int,
    seed_edges_generated: int,
    seed_edges_persisted: int,
    validation_failures: int,
    runtime_seconds: float,
    error_message: str | None = None,
    details: dict | None = None,
) -> dict:
    return {
        "run_id": RUN_ID,
        "status": status,
        "active_rules_loaded": int(active_rules_loaded or 0),
        "source_edges_loaded": int(source_edges_loaded or 0),
        "seed_edges_generated": int(seed_edges_generated or 0),
        "seed_edges_persisted": int(seed_edges_persisted or 0),
        "validation_failures": int(validation_failures or 0),
        "runtime_seconds": round(float(runtime_seconds or 0), 4),
        "error_message": error_message,
        "details": details or {},
        "created_at": utc_now_iso(),
    }


def persist_telemetry(payload: dict) -> None:
    supabase_upsert(
        SEED_TELEMETRY_TABLE,
        [payload],
        on_conflict="run_id",
    )


def main() -> None:
    started = time.time()

    print("=" * 80)
    print("PHASE 5A.3 — DIRECTED INTERMEDIARY SEEDING LAYER")
    print("RUNTIME MARKER: 5A3_DIRECTED_INTERMEDIARY_SEEDING_V1")
    print("=" * 80)

    active_rules_loaded = 0
    source_edges_loaded = 0
    seed_edges_generated = 0
    seed_edges_persisted = 0
    main_edges_persisted = 0
    validation_failures = 0

    try:
        source_edges = load_existing_edges()
        source_edges_loaded = len(source_edges)
        existing_edge_pairs = build_edge_index(source_edges)

        seed_rules = load_active_seed_rules()
        active_rules_loaded = len(seed_rules)

        print(f"source_edges_loaded={source_edges_loaded}")
        print(f"active_rules_loaded={active_rules_loaded}")

        seed_edges = generate_seed_edges(seed_rules, existing_edge_pairs)
        seed_edges_generated = len(seed_edges)

        print(f"seed_edges_generated={seed_edges_generated}")

        seed_edges_persisted = persist_seed_edges(seed_edges)
        main_edges_persisted = persist_main_edges_if_enabled(seed_edges)

        if active_rules_loaded == 0:
            validation_failures += 1
            persist_validation(
                "active_seed_rules",
                "failed",
                0,
                1,
                "No active directed seed rules found.",
            )

        else:
            persist_validation(
                "active_seed_rules",
                "passed",
                active_rules_loaded,
                1,
                "Active directed seed rules loaded.",
            )

        if seed_edges_generated == 0:
            validation_failures += 1
            persist_validation(
                "seed_generation",
                "warning",
                0,
                1,
                "No seed edges generated. Graph may still lack matching source nodes.",
                {
                    "min_confidence": MIN_CONFIDENCE_SCORE,
                },
            )
            status = "warning"
        else:
            persist_validation(
                "seed_generation",
                "passed",
                seed_edges_generated,
                1,
                "Directed intermediary seed edges generated.",
            )
            status = "success"

        runtime_seconds = time.time() - started

        persist_telemetry(
            build_telemetry_payload(
                status=status,
                active_rules_loaded=active_rules_loaded,
                source_edges_loaded=source_edges_loaded,
                seed_edges_generated=seed_edges_generated,
                seed_edges_persisted=seed_edges_persisted,
                validation_failures=validation_failures,
                runtime_seconds=runtime_seconds,
                details={
                    "main_edges_persisted": main_edges_persisted,
                    "write_main_edges_enabled": PERSIST_TO_MAIN_EDGE_TABLE,
                    "min_confidence": MIN_CONFIDENCE_SCORE,
                    "runtime_marker": "5A3_DIRECTED_INTERMEDIARY_SEEDING_V1",
                },
            )
        )

        print(f"seed_edges_persisted={seed_edges_persisted}")
        print(f"main_edges_persisted={main_edges_persisted}")
        print(f"status={status}")

    except Exception as exc:
        runtime_seconds = time.time() - started
        error_message = str(exc)

        print(f"ERROR: {error_message}")

        try:
            persist_telemetry(
                build_telemetry_payload(
                    status="failed",
                    active_rules_loaded=active_rules_loaded,
                    source_edges_loaded=source_edges_loaded,
                    seed_edges_generated=seed_edges_generated,
                    seed_edges_persisted=seed_edges_persisted,
                    validation_failures=max(1, validation_failures),
                    runtime_seconds=runtime_seconds,
                    error_message=error_message,
                    details={
                        "main_edges_persisted": main_edges_persisted,
                        "write_main_edges_enabled": PERSIST_TO_MAIN_EDGE_TABLE,
                        "min_confidence": MIN_CONFIDENCE_SCORE,
                        "runtime_marker": "5A3_DIRECTED_INTERMEDIARY_SEEDING_V1",
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
