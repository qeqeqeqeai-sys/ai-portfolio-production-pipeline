#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from transmission_layers.expectation_failure.expectation_intelligence.sde_controlled_semantic_density_expansion import (
    build_sde_ecosystem_readiness_diagnostics,
    build_sde_curated_expansion_plan,
    certify_sde_governance_preservation,
)

CANDIDATES = [
    {"entity_id":"E1","adjacency_cluster":"ai_infra","propagation_pathway":"compute_to_margin","contradiction_topology":"demand_vs_capacity","regime_cluster":"risk_on","linked_entity_refs":["E2","E3"],"topology_relevance":0.91,"contradiction_interaction_potential":0.82,"propagation_pathway_value":0.87,"regime_diversity_value":0.72,"structural_interaction_strength":0.9,"monoculture_penalty":0.2,"information_density":0.85},
    {"entity_id":"E2","adjacency_cluster":"ai_apps","propagation_pathway":"hype_to_revenue","contradiction_topology":"valuation_vs_fundamentals","regime_cluster":"risk_on","linked_entity_refs":["E1"],"topology_relevance":0.83,"contradiction_interaction_potential":0.79,"propagation_pathway_value":0.7,"regime_diversity_value":0.6,"structural_interaction_strength":0.74,"monoculture_penalty":0.15,"information_density":0.82},
    {"entity_id":"E3","adjacency_cluster":"semis","propagation_pathway":"inventory_to_pricing","contradiction_topology":"guidance_vs_orders","regime_cluster":"risk_off","linked_entity_refs":["E1","E4"],"topology_relevance":0.88,"contradiction_interaction_potential":0.77,"propagation_pathway_value":0.81,"regime_diversity_value":0.84,"structural_interaction_strength":0.79,"monoculture_penalty":0.1,"information_density":0.78},
    {"entity_id":"E4","adjacency_cluster":"semis","propagation_pathway":"inventory_to_pricing","contradiction_topology":"guidance_vs_orders","regime_cluster":"risk_off","linked_entity_refs":[],"topology_relevance":0.56,"contradiction_interaction_potential":0.42,"propagation_pathway_value":0.48,"regime_diversity_value":0.52,"structural_interaction_strength":0.4,"monoculture_penalty":0.5,"information_density":0.33},
]


def main() -> None:
    diagnostics = build_sde_ecosystem_readiness_diagnostics(ecosystem_candidates=CANDIDATES, target_entity_count=300)
    plan = build_sde_curated_expansion_plan(ecosystem_candidates=CANDIDATES, diagnostics=diagnostics, target_entity_count=300, max_step_size=60)
    cert = certify_sde_governance_preservation(diagnostics=diagnostics, plan=plan)

    md = f"""# Phase SDE — Controlled Semantic Density Expansion

## strategic reprioritization
Replay ecology optimization is deferred. Current bottleneck is semantic ecosystem richness upstream of LR6 operationalization.

## bottleneck observations
- semantic breadth remains narrow
- replay-family diversity remains limited
- structural contrast remains insufficient
- transition diversity remains underdeveloped
- saturation risk can emerge before longitudinal richness forms

## curated ecosystem expansion intent
SDE prioritizes curated ecosystem adjacency, expectation propagation pathways, contradiction-topology enrichment, regime-diverse semantic clusters, and structurally linked entity groups.

## deterministic diagnostics
`{json.dumps(diagnostics, indent=2)}`

## bounded curated expansion plan
`{json.dumps(plan.get('bounded_growth_recommendation'), indent=2)}`

## anti-pattern exclusions
- no random ticker expansion
- no semantic monoculture scaling
- no replay flooding
- no low-information entity growth
- no isolated/non-interacting entity inclusion

## LR6 sequencing decision
Retain reusable LR6 diagnostics primitives, but defer full LR6 replay ecology operationalization until SDE demonstrates materially improved ecosystem richness.

## governance preservation
- append-only semantics preserved
- D8.B4/D21 boundaries preserved
- no direct SQL, no unauthorized persistence
- deterministic checksum lineage: `{cert.get('checksum')}`

## recommendation
Proceed with small, bounded SDE waves toward ~300 curated entities, and only scale further when ecology quality remains high.
"""
    out = Path("reports/sde_controlled_semantic_density_expansion.md")
    out.write_text(md, encoding="utf-8")
    print(json.dumps({"status": "ok", "report": str(out), "checksum": cert.get("checksum")}, indent=2))

if __name__ == "__main__":
    main()
