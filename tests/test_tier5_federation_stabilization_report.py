from transmission_layers.intelligence.tier5.federation_stabilization_report import build_federation_stabilization_report


def test_fixed_template_report_stability():
    base = {"federation_integrity_classification": "stable", "dominant_integrity_factor": "federation_integrity_score"}
    a = build_federation_stabilization_report(base)
    b = build_federation_stabilization_report(base)
    assert a == b
    assert "Tier5H stabilization report" in a["report_template"]
