"""
Phase 5A.4 — Canonical Structural Ontology Layer

Purpose:
- Load raw graph semantic keys.
- Normalize raw node keys.
- Map fragmented variants to stable canonical ontology identities.
- Persist node mappings and canonicalized edge view.
- Prepare graph for intermediary detection and directed seeding.

Runtime marker:
5A4_CANONICAL_STRUCTURAL_ONTOLOGY_V1
"""

from __future__ import annotations

import os
import re
import time
import hashlib
import requests
from datetime import datetime, timezone


EDGE_TABLE = "structural_theme_graph_edges"

ONTOLOGY_TERM_TABLE = "structural_theme_graph_canonical_ontology_terms"
ONTOLOGY_ALIAS_TABLE = "structural_theme_graph_canonical_ontology_aliases"
NODE_MAPPING_TABLE = "structural_theme_graph_canonical_node_mappings"
CANONICAL_EDGE_TABLE = "structural_theme_graph_canonical_edge_view_materialized"
TELEMETRY_TABLE = "structural_theme_graph_canonical_ontology_telemetry"
VALIDATION_TABLE = "structural_theme_graph_canonical_ontology_validation"

RUN_ID = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_KEY = SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

MIN_MAPPING_CONFIDENCE = float(os.getenv("CANONICAL_ONTOLOGY_MIN_CONFIDENCE", "0.70"))


def utc_now_iso() -> str:
    return datetime.utcnow().isoformat()


def stable_hash(*parts: str) -> str:
    raw = "|".join(str(p or "") for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


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
        "data centers": "data_centers",
        "data center": "data_center",
        "data centres": "data_centres",
        "data centre": "data_centre",
        "electric utilities": "electric_utilities",
        "electric utility": "electric_utility",
        "utility companies": "utility_companies",
        "power grid": "power_grid",
        "electric grid": "electric_grid",
        "grid expansion": "grid_expansion",
        "copper demand": "copper_demand",
        "copper supply": "copper_supply",
        "ai gpu": "ai_gpu",
        "cloud computing": "cloud_computing",
        "ai infrastructure": "ai_infrastructure",
        "compute capacity": "compute_capacity",
        "power demand": "power_demand",
        "electricity load": "electricity_load",
        "load growth": "load_growth",
        "investment spending": "investment_spending",
    }

    value = phrase_map.get(value, value)
    value = value.replace(" ", "_")

    return value


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


def load_raw_edges() -> list[dict]:
    endpoint = f"{EDGE_TABLE}?select=source_node_key,target_node_key"
    rows = supabase_request("GET", endpoint)

    if not rows:
        return []

    if not isinstance(rows, list):
        raise RuntimeError(f"Expected raw edge list, got {type(rows)}")

    return rows


def load_ontology_terms() -> dict[str, dict]:
    endpoint = (
        f"{ONTOLOGY_TERM_TABLE}"
        "?select=canonical_node_key,canonical_label,ontology_category,is_active"
        "&is_active=eq.true"
    )
    rows = supabase_request("GET", endpoint)

    terms = {}
    for row in rows or []:
        key = normalize_node_key(row["canonical_node_key"])
        terms[key] = row

    return terms


def load_aliases() -> dict[str, dict]:
    endpoint = (
        f"{ONTOLOGY_ALIAS_TABLE}"
        "?select=alias_node_key,canonical_node_key,alias_type,confidence_score,is_active"
        "&is_active=eq.true"
    )
    rows = supabase_request("GET", endpoint)

    aliases = {}
    for row in rows or []:
        alias_key = normalize_node_key(row["alias_node_key"])
        aliases[alias_key] = row

    return aliases


def infer_category_from_key(node_key: str) -> str:
    rules = {
        "theme": ["ai"],
        "infrastructure": ["data", "center", "cooling", "fiber", "network"],
        "energy": ["power", "grid", "electric", "utility", "energy"],
        "supply_chain": ["copper", "materials", "supply", "mining"],
        "semiconductor": ["semiconductor", "chip", "wafer", "foundry"],
        "compute": ["gpu", "compute", "cloud", "server"],
        "capital_flow": ["capex", "capital", "investment", "financing"],
        "policy": ["policy", "regulation", "government"],
    }

    for category, keywords in rules.items():
        for keyword in keywords:
            if keyword in node_key:
                return category

    return "general"


