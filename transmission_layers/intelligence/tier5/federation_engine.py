from __future__ import annotations

from typing import Any

from .federation_diagnostics import (
    bridge_boundary_diagnostics,
    contagion_bottleneck_diagnostics,
    cross_system_transmission_diagnostics,
    federation_signatures,
    federation_topology_diagnostics,
    fixed_template_explanations,
    survivability_recovery_dependency_diagnostics,
)


def run_tier5a_federation(
    *,
    systems: list[dict[str, Any]],
    bridges: list[dict[str, Any]],
    transmissions: list[dict[str, Any]],
    contagion_paths: list[dict[str, Any]],
    dependencies: list[dict[str, Any]],
) -> dict[str, Any]:
    topology = federation_topology_diagnostics(systems, bridges)
    cross_tx = cross_system_transmission_diagnostics(transmissions)
    bridge = bridge_boundary_diagnostics(bridges)
    contagion = contagion_bottleneck_diagnostics(contagion_paths)
    survivability = survivability_recovery_dependency_diagnostics(dependencies)

    result = {
        "tier": "5",
        "phase": "5A",
        "federation_mode": "deterministic",
        "status": "success",
        **topology,
        **cross_tx,
        **bridge,
        **contagion,
        **survivability,
    }
    result.update(fixed_template_explanations(result))
    result.update(federation_signatures(result))
    return result
