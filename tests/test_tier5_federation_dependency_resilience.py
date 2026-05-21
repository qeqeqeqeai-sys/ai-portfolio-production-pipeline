from copy import deepcopy

from transmission_layers.intelligence.tier5.federation_dependency_resilience import federation_dependency_resilience


def test_dependency_resilience_disconnected_and_immutable():
    deps=[{"source":"A","target":"B"},{"source":"B","target":"C"}]
    frozen=deepcopy(deps)
    out=federation_dependency_resilience(deps,{"federation_guardrails_score":0.4})
    assert deps==frozen
    assert 0<=out["federation_dependency_resilience_score"]<=1
    empty=federation_dependency_resilience([], {"federation_guardrails_score":1.0})
    assert empty["federation_dependency_resilience_score"]==0.5
