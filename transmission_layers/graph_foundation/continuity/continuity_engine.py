"""
Phase 5A.1 — Structural Continuity Engine

Purpose:
Create deterministic, bounded, replay-safe structural continuity paths:

    A → B → C

This engine solves the current graph-density problem where the graph behaves like:

    AI → many direct targets

instead of:

    AI → intermediate node → downstream node

This file intentionally avoids:
- graph ML
- embeddings
- vector databases
- stochastic expansion
- autonomous graph recursion
- unrestricted graph enrichment
- centrality analytics
- Neo4j
"""

from __future__ import annotations

import argparse
import datetime as dt
import os
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Optional

import requests


# ============================================================
# Configuration
# ============================================================

@dataclass(frozen=True)
class ContinuityConfig:
    theme_name: str = "generic"
    run_date_sgt: Optional[str] = None

    max_upstream_edges: int = 500
    max_downstream_edges_per_intermediate: int = 25
    max_candidates: int = 2000

    min_continuity_score: float = 0.62
    min_continuity_confidence: float = 0.60
    min_evidence_score: float = 0.35
    min_compatibility_score: float = 0.35

    graph_edge_limit: int = 5000
    persistence_limit: int = 5000
    pressure_limit: int = 5000
    regime_limit: int = 5000
    propagation_limit: int = 5000
    memory_limit: int = 5000

    is_replay_generated: bool = False
    replay_run_id: Optional[str] = None

    @property
    def score_weights(self) -> dict[str, float]:
        return {
            "continuity_path_score": 0.25,
            "compatibility_score": 0.20,
            "persistence_score": 0.15,
            "evidence_score": 0.15,
            "pressure_alignment_score": 0.10,
            "regime_alignment_score": 0.10,
            "propagation_support_score": 0.05,
        }


# ============================================================
# Supabase REST Client
# ============================================================

class SupabaseRestClient:
    def __init__(self) -> None:
        self.url = (os.getenv("SUPABASE_URL") or "").rstrip("/")
        self.key = (
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
            or os.getenv("SUPABASE_ANON_KEY")
            or ""
        )

        if not self.url:
            raise RuntimeError("Missing SUPABASE_URL")

        if not self.key:
            raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY")

        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    def endpoint(self, table: str) -> str:
        return f"{self.url}/rest/v1/{table}"

    def select(
        self,
        table: str,
        columns: str = "*",
        filters: Optional[dict[str, str]] = None,
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        params: dict[str, Any] = {"select": columns}

        if filters:
            params.update(filters)

        if order:
            params["order"] = order

        if limit:
            params["limit"] = limit

        response = requests.get(
            self.endpoint(table),
            headers=self.headers,
            params=params,
            timeout=45,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase select failed for {table}: "
                f"{response.status_code} {response.text[:1000]}"
            )

        return response.json()

    def upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        on_conflict: Optional[str] = None,
    ) -> None:
        if not rows:
            return

        params = {}
        if on_conflict:
            params["on_conflict"] = on_conflict

        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,returning=minimal"

        response = requests.post(
            self.endpoint(table),
            headers=headers,
            params=params,
            json=rows,
            timeout=60,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase upsert failed for {table}: "
                f"{response.status_code} {response.text[:1000]}"
            )

    def insert(self, table: str, rows: list[dict[str, Any]]) -> None:
        if not rows:
            return

        headers = dict(self.headers)
        headers["Prefer"] = "returning=minimal"

        response = requests.post(
            self.endpoint(table),
            headers=headers,
            json=rows,
            timeout=60,
        )

        if response.status_code >= 400:
            raise RuntimeError(
                f"Supabase insert failed for {table}: "
                f"{response.status_code} {response.text[:1000]}"
            )

    def chunked_upsert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        on_conflict: Optional[str] = None,
        chunk_size: int = 500,
    ) -> None:
        for i in range(0, len(rows), chunk_size):
            self.upsert(
                table=table,
                rows=rows[i : i + chunk_size],
                on_conflict=on_conflict,
            )

    def chunked_insert(
        self,
        table: str,
        rows: list[dict[str, Any]],
        chunk_size: int = 500,
    ) -> None:
        for i in range(0, len(rows), chunk_size):
            self.insert(table=table, rows=rows[i : i + chunk_size])


# ============================================================
# Table Names
# ============================================================

GRAPH_EDGES_TABLE = "structural_theme_graph_edges"

