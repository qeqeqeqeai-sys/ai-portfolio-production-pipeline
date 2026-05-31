# SEFI-G2 Database Schema Draft

This is a conceptual draft only. Do not treat this document as a SQL migration or implementation contract.

## `observation_facts`

Purpose: stores evidence-backed source-of-truth observations.

Key fields: `id`, `fact_type`, `statement`, `observed_at`, `source_id`, `confidence`, `created_at`.

## `expectation_expressions`

Purpose: stores concrete expressions of expectations supported by Observation Facts.

Key fields: `id`, `expression`, `context`, `time_horizon`, `confidence`, `created_at`, `updated_at`.

## `expectations`

Purpose: stores durable interpretive claims realized by Expectation Expressions.

Key fields: `id`, `title`, `description`, `status`, `theme_id`, `created_at`, `updated_at`.

## `themes`

Purpose: stores higher-level intelligence areas that group Expectations.

Key fields: `id`, `name`, `description`, `created_at`, `updated_at`.

## `entities`

Purpose: stores companies, assets, sectors, products, technologies, geographies, institutions, or other referents.

Key fields: `id`, `name`, `entity_type`, `canonical_identifier`, `created_at`, `updated_at`.

## `expression_entity_edges`

Purpose: stores typed relationships between Expectation Expressions and Entities.

Key fields: `id`, `expectation_expression_id`, `entity_id`, `relationship_type`, `strength`, `confidence`, `evidence_count`, `persistence`, `recency`, `first_observed_at`, `last_observed_at`.

## `evidence_sources`

Purpose: stores source metadata used to support Observation Facts.

Key fields: `id`, `source_type`, `title`, `uri`, `publisher`, `published_at`, `retrieved_at`, `created_at`.
