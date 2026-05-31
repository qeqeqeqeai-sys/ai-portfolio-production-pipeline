# SEFI-G2 Graph Design

SEFI-G2 separates the full intelligence graph from any ML projection graph.

## Full Intelligence Graph

The full intelligence graph may include Observation Facts and Evidence Sources for traceability. This graph preserves the evidence path from source material to Observation Fact, Expectation Expression, Expectation, and Theme.

## ML Projection Graph

The ML projection graph should exclude Observation Facts by default. Its default node set contains:

- Themes
- Expectations
- Expectation Expressions
- Entities

Fact-derived information should be aggregated into node and edge features rather than represented as raw fact nodes in the ML projection. This keeps the ML graph focused on meaningful intelligence structure instead of raw evidence volume.

Graph density and meaningful edges are preferred over raw graph size.

## Edge Features

Edges should include these feature fields when available:

- `strength`
- `confidence`
- `evidence_count`
- `persistence`
- `recency`
- `first_observed_at`
- `last_observed_at`
