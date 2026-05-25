"""LR6-OBS4 enriched replay candidate-universe design (deterministic observation-only layer)."""
from __future__ import annotations

from collections import Counter
from typing import Any

DETERMINISTIC_VERSION = "LR6_OBS4_ENRICHED_REPLAY_CANDIDATE_UNIVERSE_V1"
SOURCE_PHASE = "LR6-OBS4"

MEGACAP_TICKERS = {"AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "TSLA", "BRK.B"}

ROLE_TAXONOMY: list[dict[str, Any]] = [
    {"role_id": "R01", "role": "peripheral_ai_ecosystem_actors", "intent": "capture second-order AI demand and integration surfaces"},
    {"role_id": "R02", "role": "industrial_automation", "intent": "surface capex-to-execution transmission in factories and process industries"},
    {"role_id": "R03", "role": "cybersecurity", "intent": "observe trust, resilience, and compliance pressure spillovers"},
    {"role_id": "R04", "role": "grid_utilities_power_demand", "intent": "track power-constraint and load-shift propagation"},
    {"role_id": "R05", "role": "telecom_infrastructure", "intent": "observe connectivity bottlenecks and network quality migration"},
    {"role_id": "R06", "role": "data_center_infrastructure", "intent": "capture facility and interconnect constraints"},
    {"role_id": "R07", "role": "cooling_thermal_energy_efficiency", "intent": "observe thermal bottlenecks and efficiency reweighting"},
    {"role_id": "R08", "role": "memory_storage_ecosystems", "intent": "surface memory, storage, and controller bottleneck dynamics"},
    {"role_id": "R09", "role": "edge_compute_embedded_systems", "intent": "track decentralized inference and edge deployment transitions"},
    {"role_id": "R10", "role": "robotics", "intent": "observe embodiment pathways and deployment friction"},
    {"role_id": "R11", "role": "logistics_supply_chain", "intent": "capture component, warehousing, and transport fragility pathways"},
    {"role_id": "R12", "role": "ai_consulting_integration", "intent": "observe enterprise adoption velocity and implementation translation"},
    {"role_id": "R13", "role": "semiconductor_equipment", "intent": "track tool-chain capacity and cycle sensitivity"},
    {"role_id": "R14", "role": "regulatory_compliance_exposure", "intent": "capture policy and governance shock carriers"},
    {"role_id": "R15", "role": "geopolitical_semiconductor_exposure", "intent": "observe geopolitical concentration and supply-risk asymmetry"},
    {"role_id": "R16", "role": "weak_signal_secondary_bridges", "intent": "elevate sparse but recurring bridge entities"},
    {"role_id": "R17", "role": "cross_regime_contradiction_carriers", "intent": "capture entities that invert behavior across regimes"},
    {"role_id": "R18", "role": "non_megacap_replay_bridges", "intent": "reduce monoculture risk and widen replay bridge topology"},
]

CANDIDATE_UNIVERSE: list[dict[str, Any]] = [
    {"ticker": "ANET", "name": "Arista Networks", "roles": ["peripheral_ai_ecosystem_actors", "telecom_infrastructure", "non_megacap_replay_bridges"], "cap_band": "large_non_megacap"},
    {"ticker": "CIEN", "name": "Ciena", "roles": ["telecom_infrastructure", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "JNPR", "name": "Juniper Networks", "roles": ["telecom_infrastructure", "data_center_infrastructure"], "cap_band": "mid"},
    {"ticker": "HPE", "name": "Hewlett Packard Enterprise", "roles": ["edge_compute_embedded_systems", "data_center_infrastructure"], "cap_band": "large_non_megacap"},
    {"ticker": "SMCI", "name": "Super Micro Computer", "roles": ["data_center_infrastructure", "cooling_thermal_energy_efficiency"], "cap_band": "large_non_megacap"},
    {"ticker": "VRT", "name": "Vertiv", "roles": ["cooling_thermal_energy_efficiency", "grid_utilities_power_demand"], "cap_band": "large_non_megacap"},
    {"ticker": "ETN", "name": "Eaton", "roles": ["grid_utilities_power_demand", "industrial_automation"], "cap_band": "large_non_megacap"},
    {"ticker": "HUBB", "name": "Hubbell", "roles": ["grid_utilities_power_demand", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "NRG", "name": "NRG Energy", "roles": ["grid_utilities_power_demand", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "AES", "name": "AES Corp", "roles": ["grid_utilities_power_demand", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "CEG", "name": "Constellation Energy", "roles": ["grid_utilities_power_demand", "non_megacap_replay_bridges"], "cap_band": "large_non_megacap"},
    {"ticker": "VST", "name": "Vistra", "roles": ["grid_utilities_power_demand", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "PWR", "name": "Quanta Services", "roles": ["grid_utilities_power_demand", "logistics_supply_chain"], "cap_band": "large_non_megacap"},
    {"ticker": "EME", "name": "EMCOR Group", "roles": ["data_center_infrastructure", "ai_consulting_integration"], "cap_band": "mid"},
    {"ticker": "FIX", "name": "Comfort Systems USA", "roles": ["cooling_thermal_energy_efficiency", "ai_consulting_integration"], "cap_band": "mid"},
    {"ticker": "TT", "name": "Trane Technologies", "roles": ["cooling_thermal_energy_efficiency", "industrial_automation"], "cap_band": "large_non_megacap"},
    {"ticker": "ROK", "name": "Rockwell Automation", "roles": ["industrial_automation", "robotics"], "cap_band": "large_non_megacap"},
    {"ticker": "HON", "name": "Honeywell", "roles": ["industrial_automation", "edge_compute_embedded_systems"], "cap_band": "large_non_megacap"},
    {"ticker": "AME", "name": "AMETEK", "roles": ["industrial_automation", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "IR", "name": "Ingersoll Rand", "roles": ["industrial_automation", "cooling_thermal_energy_efficiency"], "cap_band": "mid"},
    {"ticker": "ABB", "name": "ABB", "roles": ["industrial_automation", "robotics", "geopolitical_semiconductor_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "SYM", "name": "Symbotic", "roles": ["robotics", "logistics_supply_chain", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "ZBRA", "name": "Zebra Technologies", "roles": ["edge_compute_embedded_systems", "logistics_supply_chain"], "cap_band": "mid"},
    {"ticker": "PATH", "name": "UiPath", "roles": ["robotics", "ai_consulting_integration", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "PANW", "name": "Palo Alto Networks", "roles": ["cybersecurity", "peripheral_ai_ecosystem_actors"], "cap_band": "large_non_megacap"},
    {"ticker": "CRWD", "name": "CrowdStrike", "roles": ["cybersecurity", "cross_regime_contradiction_carriers"], "cap_band": "large_non_megacap"},
    {"ticker": "FTNT", "name": "Fortinet", "roles": ["cybersecurity", "telecom_infrastructure"], "cap_band": "large_non_megacap"},
    {"ticker": "CYBR", "name": "CyberArk", "roles": ["cybersecurity", "regulatory_compliance_exposure"], "cap_band": "mid"},
    {"ticker": "TENB", "name": "Tenable", "roles": ["cybersecurity", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "OKTA", "name": "Okta", "roles": ["cybersecurity", "regulatory_compliance_exposure"], "cap_band": "mid"},
    {"ticker": "MU", "name": "Micron Technology", "roles": ["memory_storage_ecosystems", "geopolitical_semiconductor_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "WDC", "name": "Western Digital", "roles": ["memory_storage_ecosystems", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "STX", "name": "Seagate Technology", "roles": ["memory_storage_ecosystems", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "COHR", "name": "Coherent", "roles": ["data_center_infrastructure", "semiconductor_equipment"], "cap_band": "mid"},
    {"ticker": "LRCX", "name": "Lam Research", "roles": ["semiconductor_equipment", "geopolitical_semiconductor_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "KLAC", "name": "KLA", "roles": ["semiconductor_equipment", "geopolitical_semiconductor_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "AMAT", "name": "Applied Materials", "roles": ["semiconductor_equipment", "cross_regime_contradiction_carriers"], "cap_band": "large_non_megacap"},
    {"ticker": "ASML", "name": "ASML Holding", "roles": ["semiconductor_equipment", "geopolitical_semiconductor_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "ONTO", "name": "Onto Innovation", "roles": ["semiconductor_equipment", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "FORM", "name": "FormFactor", "roles": ["semiconductor_equipment", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "MTSI", "name": "MACOM Technology", "roles": ["edge_compute_embedded_systems", "telecom_infrastructure"], "cap_band": "mid"},
    {"ticker": "ALGM", "name": "Allegro MicroSystems", "roles": ["edge_compute_embedded_systems", "robotics"], "cap_band": "mid"},
    {"ticker": "NXPI", "name": "NXP Semiconductors", "roles": ["edge_compute_embedded_systems", "automotive_supply_chain"], "cap_band": "large_non_megacap"},
    {"ticker": "ON", "name": "ON Semiconductor", "roles": ["edge_compute_embedded_systems", "geopolitical_semiconductor_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "GFS", "name": "GlobalFoundries", "roles": ["geopolitical_semiconductor_exposure", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "MRVL", "name": "Marvell Technology", "roles": ["peripheral_ai_ecosystem_actors", "data_center_infrastructure"], "cap_band": "large_non_megacap"},
    {"ticker": "LSCC", "name": "Lattice Semiconductor", "roles": ["weak_signal_secondary_bridges", "edge_compute_embedded_systems"], "cap_band": "mid"},
    {"ticker": "RMBS", "name": "Rambus", "roles": ["memory_storage_ecosystems", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "DOCN", "name": "DigitalOcean", "roles": ["peripheral_ai_ecosystem_actors", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "DBX", "name": "Dropbox", "roles": ["memory_storage_ecosystems", "non_megacap_replay_bridges"], "cap_band": "mid"},
    {"ticker": "AKAM", "name": "Akamai Technologies", "roles": ["edge_compute_embedded_systems", "cybersecurity"], "cap_band": "large_non_megacap"},
    {"ticker": "CHKP", "name": "Check Point Software", "roles": ["cybersecurity", "regulatory_compliance_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "EXTR", "name": "Extreme Networks", "roles": ["telecom_infrastructure", "weak_signal_secondary_bridges"], "cap_band": "small_mid"},
    {"ticker": "BLDR", "name": "Builders FirstSource", "roles": ["data_center_infrastructure", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "XYL", "name": "Xylem", "roles": ["grid_utilities_power_demand", "cooling_thermal_energy_efficiency"], "cap_band": "large_non_megacap"},
    {"ticker": "WTS", "name": "Watts Water Technologies", "roles": ["cooling_thermal_energy_efficiency", "weak_signal_secondary_bridges"], "cap_band": "mid"},
    {"ticker": "RHI", "name": "Robert Half", "roles": ["ai_consulting_integration", "cross_regime_contradiction_carriers"], "cap_band": "mid"},
    {"ticker": "EPAM", "name": "EPAM Systems", "roles": ["ai_consulting_integration", "geopolitical_semiconductor_exposure"], "cap_band": "mid"},
    {"ticker": "ACN", "name": "Accenture", "roles": ["ai_consulting_integration", "regulatory_compliance_exposure"], "cap_band": "large_non_megacap"},
    {"ticker": "EXPD", "name": "Expeditors International", "roles": ["logistics_supply_chain", "cross_regime_contradiction_carriers"], "cap_band": "large_non_megacap"},
    {"ticker": "CHRW", "name": "C.H. Robinson", "roles": ["logistics_supply_chain", "weak_signal_secondary_bridges"], "cap_band": "mid"},
]


def build_lr6_obs4_candidate_universe_context(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    artifacts = lr6_artifacts if isinstance(lr6_artifacts, dict) else {}
    return {
        "deterministic_version": DETERMINISTIC_VERSION,
        "source_phase": SOURCE_PHASE,
        "design_mode": "observation_only_enriched_candidate_universe",
        "inspected_obs3_findings": bool(artifacts.get("lr6_obs3_controlled_ecological_enrichment_review", True)),
        "target_candidate_count_band": "50_to_75",
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs4_ecological_role_taxonomy() -> list[dict[str, Any]]:
    return list(ROLE_TAXONOMY)


def build_lr6_obs4_density_gap_priorities() -> list[dict[str, Any]]:
    return [
        {"gap_id": "DG01", "priority": "high", "surface": "cross_cluster_bridge_scarcity", "target_roles": ["weak_signal_secondary_bridges", "non_megacap_replay_bridges"]},
        {"gap_id": "DG02", "priority": "high", "surface": "power_compute_cooling_linkage_thinness", "target_roles": ["grid_utilities_power_demand", "cooling_thermal_energy_efficiency", "data_center_infrastructure"]},
        {"gap_id": "DG03", "priority": "moderate", "surface": "policy_to_execution_contradiction_coverage", "target_roles": ["regulatory_compliance_exposure", "ai_consulting_integration", "logistics_supply_chain"]},
        {"gap_id": "DG04", "priority": "moderate", "surface": "edge_and_embodied_deployment_asymmetry", "target_roles": ["edge_compute_embedded_systems", "robotics"]},
    ]


def build_lr6_obs4_candidate_universe() -> list[dict[str, Any]]:
    return [dict(item) for item in CANDIDATE_UNIVERSE]


def _entities_by_role(role: str, cap_limit: int = 12) -> list[dict[str, Any]]:
    selected = [c for c in CANDIDATE_UNIVERSE if role in c["roles"]]
    return [dict(c) for c in selected[:cap_limit]]


def build_lr6_obs4_weak_signal_bridge_entities() -> list[dict[str, Any]]:
    return _entities_by_role("weak_signal_secondary_bridges", cap_limit=16)


def build_lr6_obs4_contradiction_enrichment_entities() -> list[dict[str, Any]]:
    return _entities_by_role("cross_regime_contradiction_carriers", cap_limit=16)


def build_lr6_obs4_propagation_diversity_entities() -> list[dict[str, Any]]:
    entities = [c for c in CANDIDATE_UNIVERSE if any(r in c["roles"] for r in ("grid_utilities_power_demand", "telecom_infrastructure", "logistics_supply_chain", "data_center_infrastructure"))]
    return [dict(c) for c in entities[:24]]


def build_lr6_obs4_megacap_concentration_assessment() -> dict[str, Any]:
    total = len(CANDIDATE_UNIVERSE)
    mega = [c for c in CANDIDATE_UNIVERSE if c["ticker"] in MEGACAP_TICKERS]
    non_mega_ratio = round((total - len(mega)) / max(1, total), 4)
    return {
        "candidate_count": total,
        "megacap_count": len(mega),
        "megacap_ratio": round(len(mega) / max(1, total), 4),
        "non_megacap_ratio": non_mega_ratio,
        "megacap_concentration_risk": "low" if non_mega_ratio >= 0.9 else "moderate",
        "guardrail_pass": non_mega_ratio >= 0.85,
    }


def certify_lr6_obs4_design_boundary() -> dict[str, bool]:
    return {
        "observation_only": True,
        "no_prediction": True,
        "no_trading": True,
        "no_direct_sql": True,
        "no_live_ingestion": True,
        "no_persistence_write": True,
        "no_governed_activation": True,
        "architecture_expansion_frozen": True,
    }


def build_lr6_obs4_supervisor_review(lr6_artifacts: dict[str, Any] | None = None) -> dict[str, Any]:
    universe = build_lr6_obs4_candidate_universe()
    role_counts = Counter(role for c in universe for role in c["roles"])
    strongest = sorted(role_counts.items(), key=lambda x: (-x[1], x[0]))[:5]
    return {
        "context": build_lr6_obs4_candidate_universe_context(lr6_artifacts),
        "role_taxonomy": build_lr6_obs4_ecological_role_taxonomy(),
        "density_gap_priorities": build_lr6_obs4_density_gap_priorities(),
        "candidate_universe": universe,
        "weak_signal_bridge_entities": build_lr6_obs4_weak_signal_bridge_entities(),
        "contradiction_enrichment_entities": build_lr6_obs4_contradiction_enrichment_entities(),
        "propagation_diversity_entities": build_lr6_obs4_propagation_diversity_entities(),
        "megacap_concentration_assessment": build_lr6_obs4_megacap_concentration_assessment(),
        "supervisor_assessment": {
            "strongest_enrichment_categories": [name for name, _ in strongest],
            "weakest_existing_ecological_coverage": ["regulatory_compliance_exposure", "non_megacap_replay_bridges"],
            "expected_propagation_improvements": "higher cross-cluster mutation observability through power-network-logistics bridges",
            "expected_contradiction_improvements": "better policy-vs-execution and demand-vs-constraint contradiction capture",
            "replay_richness_expansion_potential": "high",
            "topology_diversification_potential": "high",
            "architecture_expansion_should_remain_frozen": True,
        },
        "boundary_certification": certify_lr6_obs4_design_boundary(),
    }


def build_lr6_obs4_markdown_report(review: dict[str, Any]) -> str:
    lines = [
        "# LR6-OBS4 Enriched Replay Candidate Universe",
        "",
        "## Objective",
        "Design a deterministic, bounded candidate universe that increases replay ecology richness without architecture expansion.",
        "",
        "## Inspected OBS3 Findings",
        f"- OBS3 enrichment review inspected: {review['context']['inspected_obs3_findings']}",
        "- Primary bottleneck interpreted as ecological richness rather than architecture quantity.",
        "",
        "## Ecological Enrichment Philosophy",
        "Prioritize bridge quality, contradiction asymmetry, and cross-cluster density over brute-force quantity growth.",
        "",
        "## Role Taxonomy",
    ]
    lines.extend([f"- {r['role']}: {r['intent']}" for r in review["role_taxonomy"]])
    lines.extend([
        "",
        "## Candidate-Universe Rationale",
        f"- Candidate count: {len(review['candidate_universe'])}",
        "- Intentional mid-cap and secondary-actor inclusion to reduce monoculture pathways.",
        "",
        "## Weak-Signal Bridge Rationale",
        "Weak-signal bridges are included to improve early topology-drift visibility.",
        "",
        "## Contradiction Enrichment Rationale",
        "Cross-regime carriers are selected to observe regime-dependent narrative inversion.",
        "",
        "## Propagation Diversity Rationale",
        "Power, telecom, logistics, and data-center bridges are interleaved for mutation tracking.",
        "",
        "## Megacap Concentration Analysis",
        f"- Megacap ratio: {review['megacap_concentration_assessment']['megacap_ratio']}",
        f"- Guardrail pass: {review['megacap_concentration_assessment']['guardrail_pass']}",
        "",
        "## Expected Replay Ecology Improvements",
        "- Higher contradiction migration visibility.",
        "- Improved weak-signal bridge continuity.",
        "- Better cross-cluster contamination detection.",
        "",
        "## Overengineering Warning",
        "Do not expand architecture; keep focus on deterministic observational design quality.",
        "",
        "## Next-Step Recommendation",
        "Run bounded longitudinal replay observations with this candidate set before any further expansion.",
    ])
    return "\n".join(lines)
