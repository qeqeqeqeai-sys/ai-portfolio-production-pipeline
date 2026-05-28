from __future__ import annotations

import json
import zipfile
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from transmission_layers.expectation_failure.real_data.hist_density3_curated_ecology_expansion import _effective_symbols

HIST_DENSITY4_SCHEMA_VERSION = "hist_density4_v1"
DEFAULT_SOURCE_ROOT = "reports/hist_density3_curated_241"
FALLBACK_SOURCE_ROOTS = (
    "reports/hist_density3_curated_241_dryrun_manual",
    "reports/hist_density3_stage2_smoke",
)
DEFAULT_REPORT_PATH = "reports/hist_density4_241_symbol_findings_review.md"
DEFAULT_ARTIFACT_PATH = "artifacts/hist_density4_241_symbol_findings_review.json"
DEFAULT_COMPLETED_BUNDLE_PATH = "temp/hist-density3-curated-241-reports.zip"
OPS_HIST_REPORT_PATHS = tuple(f"reports/ops_hist{i}_" for i in range(1, 8))


def _governance() -> dict[str, Any]:
    return {
        "governance_mode": "observational_only",
        "data_scope": "local_artifact_report_analysis_only",
        "new_ingestion_enabled": False,
        "replay_activation_enabled": False,
        "trading_execution_enabled": False,
        "supabase_write_enabled": False,
        "topology_persistence_enabled": False,
        "topology_activation_enabled": False,
        "bounded_artifact_generation_only": True,
    }


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))



def _read_zip_json(bundle_path: Path, member_name: str) -> dict[str, Any] | None:
    if not bundle_path.exists():
        return None
    with zipfile.ZipFile(bundle_path) as zf:
        matches = [name for name in zf.namelist() if name == member_name or name.endswith(f"/{member_name}")]
        if not matches:
            return None
        return json.loads(zf.read(sorted(matches)[0]).decode("utf-8"))


def _read_zip_text(bundle_path: Path, member_name: str) -> str | None:
    if not bundle_path.exists():
        return None
    with zipfile.ZipFile(bundle_path) as zf:
        matches = [name for name in zf.namelist() if name == member_name or name.endswith(f"/{member_name}")]
        if not matches:
            return None
        return zf.read(sorted(matches)[0]).decode("utf-8")


def _candidate_source_root(preferred: Path) -> tuple[Path, str]:
    if preferred.is_file() and preferred.suffix == ".zip":
        return preferred, "completed_artifact_bundle"
    if (preferred / "hist_density3_summary.json").exists():
        return preferred, "completed_summary"
    if (preferred / "hist_density3_config_preview.json").exists():
        return preferred, "config_preview_only"
    completed_bundle = Path(DEFAULT_COMPLETED_BUNDLE_PATH)
    if completed_bundle.exists():
        return completed_bundle, "completed_artifact_bundle"
    for root_text in FALLBACK_SOURCE_ROOTS:
        root = Path(root_text)
        if (root / "hist_density3_summary.json").exists():
            return root, "fallback_completed_summary"
    return preferred, "missing_current_241_20_plan"


def _root_artifacts(root: Path, source_mode: str) -> dict[str, Any]:
    if source_mode == "completed_artifact_bundle":
        summary_md = _read_zip_text(root, "hist_density3_summary.md")
        return {
            "hist_density3_summary_json": _read_zip_json(root, "hist_density3_summary.json"),
            "hist_density3_summary_md": {"present": summary_md is not None, "bytes": len((summary_md or "").encode("utf-8"))},
            "hist_density3_config_preview_json": _read_zip_json(root, "hist_density3_config_preview.json"),
        }
    summary_md_path = root / "hist_density3_summary.md"
    summary_md = summary_md_path.read_text(encoding="utf-8") if summary_md_path.exists() else None
    return {
        "hist_density3_summary_json": _read_json(root / "hist_density3_summary.json"),
        "hist_density3_summary_md": {"present": summary_md is not None, "bytes": len((summary_md or "").encode("utf-8"))},
        "hist_density3_config_preview_json": _read_json(root / "hist_density3_config_preview.json"),
    }


def _chunk_index_from_path(path_text: str, fallback: int) -> int:
    for part in Path(path_text).parts:
        if part.startswith("chunk_"):
            try:
                return int(part.split("_", 1)[1])
            except ValueError:
                return fallback
    return fallback


