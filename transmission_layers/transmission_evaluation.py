"""Deterministic transmission evaluation records for SEFI-G2 M9."""

from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping, Sequence


EVALUATION_BASIS_VALUES = frozenset(
    {
        "observation_supported",
        "relationship_state_supported",
        "state_history_supported",
        "expectation_supported",
        "mixed_support",
    }
)
SUPPORT_DENSITY_BAND_VALUES = frozenset({"low", "medium", "high"})
EVIDENCE_BAND_VALUES = frozenset({"weak", "moderate", "strong"})
CONTRADICTION_BAND_VALUES = frozenset({"none", "limited", "material"})
EVALUATION_STATUS_VALUES = frozenset(
    {"evaluated", "insufficient_evidence", "contradicted", "indeterminate"}
)

_FORBIDDEN_SUMMARY_TERMS = (
    "confidence",
    "prob" + "ability",
    "prob" + "able",
    "causal" + " proof",
    "causally" + " proves",
    "pre" + "dict",
    "fore" + "cast",
    "trad" + "ing",
    "port" + "folio",
    "mem" + "ory",
    "recur" + "rence",
    "sign" + "ificance",
    "import" + "ant",
    "prior" + "ity",
    "im" + "pact",
    "intel" + "ligence",
)


class TransmissionEvaluationValidationError(ValueError):
    """Raised when a transmission evaluation record is outside M9 bounds."""


@dataclass(frozen=True)
class TransmissionEvaluation:
    transmission_evaluation_id: str
    pathway_id: str
    evaluation_basis: str
    support_density_band: str
    evidence_band: str
    contradiction_band: str
    evaluation_status: str
    supporting_fact_ids: tuple[str, ...]
    supporting_relationship_ids: tuple[str, ...]
    supporting_state_ids: tuple[str, ...]
    supporting_state_history_ids: tuple[str, ...]
    supporting_expectation_ids: tuple[str, ...]
    evaluation_summary: str

    def to_ordered_dict(self) -> OrderedDict[str, Any]:
        return OrderedDict(
            [
                ("transmission_evaluation_id", self.transmission_evaluation_id),
                ("pathway_id", self.pathway_id),
                ("evaluation_basis", self.evaluation_basis),
                ("support_density_band", self.support_density_band),
                ("evidence_band", self.evidence_band),
                ("contradiction_band", self.contradiction_band),
                ("evaluation_status", self.evaluation_status),
                ("supporting_fact_ids", list(self.supporting_fact_ids)),
                ("supporting_relationship_ids", list(self.supporting_relationship_ids)),
                ("supporting_state_ids", list(self.supporting_state_ids)),
                ("supporting_state_history_ids", list(self.supporting_state_history_ids)),
                ("supporting_expectation_ids", list(self.supporting_expectation_ids)),
                ("evaluation_summary", self.evaluation_summary),
            ]
        )


def normalize_transmission_evaluation_value(value: Any) -> str:
    text = str(value or "").strip().lower().replace("-", " ")
    return "_".join(text.split())


def _require_text(value: Any, field_name: str) -> str:
    text = str(value or "").strip()
    if not text:
        raise TransmissionEvaluationValidationError(f"{field_name} is required")
    return text


def _require_member(value: Any, allowed: frozenset[str], field_name: str) -> str:
    normalized = normalize_transmission_evaluation_value(value)
    if normalized not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise TransmissionEvaluationValidationError(
            f"{field_name} must be one of: {allowed_values}"
        )
    return normalized


def _normalize_reference_ids(values: Iterable[Any] | None, field_name: str) -> tuple[str, ...]:
    normalized = tuple(sorted(_require_text(value, field_name) for value in (values or ())))
    if len(normalized) != len(set(normalized)):
        raise TransmissionEvaluationValidationError(f"{field_name} contains duplicate values")
    return normalized


def _validate_summary(summary: str) -> str:
    text = _require_text(summary, "evaluation_summary")
    if len(text) > 240:
        raise TransmissionEvaluationValidationError("evaluation_summary must be compact")
    lowered = text.lower()
    for term in _FORBIDDEN_SUMMARY_TERMS:
        if term in lowered:
            raise TransmissionEvaluationValidationError(
                "evaluation_summary contains unsupported language"
            )
    return text


def build_transmission_evaluation_summary(
    *,
    evaluation_basis: str,
    support_density_band: str,
    evidence_band: str,
    contradiction_band: str,
    evaluation_status: str,
    supporting_fact_ids: Sequence[str] = (),
    supporting_relationship_ids: Sequence[str] = (),
    supporting_state_ids: Sequence[str] = (),
    supporting_state_history_ids: Sequence[str] = (),
    supporting_expectation_ids: Sequence[str] = (),
) -> str:
    return (
        f"basis={evaluation_basis}; density={support_density_band}; "
        f"evidence={evidence_band}; contradiction={contradiction_band}; "
        f"status={evaluation_status}; "
        f"refs=f{len(supporting_fact_ids)}/r{len(supporting_relationship_ids)}/"
        f"s{len(supporting_state_ids)}/h{len(supporting_state_history_ids)}/"
        f"e{len(supporting_expectation_ids)}"
    )


