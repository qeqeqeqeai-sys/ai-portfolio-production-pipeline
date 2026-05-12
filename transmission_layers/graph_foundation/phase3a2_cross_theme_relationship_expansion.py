import json
import math
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from graph_supabase_client import SupabaseRestClient


PIPELINE_NAME = "PHASE_3A2_CROSS_THEME_RELATIONSHIP_EXPANSION"
SNAPSHOT_VERSION = "phase3a2_v1"

ANCHOR_THEME_NAME = os.getenv("ANCHOR_THEME_NAME", "ai").strip().lower()
THEME_NAME = os.getenv("THEME_NAME", ANCHOR_THEME_NAME).strip().lower()
MAX_EVIDENCE_ROWS = int(os.getenv("MAX_EVIDENCE_ROWS", "3000"))
MIN_EVIDENCE_SCORE = float(os.getenv("MIN_EVIDENCE_SCORE", "0"))

ALLOWED_NODE_TYPES = {
    "theme",
    "asset",
    "sector",
    "subsector",
    "macro_factor",
    "commodity",
    "supply_chain",
    "economic_actor",
    "risk_factor",
    "policy_factor",
    "other",
}

ALLOWED_EDGE_TYPES = {
    "influences",
    "benefits",
    "harms",
    "accelerates",
    "suppresses",
    "dependent_on",
    "correlated_with",
    "transmits_to",
    "exposes_to",
    "supplies",
    "consumes",
    "funds",
    "regulates",
    "other",
}

# Generic, deliberately non-AI-hardcoded taxonomy.
# AI is only the current anchor theme; the extraction logic works for any anchor.
RELATIONSHIP_TAXONOMY = {
    "theme": {
        "liquidity": ["liquidity", "money supply", "qe", "qt", "funding", "capital flow"],
        "interest_rates": ["interest rate", "rates", "fed", "fomc", "treasury yield", "yield"],
        "inflation": ["inflation", "cpi", "ppi", "pricing pressure"],
        "semiconductors": ["semiconductor", "chip", "gpu", "foundry", "tsmc", "fab", "memory"],
        "energy": ["energy", "power", "electricity", "grid", "natural gas", "oil", "brent"],
        "supply_chain": ["supply chain", "inventory", "shortage", "logistics", "supplier"],
        "geopolitics": ["geopolitical", "sanction", "tariff", "export control", "war"],
        "credit_stress": ["credit spread", "high yield", "default risk", "bbb spread", "credit stress"],
        "labor_disruption": ["labor", "wage", "employment", "job displacement", "productivity"],
        "regulation": ["regulation", "regulatory", "antitrust", "compliance", "policy"],
        "demographics": ["demographic", "aging", "population", "migration"],
    },
    "risk_factor": {
        "valuation_risk": ["valuation", "multiple", "overvalued", "expensive", "drawdown"],
        "earnings_risk": ["earnings risk", "margin pressure", "revenue risk", "profit warning"],
        "concentration_risk": ["concentration", "crowded", "mega cap", "narrow leadership"],
        "execution_risk": ["execution risk", "delivery risk", "implementation risk"],
        "funding_risk": ["funding risk", "refinancing", "debt burden", "capital market"],
        "regulatory_risk": ["regulatory risk", "antitrust risk", "compliance risk"],
        "geopolitical_risk": ["geopolitical risk", "sanction risk", "export control risk"],
    },
    "policy_factor": {
        "monetary_policy": ["fed", "fomc", "rate cut", "rate hike", "monetary policy"],
        "fiscal_policy": ["fiscal", "government spending", "deficit", "subsidy"],
        "industrial_policy": ["industrial policy", "chips act", "subsidies", "reshoring"],
        "regulatory_policy": ["regulation", "regulatory policy", "antitrust", "data privacy"],
        "trade_policy": ["tariff", "export control", "trade restriction", "sanction"],
    },
    "supply_chain": {
        "semiconductor_supply_chain": ["foundry", "fab", "gpu supply", "chip supply", "tsmc"],
        "data_center_supply_chain": ["data center", "server", "rack", "cooling", "networking"],
        "power_grid_supply_chain": ["grid", "transformer", "power equipment", "electricity demand"],
        "commodity_supply_chain": ["copper", "rare earth", "lithium", "commodity supply"],
        "logistics_supply_chain": ["shipping", "freight", "logistics", "port"],
    },
    "macro_factor": {
        "growth": ["growth", "gdp", "economic activity", "cycle"],
        "inflation": ["inflation", "cpi", "ppi"],
        "rates": ["rates", "yield", "treasury", "fed"],
        "liquidity": ["liquidity", "money supply", "qe", "qt"],
        "credit": ["credit", "spread", "default"],
        "energy_prices": ["oil", "brent", "wti", "natural gas", "electricity"],
        "usd": ["usd", "dollar", "dxy"],
    },
}


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_date_sgt() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def safe_float(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
    try:
        if value is None:
            return default
        number = float(value)
        if math.isnan(number) or math.isinf(number):
            return default
        return number
    except Exception:
        return default


def clamp01(value: Any) -> float:
    number = safe_float(value, 0.0) or 0.0
    if number > 1:
        number = number / 100.0
    return max(0.0, min(1.0, number))


def compact_text(value: Any, max_len: int = 2000) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list)):
        text = json.dumps(value, ensure_ascii=False)
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len]


