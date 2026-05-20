from transmission_layers.intelligence.tier4.recovery_dynamics import (
    compare_recovery_trajectories,
    compute_recovery_durability,
    compute_recovery_trajectory,
)


def test_recovery_trajectory_deterministic_and_bounded():
    states = [
        {"resilience": 0.85, "overload": 0.2, "fragmentation": 0.15},
        {"resilience": 0.83, "overload": 0.22, "fragmentation": 0.16},
    ]
    a = compute_recovery_trajectory(states)
    b = compute_recovery_trajectory(states)
    assert a["recovery_checksum"] == b["recovery_checksum"]
    assert 0.0 <= a["bounded_recovery_score"] <= 1.0


def test_recovery_durability_and_comparison_bounds():
    states_a = [{"resilience": 0.9, "overload": 0.1, "fragmentation": 0.1}]
    states_b = [{"resilience": 0.4, "overload": 0.7, "fragmentation": 0.6}]
    a = compute_recovery_durability(states_a)
    b = compute_recovery_durability(states_b)
    cmp_ = compare_recovery_trajectories(
        compute_recovery_trajectory(states_a), compute_recovery_trajectory(states_b)
    )
    assert 0.0 <= a["recovery_durability_score"] <= 1.0
    assert -1.0 <= cmp_["bounded_recovery_score_delta"] <= 1.0
