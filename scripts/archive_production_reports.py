#!/usr/bin/env python3
"""
archive_production_reports.py

Persistent archival script for GitHub Actions AI portfolio production pipeline.

Archives:
- outputs/
- logs/
- monitoring CSVs
- holdings CSVs
- signal score CSVs
- HTML reports
- PNG charts
- validation reports
- runtime telemetry snapshot

Uploads:
- ZIP bundle
- manifest.json
- telemetry_snapshot.json
- checksum.sha256

Writes metadata to:
- public.production_report_archives

Required env vars:
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- ARCHIVE_BUCKET

Optional env vars:
- PIPELINE_NAME
- PIPELINE_STATUS
- ENVIRONMENT
- GITHUB_RUN_ID
- GITHUB_WORKFLOW
- GITHUB_REPOSITORY
- GITHUB_REF_NAME
- GITHUB_SHA
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sys
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo


try:
    from api_retry_utils import retry_requests_call
except Exception:
    retry_requests_call = None


SGT = ZoneInfo("Asia/Singapore")


@dataclass
class ArchiveConfig:
    supabase_url: str
    supabase_key: str
    bucket: str
    pipeline_name: str
    environment: str
    status: str
    github_run_id: str
    github_workflow: str
    github_repository: str
    github_branch: str
    github_sha: str
    outputs_dir: Path
    logs_dir: Path
    staging_dir: Path


def now_sgt() -> datetime:
    return datetime.now(SGT)


def env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return str(value)


def load_config() -> ArchiveConfig:
    return ArchiveConfig(
        supabase_url=env("SUPABASE_URL", required=True).rstrip("/"),
        supabase_key=env("SUPABASE_SERVICE_ROLE_KEY", required=True),
        bucket=env("ARCHIVE_BUCKET", "ai-production-archives"),
        pipeline_name=env("PIPELINE_NAME", "AI_PORTFOLIO_PRODUCTION"),
        environment=env("ENVIRONMENT", "prod"),
        status=env("PIPELINE_STATUS", "UNKNOWN").upper(),
        github_run_id=env("GITHUB_RUN_ID", "local"),
        github_workflow=env("GITHUB_WORKFLOW", ""),
        github_repository=env("GITHUB_REPOSITORY", ""),
        github_branch=env("GITHUB_REF_NAME", ""),
        github_sha=env("GITHUB_SHA", ""),
        outputs_dir=Path(env("OUTPUTS_DIR", "outputs")),
        logs_dir=Path(env("LOGS_DIR", "logs")),
        staging_dir=Path(env("ARCHIVE_STAGING_DIR", "archive_staging")),
    )


def headers(config: ArchiveConfig, content_type: Optional[str] = None) -> Dict[str, str]:
    h = {
        "apikey": config.supabase_key,
        "Authorization": f"Bearer {config.supabase_key}",
    }
    if content_type:
        h["Content-Type"] = content_type
    return h


def request_with_retry(method: str, url: str, **kwargs) -> requests.Response:
    if retry_requests_call:
        return retry_requests_call(method=method, url=url, **kwargs)

    last_exc = None
    for attempt in range(1, 4):
        try:
            response = requests.request(method, url, timeout=60, **kwargs)
            if response.status_code < 500:
                return response
            last_exc = RuntimeError(f"HTTP {response.status_code}: {response.text}")
        except Exception as exc:
            last_exc = exc

    raise RuntimeError(f"Request failed after retries: {last_exc}")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def list_archive_files(config: ArchiveConfig) -> List[Path]:
    files: List[Path] = []

    for base in [config.outputs_dir, config.logs_dir]:
        if base.exists():
            for path in base.rglob("*"):
                if path.is_file():
                    files.append(path)

    return sorted(files)


def classify_counts(files: List[Path]) -> Dict[str, int]:
    counts = {
        "file_count": len(files),
        "csv_count": 0,
        "html_count": 0,
        "png_count": 0,
        "log_count": 0,
        "validation_file_count": 0,
    }

    for f in files:
        suffix = f.suffix.lower()
        name = f.name.lower()

        if suffix == ".csv":
            counts["csv_count"] += 1
        elif suffix in [".html", ".htm"]:
            counts["html_count"] += 1
        elif suffix == ".png":
            counts["png_count"] += 1
        elif suffix == ".log":
            counts["log_count"] += 1

        if "validation" in name:
            counts["validation_file_count"] += 1

    return counts


def build_object_prefix(config: ArchiveConfig, run_dt: datetime) -> str:
    run_date = run_dt.strftime("%Y/%m/%d")
    status_folder = "success" if config.status == "SUCCESS" else "failed"

    return (
        f"{config.environment}/"
        f"{config.pipeline_name}/"
        f"{run_date}/"
        f"{status_folder}/"
        f"run_{config.github_run_id}"
    )


def build_manifest(
    config: ArchiveConfig,
    files: List[Path],
    object_prefix: str,
    run_dt: datetime,
) -> Dict[str, Any]:
    file_records = []

    for f in files:
        try:
            if f.is_relative_to(Path.cwd()):
                rel = str(f.relative_to(Path.cwd()))
            else:
                rel = str(f)
        except Exception:
            rel = str(f)

        file_records.append(
            {
                "path": rel.replace("\\", "/"),
                "size_bytes": f.stat().st_size,
                "sha256": sha256_file(f),
                "modified_at_utc": datetime.utcfromtimestamp(f.stat().st_mtime).isoformat() + "Z",
            }
        )

    return {
        "archive_version": "v1",
        "created_at_sgt": run_dt.isoformat(),
        "run_date_sgt": run_dt.date().isoformat(),
        "pipeline_name": config.pipeline_name,
        "environment": config.environment,
        "status": config.status,
        "github": {
            "run_id": config.github_run_id,
            "workflow": config.github_workflow,
            "repository": config.github_repository,
            "branch": config.github_branch,
            "sha": config.github_sha,
        },
        "storage": {
            "provider": "SUPABASE_STORAGE",
            "bucket": config.bucket,
            "object_prefix": object_prefix,
        },
        "files": file_records,
        "counts": classify_counts(files),
    }


def create_zip_bundle(config: ArchiveConfig, files: List[Path], manifest: Dict[str, Any]) -> Path:
    config.staging_dir.mkdir(parents=True, exist_ok=True)

    archive_name = f"{config.pipeline_name}_{config.github_run_id}_{config.status}_archive.zip"
    archive_path = config.staging_dir / archive_name

    manifest_path = config.staging_dir / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for f in files:
            if f.exists() and f.is_file():
                arcname = str(f).replace("\\", "/")
                zf.write(f, arcname=arcname)

        zf.write(manifest_path, arcname="metadata/manifest.json")

    return archive_path


def build_telemetry_snapshot(config: ArchiveConfig, run_dt: datetime) -> Dict[str, Any]:
    return {
        "snapshot_created_at_sgt": run_dt.isoformat(),
        "run_date_sgt": run_dt.date().isoformat(),
        "pipeline_name": config.pipeline_name,
        "environment": config.environment,
        "status": config.status,
        "github_run_id": config.github_run_id,
        "github_workflow": config.github_workflow,
        "github_repository": config.github_repository,
        "github_branch": config.github_branch,
        "github_sha": config.github_sha,
    }


def upload_file(config: ArchiveConfig, local_path: Path, object_path: str) -> None:
    content_type = mimetypes.guess_type(str(local_path))[0] or "application/octet-stream"

    url = f"{config.supabase_url}/storage/v1/object/{config.bucket}/{object_path}"

    with local_path.open("rb") as f:
        response = request_with_retry(
            "POST",
            url,
            headers={
                **headers(config, content_type),
                "x-upsert": "true",
            },
            data=f,
        )

    if response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Supabase Storage upload failed for {object_path}: "
            f"HTTP {response.status_code} - {response.text}"
        )


def insert_archive_metadata(config: ArchiveConfig, payload: Dict[str, Any]) -> None:
    url = f"{config.supabase_url}/rest/v1/production_report_archives"

    response = request_with_retry(
        "POST",
        url,
        headers={
            **headers(config, "application/json"),
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        params={"on_conflict": "pipeline_name,github_run_id,archive_version"},
        json=[payload],
    )

    if response.status_code not in [200, 201, 204]:
        raise RuntimeError(
            f"Metadata insert failed: HTTP {response.status_code} - {response.text}"
        )


def main() -> int:
    config = load_config()
    run_dt = now_sgt()

    files = list_archive_files(config)
    object_prefix = build_object_prefix(config, run_dt)

    manifest = build_manifest(config, files, object_prefix, run_dt)
    archive_path = create_zip_bundle(config, files, manifest)

    archive_sha = sha256_file(archive_path)
    archive_size = archive_path.stat().st_size

    checksum_text = f"{archive_sha}  {archive_path.name}\n"

    manifest_path = config.staging_dir / "manifest.json"
    checksum_path = config.staging_dir / "checksum.sha256"
    telemetry_path = config.staging_dir / "telemetry_snapshot.json"

    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    checksum_path.write_text(checksum_text, encoding="utf-8")
    telemetry_path.write_text(
        json.dumps(build_telemetry_snapshot(config, run_dt), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    archive_object = f"{object_prefix}/{archive_path.name}"
    manifest_object = f"{object_prefix}/manifest.json"
    checksum_object = f"{object_prefix}/checksum.sha256"
    telemetry_object = f"{object_prefix}/telemetry_snapshot.json"

    upload_file(config, archive_path, archive_object)
    upload_file(config, manifest_path, manifest_object)
    upload_file(config, checksum_path, checksum_object)
    upload_file(config, telemetry_path, telemetry_object)

    counts = classify_counts(files)

    metadata_payload = {
        "run_timestamp_sgt": run_dt.isoformat(),
        "run_date_sgt": run_dt.date().isoformat(),
        "pipeline_name": config.pipeline_name,
        "environment": config.environment,
        "status": config.status,
        "github_run_id": config.github_run_id,
        "github_workflow": config.github_workflow,
        "github_repository": config.github_repository,
        "github_branch": config.github_branch,
        "github_sha": config.github_sha,
        "storage_provider": "SUPABASE_STORAGE",
        "storage_bucket": config.bucket,
        "storage_object_path": archive_object,
        "manifest_object_path": manifest_object,
        "checksum_object_path": checksum_object,
        "telemetry_object_path": telemetry_object,
        "archive_filename": archive_path.name,
        "archive_size_bytes": archive_size,
        "archive_sha256": archive_sha,
        "compression_format": "zip",
        "archive_version": "v1",
        "archival_status": "SUCCESS",
        **counts,
    }

    insert_archive_metadata(config, metadata_payload)

    print("[ARCHIVE SUCCESS]")
    print(f"Archive object: {archive_object}")
    print(f"Archive SHA256: {archive_sha}")
    print(f"Files archived: {counts['file_count']}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ARCHIVE FAILED] {exc}", file=sys.stderr)
        raise