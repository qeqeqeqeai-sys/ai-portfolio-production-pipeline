#!/usr/bin/env python3
"""
archive_production_reports.py

Creates a persistent archive bundle from outputs/ and logs/,
uploads it to Supabase Storage, and records metadata in
public.production_report_archives.
"""

from __future__ import annotations

import hashlib
import json
import mimetypes
import os
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from zoneinfo import ZoneInfo


SGT = ZoneInfo("Asia/Singapore")


def get_env(name: str, default: Optional[str] = None, required: bool = False) -> str:
    value = os.getenv(name, default)
    if required and not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return str(value)


def request_with_retry(
    method: str,
    url: str,
    *,
    headers: Dict[str, str],
    params: Optional[Dict[str, str]] = None,
    json_body: Any = None,
    data: Any = None,
    timeout: int = 60,
    max_attempts: int = 3,
) -> requests.Response:
    last_error: Optional[Exception] = None

    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_body,
                data=data,
                timeout=timeout,
            )

            if response.status_code < 500:
                return response

            last_error = RuntimeError(
                f"HTTP {response.status_code}: {response.text[:500]}"
            )

        except Exception as exc:
            last_error = exc

        print(f"[RETRY] {method} {url} attempt {attempt}/{max_attempts} failed: {last_error}")

    raise RuntimeError(f"Request failed after {max_attempts} attempts: {last_error}")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()

    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)

    return h.hexdigest()


def collect_files(outputs_dir: Path, logs_dir: Path) -> List[Path]:
    files: List[Path] = []

    for base_dir in [outputs_dir, logs_dir]:
        if not base_dir.exists():
            print(f"[WARN] Directory does not exist: {base_dir}")
            continue

        for path in base_dir.rglob("*"):
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

    for path in files:
        suffix = path.suffix.lower()
        name = path.name.lower()

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


def build_object_prefix(
    environment: str,
    pipeline_name: str,
    status: str,
    github_run_id: str,
    run_dt: datetime,
) -> str:
    status_folder = "success" if status.upper() == "SUCCESS" else "failed"

    return (
        f"{environment}/"
        f"{pipeline_name}/"
        f"{run_dt:%Y}/"
        f"{run_dt:%m}/"
        f"{run_dt:%d}/"
        f"{status_folder}/"
        f"run_{github_run_id}"
    )


def safe_relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd())).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def build_manifest(
    *,
    files: List[Path],
    run_dt: datetime,
    pipeline_name: str,
    environment: str,
    status: str,
    github_run_id: str,
    github_workflow: str,
    github_repository: str,
    github_branch: str,
    github_sha: str,
    bucket: str,
    object_prefix: str,
) -> Dict[str, Any]:
    file_records = []

    for path in files:
        file_records.append(
            {
                "path": safe_relative_path(path),
                "size_bytes": path.stat().st_size,
                "sha256": sha256_file(path),
                "modified_at_utc": datetime.utcfromtimestamp(
                    path.stat().st_mtime
                ).isoformat()
                + "Z",
            }
        )

    return {
        "archive_version": "v1",
        "created_at_sgt": run_dt.isoformat(),
        "run_date_sgt": run_dt.date().isoformat(),
        "pipeline_name": pipeline_name,
        "environment": environment,
        "status": status,
        "github": {
            "run_id": github_run_id,
            "workflow": github_workflow,
            "repository": github_repository,
            "branch": github_branch,
            "sha": github_sha,
        },
        "storage": {
            "provider": "SUPABASE_STORAGE",
            "bucket": bucket,
            "object_prefix": object_prefix,
        },
        "counts": classify_counts(files),
        "files": file_records,
    }


