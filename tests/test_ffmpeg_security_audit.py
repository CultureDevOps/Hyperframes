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

    def test_mp4_cve_is_explicitly_open_and_vendor_grounded(self):
        errors, warnings = validate(self.data, root=ROOT, today=date(2026, 11, 1))
        self.assertEqual(errors, [])
        self.assertTrue(any("CVE-2026-107678" in warning for warning in warnings))
        evidence = self.data["open_cve_evidence"]
        self.assertEqual(evidence["status"], "unresolved")
        self.assertEqual(evidence["debian"]["status"], "vulnerable")
        self.assertEqual(evidence["ubuntu"]["noble_status"], "needs_evaluation")

    def test_cannot_mark_mp4_cve_or_debian_baseline_fixed(self):
        for path, replacement in (
            (("open_cve_evidence", "status"), "fixed"),
            (("open_cve_evidence", "debian", "status"), "fixed"),
            (("open_cve_evidence", "debian", "apt_package"), "7:9.9.9"),
            (("open_cve_evidence", "ubuntu", "noble_status"), "fixed"),
        ):
            with self.subTest(path=path):
                changed = copy.deepcopy(self.data)
                field = changed
                for key in path[:-1]:
                    field = field[key]
                field[path[-1]] = replacement
                errors, _ = validate(changed, root=ROOT, today=date(2026, 11, 1))
                self.assertTrue(errors, path)

    def test_ffmpeg_audit_is_in_required_pr_test_job(self):
        workflow = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("run: python3 scripts/audit_ffmpeg_security.py", workflow)
        self.assertNotIn("continue-on-error: true", workflow)


if __name__ == "__main__":
    unittest.main()
