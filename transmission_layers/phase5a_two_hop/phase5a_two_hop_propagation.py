"""
Phase 5A — Controlled Two-Hop Propagation Layer

Bounded deterministic propagation only:
    A -> B -> C

No recursion. No NetworkX. No SDK. Supabase REST only.

Required environment variables:
    SUPABASE_URL
    SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY

Optional environment variables:
    THEME_NAME=ai
    RUN_DATE_SGT=YYYY-MM-DD
    GITHUB_RUN_ID=<github run id>
    REPLAY_RUN_ID=<replay id>
    TOP_K_NEIGHBORS=10
    MIN_EDGE_CONFIDENCE=0.20
    MIN_EDGE_TRANSMISSION_POTENTIAL=0.00
    HOP_ATTENUATION_FACTOR=0.85
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

SGT = timezone(timedelta(hours=8))
PIPELINE_NAME = "PHASE_5A_TWO_HOP_PROPAGATION"
MAX_DEPTH = 2


def now_sgt() -> datetime:
    return datetime.now(SGT)


def today_sgt() -> str:
    return now_sgt().date().isoformat()


def clamp(value: Any, lo: float = 0.0, hi: float = 1.0, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        x = float(value)
        if math.isnan(x) or math.isinf(x):
            return default
        return max(lo, min(hi, x))
    except Exception:
        return default


def stable_hash(*parts: str) -> str:
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SupabaseRestClient:
    def __init__(self) -> None:
        self.url = os.getenv("SUPABASE_URL", "").rstrip("/")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY") or ""
        if not self.url or not self.key:
            raise RuntimeError("Missing SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY/SUPABASE_ANON_KEY")
        self.base = f"{self.url}/rest/v1"
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates",
        }

    def get(self, table: str, params: Optional[Dict[str, str]] = None, timeout: int = 60) -> List[Dict[str, Any]]:
        r = requests.get(f"{self.base}/{table}", headers=self.headers, params=params or {}, timeout=timeout)
        if r.status_code >= 300:
            raise RuntimeError(f"GET {table} failed {r.status_code}: {r.text[:1000]}")
        return r.json()

    def upsert(self, table: str, rows: List[Dict[str, Any]], on_conflict: str, timeout: int = 120) -> List[Dict[str, Any]]:
        if not rows:
            return []
        headers = dict(self.headers)
        headers["Prefer"] = "return=representation,resolution=merge-duplicates"
        params = {"on_conflict": on_conflict}
        r = requests.post(f"{self.base}/{table}", headers=headers, params=params, data=json.dumps(rows), timeout=timeout)
        if r.status_code >= 300:
            raise RuntimeError(f"UPSERT {table} failed {r.status_code}: {r.text[:2000]}")
        return r.json()

    def insert(self, table: str, rows: List[Dict[str, Any]], timeout: int = 120) -> List[Dict[str, Any]]:
        if not rows:
            return []
        headers = dict(self.headers)
        headers["Prefer"] = "return=representation"
        r = requests.post(f"{self.base}/{table}", headers=headers, data=json.dumps(rows), timeout=timeout)
        if r.status_code >= 300:
            raise RuntimeError(f"INSERT {table} failed {r.status_code}: {r.text[:2000]}")
        return r.json()


@dataclass(frozen=True)
class Edge:
    edge_id: str
    theme_name: str
    source_node_id: str
    target_node_id: str
    source_node_label: Optional[str]
    target_node_label: Optional[str]
    confidence: float
    transmission_potential: float
    propagation_score: float
    decay_factor: float
    bottleneck: float
    fragility: float
    saturation: float


@dataclass(frozen=True)
class TwoHopPath:
    run_date_sgt: str
    theme_name: str
    source_node_id: str
    intermediate_node_id: str
    target_node_id: str
    source_node_label: Optional[str]
    intermediate_node_label: Optional[str]
    target_node_label: Optional[str]
    path_hash: str
    hop1_edge_id: str
    hop2_edge_id: str
    hop1_confidence: float
    hop2_confidence: float
    hop1_transmission_potential: float
    hop2_transmission_potential: float
    path_status: str
    rejection_reason: Optional[str]
    replay_run_id: Optional[str]
    github_run_id: Optional[str]


class TwoHopPropagationEngine:
    def __init__(self) -> None:
        self.client = SupabaseRestClient()
        self.theme_name = os.getenv("THEME_NAME", "ai")
        self.run_date = os.getenv("RUN_DATE_SGT", today_sgt())
        self.github_run_id = os.getenv("GITHUB_RUN_ID")
        self.replay_run_id = os.getenv("REPLAY_RUN_ID")
        self.top_k = int(os.getenv("TOP_K_NEIGHBORS", "10"))
        self.min_confidence = float(os.getenv("MIN_EDGE_CONFIDENCE", "0.20"))
        self.min_potential = float(os.getenv("MIN_EDGE_TRANSMISSION_POTENTIAL", "0.00"))
        self.hop_attenuation = float(os.getenv("HOP_ATTENUATION_FACTOR", "0.85"))
        self.telemetry: Dict[str, Any] = {
            "source_edges_loaded": 0,
            "candidate_paths": 0,
            "accepted_paths": 0,
            "rejected_cycles": 0,
            "rejected_duplicates": 0,
            "rejected_low_confidence": 0,
            "rejected_low_potential": 0,
            "propagation_rows_written": 0,
            "snapshot_rows_written": 0,
        }

    def load_edges(self) -> List[Edge]:
        """Load latest usable directed edges from single-hop propagation when available.

        Fallback to transmission potential table if single-hop score fields are absent.
        The code is intentionally defensive because earlier phases may have slightly different column names.
        """
        params = {
            "run_date_sgt": f"eq.{self.run_date}",
            "theme_name": f"eq.{self.theme_name}",
            "select": "*",
            "limit": "5000",
        }
        raw = self.client.get("structural_theme_graph_single_hop_propagation", params=params)
        if not raw:
            # fallback for replay or partially populated days
            raw = self.client.get(
                "structural_theme_graph_transmission_potential",
                params={
                    "run_date_sgt": f"eq.{self.run_date}",
                    "theme_name": f"eq.{self.theme_name}",
                    "select": "*",
                    "limit": "5000",
                },
            )

        edges: List[Edge] = []
        for i, row in enumerate(raw):
            src = row.get("source_node_id") or row.get("from_node_id") or row.get("source_id")
            tgt = row.get("target_node_id") or row.get("to_node_id") or row.get("target_id")
            if not src or not tgt or src == tgt:
                continue

            confidence = clamp(row.get("propagation_confidence", row.get("confidence", row.get("edge_confidence", 0.5))), 0, 1, 0.5)
            potential = clamp(row.get("transmission_potential", row.get("single_hop_transmission_potential", row.get("potential_score", 0.5))), 0, 1, 0.5)
            score = clamp(row.get("single_hop_propagation_score", row.get("propagation_score", row.get("transmission_score", potential))), 0, 1, potential)
            decay = clamp(row.get("decay_factor", row.get("memory_decay_factor", 1.0)), 0, 1, 1.0)
            bottleneck = clamp(row.get("bottleneck_score", row.get("bottleneck_factor", row.get("capacity_factor", 1.0))), 0, 1, 1.0)
            fragility = clamp(row.get("fragility_score", row.get("fragility", 0.0)), 0, 1, 0.0)
            saturation = clamp(row.get("saturation_score", row.get("saturation", 0.0)), 0, 1, 0.0)

            if confidence < self.min_confidence:
                continue
            if potential < self.min_potential:
                continue

            edges.append(
                Edge(
                    edge_id=str(row.get("edge_id") or row.get("id") or stable_hash(self.run_date, self.theme_name, src, tgt, str(i))),
                    theme_name=str(row.get("theme_name") or self.theme_name),
                    source_node_id=str(src),
                    target_node_id=str(tgt),
                    source_node_label=row.get("source_node_label") or row.get("source_label") or row.get("source_name"),
                    target_node_label=row.get("target_node_label") or row.get("target_label") or row.get("target_name"),
                    confidence=confidence,
                    transmission_potential=potential,
                    propagation_score=score,
                    decay_factor=decay,
                    bottleneck=bottleneck,
                    fragility=fragility,
                    saturation=saturation,
                )
            )

        edges.sort(key=lambda e: (e.source_node_id, -e.confidence, -e.transmission_potential, -e.propagation_score))
        self.telemetry["source_edges_loaded"] = len(edges)
        return edges

    def build_adjacency(self, edges: List[Edge]) -> Dict[str, List[Edge]]:
        adjacency: Dict[str, List[Edge]] = {}
        for edge in edges:
            adjacency.setdefault(edge.source_node_id, []).append(edge)
        for src in adjacency:
            adjacency[src] = sorted(
                adjacency[src],
                key=lambda e: (e.confidence, e.transmission_potential, e.propagation_score),
                reverse=True,
            )[: self.top_k]
        return adjacency

    def generate_paths(self, adjacency: Dict[str, List[Edge]]) -> Tuple[List[TwoHopPath], Dict[str, Tuple[Edge, Edge]]]:
        paths: List[TwoHopPath] = []
        edge_pairs: Dict[str, Tuple[Edge, Edge]] = {}
        seen: set[str] = set()

        for source, first_hops in adjacency.items():
            for hop1 in first_hops:
                intermediate = hop1.target_node_id
                second_hops = adjacency.get(intermediate, [])
                for hop2 in second_hops:
                    target = hop2.target_node_id
                    self.telemetry["candidate_paths"] += 1

                    # Max depth hard stop is implicit: exactly two edges only.
                    nodes = [source, intermediate, target]
                    if len(set(nodes)) != 3:
                        self.telemetry["rejected_cycles"] += 1
                        continue

                    if hop1.confidence < self.min_confidence or hop2.confidence < self.min_confidence:
                        self.telemetry["rejected_low_confidence"] += 1
                        continue
                    if hop1.transmission_potential < self.min_potential or hop2.transmission_potential < self.min_potential:
                        self.telemetry["rejected_low_potential"] += 1
                        continue

                    p_hash = stable_hash(self.theme_name, source, intermediate, target)
                    if p_hash in seen:
                        self.telemetry["rejected_duplicates"] += 1
                        continue
                    seen.add(p_hash)

                    paths.append(
                        TwoHopPath(
                            run_date_sgt=self.run_date,
                            theme_name=self.theme_name,
                            source_node_id=source,
                            intermediate_node_id=intermediate,
                            target_node_id=target,
                            source_node_label=hop1.source_node_label,
                            intermediate_node_label=hop1.target_node_label or hop2.source_node_label,
                            target_node_label=hop2.target_node_label,
                            path_hash=p_hash,
                            hop1_edge_id=hop1.edge_id,
                            hop2_edge_id=hop2.edge_id,
                            hop1_confidence=hop1.confidence,
                            hop2_confidence=hop2.confidence,
                            hop1_transmission_potential=hop1.transmission_potential,
                            hop2_transmission_potential=hop2.transmission_potential,
                            path_status="active",
                            rejection_reason=None,
                            replay_run_id=self.replay_run_id,
                            github_run_id=self.github_run_id,
                        )
                    )
                    edge_pairs[p_hash] = (hop1, hop2)

        self.telemetry["accepted_paths"] = len(paths)
        return paths, edge_pairs

    def score_path(self, path: TwoHopPath, hop1: Edge, hop2: Edge) -> Dict[str, Any]:
        base = clamp(hop1.propagation_score * hop2.propagation_score, 0, 1)
        compounded_decay = clamp(hop1.decay_factor * hop2.decay_factor, 0, 1, 1)
        bottleneck_accumulation = clamp(min(hop1.bottleneck, hop2.bottleneck), 0, 1, 1)
        fragility_accumulation = clamp((hop1.fragility + hop2.fragility) / 2.0, 0, 1, 0)
        saturation_suppression = clamp(1.0 - max(hop1.saturation, hop2.saturation), 0, 1, 1)
        confidence = clamp(math.sqrt(hop1.confidence * hop2.confidence), 0, 1, 0)
        potential = clamp(math.sqrt(hop1.transmission_potential * hop2.transmission_potential), 0, 1, 0)

        two_hop_score = clamp(
            base
            * self.hop_attenuation
            * compounded_decay
            * bottleneck_accumulation
            * (1.0 - fragility_accumulation)
            * saturation_suppression,
            0,
            1,
            0,
        )
        two_hop_potential = clamp(two_hop_score * confidence * potential, 0, 1, 0)

        warnings: List[str] = []
        if confidence < 0.35:
            warnings.append("low_two_hop_confidence")
        if bottleneck_accumulation < 0.35:
            warnings.append("material_bottleneck")
        if fragility_accumulation > 0.70:
            warnings.append("high_fragility_accumulation")
        if saturation_suppression < 0.35:
            warnings.append("high_saturation_suppression")

        regime = "strong"
        if two_hop_potential < 0.20:
            regime = "weak"
        elif two_hop_potential < 0.45:
            regime = "moderate"
        elif two_hop_potential < 0.70:
            regime = "elevated"

        return {
            "run_date_sgt": path.run_date_sgt,
            "theme_name": path.theme_name,
            "source_node_id": path.source_node_id,
            "intermediate_node_id": path.intermediate_node_id,
            "target_node_id": path.target_node_id,
            "source_node_label": path.source_node_label,
            "intermediate_node_label": path.intermediate_node_label,
            "target_node_label": path.target_node_label,
            "path_hash": path.path_hash,
            "hop1_score": hop1.propagation_score,
            "hop2_score": hop2.propagation_score,
            "base_two_hop_score": base,
            "hop_attenuation_factor": self.hop_attenuation,
            "compounded_decay_factor": compounded_decay,
            "bottleneck_accumulation": bottleneck_accumulation,
            "fragility_accumulation": fragility_accumulation,
            "saturation_suppression": saturation_suppression,
            "two_hop_path_score": two_hop_score,
            "two_hop_confidence": confidence,
            "two_hop_transmission_potential": two_hop_potential,
            "propagation_regime": regime,
            "validation_status": "warning" if warnings else "passed",
            "validation_warnings": warnings,
            "replay_run_id": self.replay_run_id,
            "github_run_id": self.github_run_id,
        }

    def build_snapshot(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not rows:
            return {
                "run_date_sgt": self.run_date,
                "theme_name": self.theme_name,
                "snapshot_type": "daily_two_hop_propagation",
                "total_paths": 0,
                "active_paths": 0,
                "rejected_paths": int(self.telemetry["rejected_cycles"] + self.telemetry["rejected_duplicates"] + self.telemetry["rejected_low_confidence"] + self.telemetry["rejected_low_potential"]),
                "replay_run_id": self.replay_run_id,
                "github_run_id": self.github_run_id,
                "snapshot_payload": {"top_paths": []},
            }

        top_rows = sorted(rows, key=lambda r: r.get("two_hop_transmission_potential") or 0, reverse=True)
        top = top_rows[0]

        def avg(key: str) -> Optional[float]:
            vals = [float(r[key]) for r in rows if r.get(key) is not None]
            return sum(vals) / len(vals) if vals else None

        payload = {
            "top_paths": [
                {
                    "path_hash": r.get("path_hash"),
                    "source": r.get("source_node_label") or r.get("source_node_id"),
                    "intermediate": r.get("intermediate_node_label") or r.get("intermediate_node_id"),
                    "target": r.get("target_node_label") or r.get("target_node_id"),
                    "score": r.get("two_hop_path_score"),
                    "confidence": r.get("two_hop_confidence"),
                    "potential": r.get("two_hop_transmission_potential"),
                    "regime": r.get("propagation_regime"),
                }
                for r in top_rows[:20]
            ],
            "config": {
                "max_depth": MAX_DEPTH,
                "top_k_neighbors": self.top_k,
                "min_confidence": self.min_confidence,
                "min_potential": self.min_potential,
                "hop_attenuation": self.hop_attenuation,
            },
        }

        return {
            "run_date_sgt": self.run_date,
            "theme_name": self.theme_name,
            "snapshot_type": "daily_two_hop_propagation",
            "total_paths": len(rows),
            "active_paths": len(rows),
            "rejected_paths": int(self.telemetry["rejected_cycles"] + self.telemetry["rejected_duplicates"] + self.telemetry["rejected_low_confidence"] + self.telemetry["rejected_low_potential"]),
            "avg_two_hop_score": avg("two_hop_path_score"),
            "max_two_hop_score": max([float(r.get("two_hop_path_score") or 0) for r in rows]),
            "avg_confidence": avg("two_hop_confidence"),
            "avg_transmission_potential": avg("two_hop_transmission_potential"),
            "top_path_hash": top.get("path_hash"),
            "top_source_node_id": top.get("source_node_id"),
            "top_intermediate_node_id": top.get("intermediate_node_id"),
            "top_target_node_id": top.get("target_node_id"),
            "replay_run_id": self.replay_run_id,
            "github_run_id": self.github_run_id,
            "snapshot_payload": payload,
        }

    def write_telemetry(self, status: str, runtime_seconds: float, error_message: Optional[str] = None) -> None:
        row = {
            "run_date_sgt": self.run_date,
            "theme_name": self.theme_name,
            "pipeline_name": PIPELINE_NAME,
            "status": status,
            "source_edges_loaded": self.telemetry.get("source_edges_loaded", 0),
            "candidate_paths": self.telemetry.get("candidate_paths", 0),
            "accepted_paths": self.telemetry.get("accepted_paths", 0),
            "rejected_cycles": self.telemetry.get("rejected_cycles", 0),
            "rejected_duplicates": self.telemetry.get("rejected_duplicates", 0),
            "rejected_low_confidence": self.telemetry.get("rejected_low_confidence", 0),
            "rejected_low_potential": self.telemetry.get("rejected_low_potential", 0),
            "propagation_rows_written": self.telemetry.get("propagation_rows_written", 0),
            "snapshot_rows_written": self.telemetry.get("snapshot_rows_written", 0),
            "avg_attenuation": self.hop_attenuation,
            "avg_bottleneck": self.telemetry.get("avg_bottleneck"),
            "avg_fragility": self.telemetry.get("avg_fragility"),
            "avg_saturation_suppression": self.telemetry.get("avg_saturation_suppression"),
            "runtime_seconds": round(runtime_seconds, 3),
            "replay_run_id": self.replay_run_id,
            "github_run_id": self.github_run_id,
            "error_message": error_message,
            "telemetry_payload": {
                "max_depth": MAX_DEPTH,
                "top_k_neighbors": self.top_k,
                "min_confidence": self.min_confidence,
                "min_potential": self.min_potential,
                "hop_attenuation": self.hop_attenuation,
            },
        }
        self.client.insert("structural_theme_graph_two_hop_telemetry", [row])

    def run(self) -> None:
        started = time.time()
        try:
            edges = self.load_edges()
            adjacency = self.build_adjacency(edges)
            paths, edge_pairs = self.generate_paths(adjacency)

            path_rows = [asdict(p) for p in paths]
            self.client.upsert(
                "structural_theme_graph_two_hop_paths",
                path_rows,
                on_conflict="run_date_sgt,theme_name,path_hash",
            )

            propagation_rows: List[Dict[str, Any]] = []
            for path in paths:
                hop1, hop2 = edge_pairs[path.path_hash]
                propagation_rows.append(self.score_path(path, hop1, hop2))

            if propagation_rows:
                self.client.upsert(
                    "structural_theme_graph_two_hop_propagation",
                    propagation_rows,
                    on_conflict="run_date_sgt,theme_name,path_hash",
                )
            self.telemetry["propagation_rows_written"] = len(propagation_rows)

            if propagation_rows:
                self.telemetry["avg_bottleneck"] = sum(float(r["bottleneck_accumulation"]) for r in propagation_rows) / len(propagation_rows)
                self.telemetry["avg_fragility"] = sum(float(r["fragility_accumulation"]) for r in propagation_rows) / len(propagation_rows)
                self.telemetry["avg_saturation_suppression"] = sum(float(r["saturation_suppression"]) for r in propagation_rows) / len(propagation_rows)

            snapshot = self.build_snapshot(propagation_rows)
            self.client.upsert(
                "structural_theme_graph_two_hop_snapshots",
                [snapshot],
                on_conflict="run_date_sgt,theme_name,snapshot_type,replay_run_id",
            )
            self.telemetry["snapshot_rows_written"] = 1

            runtime = time.time() - started
            self.write_telemetry("success", runtime)
            print(json.dumps({"status": "success", "run_date_sgt": self.run_date, "theme_name": self.theme_name, **self.telemetry}, indent=2))
        except Exception as exc:
            runtime = time.time() - started
            try:
                self.write_telemetry("failed", runtime, str(exc)[:1500])
            except Exception as telemetry_exc:
                print(f"Telemetry write failed: {telemetry_exc}", file=sys.stderr)
            raise


if __name__ == "__main__":
    TwoHopPropagationEngine().run()