def create_zip_bundle(
    *,
    files: List[Path],
    staging_dir: Path,
    archive_filename: str,
    manifest: Dict[str, Any],
    telemetry_snapshot: Dict[str, Any],
) -> Dict[str, Path]:
    staging_dir.mkdir(parents=True, exist_ok=True)

    archive_path = staging_dir / archive_filename
    manifest_path = staging_dir / "manifest.json"
    telemetry_path = staging_dir / "telemetry_snapshot.json"
    checksum_path = staging_dir / "checksum.sha256"

    manifest_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    telemetry_path.write_text(
        json.dumps(telemetry_snapshot, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    with zipfile.ZipFile(
        archive_path,
        mode="w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        for path in files:
            zf.write(path, arcname=safe_relative_path(path))

        zf.write(manifest_path, arcname="metadata/manifest.json")
        zf.write(telemetry_path, arcname="metadata/telemetry_snapshot.json")

    archive_sha = sha256_file(archive_path)
    checksum_path.write_text(
        f"{archive_sha}  {archive_filename}\n",
        encoding="utf-8",
    )

    with zipfile.ZipFile(
        archive_path,
        mode="a",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=6,
    ) as zf:
        zf.write(checksum_path, arcname="metadata/checksum.sha256")

    return {
        "archive": archive_path,
        "manifest": manifest_path,
        "telemetry": telemetry_path,
        "checksum": checksum_path,
    }


def supabase_headers(service_role_key: str, content_type: Optional[str] = None) -> Dict[str, str]:
    headers = {
        "apikey": service_role_key,
        "Authorization": f"Bearer {service_role_key}",
    }

    if content_type:
        headers["Content-Type"] = content_type

    return headers


def upload_to_supabase_storage(
    *,
    supabase_url: str,
    service_role_key: str,
    bucket: str,
    local_path: Path,
    object_path: str,
) -> None:
    guessed_type = mimetypes.guess_type(str(local_path))[0]
    content_type = guessed_type or "application/octet-stream"

    if local_path.suffix.lower() == ".zip":
        content_type = "application/zip"
    elif local_path.suffix.lower() == ".json":
        content_type = "application/json"
    elif local_path.suffix.lower() == ".sha256":
        content_type = "text/plain"

    url = f"{supabase_url.rstrip('/')}/storage/v1/object/{bucket}/{object_path}"

    print(f"[UPLOAD] {local_path} -> {bucket}/{object_path}")
    print(f"[UPLOAD] content_type={content_type}, size={local_path.stat().st_size} bytes")

    with local_path.open("rb") as f:
        response = request_with_retry(
            "PUT",
            url,
            headers={
                **supabase_headers(service_role_key, content_type),
                "x-upsert": "true",
            },
            data=f,
            timeout=120,
            max_attempts=3,
        )

    if response.status_code not in [200, 201]:
        raise RuntimeError(
            f"Supabase Storage upload failed for {object_path}: "
            f"HTTP {response.status_code} - {response.text}"
        )


def insert_archive_metadata(
    *,
    supabase_url: str,
    service_role_key: str,
    payload: Dict[str, Any],
) -> None:
    url = f"{supabase_url.rstrip('/')}/rest/v1/production_report_archives"

    response = request_with_retry(
        "POST",
        url,
        headers={
            **supabase_headers(service_role_key, "application/json"),
            "Prefer": "resolution=merge-duplicates,return=minimal",
        },
        params={
            "on_conflict": "pipeline_name,github_run_id,archive_version",
        },
        json_body=[payload],
        timeout=60,
        max_attempts=3,
    )

    if response.status_code not in [200, 201, 204]:
        raise RuntimeError(
            f"Supabase metadata insert failed: "
            f"HTTP {response.status_code} - {response.text}"
        )


def main() -> int:
    run_dt = datetime.now(SGT)

    supabase_url = get_env("SUPABASE_URL", required=True)
    service_role_key = get_env("SUPABASE_SERVICE_ROLE_KEY", required=True)

    bucket = get_env("ARCHIVE_BUCKET", "ai-production-archives")
    pipeline_name = get_env("PIPELINE_NAME", "AI_PORTFOLIO_PRODUCTION")
    environment = get_env("ENVIRONMENT", "prod")
    status = get_env("PIPELINE_STATUS", "UNKNOWN").upper()

    github_run_id = get_env("GITHUB_RUN_ID", "local")
    github_workflow = get_env("GITHUB_WORKFLOW", "")
    github_repository = get_env("GITHUB_REPOSITORY", "")
    github_branch = get_env("GITHUB_REF_NAME", "")
    github_sha = get_env("GITHUB_SHA", "")

    outputs_dir = Path(get_env("OUTPUTS_DIR", "outputs"))
    logs_dir = Path(get_env("LOGS_DIR", "logs"))
    staging_dir = Path(get_env("ARCHIVE_STAGING_DIR", "archive_staging"))

    files = collect_files(outputs_dir, logs_dir)

    if not files:
        raise RuntimeError("No files found to archive in outputs/ or logs/")

    object_prefix = build_object_prefix(
        environment=environment,
        pipeline_name=pipeline_name,
        status=status,
        github_run_id=github_run_id,
        run_dt=run_dt,
    )

    archive_filename = (
        f"{pipeline_name}_{run_dt:%Y%m%d}_run_{github_run_id}_{status}_archive.zip"
    )

    telemetry_snapshot = {
        "snapshot_created_at_sgt": run_dt.isoformat(),
        "run_date_sgt": run_dt.date().isoformat(),
        "pipeline_name": pipeline_name,
        "environment": environment,
        "status": status,
        "github_run_id": github_run_id,
        "github_workflow": github_workflow,
        "github_repository": github_repository,
        "github_branch": github_branch,
        "github_sha": github_sha,
    }

    manifest = build_manifest(
        files=files,
        run_dt=run_dt,
        pipeline_name=pipeline_name,
        environment=environment,
        status=status,
        github_run_id=github_run_id,
        github_workflow=github_workflow,
        github_repository=github_repository,
        github_branch=github_branch,
        github_sha=github_sha,
        bucket=bucket,
        object_prefix=object_prefix,
    )

    paths = create_zip_bundle(
        files=files,
        staging_dir=staging_dir,
        archive_filename=archive_filename,
        manifest=manifest,
        telemetry_snapshot=telemetry_snapshot,
    )

    archive_path = paths["archive"]
    manifest_path = paths["manifest"]
    telemetry_path = paths["telemetry"]
    checksum_path = paths["checksum"]

    archive_sha = sha256_file(archive_path)
    archive_size = archive_path.stat().st_size
    counts = classify_counts(files)

    archive_object_path = f"{object_prefix}/{archive_filename}"
    manifest_object_path = f"{object_prefix}/manifest.json"
    telemetry_object_path = f"{object_prefix}/telemetry_snapshot.json"
    checksum_object_path = f"{object_prefix}/checksum.sha256"

    print("Archive created successfully.")
    print(f"Archive: {archive_path}")
    print(f"SHA256: {archive_sha}")
    print(f"Files archived: {len(files)}")

    upload_to_supabase_storage(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        bucket=bucket,
        local_path=archive_path,
        object_path=archive_object_path,
    )

    upload_to_supabase_storage(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        bucket=bucket,
        local_path=manifest_path,
        object_path=manifest_object_path,
    )

    upload_to_supabase_storage(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        bucket=bucket,
        local_path=telemetry_path,
        object_path=telemetry_object_path,
    )

    upload_to_supabase_storage(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        bucket=bucket,
        local_path=checksum_path,
        object_path=checksum_object_path,
    )

    metadata_payload = {
        "run_timestamp_sgt": run_dt.isoformat(),
        "run_date_sgt": run_dt.date().isoformat(),
        "pipeline_name": pipeline_name,
        "environment": environment,
        "status": status,
        "github_run_id": github_run_id,
        "github_workflow": github_workflow,
        "github_repository": github_repository,
        "github_branch": github_branch,
        "github_sha": github_sha,
        "storage_provider": "SUPABASE_STORAGE",
        "storage_bucket": bucket,
        "storage_object_path": archive_object_path,
        "manifest_object_path": manifest_object_path,
        "checksum_object_path": checksum_object_path,
        "telemetry_object_path": telemetry_object_path,
        "archive_filename": archive_filename,
        "archive_size_bytes": archive_size,
        "archive_sha256": archive_sha,
        "file_count": counts["file_count"],
        "csv_count": counts["csv_count"],
        "html_count": counts["html_count"],
        "png_count": counts["png_count"],
        "log_count": counts["log_count"],
        "validation_file_count": counts["validation_file_count"],
        "compression_format": "zip",
        "archive_version": "v1",
        "archival_status": "SUCCESS",
        "error_message": None,
    }

    insert_archive_metadata(
        supabase_url=supabase_url,
        service_role_key=service_role_key,
        payload=metadata_payload,
    )

    print("[ARCHIVE SUCCESS]")
    print(f"Storage bucket: {bucket}")
    print(f"Archive object: {archive_object_path}")
    print(f"Manifest object: {manifest_object_path}")
    print(f"Telemetry object: {telemetry_object_path}")
    print(f"Checksum object: {checksum_object_path}")

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"[ARCHIVE FAILED] {exc}", file=sys.stderr)
        raise
