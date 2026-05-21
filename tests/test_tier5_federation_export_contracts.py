from transmission_layers.intelligence.tier5.federation_export_contracts import collect_tier5_export_inventory


def test_export_inventory_deterministic():
    a = collect_tier5_export_inventory()
    b = collect_tier5_export_inventory()
    assert a == b
    assert "build_federation_health_sort_key" in a["tier5_ranking_helpers"]
