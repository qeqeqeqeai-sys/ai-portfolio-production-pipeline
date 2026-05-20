from transmission_layers.intelligence.tier5.federation_topology import federation_topology_diagnostics

def test_federation_topology_contract():
    r = federation_topology_diagnostics([{"id":"A"},{"id":"B"}], [{"redundancy":0.8}])
    assert set(r) == {"topology_density_score","topology_redundancy_score","topology_cohesion_score"}
