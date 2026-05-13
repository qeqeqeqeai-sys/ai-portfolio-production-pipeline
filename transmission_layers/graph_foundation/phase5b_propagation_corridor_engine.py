#!/usr/bin/env python3
"""
Phase 5B — Propagation Corridor Intelligence Layer

Deterministic corridor engine for the modular structural transmission research platform.
Consumes canonical graph edges, intermediary nodes, and directed seeded edges.
Does not use graph ML, embeddings, networkx centrality, Neo4j, or autonomous mutation.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

PIPELINE_NAME = "PHASE5B_PROPAGATION_CORRIDOR_INTELLIGENCE"
SINGAPORE_TZ = timezone(timedelta(hours=8))

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "90"))
MAX_MULTI_HOP_CHAINS = int(os.getenv("MAX_MULTI_HOP_CHAINS", "250"))
MIN_CORRIDOR_SCORE = float(os.getenv("MIN_CORRIDOR_SCORE", "0.05"))


def today_sgt() -> str:
    return datetime.now(SINGAPORE_TZ).date().isoformat()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clamp(value: Any, low: float = 0.0, high: float = 1.0) -> float:
    try:
        x = float(value or 0)
    except Exception:
        x = 0.0
    if math.isnan(x) or math.isinf(x):
        x = 0.0
    return max(low, min(high, x))


def stable_hash(parts: Iterable[Any]) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SupabaseClient:
    def __init__(self, url: str, key: str):
        if not url or not key:
            raise RuntimeError("Missing SUPABASE_URL or Supabase key environment variable")
        self.url = url
        self.headers = {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _request(self, method: str, table: str, params: Optional[Dict[str, str]] = None, payload: Any = None) -> Any:
        endpoint = f"{self.url}/rest/v1/{table}"
        last_error = None
        for attempt in range(4):
            try:
                response = requests.request(method, endpoint, headers=self.headers, params=params, json=payload, timeout=45)
                if response.status_code in (200, 201, 204):
                    if not response.text:
                        return []
                    return response.json()
                last_error = f"{response.status_code}: {response.text[:500]}"
            except Exception as exc:
                last_error = str(exc)
            time.sleep(1.5 * (attempt + 1))
        raise RuntimeError(f"Supabase {method} {table} failed: {last_error}")

    def fetch_all(self, table: str, params: Optional[Dict[str, str]] = None, page_size: int = 1000) -> List[Dict[str, Any]]:
        rows: List[Dict[str, Any]] = []
        offset = 0
        while True:
            q = dict(params or {})
            q["limit"] = str(page_size)
            q["offset"] = str(offset)
            batch = self._request("GET", table, q)
            if not batch:
                break
            rows.extend(batch)
            if len(batch) < page_size:
                break
            offset += page_size
        return rows

    def upsert(self, table: str, rows: List[Dict[str, Any]], conflict: str, chunk_size: int = 200) -> int:
        if not rows:
            return 0
        total = 0
        for i in range(0, len(rows), chunk_size):
            chunk = rows[i : i + chunk_size]
            params = {"on_conflict": conflict}
            headers = dict(self.headers)
            headers["Prefer"] = "resolution=merge-duplicates,return=minimal"
            endpoint = f"{self.url}/rest/v1/{table}"
            response = requests.post(endpoint, headers=headers, params=params, json=chunk, timeout=60)
            if response.status_code not in (200, 201, 204):
                raise RuntimeError(f"Supabase upsert {table} failed: {response.status_code}: {response.text[:800]}")
            total += len(chunk)
        return total


@dataclass
class EdgeMetric:
    source: str
    target: str
    edge_key: str
    edge_strength: float = 0.0
    directional_strength: float = 0.0
    confidence_score: float = 0.0
    evidence_intensity: float = 0.0
    persistence_score: float = 0.0
    source_kind: str = "canonical"


class CorridorEngine:
    def __init__(self, db: SupabaseClient):
        self.db = db
        self.run_id = f"phase5b_{today_sgt()}_{uuid.uuid4().hex[:10]}"
        self.run_date_sgt = today_sgt()
        self.started = time.time()
        self.stats: Dict[str, int] = defaultdict(int)
        self.validation_rows: List[Dict[str, Any]] = []

    def fetch_inputs(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        canonical_edges = self.db.fetch_all(
            "structural_theme_graph_canonical_edge_view_materialized",
            {"select": "*", "order": "created_at.desc"},
        )
        seed_edges = self.db.fetch_all(
            "structural_theme_graph_directed_seed_edges",
            {"select": "*", "order": "run_date_sgt.desc"},
        )
        intermediaries = self.db.fetch_all(
            "structural_theme_graph_intermediaries",
            {"select": "*", "order": "run_date_sgt.desc"},
        )
        raw_edges = self.db.fetch_all(
            "structural_theme_graph_edges",
            {"select": "*", "is_active": "eq.true", "order": "updated_at.desc"},
        )
        self.stats["canonical_edges_loaded"] = len(canonical_edges)
        self.stats["seed_edges_loaded"] = len(seed_edges)
        self.stats["intermediaries_loaded"] = len(intermediaries)
        self.stats["raw_edges_loaded"] = len(raw_edges)
        return canonical_edges, seed_edges, intermediaries, raw_edges

    def latest_intermediaries(self, rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        latest: Dict[str, Dict[str, Any]] = {}
        for row in sorted(rows, key=lambda r: (r.get("run_date_sgt") or "", r.get("updated_at") or ""), reverse=True):
            key = row.get("intermediary_key")
            if key and key not in latest:
                latest[key] = row
        return latest

    def build_edge_metrics(
        self,
        canonical_edges: List[Dict[str, Any]],
        seed_edges: List[Dict[str, Any]],
        raw_edges: List[Dict[str, Any]],
    ) -> Dict[Tuple[str, str], List[EdgeMetric]]:
        raw_by_pair: Dict[Tuple[str, str], List[Dict[str, Any]]] = defaultdict(list)
        for e in raw_edges:
            raw_by_pair[(e.get("source_node_key"), e.get("target_node_key"))].append(e)

        metrics: Dict[Tuple[str, str], List[EdgeMetric]] = defaultdict(list)

        for c in canonical_edges:
            src = c.get("canonical_source_node_key")
            tgt = c.get("canonical_target_node_key")
            if not src or not tgt or src == tgt:
                continue
            raw_candidates = raw_by_pair.get((c.get("raw_source_node_key"), c.get("raw_target_node_key")), [])
            if raw_candidates:
                for r in raw_candidates[:3]:
                    metrics[(src, tgt)].append(
                        EdgeMetric(
                            source=src,
                            target=tgt,
                            edge_key=r.get("edge_key") or c.get("canonical_edge_hash"),
                            edge_strength=clamp(r.get("edge_strength")),
                            directional_strength=clamp(abs(float(r.get("directional_strength") or 0))),
                            confidence_score=clamp(r.get("confidence_score")),
                            evidence_intensity=clamp(r.get("evidence_intensity")),
                            persistence_score=clamp(r.get("persistence_score")),
                            source_kind="canonical_raw_metric",
                        )
                    )
            else:
                metrics[(src, tgt)].append(
                    EdgeMetric(
                        source=src,
                        target=tgt,
                        edge_key=c.get("canonical_edge_hash") or stable_hash([src, tgt, "canonical"]),
                        edge_strength=0.50,
                        directional_strength=0.50,
                        confidence_score=0.60,
                        evidence_intensity=0.40,
                        persistence_score=0.40,
                        source_kind="canonical_fallback",
                    )
                )

        for s in seed_edges:
            src = s.get("source_node_key")
            tgt = s.get("target_node_key")
            if not src or not tgt or src == tgt:
                continue
            conf = clamp(s.get("confidence_score"), 0, 1)
            metrics[(src, tgt)].append(
                EdgeMetric(
                    source=src,
                    target=tgt,
                    edge_key=s.get("seed_hash") or stable_hash([src, tgt, s.get("rule_id"), "seed"]),
                    edge_strength=max(0.45, conf),
                    directional_strength=max(0.55, conf),
                    confidence_score=conf,
                    evidence_intensity=max(0.35, conf * 0.75),
                    persistence_score=max(0.30, conf * 0.70),
                    source_kind="directed_seed",
                )
            )
        return metrics

    def avg_metric(self, edge_lists: List[List[EdgeMetric]], attr: str) -> float:
        vals = [getattr(e, attr) for edges in edge_lists for e in edges]
        return clamp(sum(vals) / len(vals)) if vals else 0.0

    def edge_count_by_kind(self, edge_lists: List[List[EdgeMetric]], kind: str) -> int:
        return sum(1 for edges in edge_lists for e in edges if e.source_kind == kind or (kind == "canonical" and e.source_kind.startswith("canonical")))

    def classify_corridor(self, score: float, reuse: int, stability: float, bottleneck: float, hop_count: int) -> str:
        if score >= 0.75 and reuse >= 4 and stability >= 0.60:
            return "dominant_transmission_corridor"
        if bottleneck >= 0.70 and score >= 0.55:
            return "bottleneck_control_corridor"
        if hop_count >= 3 and score >= 0.45:
            return "multi_hop_chain_corridor"
        if reuse >= 3 and score >= 0.35:
            return "reusable_corridor"
        if score >= 0.20:
            return "emerging_corridor"
        return "weak_corridor"

    def regime_sensitivity(self, regime_stability: float, directional_strength: float) -> str:
        if regime_stability >= 0.70 and directional_strength >= 0.55:
            return "regime_stable"
        if regime_stability <= 0.30 and directional_strength >= 0.55:
            return "regime_sensitive"
        return "mixed_regime_sensitivity"

    def make_corridor(
        self,
        path_nodes: List[str],
        edge_lists: List[List[EdgeMetric]],
        inter_map: Dict[str, Dict[str, Any]],
        corridor_type: str,
    ) -> Optional[Dict[str, Any]]:
        intermediaries = path_nodes[1:-1]
        if not intermediaries:
            return None

        inter_rows = [inter_map.get(k, {}) for k in intermediaries]
        activation = clamp(sum(clamp(r.get("intermediary_activation_score")) for r in inter_rows) / max(1, len(inter_rows)))
        evidence_density = clamp(sum(clamp(r.get("evidence_density")) for r in inter_rows) / max(1, len(inter_rows)))
        regime_stability = clamp(sum(clamp(r.get("regime_stability")) for r in inter_rows) / max(1, len(inter_rows)))
        persistence_stability = clamp(sum(clamp(r.get("persistence_stability")) for r in inter_rows) / max(1, len(inter_rows)))

        avg_edge_strength = self.avg_metric(edge_lists, "edge_strength")
        avg_directional_strength = self.avg_metric(edge_lists, "directional_strength")
        avg_confidence = self.avg_metric(edge_lists, "confidence_score")
        avg_evidence = self.avg_metric(edge_lists, "evidence_intensity")
        avg_persistence = self.avg_metric(edge_lists, "persistence_score")

        reuse_frequency = sum(len(edges) for edges in edge_lists) + sum(int(r.get("total_edge_count") or 0) for r in inter_rows)
        reuse_score = clamp(math.log1p(reuse_frequency) / math.log1p(20))

        corridor_strength = clamp(0.35 * avg_edge_strength + 0.25 * avg_directional_strength + 0.20 * avg_confidence + 0.20 * activation)
        corridor_persistence = clamp(0.45 * avg_persistence + 0.35 * persistence_stability + 0.20 * reuse_score)
        corridor_stability = clamp(0.45 * regime_stability + 0.30 * persistence_stability + 0.25 * avg_confidence)
        intelligence = clamp(0.30 * corridor_strength + 0.25 * corridor_persistence + 0.20 * corridor_stability + 0.15 * reuse_score + 0.10 * evidence_density)

        bottleneck_candidates = []
        for node, row in zip(intermediaries, inter_rows):
            inbound = int(row.get("inbound_edge_count") or 0)
            outbound = int(row.get("outbound_edge_count") or 0)
            total = max(1, inbound + outbound)
            balance_penalty = 1.0 - (abs(inbound - outbound) / total)
            node_bottleneck = clamp(0.40 * clamp(row.get("intermediary_activation_score")) + 0.25 * reuse_score + 0.20 * balance_penalty + 0.15 * clamp(row.get("evidence_density")))
            bottleneck_candidates.append((node_bottleneck, node, f"activation={clamp(row.get('intermediary_activation_score')):.3f}; reuse_score={reuse_score:.3f}; balance={balance_penalty:.3f}"))
        bottleneck_score, bottleneck_node, bottleneck_reason = max(bottleneck_candidates, default=(0.0, None, None))

        if intelligence < MIN_CORRIDOR_SCORE:
            return None

        source = path_nodes[0]
        target = path_nodes[-1]
        hop_count = len(path_nodes) - 1
        corridor_hash = stable_hash([source, "->".join(path_nodes[1:-1]), target, hop_count])
        corridor_key = " -> ".join(path_nodes)
        classification = self.classify_corridor(intelligence, reuse_frequency, corridor_stability, bottleneck_score, hop_count)

        path_edges = []
        for edges in edge_lists:
            path_edges.extend([asdict(e) for e in edges[:5]])

        return {
            "run_id": self.run_id,
            "run_date_sgt": self.run_date_sgt,
            "corridor_hash": corridor_hash,
            "corridor_key": corridor_key,
            "corridor_type": corridor_type,
            "corridor_classification": classification,
            "source_node_key": source,
            "target_node_key": target,
            "intermediary_node_keys": intermediaries,
            "path_nodes": path_nodes,
            "path_edges": path_edges,
            "hop_count": hop_count,
            "source_edge_count": sum(len(edges) for edges in edge_lists),
            "seed_edge_count": self.edge_count_by_kind(edge_lists, "directed_seed"),
            "canonical_edge_count": self.edge_count_by_kind(edge_lists, "canonical"),
            "reuse_frequency": int(reuse_frequency),
            "avg_edge_strength": avg_edge_strength,
            "avg_directional_strength": avg_directional_strength,
            "avg_confidence_score": avg_confidence,
            "avg_evidence_intensity": avg_evidence,
            "avg_persistence_score": avg_persistence,
            "intermediary_activation_score": activation,
            "evidence_density": evidence_density,
            "regime_stability": regime_stability,
            "persistence_stability": persistence_stability,
            "corridor_strength": corridor_strength,
            "corridor_persistence": corridor_persistence,
            "corridor_stability": corridor_stability,
            "corridor_reuse_score": reuse_score,
            "corridor_intelligence_score": intelligence,
            "bottleneck_node_key": bottleneck_node,
            "bottleneck_score": bottleneck_score,
            "bottleneck_reason": bottleneck_reason,
            "regime_sensitivity": self.regime_sensitivity(regime_stability, avg_directional_strength),
            "dominant_pathway_flag": classification == "dominant_transmission_corridor",
            "metadata": {
                "engine_version": "phase5b_v1",
                "source": "canonical_edges + directed_seed_edges + intermediaries",
                "created_at_utc": now_iso(),
            },
            "component_scores": {
                "corridor_strength": corridor_strength,
                "corridor_persistence": corridor_persistence,
                "corridor_stability": corridor_stability,
                "reuse_score": reuse_score,
                "evidence_density": evidence_density,
                "bottleneck_score": bottleneck_score,
            },
        }

    def detect_corridors(self, edge_metrics: Dict[Tuple[str, str], List[EdgeMetric]], inter_map: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
        out_edges: Dict[str, List[str]] = defaultdict(list)
        in_edges: Dict[str, List[str]] = defaultdict(list)
        for (src, tgt) in edge_metrics:
            out_edges[src].append(tgt)
            in_edges[tgt].append(src)

        corridors: Dict[str, Dict[str, Any]] = {}
        intermediary_keys = set(inter_map.keys())

        for i in sorted(intermediary_keys):
            for src in sorted(in_edges.get(i, [])):
                for tgt in sorted(out_edges.get(i, [])):
                    if src == tgt:
                        continue
                    path = [src, i, tgt]
                    edge_lists = [edge_metrics[(src, i)], edge_metrics[(i, tgt)]]
                    row = self.make_corridor(path, edge_lists, inter_map, "two_hop")
                    if row:
                        corridors[row["corridor_hash"]] = row
        self.stats["two_hop_corridors_detected"] = len(corridors)

        multi_hop_count = 0
        for i1 in sorted(intermediary_keys):
            for i2 in sorted(out_edges.get(i1, [])):
                if i2 not in intermediary_keys or i2 == i1:
                    continue
                for src in sorted(in_edges.get(i1, [])):
                    if src in (i1, i2):
                        continue
                    for tgt in sorted(out_edges.get(i2, [])):
                        if tgt in (src, i1, i2):
                            continue
                        path = [src, i1, i2, tgt]
                        needed = [(src, i1), (i1, i2), (i2, tgt)]
                        if not all(pair in edge_metrics for pair in needed):
                            continue
                        edge_lists = [edge_metrics[pair] for pair in needed]
                        row = self.make_corridor(path, edge_lists, inter_map, "multi_hop_chain")
                        if row:
                            corridors[row["corridor_hash"]] = row
                            multi_hop_count += 1
                        if multi_hop_count >= MAX_MULTI_HOP_CHAINS:
                            break
                    if multi_hop_count >= MAX_MULTI_HOP_CHAINS:
                        break
                if multi_hop_count >= MAX_MULTI_HOP_CHAINS:
                    break
            if multi_hop_count >= MAX_MULTI_HOP_CHAINS:
                break
        self.stats["multi_hop_corridors_detected"] = multi_hop_count
        return sorted(corridors.values(), key=lambda r: r["corridor_intelligence_score"], reverse=True)

    def detect_bottlenecks(self, corridors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for c in corridors:
            node = c.get("bottleneck_node_key")
            if node:
                grouped[node].append(c)
        rows = []
        for node, items in grouped.items():
            count = len(items)
            dominant = sum(1 for c in items if c.get("dominant_pathway_flag"))
            avg_intel = sum(float(c.get("corridor_intelligence_score") or 0) for c in items) / max(1, count)
            avg_bottle = sum(float(c.get("bottleneck_score") or 0) for c in items) / max(1, count)
            max_bottle = max(float(c.get("bottleneck_score") or 0) for c in items)
            reuse_total = sum(int(c.get("reuse_frequency") or 0) for c in items)
            if max_bottle >= 0.75 and count >= 3:
                cls = "critical_bottleneck"
            elif max_bottle >= 0.55 and count >= 2:
                cls = "active_bottleneck"
            elif max_bottle >= 0.35:
                cls = "emerging_bottleneck"
            else:
                cls = "weak_bottleneck"
            rows.append({
                "run_id": self.run_id,
                "run_date_sgt": self.run_date_sgt,
                "node_key": node,
                "node_role": "intermediary_bottleneck",
                "corridor_count": count,
                "dominant_corridor_count": dominant,
                "avg_corridor_intelligence_score": clamp(avg_intel),
                "avg_bottleneck_score": clamp(avg_bottle),
                "max_bottleneck_score": clamp(max_bottle),
                "reuse_frequency_total": reuse_total,
                "bottleneck_classification": cls,
                "metadata": {"corridor_hashes": [c.get("corridor_hash") for c in items[:20]]},
            })
        self.stats["bottlenecks_detected"] = len(rows)
        return sorted(rows, key=lambda r: r["max_bottleneck_score"], reverse=True)

    def add_validation(self, name: str, ok: bool, observed: float, threshold: float, message: str, details: Optional[Dict[str, Any]] = None) -> None:
        self.validation_rows.append({
            "run_id": self.run_id,
            "run_date_sgt": self.run_date_sgt,
            "validation_name": name,
            "validation_status": "PASS" if ok else "WARN",
            "observed_value": observed,
            "threshold_value": threshold,
            "message": message,
            "details": details or {},
        })

    def validate(self, corridors: List[Dict[str, Any]], inter_map: Dict[str, Dict[str, Any]]) -> int:
        self.add_validation(
            "canonical_edges_available",
            self.stats["canonical_edges_loaded"] > 0,
            self.stats["canonical_edges_loaded"],
            1,
            "Canonical edge materialized view has rows" if self.stats["canonical_edges_loaded"] > 0 else "No canonical edges loaded",
        )
        self.add_validation(
            "intermediaries_available",
            len(inter_map) > 0,
            len(inter_map),
            1,
            "Intermediary nodes are available" if inter_map else "No intermediary nodes found",
        )
        self.add_validation(
            "corridors_detected",
            len(corridors) > 0,
            len(corridors),
            1,
            "Propagation corridors detected" if corridors else "No corridors detected; this can happen if no intermediary has both inbound and outbound canonical/seed edges",
        )
        invalid_scores = sum(1 for c in corridors if not (0 <= float(c.get("corridor_intelligence_score") or 0) <= 1))
        self.add_validation("score_range_check", invalid_scores == 0, invalid_scores, 0, "All corridor scores are within [0,1]" if invalid_scores == 0 else "Some corridor scores are outside [0,1]")
        failures = sum(1 for r in self.validation_rows if r["validation_status"] != "PASS")
        self.stats["validation_failures"] = failures
        return failures

    def write_telemetry(self, status: str, error_message: Optional[str] = None) -> None:
        runtime = round(time.time() - self.started, 3)
        row = {
            "run_id": self.run_id,
            "run_date_sgt": self.run_date_sgt,
            "pipeline_name": PIPELINE_NAME,
            "status": status,
            "canonical_edges_loaded": self.stats.get("canonical_edges_loaded", 0),
            "seed_edges_loaded": self.stats.get("seed_edges_loaded", 0),
            "intermediaries_loaded": self.stats.get("intermediaries_loaded", 0),
            "two_hop_corridors_detected": self.stats.get("two_hop_corridors_detected", 0),
            "multi_hop_corridors_detected": self.stats.get("multi_hop_corridors_detected", 0),
            "corridors_persisted": self.stats.get("corridors_persisted", 0),
            "bottlenecks_detected": self.stats.get("bottlenecks_detected", 0),
            "validation_failures": self.stats.get("validation_failures", 0),
            "runtime_seconds": runtime,
            "error_message": error_message,
            "details": dict(self.stats),
        }
        self.db.upsert("structural_theme_graph_corridor_telemetry", [row], "run_id")

    def run(self) -> None:
        try:
            canonical_edges, seed_edges, intermediary_rows, raw_edges = self.fetch_inputs()
            inter_map = self.latest_intermediaries(intermediary_rows)
            edge_metrics = self.build_edge_metrics(canonical_edges, seed_edges, raw_edges)
            corridors = self.detect_corridors(edge_metrics, inter_map)
            bottlenecks = self.detect_bottlenecks(corridors)
            self.validate(corridors, inter_map)

            persisted_corridors = self.db.upsert(
                "structural_theme_graph_propagation_corridors",
                corridors,
                "run_date_sgt,corridor_hash",
            )
            self.stats["corridors_persisted"] = persisted_corridors
            self.db.upsert(
                "structural_theme_graph_corridor_bottlenecks",
                bottlenecks,
                "run_date_sgt,node_key",
            )
            self.db.upsert(
                "structural_theme_graph_corridor_validation",
                self.validation_rows,
                "run_id,validation_name",
            )
            status = "SUCCESS" if self.stats.get("validation_failures", 0) == 0 else "SUCCESS_WITH_WARNINGS"
            self.write_telemetry(status)
            print(json.dumps({"status": status, "run_id": self.run_id, **dict(self.stats)}, indent=2))
        except Exception as exc:
            self.stats["validation_failures"] = self.stats.get("validation_failures", 0) + 1
            try:
                self.write_telemetry("FAILED", str(exc))
            except Exception:
                pass
            print(json.dumps({"status": "FAILED", "run_id": self.run_id, "error": str(exc), **dict(self.stats)}, indent=2), file=sys.stderr)
            raise


def main() -> None:
    db = SupabaseClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY or "")
    CorridorEngine(db).run()


if __name__ == "__main__":
    main()
