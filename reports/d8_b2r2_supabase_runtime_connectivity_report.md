# D8.B2-R2 Supabase Runtime Connectivity Report

## Objective
Resolve Supabase runtime credential visibility for D8.B2-R diagnostic read-only path and classify rerun readiness.

## Previous blocker
- SOURCE_BLOCKED_CLIENT_UNRESOLVED
- BLOCKED_CLIENT_CONFIGURATION

## Credential source audit
- Accepted env var names: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_ANON_KEY, SUPABASE_KEY
- Credential status: CREDENTIALS_MISSING
- URL present: False
- Key present: False
- URL source: missing
- Key source: missing

## Dashboard-vs-operator runtime comparison
- Dashboard credentials present: False
- Operator credentials present: False
- Runtime mismatch detected: False

## Connectivity probe result
- Client status: CLIENT_UNRESOLVED
- Connectivity status: READ_ONLY_CONNECTIVITY_NOT_ATTEMPTED
- Factory source: unavailable
- Blocked reason: CREDENTIALS_MISSING

## Recommendation
- BLOCKED_MISSING_CREDENTIALS

## Safe remediation instructions
1. Export SUPABASE_URL in the operator runtime (same shell/session that runs pytest/Codex).
2. Export exactly one key in operator runtime: SUPABASE_SERVICE_ROLE_KEY (preferred for full diagnostics) or SUPABASE_ANON_KEY or SUPABASE_KEY alias.
3. Re-run D8.B2-R diagnostics in read-only mode.
4. Do not place secrets into reports/logs.

## Governance confirmation
- Read-only diagnostics only.
- No write/update/delete/upsert/backfill execution in D8.B2-R2 path.
- No secret values emitted.

## Tests run/results
- See final operator output for command-level test status.
