from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Optional
from datetime import date


ALLOWED_NODE_TYPES = {
    "theme",
    "asset",
    "sector",
    "subsector",
    "macro_factor",
    "commodity",
    "supply_chain",
    "economic_actor",
    "risk_factor",
    "policy_factor",
    "other",
}

ALLOWED_EDGE_TYPES = {
    "influences",
    "benefits",
    "harms",
    "accelerates",
    "suppresses",
    "dependent_on",
    "correlated_with",
    "transmits_to",
    "exposes_to",
    "supplies",
    "consumes",
    "funds",
    "regulates",
    "other",
}


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, float(value)))


def make_node_key(node_type: str, label: str) -> str:
    cleaned = (
        label.strip()
        .lower()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("&", "and")
        .replace("-", "_")
    )
    return f"{node_type}:{cleaned}"


def make_edge_key(source_node_key: str, edge_type: str, target_node_key: str) -> str:
    return f"{source_node_key}|{edge_type}|{target_node_key}"


@dataclass
class GraphNode:
    node_key: str
    node_type: str
    node_label: str
    theme_name: Optional[str] = None
    entity: Optional[str] = None
    sector: Optional[str] = None
    subsector: Optional[str] = None
    asset_class: Optional[str] = None
    node_metadata: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True
    first_seen_run_date_sgt: Optional[str] = None
    last_seen_run_date_sgt: Optional[str] = None

    def to_row(self) -> Dict[str, Any]:
        if self.node_type not in ALLOWED_NODE_TYPES:
            raise ValueError(f"Invalid node_type: {self.node_type}")

        row = asdict(self)
        row = {k: v for k, v in row.items() if v is not None}
        return row


@dataclass
class GraphEdge:
    edge_key: str
    source_node_key: str
    target_node_key: str
    source_node_type: str
    target_node_type: str
    edge_type: str
    direction: str = "directed"
    theme_name: Optional[str] = None
    anchor_theme_name: Optional[str] = "ai"

    edge_strength: float = 0.0
    directional_strength: float = 0.0
    confidence_score: float = 0.0
    evidence_intensity: float = 0.0
    persistence_score: float = 0.0

    evidence_count: int = 0
    positive_evidence_count: int = 0
    negative_evidence_count: int = 0
    neutral_evidence_count: int = 0

    first_seen_run_date_sgt: Optional[str] = None
    last_seen_run_date_sgt: Optional[str] = None

    edge_metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_summary: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

    def to_row(self) -> Dict[str, Any]:
        if self.edge_type not in ALLOWED_EDGE_TYPES:
            raise ValueError(f"Invalid edge_type: {self.edge_type}")

        self.edge_strength = clamp(self.edge_strength, 0, 1)
        self.directional_strength = clamp(self.directional_strength, -1, 1)
        self.confidence_score = clamp(self.confidence_score, 0, 1)
        self.evidence_intensity = clamp(self.evidence_intensity, 0, 1)
        self.persistence_score = clamp(self.persistence_score, 0, 1)

        row = asdict(self)
        row = {k: v for k, v in row.items() if v is not None}
        return row
