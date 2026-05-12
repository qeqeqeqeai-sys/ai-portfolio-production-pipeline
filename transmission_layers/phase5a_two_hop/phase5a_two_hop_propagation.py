# transmission_layers/phase5a_two_hop/phase5a_two_hop_propagation.py

import os
import json
import time
import hashlib
import requests
from datetime import datetime, timezone, timedelta
from collections import defaultdict


SUPABASE_URL = os.environ["SUPABASE_URL"].rstrip("/")
SUPABASE_KEY = (
    os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    or os.environ.get("SUPABASE_ANON_KEY")
    or os.environ.get("SUPABASE_KEY")
)

if not SUPABASE_KEY:
    raise RuntimeError("Missing SUPABASE_SERVICE_ROLE_KEY / SUPABASE_ANON_KEY / SUPABASE_KEY")

THEME_NAME = os.environ.get("THEME_NAME", "ai").lower()
RUN_DATE_SGT = os.environ.get("RUN_DATE_SGT")
REPLAY_RUN_ID = os.environ.get("REPLAY_RUN_ID", "live")
GITHUB_RUN_ID = os.environ.get("GITHUB_RUN_ID")

MIN_CONFIDENCE = float(os.environ.get("MIN_TWO_HOP_CONFIDENCE", "0.0"))
MIN_TRANSMISSION_POTENTIAL = float(os.environ.get("MIN_TWO_HOP_TRANSMISSION_POTENTIAL", "0.0"))
HOP_ATTENUATION_FACTOR = float(os.environ.get("HOP_ATTENUATION_FACTOR", "0.85"))
TOP_K_PER_SOURCE = int(os.environ.get("TOP_K_PER_SOURCE", "20"))

SINGLE_HOP_TABLE = "structural_theme_graph_single_hop_propagation"
PATHS_TABLE = "structural_theme_graph_two_hop_paths"
PROPAGATION_TABLE = "structural_theme_graph_two_hop_propagation"
SNAPSHOTS_TABLE = "structural_theme_graph_two_hop_snapshots"
TELEMETRY_TABLE = "structural_theme_graph_two_hop_telemetry"


def sgt_today():
    return (datetime.now(timezone.utc) + timedelta(hours=8)).date().isoformat()


def safe_float(value, default=0.0):
    try:
        if value is None:
            return default
        return float(value)
    except Exception:
        return default


def clamp(value, low=0.0, high=1.0):
    return max(low, min(high, safe_float(value)))


def make_hash(parts):
    raw = "|".join(str(p) for p in parts)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SupabaseRestClient:
    def __init__(self):
        self.base_url = f"{SUPABASE_URL}/rest/v1"
        self.headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
        }

    def get(self, table, params=None):
        url = f"{self.base_url}/{table}"
        headers = dict(self.headers)
        headers["Accept"] = "application/json"
        response = requests.get(url, headers=headers, params=params or {}, timeout=60)

        if response.status_code >= 400:
            raise RuntimeError(f"GET {table} failed {response.status_code}: {response.text[:2000]}")

        return response.json()

    def upsert(self, table, rows, on_conflict):
        if not rows:
            return []

        url = f"{self.base_url}/{table}"
        headers = dict(self.headers)
        headers["Prefer"] = "resolution=merge-duplicates,return=representation"

        params = {"on_conflict": on_conflict}

        response = requests.post(
            url,
            headers=headers,
            params=params,
            data=json.dumps(rows),
            timeout=120,
        )

        if response.status_code >= 400:
            raise RuntimeError(f"UPSERT {table} failed {response.status_code}: {response.text[:2000]}")

        return response.json()

    def insert(self, table, rows):
        if not rows:
            return []

        url = f"{self.base_url}/{table}"
        headers = dict(self.headers)
        headers["Prefer"] = "return=representation"

        response = requests.post(
            url,
            headers=headers,
            data=json.dumps(rows),
            timeout=120,
        )

        if response.status_code >= 400:
            raise RuntimeError(f"INSERT {table} failed {response.status_code}: {response.text[:2000]}")

        return response.json()


