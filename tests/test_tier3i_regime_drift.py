import json
import subprocess
import sys
from pathlib import Path

from transmission_layers.intelligence.tier3i.regime_drift import compute_regime_drift


def _record(**overrides):
    base = {
        "run_date_sgt": "2026-01-01",
        "regime_state": "transitioning",
        "graph_concentration_score": 0.5,
        "fragmentation_score": 0.5,
        "overheating_score": 0.5,
        "propagation_density_score": 0.5,
        "structural_fragility_score": 0.5,
        "structural_stability_score": 0.5,
        "regime_transition_warning": False,
        "status": "success",
    }
    base.update(overrides)
    return base


def test_deterministic_drift_output():
    hist = [_record(run_date_sgt="2026-01-01"), _record(run_date_sgt="2026-01-02", structural_stability_score=0.6)]
    assert compute_regime_drift(hist) == compute_regime_drift(hist)


def test_bounded_scores():
    hist = [_record(overheating_score=0.0), _record(overheating_score=1.0)]
    out = compute_regime_drift(hist)
    bounded = [
        out["regime_drift_score"],
        out["fragility_drift"],
        out["stability_drift"],
        out["overheating_drift"],
        out["fragmentation_drift"],
        out["concentration_drift"],
        out["propagation_density_drift"],
        out["deterioration_signal"],
        out["improvement_signal"],
    ]
    assert all(0.0 <= v <= 1.0 for v in bounded)


def test_insufficient_history_handling():
    out = compute_regime_drift([_record()])
    assert out["drift_direction"] == "insufficient_history"


def test_improving_drift_classification():
    out = compute_regime_drift([_record(structural_stability_score=0.40, propagation_density_score=0.35), _record(structural_stability_score=0.63, propagation_density_score=0.62)])
    assert out["drift_direction"] == "improving"


def test_deteriorating_drift_classification():
    out = compute_regime_drift([_record(structural_fragility_score=0.30, overheating_score=0.30, fragmentation_score=0.25), _record(structural_fragility_score=0.75, overheating_score=0.82, fragmentation_score=0.70)])
    assert out["drift_direction"] == "deteriorating"


def test_stable_drift_classification():
    out = compute_regime_drift([_record(), _record()])
    assert out["drift_direction"] == "stable"


def test_mixed_drift_classification():
    out = compute_regime_drift([
        _record(structural_fragility_score=0.40, overheating_score=0.45, structural_stability_score=0.40, propagation_density_score=0.35),
        _record(structural_fragility_score=0.56, overheating_score=0.60, structural_stability_score=0.62, propagation_density_score=0.55),
    ])
    assert out["drift_direction"] == "mixed"


def test_persistent_transition_classification():
    hist = [
        _record(run_date_sgt="2026-01-01", regime_transition_warning=True),
        _record(run_date_sgt="2026-01-02", regime_transition_warning=True),
        _record(run_date_sgt="2026-01-03", regime_transition_warning=True),
    ]
    out = compute_regime_drift(hist)
    assert out["transition_state"] == "persistent_transition"


def test_accelerating_transition_classification():
    hist = [
        _record(run_date_sgt="2026-01-01", regime_transition_warning=True, structural_fragility_score=0.40, overheating_score=0.40),
        _record(run_date_sgt="2026-01-02", regime_transition_warning=True, structural_fragility_score=0.47, overheating_score=0.47),
        _record(run_date_sgt="2026-01-03", regime_transition_warning=True, structural_fragility_score=0.60, overheating_score=0.60),
    ]
    out = compute_regime_drift(hist)
    assert out["transition_state"] == "accelerating_transition"


def test_cooling_transition_classification():
    hist = [
        _record(overheating_score=0.72, structural_stability_score=0.44, regime_transition_warning=True),
        _record(overheating_score=0.64, structural_stability_score=0.50, regime_transition_warning=True),
    ]
    out = compute_regime_drift(hist)
    assert out["transition_state"] == "cooling_transition"


def test_regime_persistence_count():
    hist = [
        _record(regime_state="stable"),
        _record(regime_state="stable"),
        _record(regime_state="stable"),
    ]
    out = compute_regime_drift(hist)
    assert out["regime_persistence_count"] == 3


def test_transition_persistence_count():
    hist = [
        _record(regime_transition_warning=False),
        _record(regime_transition_warning=True),
        _record(regime_transition_warning=True),
    ]
    out = compute_regime_drift(hist)
    assert out["transition_persistence_count"] == 2


def test_explainability_payload_exists():
    out = compute_regime_drift([_record(), _record(structural_stability_score=0.52)])
    payload = out["explainability_payload"]
    assert "drift_rationale" in payload
    assert "key_metric_deltas" in payload
    assert "dominant_drift_drivers" in payload
    assert "transition_explanation" in payload
    assert "deterioration_warnings" in payload
    assert "improvement_notes" in payload
    assert "latest_regime_state" in payload
    assert "previous_regime_state" in payload


def test_cli_writes_output_log(tmp_path):
    repo_root = Path(__file__).resolve().parents[1]
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)
    input_data = [_record(run_date_sgt="2026-01-01"), _record(run_date_sgt="2026-01-02", structural_stability_score=0.61)]
    (logs_dir / "tier3i_structural_regime_summary.json").write_text(json.dumps(input_data), encoding="utf-8")

    subprocess.run(
        [sys.executable, "-m", "transmission_layers.intelligence.tier3i.regime_drift"],
        cwd=tmp_path,
        check=True,
        env={"PYTHONPATH": str(repo_root)},
    )

    output_path = logs_dir / "tier3i_regime_drift_summary.json"
    assert output_path.exists()
    summary = json.loads(output_path.read_text(encoding="utf-8"))
    assert summary["status"] == "success"


def test_no_tier3h5_governance_dependency():
    source = Path("transmission_layers/intelligence/tier3i/regime_drift.py").read_text(encoding="utf-8").lower()
    assert "tier3h5" not in source
    assert "governance" not in source
