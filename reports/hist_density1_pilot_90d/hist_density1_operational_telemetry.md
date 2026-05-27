# HIST-DENSITY-1 Operational Telemetry

## Telemetry goals
- Provide deterministic, bounded progress checkpoints during long HIST-DENSITY-1/OPS-HIST-1 runs.
- Allow operators to distinguish healthy progress from hangs in GitHub Actions logs.
- Expose endpoint fallback behavior and date reconciliation quality at bounded cadence.

## Bounded telemetry philosophy
- Text-only, deterministic key-value lines.
- No per-symbol spam, payload dumps, secrets, or API key output.
- No persistent telemetry store, orchestration, streaming, or external observability dependencies.

## Snapshot telemetry design
- OPS-HIST-1 emits snapshot progress every `progress_interval` snapshots (bounded to 1..20).
- Snapshot lines include: completed snapshot counter, date, elapsed seconds, normalized/partial/failed counts.
- Approximate ETA is emitted from a rolling average snapshot duration.

## Endpoint telemetry design
- OPS-HIST-1 aggregates endpoint success and failure counters across snapshots.
- Progress checkpoints include bounded endpoint family success counts and failure reasons.
- Endpoint telemetry never emits raw payloads, URLs containing credentials, or secrets.

## ETA approximation design
- ETA uses a simple rolling average over observed snapshot durations.
- Reports remaining snapshot count and estimated remaining minutes.
- Designed for bounded operational awareness, not predictive modeling.

## GitHub Actions compatibility
- Telemetry uses `print(..., flush=True)` so checkpoints are progressively visible in CI logs.
- Emission cadence is bounded and deterministic to prevent log flooding.

## Governance confirmation
- Observational-only governance boundaries remain unchanged.
- No Supabase writes, repo writeback, orchestration engines, streaming services, replay activation, or prediction/trading pathways were added.

## Why streaming/orchestration systems were not added
- Requirement was bounded operational visibility, not runtime architecture escalation.
- Deterministic checkpoint logging satisfies operator needs with minimal complexity and risk.
