import tempfile
import unittest
from pathlib import Path

from scripts.lint_workflow_observability import _lint_workflow


class WorkflowObservabilityLintTests(unittest.TestCase):
    def _lint(self, workflow_text: str):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workflow = root / ".github" / "workflows" / "test.yml"
            workflow.parent.mkdir(parents=True, exist_ok=True)
            workflow.write_text(workflow_text, encoding="utf-8")
            return _lint_workflow(workflow, root)

    def test_single_line_tier_3e_and_3f_detected(self):
        result = self._lint(
            "\n".join(
                [
                    "python -m core.orchestration_guardrails.cli aggregate operational-summary --context-file logs/execution_context.json",
                    "python -m core.orchestration_guardrails.cli trend analyze --logs-dir logs",
                    "uses: actions/upload-artifact@v4",
                ]
            )
        )
        self.assertTrue(result.tier_3e_present)
        self.assertTrue(result.tier_3f_present)
        self.assertTrue(result.artifact_upload_present)
        self.assertEqual(result.errors, ())

    def test_multiline_tier_3e_with_split_operational_summary_detected(self):
        result = self._lint(
            "\n".join(
                [
                    "python -m core.orchestration_guardrails.cli aggregate \\",
                    "  operational-summary \\",
                    "  --context-file logs/execution_context.json",
                    "python -m core.orchestration_guardrails.cli trend analyze --logs-dir logs",
                    "uses: actions/upload-artifact@v4",
                ]
            )
        )
        self.assertTrue(result.tier_3e_present)
        self.assertEqual(result.errors, ())

    def test_multiline_tier_3e_with_split_cli_invocation_detected(self):
        result = self._lint(
            "\n".join(
                [
                    "python -m core.orchestration_guardrails.cli \\",
                    "  aggregate operational-summary --context-file logs/execution_context.json",
                    "python -m core.orchestration_guardrails.cli trend analyze --logs-dir logs",
                    "uses: actions/upload-artifact@v4",
                ]
            )
        )
        self.assertTrue(result.tier_3e_present)
        self.assertEqual(result.errors, ())

    def test_multiline_tier_3f_detected(self):
        result = self._lint(
            "\n".join(
                [
                    "python -m core.orchestration_guardrails.cli aggregate operational-summary --context-file logs/execution_context.json",
                    "python -m core.orchestration_guardrails.cli trend \\",
                    "  analyze --logs-dir logs",
                    "uses: actions/upload-artifact@v4",
                ]
            )
        )
        self.assertTrue(result.tier_3f_present)
        self.assertEqual(result.errors, ())


if __name__ == "__main__":
    unittest.main()
