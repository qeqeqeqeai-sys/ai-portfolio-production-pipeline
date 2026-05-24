from transmission_layers.expectation_failure.expectation_intelligence.d8_b2r3_operator_rerun_harness import run_and_write_report


if __name__ == "__main__":
    payload = run_and_write_report()
    print(f"final_status={payload.get('final_status')}")
    print(f"recommendation={payload.get('recommendation')}")