def row_blob(row: Dict[str, Any]) -> str:
    values = []

    for field in [
        "evidence_title",
        "evidence_text",
        "evidence_type",
        "driver_category",
        "source_name",
        "ticker",
        "company",
        "sector",
        "subsector",
        "extracted_features",
        "raw_payload",
    ]:
        value = row.get(field)
        if value is None:
            continue
        values.append(compact_text(value, 3000))

    return " ".join(values).lower()


def make_node_key(node_type: str, value: Any) -> str:
    node_type = slug(node_type)
    if node_type not in ALLOWED_NODE_TYPES:
        node_type = "other"
    return f"{node_type}:{slug(value)}"


def make_edge_key(source_node_key: str, edge_type: str, target_node_key: str) -> str:
    return f"{source_node_key}__{slug(edge_type)}__{target_node_key}"


def relation_edge_type(node_type: str, driver_direction: Optional[str]) -> str:
    direction = slug(driver_direction)

    if node_type == "theme":
        return "transmits_to"

    if node_type == "policy_factor":
        return "regulates"

    if node_type == "supply_chain":
        return "dependent_on"

    if node_type == "risk_factor":
        if direction == "negative":
            return "exposes_to"
        return "influences"

    if node_type == "macro_factor":
        return "influences"

    return "other"


def directional_strength(driver_direction: Optional[str], evidence_score: float) -> float:
    direction = slug(driver_direction)
    score = clamp01(evidence_score)

    if direction == "negative":
        return -score
    if direction == "positive":
        return score
    if direction == "mixed":
        return 0.0
    return score * 0.35


