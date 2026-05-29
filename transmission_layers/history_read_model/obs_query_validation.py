from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

from .analyst_consumption_views import build_consumption_view
from .historical_live_comparison import compare_historical_live_state
from .observation_fact_retrieval import OBSERVATION_FACTS_TABLE
from .observation_intelligence_query import retrieve_intelligence_question

SCHEMA_VERSION = "obs_query5_validation_v1"
GENERATION_TIMESTAMP = "1970-01-01T00:00:00Z"

FactRows = Sequence[Mapping[str, Any]]


def _fact(
    *,
    fact_id: int,
    identifier: str,
    metric_name: str,
    metric_value: float | str | None,
    phase_id: str,
    loaded_at: str,
    payload: Mapping[str, Any] | None = None,
) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("id", fact_id),
        ("phase_id", phase_id),
        ("phase_name", phase_id.lower()),
        ("window_days", 30),
        ("entity_type", "phase"),
        ("entity_id", f"{phase_id}:{identifier}"),
        ("metric_name", metric_name),
        ("metric_value", metric_value),
        ("artifact_id", f"obs-query5-artifact-{fact_id}"),
        ("run_id", f"obs-query5-run-{fact_id}"),
        ("created_at", loaded_at),
        ("loaded_at", loaded_at),
        ("payload_jsonb", OrderedDict([("evidence_id", f"obs-query5-evidence-{fact_id}"), ("identifier", identifier), *(payload or {}).items()])),
        ("duplicate_prevention_key", f"obs-query5-dup-{fact_id}"),
    ])


def build_validation_fact_fixture() -> list[OrderedDict[str, Any]]:
    """Controlled DB-2-shaped fact rows for deterministic OBS-QUERY validation."""
    return [
        _fact(fact_id=1, identifier="persistent_structure", metric_name="persistence_score", metric_value=0.92, phase_id="HIST-INTEL-1", loaded_at="2026-05-01T00:00:00Z", payload={"persistence_score": 0.92, "stability_class": "STABLE"}),
        _fact(fact_id=2, identifier="persistent_structure", metric_name="persistence_score", metric_value=0.88, phase_id="OPS-LIVE2", loaded_at="2026-05-02T00:00:00Z", payload={"persistence_score": 0.88, "stability_class": "STABLE"}),
        _fact(fact_id=3, identifier="changed_structure", metric_name="replay_stability_drift", metric_value=-0.41, phase_id="HIST-LONG-9", loaded_at="2026-05-03T00:00:00Z", payload={"drift_class": "DETERIORATING", "stability_class_transition": "STABLE->PARTIALLY_STABLE"}),
        _fact(fact_id=4, identifier="recurring_structure", metric_name="morphology_recurrence", metric_value=2, phase_id="HIST-INTEL-3", loaded_at="2026-05-04T00:00:00Z", payload={"recurring_structures": ["recurring_structure"]}),
        _fact(fact_id=5, identifier="recurring_structure", metric_name="morphology_recurrence", metric_value=1, phase_id="OPS-LIVE2", loaded_at="2026-05-05T00:00:00Z", payload={"recurring_structures": ["recurring_structure"]}),
        _fact(fact_id=6, identifier="dominant_structure", metric_name="sector_hhi", metric_value=0.73, phase_id="HIST-INTEL-2", loaded_at="2026-05-06T00:00:00Z", payload={"dominance_score": 0.73}),
        _fact(fact_id=7, identifier="weakening_structure", metric_name="liquidity_weakening", metric_value=-0.37, phase_id="HIST-LONG-9", loaded_at="2026-05-07T00:00:00Z", payload={"drift_class": "WEAKENING"}),
        _fact(fact_id=8, identifier="transitioned_structure", metric_name="stability_class_transition", metric_value="WEAK->STABLE", phase_id="HIST-LONG-9", loaded_at="2026-05-08T00:00:00Z", payload={"transition": "WEAK->STABLE"}),
        _fact(fact_id=9, identifier="live_only_anomaly", metric_name="persistence_score", metric_value=0.44, phase_id="OPS-LIVE2", loaded_at="2026-05-09T00:00:00Z"),
        _fact(fact_id=10, identifier="historical_only_structure", metric_name="persistence_score", metric_value=0.81, phase_id="HIST-INTEL-1", loaded_at="2026-05-10T00:00:00Z"),
        _fact(fact_id=11, identifier="weakening_live_structure", metric_name="persistence_score", metric_value=0.95, phase_id="HIST-INTEL-1", loaded_at="2026-05-11T00:00:00Z"),
        _fact(fact_id=12, identifier="weakening_live_structure", metric_name="persistence_score", metric_value=0.52, phase_id="OPS-LIVE2", loaded_at="2026-05-12T00:00:00Z"),
        _fact(fact_id=13, identifier="strengthening_live_structure", metric_name="persistence_score", metric_value=0.18, phase_id="HIST-INTEL-1", loaded_at="2026-05-13T00:00:00Z"),
        _fact(fact_id=14, identifier="strengthening_live_structure", metric_name="persistence_score", metric_value=0.66, phase_id="OPS-LIVE2", loaded_at="2026-05-14T00:00:00Z"),
    ]


