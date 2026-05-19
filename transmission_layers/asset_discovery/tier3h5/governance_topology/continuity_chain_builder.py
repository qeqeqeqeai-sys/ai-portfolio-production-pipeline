from __future__ import annotations


CHAIN_CATEGORIES = (
    "orchestration",
    "monitoring",
    "history",
    "reporting",
    "auditability",
    "control_plane_state",
    "invariant_preservation",
)


def build_continuity_chains() -> dict[str, object]:
    chains = [
        {
            "chain_id": f"chain_{name}",
            "category": name,
            "path": ["phase5a", "phase5b", "phase5c", "phase5d", "phase5e", "phase5f", "phase5g"],
            "match_mode": "exact_key",
            "advisory_only": True,
        }
        for name in CHAIN_CATEGORIES
    ]
    return {
        "continuity_chain_status": "generated",
        "continuity_chains": chains,
        "continuity_chains_generated": len(chains),
    }