def extract_relationship_candidates(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    blob = row_blob(row)

    source_theme = slug(row.get("theme_name") or THEME_NAME)
    source_node_key = make_node_key("theme", source_theme)

    evidence_score = clamp01(row.get("relevance_score") or row.get("confidence_score") or 50)
    confidence = clamp01(row.get("confidence_score") or evidence_score)
    direction = row.get("driver_direction")
    run_date = str(row.get("run_date_sgt") or run_date_sgt())

    candidates = []

    for node_type, taxonomy in RELATIONSHIP_TAXONOMY.items():
        for target_name, keywords in taxonomy.items():
            matched_keywords = [kw for kw in keywords if kw in blob]

            if not matched_keywords:
                continue

            target_node_key = make_node_key(node_type, target_name)
            edge_type = relation_edge_type(node_type, direction)

            if edge_type not in ALLOWED_EDGE_TYPES:
                edge_type = "other"

            candidates.append({
                "run_date_sgt": run_date,
                "anchor_theme_name": ANCHOR_THEME_NAME,
                "theme_name": source_theme,
                "source_node_key": source_node_key,
                "source_node_type": "theme",
                "source_node_label": source_theme,
                "target_node_key": target_node_key,
                "target_node_type": node_type,
                "target_node_label": target_name,
                "edge_type": edge_type,
                "direction": "directed",
                "evidence_score": evidence_score,
                "confidence_score": confidence,
                "directional_strength": directional_strength(direction, evidence_score),
                "driver_direction": direction,
                "matched_keywords": matched_keywords,
                "evidence_id": row.get("id"),
                "evidence_title": row.get("evidence_title"),
                "evidence_text": row.get("evidence_text"),
                "evidence_type": row.get("evidence_type"),
                "driver_category": row.get("driver_category"),
                "source_name": row.get("source_name"),
                "ticker": row.get("ticker"),
                "company": row.get("company"),
                "sector": row.get("sector"),
                "subsector": row.get("subsector"),
                "raw_payload": row,
            })

    return candidates


def aggregate_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped = defaultdict(list)

    for candidate in candidates:
        key = (
            candidate["source_node_key"],
            candidate["target_node_key"],
            candidate["edge_type"],
            candidate["theme_name"],
            candidate["anchor_theme_name"],
        )
        grouped[key].append(candidate)

    edges = []

    for key, items in grouped.items():
        source_node_key, target_node_key, edge_type, theme_name, anchor_theme_name = key

        evidence_count = len(items)
        avg_score = sum(i["evidence_score"] for i in items) / evidence_count
        avg_confidence = sum(i["confidence_score"] for i in items) / evidence_count
        avg_directional = sum(i["directional_strength"] for i in items) / evidence_count

        positive_count = sum(1 for i in items if slug(i.get("driver_direction")) == "positive")
        negative_count = sum(1 for i in items if slug(i.get("driver_direction")) == "negative")
        neutral_count = evidence_count - positive_count - negative_count

        keyword_count = len(set(k for i in items for k in i.get("matched_keywords", [])))
        keyword_density = min(1.0, keyword_count / 10.0)

        evidence_intensity = min(1.0, avg_score * (1 + math.log1p(evidence_count) / 4.0))
        confidence_score = min(1.0, 0.70 * avg_confidence + 0.30 * keyword_density)
        persistence_score = min(1.0, 0.30 + evidence_count / 25.0)

        edge_strength = (
            0.35 * avg_score
            + 0.25 * confidence_score
            + 0.20 * evidence_intensity
            + 0.10 * persistence_score
            + 0.10 * keyword_density
        )

        latest_date = max(str(i.get("run_date_sgt") or run_date_sgt()) for i in items)

        evidence_summary = {
            "source": "phase3a2_cross_theme_relationship_expansion",
            "matched_keywords": sorted(set(k for i in items for k in i.get("matched_keywords", [])))[:50],
            "source_names": sorted(set(str(i.get("source_name")) for i in items if i.get("source_name"))),
            "driver_categories": sorted(set(str(i.get("driver_category")) for i in items if i.get("driver_category"))),
            "sample_evidence": [
                {
                    "evidence_id": i.get("evidence_id"),
                    "evidence_type": i.get("evidence_type"),
                    "title": i.get("evidence_title"),
                    "text": compact_text(i.get("evidence_text"), 500),
                    "ticker": i.get("ticker"),
                    "score": i.get("evidence_score"),
                    "direction": i.get("driver_direction"),
                    "matched_keywords": i.get("matched_keywords"),
                }
                for i in items[:10]
            ],
        }

        edge_metadata = {
            "phase": "3A.2",
            "pipeline_name": PIPELINE_NAME,
            "relationship_family": "cross_theme",
            "latest_evidence_date": latest_date,
            "keyword_count": keyword_count,
            "keyword_density": keyword_density,
        }

        edges.append({
            "edge_key": make_edge_key(source_node_key, edge_type, target_node_key),
            "source_node_key": source_node_key,
            "target_node_key": target_node_key,
            "source_node_type": items[0]["source_node_type"],
            "target_node_type": items[0]["target_node_type"],
            "edge_type": edge_type,
            "direction": "directed",
            "theme_name": theme_name,
            "anchor_theme_name": anchor_theme_name,
            "edge_strength": round(clamp01(edge_strength), 6),
            "directional_strength": round(max(-1.0, min(1.0, avg_directional)), 6),
            "confidence_score": round(clamp01(confidence_score), 6),
            "evidence_intensity": round(clamp01(evidence_intensity), 6),
            "persistence_score": round(clamp01(persistence_score), 6),
            "evidence_count": evidence_count,
            "positive_evidence_count": positive_count,
            "negative_evidence_count": negative_count,
            "neutral_evidence_count": neutral_count,
            "last_seen_run_date_sgt": latest_date,
            "edge_metadata": edge_metadata,
            "evidence_summary": evidence_summary,
            "is_active": True,
            "updated_at": utc_now_iso(),
        })

    return edges


def build_nodes(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes = {}

    for item in candidates:
        run_date = item.get("run_date_sgt") or run_date_sgt()
        theme_name = item["theme_name"]

        source_key = item["source_node_key"]
        nodes[source_key] = {
            "node_key": source_key,
            "node_type": "theme",
            "node_label": item["source_node_label"],
            "theme_name": theme_name,
            "entity": item["source_node_label"],
            "sector": None,
            "subsector": None,
            "asset_class": None,
            "node_metadata": {
                "phase": "3A.2",
                "source": "cross_theme_relationship_expansion",
                "role": "source_theme",
            },
            "is_active": True,
            "last_seen_run_date_sgt": run_date,
            "updated_at": utc_now_iso(),
        }

        target_key = item["target_node_key"]
        target_type = item["target_node_type"]

        nodes[target_key] = {
            "node_key": target_key,
            "node_type": target_type,
            "node_label": item["target_node_label"],
            "theme_name": theme_name if target_type == "theme" else None,
            "entity": item["target_node_label"],
            "sector": None,
            "subsector": None,
            "asset_class": None,
            "node_metadata": {
                "phase": "3A.2",
                "source": "cross_theme_relationship_expansion",
                "role": "cross_theme_target",
                "target_type": target_type,
            },
            "is_active": True,
            "last_seen_run_date_sgt": run_date,
            "updated_at": utc_now_iso(),
        }

    return list(nodes.values())


def validate_edges(edges: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    errors = []
    warnings = []

    if not edges:
        warnings.append("No cross-theme edges generated.")

    for edge in edges:
        required = [
            "edge_key",
            "source_node_key",
            "target_node_key",
            "source_node_type",
            "target_node_type",
            "edge_type",
        ]

        for col in required:
            if not edge.get(col):
                errors.append(f"Missing {col}: {edge}")

        if edge.get("source_node_key") == edge.get("target_node_key"):
            errors.append(f"Self-loop edge generated: {edge.get('edge_key')}")

        if edge.get("edge_type") not in ALLOWED_EDGE_TYPES:
            errors.append(f"Invalid edge_type: {edge.get('edge_type')}")

        if edge.get("source_node_type") not in ALLOWED_NODE_TYPES:
            errors.append(f"Invalid source_node_type: {edge.get('source_node_type')}")

        if edge.get("target_node_type") not in ALLOWED_NODE_TYPES:
            errors.append(f"Invalid target_node_type: {edge.get('target_node_type')}")

        for metric in ["edge_strength", "confidence_score", "evidence_intensity", "persistence_score"]:
            value = safe_float(edge.get(metric), None)
            if value is None or value < 0 or value > 1:
                errors.append(f"{metric} out of range for {edge.get('edge_key')}: {value}")

        directional = safe_float(edge.get("directional_strength"), None)
        if directional is None or directional < -1 or directional > 1:
            errors.append(f"directional_strength out of range for {edge.get('edge_key')}: {directional}")

    if errors:
        return "failed", errors, warnings

    if warnings:
        return "warning", errors, warnings

    return "passed", errors, warnings


def snapshot_id_for() -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{SNAPSHOT_VERSION}_{ANCHOR_THEME_NAME}_{timestamp}"


def create_snapshot(
    client: SupabaseRestClient,
    *,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
) -> str:
    snapshot_id = snapshot_id_for()

    active_nodes = [n for n in nodes if n.get("is_active", True)]
    active_edges = [e for e in edges if e.get("is_active", True)]

    def count_nodes(node_type: str) -> int:
        return sum(1 for n in active_nodes if n.get("node_type") == node_type)

    def avg_metric(metric: str) -> Optional[float]:
        values = [safe_float(e.get(metric), 0.0) or 0.0 for e in active_edges]
        if not values:
            return None
        return round(sum(values) / len(values), 6)

    snapshot = {
        "snapshot_id": snapshot_id,
        "snapshot_version": SNAPSHOT_VERSION,
        "run_date_sgt": run_date_sgt(),
        "graph_scope": "multi_theme",
        "anchor_theme_name": ANCHOR_THEME_NAME,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "active_node_count": len(active_nodes),
        "active_edge_count": len(active_edges),
        "theme_node_count": count_nodes("theme"),
        "asset_node_count": count_nodes("asset"),
        "sector_node_count": count_nodes("sector"),
        "subsector_node_count": count_nodes("subsector"),
        "macro_factor_node_count": count_nodes("macro_factor"),
        "avg_edge_strength": avg_metric("edge_strength"),
        "avg_confidence_score": avg_metric("confidence_score"),
        "avg_evidence_intensity": avg_metric("evidence_intensity"),
        "avg_persistence_score": avg_metric("persistence_score"),
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "checkpoint_status": "validated" if validation_status in {"passed", "warning"} else "failed",
        "snapshot_metadata": {
            "phase": "3A.2",
            "pipeline_name": PIPELINE_NAME,
            "relationship_family": "cross_theme",
        },
    }

    client.insert("structural_theme_graph_snapshots", [snapshot])
    return snapshot_id


def insert_edge_history(client: SupabaseRestClient, *, snapshot_id: str, edges: List[Dict[str, Any]]) -> int:
    rows = []

    for edge in edges:
        rows.append({
            "snapshot_id": snapshot_id,
            "run_date_sgt": run_date_sgt(),
            "edge_key": edge["edge_key"],
            "source_node_key": edge["source_node_key"],
            "target_node_key": edge["target_node_key"],
            "edge_type": edge["edge_type"],
            "theme_name": edge.get("theme_name"),
            "anchor_theme_name": edge.get("anchor_theme_name"),
            "edge_strength": edge.get("edge_strength"),
            "directional_strength": edge.get("directional_strength"),
            "confidence_score": edge.get("confidence_score"),
            "evidence_intensity": edge.get("evidence_intensity"),
            "persistence_score": edge.get("persistence_score"),
            "evidence_count": edge.get("evidence_count"),
            "edge_metadata": edge.get("edge_metadata") or {},
            "evidence_summary": edge.get("evidence_summary") or {},
        })

    client.upsert(
        "structural_theme_graph_edge_history",
        rows,
        on_conflict="snapshot_id,edge_key",
        return_rows=False,
    )

    return len(rows)


def write_telemetry(
    client: SupabaseRestClient,
    *,
    status: str,
    snapshot_id: Optional[str],
    nodes_upserted: int,
    edges_upserted: int,
    history_rows: int,
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
    runtime_seconds: float,
    error_message: Optional[str],
    metadata: Dict[str, Any],
):
    client.insert("structural_theme_graph_telemetry", [{
        "pipeline_name": PIPELINE_NAME,
        "snapshot_id": snapshot_id,
        "snapshot_version": SNAPSHOT_VERSION,
        "status": status,
        "nodes_upserted": nodes_upserted,
        "edges_upserted": edges_upserted,
        "edge_history_rows_inserted": history_rows,
        "validation_status": validation_status,
        "validation_error_count": len(validation_errors),
        "validation_warning_count": len(validation_warnings),
        "runtime_seconds": round(runtime_seconds, 3),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "error_message": error_message,
        "telemetry_metadata": metadata,
    }], return_rows=False)

    client.insert("structural_theme_cross_theme_relationship_runs", [{
        "anchor_theme_name": ANCHOR_THEME_NAME,
        "status": status,
        "evidence_rows_read": metadata.get("evidence_rows_read", 0),
        "candidates_generated": metadata.get("candidates_generated", 0),
        "nodes_upserted": nodes_upserted,
        "edges_upserted": edges_upserted,
        "edge_history_rows_inserted": history_rows,
        "snapshot_id": snapshot_id,
        "validation_status": validation_status,
        "validation_error_count": len(validation_errors),
        "validation_warning_count": len(validation_warnings),
        "runtime_seconds": round(runtime_seconds, 3),
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
        "error_message": error_message,
        "metadata": metadata,
    }], return_rows=False)


def fetch_evidence_rows(client: SupabaseRestClient) -> List[Dict[str, Any]]:
    filters = {
        "theme_name": f"eq.{THEME_NAME}",
    }

    rows = client.select(
        "structural_theme_evidence",
        columns="*",
        filters=filters,
        order="run_date_sgt.desc",
        limit=MAX_EVIDENCE_ROWS,
    )

    filtered = []
    for row in rows:
        score = safe_float(row.get("relevance_score"), 0.0) or 0.0
        if score >= MIN_EVIDENCE_SCORE:
            filtered.append(row)

    return filtered


def main():
    start = time.time()
    client = SupabaseRestClient()

    snapshot_id = None
    validation_status = "failed"
    validation_errors: List[str] = []
    validation_warnings: List[str] = []

    try:
        evidence_rows = fetch_evidence_rows(client)

        candidates = []
        for row in evidence_rows:
            candidates.extend(extract_relationship_candidates(row))

        edges = aggregate_candidates(candidates)
        nodes = build_nodes(candidates)

        validation_status, validation_errors, validation_warnings = validate_edges(edges)

        if validation_status == "failed":
            raise RuntimeError("Cross-theme relationship validation failed: " + " | ".join(validation_errors[:10]))

        if nodes:
            client.upsert(
                "structural_theme_graph_nodes",
                nodes,
                on_conflict="node_key",
                return_rows=False,
            )

        if edges:
            client.upsert(
                "structural_theme_graph_edges",
                edges,
                on_conflict="edge_key",
                return_rows=False,
            )

        snapshot_id = create_snapshot(
            client,
            nodes=nodes,
            edges=edges,
            validation_status=validation_status,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
        )

        history_count = insert_edge_history(
            client,
            snapshot_id=snapshot_id,
            edges=edges,
        )

        status = "success" if validation_status == "passed" else "warning"

        metadata = {
            "phase": "3A.2",
            "evidence_rows_read": len(evidence_rows),
            "candidates_generated": len(candidates),
            "nodes_generated": len(nodes),
            "edges_generated": len(edges),
            "taxonomy_node_types": list(RELATIONSHIP_TAXONOMY.keys()),
            "anchor_theme_name": ANCHOR_THEME_NAME,
            "theme_name": THEME_NAME,
        }

        write_telemetry(
            client,
            status=status,
            snapshot_id=snapshot_id,
            nodes_upserted=len(nodes),
            edges_upserted=len(edges),
            history_rows=history_count,
            validation_status=validation_status,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            runtime_seconds=time.time() - start,
            error_message=None,
            metadata=metadata,
        )

        print("Phase 3A.2 Cross-Theme Relationship Expansion completed.")
        print(f"Evidence rows read: {len(evidence_rows)}")
        print(f"Candidates generated: {len(candidates)}")
        print(f"Nodes: {len(nodes)}")
        print(f"Edges: {len(edges)}")
        print(f"Snapshot: {snapshot_id}")
        print(f"Validation: {validation_status}")

    except Exception as exc:
        metadata = {
            "phase": "3A.2",
            "anchor_theme_name": ANCHOR_THEME_NAME,
            "theme_name": THEME_NAME,
        }

        write_telemetry(
            client,
            status="failed",
            snapshot_id=snapshot_id,
            nodes_upserted=0,
            edges_upserted=0,
            history_rows=0,
            validation_status="failed",
            validation_errors=[str(exc)],
            validation_warnings=[],
            runtime_seconds=time.time() - start,
            error_message=str(exc),
            metadata=metadata,
        )

        raise


if __name__ == "__main__":
    main()
