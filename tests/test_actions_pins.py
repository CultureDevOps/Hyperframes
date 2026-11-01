"""Guard the reviewed GitHub Actions SHA pin allowlist (OPS-010)."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "scripts/actions-lock.json").read_text())
ACTIONS = LOCK["actions"]


class ActionPinsTests(unittest.TestCase):
    def test_manifest_has_expected_action_pins(self):
        self.assertEqual(LOCK["schema"], 1)
        self.assertEqual(set(ACTIONS), {
            "actions/checkout", "actions/setup-node",
            "actions/setup-python", "actions/upload-artifact",
        })
        for name, record in ACTIONS.items():
            with self.subTest(action=name):
                self.assertRegex(record["sha"], r"^[0-9a-f]{40}$")
                self.assertRegex(record["major"], r"^v[0-9]+$")

    def test_no_floating_or_unknown_action_refs(self):
        used = set()
        for path in sorted((ROOT / ".github/workflows").glob("*.yml")):
            content = path.read_text()
            matches = re.findall(
                r"(?m)^\s*-\s+uses:\s+([\w.-]+/[\w.-]+)@([^\s#]+)", content
            )
            self.assertGreater(len(matches), 0, path.name)
            for name, ref in matches:
                with self.subTest(file=path.name, action=name):
                    self.assertIn(name, ACTIONS)
                    self.assertEqual(ref, ACTIONS[name]["sha"])
                    used.add(name)
        self.assertEqual(used, set(ACTIONS))


if __name__ == "__main__":
    unittest.main()
