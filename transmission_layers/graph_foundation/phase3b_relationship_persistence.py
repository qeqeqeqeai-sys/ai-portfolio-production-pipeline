import math
import os
import statistics
import time
from collections import defaultdict
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from graph_supabase_client import SupabaseRestClient


PIPELINE_NAME = "PHASE_3B_RELATIONSHIP_PERSISTENCE"
SNAPSHOT_VERSION = "phase3b_v1"

ANCHOR_THEME_NAME = os.getenv("ANCHOR_THEME_NAME", "ai").strip().lower()
THEME_NAME = os.getenv("THEME_NAME", "").strip().lower()
LOOKBACK_DAYS = int(os.getenv("LOOKBACK_DAYS", "365"))
MAX_HISTORY_ROWS = int(os.getenv("MAX_HISTORY_ROWS", "10000"))
MIN_OBSERVATIONS_FOR_STABILITY = int(os.getenv("MIN_OBSERVATIONS_FOR_STABILITY", "2"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_date_sgt() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def parse_date(value: Any) -> Optional[date]:
    if value is None:
        return None
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)[:10]).date()
    except Exception:
        return None


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
    return max(0.0, min(1.0, safe_float(value, 0.0) or 0.0))


def days_between(a: Optional[date], b: Optional[date]) -> int:
    if not a or not b:
        return 0
    return max(0, (b - a).days + 1)


def snapshot_id_for() -> str:
    return f"{SNAPSHOT_VERSION}_{ANCHOR_THEME_NAME}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


def fetch_edge_history(client: SupabaseRestClient) -> List[Dict[str, Any]]:
    filters = {"anchor_theme_name": f"eq.{ANCHOR_THEME_NAME}"}
    if THEME_NAME:
        filters["theme_name"] = f"eq.{THEME_NAME}"

    return client.select(
        "structural_theme_graph_edge_history",
        columns="*",
        filters=filters,
        order="run_date_sgt.desc",
        limit=MAX_HISTORY_ROWS,
    )