def _ids(items: Iterable[Mapping[str, Any]]) -> set[str]:
    return {str(item.get("identifier")) for item in items}


def _pass_fail(name: str, question: str, passed: bool, expected: Mapping[str, Any], actual: Mapping[str, Any], trace: Mapping[str, Any]) -> OrderedDict[str, Any]:
    return OrderedDict([
        ("test_name", name),
        ("question", question),
        ("status", "pass" if passed else "fail"),
        ("expected_result", OrderedDict(expected)),
        ("actual_result", OrderedDict(actual)),
        ("traceability", OrderedDict(trace)),
    ])


def _query_test(name: str, question: str, query_type: str, expected_identifier: str, rows: FactRows) -> OrderedDict[str, Any]:
    result = retrieve_intelligence_question(query_type=query_type, fact_rows=rows, limit=10)
    identifiers = _ids(result.get("results") or [])
    item = next((item for item in result.get("results") or [] if item.get("identifier") == expected_identifier), None)
    passed = item is not None and bool(item.get("supporting_fact_ids")) and bool(item.get("supporting_evidence_ids"))
    return _pass_fail(
        name,
        question,
        passed,
        {"query_type": query_type, "identifier_present": expected_identifier, "traceability_required": True},
        {"query_type": result.get("query_type"), "identifiers": sorted(identifiers), "result_count": result.get("result_count")},
        {"supporting_fact_ids": list((item or {}).get("supporting_fact_ids") or []), "supporting_evidence_ids": list((item or {}).get("supporting_evidence_ids") or [])},
    )


def _comparison_test(name: str, question: str, comparison_type: str, expected_identifier: str, expected_classification: str, rows: FactRows) -> OrderedDict[str, Any]:
    result = compare_historical_live_state(comparison_type=comparison_type, fact_rows=rows, limit=10)
    item = next((item for item in result.get("results") or [] if item.get("identifier") == expected_identifier), None)
    fact_ids = [*((item or {}).get("historical_supporting_fact_ids") or []), *((item or {}).get("live_supporting_fact_ids") or [])]
    passed = item is not None and item.get("classification") == expected_classification and bool(fact_ids) and bool(item.get("supporting_evidence_ids"))
    return _pass_fail(
        name,
        question,
        passed,
        {"comparison_type": comparison_type, "identifier_present": expected_identifier, "classification": expected_classification, "traceability_required": True},
        {"comparison_type": result.get("comparison_type"), "identifiers": sorted(_ids(result.get("results") or [])), "classification": (item or {}).get("classification"), "result_count": result.get("result_count")},
        {"supporting_fact_ids": sorted(str(fact_id) for fact_id in fact_ids), "supporting_evidence_ids": list((item or {}).get("supporting_evidence_ids") or [])},
    )


def _section(view: Mapping[str, Any], name: str) -> Mapping[str, Any]:
    return next((section for section in view.get("sections") or [] if section.get("section_name") == name), {})


