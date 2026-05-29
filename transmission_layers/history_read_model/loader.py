from __future__ import annotations

import json
from collections import OrderedDict
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from typing import Any, Iterable, Mapping

PHASE_ID = "DB-1_sefi_history_read_model"
DEFAULT_ARTIFACT_PATHS = (
    "artifacts/hist_long4_real_multi_window_ecology_review.json",
    "artifacts/hist_long5b_temporal_delta_sensitivity_classification.json",
    "artifacts/hist_long6_cross_sectional_ecology_differentiation.json",
    "artifacts/hist_long7_intra_group_structural_contrast.json",
)
TABLE_ORDER = (
    "sefi_artifact_registry",
    "sefi_run_registry",
    "sefi_phase_runs",
    "sefi_hist_observations",
    "sefi_window_metrics",
    "sefi_sector_morphology",
    "sefi_symbol_metrics",
    "sefi_observation_facts",
)
MAX_PAYLOAD_BYTES = 8192

FORBIDDEN_TRUE_FLAGS = (
    "fmp_calls_enabled",
    "provider_api_calls_enabled",
    "prediction_enabled",
    "trading_execution_enabled",
    "replay_activation_enabled",
    "replay_execution_enabled",
    "topology_persistence_enabled",
    "topology_activation_enabled",
    "raw_cache_write_enabled",
)


