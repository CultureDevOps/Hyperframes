"""OPS-010: all workflow actions must use reviewed immutable SHA refs, no upload."""
import json
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
LOCK = json.loads((ROOT / "scripts/actions-lock.json").read_text(encoding="utf-8"))
ACTIONS = LOCK["actions"]


def allowed_action_ref(value):
    """Reject floating refs, unreviewed actions, local/docker actions and tags."""
    name, separator, sha = value.partition("@")
    return bool(
        separator
        and name in ACTIONS
        and re.fullmatch(r"[0-9a-f]{40}", sha)
        and sha == ACTIONS[name]["sha"]
    )


class ImmutableActionPinsTests(unittest.TestCase):
    def test_manifest_only_contains_current_read_only_actions(self):
        self.assertEqual(LOCK["schema"], 1)
        self.assertEqual(
            set(ACTIONS),
            {"actions/checkout", "actions/setup-node", "actions/setup-python"},
        )
        self.assertNotIn("actions/upload-artifact", ACTIONS)
        for name, record in ACTIONS.items():
            with self.subTest(name=name):
                self.assertRegex(record["sha"], r"^[0-9a-f]{40}$")
                self.assertRegex(record["major"], r"^v[0-9]+$")

    def test_every_workflow_action_has_a_reviewed_full_sha(self):
        used = set()
        paths = sorted((ROOT / ".github/workflows").glob("*.yml"))
        self.assertGreaterEqual(len(paths), 5)
        for path in paths:
            content = path.read_text(encoding="utf-8")
            steps = re.findall(r"(?m)^\s*(?:-\s+)?uses:\s*(\S+)", content)
            self.assertGreater(len(steps), 0, path.name)
            self.assertIn("\npermissions:\n  contents: read\n", content, path.name)
            for value in steps:
                with self.subTest(workflow=path.name, action=value):
                    self.assertTrue(allowed_action_ref(value), value)
                    used.add(value.partition("@")[0])
            # No artifact publishing step is authorized in this public repo.
            self.assertNotIn("upload-artifact", content)
            self.assertNotIn("upload_artifact", content)
        self.assertEqual(used, set(ACTIONS))

    def test_reject_floating_refs_unknown_actions_and_upload_actions(self):
        valid = "actions/checkout@" + ACTIONS["actions/checkout"]["sha"]
        self.assertTrue(allowed_action_ref(valid))
        for candidate in (
            "actions/checkout@v4",
            "actions/checkout@main",
            "actions/checkout@" + ACTIONS["actions/checkout"]["sha"][:12],
            "actions/checkout@" + "0" * 40,
            "actions/upload-artifact@ea165f8d65b6e75b540449e92b4886f43607fa02",
            "somebody/unverified@" + ACTIONS["actions/checkout"]["sha"],
            "docker://alpine:latest",
            "./.github/actions/local",
        ):
            with self.subTest(ref=candidate):
                self.assertFalse(allowed_action_ref(candidate))


if __name__ == "__main__":
    unittest.main()
