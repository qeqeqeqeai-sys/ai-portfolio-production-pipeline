# 05 — Historical Intelligence Source Notes

## Purpose
Historical Intelligence is the repository's local, observational-only stack for converting completed historical ecology artifacts into bounded facts, taxonomic findings, Narrative Evolution signals, ecosystem synthesis, and DB-2/OBS-QUERY-ready observation rows.

Repository anchors: `transmission_layers/expectation_failure/real_data/hist_long4_real_multi_window_ecology.py`, `hist_long5b_temporal_delta_sensitivity_classification.py`, `hist_long6_cross_sectional_ecology_differentiation.py`, `hist_long7_intra_group_structural_contrast.py`, `transmission_layers/history_long/*.py`, `transmission_layers/history_read_model/loader.py`, `fact_emitter.py`, `observation_fact_retrieval.py`.

## Architectural role
The stack has three roles:

1. **HIST-LONG** establishes historical ecology and structural evolution from completed local artifacts.
2. **HIST-FACT** turns historical artifacts into bounded fact and Evidence Reference rows.
3. **HIST-INTEL** groups those facts into traceable structural findings and ecosystem synthesis.

The code does not support describing these layers as forecasting systems. The repeated governance certificates disable provider calls, Supabase writes in analysis layers, prediction, trading, portfolio recommendation, replay activation/execution, topology persistence, and governed activation unless a later explicitly governed path is added.

## Layer map

### HIST-LONG-4 — real multi-window ecology review
- **Purpose**: orchestrate and review controlled historical ecology windows, with required 20/60/120 trading-day windows.
- **Inputs**: curated symbol universe settings, density runner output, review builder output, window summaries, and explicit disabled write/activation flags.
- **Outputs**: multi-window ecology artifact and review report at the configured artifact/report paths.
- **Architectural role**: establishes the historical input substrate consumed by later temporal, cross-sectional, and fact expansion layers.
- **Governance boundaries**: analysis/review posture; no Supabase write, replay activation, topology persistence, or raw cache write by default.
- **Downstream consumers**: HIST-LONG-5B, HIST-LONG-6, HIST-LONG-7, HIST-LONG-8, HIST-FACT-1, HIST-INTEL-1, HIST-INTEL-1B, and DB-1 loader defaults.

### HIST-LONG-5B — temporal delta sensitivity classification
- **Purpose**: classify how historical ecology metrics change across source windows.
- **Inputs**: completed HIST-LONG-4 artifact, with fallback blocked-artifact behavior when the source is unavailable or invalid.
- **Outputs**: temporal delta sensitivity artifact and report containing metric deltas, classifications, source verification, and governance certification.
- **Architectural role**: turns multi-window history into temporal change/sensitivity evidence.
- **Governance boundaries**: local source artifact only; no provider calls, prediction, trading, write expansion, replay execution, or topology mutation.
- **Downstream consumers**: HIST-LONG-6, HIST-LONG-7, HIST-FACT-1, HIST-FACT-2, HIST-INTEL-1, HIST-INTEL-1B, HIST-INTEL-2, and HIST-INTEL-3.

### HIST-LONG-6 — cross-sectional ecology differentiation
- **Purpose**: differentiate historical ecology by sector/subsector/group using HIST-LONG-4 and HIST-LONG-5B.
- **Inputs**: verified HIST-LONG-4 and HIST-LONG-5B artifacts across required windows.
- **Outputs**: differentiation artifact/report with representation, stability, confidence, symbol-count, symbol-share, and differentiation-score findings.
- **Architectural role**: adds cross-sectional ecology and sector/group structure to the historical substrate.
- **Governance boundaries**: observational-only, source-artifacts-only behavior; source governance flags are checked before deriving outputs.
- **Downstream consumers**: HIST-LONG-7, HIST-FACT-1, HIST-INTEL-1, HIST-INTEL-1B, HIST-INTEL-2, and ecosystem synthesis.

