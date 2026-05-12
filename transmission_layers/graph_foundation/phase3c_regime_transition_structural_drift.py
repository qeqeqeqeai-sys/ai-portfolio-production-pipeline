import math
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from graph_supabase_client import SupabaseRestClient


PIPELINE_NAME = "PHASE_3C_REGIME_TRANSITION_STRUCTURAL_DRIFT"
SNAPSHOT_VERSION = "phase3c_v1"

ANCHOR_THEME_NAME = os.getenv("ANCHOR_THEME_NAME", "ai").strip().lower()
THEME_NAME = os.getenv("THEME_NAME", "").strip().lower()
MAX_STABILITY_ROWS = int(os.getenv("MAX_STABILITY_ROWS", "20000"))
DRIFT_THRESHOLD_MILD = float(os.getenv("DRIFT_THRESHOLD_MILD", "0.05"))
DRIFT_THRESHOLD_MODERATE = float(os.getenv("DRIFT_THRESHOLD_MODERATE", "0.12"))
DRIFT_THRESHOLD_MAJOR = float(os.getenv("DRIFT_THRESHOLD_MAJOR", "0.25"))


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


def abs_float(value: Any) -> float:
    return abs(safe_float(value, 0.0) or 0.0)


def fetch_stability_rows(client: SupabaseRestClient) -> List[Dict[str, Any]]:
    filters = {"anchor_theme_name": f"eq.{ANCHOR_THEME_NAME}"}
    if THEME_NAME:
        filters["theme_name"] = f"eq.{THEME_NAME}"

    return client.select(
        "structural_theme_graph_edge_stability",
        columns="*",
        filters=filters,
        order="run_date_sgt.desc",
        limit=MAX_STABILITY_ROWS,
    )