RELATIONSHIP_PERSISTENCE_TABLE = "structural_theme_graph_relationship_persistence"
PRESSURE_TABLE = "structural_theme_graph_pressure_accumulation"
REGIME_TABLE = "structural_theme_graph_regime_transitions"
SINGLE_HOP_TABLE = "structural_theme_graph_single_hop_propagation"
MEMORY_TABLE = "structural_theme_graph_propagation_memory"

CONTINUITY_CANDIDATES_TABLE = "structural_theme_graph_continuity_candidates"
CONTINUITY_EDGES_TABLE = "structural_theme_graph_continuity_edges"
CONTINUITY_SNAPSHOTS_TABLE = "structural_theme_graph_continuity_snapshots"
CONTINUITY_TELEMETRY_TABLE = "structural_theme_graph_continuity_telemetry"
CONTINUITY_VALIDATION_TABLE = "structural_theme_graph_continuity_validation"


# ============================================================
# Generic Helpers
# ============================================================

def today_sgt() -> str:
    return (dt.datetime.utcnow() + dt.timedelta(hours=8)).date().isoformat()


def clamp(value: Any, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        if value is None:
            return 0.0
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return 0.0


def get_first(row: dict[str, Any], keys: list[str], default: Any = None) -> Any:
    for key in keys:
        if key in row and row[key] is not None:
            return row[key]
    return default


def theme_filter(theme_name: str) -> dict[str, str]:
    if theme_name and theme_name != "all":
        return {"theme_name": f"eq.{theme_name}"}
    return {}


def normalize_edge(row: dict[str, Any]) -> Optional[dict[str, Any]]:
    source_id = get_first(row, ["source_node_id", "from_node_id", "parent_node_id"])
    target_id = get_first(row, ["target_node_id", "to_node_id", "child_node_id"])

    if source_id is None or target_id is None:
        return None

    try:
        source_id = int(source_id)
        target_id = int(target_id)
    except (TypeError, ValueError):
        return None

    return {
        **row,
        "source_node_id": source_id,
        "target_node_id": target_id,
        "source_node_key": get_first(
            row,
            ["source_node_key", "from_node_key", "source_key", "source_name"],
        ),
        "target_node_key": get_first(
            row,
            ["target_node_key", "to_node_key", "target_key", "target_name"],
        ),
        "theme_name": row.get("theme_name") or "generic",
    }


# ============================================================
# Fetching
# ============================================================

def fetch_edges(client: SupabaseRestClient, config: ContinuityConfig) -> list[dict[str, Any]]:
    rows = client.select(
        table=GRAPH_EDGES_TABLE,
        columns="*",
        filters=theme_filter(config.theme_name),
        order="id.desc",
        limit=config.graph_edge_limit,
    )

    edges = []
    for row in rows:
        normalized = normalize_edge(row)
        if normalized:
            edges.append(normalized)

    return edges


def fetch_optional_table(
    client: SupabaseRestClient,
    table: str,
    config: ContinuityConfig,
    limit: int,
) -> list[dict[str, Any]]:
    try:
        return client.select(
            table=table,
            columns="*",
            filters=theme_filter(config.theme_name),
            order="id.desc",
            limit=limit,
        )
    except Exception:
        try:
            return client.select(
                table=table,
                columns="*",
                order="id.desc",
                limit=limit,
            )
        except Exception:
            return []


# ============================================================
# Index Builders
# ============================================================

def index_by_edge(rows: list[dict[str, Any]]) -> dict[tuple[int, int], dict[str, Any]]:
    indexed = {}

    for row in rows:
        source_id = get_first(row, ["source_node_id", "from_node_id"])
        target_id = get_first(row, ["target_node_id", "to_node_id"])

        if source_id is None or target_id is None:
            continue

        try:
            indexed[(int(source_id), int(target_id))] = row
        except (TypeError, ValueError):
            continue

    return indexed


def index_pressure(rows: list[dict[str, Any]]) -> dict[int, dict[str, Any]]:
    indexed = {}

    for row in rows:
        node_id = get_first(row, ["node_id", "target_node_id", "theme_node_id"])

        if node_id is None:
            continue

        try:
            indexed[int(node_id)] = row
        except (TypeError, ValueError):
            continue

    return indexed


def index_regime(rows: list[dict[str, Any]]) -> dict[tuple[int, int], str]:
    indexed = {}

    for row in rows:
        source_id = get_first(row, ["source_node_id", "from_node_id"])
        target_id = get_first(row, ["target_node_id", "to_node_id"])
        regime = get_first(
            row,
            ["current_regime", "transition_regime", "edge_regime", "regime"],
        )

        if source_id is None or target_id is None or regime is None:
            continue

        try:
            indexed[(int(source_id), int(target_id))] = str(regime)
        except (TypeError, ValueError):
            continue

    return indexed


def build_propagation_support(rows: list[dict[str, Any]]) -> dict[tuple[int, int], float]:
    support = {}

    for row in rows:
        source_id = get_first(row, ["source_node_id", "from_node_id"])
        target_id = get_first(row, ["target_node_id", "to_node_id"])

        if source_id is None or target_id is None:
            continue

        score = get_first(
            row,
            [
                "propagation_score",
                "transmission_score",
                "memory_score",
                "decayed_score",
                "single_hop_score",
            ],
            default=0.0,
        )

        try:
            key = (int(source_id), int(target_id))
            support[key] = max(support.get(key, 0.0), clamp(score))
        except (TypeError, ValueError):
            continue

    return support


# ============================================================
# Scoring
# ============================================================

def score_edge_strength(edge: dict[str, Any]) -> float:
    return clamp(
        get_first(
            edge,
            [
                "edge_confidence",
                "confidence_score",
                "relationship_confidence",
                "evidence_confidence",
                "weight",
                "edge_weight",
                "score",
            ],
            default=0.5,
        )
    )


def score_evidence(edge: dict[str, Any]) -> float:
    return clamp(
        get_first(
            edge,
            [
                "evidence_intensity_score",
                "evidence_density_score",
                "evidence_score",
                "relationship_evidence_score",
                "confidence_score",
            ],
            default=0.35,
        )
    )


def score_persistence(row: Optional[dict[str, Any]]) -> float:
    if not row:
        return 0.0

    return clamp(
        get_first(
            row,
            [
                "persistence_score",
                "temporal_stability_score",
                "stability_score",
                "edge_persistence_score",
                "relationship_persistence_score",
            ],
            default=0.0,
        )
    )


def score_pressure(row: Optional[dict[str, Any]]) -> float:
    if not row:
        return 0.0

    return clamp(
        get_first(
            row,
            [
                "pressure_score",
                "structural_pressure_score",
                "accumulated_pressure_score",
                "pressure_accumulation_score",
            ],
            default=0.0,
        )
    )


def score_regime_alignment(
    upstream_regime: Optional[str],
    downstream_regime: Optional[str],
) -> float:
    if not upstream_regime or not downstream_regime:
        return 0.5

    upstream_regime = upstream_regime.lower()
    downstream_regime = downstream_regime.lower()

    if upstream_regime == downstream_regime:
        return 1.0

    compatible_pairs = {
        ("expansion", "accumulation"),
        ("accumulation", "expansion"),
        ("stress", "risk"),
        ("risk", "stress"),
        ("neutral", "stable"),
        ("stable", "neutral"),
    }

    if (upstream_regime, downstream_regime) in compatible_pairs:
        return 0.7

    return 0.35


def infer_continuity_category(
    upstream_edge: dict[str, Any],
    downstream_edge: dict[str, Any],
) -> str:
    text = " ".join(
        str(x or "").lower()
        for x in [
            upstream_edge.get("relationship_type"),
            downstream_edge.get("relationship_type"),
            upstream_edge.get("edge_type"),
            downstream_edge.get("edge_type"),
            upstream_edge.get("source_node_key"),
            upstream_edge.get("target_node_key"),
            downstream_edge.get("source_node_key"),
            downstream_edge.get("target_node_key"),
        ]
    )

    if any(k in text for k in ["supply", "supplier", "semiconductor", "equipment"]):
        return "supply_chain"

    if any(k in text for k in ["demand", "customer", "consumption", "capex"]):
        return "demand_transmission"

    if any(k in text for k in ["credit", "bank", "liquidity", "refinancing"]):
        return "balance_sheet"

    if any(k in text for k in ["cost", "inflation", "transport", "freight"]):
        return "cost_transmission"

    if any(k in text for k in ["utility", "power", "data center", "infrastructure"]):
        return "infrastructure"

    if any(k in text for k in ["rate", "macro", "growth", "dollar", "oil"]):
        return "macro_pressure"

    if any(k in text for k in ["capital", "flow", "investment"]):
        return "capital_flow"

    return "structural"


def score_candidate(candidate: dict[str, Any], config: ContinuityConfig) -> dict[str, Any]:
    upstream = candidate["upstream_edge"]
    downstream = candidate["downstream_edge"]

    upstream_strength = score_edge_strength(upstream)
    downstream_strength = score_edge_strength(downstream)

    continuity_path_score = clamp(
        upstream_strength * 0.55 + downstream_strength * 0.45
    )

    evidence_score = clamp(
        (score_evidence(upstream) + score_evidence(downstream)) / 2
    )

    persistence_score = clamp(
        (
            score_persistence(candidate.get("upstream_persistence"))
            + score_persistence(candidate.get("downstream_persistence"))
        )
        / 2
    )

    pressure_alignment_score = clamp(
        score_pressure(candidate.get("source_pressure")) * 0.30
        + score_pressure(candidate.get("intermediate_pressure")) * 0.40
        + score_pressure(candidate.get("target_pressure")) * 0.30
    )

    regime_alignment_score = score_regime_alignment(
        candidate.get("upstream_regime"),
        candidate.get("downstream_regime"),
    )

    compatibility_score = clamp(
        evidence_score * 0.35
        + persistence_score * 0.25
        + pressure_alignment_score * 0.25
        + regime_alignment_score * 0.15
    )

    propagation_support_score = clamp(candidate.get("propagation_support_score"))

    weights = config.score_weights

    continuity_score = clamp(
        continuity_path_score * weights["continuity_path_score"]
        + compatibility_score * weights["compatibility_score"]
        + persistence_score * weights["persistence_score"]
        + evidence_score * weights["evidence_score"]
        + pressure_alignment_score * weights["pressure_alignment_score"]
        + regime_alignment_score * weights["regime_alignment_score"]
        + propagation_support_score * weights["propagation_support_score"]
    )

    continuity_confidence = clamp(
        continuity_score * 0.50
        + evidence_score * 0.20
        + persistence_score * 0.15
        + compatibility_score * 0.15
    )

    return {
        "continuity_category": infer_continuity_category(upstream, downstream),
        "continuity_score": round(continuity_score, 6),
        "continuity_confidence": round(continuity_confidence, 6),
        "continuity_evidence_score": round(evidence_score, 6),
        "continuity_persistence_score": round(persistence_score, 6),
        "continuity_compatibility_score": round(compatibility_score, 6),
        "pressure_alignment_score": round(pressure_alignment_score, 6),
        "regime_alignment_score": round(regime_alignment_score, 6),
    }


# ============================================================
# Candidate Generation
# ============================================================

def generate_candidates(
    edges: list[dict[str, Any]],
    persistence_index: dict[tuple[int, int], dict[str, Any]],
    pressure_index: dict[int, dict[str, Any]],
    regime_index: dict[tuple[int, int], str],
    propagation_support: dict[tuple[int, int], float],
    config: ContinuityConfig,
) -> list[dict[str, Any]]:

    downstream_by_source: dict[int, list[dict[str, Any]]] = defaultdict(list)

    for edge in edges:
        downstream_by_source[int(edge["source_node_id"])].append(edge)

    upstream_edges = sorted(
        edges,
        key=lambda e: score_edge_strength(e),
        reverse=True,
    )[: config.max_upstream_edges]

    candidates = []

    for upstream in upstream_edges:
        source_id = int(upstream["source_node_id"])
        intermediate_id = int(upstream["target_node_id"])

        downstream_edges = downstream_by_source.get(intermediate_id, [])

        if not downstream_edges:
            continue

        downstream_edges = sorted(
            downstream_edges,
            key=lambda e: score_edge_strength(e),
            reverse=True,
        )[: config.max_downstream_edges_per_intermediate]

        for downstream in downstream_edges:
            target_id = int(downstream["target_node_id"])

            candidate = {
                "upstream_edge": upstream,
                "downstream_edge": downstream,
                "source_node_id": source_id,
                "intermediate_node_id": intermediate_id,
                "target_node_id": target_id,
                "source_node_key": upstream.get("source_node_key"),
                "intermediate_node_key": (
                    upstream.get("target_node_key")
                    or downstream.get("source_node_key")
                ),
                "target_node_key": downstream.get("target_node_key"),
                "theme_name": (
                    config.theme_name
                    if config.theme_name != "all"
                    else upstream.get("theme_name", "generic")
                ),
                "upstream_edge_id": upstream.get("id"),
                "downstream_edge_id": downstream.get("id"),
                "upstream_persistence": persistence_index.get((source_id, intermediate_id)),
                "downstream_persistence": persistence_index.get((intermediate_id, target_id)),
                "source_pressure": pressure_index.get(source_id),
                "intermediate_pressure": pressure_index.get(intermediate_id),
                "target_pressure": pressure_index.get(target_id),
                "upstream_regime": regime_index.get((source_id, intermediate_id)),
                "downstream_regime": regime_index.get((intermediate_id, target_id)),
                "propagation_support_score": max(
                    propagation_support.get((source_id, intermediate_id), 0.0),
                    propagation_support.get((intermediate_id, target_id), 0.0),
                ),
            }

            candidate.update(score_candidate(candidate, config))
            candidates.append(candidate)

            if len(candidates) >= config.max_candidates:
                return candidates

    return candidates


# ============================================================
# Validation
# ============================================================

def is_cycle_safe(source_id: int, intermediate_id: int, target_id: int) -> bool:
    return (
        source_id != intermediate_id
        and intermediate_id != target_id
        and source_id != target_id
    )


def validate_candidate(
    candidate: dict[str, Any],
    seen_keys: set[tuple[int, int, int, str]],
    config: ContinuityConfig,
) -> tuple[bool, Optional[str]]:

    source_id = int(candidate["source_node_id"])
    intermediate_id = int(candidate["intermediate_node_id"])
    target_id = int(candidate["target_node_id"])
    theme_name = str(candidate.get("theme_name") or "generic")

    if not is_cycle_safe(source_id, intermediate_id, target_id):
        return False, "cycle_or_self_loop"

    key = (source_id, intermediate_id, target_id, theme_name)

    if key in seen_keys:
        return False, "duplicate_candidate"

    if candidate["continuity_score"] < config.min_continuity_score:
        return False, "below_min_continuity_score"

    if candidate["continuity_confidence"] < config.min_continuity_confidence:
        return False, "below_min_continuity_confidence"

    if candidate["continuity_evidence_score"] < config.min_evidence_score:
        return False, "below_min_evidence_score"

    if candidate["continuity_compatibility_score"] < config.min_compatibility_score:
        return False, "below_min_compatibility_score"

    return True, None


# ============================================================
# Row Builders
# ============================================================

def build_candidate_row(
    candidate: dict[str, Any],
    run_date_sgt: str,
    validation_status: str,
    rejection_reason: Optional[str],
) -> dict[str, Any]:
    return {
        "run_date_sgt": run_date_sgt,
        "source_node_id": candidate["source_node_id"],
        "intermediate_node_id": candidate["intermediate_node_id"],
        "target_node_id": candidate["target_node_id"],
        "source_node_key": candidate.get("source_node_key"),
        "intermediate_node_key": candidate.get("intermediate_node_key"),
        "target_node_key": candidate.get("target_node_key"),
        "theme_name": candidate.get("theme_name") or "generic",
        "continuity_category": candidate.get("continuity_category") or "structural",
        "upstream_edge_id": candidate.get("upstream_edge_id"),
        "downstream_edge_id": candidate.get("downstream_edge_id"),
        "candidate_reason": "deterministic_two_leg_continuity_completion",
        "continuity_score": candidate.get("continuity_score"),
        "continuity_confidence": candidate.get("continuity_confidence"),
        "continuity_evidence_score": candidate.get("continuity_evidence_score"),
        "continuity_persistence_score": candidate.get("continuity_persistence_score"),
        "continuity_compatibility_score": candidate.get("continuity_compatibility_score"),
        "pressure_alignment_score": candidate.get("pressure_alignment_score"),
        "regime_alignment_score": candidate.get("regime_alignment_score"),
        "validation_status": validation_status,
        "rejection_reason": rejection_reason,
        "is_cycle_safe": rejection_reason != "cycle_or_self_loop",
        "is_unique_candidate": rejection_reason != "duplicate_candidate",
    }


def build_edge_row(
    candidate_row: dict[str, Any],
    config: ContinuityConfig,
) -> dict[str, Any]:
    return {
        "run_date_sgt": candidate_row["run_date_sgt"],
        "source_node_id": candidate_row["source_node_id"],
        "intermediate_node_id": candidate_row["intermediate_node_id"],
        "target_node_id": candidate_row["target_node_id"],
        "source_node_key": candidate_row.get("source_node_key"),
        "intermediate_node_key": candidate_row.get("intermediate_node_key"),
        "target_node_key": candidate_row.get("target_node_key"),
        "theme_name": candidate_row.get("theme_name") or "generic",
        "continuity_category": candidate_row.get("continuity_category") or "structural",
        "continuity_score": candidate_row.get("continuity_score"),
        "continuity_confidence": candidate_row.get("continuity_confidence"),
        "continuity_evidence_score": candidate_row.get("continuity_evidence_score"),
        "continuity_persistence_score": candidate_row.get("continuity_persistence_score"),
        "continuity_compatibility_score": candidate_row.get("continuity_compatibility_score"),
        "pressure_alignment_score": candidate_row.get("pressure_alignment_score"),
        "regime_alignment_score": candidate_row.get("regime_alignment_score"),
        "activation_status": "active",
        "activation_reason": "passed_structural_continuity_validation",
        "is_replay_generated": config.is_replay_generated,
        "replay_run_id": config.replay_run_id,
    }


def build_snapshot_row(
    run_date_sgt: str,
    theme_name: str,
    candidates: list[dict[str, Any]],
    accepted_edges: list[dict[str, Any]],
    rejected_candidates: list[dict[str, Any]],
    config: ContinuityConfig,
) -> dict[str, Any]:

    scores = [
        float(row["continuity_score"])
        for row in accepted_edges
        if row.get("continuity_score") is not None
    ]

    top_continuities = sorted(
        accepted_edges,
        key=lambda row: float(row.get("continuity_score") or 0.0),
        reverse=True,
    )[:25]

    return {
        "run_date_sgt": run_date_sgt,
        "theme_name": theme_name,
        "snapshot_type": "daily_continuity_state",
        "candidate_count": len(candidates),
        "accepted_count": len(accepted_edges),
        "rejected_count": len(rejected_candidates),
        "avg_continuity_score": round(sum(scores) / len(scores), 6) if scores else None,
        "max_continuity_score": round(max(scores), 6) if scores else None,
        "min_continuity_score": round(min(scores), 6) if scores else None,
        "continuity_payload": {
            "top_continuities": [
                {
                    "source_node_key": row.get("source_node_key"),
                    "intermediate_node_key": row.get("intermediate_node_key"),
                    "target_node_key": row.get("target_node_key"),
                    "continuity_category": row.get("continuity_category"),
                    "continuity_score": row.get("continuity_score"),
                    "continuity_confidence": row.get("continuity_confidence"),
                }
                for row in top_continuities
            ]
        },
        "is_replay_generated": config.is_replay_generated,
        "replay_run_id": config.replay_run_id or "live",
    }


def build_telemetry_row(
    run_date_sgt: str,
    theme_name: str,
    status: str,
    candidates_generated: int,
    candidates_validated: int,
    accepted_count: int,
    rejected_count: int,
    cycle_rejections: int,
    duplicate_rejections: int,
    runtime_seconds: float,
    error_message: Optional[str] = None,
) -> dict[str, Any]:
    return {
        "run_date_sgt": run_date_sgt,
        "pipeline_name": "STRUCTURAL_CONTINUITY_ENGINE",
        "theme_name": theme_name,
        "status": status,
        "candidates_generated": candidates_generated,
        "candidates_validated": candidates_validated,
        "continuities_accepted": accepted_count,
        "continuities_rejected": rejected_count,
        "cycle_rejections": cycle_rejections,
        "duplicate_rejections": duplicate_rejections,
        "runtime_seconds": runtime_seconds,
        "error_message": error_message,
        "github_run_id": os.getenv("GITHUB_RUN_ID"),
        "github_workflow": os.getenv("GITHUB_WORKFLOW"),
        "github_repository": os.getenv("GITHUB_REPOSITORY"),
        "github_branch": os.getenv("GITHUB_REF_NAME"),
    }


def build_validation_rows(
    run_date_sgt: str,
    theme_name: str,
    accepted_count: int,
    rejected_count: int,
    cycle_rejections: int,
    duplicate_rejections: int,
) -> list[dict[str, Any]]:

    total = accepted_count + rejected_count
    acceptance_rate = accepted_count / total if total else 0.0

    return [
        {
            "run_date_sgt": run_date_sgt,
            "theme_name": theme_name,
            "validation_name": "acceptance_rate_nonzero",
            "validation_status": "pass" if accepted_count > 0 else "warn",
            "validation_value": round(acceptance_rate, 6),
            "threshold_value": 0.0,
            "details": {
                "accepted_count": accepted_count,
                "rejected_count": rejected_count,
            },
        },
        {
            "run_date_sgt": run_date_sgt,
            "theme_name": theme_name,
            "validation_name": "cycle_rejection_monitor",
            "validation_status": "pass",
            "validation_value": float(cycle_rejections),
            "threshold_value": None,
            "details": {"cycle_rejections": cycle_rejections},
        },
        {
            "run_date_sgt": run_date_sgt,
            "theme_name": theme_name,
            "validation_name": "duplicate_rejection_monitor",
            "validation_status": "pass",
            "validation_value": float(duplicate_rejections),
            "threshold_value": None,
            "details": {"duplicate_rejections": duplicate_rejections},
        },
    ]


# ============================================================
# Persistence
# ============================================================

def persist_outputs(
    client: SupabaseRestClient,
    candidate_rows: list[dict[str, Any]],
    accepted_edge_rows: list[dict[str, Any]],
    snapshot_row: dict[str, Any],
    telemetry_row: dict[str, Any],
    validation_rows: list[dict[str, Any]],
) -> None:

    client.chunked_upsert(
        table=CONTINUITY_CANDIDATES_TABLE,
        rows=candidate_rows,
        on_conflict="run_date_sgt,theme_name,source_node_id,intermediate_node_id,target_node_id",
    )

    client.chunked_upsert(
        table=CONTINUITY_EDGES_TABLE,
        rows=accepted_edge_rows,
        on_conflict="run_date_sgt,theme_name,source_node_id,intermediate_node_id,target_node_id",
    )

    client.upsert(
        table=CONTINUITY_SNAPSHOTS_TABLE,
        rows=[snapshot_row],
        on_conflict="run_date_sgt,theme_name,snapshot_type,replay_run_id",
    )

    client.insert(
        table=CONTINUITY_TELEMETRY_TABLE,
        rows=[telemetry_row],
    )

    client.chunked_insert(
        table=CONTINUITY_VALIDATION_TABLE,
        rows=validation_rows,
    )


# ============================================================
# Engine
# ============================================================

def run_continuity_engine(config: ContinuityConfig) -> dict[str, Any]:
    started = time.time()
    run_date = config.run_date_sgt or today_sgt()

    client = SupabaseRestClient()

    candidates_generated = 0
    candidates_validated = 0
    cycle_rejections = 0
    duplicate_rejections = 0

    try:
        edges = fetch_edges(client, config)

        persistence_rows = fetch_optional_table(
            client,
            RELATIONSHIP_PERSISTENCE_TABLE,
            config,
            config.persistence_limit,
        )

        pressure_rows = fetch_optional_table(
            client,
            PRESSURE_TABLE,
            config,
            config.pressure_limit,
        )

        regime_rows = fetch_optional_table(
            client,
            REGIME_TABLE,
            config,
            config.regime_limit,
        )

        single_hop_rows = fetch_optional_table(
            client,
            SINGLE_HOP_TABLE,
            config,
            config.propagation_limit,
        )

        memory_rows = fetch_optional_table(
            client,
            MEMORY_TABLE,
            config,
            config.memory_limit,
        )

        persistence_index = index_by_edge(persistence_rows)
        pressure_index = index_pressure(pressure_rows)
        regime_index = index_regime(regime_rows)
        propagation_support = build_propagation_support(single_hop_rows + memory_rows)

        candidates = generate_candidates(
            edges=edges,
            persistence_index=persistence_index,
            pressure_index=pressure_index,
            regime_index=regime_index,
            propagation_support=propagation_support,
            config=config,
        )

        candidates_generated = len(candidates)

        seen_keys: set[tuple[int, int, int, str]] = set()
        candidate_rows = []
        accepted_edge_rows = []
        rejected_candidate_rows = []

        for candidate in candidates:
            is_valid, rejection_reason = validate_candidate(
                candidate=candidate,
                seen_keys=seen_keys,
                config=config,
            )

            candidates_validated += 1

            if rejection_reason == "cycle_or_self_loop":
                cycle_rejections += 1

            if rejection_reason == "duplicate_candidate":
                duplicate_rejections += 1

            validation_status = "accepted" if is_valid else "rejected"

            candidate_row = build_candidate_row(
                candidate=candidate,
                run_date_sgt=run_date,
                validation_status=validation_status,
                rejection_reason=rejection_reason,
            )

            candidate_rows.append(candidate_row)

            if is_valid:
                seen_keys.add(
                    (
                        int(candidate["source_node_id"]),
                        int(candidate["intermediate_node_id"]),
                        int(candidate["target_node_id"]),
                        str(candidate.get("theme_name") or "generic"),
                    )
                )

                accepted_edge_rows.append(
                    build_edge_row(candidate_row, config)
                )
            else:
                rejected_candidate_rows.append(candidate_row)

        runtime_seconds = round(time.time() - started, 3)

        snapshot_row = build_snapshot_row(
            run_date_sgt=run_date,
            theme_name=config.theme_name,
            candidates=candidate_rows,
            accepted_edges=accepted_edge_rows,
            rejected_candidates=rejected_candidate_rows,
            config=config,
        )

        telemetry_row = build_telemetry_row(
            run_date_sgt=run_date,
            theme_name=config.theme_name,
            status="success",
            candidates_generated=candidates_generated,
            candidates_validated=candidates_validated,
            accepted_count=len(accepted_edge_rows),
            rejected_count=len(rejected_candidate_rows),
            cycle_rejections=cycle_rejections,
            duplicate_rejections=duplicate_rejections,
            runtime_seconds=runtime_seconds,
        )

        validation_rows = build_validation_rows(
            run_date_sgt=run_date,
            theme_name=config.theme_name,
            accepted_count=len(accepted_edge_rows),
            rejected_count=len(rejected_candidate_rows),
            cycle_rejections=cycle_rejections,
            duplicate_rejections=duplicate_rejections,
        )

        persist_outputs(
            client=client,
            candidate_rows=candidate_rows,
            accepted_edge_rows=accepted_edge_rows,
            snapshot_row=snapshot_row,
            telemetry_row=telemetry_row,
            validation_rows=validation_rows,
        )

        return {
            "status": "success",
            "run_date_sgt": run_date,
            "theme_name": config.theme_name,
            "edges_loaded": len(edges),
            "candidates_generated": candidates_generated,
            "candidates_validated": candidates_validated,
            "continuities_accepted": len(accepted_edge_rows),
            "continuities_rejected": len(rejected_candidate_rows),
            "cycle_rejections": cycle_rejections,
            "duplicate_rejections": duplicate_rejections,
            "runtime_seconds": runtime_seconds,
        }

    except Exception as exc:
        runtime_seconds = round(time.time() - started, 3)

        try:
            telemetry_row = build_telemetry_row(
                run_date_sgt=run_date,
                theme_name=config.theme_name,
                status="failed",
                candidates_generated=candidates_generated,
                candidates_validated=candidates_validated,
                accepted_count=0,
                rejected_count=0,
                cycle_rejections=cycle_rejections,
                duplicate_rejections=duplicate_rejections,
                runtime_seconds=runtime_seconds,
                error_message=str(exc)[:1000],
            )

            client.insert(
                table=CONTINUITY_TELEMETRY_TABLE,
                rows=[telemetry_row],
            )
        except Exception:
            pass

        raise


# ============================================================
# CLI
# ============================================================

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Phase 5A.1 Structural Continuity Engine"
    )

    parser.add_argument("--theme-name", default="generic")
    parser.add_argument("--run-date-sgt", default=None)

    parser.add_argument("--max-upstream-edges", type=int, default=500)
    parser.add_argument("--max-downstream-edges-per-intermediate", type=int, default=25)
    parser.add_argument("--max-candidates", type=int, default=2000)

    parser.add_argument("--min-continuity-score", type=float, default=0.62)
    parser.add_argument("--min-continuity-confidence", type=float, default=0.60)
    parser.add_argument("--min-evidence-score", type=float, default=0.35)
    parser.add_argument("--min-compatibility-score", type=float, default=0.35)

    parser.add_argument("--is-replay-generated", action="store_true")
    parser.add_argument("--replay-run-id", default=None)

    return parser.parse_args()


def main() -> None:
    args = parse_args()

    config = ContinuityConfig(
        theme_name=args.theme_name,
        run_date_sgt=args.run_date_sgt,
        max_upstream_edges=args.max_upstream_edges,
        max_downstream_edges_per_intermediate=args.max_downstream_edges_per_intermediate,
        max_candidates=args.max_candidates,
        min_continuity_score=args.min_continuity_score,
        min_continuity_confidence=args.min_continuity_confidence,
        min_evidence_score=args.min_evidence_score,
        min_compatibility_score=args.min_compatibility_score,
        is_replay_generated=args.is_replay_generated,
        replay_run_id=args.replay_run_id,
    )

    result = run_continuity_engine(config)
    print(result)


if __name__ == "__main__":
    main()