def _consumption_test(name: str, view_type: str, required_sections: Sequence[str], required_identifiers: Sequence[str], rows: FactRows) -> OrderedDict[str, Any]:
    view = build_consumption_view(view_type=view_type, fact_rows=rows, limit=10)
    sections = {str(section.get("section_name")): section for section in view.get("sections") or []}
    present_identifiers = sorted({str(item.get("identifier")) for section in sections.values() for item in section.get("items") or []})
    sections_present = all(section in sections and sections[section].get("item_count", 0) > 0 for section in required_sections)
    identifiers_present = all(identifier in present_identifiers for identifier in required_identifiers)
    traceability_present = bool(view.get("supporting_fact_ids")) and bool(view.get("supporting_evidence_ids"))
    return _pass_fail(
        name,
        f"Can analysts consume {view_type} with required structures?",
        sections_present and identifiers_present and traceability_present,
        {"view_type": view_type, "required_sections": list(required_sections), "required_identifiers": list(required_identifiers), "traceability_required": True},
        {"view_type": view.get("view_type"), "sections": sorted(sections), "identifiers": present_identifiers},
        {"supporting_fact_ids": list(view.get("supporting_fact_ids") or []), "supporting_evidence_ids": list(view.get("supporting_evidence_ids") or [])},
    )


def _traceability_test(rows: FactRows) -> OrderedDict[str, Any]:
    outputs: list[Mapping[str, Any]] = []
    outputs.extend(retrieve_intelligence_question(query_type=query_type, fact_rows=rows, limit=10) for query_type in ("persisted", "changed", "recurred", "dominant", "weakened", "transitioned"))
    outputs.extend(compare_historical_live_state(comparison_type=comparison_type, fact_rows=rows, limit=10) for comparison_type in ("baseline_overlap", "live_anomalies", "historical_recurrence", "persistent_weakening_live", "weak_strengthening_live", "baseline_deviation"))
    outputs.extend(build_consumption_view(view_type=view_type, fact_rows=rows, limit=10) for view_type in ("ecosystem_briefing", "investigation_queue"))
    fixture_fact_ids = {str(row["id"]) for row in rows}
    fixture_evidence_ids = {str((row.get("payload_jsonb") or {}).get("evidence_id")) for row in rows}
    missing: list[str] = []
    for index, output in enumerate(outputs):
        fact_ids = set(str(fact_id) for fact_id in [*(output.get("supporting_fact_ids") or []), *(output.get("historical_fact_ids") or []), *(output.get("live_fact_ids") or [])])
        evidence_ids = set(str(evidence_id) for evidence_id in output.get("supporting_evidence_ids") or [])
        if output.get("result_count", len(output.get("sections") or [])) and (not fact_ids or not evidence_ids):
            missing.append(f"output_{index}")
        if not fact_ids <= fixture_fact_ids or not evidence_ids <= fixture_evidence_ids:
            missing.append(f"output_{index}_fixture_mismatch")
    return _pass_fail(
        "traceability_drilldown_chain",
        "Does every non-empty output retain view/result to fact to evidence drilldown?",
        not missing,
        {"supporting_fact_ids_present": True, "supporting_evidence_ids_present": True, "ids_match_fixture_rows": True},
        {"outputs_checked": len(outputs), "missing_or_mismatched_outputs": missing},
        {"fixture_fact_ids": sorted(fixture_fact_ids), "fixture_evidence_ids": sorted(fixture_evidence_ids)},
    )


def _governance_test(rows: FactRows) -> OrderedDict[str, Any]:
    outputs = [
        retrieve_intelligence_question(query_type="persisted", fact_rows=rows, limit=10),
        compare_historical_live_state(comparison_type="baseline_overlap", fact_rows=rows, limit=10),
        build_consumption_view(view_type="ecosystem_briefing", fact_rows=rows, limit=10),
    ]
    required_flags = {
        "provider_api_calls_enabled": False,
        "db_writes_enabled": False,
        "schema_migrations_enabled": False,
        "predictions_enabled": False,
        "recommendations_enabled": False,
        "market_actions_enabled": False,
        "no_new_intelligence_generation": True,
        "source_of_truth": OBSERVATION_FACTS_TABLE,
    }
    violations = []
    for output in outputs:
        cert = output.get("governance_certification") or {}
        for key, expected in required_flags.items():
            if cert.get(key) != expected:
                violations.append({"phase": cert.get("phase"), "flag": key, "actual": cert.get(key), "expected": expected})
    return _pass_fail(
        "governance_certification",
        "Does validation reuse retrieval without providers, DB writes, schema mutations, predictions, recommendations, or new intelligence generation?",
        not violations,
        required_flags,
        {"outputs_checked": len(outputs), "violations": violations},
        {"source_table": OBSERVATION_FACTS_TABLE, "validation_mode": "controlled_fact_fixtures_only"},
    )