def canonicalize_node(
    raw_node_key: str,
    ontology_terms: dict[str, dict],
    aliases: dict[str, dict],
) -> dict:
    normalized = normalize_node_key(raw_node_key)

    if not normalized:
        canonical = ""
        method = "empty"
        confidence = 0.0
        label = None
        category = None

    elif normalized in ontology_terms:
        canonical = normalized
        method = "canonical_exact"
        confidence = 1.0
        term = ontology_terms[canonical]
        label = term.get("canonical_label")
        category = term.get("ontology_category")

    elif normalized in aliases:
        alias = aliases[normalized]
        confidence = float(alias.get("confidence_score") or 0)

        if confidence >= MIN_MAPPING_CONFIDENCE:
            canonical = normalize_node_key(alias["canonical_node_key"])
            method = f"alias_{alias.get('alias_type') or 'manual'}"
            term = ontology_terms.get(canonical, {})
            label = term.get("canonical_label")
            category = term.get("ontology_category") or infer_category_from_key(canonical)
        else:
            canonical = normalized
            method = "alias_below_confidence_fallback"
            label = normalized.replace("_", " ").title()
            category = infer_category_from_key(normalized)

    else:
        canonical = normalized
        method = "normalized_fallback"
        confidence = 0.60
        label = normalized.replace("_", " ").title()
        category = infer_category_from_key(normalized)

    return {
        "raw_node_key": raw_node_key,
        "normalized_node_key": normalized,
        "canonical_node_key": canonical,
        "canonical_label": label,
        "ontology_category": category,
        "mapping_method": method,
        "confidence_score": confidence,
    }


def extract_raw_nodes(edges: list[dict]) -> list[str]:
    nodes = set()

    for row in edges:
        source = row.get("source_node_key")
        target = row.get("target_node_key")

        if source:
            nodes.add(str(source))
        if target:
            nodes.add(str(target))

    return sorted(nodes)


def build_mapping_rows(
    raw_nodes: list[str],
    ontology_terms: dict[str, dict],
    aliases: dict[str, dict],
) -> tuple[list[dict], dict[str, dict]]:
    rows = []
    mapping_lookup = {}

    for raw_node in raw_nodes:
        mapped = canonicalize_node(raw_node, ontology_terms, aliases)

        mapping_hash = stable_hash(
            mapped["raw_node_key"],
            mapped["normalized_node_key"],
            mapped["canonical_node_key"],
        )

        row = {
            "run_id": RUN_ID,
            "raw_node_key": mapped["raw_node_key"],
            "normalized_node_key": mapped["normalized_node_key"],
            "canonical_node_key": mapped["canonical_node_key"],
            "canonical_label": mapped["canonical_label"],
            "ontology_category": mapped["ontology_category"],
            "mapping_method": mapped["mapping_method"],
            "confidence_score": mapped["confidence_score"],
            "mapping_hash": mapping_hash,
            "created_at": utc_now_iso(),
        }

        rows.append(row)
        mapping_lookup[raw_node] = row

    return rows, mapping_lookup


