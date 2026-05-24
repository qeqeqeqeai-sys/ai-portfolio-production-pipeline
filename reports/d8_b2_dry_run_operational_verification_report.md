# D8.B2 Dry-Run Operational Verification Report

```json
{
  "client_resolved": false,
  "replay_rows": 0,
  "manifest_rows": 0,
  "history_rows": 0,
  "candidates": 0,
  "gov": {
    "status": "GOVERNANCE_OK",
    "dry_run": true,
    "allowed_tables": [
      "dashboard_replay_metadata_records"
    ],
    "blocking_reasons": [],
    "governance_checksum": "84a68db89bf864fe5113d37031f722308e58d3ee359e16b8370df66b7a83d6e4"
  },
  "validation": {
    "accepted_candidates": [],
    "rejected_candidates": [],
    "duplicate_ids": [],
    "candidate_validation_checksum": "039c31b301edea7a5a0b8fcfb84a69d88c34ef6070bf07141fb0f639751fe079"
  },
  "plan": {
    "d8_b2_version": "d8_b2_controlled_replay_backfill_execution_v1",
    "dry_run": true,
    "governance_status": "GOVERNANCE_OK",
    "candidate_count": 0,
    "accepted_count": 0,
    "rejected_count": 0,
    "duplicate_count": 0,
    "estimated_inserted_count": 0,
    "target_tables": [
      "dashboard_replay_metadata_records"
    ],
    "checksum_manifest": {
      "b1_backfill_plan_checksum": "5f3bea5f4fd93d170a76085107e4e42c2113560732d8c0bbad8366f82a62dddc",
      "candidate_validation_checksum": "039c31b301edea7a5a0b8fcfb84a69d88c34ef6070bf07141fb0f639751fe079",
      "governance_checksum": "84a68db89bf864fe5113d37031f722308e58d3ee359e16b8370df66b7a83d6e4"
    },
    "execution_status": "BACKFILL_DRY_RUN_READY",
    "candidate_validation": {
      "accepted_candidates": [],
      "rejected_candidates": [],
      "duplicate_ids": [],
      "candidate_validation_checksum": "039c31b301edea7a5a0b8fcfb84a69d88c34ef6070bf07141fb0f639751fe079"
    },
    "execution_plan_checksum": "593fec7c64ee30f4422fb51b6b6b0fd03a9b070f0f7dd1dbd8d8e76b1b993688"
  },
  "execution": {
    "status": "BACKFILL_DRY_RUN_ONLY",
    "plan": {
      "d8_b2_version": "d8_b2_controlled_replay_backfill_execution_v1",
      "dry_run": true,
      "governance_status": "GOVERNANCE_OK",
      "candidate_count": 0,
      "accepted_count": 0,
      "rejected_count": 0,
      "duplicate_count": 0,
      "estimated_inserted_count": 0,
      "target_tables": [
        "dashboard_replay_metadata_records"
      ],
      "checksum_manifest": {
        "b1_backfill_plan_checksum": "5f3bea5f4fd93d170a76085107e4e42c2113560732d8c0bbad8366f82a62dddc",
        "candidate_validation_checksum": "039c31b301edea7a5a0b8fcfb84a69d88c34ef6070bf07141fb0f639751fe079",
        "governance_checksum": "84a68db89bf864fe5113d37031f722308e58d3ee359e16b8370df66b7a83d6e4"
      },
      "execution_status": "BACKFILL_DRY_RUN_READY",
      "candidate_validation": {
        "accepted_candidates": [],
        "rejected_candidates": [],
        "duplicate_ids": [],
        "candidate_validation_checksum": "039c31b301edea7a5a0b8fcfb84a69d88c34ef6070bf07141fb0f639751fe079"
      },
      "execution_plan_checksum": "593fec7c64ee30f4422fb51b6b6b0fd03a9b070f0f7dd1dbd8d8e76b1b993688"
    },
    "audit_manifest": {
      "candidate_ids": [],
      "accepted_ids": [],
      "rejected_ids_with_reasons": [],
      "duplicate_ids": [],
      "target_table_inventory": [
        "dashboard_replay_metadata_records"
      ],
      "checksum_lineage": {
        "b1_backfill_plan_checksum": "5f3bea5f4fd93d170a76085107e4e42c2113560732d8c0bbad8366f82a62dddc",
        "candidate_validation_checksum": "039c31b301edea7a5a0b8fcfb84a69d88c34ef6070bf07141fb0f639751fe079",
        "governance_checksum": "84a68db89bf864fe5113d37031f722308e58d3ee359e16b8370df66b7a83d6e4"
      },
      "governance_flags": {
        "blocking_reasons": [],
        "status": "GOVERNANCE_OK"
      },
      "dry_run": true,
      "write_count": 0,
      "manifest_checksum": "99a615742cf7bb6910324b7928452e9a2b7792269b87b513ee937d219d77cb6a"
    },
    "inserted_count": 0,
    "execution_checksum": "2067e42fcf171fc328ec7825bd373000184f0f52cd64bdf30097bcff9a180ce5"
  },
  "lineage_gaps": 0,
  "evidence_gaps": 0,
  "checksum_gaps": 0,
  "contradiction_gaps": 0,
  "theme_gaps": 0,
  "readback": {
    "status": "READBACK_VERIFICATION_DRY_RUN",
    "no_write_governance": true,
    "before": {
      "run_count": 0,
      "unique_run_count": 0,
      "replay_continuity_score": 0.0,
      "evidence_reinforcement_score": 0.0,
      "linkage_density": 0.0,
      "semantic_persistence_count": 0,
      "contradiction_continuity_count": 0,
      "strongest_evidence_availability": 0,
      "explainability_confidence": 0.0,
      "duplicate_run_count": 0
    },
    "after": {
      "run_count": 0,
      "unique_run_count": 0,
      "replay_continuity_score": 0.0,
      "evidence_reinforcement_score": 0.0,
      "linkage_density": 0.0,
      "semantic_persistence_count": 0,
      "contradiction_continuity_count": 0,
      "strongest_evidence_availability": 0,
      "explainability_confidence": 0.0,
      "duplicate_run_count": 0
    },
    "deltas": {
      "replay_continuity_score_delta": 0.0,
      "evidence_reinforcement_score_delta": 0.0,
      "linkage_density_delta": 0.0,
      "semantic_persistence_count_delta": 0.0,
      "contradiction_continuity_count_delta": 0.0,
      "strongest_evidence_availability_delta": 0.0,
      "explainability_confidence_delta": 0.0
    },
    "sparse_history": true,
    "duplicate_replay_ids_detected": false
  }
}
```