def _category(name: str, tests: Sequence[Mapping[str, Any]]) -> OrderedDict[str, Any]:
    passed = sum(1 for test in tests if test.get("status") == "pass")
    failed = len(tests) - passed
    return OrderedDict([("category_name", name), ("tests_executed", len(tests)), ("tests_passed", passed), ("tests_failed", failed), ("tests", list(tests))])


def _rate(passed: int, total: int) -> float:
    return 1.0 if total == 0 else round(passed / total, 6)


def run_obs_query5_validation(fact_rows: FactRows | None = None) -> OrderedDict[str, Any]:
    rows = list(fact_rows or build_validation_fact_fixture())
    retrieval_tests = [
        _query_test("persisted_retrieval", "What persisted?", "persisted", "persistent_structure", rows),
        _query_test("changed_retrieval", "What changed?", "changed", "changed_structure", rows),
        _query_test("recurrence_retrieval", "What recurred?", "recurred", "recurring_structure", rows),
        _query_test("dominant_retrieval", "What dominates?", "dominant", "dominant_structure", rows),
        _query_test("weakening_retrieval", "What weakened?", "weakened", "weakening_structure", rows),
        _query_test("transition_retrieval", "What transitioned?", "transitioned", "WEAK->STABLE", rows),
    ]
    comparison_tests = [
        _comparison_test("overlap_detection", "What persisted across historical and live?", "baseline_overlap", "persistent_structure", "historical_and_live", rows),
        _comparison_test("live_only_anomaly_detection", "What is unusual in live observations?", "live_anomalies", "live_only_anomaly", "live_only", rows),
        _comparison_test("historical_only_detection", "What historical structures are absent live?", "baseline_overlap", "historical_only_structure", "historical_only", rows),
        _comparison_test("strengthening_detection", "What strengthened live versus historical?", "weak_strengthening_live", "strengthening_live_structure", "live_stronger_than_historical", rows),
        _comparison_test("weakening_detection", "What weakened live versus historical?", "persistent_weakening_live", "weakening_live_structure", "live_weaker_than_historical", rows),
        _comparison_test("recurrence_detection", "What historical patterns recurred live?", "historical_recurrence", "recurring_structure", "recurring_historical_pattern", rows),
    ]
    consumption_tests = [
        _consumption_test("ecosystem_briefing_coverage", "ecosystem_briefing", ["Persistent Structures", "Significant Deviations", "Investigation Candidates"], ["persistent_structure", "live_only_anomaly"], rows),
        _consumption_test("investigation_queue_coverage", "investigation_queue", ["Investigation Queue", "Changed Structure Context", "Weakening Structure Context"], ["live_only_anomaly", "weakening_live_structure", "strengthening_live_structure"], rows),
    ]
    traceability_tests = [_traceability_test(rows)]
    governance_tests = [_governance_test(rows)]
    categories = [
        _category("Category A — Retrieval Correctness", retrieval_tests),
        _category("Category B — Historical vs Live Validation", comparison_tests),
        _category("Category C — Consumption View Validation", consumption_tests),
        _category("Category D — Traceability Validation", traceability_tests),
        _category("Category E — Governance Validation", governance_tests),
    ]
    tests_executed = sum(category["tests_executed"] for category in categories)
    tests_passed = sum(category["tests_passed"] for category in categories)
    tests_failed = sum(category["tests_failed"] for category in categories)
    retrieval = categories[0]
    comparison = categories[1]
    consumption = categories[2]
    traceability = categories[3]
    governance = categories[4]
    return OrderedDict([
        ("schema_version", SCHEMA_VERSION),
        ("validation_run", OrderedDict([("phase", "OBS-QUERY-5"), ("generation_timestamp", GENERATION_TIMESTAMP), ("validation_mode", "deterministic_controlled_fact_fixture"), ("source_table", OBSERVATION_FACTS_TABLE), ("fixture_fact_count", len(rows))])),
        ("categories", categories),
        ("tests_executed", tests_executed),
        ("tests_passed", tests_passed),
        ("tests_failed", tests_failed),
        ("coverage_metrics", OrderedDict([
            ("retrieval_correctness_rate", _rate(retrieval["tests_passed"], retrieval["tests_executed"])),
            ("comparison_correctness_rate", _rate(comparison["tests_passed"], comparison["tests_executed"])),
            ("consumption_view_coverage", _rate(consumption["tests_passed"], consumption["tests_executed"])),
            ("traceability_coverage", _rate(traceability["tests_passed"], traceability["tests_executed"])),
            ("governance_compliance", _rate(governance["tests_passed"], governance["tests_executed"])),
        ])),
        ("governance_certification", OrderedDict([("validation_only", True), ("retrieval_reuse_only", True), ("provider_api_calls_enabled", False), ("db_writes_enabled", False), ("schema_migrations_enabled", False), ("predictions_enabled", False), ("recommendations_enabled", False), ("market_actions_enabled", False), ("no_new_intelligence_generation", True), ("source_of_truth", OBSERVATION_FACTS_TABLE)])),
        ("overall_status", "pass" if tests_failed == 0 else "fail"),
    ])


