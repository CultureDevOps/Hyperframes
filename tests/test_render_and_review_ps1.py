"""OPS-010: PowerShell local render/review is non-publishing and reproducible."""
from pathlib import Path
import re
import shutil
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "render_and_review.ps1"
CI = ROOT / ".github" / "workflows" / "verify.yml"


class PowerShellLocalReviewTests(unittest.TestCase):
    def test_all_compositions_and_original_soundtracks(self):
        content = SCRIPT.read_text(encoding="utf-8")
        for name, generator, duration in (
            ("intro", "generate_soundtrack.py", 10),
            ("nounours", "generate_teddy_soundtrack.py", 10),
            ("mvc", "generate_mvc_soundtrack.py", 35),
        ):
            with self.subTest(composition=name):
                self.assertRegex(content, rf"{name}\s*=\s*@\{{\s*Seconds\s*=\s*{duration};")
                self.assertIn(generator, content)
        self.assertIn("ValidateSet('intro', 'nounours', 'mvc')", content)

    def test_local_media_only_and_temp_files_cleaned(self):
        content = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("GetFullPath($OutputDirectory)", content)
        self.assertIn("StartsWith($repoPrefix", content)
        self.assertIn("Copy-Item -LiteralPath $muxed -Destination $final", content)
        self.assertIn("Move-Item -LiteralPath $muxed -Destination $final", content)
        self.assertIn("Initialize-PrivateWindowsDirectory -Path $outputFull", content)
        self.assertIn("Assert-PrivateWindowsAcl -Path $final -AllowInheritedChild", content)
        self.assertIn("Remove-Item -LiteralPath $temporary -Force", content)
        self.assertIn("private_visual_review.py", content)
        self.assertIn("verify_render.py", content)
        self.assertIn("'--no-install', 'hyperframes', 'lint'", content)
        self.assertIn("'--no-install', 'hyperframes', 'render'", content)
        self.assertIn("HYPERFRAMES_NO_UPDATE_CHECK", content)
        self.assertIn("'-map', '0:v:0', '-map', '1:a:0'", content)
        self.assertNotRegex(content, r"(?i)(?:upload-artifact|invoke-restmethod|invoke-webrequest|start-bitstransfer|github\.com/api|curl(?:\.exe)?\s)")
        self.assertNotIn("Publish-", content)

    def test_ntfs_fail_closed_guards_are_present(self):
        content = (ROOT / "scripts/private_output_acl.ps1").read_text(encoding="utf-8")
        self.assertIn("SetAccessRuleProtection($true, $false)", content)
        self.assertIn("S-1-5-18", content)
        self.assertIn("Assert-PrivateWindowsAcl", content)
        self.assertIn("DriveType", content)
        self.assertIn("ReparsePoint", content)
        self.assertIn("NTFS_UNSAFE", content)
        self.assertNotIn("icacls /grant Everyone", content)
        self.assertNotIn("Invoke-RestMethod", content)

    def test_pr_ci_exercises_power_shell_no_media_artifacts(self):
        workflow = CI.read_text(encoding="utf-8")
        self.assertIn("scripts/render_and_review.ps1", workflow)
        self.assertIn("-Composition intro -SkipInstall", workflow)
        self.assertIn("-Composition mvc -PlanOnly", workflow)
        self.assertIn("test-windows-local:", workflow)
        self.assertIn("tests/test_windows_acl.ps1", workflow)
        self.assertNotIn("upload-artifact", workflow)
        self.assertNotIn("upload_artifact", workflow)

    @unittest.skipUnless(shutil.which("pwsh"), "PowerShell Core unavailable on this host")
    def test_plan_mode_no_side_effects(self):
        command = [
            "pwsh", "-NoProfile", "-File", str(SCRIPT),
            "-Composition", "mvc", "-PlanOnly",
        ]
        process = subprocess.run(
            command, capture_output=True, text=True, timeout=30, cwd=ROOT, check=False
        )
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIn("PLAN_ONLY: composition=mvc seconds=35", process.stdout)
        self.assertIn("MEDIA_UPLOAD: disabled", process.stdout)


if __name__ == "__main__":
    unittest.main()
