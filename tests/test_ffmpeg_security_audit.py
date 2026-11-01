"""Policy tests: guard FFmpeg version agreement and timely security review."""
import copy
from datetime import date
import json
from pathlib import Path
import unittest

from scripts.audit_ffmpeg_security import POLICY, ROOT, validate


class FFmpegPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(POLICY.read_text())

    def test_manifest_agrees_with_pinned_workflows(self):
        errors, warnings = validate(self.data, root=ROOT, today=date(2026, 11, 1))
        self.assertEqual(errors, [])
        self.assertTrue(any("USN-8915-1" in warning for warning in warnings))

    def test_mismatch_detected(self):
        modified = copy.deepcopy(self.data)
        modified["apt_package"] = "7:6.1.1-3ubuntu5+esm15"
        errors, _ = validate(modified, root=ROOT, today=date(2026, 11, 1))
        self.assertTrue(any("runtime" in e.lower() or "workflow" in e.lower() or "version" in e.lower() for e in errors))

    def test_expired_review_fails_closed(self):
        errors, _ = validate(self.data, root=ROOT, today=date(2026, 11, 16))
        self.assertTrue(any("overdue" in e.lower() for e in errors))

    def test_cannot_silence_vendor_advisory(self):
        modified = copy.deepcopy(self.data)
        modified["security_status"] = "secure"
        errors, _ = validate(modified, root=ROOT, today=date(2026, 11, 1))
        self.assertTrue(any("silently" in e.lower() for e in errors))

    def test_ffmpeg_audit_is_in_required_pr_test_job(self):
        workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("run: python3 scripts/audit_ffmpeg_security.py", workflow)
        self.assertNotIn("continue-on-error: true", workflow)


if __name__ == "__main__":
    unittest.main()