### HIST-LONG-7 — intra-group structural contrast
- **Purpose**: compare structure inside selected groups and distinguish coherent, fragmented, broad, or fragile group behavior.
- **Inputs**: HIST-LONG-4, HIST-LONG-5B, and HIST-LONG-6 artifacts.
- **Outputs**: intra-group contrast artifact/report with morphology classifications, structural reads, topology-stability indicators, and breadth/fragility indicators.
- **Architectural role**: adds morphology and within-group contrast to the historical ecology stack.
- **Governance boundaries**: local source artifacts only; forbidden flags include provider calls, all reexecution/activation flags, persistence writes, prediction, and trading.
- **Downstream consumers**: HIST-FACT-1, HIST-INTEL-1, HIST-INTEL-1B, HIST-INTEL-2, HIST-INTEL-3, and HIST-INTEL-4.

### HIST-LONG-8 — cross-window persistence structural stability
- **Purpose**: analyze whether structures persist across historical windows.
- **Inputs**: HIST-LONG-4 source artifact or provided observation facts.
- **Outputs**: persistence analysis, observations, fact rows, and markdown report.
- **Architectural role**: elevates recurrence and persistence into fact-like rows consumable by HIST-LONG-9 and HIST-FACT-1.
- **Governance boundaries**: bounded local analysis with no provider, write, prediction, trading, or topology side effects.
- **Downstream consumers**: HIST-LONG-9, HIST-FACT-1, OBS-QUERY validation fixtures, and historical/live comparison examples.

### HIST-LONG-9 — persistence evolution and stability drift
- **Purpose**: analyze how persistence and stability classes drift over time.
- **Inputs**: HIST-LONG-8-style observation facts and inspected input metadata.
- **Outputs**: drift analysis, stability-class transitions, fact rows, and report.
- **Architectural role**: captures structural evolution: weakening, strengthening, deterioration, and stability-class movement.
- **Governance boundaries**: fact/read-model oriented local analysis; no forecasting, no trade/action generation, and no external provider dependency.
- **Downstream consumers**: HIST-FACT-1, OBS-QUERY validation, historical/live comparison, and consumption Evidence Reference drill-down.

### HIST-FACT-1 — historical observation fact expansion
- **Purpose**: deterministically expand HIST-LONG artifacts into bounded historical observation facts.
- **Inputs**: HIST-LONG-4, HIST-LONG-5B, HIST-LONG-6, HIST-LONG-7, HIST-LONG-8, and HIST-LONG-9 artifacts/reports when available.
- **Outputs**: `expanded_facts` with `fact_id`, `fact_type`, entity fields, metric fields, `window_days`, `evidence_count`, `confidence_label`, `source_phase`, `source_artifact`, and bounded `payload_jsonb`.
- **Architectural role**: normalizes heterogeneous historical ecology evidence into a common fact vocabulary that DB-2 and HIST-INTEL can consume.
- **Governance boundaries**: deterministic fact generation over existing local artifacts only; no providers, no Supabase writes, no live ingestion, no prediction, no trading, no recommendation, and no governed activation.
- **Downstream consumers**: HIST-FACT-2, HIST-INTEL-1B, HIST-INTEL-2, HIST-INTEL-4, DB-2 emission, OBS-QUERY examples.

### HIST-FACT-2 — historical regime evidence expansion
- **Purpose**: convert HIST-FACT-1 and intelligence outputs into bounded regime evidence.
- **Inputs**: HIST-FACT-1 expanded facts, HIST-INTEL-2 taxonomy-weighted output, and HIST-INTEL-3 Narrative Evolution output.
- **Outputs**: expanded regime evidence and report rows carrying stable Evidence Reference identifiers, domains, scores, labels, and source lineage.
- **Architectural role**: bridges raw historical facts to regime/evolution evidence used by synthesis and downstream query validation.
- **Governance boundaries**: local report/artifact inputs only; no provider, write, prediction, trading, portfolio, replay, or topology side effects.
- **Downstream consumers**: HIST-INTEL-4 and any DB-2/OBS-QUERY path that needs Evidence Reference identifiers in payloads.

### HIST-INTEL-1 — historical structural findings
- **Purpose**: extract ranked structural findings from historical artifacts.
- **Inputs**: HIST-LONG-4 through HIST-LONG-7 artifacts and optional observation facts.
- **Outputs**: deterministic report with findings, source digest, confidence labels, source status, and bounded top-N selections.
- **Architectural role**: first intelligence read over historical ecology; identifies persistence, fragility, drift, recurrence, and stability themes without creating forecasts.
- **Governance boundaries**: analysis-only; no provider calls, no Supabase writes, no prediction, no trading, no portfolio recommendation, no governed activation.
- **Downstream consumers**: HIST-INTEL-1B compact source path, HIST-FACT-2 context, and whitepaper historical intelligence narrative.

