from transmission_layers.expectation_failure.expectation_intelligence.d8_b2_real_supabase_dry_run_retry import run_and_write_report


if __name__ == "__main__":
    payload = run_and_write_report()
    inv = payload.get("candidate_inventory") or {}
    plan = payload.get("plan") or {}
    print(f"replay_metadata_row_count={inv.get('replay_metadata_row_count')}")
    print(f"manifest_row_count={inv.get('manifest_row_count')}")
    print(f"accepted_candidates={inv.get('accepted_candidates')}")
    print(f"rejected_candidates={inv.get('rejected_candidates')}")
    print(f"duplicate_candidates={inv.get('duplicate_candidates')}")
    print(f"execution_status={plan.get('execution_status')}")
    print(f"recommendation={payload.get('recommendation')}")
