# Phase B6 — Institutional Reporting & Analyst Briefing Layer

## Objective
Implement deterministic institutional reporting that packages B1-B5 outputs into fixed report sections and fixed-template analyst briefing artifacts.

## Architecture identity
- deterministic institutional expectation-fragility intelligence
- additive-only deterministic formatting/summarization

## Public APIs
- build_b6_report_context
- build_executive_fragility_summary
- build_key_fragility_findings
- build_heatmap_briefing_section
- build_asymmetry_briefing_section
- build_benchmark_relative_briefing_section
- build_historical_replay_briefing_section
- build_alert_briefing_section
- build_entity_briefing_cards
- build_subsector_briefing_cards
- build_evidence_appendix
- build_limitations_and_disclosures
- build_phase_b6_institutional_report

## Report section model
Fixed section ordering with MISSING_INPUT handling for absent upstream phase reports.

## Deterministic briefing methodology
B6 only extracts, sorts, and templates supplied B1-B5 context with fixed precedence and fixed template identifiers.

## Entity/subsector card methodology
Exact deterministic key precedence: entity_id > ticker > entity_name. No fuzzy matching.

## Evidence appendix design
Includes source phase inventory, checksum inventory, evidence references, and replay trace.

## Replayability guarantees
Stable checksums from canonical JSON serialization, fixed section ordering, fixed sort/tie-break rules.

## Exclusions preserved
No recommendations, no allocation, no execution, no autonomous dispatch, no unrestricted narrative generation.

## Tests run
See pytest commands in implementation validation.

## Final implementation status
Implemented and validated with targeted phase tests plus legacy B1-B5 regression checks.