def group_by_edge(rows: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    grouped = defaultdict(list)
    for row in rows:
        edge_key = row.get("edge_key")
        if edge_key:
            grouped[edge_key].append(row)

    for edge_key in grouped:
        grouped[edge_key].sort(key=lambda r: str(r.get("run_date_sgt") or ""))

    return grouped


def transition_direction(prev: Optional[Dict[str, Any]], curr: Dict[str, Any]) -> Tuple[str, str]:
    if prev is None:
        return "new_relationship", "emerging"

    prev_regime = prev.get("temporal_regime")
    curr_regime = curr.get("temporal_regime")
    prev_status = prev.get("relationship_status")
    curr_status = curr.get("relationship_status")

    if prev_regime == curr_regime and prev_status == curr_status:
        return "no_regime_change", "unchanged"

    regime_pair = f"{prev_regime}_to_{curr_regime}"

    if curr_regime == "reinforcing" or curr_status == "reinforced":
        return regime_pair, "strengthening"
    if curr_regime == "decaying" or curr_status == "weakening":
        return regime_pair, "weakening"
    if curr_regime == "stable":
        return regime_pair, "stabilizing"
    if curr_regime == "volatile":
        return regime_pair, "destabilizing"
    if curr_regime == "emerging":
        return regime_pair, "emerging"
    if curr_regime == "dormant":
        return regime_pair, "dormant"

    return regime_pair, "mixed"


def build_transition_row(edge_key: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
    curr = history[-1]
    prev = history[-2] if len(history) >= 2 else None

    transition_type, direction = transition_direction(prev, curr)

    prev_stability = safe_float(prev.get("stability_score"), None) if prev else None
    curr_stability = safe_float(curr.get("stability_score"), 0.0) or 0.0

    prev_reinforcement = safe_float(prev.get("reinforcement_score"), None) if prev else None
    curr_reinforcement = safe_float(curr.get("reinforcement_score"), 0.0) or 0.0

    prev_decay = safe_float(prev.get("decay_score"), None) if prev else None
    curr_decay = safe_float(curr.get("decay_score"), 0.0) or 0.0

    prev_emergence = safe_float(prev.get("emergence_score"), None) if prev else None
    curr_emergence = safe_float(curr.get("emergence_score"), 0.0) or 0.0

    stability_delta = curr_stability - (prev_stability if prev_stability is not None else 0.0)
    reinforcement_delta = curr_reinforcement - (prev_reinforcement if prev_reinforcement is not None else 0.0)
    decay_delta = curr_decay - (prev_decay if prev_decay is not None else 0.0)
    emergence_delta = curr_emergence - (prev_emergence if prev_emergence is not None else 0.0)

    transition_strength = max(
        abs(stability_delta),
        abs(reinforcement_delta),
        abs(decay_delta),
        abs(emergence_delta),
    )

    return {
        "run_date_sgt": run_date_sgt(),
        "edge_key": edge_key,
        "source_node_key": curr.get("source_node_key"),
        "target_node_key": curr.get("target_node_key"),
        "edge_type": curr.get("edge_type"),
        "theme_name": curr.get("theme_name"),
        "anchor_theme_name": curr.get("anchor_theme_name") or ANCHOR_THEME_NAME,
        "previous_temporal_regime": prev.get("temporal_regime") if prev else None,
        "current_temporal_regime": curr.get("temporal_regime"),
        "previous_relationship_status": prev.get("relationship_status") if prev else None,
        "current_relationship_status": curr.get("relationship_status"),
        "transition_type": transition_type,
        "transition_direction": direction,
        "transition_strength": round(transition_strength, 6),
        "stability_delta": round(stability_delta, 6),
        "reinforcement_delta": round(reinforcement_delta, 6),
        "decay_delta": round(decay_delta, 6),
        "emergence_delta": round(emergence_delta, 6),
        "previous_stability_score": round(prev_stability, 6) if prev_stability is not None else None,
        "current_stability_score": round(curr_stability, 6),
        "previous_reinforcement_score": round(prev_reinforcement, 6) if prev_reinforcement is not None else None,
        "current_reinforcement_score": round(curr_reinforcement, 6),
        "previous_decay_score": round(prev_decay, 6) if prev_decay is not None else None,
        "current_decay_score": round(curr_decay, 6),
        "previous_emergence_score": round(prev_emergence, 6) if prev_emergence is not None else None,
        "current_emergence_score": round(curr_emergence, 6),
        "transition_metadata": {
            "phase": "3C",
            "pipeline_name": PIPELINE_NAME,
            "history_points": len(history),
            "previous_run_date_sgt": prev.get("run_date_sgt") if prev else None,
            "current_run_date_sgt": curr.get("run_date_sgt"),
            "previous_temporal_regime": prev.get("temporal_regime") if prev else None,
            "current_temporal_regime": curr.get("temporal_regime"),
        },
        "updated_at": utc_now_iso(),
    }


def average(rows: List[Dict[str, Any]], metric: str) -> Optional[float]:
    values = [safe_float(r.get(metric), None) for r in rows]
    values = [v for v in values if v is not None]
    if not values:
        return None
    return sum(values) / len(values)


def drift_regime(magnitude: float) -> str:
    if magnitude >= DRIFT_THRESHOLD_MAJOR:
        return "major_drift"
    if magnitude >= DRIFT_THRESHOLD_MODERATE:
        return "moderate_drift"
    if magnitude >= DRIFT_THRESHOLD_MILD:
        return "mild_drift"
    return "no_material_drift"


def drift_direction(delta: float) -> str:
    if delta > 0:
        return "increasing"
    if delta < 0:
        return "decreasing"
    return "flat"


def latest_previous_by_edge(grouped: Dict[str, List[Dict[str, Any]]]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    latest = []
    previous = []

    for _, history in grouped.items():
        if history:
            latest.append(history[-1])
        if len(history) >= 2:
            previous.append(history[-2])

    return latest, previous


def make_drift_row(
    *,
    drift_scope: str,
    dimension: str,
    current_rows: List[Dict[str, Any]],
    previous_rows: List[Dict[str, Any]],
    group_values: Dict[str, Any],
) -> Dict[str, Any]:
    current_value = average(current_rows, dimension)
    previous_value = average(previous_rows, dimension)

    if current_value is None:
        current_value = 0.0

    if previous_value is None:
        previous_value = 0.0

    delta = current_value - previous_value
    magnitude = abs(delta)

    return {
        "run_date_sgt": run_date_sgt(),
        "drift_scope": drift_scope,
        "anchor_theme_name": ANCHOR_THEME_NAME,
        "theme_name": group_values.get("theme_name"),
        "source_node_key": group_values.get("source_node_key"),
        "target_node_type": group_values.get("target_node_type"),
        "edge_type": group_values.get("edge_type"),
        "drift_dimension": dimension,
        "previous_value": round(previous_value, 6),
        "current_value": round(current_value, 6),
        "drift_delta": round(delta, 6),
        "drift_magnitude": round(magnitude, 6),
        "drift_direction": drift_direction(delta),
        "drift_regime": drift_regime(magnitude),
        "affected_edges": len(current_rows),
        "total_edges": len(current_rows),
        "drift_metadata": {
            "phase": "3C",
            "pipeline_name": PIPELINE_NAME,
            "group_values": group_values,
            "previous_rows": len(previous_rows),
            "current_rows": len(current_rows),
            "thresholds": {
                "mild": DRIFT_THRESHOLD_MILD,
                "moderate": DRIFT_THRESHOLD_MODERATE,
                "major": DRIFT_THRESHOLD_MAJOR,
            },
        },
        "updated_at": utc_now_iso(),
    }


def generate_drift_rows(grouped: Dict[str, List[Dict[str, Any]]]) -> List[Dict[str, Any]]:
    latest, previous = latest_previous_by_edge(grouped)

    dimensions = [
        "stability_score",
        "reinforcement_score",
        "decay_score",
        "emergence_score",
        "latest_edge_strength",
        "avg_evidence_intensity",
        "avg_confidence_score",
    ]

    drift_rows = []

    for dimension in dimensions:
        drift_rows.append(make_drift_row(
            drift_scope="anchor_theme",
            dimension=dimension,
            current_rows=latest,
            previous_rows=previous,
            group_values={},
        ))

    group_specs = [
        ("target_node_type", "target_node_type"),
        ("edge_type", "edge_type"),
        ("theme_name", "theme_name"),
    ]

    for drift_scope, field in group_specs:
        groups = sorted(set(str(r.get(field) or "") for r in latest if r.get(field)))
        for group in groups:
            current_rows = [r for r in latest if str(r.get(field) or "") == group]
            previous_rows = [r for r in previous if str(r.get(field) or "") == group]
            if not current_rows:
                continue

            group_values = {field: group}

            for dimension in dimensions:
                drift_rows.append(make_drift_row(
                    drift_scope=drift_scope,
                    dimension=dimension,
                    current_rows=current_rows,
                    previous_rows=previous_rows,
                    group_values=group_values,
                ))

    return drift_rows


def validate(transitions: List[Dict[str, Any]], drift_rows: List[Dict[str, Any]]) -> Tuple[str, List[str], List[str]]:
    errors, warnings = [], []

    if not transitions:
        warnings.append("No regime transitions generated.")

    if not drift_rows:
        warnings.append("No structural drift rows generated.")

    allowed_directions = {"strengthening", "weakening", "stabilizing", "destabilizing", "emerging", "dormant", "unchanged", "mixed"}
    allowed_drift_regimes = {"no_material_drift", "mild_drift", "moderate_drift", "major_drift"}

    for row in transitions:
        for field in ["run_date_sgt", "edge_key", "source_node_key", "target_node_key", "edge_type", "current_temporal_regime", "current_relationship_status", "transition_type", "transition_direction"]:
            if not row.get(field):
                errors.append(f"Missing transition field {field}: {row}")

        if row.get("transition_direction") not in allowed_directions:
            errors.append(f"Invalid transition direction: {row.get('transition_direction')}")

        value = safe_float(row.get("transition_strength"), None)
        if value is None or value < 0:
            errors.append(f"Invalid transition_strength for {row.get('edge_key')}: {value}")

    for row in drift_rows:
        for field in ["run_date_sgt", "drift_scope", "drift_dimension", "drift_direction", "drift_regime"]:
            if not row.get(field):
                errors.append(f"Missing drift field {field}: {row}")

        if row.get("drift_regime") not in allowed_drift_regimes:
            errors.append(f"Invalid drift_regime: {row.get('drift_regime')}")

        value = safe_float(row.get("drift_magnitude"), None)
        if value is None or value < 0:
            errors.append(f"Invalid drift_magnitude: {value}")

    if errors:
        return "failed", errors, warnings
    if warnings:
        return "warning", errors, warnings
    return "passed", errors, warnings


def top_rows(rows: List[Dict[str, Any]], metric: str, n: int = 10) -> List[Dict[str, Any]]:
    sorted_rows = sorted(rows, key=lambda r: safe_float(r.get(metric), 0.0) or 0.0, reverse=True)
    out = []
    for row in sorted_rows[:n]:
        out.append({
            k: row.get(k)
            for k in [
                "edge_key",
                "source_node_key",
                "target_node_key",
                "edge_type",
                "transition_type",
                "transition_direction",
                "transition_strength",
                "drift_scope",
                "drift_dimension",
                "drift_magnitude",
                "drift_regime",
                "target_node_type",
                "theme_name",
            ]
            if k in row
        })
    return out


def create_snapshot(
    client: SupabaseRestClient,
    transitions: List[Dict[str, Any]],
    drift_rows: List[Dict[str, Any]],
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
) -> str:
    snapshot_id = snapshot_id_for()

    def count_transition(direction: str) -> int:
        return sum(1 for r in transitions if r.get("transition_direction") == direction)

    def count_drift(regime: str) -> int:
        return sum(1 for r in drift_rows if r.get("drift_regime") == regime)

    avg_transition_strength = average(transitions, "transition_strength")
    avg_drift_magnitude = average(drift_rows, "drift_magnitude")

    client.insert("structural_theme_graph_drift_snapshots", [{
        "snapshot_id": snapshot_id,
        "run_date_sgt": run_date_sgt(),
        "snapshot_version": SNAPSHOT_VERSION,
        "anchor_theme_name": ANCHOR_THEME_NAME,
        "theme_name": THEME_NAME or None,
        "transitions_detected": len(transitions),
        "strengthening_transitions": count_transition("strengthening"),
        "weakening_transitions": count_transition("weakening"),
        "stabilizing_transitions": count_transition("stabilizing"),
        "destabilizing_transitions": count_transition("destabilizing"),
        "emerging_transitions": count_transition("emerging"),
        "dormant_transitions": count_transition("dormant"),
        "drift_rows_generated": len(drift_rows),
        "major_drift_count": count_drift("major_drift"),
        "moderate_drift_count": count_drift("moderate_drift"),
        "mild_drift_count": count_drift("mild_drift"),
        "avg_transition_strength": round(avg_transition_strength, 6) if avg_transition_strength is not None else None,
        "avg_drift_magnitude": round(avg_drift_magnitude, 6) if avg_drift_magnitude is not None else None,
        "strongest_transitions": top_rows(transitions, "transition_strength", 10),
        "largest_drift_dimensions": top_rows(drift_rows, "drift_magnitude", 10),
        "validation_status": validation_status,
        "validation_errors": validation_errors,
        "validation_warnings": validation_warnings,
        "snapshot_metadata": {
            "phase": "3C",
            "pipeline_name": PIPELINE_NAME,
            "thresholds": {
                "mild": DRIFT_THRESHOLD_MILD,
                "moderate": DRIFT_THRESHOLD_MODERATE,
                "major": DRIFT_THRESHOLD_MAJOR,
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
    transitions_upserted: int,
    drift_rows_upserted: int,
    validation_status: str,
    validation_errors: List[str],
    validation_warnings: List[str],
    runtime_seconds: float,
    error_message: Optional[str],
    metadata: Dict[str, Any],
) -> None:
    client.insert("structural_theme_graph_drift_telemetry", [{
        "pipeline_name": PIPELINE_NAME,
        "snapshot_id": snapshot_id,
        "status": status,
        "stability_rows_read": stability_rows_read,
        "transitions_upserted": transitions_upserted,
        "drift_rows_upserted": drift_rows_upserted,
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
    stability_rows_read = 0
    transitions: List[Dict[str, Any]] = []
    drift_rows: List[Dict[str, Any]] = []

    try:
        stability_rows = fetch_stability_rows(client)
        stability_rows_read = len(stability_rows)

        grouped = group_by_edge(stability_rows)
        transitions = [build_transition_row(edge_key, history) for edge_key, history in grouped.items()]
        drift_rows = generate_drift_rows(grouped)

        validation_status, validation_errors, validation_warnings = validate(transitions, drift_rows)

        if validation_status == "failed":
            raise RuntimeError("Phase 3C validation failed: " + " | ".join(validation_errors[:10]))

        if transitions:
            client.upsert(
                "structural_theme_graph_regime_transitions",
                transitions,
                on_conflict="run_date_sgt,edge_key",
                return_rows=False,
            )

        if drift_rows:
            client.upsert(
                "structural_theme_graph_structural_drift",
                drift_rows,
                on_conflict="run_date_sgt,drift_scope,anchor_theme_name,theme_name,source_node_key,target_node_type,edge_type,drift_dimension",
                return_rows=False,
            )

        snapshot_id = create_snapshot(client, transitions, drift_rows, validation_status, validation_errors, validation_warnings)

        transition_counts = defaultdict(int)
        for row in transitions:
            transition_counts[row.get("transition_direction")] += 1

        drift_counts = defaultdict(int)
        for row in drift_rows:
            drift_counts[row.get("drift_regime")] += 1

        metadata = {
            "phase": "3C",
            "anchor_theme_name": ANCHOR_THEME_NAME,
            "theme_name": THEME_NAME or None,
            "stability_rows_read": stability_rows_read,
            "unique_edges_analyzed": len(grouped),
            "transition_counts": dict(transition_counts),
            "drift_counts": dict(drift_counts),
        }

        status = "success" if validation_status == "passed" else "warning"

        write_telemetry(
            client,
            status=status,
            snapshot_id=snapshot_id,
            stability_rows_read=stability_rows_read,
            transitions_upserted=len(transitions),
            drift_rows_upserted=len(drift_rows),
            validation_status=validation_status,
            validation_errors=validation_errors,
            validation_warnings=validation_warnings,
            runtime_seconds=time.time() - start,
            error_message=None,
            metadata=metadata,
        )

        print("Phase 3C Regime Transition & Structural Drift completed.")
        print(f"Stability rows read: {stability_rows_read}")
        print(f"Transitions upserted: {len(transitions)}")
        print(f"Drift rows upserted: {len(drift_rows)}")
        print(f"Snapshot: {snapshot_id}")
        print(f"Validation: {validation_status}")
        print(f"Transition counts: {dict(transition_counts)}")
        print(f"Drift counts: {dict(drift_counts)}")

    except Exception as exc:
        write_telemetry(
            client,
            status="failed",
            snapshot_id=snapshot_id,
            stability_rows_read=stability_rows_read,
            transitions_upserted=0,
            drift_rows_upserted=0,
            validation_status="failed",
            validation_errors=[str(exc)],
            validation_warnings=[],
            runtime_seconds=time.time() - start,
            error_message=str(exc),
            metadata={
                "phase": "3C",
                "anchor_theme_name": ANCHOR_THEME_NAME,
                "theme_name": THEME_NAME or None,
            },
        )
        raise


if __name__ == "__main__":
    main()
