from transmission_layers.expectation_failure.real_data.b1_real_entity_registry import (
    FIXED_ENTITY_ORDER,
    build_entity_lookup_proxy,
    build_fixed_real_entity_registry,
)


def test_b1_registry_deterministic_ordering():
    registry = build_fixed_real_entity_registry()
    assert [r["ticker"] for r in registry] == list(FIXED_ENTITY_ORDER)
    assert [r["deterministic_order"] for r in registry] == list(range(1, 11))


def test_b1_registry_immutable_lookup_proxy():
    registry = build_fixed_real_entity_registry()
    proxy = build_entity_lookup_proxy(registry)
    assert proxy["NVDA"]["ticker"] == "NVDA"
    try:
        proxy["NVDA"]["ticker"] = "X"
        assert False, "proxy should be immutable"
    except TypeError:
        assert True
