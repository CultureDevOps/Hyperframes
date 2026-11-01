"""Regression guard: manually triggered legacy renders must not publish videos."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
FILES = ("render.yml", "nounours.yml", "mvc.yml")
CHECKOUT = "actions/checkout@11d5960a326750d5838078e36cf38b85af677262"
SETUP_NODE = "actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020"

class ManualRenderSafetyTests(unittest.TestCase):
    def test_manual_only_no_upload_and_pinned_actions(self):
        for name in FILES:
            with self.subTest(workflow=name):
                source = (ROOT / ".github" / "workflows" / name).read_text(encoding="utf-8")
                self.assertIn("\non:\n  workflow_dispatch:\n", source)
                self.assertNotRegex(source, r"(?m)^  (push|schedule|pull_request|workflow_run|workflow_call):")
                self.assertNotIn("upload-artifact", source)
                self.assertNotIn("upload_artifact", source)
                self.assertIn(CHECKOUT, source)
                self.assertIn(SETUP_NODE, source)
                self.assertIn("\npermissions:\n  contents: read\n", source)

if __name__ == "__main__":
    unittest.main()
