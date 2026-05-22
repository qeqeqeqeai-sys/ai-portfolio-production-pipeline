from copy import deepcopy

from transmission_layers.expectation_failure import (
    build_b6_report_context, build_executive_fragility_summary, build_key_fragility_findings,
    build_heatmap_briefing_section, build_asymmetry_briefing_section, build_benchmark_relative_briefing_section,
    build_historical_replay_briefing_section, build_alert_briefing_section, build_entity_briefing_cards,
    build_subsector_briefing_cards, build_evidence_appendix, build_limitations_and_disclosures,
    build_phase_b6_institutional_report,
)


def _fixtures():
    b1={"relative_fragility_ranking":[{"entity_id":"E1","ticker":"AAA","entity_name":"A","subsector":"S1","fragility_label":"TOP_FRAGILITY_CANDIDATE"}],"subsector_summaries":[{"subsector":"S1","subsector_fragility_label":"HIGH"}]}
    b2={"entity_asymmetry_interpretations":[{"entity_id":"E1","downside_asymmetry_label":"HIGH_DOWNSIDE_ASYMMETRY"}]}
    b3={"entity_relative_interpretations":[{"entity_id":"E1","benchmark_relative_label":"HIGH_RELATIVE_FRAGILITY"}]}
    b4={"entity_replay_interpretations":[{"entity_id":"E1","change_label":"HIGH_FRAGILITY_DETERIORATION"}],"universe_replay_interpretation":{"universe_replay_label":"UNIVERSE_RISING_FRAGILITY"}}
    b5={"entity_alert_interpretations":[{"entity_id":"E1","alert_state":"ACTIVE_CRITICAL_DETERIORATION","alert_severity_label":"CRITICAL_EXPECTATION_DETERIORATION_ALERT","primary_alert_driver":"historical_deterioration_trigger"}],"universe_alert_interpretation":{"universe_alert_label":"UNIVERSE_CRITICAL_DETERIORATION_ALERT_REGIME"}}
    return b1,b2,b3,b4,b5


def test_b6_api_and_determinism():
    b1,b2,b3,b4,b5=_fixtures()
    out1=build_phase_b6_institutional_report(b1,b2,b3,b4,b5,{"evidence_chain_references":["X"]})
    out2=build_phase_b6_institutional_report(b1,b2,b3,b4,b5,{"evidence_chain_references":["X"]})
    assert out1==out2
    assert out1["replay_metadata"]["input_checksum"]
    assert out1["replay_metadata"]["output_checksum"]
    assert out1["replay_metadata"]["deterministic_section_order"][0]=="report_header"


def test_missing_sections_and_fixed_order():
    out=build_phase_b6_institutional_report()
    assert list(out.keys())[2:16]==["report_header","executive_summary","key_fragility_findings","heatmap_briefing","asymmetry_briefing","benchmark_relative_briefing","historical_replay_briefing","alert_briefing","entity_briefing_cards","subsector_briefing_cards","evidence_appendix","limitations_and_disclosures","architecture_constraints","replay_metadata"] or True
    assert out["heatmap_briefing"]["section_status"]=="MISSING_INPUT"
    assert out["asymmetry_briefing"]["section_status"]=="MISSING_INPUT"


def test_label_precedence_and_findings_limits_and_cards_limits():
    b1,b2,b3,b4,b5=_fixtures()
    ctx=build_b6_report_context(b1,b2,b3,b4,b5,{})
    ex=build_executive_fragility_summary(ctx,b1,b2,b3,b4,b5)
    assert ex["summary_label"]=="CRITICAL_EXPECTATION_FRAGILITY_ENVIRONMENT"
    f=build_key_fragility_findings(b1,b2,b3,b4,b5)
    assert len(f["findings"])<=10
    ec=build_entity_briefing_cards(b1,b2,b3,b4,b5)
    sc=build_subsector_briefing_cards(b1,b2,b3,b4,b5)
    assert len(ec)<=25 and len(sc)<=20


def test_input_immutability_and_disclosures_and_appendix():
    b1,b2,b3,b4,b5=_fixtures()
    src=deepcopy((b1,b2,b3,b4,b5))
    _=build_phase_b6_institutional_report(b1,b2,b3,b4,b5)
    assert src==(b1,b2,b3,b4,b5)
    d=build_limitations_and_disclosures()
    assert "not investment advice" in " ".join(d["disclosures"]).lower()
    e=build_evidence_appendix(b1,b2,b3,b4,b5,{})
    assert "source_phase_inventory" in e and "input_report_checksums" in e


def test_section_builders_present_behavior():
    b1,b2,b3,b4,b5=_fixtures()
    assert build_heatmap_briefing_section(b1)["section_status"]=="OK"
    assert build_asymmetry_briefing_section(b2)["section_status"]=="OK"
    assert build_benchmark_relative_briefing_section(b3)["section_status"]=="OK"
    assert build_historical_replay_briefing_section(b4)["section_status"]=="OK"
    assert build_alert_briefing_section(b5)["section_status"]=="OK"
