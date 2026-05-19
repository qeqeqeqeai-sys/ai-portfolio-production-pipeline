import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.governance_orchestration import run_governance_production_orchestration


def _read(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _seed_inputs() -> None:
    p = Path("logs/tier3h5_phase3a_cross_registry_summary.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"deterministic_alias_count": 1, "linkage_mode": "deterministic_exact_match_only", "enforcement_enabled": False, "canonical_override_enabled": False}, sort_keys=True), encoding="utf-8")


def test_phase5a_orchestration_emits_deterministic_outputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_inputs()
    first = run_governance_production_orchestration()
    second = run_governance_production_orchestration()

    assert first["summary"] == second["summary"]
    assert [s["stage_name"] for s in first["stage_registry"]] == [s["stage_name"] for s in second["stage_registry"]]
    assert _read("logs/tier3h5_orchestration_summary.json") == _read("logs/tier3h5_phase5a_orchestration_summary.json")


def test_phase5a_orchestration_guardrails_and_coordination(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    _seed_inputs()
    run_governance_production_orchestration()

    guardrails = _read("logs/tier3h5_orchestration_guardrails.json")
    artifacts = _read("logs/tier3h5_artifact_coordination_summary.json")
    upload = _read("logs/tier3h5_upload_coordination_summary.json")
    runtime = _read("logs/tier3h5_orchestration_runtime_context.json")

    assert guardrails["advisory_only_verification"] is True
    assert guardrails["exact_match_only_preservation_check"] is True
    assert guardrails["tier3h4_freeze_boundary_preservation_check"] is True
    assert artifacts["artifact_inventory_count"] >= 9
    assert upload["upload_eligibility_status"] in {"eligible", "partial_orchestration_available"}
    assert runtime["tier3h4_freeze_boundary_preserved"] is True