def build_canonical_edge_rows(edges: list[dict], mapping_lookup: dict[str, dict]) -> list[dict]:
    rows = []

    for edge in edges:
        raw_source = str(edge.get("source_node_key") or "")
        raw_target = str(edge.get("target_node_key") or "")

        if not raw_source or not raw_target:
            continue

        source_map = mapping_lookup.get(raw_source)
        target_map = mapping_lookup.get(raw_target)

        if not source_map or not target_map:
            continue

        canonical_source = source_map["canonical_node_key"]
        canonical_target = target_map["canonical_node_key"]

        if not canonical_source or not canonical_target:
            continue

        if canonical_source == canonical_target:
            continue

        canonical_edge_hash = stable_hash(
            canonical_source,
            canonical_target,
            source_map["mapping_method"],
            target_map["mapping_method"],
        )

        rows.append(
            {
                "run_id": RUN_ID,
                "raw_source_node_key": raw_source,
                "raw_target_node_key": raw_target,
                "canonical_source_node_key": canonical_source,
                "canonical_target_node_key": canonical_target,
                "source_mapping_method": source_map["mapping_method"],
                "target_mapping_method": target_map["mapping_method"],
                "canonical_edge_hash": canonical_edge_hash,
                "created_at": utc_now_iso(),
            }
        )

    deduped = {}
    for row in rows:
        deduped[row["canonical_edge_hash"]] = row

    return list(deduped.values())


def persist_mappings(rows: list[dict]) -> int:
    if not rows:
        return 0

    supabase_upsert(
        NODE_MAPPING_TABLE,
        rows,
        on_conflict="mapping_hash",
    )

    return len(rows)


def persist_canonical_edges(rows: list[dict]) -> int:
    if not rows:
        return 0

    supabase_upsert(
        CANONICAL_EDGE_TABLE,
        rows,
        on_conflict="canonical_edge_hash",
    )

    return len(rows)


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
        VALIDATION_TABLE,
        [payload],
        on_conflict="run_id,validation_name",
    )


def build_telemetry_payload(
    status: str,
    raw_edges_loaded: int,
    raw_nodes_detected: int,
    ontology_terms_loaded: int,
    aliases_loaded: int,
    mappings_generated: int,
    canonical_edges_generated: int,
    validation_failures: int,
    runtime_seconds: float,
    error_message: str | None = None,
    details: dict | None = None,
) -> dict:
    return {
        "run_id": RUN_ID,
        "status": status,
        "raw_edges_loaded": int(raw_edges_loaded or 0),
        "raw_nodes_detected": int(raw_nodes_detected or 0),
        "ontology_terms_loaded": int(ontology_terms_loaded or 0),
        "aliases_loaded": int(aliases_loaded or 0),
        "mappings_generated": int(mappings_generated or 0),
        "canonical_edges_generated": int(canonical_edges_generated or 0),
        "validation_failures": int(validation_failures or 0),
        "runtime_seconds": round(float(runtime_seconds or 0), 4),
        "error_message": error_message,
        "details": details or {},
        "created_at": utc_now_iso(),
    }


def persist_telemetry(payload: dict) -> None:
    supabase_upsert(
        TELEMETRY_TABLE,
        [payload],
        on_conflict="run_id",
    )


def summarize_mapping_methods(mapping_rows: list[dict]) -> dict:
    summary = {}

    for row in mapping_rows:
        method = row["mapping_method"]
        summary[method] = summary.get(method, 0) + 1

    return summary


