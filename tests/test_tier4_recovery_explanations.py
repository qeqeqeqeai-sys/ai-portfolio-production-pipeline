from transmission_layers.intelligence.tier4.recovery_explanations import explain_recovery_dynamics


def test_recovery_explanation_stable_length_and_template():
    summary = {"recovery_durability_score": 0.8, "recovery_persistence_score": 0.7, "relapse_detected": False, "dominant_decay_factor": "none"}
    text = explain_recovery_dynamics(summary)
    assert "factors:" in text
    assert len(text) <= 280
