"""
Phase 5A.2 — Structural Intermediary Formation Engine.

Detects semantic-key nodes that are both downstream targets and upstream sources,
then persists reusable intermediary transmission hubs.
"""
from __future__ import annotations

import argparse
import os
import sys
import time
import uuid
from collections import Counter, defaultdict
from typing import Any

from intermediary_classification import classify_intermediary
from intermediary_normalization import canonical_name, collect_normalized_forms, normalize_text
from intermediary_scoring import calculate_scores
from intermediary_telemetry import persist_telemetry, persist_validations
from intermediary_utils import SupabaseClient, today_sgt_iso
from intermediary_validation import build_validation_rows

DEFAULT_EDGE_TABLES = [
    "structural_theme_graph_edges",
    "structural_theme_graph_continuity_edges",
    "structural_theme_graph_two_hop_edges",
    "structural_theme_graph_transmission_edges",
]


def _first_present(row: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return None


def load_edges(client: SupabaseClient, table_names: list[str], limit_per_table: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    all_edges: list[dict[str, Any]] = []
    diagnostics: dict[str, Any] = {"tables": {}}
    select_cols = "select=source_node_key,target_node_key,source_theme,target_theme,theme_name,evidence_count,edge_weight,confidence_score,run_date_sgt"
    for table in table_names:
        try:
            rows = client.select(table, query=select_cols, limit=limit_per_table)
            normalized = []
            for r in rows:
                src = _first_present(r, ["source_node_key", "source_key", "source", "source_node"])
                tgt = _first_present(r, ["target_node_key", "target_key", "target", "target_node"])
                if src and tgt:
                    normalized.append({**r, "_source": str(src), "_target": str(tgt), "_edge_table": table})
            all_edges.extend(normalized)
            diagnostics["tables"][table] = {"status": "loaded", "rows": len(normalized)}
        except Exception as exc:  # noqa: BLE001
            diagnostics["tables"][table] = {"status": "skipped", "error": str(exc)}
    return all_edges, diagnostics


def detect_intermediaries(edges: list[dict[str, Any]], run_date_sgt: str, min_inbound: int, min_outbound: int) -> list[dict[str, Any]]:
    inbound: Counter[str] = Counter()
    outbound: Counter[str] = Counter()
    inbound_forms: defaultdict[str, list[str]] = defaultdict(list)
    outbound_forms: defaultdict[str, list[str]] = defaultdict(list)
    source_themes: defaultdict[str, set[str]] = defaultdict(set)
    target_themes: defaultdict[str, set[str]] = defaultdict(set)
    evidence_values: defaultdict[str, list[float]] = defaultdict(list)

    for edge in edges:
        raw_src = edge["_source"]
        raw_tgt = edge["_target"]
        src = normalize_text(raw_src)
        tgt = normalize_text(raw_tgt)
        if not src or not tgt or src == tgt:
            continue

        outbound[src] += 1
        inbound[tgt] += 1
        outbound_forms[src].append(raw_src)
        inbound_forms[tgt].append(raw_tgt)

        theme = str(edge.get("theme_name") or edge.get("source_theme") or "unknown")
        source_themes[src].add(theme)
        target_themes[tgt].add(str(edge.get("target_theme") or theme))

        evidence_count = edge.get("evidence_count")
        confidence = edge.get("confidence_score") or edge.get("edge_weight")
        try:
            evidence_values[tgt].append(float(evidence_count if evidence_count is not None else confidence if confidence is not None else 0))
        except Exception:
            evidence_values[tgt].append(0.0)

    candidates = sorted(set(inbound) & set(outbound))
    rows: list[dict[str, Any]] = []
    for key in candidates:
        if inbound[key] < min_inbound or outbound[key] < min_outbound:
            continue
        evidence_density = min(1.0, sum(evidence_values.get(key, [0.0])) / max(1, inbound[key] * 3.0))
        base = {
            "run_date_sgt": run_date_sgt,
            "intermediary_key": key,
            "canonical_name": canonical_name(key),
            "intermediary_category": classify_intermediary(key),
            "inbound_edge_count": inbound[key],
            "outbound_edge_count": outbound[key],
            "source_theme_count": len(source_themes.get(key, set())),
            "target_theme_count": len(target_themes.get(key, set())),
            "evidence_density": round(evidence_density, 6),
            "regime_stability": 0,
            "persistence_stability": 0,
            "normalized_forms": collect_normalized_forms(inbound_forms[key] + outbound_forms[key]),
        }
        scores = calculate_scores(base)
        rows.append({
            **base,
            **scores,
            "metadata": {
                "phase": "5A.2",
                "formation_logic": "node appears as both target_node_key and source_node_key",
                "min_inbound": min_inbound,
                "min_outbound": min_outbound,
            },
        })
    return sorted(rows, key=lambda r: (-float(r["intermediary_activation_score"]), r["intermediary_key"]))


def build_score_rows(intermediaries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for item in intermediaries:
        for name, value in item.get("component_scores", {}).items():
            rows.append({
                "run_date_sgt": item["run_date_sgt"],
                "intermediary_key": item["intermediary_key"],
                "score_name": name,
                "score_value": value,
                "score_weight": 1,
                "score_reason": f"Deterministic {name} component for intermediary formation.",
                "component_details": item.get("component_scores", {}),
            })
    return rows


def build_snapshot(run_id: str, run_date_sgt: str, intermediaries: list[dict[str, Any]]) -> dict[str, Any]:
    category_counts = Counter([r["intermediary_category"] for r in intermediaries])
    top = [
        {
            "intermediary_key": r["intermediary_key"],
            "canonical_name": r["canonical_name"],
            "category": r["intermediary_category"],
            "activation_score": r["intermediary_activation_score"],
            "inbound": r["inbound_edge_count"],
            "outbound": r["outbound_edge_count"],
        }
        for r in intermediaries[:25]
    ]
    avg_score = sum(float(r["intermediary_activation_score"]) for r in intermediaries) / max(1, len(intermediaries))
    return {
        "run_id": run_id,
        "run_date_sgt": run_date_sgt,
        "snapshot_type": "daily_intermediary_snapshot",
        "total_intermediaries": len(intermediaries),
        "active_intermediaries": sum(1 for r in intermediaries if float(r["intermediary_activation_score"]) >= 0.35),
        "top_intermediaries": top,
        "category_distribution": dict(category_counts),
        "aggregate_metrics": {"avg_activation_score": round(avg_score, 6)},
    }


def run(args: argparse.Namespace) -> int:
    started = time.time()
    run_id = args.run_id or f"phase5a2-{uuid.uuid4().hex[:12]}"
    run_date_sgt = args.run_date_sgt or today_sgt_iso()
    client = SupabaseClient()
    status = "SUCCESS"
    error_message = None
    metrics: dict[str, Any] = {}
    diagnostics: dict[str, Any] = {}

    try:
        tables = [t.strip() for t in (args.edge_tables or ",".join(DEFAULT_EDGE_TABLES)).split(",") if t.strip()]
        edges, diagnostics = load_edges(client, tables, args.limit_per_table)
        intermediaries = detect_intermediaries(edges, run_date_sgt, args.min_inbound, args.min_outbound)
        persisted = client.upsert("structural_theme_graph_intermediaries", intermediaries, on_conflict="run_date_sgt,intermediary_key")
        score_rows = build_score_rows(intermediaries)
        client.upsert("structural_theme_graph_intermediary_scores", score_rows, on_conflict="run_date_sgt,intermediary_key,score_name")
        snapshot = build_snapshot(run_id, run_date_sgt, intermediaries)
        client.upsert("structural_theme_graph_intermediary_snapshots", [snapshot], on_conflict="run_id,snapshot_type")
        metrics = {
            "edges_loaded": len(edges),
            "candidate_nodes_loaded": len(set([normalize_text(e["_source"]) for e in edges] + [normalize_text(e["_target"]) for e in edges])),
            "intermediaries_detected": len(intermediaries),
            "intermediaries_persisted": persisted,
        }
        validation_rows = build_validation_rows(run_id, run_date_sgt, metrics)
        persist_validations(client, validation_rows)
        metrics["validation_failures"] = sum(1 for r in validation_rows if r["validation_status"] not in {"PASS", "WARN"})
    except Exception as exc:  # noqa: BLE001
        status = "FAILED"
        error_message = str(exc)
        print(f"ERROR: {error_message}", file=sys.stderr)
    finally:
        telemetry = {
            "run_id": run_id,
            "run_date_sgt": run_date_sgt,
            "pipeline_name": "PHASE5A2_STRUCTURAL_INTERMEDIARY_FORMATION",
            "status": status,
            "runtime_seconds": round(time.time() - started, 3),
            "error_message": error_message,
            "details": {"diagnostics": diagnostics, "args": vars(args)},
            **{k: int(v) for k, v in metrics.items() if isinstance(v, int)},
        }
        try:
            persist_telemetry(client, telemetry)
        except Exception as telemetry_exc:  # noqa: BLE001
            print(f"WARNING: telemetry persistence failed: {telemetry_exc}", file=sys.stderr)
    return 0 if status == "SUCCESS" else 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Phase 5A.2 Structural Intermediary Formation")
    parser.add_argument("--run-id", default=os.getenv("GITHUB_RUN_ID"))
    parser.add_argument("--run-date-sgt", default=os.getenv("RUN_DATE_SGT"))
    parser.add_argument("--edge-tables", default=os.getenv("INTERMEDIARY_EDGE_TABLES", ",".join(DEFAULT_EDGE_TABLES)))
    parser.add_argument("--limit-per-table", type=int, default=int(os.getenv("INTERMEDIARY_LIMIT_PER_TABLE", "5000")))
    parser.add_argument("--min-inbound", type=int, default=int(os.getenv("INTERMEDIARY_MIN_INBOUND", "1")))
    parser.add_argument("--min-outbound", type=int, default=int(os.getenv("INTERMEDIARY_MIN_OUTBOUND", "1")))
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run(parse_args()))
