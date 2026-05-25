# SDE-1C Candidate Universe Pruning & Topology Quality Report

## objective
Deterministically prune candidate universe from 350 to 300 while preserving governance and interpretability.

## inputs inspected
- configs/sde1_curated_entity_ecosystems.yaml
- reports/sde1_curated_semantic_ecosystem_blueprint.md
- tests/test_sde1_curated_semantic_ecosystem_design.py

## scoring methodology
Deterministic scorecard dimensions: ecosystem_connectivity_score, contradiction_surface_score, propagation_link_score, regime_exposure_score, information_quality_score, semantic_uniqueness_score, replay_ecology_value_score, anti_monoculture_adjustment, low_information_penalty, structural_role_weight.

## pruning methodology
- deterministic ranking
- one guaranteed selection per ecosystem family
- target fill to 300 with per-family and combined monoculture caps
- deterministic tie-breakers

## deterministic tie-breaker rules
1) higher total score 2) higher contradiction score 3) higher propagation score 4) higher connectivity 5) lexical entity_id.

## ecosystem balance before pruning
{'ai_compute_core': 30, 'hyperscaler_cloud_demand': 30, 'semiconductor_supply_chain': 29, 'power_grid_cooling_datacenter_infra': 29, 'memory_networking_interconnect': 29, 'ai_application_software_monetization': 29, 'automation_robotics_industrial_ai': 29, 'energy_commodities_physical_inputs': 29, 'financing_rates_liquidity': 29, 'china_geopolitical_export_control_exposure': 29, 'end_market_demand_validation': 29, 'narrative_hype_speculation_amplification': 29}

## ecosystem balance after pruning
{'ai_compute_core': 30, 'hyperscaler_cloud_demand': 22, 'semiconductor_supply_chain': 29, 'power_grid_cooling_datacenter_infra': 21, 'memory_networking_interconnect': 29, 'ai_application_software_monetization': 21, 'automation_robotics_industrial_ai': 29, 'energy_commodities_physical_inputs': 20, 'financing_rates_liquidity': 29, 'china_geopolitical_export_control_exposure': 20, 'end_market_demand_validation': 29, 'narrative_hype_speculation_amplification': 21}

## topology quality interpretation
Selection favors multi-relationship and high-connectivity nodes to maximize interpretable ecosystem topology.

## contradiction richness interpretation
Contradiction-rich entities are prioritized directly in both scoring and tie-break ordering.

## propagation richness interpretation
Propagation-linked entities are prioritized through direct scoring and deterministic secondary rank priority.

## entities excluded summary
Excluded entities: 50. Exclusions are primarily lower-information, lower-connectivity, or monoculture-overrepresented entities.

## governance preservation review
Planning/config/report/test only. No replay execution, replay waves, persistence writes, direct SQL, predictive modeling, or trading logic introduced.

## deterministic reproducibility review
Deterministic constants and tie-break ordering ensure reproducible selections from the same source config.

## recommendation for next phase
Use the pruned universe as SDE-1D planning baseline while maintaining non-execution and non-persistence scope.
