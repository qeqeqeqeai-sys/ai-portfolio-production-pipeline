# LR6-EXP6 Replay Ecology Snapshot Export

## Objective
Build a deterministic, bounded replay ecology snapshot export layer that transforms LR6-EXP5 dashboard intelligence into reviewable, portable, and comparison-ready observation snapshots.

## Methodology
- Reused LR6-EXP5 dashboard view model as primary normalized source.
- Preserved evidence-linked panel structures from LR6-EXP4 trace wiring.
- Kept interpretation and caveat semantics aligned with LR6-EXP3 outputs.
- Maintained diagnostic boundary assumptions from LR6-EXP2 longitudinal observation.
- Applied deterministic construction, bounded sectioning, and stable serialization behaviors to support longitudinal use.

## Snapshot Design
The export builder composes a single deterministic artifact with:
- deterministic versioning marker
- deterministic seed marker
- metadata block
- JSON-safe payload block
- readable markdown block
- explicit experimental certification block

Snapshot sections are bounded and fixed:
- overview
- replay_drift
- propagation_evolution
- contradiction_ecology
- saturation_monoculture
- ecosystem_interaction
- entity_cluster_attribution
- caveats
- next_observation_priorities

## Metadata Design
Metadata includes:
- snapshot_id
- generated_at_marker
- source_phase
- source_modules
- ecosystem_universe_size
- dashboard_sections_included
- deterministic_comparison_key
- experimental_mode_only
- no_prediction
- no_trading
- no_governed_activation

All metadata fields are deterministic and carry no persistence or operational side effects.

## JSON Export Design
JSON payload is structured for comparison-readability:
- fixed section names
- stable nested composition
- bounded list sizes
- clipped text sizes
- evidence-linked references retained from LR6-EXP5/EXP4
- no raw metric dumping beyond summarized, panel-level observations

## Markdown Export Design
Markdown renderer provides:
- deterministic heading order
- deterministic section order
- bounded bullet rendering
- readable evidence reference exposure
- stable list formatting suitable for analyst review and diffing

## Comparison-Key Design
A deterministic comparison key is generated from stable ecology state fields:
- dominant ecology state
- maturity band
- confidence band
- most referenced clusters
- strongest contradiction contributors
- strongest propagation contributors
- saturation indicators (from saturation/monoculture observations)
- interaction indicators
- contradiction and propagation pathway surfaces

This key is explicitly designed to support future EXP6A longitudinal snapshot comparison workflows.

## Boundedness Review
Boundedness controls include:
- maximum section item count
- maximum text clip length
- stable de-duplication for key fragments
- capped caveat and next-priority lists
- deterministic truncation strategy with ellipsis

## Future EXP6A Comparison-Readiness
The snapshot export is comparison-ready through:
- deterministic structure
- deterministic key derivation
- stable metadata schema
- stable section ordering
- portable JSON + Markdown dual representation

## Caveats
- Snapshot output reflects observational replay ecology interpretation and not causal proof.
- Key comparison fields are intentionally compressed; deeper drift diagnostics should remain in upstream EXP2/EXP4 layers.

## Explicit Experimental-Only Statement
This module is experimental-only and does not activate governed LR6 operations.

## Explicit No-Prediction Statement
This module performs no prediction and contains no predictive recommendation logic.

## Explicit No-Trading Statement
This module performs no trading analysis and emits no trading instructions.

## Explicit No-Governed-Activation Statement
This module does not trigger or simulate governed LR6 activation pathways.
