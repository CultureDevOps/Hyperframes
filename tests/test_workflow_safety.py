"""Protect manual video publishing: no render runs on push or on a PR."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
RENDERS = ("render.yml", "nounours.yml", "mvc.yml")


class WorkflowSafetyTests(unittest.TestCase):
    def test_render_workflows_require_manual_dispatch(self):
        for name in RENDERS:
            with self.subTest(name=name):
                contents = (ROOT / ".github" / "workflows" / name).read_text()
                self.assertRegex(contents, r"(?m)^on:\n  workflow_dispatch:\n")
                self.assertNotRegex(contents, r"(?m)^  (?:push|pull_request|schedule|workflow_run):")
                self.assertIn("upload_artifact:", contents)
                self.assertIn("type: boolean", contents)
                self.assertIn("default: false", contents)

    def test_artifact_upload_requires_opt_in(self):
        for name in RENDERS:
            with self.subTest(name=name):
                contents = (ROOT / ".github" / "workflows" / name).read_text()
                self.assertEqual(contents.count("uses: actions/upload-artifact@v4"), 1)
                self.assertEqual(contents.count("if: ${{ inputs.upload_artifact == true }}"), 1)
                self.assertNotIn("**/*.mp4", contents)
                self.assertIn("retention-days: 3", contents)

    def test_intro_lint_required_and_css_only_timeline_opt_out(self):
        contents = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("compositions/culturedevops/intro/**", contents)
        self.assertIn("run: npx --no-install hyperframes lint", contents)
        self.assertNotIn("continue-on-error: true", contents)
        html = (ROOT / "compositions" / "culturedevops" / "intro" / "index.html").read_text()
        self.assertIn('<main class="stage" data-no-timeline', html)
        self.assertNotIn("window.__timelines", html)

    def test_all_css_only_compositions_are_declared(self):
        for name in ("intro", "mvc", "nounours"):
            with self.subTest(name=name):
                html = (ROOT / "compositions" / "culturedevops" / name / "index.html").read_text()
                self.assertIn('<main class="stage" data-no-timeline', html)
                self.assertNotIn("window.__timelines", html)

    def test_ci_lints_all_three_without_bypass(self):
        contents = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        for name in ("intro", "mvc", "nounours"):
            self.assertIn("compositions/culturedevops/" + name + "/**", contents)
            self.assertIn("working-directory: compositions/culturedevops/" + name, contents)
        self.assertEqual(contents.count("run: npx --no-install hyperframes lint"), 3)
        self.assertNotIn("continue-on-error: true", contents)
        self.assertNotIn("lint || true", contents)

    def test_other_compositions_have_ephemeral_smoke_without_upload(self):
        contents = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("smoke-other:", contents)
        self.assertIn("composition: nounours", contents)
        self.assertIn("composition: mvc", contents)
        self.assertNotIn("upload-artifact", contents)
        self.assertNotIn("upload_artifact", contents)

    def test_pr_smoke_is_ephemeral_without_upload(self):
        contents = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("pull_request:", contents)
        self.assertNotIn("  push:", contents)
        self.assertIn("smoke-intro:", contents)
        self.assertIn("if: github.event_name == 'pull_request'", contents)
        self.assertIn("needs: test", contents)
        self.assertIn("hyperframes render --output", contents)
        self.assertIn("scripts/verify_render.py", contents)
        self.assertNotIn("upload-artifact", contents)
        self.assertNotIn("upload_artifact", contents)
        self.assertNotIn("workflow_run:", contents)


if __name__ == "__main__":
    unittest.main()