class Phase5ATwoHopPropagationEngine:
    def __init__(self):
        self.client = SupabaseRestClient()
        self.run_date_sgt = RUN_DATE_SGT or sgt_today()
        self.theme_name = THEME_NAME
        self.start_time = time.time()

        self.telemetry = {
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

    def load_single_hop_edges(self):
        params = {
            "select": "*",
            "run_date_sgt": f"eq.{self.run_date_sgt}",
            "theme_name": f"eq.{self.theme_name}",
            "order": "propagated_pressure_score.desc.nullslast",
            "limit": "5000",
        }

        rows = self.client.get(SINGLE_HOP_TABLE, params=params)

        if not rows:
            latest_params = {
                "select": "run_date_sgt",
                "theme_name": f"eq.{self.theme_name}",
                "order": "run_date_sgt.desc",
                "limit": "1",
            }

            latest_rows = self.client.get(SINGLE_HOP_TABLE, params=latest_params)

            if latest_rows:
                self.run_date_sgt = latest_rows[0]["run_date_sgt"]

                params["run_date_sgt"] = f"eq.{self.run_date_sgt}"
                rows = self.client.get(SINGLE_HOP_TABLE, params=params)

        edges = []

        for row in rows:
            source = row.get("source_node_key") or row.get("source_node_id")
            target = row.get("target_node_key") or row.get("target_node_id")

            if not source or not target:
                continue

            if source == target:
                continue

            hop_score = safe_float(
                row.get("propagated_pressure_score"),
                safe_float(row.get("single_hop_propagation_score"), 0.0),
            )

            confidence = clamp(
                safe_float(row.get("edge_confidence_score"), 1.0)
                * safe_float(row.get("confidence_modifier"), 1.0)
            )

            transmission_potential = clamp(
                safe_float(
                    row.get("propagation_transfer_weight"),
                    safe_float(row.get("transmission_potential"), 0.0),
                )
            )

            bottleneck_modifier = clamp(row.get("bottleneck_modifier"), 1.0)
            fragility_modifier = clamp(row.get("fragility_modifier"), 1.0)
            saturation_modifier = clamp(row.get("saturation_modifier"), 1.0)
            decay_factor = clamp(
                row.get("memory_decay_factor")
                or row.get("decay_factor")
                or row.get("propagation_decay_factor"),
                1.0,
            )

            edge = {
                "source_node_id": str(source),
                "target_node_id": str(target),
                "source_node_label": row.get("source_node_label") or str(source),
                "target_node_label": row.get("target_node_label") or str(target),
                "edge_id": str(row.get("id")) if row.get("id") is not None else None,
                "hop_score": hop_score,
                "confidence": confidence,
                "transmission_potential": transmission_potential,
                "bottleneck_modifier": bottleneck_modifier,
                "fragility_risk": 1.0 - fragility_modifier,
                "saturation_suppression": saturation_modifier,
                "decay_factor": decay_factor,
                "raw": row,
            }

            edges.append(edge)

        self.telemetry["source_edges_loaded"] = len(edges)
        return edges

    def select_top_edges_per_source(self, edges):
        grouped = defaultdict(list)

        for edge in edges:
            grouped[edge["source_node_id"]].append(edge)

        selected = []

        for _, group in grouped.items():
            ranked = sorted(
                group,
                key=lambda e: (
                    e["hop_score"],
                    e["confidence"],
                    e["transmission_potential"],
                ),
                reverse=True,
            )
            selected.extend(ranked[:TOP_K_PER_SOURCE])

        return selected

    def generate_two_hop_paths(self, edges):
        outgoing = defaultdict(list)

        for edge in edges:
            outgoing[edge["source_node_id"]].append(edge)

        seen_hashes = set()
        paths = []
        propagation_rows = []

        for hop1 in edges:
            source = hop1["source_node_id"]
            intermediate = hop1["target_node_id"]

            if intermediate not in outgoing:
                continue

            for hop2 in outgoing[intermediate]:
                target = hop2["target_node_id"]

                self.telemetry["candidate_paths"] += 1

                nodes = [source, intermediate, target]

                if len(set(nodes)) != 3:
                    self.telemetry["rejected_cycles"] += 1
                    continue

                path_hash = make_hash([
                    self.theme_name,
                    self.run_date_sgt,
                    REPLAY_RUN_ID,
                    source,
                    intermediate,
                    target,
                ])

                if path_hash in seen_hashes:
                    self.telemetry["rejected_duplicates"] += 1
                    continue

                seen_hashes.add(path_hash)

                two_hop_confidence = clamp(
                    (hop1["confidence"] + hop2["confidence"]) / 2.0
                )

                if two_hop_confidence < MIN_CONFIDENCE:
                    self.telemetry["rejected_low_confidence"] += 1
                    continue

                hop1_potential = hop1["transmission_potential"]
                hop2_potential = hop2["transmission_potential"]

                two_hop_transmission_potential = clamp(
                    min(hop1_potential, hop2_potential) * two_hop_confidence
                )

                if two_hop_transmission_potential < MIN_TRANSMISSION_POTENTIAL:
                    self.telemetry["rejected_low_potential"] += 1
                    continue

                hop1_score = safe_float(hop1["hop_score"])
                hop2_score = safe_float(hop2["hop_score"])

                base_two_hop_score = hop1_score * hop2_score

                compounded_decay_factor = clamp(
                    hop1["decay_factor"] * hop2["decay_factor"]
                )

                bottleneck_accumulation = clamp(
                    min(hop1["bottleneck_modifier"], hop2["bottleneck_modifier"])
                )

                fragility_accumulation = clamp(
                    (hop1["fragility_risk"] + hop2["fragility_risk"]) / 2.0
                )

                saturation_suppression = clamp(
                    min(hop1["saturation_suppression"], hop2["saturation_suppression"])
                )

                two_hop_path_score = (
                    base_two_hop_score
                    * HOP_ATTENUATION_FACTOR
                    * compounded_decay_factor
                    * bottleneck_accumulation
                    * (1.0 - fragility_accumulation)
                    * saturation_suppression
                )

                two_hop_path_score = max(0.0, two_hop_path_score)

                if two_hop_path_score >= 0.75:
                    regime = "high"
                elif two_hop_path_score >= 0.45:
                    regime = "medium"
                elif two_hop_path_score > 0:
                    regime = "low"
                else:
                    regime = "inactive"

                path_row = {
                    "run_date_sgt": self.run_date_sgt,
                    "theme_name": self.theme_name,
                    "source_node_id": source,
                    "intermediate_node_id": intermediate,
                    "target_node_id": target,
                    "source_node_label": hop1["source_node_label"],
                    "intermediate_node_label": hop1["target_node_label"],
                    "target_node_label": hop2["target_node_label"],
                    "path_hash": path_hash,
                    "hop1_edge_id": hop1["edge_id"],
                    "hop2_edge_id": hop2["edge_id"],
                    "hop1_confidence": hop1["confidence"],
                    "hop2_confidence": hop2["confidence"],
                    "hop1_transmission_potential": hop1_potential,
                    "hop2_transmission_potential": hop2_potential,
                    "path_status": "active",
                    "rejection_reason": None,
                    "replay_run_id": REPLAY_RUN_ID,
                    "github_run_id": GITHUB_RUN_ID,
                }

                propagation_row = {
                    "run_date_sgt": self.run_date_sgt,
                    "theme_name": self.theme_name,
                    "source_node_id": source,
                    "intermediate_node_id": intermediate,
                    "target_node_id": target,
                    "source_node_label": hop1["source_node_label"],
                    "intermediate_node_label": hop1["target_node_label"],
                    "target_node_label": hop2["target_node_label"],
                    "path_hash": path_hash,
                    "hop1_score": hop1_score,
                    "hop2_score": hop2_score,
                    "base_two_hop_score": base_two_hop_score,
                    "hop_attenuation_factor": HOP_ATTENUATION_FACTOR,
                    "compounded_decay_factor": compounded_decay_factor,
                    "bottleneck_accumulation": bottleneck_accumulation,
                    "fragility_accumulation": fragility_accumulation,
                    "saturation_suppression": saturation_suppression,
                    "two_hop_path_score": two_hop_path_score,
                    "two_hop_confidence": two_hop_confidence,
                    "two_hop_transmission_potential": two_hop_transmission_potential,
                    "propagation_regime": regime,
                    "validation_status": "passed",
                    "validation_warnings": [],
                    "replay_run_id": REPLAY_RUN_ID,
                    "github_run_id": GITHUB_RUN_ID,
                }

                paths.append(path_row)
                propagation_rows.append(propagation_row)
                self.telemetry["accepted_paths"] += 1

        return paths, propagation_rows

    def create_snapshot(self, propagation_rows):
        total_paths = self.telemetry["candidate_paths"]
        active_paths = len(propagation_rows)
        rejected_paths = max(total_paths - active_paths, 0)

        if propagation_rows:
            avg_score = sum(safe_float(r["two_hop_path_score"]) for r in propagation_rows) / len(propagation_rows)
            max_score = max(safe_float(r["two_hop_path_score"]) for r in propagation_rows)
            avg_confidence = sum(safe_float(r["two_hop_confidence"]) for r in propagation_rows) / len(propagation_rows)
            avg_potential = sum(safe_float(r["two_hop_transmission_potential"]) for r in propagation_rows) / len(propagation_rows)

            top = max(propagation_rows, key=lambda r: safe_float(r["two_hop_path_score"]))
            top_path_hash = top["path_hash"]
            top_source = top["source_node_id"]
            top_intermediate = top["intermediate_node_id"]
            top_target = top["target_node_id"]
        else:
            avg_score = None
            max_score = None
            avg_confidence = None
            avg_potential = None
            top_path_hash = None
            top_source = None
            top_intermediate = None
            top_target = None

        return {
            "run_date_sgt": self.run_date_sgt,
            "theme_name": self.theme_name,
            "snapshot_type": "daily_two_hop_propagation",
            "total_paths": total_paths,
            "active_paths": active_paths,
            "rejected_paths": rejected_paths,
            "avg_two_hop_score": avg_score,
            "max_two_hop_score": max_score,
            "avg_confidence": avg_confidence,
            "avg_transmission_potential": avg_potential,
            "top_path_hash": top_path_hash,
            "top_source_node_id": top_source,
            "top_intermediate_node_id": top_intermediate,
            "top_target_node_id": top_target,
            "replay_run_id": REPLAY_RUN_ID,
            "github_run_id": GITHUB_RUN_ID,
            "snapshot_payload": {
                "phase": "5A",
                "mode": "controlled_two_hop",
                "max_depth": 2,
                "source_table": SINGLE_HOP_TABLE,
                "min_confidence": MIN_CONFIDENCE,
                "min_transmission_potential": MIN_TRANSMISSION_POTENTIAL,
                "hop_attenuation_factor": HOP_ATTENUATION_FACTOR,
                "top_k_per_source": TOP_K_PER_SOURCE,
                "telemetry": self.telemetry,
            },
        }

    def write_telemetry(self, status, error_message=None, propagation_rows=None):
        runtime_seconds = round(time.time() - self.start_time, 3)

        propagation_rows = propagation_rows or []

        if propagation_rows:
            avg_attenuation = HOP_ATTENUATION_FACTOR
            avg_bottleneck = sum(safe_float(r["bottleneck_accumulation"]) for r in propagation_rows) / len(propagation_rows)
            avg_fragility = sum(safe_float(r["fragility_accumulation"]) for r in propagation_rows) / len(propagation_rows)
            avg_saturation = sum(safe_float(r["saturation_suppression"]) for r in propagation_rows) / len(propagation_rows)
        else:
            avg_attenuation = HOP_ATTENUATION_FACTOR
            avg_bottleneck = None
            avg_fragility = None
            avg_saturation = None

        row = {
            "run_date_sgt": self.run_date_sgt,
            "theme_name": self.theme_name,
            "pipeline_name": "PHASE_5A_TWO_HOP_PROPAGATION",
            "status": status,
            "source_edges_loaded": self.telemetry["source_edges_loaded"],
            "candidate_paths": self.telemetry["candidate_paths"],
            "accepted_paths": self.telemetry["accepted_paths"],
            "rejected_cycles": self.telemetry["rejected_cycles"],
            "rejected_duplicates": self.telemetry["rejected_duplicates"],
            "rejected_low_confidence": self.telemetry["rejected_low_confidence"],
            "rejected_low_potential": self.telemetry["rejected_low_potential"],
            "propagation_rows_written": self.telemetry["propagation_rows_written"],
            "snapshot_rows_written": self.telemetry["snapshot_rows_written"],
            "avg_attenuation": avg_attenuation,
            "avg_bottleneck": avg_bottleneck,
            "avg_fragility": avg_fragility,
            "avg_saturation_suppression": avg_saturation,
            "runtime_seconds": runtime_seconds,
            "replay_run_id": REPLAY_RUN_ID,
            "github_run_id": GITHUB_RUN_ID,
            "error_message": error_message,
            "telemetry_payload": {
                "phase": "5A",
                "mode": "controlled_two_hop",
                "max_depth": 2,
                "run_date_sgt": self.run_date_sgt,
                "theme_name": self.theme_name,
                "thresholds": {
                    "min_confidence": MIN_CONFIDENCE,
                    "min_transmission_potential": MIN_TRANSMISSION_POTENTIAL,
                    "top_k_per_source": TOP_K_PER_SOURCE,
                },
            },
        }

        self.client.insert(TELEMETRY_TABLE, [row])

    def run(self):
        try:
            edges = self.load_single_hop_edges()
            selected_edges = self.select_top_edges_per_source(edges)

            path_rows, propagation_rows = self.generate_two_hop_paths(selected_edges)

            if path_rows:
                self.client.upsert(
                    PATHS_TABLE,
                    path_rows,
                    "run_date_sgt,theme_name,path_hash",
                )

            if propagation_rows:
                written = self.client.upsert(
                    PROPAGATION_TABLE,
                    propagation_rows,
                    "run_date_sgt,theme_name,path_hash",
                )
                self.telemetry["propagation_rows_written"] = len(written)

            snapshot = self.create_snapshot(propagation_rows)

            snapshot_written = self.client.upsert(
                SNAPSHOTS_TABLE,
                [snapshot],
                "run_date_sgt,theme_name,snapshot_type,replay_run_id",
            )
            self.telemetry["snapshot_rows_written"] = len(snapshot_written)

            self.write_telemetry("success", propagation_rows=propagation_rows)

            result = {
                "status": "success",
                "run_date_sgt": self.run_date_sgt,
                "theme_name": self.theme_name,
                **self.telemetry,
            }

            print(json.dumps(result, indent=2))
            return result

        except Exception as exc:
            error_message = str(exc)
            try:
                self.write_telemetry("failed", error_message=error_message)
            except Exception:
                pass

            print(json.dumps({
                "status": "failed",
                "run_date_sgt": self.run_date_sgt,
                "theme_name": self.theme_name,
                "error": error_message,
                **self.telemetry,
            }, indent=2))

            raise


if __name__ == "__main__":
    Phase5ATwoHopPropagationEngine().run()
