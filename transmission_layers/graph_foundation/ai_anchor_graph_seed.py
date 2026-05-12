from typing import List, Tuple
from .graph_models import GraphNode, GraphEdge, make_node_key, make_edge_key
from .edge_scoring import score_edge


AI_ANCHOR_THEME_NAME = "ai"


AI_ANCHOR_RELATIONSHIPS: List[Tuple[str, str, str, str, str, int, float]] = [
    ("AI", "theme", "semiconductors", "sector", "benefits", 1, 0.85),
    ("AI", "theme", "hyperscalers", "subsector", "benefits", 1, 0.80),
    ("AI", "theme", "data centers", "subsector", "accelerates", 1, 0.85),
    ("AI", "theme", "utilities", "sector", "influences", 1, 0.65),
    ("AI", "theme", "power demand", "macro_factor", "accelerates", 1, 0.85),
    ("AI", "theme", "copper", "commodity", "influences", 1, 0.60),
    ("AI", "theme", "enterprise software", "sector", "benefits", 1, 0.70),
    ("AI", "theme", "cybersecurity", "sector", "benefits", 1, 0.70),
    ("AI", "theme", "labor disruption", "risk_factor", "accelerates", 1, 0.75),
    ("AI", "theme", "productivity beneficiaries", "economic_actor", "benefits", 1, 0.70),
    ("AI", "theme", "AI infrastructure suppliers", "supply_chain", "benefits", 1, 0.85),
]


def build_ai_anchor_seed(run_date_sgt: str):
    """
    Creates AI anchor graph seed nodes and edges.
    This is the first graph foundation pass only.
    """

    nodes_by_key = {}
    edges = []

    for source_label, source_type, target_label, target_type, edge_type, direction_sign, prior_strength in AI_ANCHOR_RELATIONSHIPS:
        source_key = make_node_key(source_type, source_label)
        target_key = make_node_key(target_type, target_label)

        nodes_by_key[source_key] = GraphNode(
            node_key=source_key,
            node_type=source_type,
            node_label=source_label,
            theme_name=AI_ANCHOR_THEME_NAME if source_type == "theme" else None,
            node_metadata={
                "anchor_role": "source_theme" if source_type == "theme" else "related_node",
                "pass": "PASS_1_GENERIC_GRAPH_FOUNDATION",
            },
            first_seen_run_date_sgt=run_date_sgt,
            last_seen_run_date_sgt=run_date_sgt,
        )

        nodes_by_key[target_key] = GraphNode(
            node_key=target_key,
            node_type=target_type,
            node_label=target_label,
            theme_name=AI_ANCHOR_THEME_NAME,
            sector=target_label if target_type == "sector" else None,
            subsector=target_label if target_type == "subsector" else None,
            asset_class="commodity" if target_type == "commodity" else None,
            node_metadata={
                "anchor_theme": AI_ANCHOR_THEME_NAME,
                "pass": "PASS_1_GENERIC_GRAPH_FOUNDATION",
            },
            first_seen_run_date_sgt=run_date_sgt,
            last_seen_run_date_sgt=run_date_sgt,
        )

        score = score_edge(
            evidence_count=1,
            positive_evidence_count=1 if direction_sign > 0 else 0,
            negative_evidence_count=1 if direction_sign < 0 else 0,
            neutral_evidence_count=0,
            observed_days=1,
            active_days=1,
            base_confidence=0.55,
            manual_prior_strength=prior_strength,
            direction_sign=direction_sign,
        )

        edge_key = make_edge_key(source_key, edge_type, target_key)

        edges.append(
            GraphEdge(
                edge_key=edge_key,
                source_node_key=source_key,
                target_node_key=target_key,
                source_node_type=source_type,
                target_node_type=target_type,
                edge_type=edge_type,
                theme_name=AI_ANCHOR_THEME_NAME,
                anchor_theme_name=AI_ANCHOR_THEME_NAME,
                evidence_count=1,
                positive_evidence_count=1 if direction_sign > 0 else 0,
                negative_evidence_count=1 if direction_sign < 0 else 0,
                neutral_evidence_count=0,
                first_seen_run_date_sgt=run_date_sgt,
                last_seen_run_date_sgt=run_date_sgt,
                edge_metadata={
                    "seeded_by": "ai_anchor_graph_seed",
                    "manual_prior_strength": prior_strength,
                    "pass": "PASS_1_GENERIC_GRAPH_FOUNDATION",
                },
                evidence_summary={
                    "summary": "Initial AI anchor relationship seed. Replace or augment with evidence-backed relationships in later passes.",
                    "source": "manual_architecture_seed",
                },
                **score,
            )
        )

    return list(nodes_by_key.values()), edges
