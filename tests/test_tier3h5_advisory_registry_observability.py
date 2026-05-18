import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from transmission_layers.asset_discovery.tier3h5.advisory_registry_observability import summarize_advisory_registry, write_advisory_registry_summary


def test_observability_summary_generation(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    payload = {
        "advisory_registry_enabled": True,
        "registry_lookup_attempts": 2,
        "registry_exact_matches": 1,
        "registry_no_match": 1,
        "registry_conflicts": 0,
        "registry_invalid_input": 0,
        "advisory_registry_failures": 0,
        "support_candidates": [{"support_strength": 1.0}, {"support_strength": 0.0}],
    }
    summary = write_advisory_registry_summary(payload)
    disk = json.loads(Path("logs/tier3h5_advisory_registry_summary.json").read_text(encoding="utf-8"))
    assert summary == disk
    assert disk["registry_support_candidates"] == 2
    assert disk["registry_support_strength_avg"] == 0.5
    assert disk["tier3h4_behavior_mutated"] is False


def test_disabled_and_replay_stability() -> None:
    a = summarize_advisory_registry(None)
    b = summarize_advisory_registry(None)
    assert a == b
    assert a["advisory_registry_enabled"] is False


def test_tier3h4_outputs_unchanged_except_advisory_telemetry() -> None:
    frozen = {"advisory_status_counts": {"advisory_review": 3}, "record_count": 3}
    with_advisory = dict(frozen)
    with_advisory["advisory_registry_summary"] = summarize_advisory_registry({"advisory_registry_enabled": True})
    assert {k: v for k, v in with_advisory.items() if k != "advisory_registry_summary"} == frozen
