from transmission_layers.intelligence.tier5.federation_observability_signatures import observability_checksum


def test_observability_checksum_stability_with_rounding():
    assert observability_checksum({"x": 0.11111119}, "p") == observability_checksum({"x": 0.11111111}, "p")
