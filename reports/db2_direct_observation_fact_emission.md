# DB-2 — Direct Observation Fact Emission

## Objective
DB-2 adds a small reusable direct-emission layer for normalized observation facts. Future SEFI phases can build rows for `sefi_observation_facts` directly instead of producing large intermediate JSON and parsing it later.

## Design
The implementation lives in `transmission_layers/history_read_model/fact_emitter.py`. It is intentionally narrow:

- It builds deterministic insert dictionaries for the existing DB-1 `sefi_observation_facts` table.
- It validates rows fail-closed before any execute path can write.
- It keeps `payload_jsonb` bounded to the DB-1 8192-byte limit.
- It normalizes `entity_type`, `entity_id`, and `metric_name` into stable strings.
- It uppercases `entity_id` only when `entity_type == "symbol"`.
- It computes `duplicate_prevention_key` from stable row identity fields.

No schema changes are introduced.

## Helper APIs
- `build_fact_emission_context(...)` creates the explicit governance context with `enabled`, `dry_run`, `phase_id`, `phase_name`, `artifact_id`, and `run_id`.
- `should_emit_facts(context)` returns true only when emission is explicitly enabled and required context fields are present.
- `build_observation_fact_row(...)` builds and validates one deterministic row.
- `build_observation_fact_rows(context=..., observations=...)` converts metric observations into rows only when the context gate permits emission.
- `validate_observation_fact_row(row)` validates required fields, metric type safety, payload bounds, window type safety, and duplicate-key determinism.
- `emit_observation_facts(client, rows, dry_run=True)` validates rows and either returns a dry-run summary or performs append-only inserts through an injected client.

## Dry-run / Execute Behavior
Dry-run is the default. In dry-run mode, rows are validated and counted, but the Supabase client is not touched. Execute mode requires `dry_run=False`; it performs only:

```text
client.table("sefi_observation_facts").insert(rows).execute()
```

There is no upsert, update, delete, RPC, provider call, replay execution, or client construction.

## Governance Boundary
DB-2 is a construction and append-only emission helper. It does not fetch provider data, call FMP, perform live ingestion, run replay execution, create predictions, execute trades, or modify topology persistence. Inputs must already be governed phase observations supplied by future callers.

## How HIST-LONG-8 Should Use It
HIST-LONG-8 should:

1. Build a context with `enabled=True` only after its own phase governance gate passes.
2. Keep `dry_run=True` for certification and preview runs.
3. Pass bounded, already-derived metric observations to `build_observation_fact_rows(...)`.
4. Review dry-run counts and sample rows without writing.
5. Use `emit_observation_facts(client, rows, dry_run=False)` only for approved append-only persistence.

## Certification
DB-2 certifies:

- No prediction.
- No trading.
- No live ingestion.
- No FMP/provider/API calls.
- No replay execution.
- No topology persistence changes.
- No schema changes.
- No modification to existing HIST-LONG artifacts.
