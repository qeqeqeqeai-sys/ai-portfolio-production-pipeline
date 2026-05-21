from transmission_layers.operationalization.serialization import stable_checksum, stable_serialize


def test_same_payload_gives_same_serialization():
    payload = {"b": 2, "a": 1, "text": "caf\u00e9"}
    first = stable_serialize(payload)
    second = stable_serialize(payload)
    assert first == second


def test_shuffled_key_order_gives_same_serialization():
    payload_a = {"z": 1, "a": 2, "m": {"y": 9, "x": 8}}
    payload_b = {"m": {"x": 8, "y": 9}, "a": 2, "z": 1}
    assert stable_serialize(payload_a) == stable_serialize(payload_b)


def test_nested_structures_deterministic():
    payload = {
        "nested": [
            {"k2": [3, 2, 1], "k1": {"n": True, "m": None}},
            ("alpha", {"beta": 2}),
        ]
    }
    first = stable_serialize(payload)
    second = stable_serialize(payload)
    assert first == second


def test_set_values_sorted_deterministically():
    payload_a = {"values": {"b", "a", "c"}}
    payload_b = {"values": {"c", "b", "a"}}
    assert stable_serialize(payload_a) == stable_serialize(payload_b)


def test_input_is_not_mutated():
    payload = {"x": [1, 2], "s": {3, 1}, "d": {"b": 2, "a": 1}}
    original = {"x": [1, 2], "s": {3, 1}, "d": {"b": 2, "a": 1}}
    _ = stable_serialize(payload)
    assert payload == original
    assert isinstance(payload["s"], set)


def test_checksum_stable_across_repeated_calls():
    payload = {"a": 1, "b": [1, 2, 3]}
    assert stable_checksum(payload) == stable_checksum(payload)


def test_checksum_changes_when_payload_changes():
    payload_a = {"a": 1, "b": 2}
    payload_b = {"a": 1, "b": 3}
    assert stable_checksum(payload_a) != stable_checksum(payload_b)
