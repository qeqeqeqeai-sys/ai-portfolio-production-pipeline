import math
import os
import re
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from graph_supabase_client import SupabaseRestClient


PIPELINE_NAME = "PHASE_3D_STRUCTURAL_PRESSURE_ACCUMULATION"
SNAPSHOT_VERSION = "phase3d_v1"

ANCHOR_THEME_NAME = os.getenv("ANCHOR_THEME_NAME", "ai").strip().lower()
THEME_NAME = os.getenv("THEME_NAME", "").strip().lower()
MAX_ROWS = int(os.getenv("MAX_ROWS", "20000"))

PRESSURE_HIGH_THRESHOLD = float(os.getenv("PRESSURE_HIGH_THRESHOLD", "0.65"))
PRESSURE_EXTREME_THRESHOLD = float(os.getenv("PRESSURE_EXTREME_THRESHOLD", "0.82"))
PRESSURE_MODERATE_THRESHOLD = float(os.getenv("PRESSURE_MODERATE_THRESHOLD", "0.35"))


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_date_sgt() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def snapshot_id_for() -> str:
    return f"{SNAPSHOT_VERSION}_{ANCHOR_THEME_NAME}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"


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


def slug(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def fetch_rows(client: SupabaseRestClient, table: str) -> List[Dict[str, Any]]:
    filters = {"anchor_theme_name": f"eq.{ANCHOR_THEME_NAME}"}
    if THEME_NAME:
        filters["theme_name"] = f"eq.{THEME_NAME}"

    return client.select(
        table,
        columns="*",
        filters=filters,
        order="run_date_sgt.desc",
        limit=MAX_ROWS,
    )


def pressure_regime(score: float) -> str:
    if score >= PRESSURE_EXTREME_THRESHOLD:
        return "extreme_pressure"
    if score >= PRESSURE_HIGH_THRESHOLD:
        return "high_pressure"
    if score >= PRESSURE_MODERATE_THRESHOLD:
        return "moderate_pressure"
    return "low_pressure"


def pressure_direction(positive_pressure: float, negative_pressure: float) -> str:
    total = positive_pressure + negative_pressure
    if total <= 1e-9:
        return "neutral"
    ratio = abs(positive_pressure - negative_pressure) / total
    if ratio < 0.15:
        return "mixed"
    return "positive" if positive_pressure > negative_pressure else "negative"


def pressure_status(
    pressure_score: float,
    saturation_score: float,
    imbalance_score: float,
    reinforcing_pressure: float,
    decay_pressure: float,
    persistence_pressure: float,
) -> str:
    if saturation_score >= 0.80:
        return "saturated"
    if imbalance_score >= 0.65:
        return "imbalanced"
    if pressure_score >= PRESSURE_HIGH_THRESHOLD and decay_pressure >= 0.45:
        return "releasing"
    if pressure_score >= PRESSURE_HIGH_THRESHOLD:
        return "stressed"
    if persistence_pressure >= 0.60:
        return "persistent"
    if reinforcing_pressure >= 0.45:
        return "building"
    return "normal"


def edge_positive_negative(row: Dict[str, Any]) -> Tuple[float, float]:
    directional = safe_float(row.get("directional_strength"), 0.0) or 0.0
    strength = clamp01(row.get("latest_edge_strength") or row.get("edge_strength") or row.get("avg_edge_strength"))

    if directional > 0:
        return strength, 0.0
    if directional < 0:
        return 0.0, strength

    status = str(row.get("relationship_status") or "")
    regime = str(row.get("temporal_regime") or "")

    if status in {"weakening", "dormant"} or regime in {"decaying", "dormant"}:
        return 0.0, strength

    return strength * 0.5, strength * 0.5


def transition_positive_negative(row: Dict[str, Any]) -> Tuple[float, float]:
    direction = row.get("transition_direction")
    strength = clamp01(row.get("transition_strength"))

    if direction in {"strengthening", "stabilizing", "emerging"}:
        return strength, 0.0
    if direction in {"weakening", "destabilizing", "dormant"}:
        return 0.0, strength
    return strength * 0.5, strength * 0.5


def drift_positive_negative(row: Dict[str, Any]) -> Tuple[float, float]:
    drift_direction = row.get("drift_direction")
    dimension = str(row.get("drift_dimension") or "")
    magnitude = clamp01(row.get("drift_magnitude"))

    negative_dimensions = {"decay_score"}
    positive_dimensions = {"reinforcement_score", "stability_score", "emergence_score", "avg_confidence_score", "avg_evidence_intensity"}

    if dimension in negative_dimensions:
        return (0.0, magnitude) if drift_direction == "increasing" else (magnitude, 0.0)

    if dimension in positive_dimensions:
        return (magnitude, 0.0) if drift_direction == "increasing" else (0.0, magnitude)

    return magnitude * 0.5, magnitude * 0.5


def pressure_key(scope: str, values: Dict[str, Any]) -> str:
    parts = [
        scope,
        values.get("anchor_theme_name") or ANCHOR_THEME_NAME,
        values.get("theme_name") or "",
        values.get("source_node_key") or "",
        values.get("target_node_key") or "",
        values.get("target_node_type") or "",
        values.get("edge_type") or "",
    ]
    return "pressure:" + ":".join(slug(p) for p in parts if p != "")


def build_group_rows(
    *,
    scope: str,
    stability_rows: List[Dict[str, Any]],
    transition_rows: List[Dict[str, Any]],
    drift_rows: List[Dict[str, Any]],
    values: Dict[str, Any],
) -> Dict[str, Any]:
    pos_edge, neg_edge = 0.0, 0.0
    for row in stability_rows:
        p, n = edge_positive_negative(row)
        pos_edge += p
        neg_edge += n

    pos_transition, neg_transition = 0.0, 0.0
    for row in transition_rows:
        p, n = transition_positive_negative(row)
        pos_transition += p
        neg_transition += n

    pos_drift, neg_drift = 0.0, 0.0
    for row in drift_rows:
        p, n = drift_positive_negative(row)
        pos_drift += p
        neg_drift += n

    contributing_edges = len(stability_rows)
    contributing_transitions = len(transition_rows)
    contributing_drift_events = len(drift_rows)

    normalizer = max(1.0, contributing_edges + contributing_transitions + contributing_drift_events)

    positive_pressure = clamp01((pos_edge + pos_transition + pos_drift) / normalizer)
    negative_pressure = clamp01((neg_edge + neg_transition + neg_drift) / normalizer)

    reinforcing_pressure = clamp01(sum(clamp01(r.get("reinforcement_score")) for r in stability_rows) / max(1, contributing_edges))
    decay_pressure = clamp01(sum(clamp01(r.get("decay_score")) for r in stability_rows) / max(1, contributing_edges))
    emergence_pressure = clamp01(sum(clamp01(r.get("emergence_score")) for r in stability_rows) / max(1, contributing_edges))
    drift_pressure = clamp01(sum(clamp01(r.get("drift_magnitude")) for r in drift_rows) / max(1, contributing_drift_events))
    persistence_pressure = clamp01(sum(clamp01(r.get("stability_score")) for r in stability_rows) / max(1, contributing_edges))

    volatile_edges = sum(1 for r in stability_rows if r.get("temporal_regime") == "volatile")
    volatile_transitions = sum(1 for r in transition_rows if r.get("transition_direction") in {"destabilizing", "mixed"})
    volatility_pressure = clamp01((volatile_edges + volatile_transitions) / max(1, contributing_edges + contributing_transitions))

    gross_pressure = positive_pressure + negative_pressure
    imbalance_score = clamp01(abs(positive_pressure - negative_pressure) / max(1e-9, gross_pressure)) if gross_pressure > 0 else 0.0

    saturation_score = clamp01(
        0.35 * persistence_pressure
        + 0.25 * drift_pressure
        + 0.20 * reinforcing_pressure
        + 0.20 * max(positive_pressure, negative_pressure)
    )

    pressure_score = clamp01(
        0.25 * max(positive_pressure, negative_pressure)
        + 0.20 * reinforcing_pressure
        + 0.15 * decay_pressure
        + 0.15 * emergence_pressure
        + 0.15 * drift_pressure
        + 0.10 * persistence_pressure
    )

    direction = pressure_direction(positive_pressure, negative_pressure)
    regime = pressure_regime(pressure_score)
    status = pressure_status(
        pressure_score,
        saturation_score,
        imbalance_score,
        reinforcing_pressure,
        decay_pressure,
        persistence_pressure,
    )

    row = {
        "run_date_sgt": run_date_sgt(),
        "pressure_key": pressure_key(scope, values),
        "pressure_scope": scope,
        "anchor_theme_name": values.get("anchor_theme_name") or ANCHOR_THEME_NAME,
        "theme_name": values.get("theme_name"),
        "source_node_key": values.get("source_node_key"),
        "target_node_key": values.get("target_node_key"),
        "target_node_type": values.get("target_node_type"),
        "edge_type": values.get("edge_type"),
        "pressure_direction": direction,
        "pressure_score": round(pressure_score, 6),
        "positive_pressure": round(positive_pressure, 6),
        "negative_pressure": round(negative_pressure, 6),
        "reinforcing_pressure": round(reinforcing_pressure, 6),
        "decay_pressure": round(decay_pressure, 6),
        "emergence_pressure": round(emergence_pressure, 6),
        "drift_pressure": round(drift_pressure, 6),
        "persistence_pressure": round(persistence_pressure, 6),
        "volatility_pressure": round(volatility_pressure, 6),
        "saturation_score": round(saturation_score, 6),
        "imbalance_score": round(imbalance_score, 6),
        "pressure_regime": regime,
        "pressure_status": status,
        "contributing_edges": contributing_edges,
        "contributing_transitions": contributing_transitions,
        "contributing_drift_events": contributing_drift_events,
        "pressure_metadata": {
            "phase": "3D",
            "pipeline_name": PIPELINE_NAME,
            "scope_values": values,
            "sample_edges": [
                {
                    "edge_key": r.get("edge_key"),
                    "source_node_key": r.get("source_node_key"),
                    "target_node_key": r.get("target_node_key"),
                    "temporal_regime": r.get("temporal_regime"),
                    "stability_score": r.get("stability_score"),
                    "reinforcement_score": r.get("reinforcement_score"),
                    "decay_score": r.get("decay_score"),
                }
                for r in stability_rows[:10]
            ],
            "sample_transitions": [
                {
                    "edge_key": r.get("edge_key"),
                    "transition_type": r.get("transition_type"),
                    "transition_direction": r.get("transition_direction"),
                    "transition_strength": r.get("transition_strength"),
                }
                for r in transition_rows[:10]
            ],
            "sample_drift": [
                {
                    "drift_scope": r.get("drift_scope"),
                    "drift_dimension": r.get("drift_dimension"),
                    "drift_direction": r.get("drift_direction"),
                    "drift_magnitude": r.get("drift_magnitude"),
                    "drift_regime": r.get("drift_regime"),
                }
                for r in drift_rows[:10]
            ],
        },
        "updated_at": utc_now_iso(),
    }

    return row


def group_filter(rows: List[Dict[str, Any]], field: str, value: Any) -> List[Dict[str, Any]]:
    return [r for r in rows if str(r.get(field) or "") == str(value or "")]


def generate_pressure_rows(
    stability_rows: List[Dict[str, Any]],
    transition_rows: List[Dict[str, Any]],
    drift_rows: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rows = []

    rows.append(build_group_rows(
        scope="anchor_theme",
        stability_rows=stability_rows,
        transition_rows=transition_rows,
        drift_rows=drift_rows,
        values={"anchor_theme_name": ANCHOR_THEME_NAME, "theme_name": THEME_NAME or None},
    ))

    group_specs = [
        ("theme", "theme_name"),
        ("target_node_type", "target_node_type"),
        ("edge_type", "edge_type"),
        ("source_node", "source_node_key"),
        ("target_node", "target_node_key"),
    ]

    for scope, field in group_specs:
        values = sorted(set(str(r.get(field) or "") for r in stability_rows if r.get(field)))
        for value in values:
            s_rows = group_filter(stability_rows, field, value)
            t_rows = group_filter(transition_rows, field, value) if transition_rows and field in transition_rows[0] else []
            d_rows = group_filter(drift_rows, field, value) if drift_rows and field in drift_rows[0] else []

            values_dict = {
                "anchor_theme_name": ANCHOR_THEME_NAME,
                "theme_name": value if field == "theme_name" else None,
                "source_node_key": value if field == "source_node_key" else None,
                "target_node_key": value if field == "target_node_key" else None,
                "target_node_type": value if field == "target_node_type" else None,
                "edge_type": value if field == "edge_type" else None,
            }

            rows.append(build_group_rows(
                scope=scope,
                stability_rows=s_rows,
                transition_rows=t_rows,
                drift_rows=d_rows,
                values=values_dict,
            ))

    return rows


def validate(rows: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    errors, warnings = [], []

    if not rows:
        warnings.append("No pressure rows generated.")

    valid_directions = {"positive", "negative", "mixed", "neutral"}
    valid_regimes = {"low_pressure", "moderate_pressure", "high_pressure", "extreme_pressure"}
    valid_statuses = {"normal", "building", "persistent", "stressed", "saturated", "imbalanced", "releasing"}

    metrics = [
        "pressure_score",
        "positive_pressure",
        "negative_pressure",
        "reinforcing_pressure",
        "decay_pressure",
        "emergence_pressure",
        "drift_pressure",
        "persistence_pressure",
        "volatility_pressure",
        "saturation_score",
        "imbalance_score",
    ]

    for row in rows:
        for field in ["run_date_sgt", "pressure_key", "pressure_scope", "pressure_direction", "pressure_regime", "pressure_status"]:
            if not row.get(field):
                errors.append(f"Missing {field}: {row}")

        if row.get("pressure_direction") not in valid_directions:
            errors.append(f"Invalid pressure_direction: {row.get('pressure_direction')}")

        if row.get("pressure_regime") not in valid_regimes:
            errors.append(f"Invalid pressure_regime: {row.get('pressure_regime')}")

        if row.get("pressure_status") not in valid_statuses:
            errors.append(f"Invalid pressure_status: {row.get('pressure_status')}")

        for metric in metrics:
            value = safe_float(row.get(metric), None)
            if value is None or value < 0 or value > 1:
                errors.append(f"{metric} out of range for {row.get('pressure_key')}: {value}")

    if errors:
        return "failed", errors, warnings
    if warnings:
        return "warning", errors, warnings
    return "passed", errors, warnings


def top_rows(rows: List[Dict[str, Any]], metric: str, n: int = 10) -> List[Dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda r: safe_float(r.get(metric), 0.0) or 0.0, reverse=True)
    return [
        {
            "pressure_key": r.get("pressure_key"),
            "pressure_scope": r.get("pressure_scope"),
            "theme_name": r.get("theme_name"),
            "source_node_key": r.get("source_node_key"),
            "target_node_key": r.get("target_node_key"),
            "target_node_type": r.get("target_node_type"),
            "edge_type": r.get("edge_type"),
            "pressure_score": r.get("pressure_score"),
            "pressure_regime": r.get("pressure_regime"),
            "pressure_status": r.get("pressure_status"),
            metric: r.get(metric),
        }
        for r in sorted_rows[:n]
    ]


def average(rows: List[Dict[str, Any]], metric: str) -> Optional[float]:
    values = [safe_float(r.get(metric), None) for r in rows]
    values = [v for v in values if v is not None]
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def create_snapshot(
    client: SupabaseRestClient,
    rows: List[Dict[str, Any]],
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
) -> str:
    snapshot_id = snapshot_id_for()

    def count_regime(regime: str) -> int:
        return sum(1 for r in rows if r.get("pressure_regime") == regime)

    def count_status(status: str) -> int:
        return sum(1 for r in rows if r.get("pressure_status") == status)

    client.insert("structural_theme_graph_pressure_snapshots", [{
        "snapshot_id": snapshot_id,
        "run_date_sgt": run_date_sgt(),
        "snapshot_version": SNAPSHOT_VERSION,
        "anchor_theme_name": ANCHOR_THEME_NAME,
        "theme_name": THEME_NAME or None,
        "pressure_rows_generated": len(rows),
        "low_pressure_count": count_regime("low_pressure"),
        "moderate_pressure_count": count_regime("moderate_pressure"),
        "high_pressure_count": count_regime("high_pressure"),
        "extreme_pressure_count": count_regime("extreme_pressure"),
        "building_count": count_status("building"),
        "persistent_count": count_status("persistent"),
        "stressed_count": count_status("stressed"),
        "saturated_count": count_status("saturated"),
        "imbalanced_count": count_status("imbalanced"),
        "releasing_count": count_status("releasing"),
        "avg_pressure_score": average(rows, "pressure_score"),
        "avg_saturation_score": average(rows, "saturation_score"),
        "avg_imbalance_score": average(rows, "imbalance_score"),
        "highest_pressure_nodes": top_rows(rows, "pressure_score", 10),
        "highest_pressure_scopes": top_rows(rows, "saturation_score", 10),
        "largest_imbalances": top_rows(rows, "imbalance_score", 10),
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "snapshot_metadata": {
            "phase": "3D",
            "pipeline_name": PIPELINE_NAME,
            "thresholds": {
                "moderate": PRESSURE_MODERATE_THRESHOLD,
                "high": PRESSURE_HIGH_THRESHOLD,
                "extreme": PRESSURE_EXTREME_THRESHOLD,
            },
        },
    }], return_rows=False)

    return snapshot_id


def write_telemetry(
    client: SupabaseRestClient,
    *,
    status: str,
    snapshot_id: Optional[str],
    stability_rows_read: int,
    transition_rows_read: int,
    drift_rows_read: int,
    pressure_rows_upserted: int,
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
    runtime_seconds: float,
    error_message: Optional[str],
    metadata: Dict[str, Any],
) -> None:
    client.insert("structural_theme_graph_pressure_telemetry", [{
        "pipeline_name": PIPELINE_NAME,
        "snapshot_id": snapshot_id,
        "status": status,
        "stability_rows_read": stability_rows_read,
        "transition_rows_read": transition_rows_read,
        "drift_rows_read": drift_rows_read,
        "pressure_rows_upserted": pressure_rows_upserted,
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
    stability_rows = []
    transition_rows = []
    drift_rows = []
    pressure_rows = []

    try:
        stability_rows = fetch_rows(client, "structural_theme_graph_edge_stability")
        transition_rows = fetch_rows(client, "structural_theme_graph_regime_transitions")
        drift_rows = fetch_rows(client, "structural_theme_graph_structural_drift")

        pressure_rows = generate_pressure_rows(stability_rows, transition_rows, drift_rows)

        validation_status, validation_errors, validation_warnings = validate(pressure_rows)

        if validation_status == "failed":
            raise RuntimeError("Phase 3D validation failed: " + " | ".join(validation_errors[:10]))

        if pressure_rows:
            client.upsert(
                "structural_theme_graph_pressure_accumulation",
                pressure_rows,
                on_conflict="run_date_sgt,pressure_key",
                return_rows=False,
            )

        snapshot_id = create_snapshot(
            client,
            pressure_rows,
            validation_status,
            validation_errors,
            validation_warnings,
        )

        pressure_regime_counts = defaultdict(int)
        pressure_status_counts = defaultdict(int)

        for row in pressure_rows:
            pressure_regime_counts[row.get("pressure_regime")] += 1
            pressure_status_counts[row.get("pressure_status")] += 1

        metadata = {
            "phase": "3D",
            "anchor_theme_name": ANCHOR_THEME_NAME,
            "theme_name": THEME_NAME or None,
            "pressure_regime_counts": dict(pressure_regime_counts),
            "pressure_status_counts": dict(pressure_status_counts),
        }

        status = "success" if validation_status == "passed" else "warning"

        write_telemetry(
            client,
            status=status,
            snapshot_id=snapshot_id,
            stability_rows_read=len(stability_rows),
            transition_rows_read=len(transition_rows),
            drift_rows_read=len(drift_rows),
            pressure_rows_upserted=len(pressure_rows),
            validation_status=validation_status,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            runtime_seconds=time.time() - start,
            error_message=None,
            metadata=metadata,
        )

        print("Phase 3D Structural Pressure Accumulation completed.")
        print(f"Stability rows read: {len(stability_rows)}")
        print(f"Transition rows read: {len(transition_rows)}")
        print(f"Drift rows read: {len(drift_rows)}")
        print(f"Pressure rows upserted: {len(pressure_rows)}")
        print(f"Snapshot: {snapshot_id}")
        print(f"Validation: {validation_status}")
        print(f"Pressure regime counts: {dict(pressure_regime_counts)}")
        print(f"Pressure status counts: {dict(pressure_status_counts)}")

    except Exception as exc:
        write_telemetry(
            client,
            status="failed",
            snapshot_id=snapshot_id,
            stability_rows_read=len(stability_rows),
            transition_rows_read=len(transition_rows),
            drift_rows_read=len(drift_rows),
            pressure_rows_upserted=0,
            validation_status="failed",
            validation_errors=[str(exc)],
            validation_warnings=[],
            runtime_seconds=time.time() - start,
            error_message=str(exc),
            metadata={
                "phase": "3D",
                "anchor_theme_name": ANCHOR_THEME_NAME,
                "theme_name": THEME_NAME or None,
            },
        )
        raise


if __name__ == "__main__":
    main()
