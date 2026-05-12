from typing import Dict, Any
from .graph_models import clamp


def score_edge(
    evidence_count: int,
    positive_evidence_count: int = 0,
    negative_evidence_count: int = 0,
    neutral_evidence_count: int = 0,
    observed_days: int = 1,
    active_days: int = 1,
    base_confidence: float = 0.50,
    manual_prior_strength: float = 0.50,
    direction_sign: int = 1,
) -> Dict[str, float]:
    """
    Infrastructure-level scoring only.
    No graph analytics. No propagation. No centrality.

    edge_strength:
        Generic strength estimate from evidence intensity, confidence, and persistence.

    directional_strength:
        Signed strength in [-1, 1].
        Positive direction means source supports/benefits/accelerates target.
        Negative direction means source harms/suppresses target.
    """

    evidence_count = max(0, int(evidence_count))
    positive_evidence_count = max(0, int(positive_evidence_count))
    negative_evidence_count = max(0, int(negative_evidence_count))
    neutral_evidence_count = max(0, int(neutral_evidence_count))

    observed_days = max(1, int(observed_days))
    active_days = max(0, int(active_days))

    # Saturating evidence intensity. 10+ evidence items approaches high intensity.
    evidence_intensity = clamp(evidence_count / 10.0, 0, 1)

    # Persistence is how often this relationship appears within available observation windows.
    persistence_score = clamp(active_days / observed_days, 0, 1)

    # Directional balance. Neutral evidence does not move sign.
    directional_balance = 0.0
    directional_denominator = positive_evidence_count + negative_evidence_count
    if directional_denominator > 0:
        directional_balance = (
            positive_evidence_count - negative_evidence_count
        ) / directional_denominator

    confidence_score = clamp(
        0.45 * base_confidence
        + 0.35 * evidence_intensity
        + 0.20 * persistence_score,
        0,
        1,
    )

    edge_strength = clamp(
        0.40 * manual_prior_strength
        + 0.30 * evidence_intensity
        + 0.20 * confidence_score
        + 0.10 * persistence_score,
        0,
        1,
    )

    signed_direction = 1 if direction_sign >= 0 else -1
    directional_strength = clamp(
        signed_direction * edge_strength * max(abs(directional_balance), 0.50),
        -1,
        1,
    )

    return {
        "edge_strength": round(edge_strength, 6),
        "directional_strength": round(directional_strength, 6),
        "confidence_score": round(confidence_score, 6),
        "evidence_intensity": round(evidence_intensity, 6),
        "persistence_score": round(persistence_score, 6),
    }