### HIST-INTEL-1B — fact-native historical findings
- **Purpose**: produce historical findings directly from observation facts and compact historical sources.
- **Inputs**: local fact rows and compact source artifacts including HIST-LONG-4 through HIST-LONG-7 and HIST-INTEL-1.
- **Outputs**: fact-native findings with bounded top-N, local fact-row counts, and source digest.
- **Architectural role**: aligns historical intelligence with DB-2's fact-native architecture by prioritizing observation facts over large generated artifacts.
- **Governance boundaries**: local-only, bounded row scans; no provider/write/prediction/trading/recommendation behavior.
- **Downstream consumers**: OBS-QUERY-style question answering and DB-2 historical fact interpretation.

### HIST-INTEL-2 — taxonomy-weighted intelligence engine
- **Purpose**: weight fact rows by taxonomy so historical signals can be ranked by persistence, fragility, drift, replay/recurrence, and stability themes.
- **Inputs**: HIST-FACT-1 expanded observation facts or provided fact rows.
- **Outputs**: taxonomy-weighted rows, domain summaries, confidence/coverage metrics, and report outputs.
- **Architectural role**: provides the domain vocabulary that OBS-QUERY later exposes as taxonomy filters and intelligence questions.
- **Governance boundaries**: bounded local facts, no external calls, no prediction, no trading/recommendation, and no write-side effects.
- **Downstream consumers**: HIST-FACT-2, HIST-INTEL-3, HIST-INTEL-4, OBS-QUERY fixtures.

### HIST-INTEL-3 — Narrative Evolution and regime transition mapping
- **Purpose**: map recurring, emerging, decaying, and transitioned narrative/regime structures from taxonomy-weighted historical rows.
- **Inputs**: HIST-INTEL-2 output and bounded local fact and Evidence Reference rows.
- **Outputs**: narrative sets, transition maps, recurring structure records, and governance-certified report outputs.
- **Architectural role**: captures morphology and recurrence language for historical intelligence without claiming forward prediction.
- **Governance boundaries**: local analysis over existing facts; no providers, no writes, no forecast/action generation.
- **Downstream consumers**: HIST-FACT-2, HIST-INTEL-4, OBS-QUERY validation rows for recurrence and transition questions.

### HIST-INTEL-4 — ecosystem intelligence synthesis
- **Purpose**: synthesize historical facts, regime evidence, taxonomy output, and Narrative Evolution into a traceable ecosystem characterization.
- **Inputs**: HIST-FACT-1, HIST-FACT-2, HIST-INTEL-2, and HIST-INTEL-3 outputs.
- **Outputs**: executive synthesis, structural identity, dominant historical forces, stability assessment, transition-readiness assessment, narrative-continuity assessment, evidence summary, limitations, and governance certification.
- **Architectural role**: terminal historical intelligence synthesis before DB-2/OBS-QUERY consumption; all conclusions remain evidence-bounded and traceable to source facts/evidence.
- **Governance boundaries**: analysis-only; no provider calls, Supabase writes, predictions, trading, portfolio recommendations, replay/topology activation, or governed activation.
- **Downstream consumers**: DB-2 source notes, OBS-QUERY comparison and question layers, consumption views, and whitepaper narrative.

## Persistence, recurrence, stability, morphology, ecology, and structural evolution
- **Persistence** is represented by cross-window persistence scores, persistent structures, source-score facts, and HIST-LONG-8/HIST-LONG-9 fact rows.
- **Recurrence** is represented by repeated historical structures and Narrative Evolution outputs such as recurring historical pattern and recurring structure classifications.
- **Stability** is represented by stability labels, stability-class transitions, stable vs destabilizing evidence scores, and live/historical comparisons.
- **Morphology** is represented by sector morphology, intra-group structural contrast, dominant/fragmented/coherent group reads, and narrative morphology classifications.
- **Ecology** is represented by window metrics, sector/subsector concentration, symbol coverage, group differentiation, and ecosystem characterization.
- **Structural evolution** is represented by temporal deltas, drift classes, transition maps, decaying/emerging narrative sets, and persistence drift.

