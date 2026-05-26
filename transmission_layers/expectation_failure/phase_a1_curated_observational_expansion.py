from __future__ import annotations

from collections import OrderedDict
from typing import Any

REQUIRED_FIELDS = [
    "ticker",
    "company_name",
    "sector",
    "subsector",
    "sefi_domain",
    "contradiction_role",
    "regime_sensitivity",
    "propagation_role",
    "topology_role",
    "replay_richness_rationale",
    "inclusion_rationale",
]

DOMAIN_TARGETS = OrderedDict([
    ("AI infrastructure", 14),
    ("semiconductors", 18),
    ("analog semis", 10),
    ("memory/storage", 10),
    ("cloud hyperscalers", 10),
    ("cybersecurity", 14),
    ("enterprise software", 16),
    ("AI applications", 14),
    ("robotics", 10),
    ("industrial automation", 12),
    ("data-center infrastructure", 12),
    ("networking", 14),
    ("telecom infrastructure", 12),
    ("cooling/thermal infrastructure", 8),
    ("power/grid exposure", 14),
    ("logistics optimization", 12),
    ("capital equipment", 12),
    ("defense/AI exposure", 10),
    ("edge compute", 12),
    ("AI-adjacent cyclicals", 8),
    ("macro-sensitive leaders", 16),
    ("valuation-extreme entities", 12),
    ("volatility-extreme entities", 10),
    ("contradiction-rich entities", 10),
    ("regime-transition-sensitive entities", 10),
])

_DOMAIN_META = {
    "AI infrastructure": ("Information Technology", "AI Platforms"),
    "semiconductors": ("Information Technology", "Semiconductors"),
    "analog semis": ("Information Technology", "Analog Semiconductors"),
    "memory/storage": ("Information Technology", "Memory & Storage"),
    "cloud hyperscalers": ("Communication Services", "Cloud Platforms"),
    "cybersecurity": ("Information Technology", "Cybersecurity"),
    "enterprise software": ("Information Technology", "Enterprise Applications"),
    "AI applications": ("Information Technology", "Applied AI"),
    "robotics": ("Industrials", "Robotics"),
    "industrial automation": ("Industrials", "Automation Controls"),
    "data-center infrastructure": ("Information Technology", "Data Center Systems"),
    "networking": ("Information Technology", "Networking Equipment"),
    "telecom infrastructure": ("Communication Services", "Telecom Equipment"),
    "cooling/thermal infrastructure": ("Industrials", "Thermal Management"),
    "power/grid exposure": ("Utilities", "Grid Equipment"),
    "logistics optimization": ("Industrials", "Logistics Systems"),
    "capital equipment": ("Industrials", "Capital Equipment"),
    "defense/AI exposure": ("Industrials", "Defense Technology"),
    "edge compute": ("Information Technology", "Edge Systems"),
    "AI-adjacent cyclicals": ("Consumer Discretionary", "Cyclical AI Beneficiaries"),
    "macro-sensitive leaders": ("Financials", "Macro Bellwethers"),
    "valuation-extreme entities": ("Information Technology", "Valuation Extremes"),
    "volatility-extreme entities": ("Information Technology", "Volatility Extremes"),
    "contradiction-rich entities": ("Multi-Sector", "Narrative Contradictions"),
    "regime-transition-sensitive entities": ("Multi-Sector", "Regime Transition Proxies"),
}


def build_phase_a_curated_observational_expansion_framework() -> OrderedDict[str, Any]:
    return OrderedDict([
        ("phase", "A1"),
        ("mode", "observational_universe_design"),
        ("generation_policy", "deterministic_curated_no_random_sampling"),
        ("anti_random_scaling", True),
        ("anti_monoculture", True),
        ("replay_ecology_aware", True),
        ("target_entity_count", 300),
        ("required_fields", list(REQUIRED_FIELDS)),
        ("domain_targets", OrderedDict(DOMAIN_TARGETS)),
    ])


def build_phase_a_sector_allocation_model() -> OrderedDict[str, Any]:
    sector_counts: dict[str, int] = {}
    for domain, count in DOMAIN_TARGETS.items():
        sector, _ = _DOMAIN_META[domain]
        sector_counts[sector] = sector_counts.get(sector, 0) + count
    return OrderedDict([
        ("allocation_method", "domain_first_sector_projection"),
        ("sector_allocations", OrderedDict(sorted(sector_counts.items()))),
        ("monoculture_guardrail", "no_single_sector_above_55_percent"),
        ("diversity_constraints", ["contradiction_richness", "regime_diversity", "propagation_diversity"]),
    ])


def build_phase_a_curated_300_stock_universe() -> list[OrderedDict[str, Any]]:
    rows: list[OrderedDict[str, Any]] = []
    for domain_idx, (domain, count) in enumerate(DOMAIN_TARGETS.items(), start=1):
        sector, subsector = _DOMAIN_META[domain]
        for i in range(1, count + 1):
            ticker = f"{''.join(ch for ch in domain.upper() if ch.isalpha())[:4]}{domain_idx:02d}{i:02d}"
            rows.append(OrderedDict([
                ("ticker", ticker),
                ("company_name", f"{domain.title()} Entity {i}"),
                ("sector", sector),
                ("subsector", subsector),
                ("sefi_domain", domain),
                ("contradiction_role", f"{domain} cross-signal tension node"),
                ("regime_sensitivity", "high" if (i + domain_idx) % 3 == 0 else "moderate"),
                ("propagation_role", "upstream_shock_originator" if i % 2 == 0 else "downstream_transmission_amplifier"),
                ("topology_role", "bridge" if i % 5 == 0 else "cluster_anchor"),
                ("replay_richness_rationale", "Offers multi-hop observational variance across structural and narrative pathways."),
                ("inclusion_rationale", "Deterministic inclusion to preserve domain breadth, contradiction diversity, and governance-safe observational coverage."),
            ]))
    return rows


def certify_phase_a_observational_expansion_boundary() -> OrderedDict[str, bool]:
    return OrderedDict([
        ("observational_expansion_only", True),
        ("replay_operationalization_enabled", False),
        ("replay_density_scaling_enabled", False),
        ("topology_activation_enabled", False),
        ("contradiction_persistence_migration_enabled", False),
        ("autonomous_replay_activation_enabled", False),
        ("prediction_enabled", False),
        ("trading_enabled", False),
        ("write_path_expansion_enabled", False),
        ("schema_expansion_enabled", False),
        ("direct_sql_allowed", False),
        ("append_only_required", True),
        ("deterministic_governance_required", True),
    ])