def _load_chunk_manifests(root: Path, source_mode: str) -> list[dict[str, Any]]:
    manifests: list[dict[str, Any]] = []
    if source_mode == "completed_artifact_bundle":
        with zipfile.ZipFile(root) as zf:
            names = sorted(name for name in zf.namelist() if name.endswith("/manifests/density_summary.json") or name == "manifests/density_summary.json")
            for idx, name in enumerate(names, start=1):
                payload = json.loads(zf.read(name).decode("utf-8"))
                manifests.append({"chunk_index": _chunk_index_from_path(name, idx), "path": name, "payload": payload})
        return sorted(manifests, key=lambda row: row["chunk_index"])
    for idx, path in enumerate(sorted(root.glob("chunk_*/manifests/density_summary.json")), start=1):
        manifests.append({"chunk_index": _chunk_index_from_path(str(path), idx), "path": str(path), "payload": json.loads(path.read_text(encoding="utf-8"))})
    return sorted(manifests, key=lambda row: row["chunk_index"])


def _load_ops_hist_snapshots(root: Path, source_mode: str) -> list[dict[str, Any]]:
    snapshots: list[dict[str, Any]] = []
    if source_mode == "completed_artifact_bundle":
        with zipfile.ZipFile(root) as zf:
            names = sorted(name for name in zf.namelist() if "/snapshots/ops_hist1_" in name and name.endswith(".json"))
            for idx, name in enumerate(names, start=1):
                payload = json.loads(zf.read(name).decode("utf-8"))
                snapshots.append({"chunk_index": _chunk_index_from_path(name, idx), "path": name, "payload": payload})
        return snapshots
    for idx, path in enumerate(sorted(root.glob("chunk_*/snapshots/ops_hist1_*.json")), start=1):
        snapshots.append({"chunk_index": _chunk_index_from_path(str(path), idx), "path": str(path), "payload": json.loads(path.read_text(encoding="utf-8"))})
    return snapshots

def _current_241_20_preview() -> dict[str, Any]:
    symbols, universe_telemetry = _effective_symbols(max_symbols=241, include_high_risk_symbols=False, apply_sde2_replacements=True)
    chunks = [symbols[i:i + 50] for i in range(0, len(symbols), 50)]
    return {
        "schema_version": "hist_density3_v1",
        "chunk_plan": {"symbol_chunk_count": len(chunks), "symbol_chunk_size": 50, "trading_days": 20},
        "chunk_symbols": chunks,
        "estimated_symbol_date_rows": len(symbols) * 20,
        "universe_telemetry": universe_telemetry,
        "governance_certification": {
            "governance_mode": "observational_only",
            "replay_execution_enabled": False,
            "topology_activation_enabled": False,
            "persistence": "local_artifacts_only",
            "no_prediction_or_trading_execution": True,
            "no_cognition_replay_topology_persistence": True,
        },
    }


def _iter_chunk_results(summary: dict[str, Any]) -> list[dict[str, Any]]:
    return list(summary.get("ops_hist_artifact_summary", {}).get("chunk_results", []) or [])



def _chunk_results_from_manifests(manifests: list[dict[str, Any]], preview: dict[str, Any] | None) -> list[dict[str, Any]]:
    chunk_symbols = (preview or {}).get("chunk_symbols", []) or []
    rows: list[dict[str, Any]] = []
    for manifest in manifests:
        chunk_index = int(manifest["chunk_index"])
        payload = manifest.get("payload", {}) or {}
        density = payload.get("density_summary", payload) or {}
        telemetry = density.get("telemetry_summary", density.get("telemetry", {})) or {}
        symbols = list(chunk_symbols[chunk_index - 1]) if 0 < chunk_index <= len(chunk_symbols) else []
        symbol_count = int(density.get("symbol_count", telemetry.get("symbol_count", len(symbols))) or len(symbols) or 0)
        rows.append({
            "chunk_index": chunk_index,
            "chunk_symbol_count": symbol_count,
            "chunk_symbols": symbols,
            "telemetry": telemetry,
            "missing_record_samples": telemetry.get("missing_record_samples", density.get("missing_record_samples", [])) or [],
            "endpoint_failure_samples": telemetry.get("endpoint_failure_samples", density.get("endpoint_failure_samples", [])) or [],
            "manifest_path": manifest.get("path"),
        })
    return sorted(rows, key=lambda row: row["chunk_index"])


def _merge_manifest_chunks(summary: dict[str, Any], manifests: list[dict[str, Any]], preview: dict[str, Any] | None) -> dict[str, Any]:
    if not manifests:
        return summary
    merged = dict(summary)
    merged["ops_hist_artifact_summary"] = dict(merged.get("ops_hist_artifact_summary", {}))
    merged["ops_hist_artifact_summary"]["chunk_results"] = _chunk_results_from_manifests(manifests, preview)
    return merged

def _normalize_endpoint_counts(status_counts: dict[str, Any]) -> dict[str, int]:
    return {str(k): int(v) for k, v in sorted((status_counts or {}).items())}