## Historical stack ordering rationale
Repository evidence supports a layered but not strictly linear ordering. HIST-LONG-4/5B/6/7 build the completed historical ecology substrate. HIST-LONG-8/9 derive persistence, recurrence, and drift fact-like rows from that substrate. HIST-FACT-1/2 expand historical artifacts and Evidence Reference identifiers into bounded observation-fact candidates. HIST-INTEL-1/1B/2/3/4 group local facts and artifacts into structural findings, taxonomy weights, Narrative Evolution, and ecosystem synthesis. DB-2 persistence occurs only when a governed emission path writes candidates to `sefi_observation_facts`; OBS-QUERY can then retrieve persisted facts or, in validation/local modes, bounded fixtures. Therefore the stack should be read as a set of producing, contributing, and consuming roles rather than a one-way pipe from Historical Intelligence into DB-2.

## Contribution to DB-2
Historical Intelligence contributes to DB-2 in two ways:

1. `history_read_model.loader` can load historical artifacts into append-only registry, run, phase, observation, window, morphology, symbol, and observation-fact tables after validating completed status, schema, governance, bounded payloads, and duplicate-prevention keys.
2. `fact_emitter.py` can emit normalized observation facts from historical/intelligence observations into `sefi_observation_facts` with explicit phase, artifact, run, entity, metric, window, payload, and duplicate-key lineage.

## Historical to OBS-QUERY handoff
| Historical output | OBS-QUERY filter or input | OBS-QUERY question/comparison type |
| --- | --- | --- |
| Persisted historical observation facts with `phase_id` such as `HIST-LONG-*`, `HIST-FACT-*`, or `HIST-INTEL-*` | `source_layer` / `phase_id`; `taxonomy` / `metric_name`; `snapshot_date`; `symbol`; `evidence_id` when present | OBS-QUERY-1 fact retrieval; OBS-QUERY-2 `persisted`; OBS-QUERY-3 `baseline_overlap` |
| Persistence and recurrence fact-like rows from HIST-LONG-8/9 and fact-native historical findings | `taxonomy` values such as persistence, stability, drift, replay-density, or source metric names; optional local fixtures in validation | OBS-QUERY-2 `persisted`, `recurred`, `dominant`; OBS-QUERY-4 persistence monitor |
| Stability drift / weakening / transition outputs | `taxonomy` / metric names and historical source phase selection | OBS-QUERY-2 `changed`, `weakened`, `transitioned`; OBS-QUERY-3 `baseline_deviation` and `persistent_weakening_live` when live facts exist |
| Taxonomy-weighted findings and ecosystem synthesis artifacts | Existing local artifacts for consumption adapters; supporting fact IDs and Evidence Reference identifiers | OBS-QUERY-4 ecosystem briefing / investigation queue; Daily Briefing Story Evolution and Evidence Reference drill-down |
| Regime Evidence Reference identifiers carried in payloads | `evidence_id` filter where DB-2 row ID, duplicate key, or payload `evidence_id` matches | OBS-QUERY-1 drill-down and OBS-QUERY-5 traceability validation |

## Contribution to OBS-QUERY
OBS-QUERY reads DB-2 facts and exposes them as retrieval envelopes, typed intelligence questions, historical/live comparisons, and consumption views. Historical Intelligence supplies phase IDs, metric names, taxonomy labels, persistence/drift/recurrence/stability payloads, fact IDs, Evidence Reference identifiers, artifact IDs, and run IDs that OBS-QUERY can retrieve and compare without synthesis or writes.

## Architectural ambiguities
- HIST-LONG-4 through HIST-LONG-7 live under `expectation_failure/real_data`, while HIST-LONG-8/9 and HIST-FACT/HIST-INTEL live under `history_long`; the architecture is coherent but split across packages.
- Some default paths point at generated `artifacts/` and `reports/`, which this source pack treats as contracts rather than inspecting generated content.
- Current evidence supports historical intelligence, comparison, and structural state description; it does not support labeling the stack as a forecasting system.
