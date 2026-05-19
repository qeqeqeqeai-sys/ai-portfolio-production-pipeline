import json
import subprocess
from pathlib import Path

from transmission_layers.intelligence.tier3i.historical_replay import build_historical_structural_replay


def _base_records():
    return [
        {"run_date_sgt": "2026-01-01", "regime_state": "stable", "drift_direction": "stable", "contagion_risk_state": "contained", "structural_fragility_score": 0.2, "overheating_score": 0.2, "contagion_pressure_score": 0.2, "fragmentation_score": 0.2, "structural_stability_score": 0.8},
        {"run_date_sgt": "2026-01-02", "regime_state": "transitioning", "drift_direction": "deteriorating", "contagion_risk_state": "spreading", "structural_fragility_score": 0.5, "overheating_score": 0.4, "contagion_pressure_score": 0.6, "fragmentation_score": 0.4, "structural_stability_score": 0.5},
        {"run_date_sgt": "2026-01-03", "regime_state": "fragile", "drift_direction": "deteriorating", "contagion_risk_state": "fragile", "structural_fragility_score": 0.7, "overheating_score": 0.6, "contagion_pressure_score": 0.75, "fragmentation_score": 0.6, "structural_stability_score": 0.3},
    ]


def test_deterministic_replay_output_and_bounded_scores():
    a = build_historical_structural_replay(_base_records())
    b = build_historical_structural_replay(_base_records())
    assert a == b
    for key, val in a.items():
        if key.endswith("_score") or key.endswith("_peak"):
            assert 0.0 <= float(val) <= 1.0


def test_insufficient_history_and_thin_band():
    out = build_historical_structural_replay([_base_records()[0]])
    assert out["replay_health_state"] == "insufficient_history"
    assert out["structural_memory_band"] == "thin"
    assert out["fragility_trend_score"] == 0.0


def test_sorting_and_duplicate_date_handling():
    records = [_base_records()[2], _base_records()[0], {**_base_records()[1], "structural_fragility_score": 0.51}, _base_records()[1]]
    out = build_historical_structural_replay(records)
    assert out["replay_window_size"] == 3
    assert out["replay_start_date"] == "2026-01-01"
    assert out["historical_fragility_peak"] == 0.7


def test_counts_and_peaks_and_trends():
    out = build_historical_structural_replay(_base_records())
    assert out["historical_overheating_peak"] == 0.6
    assert out["regime_transition_count"] == 2
    assert out["drift_reversal_count"] == 0
    assert out["contagion_state_change_count"] == 2
    assert out["persistent_fragility_count"] == 1
    assert out["persistent_overheating_count"] == 0
    assert out["persistent_contagion_count"] == 1
    assert out["recovery_count"] == 0
    assert out["fragility_trend_score"] == 0.5


def test_health_classifications_and_memory_bands():
    stable = build_historical_structural_replay([
        {"run_date_sgt": "2026-01-01", "regime_state": "stable", "structural_fragility_score": 0.1, "overheating_score": 0.1, "contagion_pressure_score": 0.1, "fragmentation_score": 0.1, "structural_stability_score": 0.5},
        {"run_date_sgt": "2026-01-02", "regime_state": "stable", "structural_fragility_score": 0.12, "overheating_score": 0.1, "contagion_pressure_score": 0.1, "fragmentation_score": 0.1, "structural_stability_score": 0.55},
        {"run_date_sgt": "2026-01-03", "regime_state": "stable", "structural_fragility_score": 0.13, "overheating_score": 0.11, "contagion_pressure_score": 0.12, "fragmentation_score": 0.1, "structural_stability_score": 0.58},
    ])
    assert stable["replay_health_state"] == "historically_stable"
    assert stable["structural_memory_band"] == "usable"

    improving = build_historical_structural_replay([
        {"run_date_sgt": "2026-01-01", "regime_state": "transitioning", "structural_fragility_score": 0.5, "overheating_score": 0.4, "contagion_pressure_score": 0.4, "fragmentation_score": 0.4, "structural_stability_score": 0.2},
        {"run_date_sgt": "2026-01-02", "regime_state": "stable", "structural_fragility_score": 0.2, "overheating_score": 0.2, "contagion_pressure_score": 0.2, "fragmentation_score": 0.2, "structural_stability_score": 0.8},
    ])
    assert improving["replay_health_state"] == "historically_improving"

    mixed = build_historical_structural_replay([
        {"run_date_sgt": "2026-01-01", "regime_state": "stable", "structural_fragility_score": 0.2, "overheating_score": 0.6, "contagion_pressure_score": 0.2, "fragmentation_score": 0.3, "structural_stability_score": 0.3},
        {"run_date_sgt": "2026-01-02", "regime_state": "overheated", "structural_fragility_score": 0.2, "overheating_score": 0.2, "contagion_pressure_score": 0.8, "fragmentation_score": 0.3, "structural_stability_score": 0.4},
    ])
    assert mixed["replay_health_state"] in {"historically_mixed", "historically_deteriorating"}


def test_other_health_states_and_explainability():
    deteriorating = build_historical_structural_replay(_base_records())
    assert deteriorating["replay_health_state"] in {"historically_deteriorating", "historically_fragile", "historically_contagious", "historically_mixed"}
    assert "explainability_payload" in deteriorating

    strong = build_historical_structural_replay(_base_records() + [
        {"run_date_sgt": "2026-01-04", "regime_state": "overheated", "overheating_score": 0.75, "structural_fragility_score": 0.65, "contagion_pressure_score": 0.64, "fragmentation_score": 0.65, "structural_stability_score": 0.2},
        {"run_date_sgt": "2026-01-05", "regime_state": "overheated", "overheating_score": 0.8, "structural_fragility_score": 0.7, "contagion_pressure_score": 0.7, "fragmentation_score": 0.7, "structural_stability_score": 0.2},
        {"run_date_sgt": "2026-01-06", "regime_state": "fragile", "contagion_risk_state": "contaminated", "overheating_score": 0.3, "structural_fragility_score": 0.8, "contagion_pressure_score": 0.8, "fragmentation_score": 0.8, "structural_stability_score": 0.1},
    ])
    assert strong["structural_memory_band"] == "strong"
    assert strong["replay_health_state"] in {"historically_overheated", "historically_fragile", "historically_contagious"}


def test_cli_writes_summary_and_no_tier3h5_dependency():
    subprocess.run(["python", "-m", "transmission_layers.intelligence.tier3i.historical_replay"], check=True)
    p = Path("logs/tier3i_historical_replay_summary.json")
    assert p.exists()
    data = json.loads(p.read_text(encoding="utf-8"))
    assert data["tier"] == "3I"
    assert data["phase"] == "3D"