class ArtifactLoadError(RuntimeError):
    """Raised when SEFI history artifacts cannot be deterministically normalized."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _json_bytes(payload: Mapping[str, Any]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")


def _bounded_payload(payload: Mapping[str, Any]) -> OrderedDict[str, Any]:
    ordered = OrderedDict((str(k), v) for k, v in sorted(payload.items()))
    if len(_json_bytes(ordered)) > MAX_PAYLOAD_BYTES:
        raise ArtifactLoadError("payload_jsonb exceeds DB-1 bounded metadata limit")
    return ordered


def _sha256_file(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _read_artifact(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ArtifactLoadError(f"missing source artifact: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ArtifactLoadError(f"invalid JSON source artifact: {path}") from exc
    if not isinstance(payload, dict):
        raise ArtifactLoadError(f"source artifact must be a JSON object: {path}")
    for required in ("status", "schema_version", "governance_certification"):
        if required not in payload:
            raise ArtifactLoadError(f"source artifact missing required key {required}: {path}")
    if str(payload.get("status")).lower() not in {"ok", "success"}:
        raise ArtifactLoadError(f"source artifact status is not completed/ok: {path}")
    governance = payload.get("governance_certification") or {}
    if not isinstance(governance, Mapping):
        raise ArtifactLoadError(f"governance_certification must be an object: {path}")
    enabled = [flag for flag in FORBIDDEN_TRUE_FLAGS if governance.get(flag) is True]
    if enabled:
        raise ArtifactLoadError(f"source artifact violates DB-1 governance boundary: {enabled}")
    return payload


def _phase_name(artifact: Mapping[str, Any], path: Path) -> str:
    governance = artifact.get("governance_certification") or {}
    return str(governance.get("phase") or path.stem)


def deterministic_duplicate_key(table_name: str, *parts: Any) -> str:
    normalized = "|".join(str(part) for part in (table_name, *parts))
    return sha256(normalized.encode("utf-8")).hexdigest()


def _artifact_id(source_path: Path, source_sha: str) -> str:
    return deterministic_duplicate_key("sefi_artifact_registry", source_path.as_posix(), source_sha)[:32]


def _base(artifact_id: str, run_id: str, loaded_at: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase_id", PHASE_ID),
        ("artifact_id", artifact_id),
        ("run_id", run_id),
        ("loaded_at", loaded_at),
    ])


def _artifact_registry_row(artifact: Mapping[str, Any], source_path: Path, source_sha: str, artifact_id: str, loaded_at: str) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("artifact_id", artifact_id),
        ("source_artifact_path", source_path.as_posix()),
        ("source_artifact_sha256", source_sha),
        ("artifact_kind", _phase_name(artifact, source_path)),
        ("schema_version", artifact.get("schema_version")),
        ("created_at", loaded_at),
        ("loaded_at", loaded_at),
        ("payload_jsonb", _bounded_payload({"status": artifact.get("status"), "review_date": artifact.get("review_date")})),
        ("duplicate_prevention_key", deterministic_duplicate_key("sefi_artifact_registry", source_path.as_posix(), source_sha)),
    ])


def _run_registry_row(artifact: Mapping[str, Any], source_path: Path, artifact_id: str, run_id: str, loaded_at: str) -> OrderedDict[str, Any]:
    phase_name = _phase_name(artifact, source_path)
    return OrderedDict([
        ("run_id", run_id),
        ("phase_id", PHASE_ID),
        ("phase_name", phase_name),
        ("artifact_id", artifact_id),
        ("status", str(artifact.get("status"))),
        ("created_at", loaded_at),
        ("loaded_at", loaded_at),
        ("completed_at", artifact.get("review_date")),
        ("payload_jsonb", _bounded_payload({"schema_version": artifact.get("schema_version")})),
        ("duplicate_prevention_key", deterministic_duplicate_key("sefi_run_registry", PHASE_ID, phase_name, artifact_id, run_id)),
    ])


def _phase_run_row(artifact: Mapping[str, Any], source_path: Path, artifact_id: str, run_id: str, loaded_at: str) -> OrderedDict[str, Any]:
    governance = artifact.get("governance_certification") or {}
    phase_name = _phase_name(artifact, source_path)
    payload = _bounded_payload({
        "schema_version": artifact.get("schema_version"),
        "review_date": artifact.get("review_date"),
        "governance_mode": governance.get("governance_mode"),
        "local_artifacts_only": governance.get("local_artifacts_only"),
        "observational_only": governance.get("observational_report_only") or governance.get("analysis_only"),
    })
    row = _base(artifact_id, run_id, loaded_at)
    row.update(OrderedDict([
        ("phase_name", phase_name),
        ("status", str(artifact.get("status"))),
        ("created_at", loaded_at),
        ("completed_at", artifact.get("review_date")),
        ("payload_jsonb", payload),
        ("duplicate_prevention_key", deterministic_duplicate_key("sefi_phase_runs", PHASE_ID, phase_name, artifact_id)),
    ]))
    return row


def _observation_rows(artifact: Mapping[str, Any], source_path: Path, artifact_id: str, run_id: str, loaded_at: str) -> list[OrderedDict[str, Any]]:
    phase_name = _phase_name(artifact, source_path)
    observations = []
    for key in ("longitudinal_comparison", "baseline_summary", "foxa_assessment", "fragility_assessment", "cross_group_findings", "boundary_certification"):
        value = artifact.get(key)
        if isinstance(value, Mapping):
            scalar = {k: v for k, v in value.items() if not isinstance(v, (dict, list))}
            observations.append((key, scalar))
    if not observations:
        observations.append(("artifact_status", {"status": artifact.get("status")}))
    rows = []
    for observation_type, payload in observations:
        row = _base(artifact_id, run_id, loaded_at)
        row.update(OrderedDict([
            ("observation_type", observation_type),
            ("phase_name", phase_name),
            ("observed_at", artifact.get("review_date")),
            ("created_at", loaded_at),
            ("payload_jsonb", _bounded_payload(payload)),
            ("duplicate_prevention_key", deterministic_duplicate_key("sefi_hist_observations", PHASE_ID, phase_name, artifact_id, observation_type)),
        ]))
        rows.append(row)
    return rows


def _window_metric_rows(artifact: Mapping[str, Any], source_path: Path, artifact_id: str, run_id: str, loaded_at: str) -> list[OrderedDict[str, Any]]:
    rows = []
    phase_name = _phase_name(artifact, source_path)
    for item in artifact.get("window_level_results", []) or []:
        if not isinstance(item, Mapping):
            continue
        window_days = item.get("window_trading_days", item.get("window_days", item.get("window")))
        if window_days is None:
            continue
        payload = _bounded_payload({
            "source_mode": item.get("source_mode"),
            "completed_telemetry_mode": item.get("completed_telemetry_mode"),
            "endpoint_failures": item.get("endpoint_failures"),
        })
        row = _base(artifact_id, run_id, loaded_at)
        row.update(OrderedDict([
            ("phase_name", phase_name),
            ("window_days", int(window_days)),
            ("completeness", item.get("completeness")),
            ("replay_density", item.get("replay_density")),
            ("replay_saturation", item.get("replay_saturation")),
            ("contradiction_burden", item.get("contradiction_burden")),
            ("sector_hhi", (item.get("sector_hhi") or {}).get("hhi")),
            ("subsector_hhi", (item.get("subsector_hhi") or {}).get("hhi")),
            ("effective_symbol_count", item.get("effective_symbol_count")),
            ("created_at", loaded_at),
            ("payload_jsonb", payload),
            ("duplicate_prevention_key", deterministic_duplicate_key("sefi_window_metrics", PHASE_ID, phase_name, artifact_id, int(window_days))),
        ]))
        rows.append(row)
    metric_values = artifact.get("metric_values_by_window") or {}
    if isinstance(metric_values, Mapping):
        for window, metrics in sorted(metric_values.items()):
            if not isinstance(metrics, Mapping):
                continue
            row = _base(artifact_id, run_id, loaded_at)
            row.update(OrderedDict([
                ("phase_name", phase_name),
                ("window_days", int(window)),
                ("completeness", metrics.get("completeness")),
                ("replay_density", metrics.get("replay_density")),
                ("replay_saturation", metrics.get("replay_saturation")),
                ("contradiction_burden", metrics.get("contradiction_burden")),
                ("sector_hhi", metrics.get("sector_hhi")),
                ("subsector_hhi", metrics.get("subsector_hhi")),
                ("effective_symbol_count", metrics.get("effective_symbol_count")),
                ("created_at", loaded_at),
                ("payload_jsonb", _bounded_payload({"source": "metric_values_by_window"})),
                ("duplicate_prevention_key", deterministic_duplicate_key("sefi_window_metrics", PHASE_ID, phase_name, artifact_id, int(window))),
            ]))
            rows.append(row)
    return rows


def _sector_rows(artifact: Mapping[str, Any], source_path: Path, artifact_id: str, run_id: str, loaded_at: str) -> list[OrderedDict[str, Any]]:
    rows = []
    phase_name = _phase_name(artifact, source_path)
    findings = artifact.get("findings") or {}
    for morphology_type, items in findings.items() if isinstance(findings, Mapping) else []:
        if not isinstance(items, list):
            continue
        for idx, item in enumerate(items[:25]):
            if not isinstance(item, Mapping):
                continue
            group_name = item.get("sector") or item.get("subsector") or item.get("group") or item.get("chunk")
            if not group_name:
                continue
            row = _base(artifact_id, run_id, loaded_at)
            row.update(OrderedDict([
                ("phase_name", phase_name),
                ("morphology_type", str(morphology_type)),
                ("sector", item.get("sector")),
                ("subsector", item.get("subsector")),
                ("symbol_count", item.get("symbol_count")),
                ("symbol_share", item.get("symbol_share")),
                ("rank", idx + 1),
                ("created_at", loaded_at),
                ("payload_jsonb", _bounded_payload({k: v for k, v in item.items() if k not in {"sector", "subsector", "symbol_count", "symbol_share"}})),
                ("duplicate_prevention_key", deterministic_duplicate_key("sefi_sector_morphology", PHASE_ID, phase_name, artifact_id, morphology_type, group_name, idx + 1)),
            ]))
            rows.append(row)
    for idx, item in enumerate(artifact.get("group_morphology_decomposition", []) or []):
        if not isinstance(item, Mapping):
            continue
        group_name = item.get("group") or item.get("sector")
        if not group_name:
            continue
        row = _base(artifact_id, run_id, loaded_at)
        row.update(OrderedDict([
            ("phase_name", phase_name),
            ("morphology_type", "group_morphology_decomposition"),
            ("sector", group_name),
            ("subsector", None),
            ("symbol_count", item.get("symbol_count")),
            ("symbol_share", item.get("symbol_share")),
            ("rank", idx + 1),
            ("created_at", loaded_at),
            ("payload_jsonb", _bounded_payload({"classification": item.get("classification"), "fragility_indicators": item.get("fragility_indicators")})),
            ("duplicate_prevention_key", deterministic_duplicate_key("sefi_sector_morphology", PHASE_ID, phase_name, artifact_id, "group_morphology_decomposition", group_name, idx + 1)),
        ]))
        rows.append(row)
    return rows


def _symbol_rows(artifact: Mapping[str, Any], source_path: Path, artifact_id: str, run_id: str, loaded_at: str) -> list[OrderedDict[str, Any]]:
    rows = []
    phase_name = _phase_name(artifact, source_path)
    for window in artifact.get("window_level_results", []) or []:
        if not isinstance(window, Mapping):
            continue
        window_days = window.get("window_trading_days", window.get("window_days", window.get("window")))
        for source_key in ("weak_symbols", "weak_symbol_details"):
            for idx, item in enumerate(window.get(source_key, []) or []):
                symbol = item.get("symbol") if isinstance(item, Mapping) else item
                if not symbol:
                    continue
                payload = item if isinstance(item, Mapping) else {"source_key": source_key}
                row = _base(artifact_id, run_id, loaded_at)
                row.update(OrderedDict([
                    ("phase_name", phase_name),
                    ("symbol", str(symbol).upper()),
                    ("window_days", int(window_days) if window_days is not None else None),
                    ("metric_type", source_key),
                    ("metric_value", None),
                    ("created_at", loaded_at),
                    ("payload_jsonb", _bounded_payload(payload)),
                    ("duplicate_prevention_key", deterministic_duplicate_key("sefi_symbol_metrics", PHASE_ID, phase_name, artifact_id, symbol, window_days, source_key, idx)),
                ]))
                rows.append(row)
    return rows


def _fact_row(*, phase_name: str, artifact_id: str, run_id: str, loaded_at: str, window_days: int | None, entity_type: str, entity_id: str, metric_name: str, metric_value: Any, payload: Mapping[str, Any] | None = None) -> OrderedDict[str, Any] | None:
    if metric_value is None:
        return None
    row = _base(artifact_id, run_id, loaded_at)
    row.update(OrderedDict([
        ("phase_name", phase_name),
        ("window_days", window_days),
        ("entity_type", entity_type),
        ("entity_id", entity_id),
        ("metric_name", metric_name),
        ("metric_value", metric_value),
        ("created_at", loaded_at),
        ("payload_jsonb", _bounded_payload(payload or {})),
        ("duplicate_prevention_key", deterministic_duplicate_key("sefi_observation_facts", PHASE_ID, phase_name, artifact_id, run_id, window_days, entity_type, entity_id, metric_name)),
    ]))
    return row


def _observation_fact_rows(*, window_rows: list[Mapping[str, Any]], sector_rows: list[Mapping[str, Any]], symbol_rows: list[Mapping[str, Any]], artifact_id: str, run_id: str, loaded_at: str, phase_name: str) -> list[OrderedDict[str, Any]]:
    facts: list[OrderedDict[str, Any]] = []
    for row in window_rows:
        for metric in ("completeness", "replay_density", "replay_saturation", "contradiction_burden", "sector_hhi", "subsector_hhi", "effective_symbol_count"):
            fact = _fact_row(
                phase_name=phase_name,
                artifact_id=artifact_id,
                run_id=run_id,
                loaded_at=loaded_at,
                window_days=row.get("window_days"),
                entity_type="window",
                entity_id=str(row.get("window_days")),
                metric_name=metric,
                metric_value=row.get(metric),
            )
            if fact:
                facts.append(fact)
    for row in sector_rows:
        entity_id = row.get("sector") or row.get("subsector")
        if not entity_id:
            continue
        for metric in ("symbol_count", "symbol_share"):
            fact = _fact_row(
                phase_name=phase_name,
                artifact_id=artifact_id,
                run_id=run_id,
                loaded_at=loaded_at,
                window_days=None,
                entity_type="sector" if row.get("sector") else "subsector",
                entity_id=str(entity_id),
                metric_name=f"{row.get('morphology_type')}.{metric}",
                metric_value=row.get(metric),
                payload={"rank": row.get("rank")},
            )
            if fact:
                facts.append(fact)
    for row in symbol_rows:
        fact = _fact_row(
            phase_name=phase_name,
            artifact_id=artifact_id,
            run_id=run_id,
            loaded_at=loaded_at,
            window_days=row.get("window_days"),
            entity_type="symbol",
            entity_id=str(row.get("symbol")),
            metric_name=str(row.get("metric_type")),
            metric_value=row.get("metric_value"),
        )
        if fact:
            facts.append(fact)
    return facts


def build_rows_from_artifact(path: str | Path, *, run_id: str | None = None, loaded_at: str | None = None) -> OrderedDict[str, list[OrderedDict[str, Any]]]:
    source_path = Path(path)
    artifact = _read_artifact(source_path)
    source_sha = _sha256_file(source_path)
    artifact_id = _artifact_id(source_path, source_sha)
    phase_name = _phase_name(artifact, source_path)
    stable_run_id = deterministic_duplicate_key("run", PHASE_ID, run_id or "default", artifact_id)[:24]
    stable_loaded_at = loaded_at or _utc_now()
    window_rows = _window_metric_rows(artifact, source_path, artifact_id, stable_run_id, stable_loaded_at)
    sector_rows = _sector_rows(artifact, source_path, artifact_id, stable_run_id, stable_loaded_at)
    symbol_rows = _symbol_rows(artifact, source_path, artifact_id, stable_run_id, stable_loaded_at)
    return OrderedDict([
        ("sefi_artifact_registry", [_artifact_registry_row(artifact, source_path, source_sha, artifact_id, stable_loaded_at)]),
        ("sefi_run_registry", [_run_registry_row(artifact, source_path, artifact_id, stable_run_id, stable_loaded_at)]),
        ("sefi_phase_runs", [_phase_run_row(artifact, source_path, artifact_id, stable_run_id, stable_loaded_at)]),
        ("sefi_hist_observations", _observation_rows(artifact, source_path, artifact_id, stable_run_id, stable_loaded_at)),
        ("sefi_window_metrics", window_rows),
        ("sefi_sector_morphology", sector_rows),
        ("sefi_symbol_metrics", symbol_rows),
        ("sefi_observation_facts", _observation_fact_rows(window_rows=window_rows, sector_rows=sector_rows, symbol_rows=symbol_rows, artifact_id=artifact_id, run_id=stable_run_id, loaded_at=stable_loaded_at, phase_name=phase_name)),
    ])


def build_read_model_rows(paths: Iterable[str | Path] = DEFAULT_ARTIFACT_PATHS, *, run_id: str | None = None, loaded_at: str | None = None) -> OrderedDict[str, list[OrderedDict[str, Any]]]:
    loaded = loaded_at or _utc_now()
    merged: OrderedDict[str, list[OrderedDict[str, Any]]] = OrderedDict((table, []) for table in TABLE_ORDER)
    for path in paths:
        rows = build_rows_from_artifact(path, run_id=run_id, loaded_at=loaded)
        for table, table_rows in rows.items():
            merged[table].extend(table_rows)
    return merged


def load_rows_to_supabase(client: Any, rows_by_table: Mapping[str, list[Mapping[str, Any]]]) -> OrderedDict[str, int]:
    """Append rows through an injected Supabase client; no client is created here."""
    counts: OrderedDict[str, int] = OrderedDict()
    for table in TABLE_ORDER:
        rows = rows_by_table.get(table, [])
        if not rows:
            counts[table] = 0
            continue
        client.table(table).insert(list(rows)).execute()
        counts[table] = len(rows)
    return counts