def main() -> None:
    started = time.time()

    print("=" * 80)
    print("PHASE 5A.4 — CANONICAL STRUCTURAL ONTOLOGY LAYER")
    print("RUNTIME MARKER: 5A4_CANONICAL_STRUCTURAL_ONTOLOGY_V1")
    print("=" * 80)

    raw_edges_loaded = 0
    raw_nodes_detected = 0
    ontology_terms_loaded = 0
    aliases_loaded = 0
    mappings_generated = 0
    canonical_edges_generated = 0
    mappings_persisted = 0
    canonical_edges_persisted = 0
    validation_failures = 0

    try:
        raw_edges = load_raw_edges()
        raw_edges_loaded = len(raw_edges)

        raw_nodes = extract_raw_nodes(raw_edges)
        raw_nodes_detected = len(raw_nodes)

        ontology_terms = load_ontology_terms()
        aliases = load_aliases()

        ontology_terms_loaded = len(ontology_terms)
        aliases_loaded = len(aliases)

        mapping_rows, mapping_lookup = build_mapping_rows(
            raw_nodes,
            ontology_terms,
            aliases,
        )

        mappings_generated = len(mapping_rows)

        canonical_edge_rows = build_canonical_edge_rows(
            raw_edges,
            mapping_lookup,
        )

        canonical_edges_generated = len(canonical_edge_rows)

        mappings_persisted = persist_mappings(mapping_rows)
        canonical_edges_persisted = persist_canonical_edges(canonical_edge_rows)

        if raw_edges_loaded == 0:
            validation_failures += 1
            persist_validation(
                "raw_edges_loaded",
                "failed",
                raw_edges_loaded,
                1,
                "No raw graph edges were loaded.",
            )
        else:
            persist_validation(
                "raw_edges_loaded",
                "passed",
                raw_edges_loaded,
                1,
                "Raw graph edges loaded successfully.",
            )

        if ontology_terms_loaded == 0:
            validation_failures += 1
            persist_validation(
                "ontology_terms_loaded",
                "failed",
                ontology_terms_loaded,
                1,
                "No active ontology terms were loaded.",
            )
        else:
            persist_validation(
                "ontology_terms_loaded",
                "passed",
                ontology_terms_loaded,
                1,
                "Active ontology terms loaded successfully.",
            )

        if canonical_edges_generated == 0:
            validation_failures += 1
            persist_validation(
                "canonical_edges_generated",
                "warning",
                canonical_edges_generated,
                1,
                "No canonical edges generated.",
            )
            status = "warning"
        else:
            persist_validation(
                "canonical_edges_generated",
                "passed",
                canonical_edges_generated,
                1,
                "Canonical edges generated successfully.",
            )
            status = "success"

        runtime_seconds = time.time() - started

        mapping_method_summary = summarize_mapping_methods(mapping_rows)

        persist_telemetry(
            build_telemetry_payload(
                status=status,
                raw_edges_loaded=raw_edges_loaded,
                raw_nodes_detected=raw_nodes_detected,
                ontology_terms_loaded=ontology_terms_loaded,
                aliases_loaded=aliases_loaded,
                mappings_generated=mappings_generated,
                canonical_edges_generated=canonical_edges_generated,
                validation_failures=validation_failures,
                runtime_seconds=runtime_seconds,
                details={
                    "mappings_persisted": mappings_persisted,
                    "canonical_edges_persisted": canonical_edges_persisted,
                    "mapping_method_summary": mapping_method_summary,
                    "min_mapping_confidence": MIN_MAPPING_CONFIDENCE,
                    "runtime_marker": "5A4_CANONICAL_STRUCTURAL_ONTOLOGY_V1",
                },
            )
        )

        print(f"raw_edges_loaded={raw_edges_loaded}")
        print(f"raw_nodes_detected={raw_nodes_detected}")
        print(f"ontology_terms_loaded={ontology_terms_loaded}")
        print(f"aliases_loaded={aliases_loaded}")
        print(f"mappings_generated={mappings_generated}")
        print(f"canonical_edges_generated={canonical_edges_generated}")
        print(f"mappings_persisted={mappings_persisted}")
        print(f"canonical_edges_persisted={canonical_edges_persisted}")
        print(f"mapping_method_summary={mapping_method_summary}")
        print(f"status={status}")

    except Exception as exc:
        runtime_seconds = time.time() - started
        error_message = str(exc)

        print(f"ERROR: {error_message}")

        try:
            persist_telemetry(
                build_telemetry_payload(
                    status="failed",
                    raw_edges_loaded=raw_edges_loaded,
                    raw_nodes_detected=raw_nodes_detected,
                    ontology_terms_loaded=ontology_terms_loaded,
                    aliases_loaded=aliases_loaded,
                    mappings_generated=mappings_generated,
                    canonical_edges_generated=canonical_edges_generated,
                    validation_failures=max(1, validation_failures),
                    runtime_seconds=runtime_seconds,
                    error_message=error_message,
                    details={
                        "mappings_persisted": mappings_persisted,
                        "canonical_edges_persisted": canonical_edges_persisted,
                        "min_mapping_confidence": MIN_MAPPING_CONFIDENCE,
                        "runtime_marker": "5A4_CANONICAL_STRUCTURAL_ONTOLOGY_V1",
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