def group_history_by_edge(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped = defaultdict(list)
    for row in rows:
        if row.get("edge_key"):
            grouped[row["edge_key"]].append(row)

    for edge_key in grouped:
        grouped[edge_key].sort(key=lambda r: str(r.get("run_date_sgt") or ""))

    return grouped


def volatility_score(values: List[float]) -> float:
    if len(values) < 2:
        return 0.0
    try:
        return clamp01(statistics.pstdev(values))
    except Exception:
        return 0.0


def trend_metrics(values: List[float]) -> Tuple[float, Optional[float], float]:
    if not values:
        return 0.0, None, 0.0

    first = values[0]
    latest = values[-1]
    change_abs = latest - first
    change_pct = change_abs / abs(first) if abs(first) > 1e-9 else None
    slope = change_abs / (len(values) - 1) if len(values) >= 2 else 0.0
    return change_abs, change_pct, slope


def classify_temporal_regime(
    observation_count: int,
    persistence_ratio: float,
    strength_change_abs: float,
    volatility: float,
    latest_strength: float,
    days_since_last_seen: int,
) -> Tuple[str, str]:
    if observation_count < MIN_OBSERVATIONS_FOR_STABILITY:
        return ("emerging", "new") if days_since_last_seen <= 7 else ("insufficient_history", "active")

    if days_since_last_seen > 30:
        return "dormant", "dormant"
    if volatility >= 0.20:
        return "volatile", "volatile"
    if strength_change_abs >= 0.08 and latest_strength >= 0.35:
        return "reinforcing", "reinforced"
    if strength_change_abs <= -0.08:
        return "decaying", "weakening"
    if persistence_ratio >= 0.50 and volatility < 0.15:
        return "stable", "active"
    if persistence_ratio < 0.20:
        return "emerging", "new"
    return "stable", "active"


def compute_edge_stability(edge_key: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    today = parse_date(run_date_sgt()) or date.today()
    dates = [parse_date(row.get("run_date_sgt")) for row in history]
    dates = [d for d in dates if d is not None]

    first_seen = min(dates) if dates else today
    last_seen = max(dates) if dates else today

    observation_count = len(history)
    active_days = days_between(first_seen, last_seen)
    lookback_days = max(1, min(LOOKBACK_DAYS, days_between(first_seen, today)))
    persistence_ratio = min(1.0, observation_count / lookback_days)

    strengths = [clamp01(row.get("edge_strength")) for row in history]
    confidences = [clamp01(row.get("confidence_score")) for row in history]
    intensities = [clamp01(row.get("evidence_intensity")) for row in history]
    persistence_scores = [clamp01(row.get("persistence_score")) for row in history]

    latest_row = history[-1]
    avg_strength = sum(strengths) / len(strengths) if strengths else 0.0
    latest_strength = strengths[-1] if strengths else 0.0
    min_strength = min(strengths) if strengths else 0.0
    max_strength = max(strengths) if strengths else 0.0
    strength_change_abs, strength_change_pct, slope = trend_metrics(strengths)
    vol = volatility_score(strengths)

    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
    avg_intensity = sum(intensities) / len(intensities) if intensities else 0.0
    avg_persistence = sum(persistence_scores) / len(persistence_scores) if persistence_scores else 0.0

    days_since_last_seen = max(0, (today - last_seen).days)

    stability_score = clamp01(0.35 * persistence_ratio + 0.25 * avg_confidence + 0.20 * avg_intensity + 0.20 * (1.0 - vol))
    reinforcement_score = clamp01(max(0.0, strength_change_abs) * 2.0 + max(0.0, slope) * 5.0 + 0.25 * latest_strength + 0.20 * avg_intensity)
    decay_score = clamp01(max(0.0, -strength_change_abs) * 2.0 + max(0.0, -slope) * 5.0 + min(1.0, days_since_last_seen / 60.0) * 0.35)
    emergence_score = clamp01((1.0 if observation_count <= 2 else 0.0) * 0.35 + latest_strength * 0.35 + avg_intensity * 0.20 + (1.0 if days_since_last_seen <= 7 else 0.0) * 0.10)

    temporal_regime, relationship_status = classify_temporal_regime(
        observation_count, persistence_ratio, strength_change_abs, vol, latest_strength, days_since_last_seen
    )

    return {
        "run_date_sgt": run_date_sgt(),
        "edge_key": edge_key,
        "source_node_key": latest_row.get("source_node_key"),
        "target_node_key": latest_row.get("target_node_key"),
        "edge_type": latest_row.get("edge_type"),
        "theme_name": latest_row.get("theme_name"),
        "anchor_theme_name": latest_row.get("anchor_theme_name") or ANCHOR_THEME_NAME,
        "first_seen_date_sgt": first_seen.isoformat(),
        "last_seen_date_sgt": last_seen.isoformat(),
        "observation_count": observation_count,
        "active_days": active_days,
        "persistence_ratio": round(persistence_ratio, 6),
        "avg_edge_strength": round(avg_strength, 6),
        "latest_edge_strength": round(latest_strength, 6),
        "min_edge_strength": round(min_strength, 6),
        "max_edge_strength": round(max_strength, 6),
        "strength_change_abs": round(strength_change_abs, 6),
        "strength_change_pct": round(strength_change_pct, 6) if strength_change_pct is not None else None,
        "avg_confidence_score": round(avg_confidence, 6),
        "avg_evidence_intensity": round(avg_intensity, 6),
        "avg_persistence_score": round(avg_persistence, 6),
        "stability_score": round(stability_score, 6),
        "reinforcement_score": round(reinforcement_score, 6),
        "decay_score": round(decay_score, 6),
        "emergence_score": round(emergence_score, 6),
        "temporal_regime": temporal_regime,
        "relationship_status": relationship_status,
        "stability_metadata": {
            "phase": "3B",
            "pipeline_name": PIPELINE_NAME,
            "lookback_days": LOOKBACK_DAYS,
            "volatility_score": round(vol, 6),
            "days_since_last_seen": days_since_last_seen,
            "slope_proxy": round(slope, 6),
            "recent_history_points": [
                {
                    "run_date_sgt": row.get("run_date_sgt"),
                    "edge_strength": row.get("edge_strength"),
                    "confidence_score": row.get("confidence_score"),
                    "evidence_intensity": row.get("evidence_intensity"),
                    "persistence_score": row.get("persistence_score"),
                    "evidence_count": row.get("evidence_count"),
                }
                for row in history[-20:]
            ],
        },
        "updated_at": utc_now_iso(),
    }


def validate_rows(rows: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    errors, warnings = [], []

    if not rows:
        warnings.append("No edge stability rows generated.")

    for row in rows:
        for field in ["run_date_sgt", "edge_key", "source_node_key", "target_node_key", "edge_type", "temporal_regime", "relationship_status"]:
            if not row.get(field):
                errors.append(f"Missing {field}: {row}")

        for metric in ["persistence_ratio", "avg_edge_strength", "latest_edge_strength", "min_edge_strength", "max_edge_strength",
                       "avg_confidence_score", "avg_evidence_intensity", "avg_persistence_score", "stability_score",
                       "reinforcement_score", "decay_score", "emergence_score"]:
            value = safe_float(row.get(metric), None)
            if value is None or value < 0 or value > 1:
                errors.append(f"{metric} out of range for {row.get('edge_key')}: {value}")

    if errors:
        return "failed", errors, warnings
    if warnings:
        return "warning", errors, warnings
    return "passed", errors, warnings


def top_edges(rows: List[Dict[str, Any]], metric: str, n: int = 10) -> List[Dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda r: safe_float(r.get(metric), 0.0) or 0.0, reverse=True)
    return [
        {
            "edge_key": row.get("edge_key"),
            "source_node_key": row.get("source_node_key"),
            "target_node_key": row.get("target_node_key"),
            "edge_type": row.get("edge_type"),
            "theme_name": row.get("theme_name"),
            metric: row.get(metric),
            "temporal_regime": row.get("temporal_regime"),
            "relationship_status": row.get("relationship_status"),
            "observation_count": row.get("observation_count"),
        }
        for row in sorted_rows[:n]
    ]


def create_snapshot(client: SupabaseRestClient, rows: List[Dict[str, Any]],
                    validation_status: str, validation_errors: List[str], validation_warnings: List[str]) -> str:
    snapshot_id = snapshot_id_for()

    def avg(metric: str) -> Optional[float]:
        values = [safe_float(row.get(metric), 0.0) or 0.0 for row in rows]
        return round(sum(values) / len(values), 6) if values else None

    def count_regime(regime: str) -> int:
        return sum(1 for row in rows if row.get("temporal_regime") == regime)

    client.insert("structural_theme_graph_persistence_snapshots", [{
        "snapshot_id": snapshot_id,
        "run_date_sgt": run_date_sgt(),
        "snapshot_version": SNAPSHOT_VERSION,
        "anchor_theme_name": ANCHOR_THEME_NAME,
        "theme_name": THEME_NAME or None,
        "edges_analyzed": len(rows),
        "stable_edges": count_regime("stable"),
        "emerging_edges": count_regime("emerging"),
        "reinforcing_edges": count_regime("reinforcing"),
        "decaying_edges": count_regime("decaying"),
        "volatile_edges": count_regime("volatile"),
        "dormant_edges": count_regime("dormant"),
        "avg_stability_score": avg("stability_score"),
        "avg_reinforcement_score": avg("reinforcement_score"),
        "avg_decay_score": avg("decay_score"),
        "avg_emergence_score": avg("emergence_score"),
        "strongest_persistent_edges": top_edges(rows, "stability_score", 10),
        "newest_emerging_edges": top_edges(rows, "emergence_score", 10),
        "weakening_edges": top_edges(rows, "decay_score", 10),
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "snapshot_metadata": {
            "phase": "3B",
            "pipeline_name": PIPELINE_NAME,
            "lookback_days": LOOKBACK_DAYS,
            "min_observations_for_stability": MIN_OBSERVATIONS_FOR_STABILITY,
        },
    }], return_rows=False)

    return snapshot_id


def write_telemetry(client: SupabaseRestClient, status: str, snapshot_id: Optional[str],
                    edges_read: int, stability_rows_upserted: int, validation_status: str,
                    validation_errors: List[str], validation_warnings: List[str],
                    runtime_seconds: float, error_message: Optional[str], metadata: Dict[str, Any]) -> None:
    client.insert("structural_theme_graph_persistence_telemetry", [{
        "pipeline_name": PIPELINE_NAME,
        "snapshot_id": snapshot_id,
        "status": status,
        "edges_read": edges_read,
        "stability_rows_upserted": stability_rows_upserted,
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


def main():
    start = time.time()
    client = SupabaseRestClient()
    snapshot_id = None
    rows = []
    history_rows_read = 0

    try:
        history_rows = fetch_edge_history(client)
        history_rows_read = len(history_rows)

        grouped = group_history_by_edge(history_rows)
        rows = [compute_edge_stability(edge_key, history) for edge_key, history in grouped.items()]

        validation_status, validation_errors, validation_warnings = validate_rows(rows)
        if validation_status == "failed":
            raise RuntimeError("Relationship persistence validation failed: " + " | ".join(validation_errors[:10]))

        if rows:
            client.upsert(
                "structural_theme_graph_edge_stability",
                rows,
                on_conflict="run_date_sgt,edge_key",
                return_rows=False,
            )

        snapshot_id = create_snapshot(client, rows, validation_status, validation_errors, validation_warnings)

        regime_counts = {
            "stable": sum(1 for r in rows if r.get("temporal_regime") == "stable"),
            "emerging": sum(1 for r in rows if r.get("temporal_regime") == "emerging"),
            "reinforcing": sum(1 for r in rows if r.get("temporal_regime") == "reinforcing"),
            "decaying": sum(1 for r in rows if r.get("temporal_regime") == "decaying"),
            "volatile": sum(1 for r in rows if r.get("temporal_regime") == "volatile"),
            "dormant": sum(1 for r in rows if r.get("temporal_regime") == "dormant"),
        }

        metadata = {
            "phase": "3B",
            "anchor_theme_name": ANCHOR_THEME_NAME,
            "theme_name": THEME_NAME or None,
            "lookback_days": LOOKBACK_DAYS,
            "history_rows_read": history_rows_read,
            "unique_edges_analyzed": len(rows),
            "regime_counts": regime_counts,
        }

        status = "success" if validation_status == "passed" else "warning"
        write_telemetry(client, status, snapshot_id, history_rows_read, len(rows),
                        validation_status, validation_errors, validation_warnings,
                        time.time() - start, None, metadata)

        print("Phase 3B Relationship Persistence & Temporal Stability completed.")
        print(f"History rows read: {history_rows_read}")
        print(f"Unique edges analyzed: {len(rows)}")
        print(f"Snapshot: {snapshot_id}")
        print(f"Validation: {validation_status}")
        print(f"Regime counts: {regime_counts}")

    except Exception as exc:
        write_telemetry(
            client, "failed", snapshot_id, history_rows_read, 0, "failed",
            [str(exc)], [], time.time() - start, str(exc),
            {
                "phase": "3B",
                "anchor_theme_name": ANCHOR_THEME_NAME,
                "theme_name": THEME_NAME or None,
                "lookback_days": LOOKBACK_DAYS,
            },
        )
        raise


if __name__ == "__main__":
    main()