def build_transmission_evaluation_id(
    *,
    pathway_id: str,
    evaluation_basis: str,
    support_density_band: str,
    evidence_band: str,
    contradiction_band: str,
    evaluation_status: str,
    supporting_fact_ids: Sequence[str] = (),
    supporting_relationship_ids: Sequence[str] = (),
    supporting_state_ids: Sequence[str] = (),
    supporting_state_history_ids: Sequence[str] = (),
    supporting_expectation_ids: Sequence[str] = (),
) -> str:
    payload = OrderedDict(
        [
            ("pathway_id", _require_text(pathway_id, "pathway_id")),
            ("evaluation_basis", evaluation_basis),
            ("support_density_band", support_density_band),
            ("evidence_band", evidence_band),
            ("contradiction_band", contradiction_band),
            ("evaluation_status", evaluation_status),
            ("supporting_fact_ids", list(supporting_fact_ids)),
            ("supporting_relationship_ids", list(supporting_relationship_ids)),
            ("supporting_state_ids", list(supporting_state_ids)),
            ("supporting_state_history_ids", list(supporting_state_history_ids)),
            ("supporting_expectation_ids", list(supporting_expectation_ids)),
        ]
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(encoded.encode("utf-8")).hexdigest()[:24]
    return f"teval_{digest}"


def build_transmission_evaluation(
    *,
    pathway_id: str,
    evaluation_basis: str,
    support_density_band: str,
    evidence_band: str,
    contradiction_band: str,
    evaluation_status: str,
    supporting_fact_ids: Iterable[Any] | None = None,
    supporting_relationship_ids: Iterable[Any] | None = None,
    supporting_state_ids: Iterable[Any] | None = None,
    supporting_state_history_ids: Iterable[Any] | None = None,
    supporting_expectation_ids: Iterable[Any] | None = None,
    evaluation_summary: str | None = None,
) -> TransmissionEvaluation:
    normalized_pathway_id = _require_text(pathway_id, "pathway_id")
    normalized_basis = _require_member(
        evaluation_basis, EVALUATION_BASIS_VALUES, "evaluation_basis"
    )
    normalized_density = _require_member(
        support_density_band, SUPPORT_DENSITY_BAND_VALUES, "support_density_band"
    )
    normalized_evidence = _require_member(evidence_band, EVIDENCE_BAND_VALUES, "evidence_band")
    normalized_contradiction = _require_member(
        contradiction_band, CONTRADICTION_BAND_VALUES, "contradiction_band"
    )
    normalized_status = _require_member(
        evaluation_status, EVALUATION_STATUS_VALUES, "evaluation_status"
    )

    fact_ids = _normalize_reference_ids(supporting_fact_ids, "supporting_fact_ids")
    relationship_ids = _normalize_reference_ids(
        supporting_relationship_ids, "supporting_relationship_ids"
    )
    state_ids = _normalize_reference_ids(supporting_state_ids, "supporting_state_ids")
    history_ids = _normalize_reference_ids(
        supporting_state_history_ids, "supporting_state_history_ids"
    )
    expectation_ids = _normalize_reference_ids(
        supporting_expectation_ids, "supporting_expectation_ids"
    )

    if normalized_status != "insufficient_evidence" and not fact_ids:
        raise TransmissionEvaluationValidationError(
            "supporting_fact_ids are required for this evaluation_status"
        )
    if not (relationship_ids or state_ids or history_ids or expectation_ids):
        raise TransmissionEvaluationValidationError("at least one structural reference is required")

    summary = evaluation_summary or build_transmission_evaluation_summary(
        evaluation_basis=normalized_basis,
        support_density_band=normalized_density,
        evidence_band=normalized_evidence,
        contradiction_band=normalized_contradiction,
        evaluation_status=normalized_status,
        supporting_fact_ids=fact_ids,
        supporting_relationship_ids=relationship_ids,
        supporting_state_ids=state_ids,
        supporting_state_history_ids=history_ids,
        supporting_expectation_ids=expectation_ids,
    )
    normalized_summary = _validate_summary(summary)

    evaluation_id = build_transmission_evaluation_id(
        pathway_id=normalized_pathway_id,
        evaluation_basis=normalized_basis,
        support_density_band=normalized_density,
        evidence_band=normalized_evidence,
        contradiction_band=normalized_contradiction,
        evaluation_status=normalized_status,
        supporting_fact_ids=fact_ids,
        supporting_relationship_ids=relationship_ids,
        supporting_state_ids=state_ids,
        supporting_state_history_ids=history_ids,
        supporting_expectation_ids=expectation_ids,
    )

    return TransmissionEvaluation(
        transmission_evaluation_id=evaluation_id,
        pathway_id=normalized_pathway_id,
        evaluation_basis=normalized_basis,
        support_density_band=normalized_density,
        evidence_band=normalized_evidence,
        contradiction_band=normalized_contradiction,
        evaluation_status=normalized_status,
        supporting_fact_ids=fact_ids,
        supporting_relationship_ids=relationship_ids,
        supporting_state_ids=state_ids,
        supporting_state_history_ids=history_ids,
        supporting_expectation_ids=expectation_ids,
        evaluation_summary=normalized_summary,
    )


def group_transmission_evaluations_by_status(
    evaluations: Iterable[TransmissionEvaluation | Mapping[str, Any]],
) -> OrderedDict[str, list[TransmissionEvaluation | Mapping[str, Any]]]:
    grouped: OrderedDict[str, list[TransmissionEvaluation | Mapping[str, Any]]] = OrderedDict(
        (status, []) for status in sorted(EVALUATION_STATUS_VALUES)
    )
    for evaluation in evaluations:
        status = getattr(evaluation, "evaluation_status", None)
        if status is None and isinstance(evaluation, Mapping):
            status = evaluation.get("evaluation_status")
        normalized = _require_member(status, EVALUATION_STATUS_VALUES, "evaluation_status")
        grouped[normalized].append(evaluation)
    return grouped