def render_obs_query5_validation_markdown(result: Mapping[str, Any]) -> str:
    lines = [
        "# OBS-QUERY Validation Summary\n\n",
        "## Retrieval Validation\n",
        _category_summary(result, "Category A — Retrieval Correctness"),
        "\n## Historical vs Live Validation\n",
        _category_summary(result, "Category B — Historical vs Live Validation"),
        "\n## Consumption Validation\n",
        _category_summary(result, "Category C — Consumption View Validation"),
        "\n## Traceability Validation\n",
        _category_summary(result, "Category D — Traceability Validation"),
        "\n## Governance Validation\n",
        _category_summary(result, "Category E — Governance Validation"),
        "\n## Overall Assessment\n",
        f"- overall_status: {result.get('overall_status')}\n",
        f"- tests_executed: {result.get('tests_executed')}\n",
        f"- tests_passed: {result.get('tests_passed')}\n",
        f"- tests_failed: {result.get('tests_failed')}\n",
        "- scorecard_methodology: explicit pass/fail counts converted to rates; no arbitrary weighting.\n",
    ]
    for key, value in (result.get("coverage_metrics") or {}).items():
        lines.append(f"- {key}: {value}\n")
    return "".join(lines)


def _category_summary(result: Mapping[str, Any], category_name: str) -> str:
    category = next((item for item in result.get("categories") or [] if item.get("category_name") == category_name), {})
    lines = [f"- tests_executed: {category.get('tests_executed', 0)}\n", f"- tests_passed: {category.get('tests_passed', 0)}\n", f"- tests_failed: {category.get('tests_failed', 0)}\n\n"]
    lines.append("| test | status | question | supporting facts | supporting evidence |\n")
    lines.append("| --- | --- | --- | --- | --- |\n")
    for test in category.get("tests") or []:
        trace = test.get("traceability") or {}
        lines.append(f"| {test.get('test_name')} | {test.get('status')} | {test.get('question')} | {', '.join(trace.get('supporting_fact_ids') or trace.get('fixture_fact_ids') or [])} | {', '.join(trace.get('supporting_evidence_ids') or trace.get('fixture_evidence_ids') or [])} |\n")
    return "".join(lines)


def write_obs_query5_validation_outputs(result: Mapping[str, Any], *, output_json: str | Path | None = None, output_md: str | Path | None = None) -> OrderedDict[str, str | None]:
    json_path = Path(output_json) if output_json else None
    md_path = Path(output_md) if output_md else None
    if json_path is not None:
        json_path.parent.mkdir(parents=True, exist_ok=True)
        json_path.write_text(json.dumps(result, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")
    if md_path is not None:
        md_path.parent.mkdir(parents=True, exist_ok=True)
        md_path.write_text(render_obs_query5_validation_markdown(result), encoding="utf-8")
    return OrderedDict([("output_json", str(json_path) if json_path else None), ("output_md", str(md_path) if md_path else None)])
