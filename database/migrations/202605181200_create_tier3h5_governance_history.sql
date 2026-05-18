-- Tier 3H.5 Phase 4C additive, advisory-only governance history persistence.
-- These append-oriented tables store deterministic archived summaries only; they do
-- not enforce, remediate, override canonical identity, or mutate scoring/confidence.

CREATE TABLE IF NOT EXISTS tier3h5_governance_incident_history (
    incident_history_id TEXT PRIMARY KEY,
    incident_id TEXT,
    incident_key TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    signal TEXT NOT NULL,
    entity TEXT NOT NULL,
    incident_hash TEXT NOT NULL,
    incident_lifecycle_hash TEXT NOT NULL,
    replay_mode TEXT NOT NULL DEFAULT 'advisory_only',
    enforcement_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tier3h5_governance_escalation_history (
    escalation_history_id TEXT PRIMARY KEY,
    escalation_status TEXT NOT NULL,
    governance_review_recommended BOOLEAN NOT NULL DEFAULT FALSE,
    escalation_summary_hash TEXT,
    escalation_history_hash TEXT NOT NULL,
    replay_mode TEXT NOT NULL DEFAULT 'advisory_only',
    enforcement_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tier3h5_governance_watchlist_history (
    watchlist_history_id TEXT PRIMARY KEY,
    watchlist_name TEXT NOT NULL,
    watchlist_count INTEGER NOT NULL DEFAULT 0,
    watchlist_evolution_hash TEXT NOT NULL,
    replay_mode TEXT NOT NULL DEFAULT 'advisory_only',
    enforcement_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tier3h5_governance_trend_history (
    governance_trend_hash TEXT PRIMARY KEY,
    governance_trend_status TEXT NOT NULL,
    escalation_trend_status TEXT NOT NULL,
    replay_stability_trend TEXT NOT NULL,
    lineage_stability_trend TEXT NOT NULL,
    replay_mode TEXT NOT NULL DEFAULT 'advisory_only',
    enforcement_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tier3h5_governance_continuity_history (
    continuity_hash TEXT PRIMARY KEY,
    historical_continuity_status TEXT NOT NULL,
    governance_history_depth INTEGER NOT NULL DEFAULT 0,
    persistent_incident_count INTEGER NOT NULL DEFAULT 0,
    recurring_incident_count INTEGER NOT NULL DEFAULT 0,
    transient_incident_count INTEGER NOT NULL DEFAULT 0,
    replay_mode TEXT NOT NULL DEFAULT 'advisory_only',
    enforcement_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
