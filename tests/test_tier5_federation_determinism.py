from transmission_layers.intelligence.tier5.federation_determinism import stable_checksum, deterministic_replay_stability


def test_stable_checksum_rounding_and_ordering():
    a = {"b": 1.123456789, "a": [3, 2, 1]}
    b = {"a": [3, 2, 1], "b": 1.1234567}
    assert stable_checksum(a, prefix="x") == stable_checksum(b, prefix="x")


def test_deterministic_replay_stability():
    score, checksum = deterministic_replay_stability({"x": 1.0})
    assert score == 1.0
    assert checksum.startswith("det_")
