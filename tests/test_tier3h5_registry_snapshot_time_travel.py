import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.registry_snapshot_archive import run_phase2d_snapshot_archive
from transmission_layers.asset_discovery.tier3h5.registry_snapshot_time_travel import run_phase2d_time_travel_reconstruction


def _rows(snapshot_id: str = "snap-301"):
    return {
        "lineage": [
            {
                "registry_snapshot_id": snapshot_id,
                "source_name": "exchange_primary",
                "source_dataset_version": "2026.05",
                "ingestion_run_id": "run-301",
                "registry_effective_date": "2026-05-18",
                "registry_region": "US",
                "normalization_version": "tier3h5_phase2a_v1",
                "records_seen": 100,
                "records_accepted": 98,
                "records_rejected": 2,
                "duplicates": 1,
                "conflicts": 0,
                "normalization_failures": 0,
                "deterministic_id_collisions": 0,
            }
        ]
    }


def test_snapshot_archive_manifest_and_hash_determinism(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("logs/tier3h5_registry_snapshot_lineage.json").write_text(json.dumps(_rows()), encoding="utf-8")

    first = run_phase2d_snapshot_archive()
    second = run_phase2d_snapshot_archive()

    assert first["manifest"]["snapshot_hash"] == second["manifest"]["snapshot_hash"]
    assert first["manifest"]["archival_status"] == "archived"


def test_time_travel_reconstruction_and_hash_verification(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("logs/tier3h5_registry_snapshot_lineage.json").write_text(json.dumps(_rows("snap-302")), encoding="utf-8")

    run_phase2d_snapshot_archive()
    summary = run_phase2d_time_travel_reconstruction("snap-302")

    assert summary["reconstruction_status"] == "reconstructed"
    assert summary["snapshot_hash_verified"] is True


def test_archive_unavailable_and_snapshot_not_found(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()

    unavailable = run_phase2d_time_travel_reconstruction("snap-missing")
    assert unavailable["reconstruction_status"] == "archive_unavailable"

    Path("logs/tier3h5_registry_snapshot_lineage.json").write_text(json.dumps(_rows("snap-303")), encoding="utf-8")
    run_phase2d_snapshot_archive()
    not_found = run_phase2d_time_travel_reconstruction("snap-other")
    assert not_found["reconstruction_status"] == "snapshot_not_found"


def test_hash_stability_excludes_archive_timestamp(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    Path("logs").mkdir()
    Path("logs/tier3h5_registry_snapshot_lineage.json").write_text(json.dumps(_rows("snap-304")), encoding="utf-8")

    run_phase2d_snapshot_archive()
    archive = json.loads(Path("logs/tier3h5_canonical_registry_snapshot_archive.json").read_text(encoding="utf-8"))
    manifest = json.loads(Path("logs/tier3h5_snapshot_archive_manifest.json").read_text(encoding="utf-8"))
    archive["archived_at_sgt"] = "2099-01-01T00:00:00Z"
    Path("logs/tier3h5_canonical_registry_snapshot_archive.json").write_text(json.dumps(archive), encoding="utf-8")

    summary = run_phase2d_time_travel_reconstruction("snap-304")
    assert summary["snapshot_hash"] == manifest["snapshot_hash"]
    assert summary["snapshot_hash_verified"] is True
