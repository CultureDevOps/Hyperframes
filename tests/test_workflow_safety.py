"""Protect the review boundary: PRs must never render or upload video."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
RENDERS = ("render.yml", "nounours.yml", "mvc.yml")


class WorkflowSafetyTests(unittest.TestCase):
    def test_existing_render_workflows_run_on_main_only(self):
        for name in RENDERS:
            with self.subTest(name=name):
                contents = (ROOT / ".github" / "workflows" / name).read_text()
                self.assertIn("branches: [main]", contents)
                self.assertNotIn("pull_request:", contents)

    def test_pr_validation_workflow_does_not_render_or_upload(self):
        contents = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("pull_request:", contents)
        self.assertNotIn("hyperframes render", contents)
        self.assertNotIn("upload-artifact", contents)


if __name__ == "__main__":
    unittest.main()
