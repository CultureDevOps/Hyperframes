"""The pinned toolchain must not silently drift away from the known-good baseline."""
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PinnedToolchainTests(unittest.TestCase):
    def test_package_and_lockfile_agree(self):
        package = json.loads((ROOT / "package.json").read_text())
        lock = json.loads((ROOT / "package-lock.json").read_text())
        self.assertEqual(package["devDependencies"]["hyperframes"], "0.8.221")
        self.assertEqual(lock["lockfileVersion"], 3)
        self.assertEqual(lock["packages"][""]["devDependencies"]["hyperframes"], "0.8.221")
        self.assertEqual(lock["packages"]["node_modules/hyperframes"]["version"], "0.8.221")

    def test_registry_integrity(self):
        lock = json.loads((ROOT / "package-lock.json").read_text())
        for package in lock["packages"].values():
            if "resolved" in package:
                self.assertTrue(package["resolved"].startswith("https://registry.npmjs.org/"))
                self.assertTrue(package.get("integrity"))

    def test_all_render_workflows_use_immutable_install(self):
        for name in ("render.yml", "nounours.yml", "mvc.yml"):
            with self.subTest(name=name):
                text = (ROOT / ".github" / "workflows" / name).read_text()
                self.assertIn("runs-on: ubuntu-24.04", text)
                self.assertIn("npm ci --no-audit --no-fund", text)
                self.assertNotIn("npm install --no-audit --no-fund", text)
                self.assertIn("HYPERFRAMES_NO_UPDATE_CHECK:", text)

    def test_pull_request_checks_install_without_render(self):
        text = (ROOT / ".github" / "workflows" / "verify.yml").read_text()
        self.assertIn("npm ci --no-audit --no-fund", text)
        self.assertIn("npx --no-install hyperframes --help", text)
        self.assertNotIn("hyperframes render", text)
        self.assertNotIn("upload-artifact", text)


if __name__ == "__main__":
    unittest.main()
