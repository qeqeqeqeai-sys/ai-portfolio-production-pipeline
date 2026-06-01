from pathlib import Path

import pytest

from transmission_layers.transmission_evaluation import (
    TransmissionEvaluationValidationError,
    build_transmission_evaluation,
    build_transmission_evaluation_id,
    group_transmission_evaluations_by_status,
    normalize_transmission_evaluation_value,
)


def _evaluation(**overrides):
    base = {
        "pathway_id": "pathway:a",
        "evaluation_basis": "Observation Supported",
        "support_density_band": "Medium",
        "evidence_band": "Moderate",
        "contradiction_band": "None",
        "evaluation_status": "Evaluated",
        "supporting_fact_ids": ["fact-2", "fact-1"],
        "supporting_relationship_ids": ["rel-1"],
        "supporting_state_ids": [],
        "supporting_state_history_ids": [],
        "supporting_expectation_ids": [],
    }
    base.update(overrides)
    return build_transmission_evaluation(**base)


def test_deterministic_evaluation_ids_are_replay_safe():
    first = _evaluation()
    second = _evaluation()
    direct = build_transmission_evaluation_id(
        pathway_id="pathway:a",
        evaluation_basis="observation_supported",
        support_density_band="medium",
        evidence_band="moderate",
        contradiction_band="none",
        evaluation_status="evaluated",
        supporting_fact_ids=("fact-1", "fact-2"),
        supporting_relationship_ids=("rel-1",),
    )

    assert first.transmission_evaluation_id == second.transmission_evaluation_id == direct
    assert first.transmission_evaluation_id.startswith("teval_")


def test_builder_normalizes_values_and_reference_order():
    evaluation = _evaluation(
        evaluation_basis="relationship-state-supported",
        support_density_band=" high ",
        evidence_band=" strong ",
        contradiction_band=" limited ",
        evaluation_status=" contradicted ",
        supporting_fact_ids=[" fact-b ", "fact-a"],
        supporting_state_ids=["state-b", "state-a"],
        supporting_relationship_ids=[],
    )

    assert normalize_transmission_evaluation_value("Relationship State Supported") == "relationship_state_supported"
    assert evaluation.evaluation_basis == "relationship_state_supported"
    assert evaluation.supporting_fact_ids == ("fact-a", "fact-b")
    assert evaluation.supporting_state_ids == ("state-a", "state-b")


@pytest.mark.parametrize(
    "field,value",
    [
        ("evaluation_basis", "open_ended"),
        ("support_density_band", "dense"),
        ("evidence_band", "certain"),
        ("contradiction_band", "total"),
        ("evaluation_status", "complete"),
    ],
)
def test_bounded_taxonomy_validation(field, value):
    with pytest.raises(TransmissionEvaluationValidationError, match=field):
        _evaluation(**{field: value})


def test_missing_pathway_id_rejected():
    with pytest.raises(TransmissionEvaluationValidationError, match="pathway_id"):
        _evaluation(pathway_id="")


def test_missing_fact_support_rejected_unless_status_allows_exception():
    with pytest.raises(TransmissionEvaluationValidationError, match="supporting_fact_ids"):
        _evaluation(supporting_fact_ids=[])


def test_insufficient_evidence_allows_missing_fact_support():
    evaluation = _evaluation(
        evaluation_status="insufficient_evidence",
        supporting_fact_ids=[],
        supporting_relationship_ids=[],
        supporting_expectation_ids=["exp-1"],
    )

    assert evaluation.supporting_fact_ids == ()
    assert evaluation.evaluation_status == "insufficient_evidence"


def test_structural_support_required():
    with pytest.raises(TransmissionEvaluationValidationError, match="structural reference"):
        _evaluation(
            supporting_relationship_ids=[],
            supporting_state_ids=[],
            supporting_state_history_ids=[],
            supporting_expectation_ids=[],
        )


def test_duplicate_references_fail_closed():
    with pytest.raises(TransmissionEvaluationValidationError, match="duplicate"):
        _evaluation(supporting_fact_ids=["fact-1", "fact-1"])


def test_grouping_by_status():
    evaluated = _evaluation(pathway_id="pathway:1", evaluation_status="evaluated")
    indeterminate = _evaluation(pathway_id="pathway:2", evaluation_status="indeterminate")

    grouped = group_transmission_evaluations_by_status([indeterminate, evaluated])

    assert [item.pathway_id for item in grouped["evaluated"]] == ["pathway:1"]
    assert [item.pathway_id for item in grouped["indeterminate"]] == ["pathway:2"]


def test_evaluation_record_remains_structural_evidence_only():
    evaluation = _evaluation().to_ordered_dict()

    assert set(evaluation) == {
        "transmission_evaluation_id",
        "pathway_id",
        "evaluation_basis",
        "support_density_band",
        "evidence_band",
        "contradiction_band",
        "evaluation_status",
        "supporting_fact_ids",
        "supporting_relationship_ids",
        "supporting_state_ids",
        "supporting_state_history_ids",
        "supporting_expectation_ids",
        "evaluation_summary",
    }


def test_m9_implementation_avoids_forbidden_concepts():
    source = Path("transmission_layers/transmission_evaluation.py").read_text(encoding="utf-8").lower()
    forbidden_terms = [
        "influence",
        "prediction",
        "forecast",
        "causal proof",
        "probability",
        "trading",
        "portfolio",
        "memory",
        "recurrence",
        "graph ml",
        "machine learning",
        "significance",
        "important",
        "priority",
        "impact",
        "intelligence",
    ]

    assert not [term for term in forbidden_terms if term in source]
