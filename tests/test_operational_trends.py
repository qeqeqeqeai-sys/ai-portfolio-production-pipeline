import json
import tempfile
import unittest
from pathlib import Path

from core.orchestration_guardrails.operational_trends import TREND_FILES, analyze_operational_trends


class OperationalTrendTests(unittest.TestCase):
    def test_empty_logs_directory_generates_all_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp) / "logs"
            result = analyze_operational_trends(logs_dir=str(logs), analysis_window_days=7)
            self.assertEqual(len(result["files_written"]), 5)
            for artifact in TREND_FILES.values():
                self.assertTrue((logs / artifact).exists())

    def test_malformed_json_is_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            logs = Path(tmp) / "logs"
            logs.mkdir(parents=True, exist_ok=True)
            (logs / "execution_context.json").write_text("{bad json", encoding="utf-8")
            (logs / "platform_runtime_summary.json").write_text(json.dumps({"runtime_seconds": 2222}), encoding="utf-8")

            analyze_operational_trends(logs_dir=str(logs))

            trend = json.loads((logs / "platform_operational_trend_summary.json").read_text(encoding="utf-8"))
            self.assertTrue(trend["advisory_warnings"])
            self.assertIn("analysis_window", trend)


if __name__ == "__main__":
    unittest.main()
