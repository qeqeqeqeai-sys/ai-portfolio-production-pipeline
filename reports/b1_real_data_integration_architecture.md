# B1 Controlled Real Financial Data Integration Architecture

## Scope
This B1 layer introduces deterministic real-data integration scaffolding for the Structural Expectation-Failure Intelligence Platform (SEFI) without introducing trading, forecasting, optimization, or autonomous behavior.

## Deterministic Pipeline
Raw normalized inputs -> deterministic market snapshot -> deterministic fragility payload -> deterministic certification -> stable checksum envelope -> persistence-ready replay artifact.

## Architectural Guarantees
- Fixed entity universe: NVDA, AMD, TSM, ASML, AVGO, SMCI, MSFT, GOOGL, META, AMZN.
- Fixed benchmark universe: SOXX, QQQ, SPY.
- Fixed subsector mapping and deterministic ordering.
- Bounded score normalization (0-100) with clamping and explicit missing/invalid fallbacks.
- Immutable input handling via deep-copy and read-only lookup proxy support.
- No runtime network calls; no autonomous ingestion.
- Deterministic explanation templates and benchmark-relative interpretation labels.
- Replay-safe checksums derived from canonical JSON serialization.

## Additive Modules
- `b1_real_entity_registry.py`: fixed entities and immutable lookup proxy.
- `b1_benchmark_registry.py`: fixed deterministic benchmark registry.
- `b1_market_snapshot_builder.py`: bounded snapshot construction with missing-data visibility.
- `b1_fragility_payload_builder.py`: deterministic fragility interpretation.
- `b1_snapshot_certification.py`: certification envelope, replay checksum, degraded visibility.