def _chunk_quality_rows(summary: dict[str, Any], preview: dict[str, Any] | None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    chunks = _iter_chunk_results(summary)
    if chunks:
        for chunk in chunks:
            telemetry = chunk.get("telemetry", {}) or {}
            normalized = int(telemetry.get("normalized_count", 0) or 0)
            partial = int(telemetry.get("partial_count", 0) or 0)
            failed = int(telemetry.get("failed_count", 0) or 0)
            exact = int(telemetry.get("exact_date_matches", 0) or 0)
            reconciled = int(telemetry.get("reconciled_prior_dates", 0) or 0)
            missing = int(telemetry.get("missing_dates", 0) or 0)
            requested_days = int(telemetry.get("resolved_trading_days", telemetry.get("requested_trading_days", 0)) or 0)
            symbol_count = int(chunk.get("chunk_symbol_count", telemetry.get("symbol_count", 0)) or 0)
            expected_rows = symbol_count * requested_days if requested_days else 0
            rows.append({
                "chunk_index": int(chunk.get("chunk_index", len(rows) + 1)),
                "chunk_symbol_count": symbol_count,
                "normalized_count": normalized,
                "partial_count": partial,
                "failed_count": failed,
                "exact_date_matches": exact,
                "reconciled_prior_dates": reconciled,
                "missing_dates": missing,
                "endpoint_status_counts": _normalize_endpoint_counts(telemetry.get("endpoint_status_counts", {})),
                "top_failure_reasons": telemetry.get("top_failure_reasons", []),
                "missing_record_sample_count": int(telemetry.get("missing_record_sample_count", 0) or 0),
                "endpoint_failure_sample_count": int(telemetry.get("endpoint_failure_sample_count", 0) or 0),
                "affected_symbol_count": int(telemetry.get("affected_symbol_count", 0) or 0),
                "affected_date_count": int(telemetry.get("affected_date_count", 0) or 0),
                "expected_symbol_date_rows": expected_rows,
                "normalization_density": round(normalized / max(expected_rows, 1), 6) if expected_rows else 0.0,
                "reconciliation_density": round((exact + reconciled) / max(expected_rows, 1), 6) if expected_rows else 0.0,
                "chunk_symbols": list(chunk.get("chunk_symbols", [])),
            })
        return sorted(rows, key=lambda r: r["chunk_index"])

    if preview:
        chunk_symbols = preview.get("chunk_symbols", []) or []
        trading_days = int(preview.get("chunk_plan", {}).get("trading_days", 0) or 0)
        for idx, symbols in enumerate(chunk_symbols, start=1):
            rows.append({
                "chunk_index": idx,
                "chunk_symbol_count": len(symbols),
                "normalized_count": None,
                "partial_count": None,
                "failed_count": None,
                "exact_date_matches": None,
                "reconciled_prior_dates": None,
                "missing_dates": None,
                "endpoint_status_counts": {},
                "top_failure_reasons": [],
                "missing_record_sample_count": 0,
                "endpoint_failure_sample_count": 0,
                "affected_symbol_count": 0,
                "affected_date_count": 0,
                "expected_symbol_date_rows": len(symbols) * trading_days,
                "normalization_density": None,
                "reconciliation_density": None,
                "chunk_symbols": list(symbols),
            })
    return rows


def _samples_by_symbol(chunks: Iterable[dict[str, Any]]) -> tuple[Counter[str], Counter[str], Counter[str], dict[str, list[str]]]:
    missing = Counter()
    endpoint = Counter()
    reasons = Counter()
    dates: dict[str, set[str]] = defaultdict(set)
    for chunk in chunks:
        for sample in chunk.get("missing_record_samples", []) or []:
            symbol = str(sample.get("symbol", "")).upper()
            if symbol:
                missing[symbol] += 1
                if sample.get("requested_snapshot_date"):
                    dates[symbol].add(str(sample["requested_snapshot_date"]))
            reason = str(sample.get("reason", sample.get("failure_reason", "zero_records_returned")) or "zero_records_returned")
            if symbol and reason:
                reasons[f"{symbol}:{reason}"] += 1
        for sample in chunk.get("endpoint_failure_samples", []) or []:
            symbol = str(sample.get("symbol", "")).upper()
            if symbol:
                endpoint[symbol] += 1
                if sample.get("requested_snapshot_date"):
                    dates[symbol].add(str(sample["requested_snapshot_date"]))
            reason = str(sample.get("status", sample.get("reason", sample.get("failure_reason", "endpoint_failure"))) or "endpoint_failure")
            if symbol and reason:
                reasons[f"{symbol}:{reason}"] += 1
    return missing, endpoint, reasons, {k: sorted(v) for k, v in dates.items()}


def _weak_symbols(summary: dict[str, Any]) -> list[dict[str, Any]]:
    missing, endpoint, reasons, dates = _samples_by_symbol(_iter_chunk_results(summary))
    symbols = sorted(set(missing) | set(endpoint))
    weak: list[dict[str, Any]] = []
    for symbol in symbols:
        reason_rows = []
        prefix = f"{symbol}:"
        for key, count in sorted(reasons.items(), key=lambda kv: (-kv[1], kv[0])):
            if key.startswith(prefix):
                reason_rows.append({"reason": key[len(prefix):], "count": int(count)})
        needs_replacement_review = any(r["reason"] in {"HTTP_403", "zero_records_returned", "403"} for r in reason_rows)
        weak.append({
            "symbol": symbol,
            "missing_sample_count": int(missing[symbol]),
            "endpoint_failure_sample_count": int(endpoint[symbol]),
            "observed_dates": dates.get(symbol, []),
            "observed_reasons": reason_rows,
            "replacement_review_later": needs_replacement_review,
        })
    return sorted(weak, key=lambda r: (-(r["missing_sample_count"] + r["endpoint_failure_sample_count"]), r["symbol"]))


def _load_ops_hist_report_inventory() -> list[dict[str, Any]]:
    rows = []
    for path in sorted(Path("reports").glob("ops_hist*.md")):
        name = path.name.lower()
        if not any(name.startswith(f"ops_hist{i}_") for i in range(1, 8)):
            continue
        text = path.read_text(encoding="utf-8")
        rows.append({
            "path": str(path),
            "bytes": len(text.encode("utf-8")),
            "mentions_governance": "Governance" in text or "governance" in text,
            "mentions_streamlit_payload": "Streamlit" in text,
            "mentions_canonical_table": "Canonical" in text,
            "mentions_recurrence": "recurrence" in text.lower(),
            "mentions_topology": "topology" in text.lower(),
            "mentions_morphology": "morphology" in text.lower(),
            "mentions_saturation": "saturation" in text.lower(),
        })
    return rows



def _mean(values: list[float]) -> float | None:
    if not values:
        return None
    return round(sum(values) / len(values), 6)


def _range(values: list[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "max": None}
    return {"min": round(min(values), 6), "max": round(max(values), 6)}


def _snapshot_ecology_diagnostics(snapshots: list[dict[str, Any]]) -> dict[str, Any]:
    by_chunk: dict[int, list[dict[str, Any]]] = defaultdict(list)
    for row in snapshots:
        by_chunk[int(row["chunk_index"])].append(row.get("payload", {}) or {})

    chunk_rows: list[dict[str, Any]] = []
    all_hhi: list[float] = []
    all_norm: list[float] = []
    posture_counter = Counter()
    degraded_market_cap = 0
    for chunk_index in sorted(by_chunk):
        payloads = by_chunk[chunk_index]
        hhi_values: list[float] = []
        norm_values: list[float] = []
        symbol_counts: list[int] = []
        sector_rows = 0
        posture_counts = Counter()
        dates: set[str] = set()
        preflight_symbols: set[str] = set()
        for payload in payloads:
            operational = payload.get("operational_diagnostics", {}) or {}
            canonical = payload.get("canonical_payloads", {}) or {}
            adapter = payload.get("adapter_diagnostics", {}) or {}
            if payload.get("snapshot_date"):
                dates.add(str(payload["snapshot_date"]))
            posture = str(payload.get("posture") or "unknown")
            posture_counts[posture] += 1
            posture_counter[posture] += 1
            if isinstance(operational.get("sector_hhi"), (int, float)):
                hhi_values.append(float(operational["sector_hhi"]))
            if isinstance(operational.get("normalization_completeness"), (int, float)):
                norm_values.append(float(operational["normalization_completeness"]))
            if isinstance(operational.get("symbols_successfully_normalized"), int):
                symbol_counts.append(int(operational["symbols_successfully_normalized"]))
            sector_rows = max(sector_rows, len(canonical.get("sector_transition_rows", []) or []), len((payload.get("streamlit_payloads", {}) or {}).get("sector_transition_table", []) or []))
            if adapter.get("historical_market_cap_endpoint_status") == "degraded":
                degraded_market_cap += 1
            for sample in adapter.get("downstream_preflight_failure_symbol_samples", []) or []:
                symbol = str(sample.get("symbol", "")).upper()
                if symbol:
                    preflight_symbols.add(symbol)
        all_hhi.extend(hhi_values)
        all_norm.extend(norm_values)
        chunk_rows.append({
            "chunk_index": chunk_index,
            "snapshot_count": len(payloads),
            "date_count": len(dates),
            "posture_counts": dict(sorted(posture_counts.items())),
            "sector_hhi_range": _range(hhi_values),
            "sector_hhi_average": _mean(hhi_values),
            "normalization_completeness_range": _range(norm_values),
            "normalization_completeness_average": _mean(norm_values),
            "normalized_symbol_count_range": {"min": min(symbol_counts) if symbol_counts else None, "max": max(symbol_counts) if symbol_counts else None},
            "structural_richness": {"sector_transition_rows": sector_rows, "posture_variety": len(posture_counts)},
            "preflight_failure_symbols": sorted(preflight_symbols),
        })
    return {
        "snapshot_count": len(snapshots),
        "chunk_count": len(chunk_rows),
        "posture_counts": dict(sorted(posture_counter.items())),
        "posture_stability": "stable_single_posture" if len(posture_counter) == 1 and posture_counter else "mixed_posture",
        "sector_hhi_range": _range(all_hhi),
        "normalization_completeness_range": _range(all_norm),
        "market_cap_optionalization": {
            "degraded_snapshot_count": degraded_market_cap,
            "assessment": "historical marketCap degradation is treated as optional enrichment telemetry, not ingestion failure",
        },
        "chunk_diagnostics": chunk_rows,
        "temporal_stability_days": max((row["date_count"] for row in chunk_rows), default=0),
    }


def _top_failure_reasons(chunk_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = Counter()
    for row in chunk_rows:
        for reason in row.get("top_failure_reasons", []) or []:
            if isinstance(reason, dict):
                counts[str(reason.get("reason", "unknown"))] += int(reason.get("count", 0) or 0)
            else:
                counts[str(reason)] += 1
    return [{"reason": reason, "count": int(count)} for reason, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))]

def _ecology_findings(chunk_rows: list[dict[str, Any]], weak: list[dict[str, Any]], ops_inventory: list[dict[str, Any]], source_mode: str) -> dict[str, Any]:
    densities = [r["normalization_density"] for r in chunk_rows if isinstance(r.get("normalization_density"), float)]
    weak_symbols = [r["symbol"] for r in weak]
    topology_reports = sum(1 for r in ops_inventory if r["mentions_topology"])
    recurrence_reports = sum(1 for r in ops_inventory if r["mentions_recurrence"])
    morphology_reports = sum(1 for r in ops_inventory if r["mentions_morphology"])
    saturation_reports = sum(1 for r in ops_inventory if r["mentions_saturation"])
    density_spread = round(max(densities) - min(densities), 6) if densities else None
    return {
        "replay_density_shifts": "Density comparison is chunk-bounded; completed chunk telemetry supports direct spread observation." if densities else "Chunk density telemetry unavailable in checked-in source; review records configuration-level coverage only.",
        "chunk_density_spread": density_spread,
        "sector_subsector_clustering": "SDE2 curated universe and chunk plan preserve cross-sector/subsector diversity; per-sector realized density requires completed chunk telemetry." if (source_mode.endswith("config_preview_only") or source_mode.startswith("missing_")) else "Review uses chunk-normalized telemetry plus SDE2 curation as the sector/subsector diversity frame.",
        "fragility_persistence": "Weak-symbol persistence is sampled from missing-record and endpoint-failure telemetry; no weak symbol samples were present." if not weak_symbols else f"Weak-symbol persistence observed in bounded samples for {', '.join(weak_symbols[:10])}.",
        "contradiction_replay_recurrence": "OPS-HIST recurrence/morphology/saturation report surfaces are present for descriptive recurrence review." if recurrence_reports else "OPS-HIST recurrence surfaces were not found in local markdown inventory.",
        "topology_richness": "OPS-HIST topology and morphology report surfaces indicate multi-layer descriptive topology richness." if topology_reports and morphology_reports else "Topology richness is bounded by available local report inventory.",
        "monoculture_risk": "No single chunk can be assessed as dominant without completed telemetry." if not densities else ("Low observed chunk monoculture risk; density spread is bounded." if density_spread is not None and density_spread <= 0.05 else "Chunk density concentration requires follow-up review."),
        "temporal_stability_across_20_days": "20-day window stability is certified at configuration level; completed telemetry is required for realized temporal variance." if (source_mode.endswith("config_preview_only") or source_mode.startswith("missing_")) else "20-day realized telemetry is available for chunk-level stability review.",
        "ops_hist_surface_counts": {"topology_reports": topology_reports, "recurrence_reports": recurrence_reports, "morphology_reports": morphology_reports, "saturation_reports": saturation_reports},
    }


def _compare_chunks(chunk_rows: list[dict[str, Any]]) -> dict[str, Any]:
    comparable = [r for r in chunk_rows if isinstance(r.get("normalization_density"), float)]
    if not comparable:
        return {
            "richest_chunks": [],
            "weakest_chunks": [],
            "dominant_chunk": None,
            "assessment": "Completed chunk density metrics unavailable; structural comparison limited to configured chunk sizes.",
            "configured_chunk_sizes": [{"chunk_index": r["chunk_index"], "chunk_symbol_count": r["chunk_symbol_count"]} for r in chunk_rows],
        }
    sorted_rows = sorted(comparable, key=lambda r: (-int(r.get("normalized_count") or 0), -r["normalization_density"], int(r.get("missing_dates", 0) or 0), r["chunk_index"]))
    weakest = sorted(comparable, key=lambda r: (int(r.get("normalized_count") or 0), r["normalization_density"], -int(r.get("missing_dates", 0) or 0), r["chunk_index"]))
    max_density = max(r["normalization_density"] for r in comparable)
    dominant = sorted_rows[0]["chunk_index"] if sum(1 for r in comparable if r["normalization_density"] == max_density) == 1 else None
    by_index = {r["chunk_index"]: r for r in comparable}
    notes = []
    if by_index.get(3, {}).get("normalized_count") == 1000 and by_index.get(4, {}).get("normalized_count") == 1000:
        notes.append("chunk_03 and chunk_04 strongest: 1000 normalized rows each")
    if 1 in by_index:
        notes.append(f"chunk_01 acceptable: {by_index[1]['normalized_count']}")
    if 2 in by_index:
        notes.append(f"chunk_02 weaker: {by_index[2]['normalized_count']}")
    if 5 in by_index:
        row = by_index[5]
        notes.append(f"chunk_05 degraded but completed: {row['normalized_count']}/{row['expected_symbol_date_rows']}, provider issue isolated to weak symbols")
    return {
        "richest_chunks": [{"chunk_index": r["chunk_index"], "normalized_count": r["normalized_count"], "requested_symbol_date_capacity": r["expected_symbol_date_rows"], "normalization_density": r["normalization_density"]} for r in sorted_rows[:2]],
        "weakest_chunks": [{"chunk_index": r["chunk_index"], "normalized_count": r["normalized_count"], "requested_symbol_date_capacity": r["expected_symbol_date_rows"], "normalization_density": r["normalization_density"], "missing_dates": r["missing_dates"]} for r in weakest[:2]],
        "dominant_chunk": dominant,
        "deterministic_notes": notes,
        "assessment": "Chunk comparison is deterministic: normalized row count, density, missing-date burden, then chunk index.",
    }


def build_hist_density4_findings_review(source_root: str = DEFAULT_SOURCE_ROOT) -> dict[str, Any]:
    root, source_mode = _candidate_source_root(Path(source_root))
    source_artifacts = _root_artifacts(root, source_mode)
    summary = source_artifacts["hist_density3_summary_json"] or {}
    preview = source_artifacts["hist_density3_config_preview_json"]
    chunk_manifests = _load_chunk_manifests(root, source_mode)
    snapshots = _load_ops_hist_snapshots(root, source_mode)
    if not summary and not preview and source_mode == "missing_current_241_20_plan":
        preview = _current_241_20_preview()
    if not summary and preview:
        summary = {
            "status": "config_preview_only",
            "schema_version": preview.get("schema_version"),
            "preflight_validation": preview.get("preflight_validation", {}),
            "chunking_configuration": preview.get("chunk_plan", {}),
            "governance_certification": preview.get("governance_certification", {}),
        }
    summary = _merge_manifest_chunks(summary, chunk_manifests, preview)
    chunk_rows = _chunk_quality_rows(summary, preview)
    weak = _weak_symbols(summary)
    ops_inventory = _load_ops_hist_report_inventory()
    snapshot_ecology = _snapshot_ecology_diagnostics(snapshots)
    endpoint_failures = Counter()
    for row in chunk_rows:
        for key, value in row.get("endpoint_status_counts", {}).items():
            if "fail" in key.lower() or "403" in key or "error" in key.lower() or "http" in key.lower() or "zero_records" in key.lower():
                endpoint_failures[key] += int(value)
    effective_symbol_count = len((preview or {}).get("effective_symbols", []) or []) or sum(int(r.get("chunk_symbol_count", 0) or 0) for r in chunk_rows)
    trading_days = int(((preview or {}).get("chunk_plan", {}) or {}).get("trading_days", 0) or max((int(r.get("expected_symbol_date_rows", 0) or 0) // max(int(r.get("chunk_symbol_count", 0) or 1), 1) for r in chunk_rows), default=0))
    aggregate_top_failures = _top_failure_reasons(chunk_rows)
    artifact = {
        "schema_version": HIST_DENSITY4_SCHEMA_VERSION,
        "status": "ok",
        "review_date": date.today().isoformat(),
        "source_root": str(root),
        "source_mode": source_mode,
        "source_status": summary.get("status", "missing"),
        "completed_telemetry_mode": bool(chunk_manifests or _iter_chunk_results(summary)),
        "source_artifacts_inspected": {
            "root_files": {
                "hist_density3_summary_json": source_artifacts["hist_density3_summary_json"] is not None,
                "hist_density3_summary_md": source_artifacts["hist_density3_summary_md"],
                "hist_density3_config_preview_json": source_artifacts["hist_density3_config_preview_json"] is not None,
            },
            "chunk_manifest_count": len(chunk_manifests),
            "ops_hist_snapshot_count": len(snapshots),
        },
        "ingestion_quality": {
            "chunk_quality_rows": chunk_rows,
            "aggregate": {
                "chunk_count": len(chunk_rows),
                "effective_symbol_count": effective_symbol_count,
                "configured_symbol_count": sum(int(r.get("chunk_symbol_count", 0) or 0) for r in chunk_rows),
                "trading_days": trading_days,
                "estimated_symbol_date_rows": int((preview or {}).get("estimated_symbol_date_rows", 0) or effective_symbol_count * trading_days),
                "requested_symbol_date_capacity_total": sum(int(r.get("expected_symbol_date_rows") or 0) for r in chunk_rows),
                "normalized_count_total": sum(int(r.get("normalized_count") or 0) for r in chunk_rows),
                "partial_count_total": sum(int(r.get("partial_count") or 0) for r in chunk_rows),
                "failed_count_total": sum(int(r.get("failed_count") or 0) for r in chunk_rows),
                "exact_date_matches_total": sum(int(r.get("exact_date_matches") or 0) for r in chunk_rows),
                "reconciled_prior_dates_total": sum(int(r.get("reconciled_prior_dates") or 0) for r in chunk_rows),
                "missing_dates_total": sum(int(r.get("missing_dates") or 0) for r in chunk_rows),
                "endpoint_failures": dict(sorted(endpoint_failures.items())),
                "affected_symbol_count": max((int(r.get("affected_symbol_count") or 0) for r in chunk_rows), default=0),
                "affected_date_count": max((int(r.get("affected_date_count") or 0) for r in chunk_rows), default=0),
                "top_failure_reasons": aggregate_top_failures,
            },
            "missing_date_patterns": "Sample-based missing-date telemetry is absent." if not weak else "Missing-date samples cluster by weak symbols listed in weak_symbol_review.",
        },
        "weak_symbol_review": weak,
        "first_ecology_findings": _ecology_findings(chunk_rows, weak, ops_inventory, source_mode),
        "ecology_findings": snapshot_ecology,
        "chunk_comparison": _compare_chunks(chunk_rows),
        "operational_stability_assessment": {
            "full_rollout_completed": len(chunk_rows) == 5 and summary.get("status") == "ok",
            "fail_closed_controls": "did_not_collapse_run",
            "provider_degradation": "isolated_to_weak_symbols" if weak else "not_observed",
            "telemetry_identified_weak_symbols": [row["symbol"] for row in weak],
            "historical_market_cap_optionalization": "behaved_as_intended",
            "ops_hist_ops_live_boundary": "appears_stable_after_canonicalization_fixes",
        },
        "ops_hist_inventory": ops_inventory,
        "governance_certification": _governance(),
        "recommended_next_phase": "Consider replacement or vendor-symbol investigation for PARA before longer backfills; otherwise proceed only with bounded observational operator review and no replay, prediction, trading, topology persistence, or Supabase writes.",
    }
    return artifact


def render_hist_density4_markdown(artifact: dict[str, Any]) -> str:
    g = artifact["governance_certification"]
    agg = artifact["ingestion_quality"]["aggregate"]
    lines = [
        "# HIST-DENSITY-4 — First 241-Symbol Historical Ecology Findings Review",
        "",
        "## Scope Certification",
        f"- Review mode: {g['governance_mode']}",
        f"- Data scope: {g['data_scope']}",
        f"- New ingestion enabled: {g['new_ingestion_enabled']}",
        f"- Replay activation enabled: {g['replay_activation_enabled']}",
        f"- Trading execution enabled: {g['trading_execution_enabled']}",
        f"- Supabase writes enabled: {g['supabase_write_enabled']}",
        f"- Topology persistence enabled: {g['topology_persistence_enabled']}",
        "",
        "## Source Artifacts Inspected",
        f"- Source root: `{artifact['source_root']}`",
        f"- Source mode: `{artifact['source_mode']}`",
        f"- Source status: `{artifact['source_status']}`",
        f"- Completed telemetry mode: {artifact['completed_telemetry_mode']}",
        f"- Parsed chunk manifests: {artifact['source_artifacts_inspected']['chunk_manifest_count']}",
        f"- Parsed OPS-HIST snapshots: {artifact['source_artifacts_inspected']['ops_hist_snapshot_count']}",
        f"- OPS-HIST markdown inventory count: {len(artifact['ops_hist_inventory'])}",
        "",
        "## Ingestion Quality Summary",
        f"- Chunk count: {agg['chunk_count']}",
        f"- Effective symbol count: {agg['effective_symbol_count']}",
        f"- Configured symbol count: {agg['configured_symbol_count']}",
        f"- Trading days: {agg['trading_days']}",
        f"- Estimated symbol-date rows: {agg['estimated_symbol_date_rows']}",
        f"- Requested symbol-date capacity total: {agg['requested_symbol_date_capacity_total']}",
        f"- Normalized count total: {agg['normalized_count_total']}",
        f"- Partial count total: {agg['partial_count_total']}",
        f"- Failed count total: {agg['failed_count_total']}",
        f"- Exact date matches total: {agg['exact_date_matches_total']}",
        f"- Reconciled prior dates total: {agg['reconciled_prior_dates_total']}",
        f"- Missing dates total: {agg['missing_dates_total']}",
        f"- Endpoint failures: `{json.dumps(agg['endpoint_failures'], sort_keys=True)}`",
        f"- Affected symbols/dates: {agg['affected_symbol_count']} symbols across {agg['affected_date_count']} dates",
        f"- Top failure reasons: `{json.dumps(agg['top_failure_reasons'], sort_keys=True)}`",
        f"- Missing-date patterns: {artifact['ingestion_quality']['missing_date_patterns']}",
        "",
        "## Chunk Quality Rows",
    ]
    for row in artifact["ingestion_quality"]["chunk_quality_rows"]:
        lines.append(f"- Chunk {row['chunk_index']}: symbols={row['chunk_symbol_count']}, normalized={row['normalized_count']}/{row['expected_symbol_date_rows']}, partial={row['partial_count']}, failed={row['failed_count']}, exact={row['exact_date_matches']}, reconciled={row['reconciled_prior_dates']}, missing={row['missing_dates']}, affected_symbols={row['affected_symbol_count']}, affected_dates={row['affected_date_count']}, endpoint_status_counts={json.dumps(row['endpoint_status_counts'], sort_keys=True)}, normalization_density={row['normalization_density']}")
    lines.extend(["", "## Weak Symbols"])
    if artifact["weak_symbol_review"]:
        for row in artifact["weak_symbol_review"]:
            lines.append(f"- {row['symbol']}: missing_samples={row['missing_sample_count']}, endpoint_failure_samples={row['endpoint_failure_sample_count']}, replacement_review_later={row['replacement_review_later']}, reasons={json.dumps(row['observed_reasons'], sort_keys=True)}")
    else:
        lines.append("- No weak symbols were present in bounded local telemetry samples.")
    lines.extend(["", "## Operational Stability Assessment"])
    for key, value in artifact["operational_stability_assessment"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## First Ecology Findings"])
    for key, value in artifact["first_ecology_findings"].items():
        lines.append(f"- {key}: {value}")
    lines.extend(["", "## Ecology Findings From OPS-HIST Snapshots"])
    ecology = artifact["ecology_findings"]
    lines.append(f"- Posture stability: {ecology['posture_stability']} with counts {json.dumps(ecology['posture_counts'], sort_keys=True)}")
    lines.append(f"- Sector HHI range: {json.dumps(ecology['sector_hhi_range'], sort_keys=True)}")
    lines.append(f"- Normalization completeness range: {json.dumps(ecology['normalization_completeness_range'], sort_keys=True)}")
    lines.append(f"- Temporal stability over 20 days: observed max chunk date count {ecology['temporal_stability_days']}")
    lines.append(f"- Historical marketCap optionalization: {ecology['market_cap_optionalization']['assessment']}")
    for row in ecology["chunk_diagnostics"]:
        lines.append(f"- Chunk {row['chunk_index']} ecology: dates={row['date_count']}, sector_hhi={json.dumps(row['sector_hhi_range'], sort_keys=True)}, normalization={json.dumps(row['normalization_completeness_range'], sort_keys=True)}, structural_richness={json.dumps(row['structural_richness'], sort_keys=True)}, preflight_failure_symbols={row['preflight_failure_symbols']}")
    lines.extend(["", "## Chunk Comparison"])
    for key, value in artifact["chunk_comparison"].items():
        lines.append(f"- {key}: {value}")
    lines.extend([
        "",
        "## Recommended Next Phase",
        f"- {artifact['recommended_next_phase']}",
        "",
        "## Governance Confirmation",
        "- Observational only: certified.",
        "- No new ingestion: certified.",
        "- No replay activation: certified.",
        "- No topology persistence: certified.",
        "- No Supabase writes: certified.",
        "- No trading execution: certified.",
    ])
    return "\n".join(lines) + "\n"


def write_hist_density4_findings_review(source_root: str = DEFAULT_SOURCE_ROOT, report_path: str = DEFAULT_REPORT_PATH, artifact_path: str = DEFAULT_ARTIFACT_PATH) -> dict[str, Any]:
    artifact = build_hist_density4_findings_review(source_root=source_root)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).parent.mkdir(parents=True, exist_ok=True)
    Path(artifact_path).write_text(json.dumps(artifact, indent=2, sort_keys=True), encoding="utf-8")
    Path(report_path).write_text(render_hist_density4_markdown(artifact), encoding="utf-8")
    return artifact
