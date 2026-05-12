import json
import math
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from graph_supabase_client import SupabaseRestClient


PIPELINE_NAME = "PHASE_3A_EVIDENCE_GRAPH_EXPANSION"
SNAPSHOT_VERSION = "phase3a_v1"

DEFAULT_THEME_NAME = os.getenv("THEME_NAME", "ai").strip().lower()
ANCHOR_THEME_NAME = os.getenv("ANCHOR_THEME_NAME", "ai").strip().lower()

MAX_ROWS_PER_SOURCE = int(os.getenv("MAX_ROWS_PER_SOURCE", "1000"))

SOURCE_TABLES = [
    "structural_theme_evidence",
    "structural_theme_explanations",
    "ai_transmission_scores",
    "structural_theme_scores",
]

TABLE_MAPPINGS = {
    "structural_theme_evidence": {
        "theme": "theme_name",
        "ticker": "ticker",
        "company": "company",
        "sector": "sector",
        "subsector": "subsector",
        "title": "evidence_title",
        "text": "evidence_text",
        "score_fields": ["relevance_score", "confidence_score", "sentiment_score"],
        "direction": "driver_direction",
        "date": "run_date_sgt",
        "source_url": "source_url",
        "source_name": "source_name",
        "raw_payload": "raw_payload",
    },
    "structural_theme_explanations": {
        "theme": "theme_name",
        "ticker": "ticker",
        "company": "company",
        "sector": "sector",
        "subsector": "subsector",
        "title": None,
        "text": "evidence_summary",
        "score_fields": ["final_score", "confidence_score"],
        "direction": None,
        "date": "run_date_sgt",
        "source_url": None,
        "source_name": None,
        "raw_payload": "metadata",
    },
    "ai_transmission_scores": {
        "theme": None,
        "ticker": "ticker",
        "company": "company",
        "sector": "sector",
        "subsector": "subsector",
        "title": None,
        "text": None,
        "score_fields": [
            "transmission_score",
            "ai_transmission_score",
            "overall_score",
            "final_score",
            "confidence_score",
        ],
        "direction": None,
        "date": "run_date_sgt",
        "fallback_theme": "ai",
        "source_url": None,
        "source_name": None,
        "raw_payload": None,
    },
    "structural_theme_scores": {
        "theme": "theme_name",
        "ticker": "ticker",
        "company": "company",
        "sector": "sector",
        "subsector": "subsector",
        "title": None,
        "text": None,
        "score_fields": [
            "theme_score",
            "structural_theme_score",
            "overall_score",
            "final_score",
            "confidence_score",
        ],
        "direction": None,
        "date": "run_date_sgt",
        "source_url": None,
        "source_name": None,
        "raw_payload": None,
    },
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

MACRO_KEYWORDS = {
    "interest_rates": ["interest rate", "rates", "fed", "fomc", "us10y", "treasury yield", "bond yield"],
    "inflation": ["inflation", "cpi", "ppi", "prices"],
    "liquidity": ["liquidity", "money supply", "m2", "quantitative easing", "quantitative tightening"],
    "credit_stress": ["credit spread", "high yield", "bbb spread", "default risk"],
    "energy_prices": ["oil", "brent", "wti", "natural gas", "energy price"],
    "usd_strength": ["dollar", "usd", "dxy"],
    "labor_disruption": ["labor", "employment", "wages", "jobless", "unemployment"],
    "regulation": ["regulation", "regulatory", "antitrust", "policy", "compliance"],
    "geopolitics": ["geopolitical", "war", "sanction", "tariff", "export control"],
    "supply_chain": ["supply chain", "shortage", "inventory", "logistics"],
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


def safe_number(value: Any, default: Optional[float] = 0.0) -> Optional[float]:
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
    number = safe_number(value, 0.0)
    if number is None:
        return 0.0
    if number > 1:
        number = number / 100.0
    return max(0.0, min(1.0, number))


def signed_direction(direction: Optional[str], score: float) -> float:
    direction_norm = slug(direction)

    if direction_norm in {"negative", "harm", "harms", "bearish", "risk", "down"}:
        return -score

    if direction_norm in {"positive", "benefit", "benefits", "bullish", "up"}:
        return score

    if direction_norm in {"mixed"}:
        return 0.0

    return score


def edge_type_from_direction(direction: Optional[str], target_node_type: str) -> str:
    direction_norm = slug(direction)

    if direction_norm in {"positive", "benefit", "benefits", "bullish", "up"}:
        return "benefits"

    if direction_norm in {"negative", "harm", "harms", "bearish", "risk", "down"}:
        return "harms"

    if target_node_type in {"asset", "sector", "subsector"}:
        return "exposes_to"

    if target_node_type in {"macro_factor", "risk_factor", "policy_factor"}:
        return "influences"

    if target_node_type == "theme":
        return "transmits_to"

    return "other"


def get_first(row: Dict[str, Any], candidates: Iterable[Optional[str]]) -> Any:
    for col in candidates:
        if col and col in row and row.get(col) not in (None, ""):
            return row.get(col)
    return None


def row_theme(table: str, row: Dict[str, Any]) -> str:
    mapping = TABLE_MAPPINGS[table]
    theme_col = mapping.get("theme")
    fallback = mapping.get("fallback_theme") or DEFAULT_THEME_NAME
    return slug(row.get(theme_col) if theme_col else fallback)


def row_date(table: str, row: Dict[str, Any]) -> str:
    mapping = TABLE_MAPPINGS[table]
    date_col = mapping.get("date")
    return str(row.get(date_col) or run_date_sgt())


def row_score(table: str, row: Dict[str, Any]) -> float:
    mapping = TABLE_MAPPINGS[table]
    score_fields = mapping.get("score_fields") or []
    values = []

    for field in score_fields:
        value = row.get(field)
        if value is not None:
            values.append(clamp01(value))

    if not values:
        return 0.5

    return round(sum(values) / len(values), 6)


def row_text(table: str, row: Dict[str, Any]) -> str:
    mapping = TABLE_MAPPINGS[table]

    values = []
    for key in [
        mapping.get("ticker"),
        mapping.get("company"),
        mapping.get("sector"),
        mapping.get("subsector"),
        mapping.get("title"),
        mapping.get("text"),
        mapping.get("source_name"),
    ]:
        if key and row.get(key):
            values.append(str(row.get(key)))

    for generic_key in [
        "top_positive_drivers",
        "top_negative_drivers",
        "component_decomposition",
        "transmission_pathways",
        "metadata",
        "raw_payload",
    ]:
        if generic_key in row and row.get(generic_key):
            try:
                values.append(json.dumps(row.get(generic_key)))
            except Exception:
                values.append(str(row.get(generic_key)))

    return " ".join(values).lower()


def make_node_key(node_type: str, value: Any) -> str:
    node_type = slug(node_type)
    if node_type not in ALLOWED_NODE_TYPES:
        node_type = "other"
    return f"{node_type}:{slug(value)}"


def make_edge_key(source_node_key: str, edge_type: str, target_node_key: str) -> str:
    return f"{source_node_key}__{slug(edge_type)}__{target_node_key}"


def extract_macro_factors(table: str, row: Dict[str, Any]) -> List[str]:
    blob = row_text(table, row)
    factors = []

    for factor, keywords in MACRO_KEYWORDS.items():
        if any(keyword in blob for keyword in keywords):
            factors.append(factor)

    return sorted(set(factors))


def generate_candidates(table: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mapping = TABLE_MAPPINGS[table]
    candidates = []

    for row in rows:
        theme = row_theme(table, row)
        score = row_score(table, row)
        date_value = row_date(table, row)
        direction_col = mapping.get("direction")
        direction = row.get(direction_col) if direction_col else None

        source_node_key = make_node_key("theme", theme)

        ticker = row.get(mapping.get("ticker")) if mapping.get("ticker") else None
        company = row.get(mapping.get("company")) if mapping.get("company") else None
        sector = row.get(mapping.get("sector")) if mapping.get("sector") else None
        subsector = row.get(mapping.get("subsector")) if mapping.get("subsector") else None

        raw_payload_col = mapping.get("raw_payload")
        raw_payload = row.get(raw_payload_col) if raw_payload_col else None

        evidence_title = row.get(mapping.get("title")) if mapping.get("title") else None
        evidence_text = row.get(mapping.get("text")) if mapping.get("text") else None
        source_url = row.get(mapping.get("source_url")) if mapping.get("source_url") else None
        source_name = row.get(mapping.get("source_name")) if mapping.get("source_name") else None

        target_items = []

        if sector:
            target_items.append(("sector", sector))
        if subsector:
            target_items.append(("subsector", subsector))
        if ticker:
            target_items.append(("asset", ticker))

        for macro_factor in extract_macro_factors(table, row):
            target_items.append(("macro_factor", macro_factor))

        for target_node_type, target_value in target_items:
            target_node_key = make_node_key(target_node_type, target_value)
            edge_type = edge_type_from_direction(direction, target_node_type)

            if edge_type not in ALLOWED_EDGE_TYPES:
                edge_type = "other"

            directional_strength = signed_direction(direction, score)

            candidates.append({
                "run_date_sgt": date_value,
                "theme_name": theme,
                "anchor_theme_name": ANCHOR_THEME_NAME,
                "source_node_key": source_node_key,
                "source_node_type": "theme",
                "source_node_label": theme,
                "target_node_key": target_node_key,
                "target_node_type": target_node_type,
                "target_node_label": str(target_value),
                "edge_type": edge_type,
                "direction": "directed",
                "evidence_source_table": table,
                "evidence_record_id": str(row.get("id") or ""),
                "evidence_title": evidence_title,
                "evidence_text": evidence_text,
                "evidence_url": source_url,
                "source_name": source_name,
                "evidence_score": score,
                "directional_score": directional_strength,
                "driver_direction": direction,
                "ticker": ticker,
                "company": company,
                "sector": sector,
                "subsector": subsector,
                "raw_payload": raw_payload if raw_payload is not None else row,
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
        scores = [safe_number(i["evidence_score"], 0.0) or 0.0 for i in items]
        signed_scores = [safe_number(i["directional_score"], 0.0) or 0.0 for i in items]

        avg_score = sum(scores) / evidence_count if evidence_count else 0.0
        avg_signed = sum(signed_scores) / evidence_count if evidence_count else 0.0

        positive_count = sum(1 for i in items if slug(i.get("driver_direction")) == "positive")
        negative_count = sum(1 for i in items if slug(i.get("driver_direction")) == "negative")
        neutral_count = evidence_count - positive_count - negative_count

        evidence_intensity = min(1.0, avg_score * (1.0 + math.log1p(evidence_count) / 4.0))
        confidence_score = min(1.0, avg_score * (0.75 + min(evidence_count, 10) / 40.0))
        persistence_score = min(1.0, 0.35 + evidence_count / 20.0)

        edge_strength = (
            0.40 * avg_score
            + 0.25 * confidence_score
            + 0.20 * evidence_intensity
            + 0.15 * persistence_score
        )

        latest_date = max(str(i.get("run_date_sgt") or run_date_sgt()) for i in items)

        sample_items = items[:10]

        evidence_summary = {
            "source_tables": sorted(set(i["evidence_source_table"] for i in items)),
            "sample_evidence": [
                {
                    "table": i.get("evidence_source_table"),
                    "record_id": i.get("evidence_record_id"),
                    "title": i.get("evidence_title"),
                    "text": str(i.get("evidence_text") or "")[:500],
                    "url": i.get("evidence_url"),
                    "score": i.get("evidence_score"),
                    "direction": i.get("driver_direction"),
                }
                for i in sample_items
            ],
        }

        edge_metadata = {
            "phase": "3A",
            "pipeline_name": PIPELINE_NAME,
            "aggregation_method": "weighted_evidence_mean",
            "latest_evidence_date": latest_date,
        }

        edge = {
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
            "directional_strength": round(max(-1.0, min(1.0, avg_signed)), 6),
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
        }

        edges.append(edge)

    return edges


def build_nodes(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    nodes: Dict[str, Dict[str, Any]] = {}

    for item in candidates:
        run_date = item.get("run_date_sgt") or run_date_sgt()
        theme_name = item["theme_name"]

        source_node_key = item["source_node_key"]
        nodes[source_node_key] = {
            "node_key": source_node_key,
            "node_type": "theme",
            "node_label": item["source_node_label"],
            "theme_name": theme_name,
            "entity": item["source_node_label"],
            "sector": None,
            "subsector": None,
            "asset_class": None,
            "node_metadata": {
                "phase": "3A",
                "source": "evidence_graph_expansion",
            },
            "is_active": True,
            "last_seen_run_date_sgt": run_date,
            "updated_at": utc_now_iso(),
        }

        target_node_key = item["target_node_key"]
        target_type = item["target_node_type"]

        nodes[target_node_key] = {
            "node_key": target_node_key,
            "node_type": target_type,
            "node_label": item["target_node_label"],
            "theme_name": theme_name,
            "entity": item.get("company") or item.get("ticker") or item["target_node_label"],
            "sector": item.get("sector"),
            "subsector": item.get("subsector"),
            "asset_class": "equity" if target_type == "asset" else None,
            "node_metadata": {
                "phase": "3A",
                "source": "evidence_graph_expansion",
                "ticker": item.get("ticker"),
                "company": item.get("company"),
            },
            "is_active": True,
            "last_seen_run_date_sgt": run_date,
            "updated_at": utc_now_iso(),
        }

    return list(nodes.values())


def build_edge_evidence_rows(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for item in candidates:
        rows.append({
            "run_date_sgt": item.get("run_date_sgt") or run_date_sgt(),
            "theme_name": item["theme_name"],
            "source_node_key": item["source_node_key"],
            "target_node_key": item["target_node_key"],
            "source_node_type": item["source_node_type"],
            "target_node_type": item["target_node_type"],
            "edge_type": item["edge_type"],
            "evidence_source_table": item["evidence_source_table"],
            "evidence_record_id": item["evidence_record_id"],
            "evidence_title": item.get("evidence_title"),
            "evidence_text": item.get("evidence_text"),
            "evidence_url": item.get("evidence_url"),
            "evidence_score": item.get("evidence_score"),
            "directional_score": item.get("directional_score"),
            "driver_direction": item.get("driver_direction"),
            "raw_payload": item.get("raw_payload"),
            "created_at": utc_now_iso(),
        })

    return rows


def validate_edges(edges: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    errors = []
    warnings = []

    if not edges:
        warnings.append("No graph edges generated.")

    for edge in edges:
        for col in [
            "edge_key",
            "source_node_key",
            "target_node_key",
            "source_node_type",
            "target_node_type",
            "edge_type",
        ]:
            if not edge.get(col):
                errors.append(f"Missing required edge column {col}: {edge}")

        if edge.get("source_node_key") == edge.get("target_node_key"):
            errors.append(f"Self-loop edge generated: {edge.get('edge_key')}")

        if edge.get("edge_type") not in ALLOWED_EDGE_TYPES:
            errors.append(f"Invalid edge_type {edge.get('edge_type')} for {edge.get('edge_key')}")

        if edge.get("source_node_type") not in ALLOWED_NODE_TYPES:
            errors.append(f"Invalid source_node_type {edge.get('source_node_type')} for {edge.get('edge_key')}")

        if edge.get("target_node_type") not in ALLOWED_NODE_TYPES:
            errors.append(f"Invalid target_node_type {edge.get('target_node_type')} for {edge.get('edge_key')}")

        for metric in ["edge_strength", "confidence_score", "evidence_intensity", "persistence_score"]:
            value = safe_number(edge.get(metric), None)
            if value is None or value < 0 or value > 1:
                errors.append(f"{metric} out of range for {edge.get('edge_key')}: {value}")

        directional = safe_number(edge.get("directional_strength"), None)
        if directional is None or directional < -1 or directional > 1:
            errors.append(f"directional_strength out of range for {edge.get('edge_key')}: {directional}")

    if errors:
        return "failed", errors, warnings

    if warnings:
        return "warning", errors, warnings

    return "passed", errors, warnings


def snapshot_id_for(theme_name: str) -> str:
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{SNAPSHOT_VERSION}_{theme_name}_{timestamp}"


def create_snapshot(
    client: SupabaseRestClient,
    *,
    theme_name: str,
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
) -> str:
    snapshot_id = snapshot_id_for(theme_name)

    active_nodes = [n for n in nodes if n.get("is_active", True)]
    active_edges = [e for e in edges if e.get("is_active", True)]

    def count_nodes(node_type: str) -> int:
        return sum(1 for n in active_nodes if n.get("node_type") == node_type)

    def avg_metric(metric: str) -> Optional[float]:
        values = [safe_number(e.get(metric), 0.0) or 0.0 for e in active_edges]
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
            "phase": "3A",
            "pipeline_name": PIPELINE_NAME,
            "source_tables": SOURCE_TABLES,
        },
    }

    client.insert("structural_theme_graph_snapshots", [snapshot])

    return snapshot_id


def insert_edge_history(
    client: SupabaseRestClient,
    *,
    snapshot_id: str,
    edges: List[Dict[str, Any]],
) -> int:
    history_rows = []

    for edge in edges:
        history_rows.append({
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
        history_rows,
        on_conflict="snapshot_id,edge_key",
        return_rows=False,
    )

    return len(history_rows)


def write_graph_telemetry(
    client: SupabaseRestClient,
    *,
    status: str,
    snapshot_id: Optional[str],
    nodes_upserted: int,
    edges_upserted: int,
    history_rows: int,
    validation_status: Optional[str],
    validation_errors: List[str],
    validation_warnings: List[str],
    runtime_seconds: float,
    error_message: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    telemetry = {
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
        "telemetry_metadata": metadata or {},
    }

    client.insert("structural_theme_graph_telemetry", [telemetry], return_rows=False)


def fetch_rows_for_source(client: SupabaseRestClient, table: str) -> List[Dict[str, Any]]:
    mapping = TABLE_MAPPINGS[table]
    date_col = mapping.get("date") or "run_date_sgt"

    filters = {}

    theme_col = mapping.get("theme")
    if theme_col:
        filters[theme_col] = f"eq.{DEFAULT_THEME_NAME}"

    return client.select(
        table,
        columns="*",
        filters=filters,
        order=f"{date_col}.desc",
        limit=MAX_ROWS_PER_SOURCE,
    )


def main():
    start = time.time()
    client = SupabaseRestClient()

    all_candidates: List[Dict[str, Any]] = []
    source_counts = {}
    snapshot_id = None

    try:
        for table in SOURCE_TABLES:
            try:
                rows = fetch_rows_for_source(client, table)
                source_counts[table] = len(rows)
                generated = generate_candidates(table, rows)
                all_candidates.extend(generated)
                print(f"{table}: rows={len(rows)}, candidates={len(generated)}")
            except Exception as exc:
                source_counts[table] = f"skipped: {exc}"
                print(f"WARNING: skipped {table}: {exc}")

        evidence_rows = build_edge_evidence_rows(all_candidates)

        if evidence_rows:
            client.insert(
                "structural_theme_graph_edge_evidence",
                evidence_rows,
                return_rows=False,
            )

        edges = aggregate_candidates(all_candidates)
        nodes = build_nodes(all_candidates)

        validation_status, validation_errors, validation_warnings = validate_edges(edges)

        if validation_status == "failed":
            raise RuntimeError("Graph validation failed: " + " | ".join(validation_errors[:10]))

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
            theme_name=DEFAULT_THEME_NAME,
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

        write_graph_telemetry(
            client,
            status="success" if validation_status == "passed" else "warning",
            snapshot_id=snapshot_id,
            nodes_upserted=len(nodes),
            edges_upserted=len(edges),
            history_rows=history_count,
            validation_status=validation_status,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            runtime_seconds=time.time() - start,
            metadata={
                "candidate_count": len(all_candidates),
                "evidence_rows_inserted": len(evidence_rows),
                "source_counts": source_counts,
            },
        )

        print("Phase 3A Evidence Graph Expansion completed.")
        print(f"Candidates: {len(all_candidates)}")
        print(f"Nodes: {len(nodes)}")
        print(f"Edges: {len(edges)}")
        print(f"Snapshot: {snapshot_id}")
        print(f"Validation: {validation_status}")

    except Exception as exc:
        write_graph_telemetry(
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
            metadata={
                "candidate_count": len(all_candidates),
                "source_counts": source_counts,
            },
        )
        raise


if __name__ == "__main__":
    main()
