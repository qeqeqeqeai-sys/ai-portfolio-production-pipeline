# SEFI-G2 Ontology

This document defines the minimal SEFI-G2 core ontology.

## Core Objects

### Observation Fact

An evidence-backed, source-of-truth record describing something observed. Observation Facts support Expectation Expressions and are not Graph ML nodes in the core model.

### Expectation Expression

A concrete, contextual expression of an expectation derived from one or more Observation Facts. Expectation Expressions are the primary horizontal attachment point for Entities.

### Expectation

A durable interpretive claim realized by one or more Expectation Expressions.

### Theme

A higher-level intelligence area that groups related Expectations.

### Entity

A company, asset, sector, product, technology, geography, institution, or other referent affected by or participating in Expectation Expressions. Entities do not belong to themes or expectations.

### Evidence Source

The origin, document, feed, dataset, filing, article, transcript, or other source supporting an Observation Fact.

## Allowed Relationships

- Observation Fact supports Expectation Expression.
- Expectation Expression realizes Expectation.
- Expectation belongs to Theme.
- Expectation Expression affects Entity.
- Entity participates in multiple Expectation Expressions.
- Evidence Source supports Observation Fact.

## Expression-Entity Relationship Types

Expression-Entity edges may use only these initial relationship types:

- `benefits`
- `constrains`
- `enables`
- `inhibits`
- `supplies`
- `depends_on`
- `competes_with`
- `substitutes_for`
