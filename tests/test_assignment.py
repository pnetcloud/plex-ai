"""Read-only assignment validation, including CLI and malformed input."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/plex/scripts/check_assignment.py"
SPEC = importlib.util.spec_from_file_location("plex_assignment", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
TEMPLATE = ROOT / "skills/plex/assets/assignment.json.template"


class AssignmentTests(unittest.TestCase):
    def setUp(self):
        self.assignment = json.loads(TEMPLATE.read_text())
        self.snapshot = {"roles": ["pm", "dev", "reviewer"]}

    def test_supported_modes_and_criterion_counts(self):
        for mode in ("normal", "plan", "goal"):
            for count in (1, 3, 5):
                data = copy.deepcopy(self.assignment)
                data["acceptance"] *= count
                data["execution"]["mode"] = mode
                with self.subTest(mode=mode, count=count):
                    self.assertEqual(MODULE.validate(data, self.snapshot), [])
        self.assignment["scope"]["write"] = []
        self.assignment["inputs"] = []
        self.assignment["dependencies"] = []
        self.assertEqual(MODULE.validate(self.assignment, self.snapshot), [])

    def test_unknown_and_inactive_native_roles_are_rejected(self):
        for role in ("dev", "worker", "plex-po", "plex-old", [], None):
            self.assignment["role"] = role
            with self.subTest(role=role):
                self.assertTrue(MODULE.validate(self.assignment, self.snapshot))

    def test_required_fields_and_wrong_types(self):
        for field in self.assignment:
            data = copy.deepcopy(self.assignment)
            del data[field]
            with self.subTest(missing=field):
                self.assertTrue(MODULE.validate(data, self.snapshot))
        for field, value in (
            ("outcome", " "), ("reference", False), ("inputs", "file.py"),
            ("dependencies", [""]), ("scope", []), ("scope", {"write": [1], "exclude": []}),
            ("acceptance", []), ("acceptance", [{}]), ("acceptance", ["passes"]),
            ("acceptance", [{"criterion": "Works", "check": " "}]),
            ("acceptance", self.assignment["acceptance"] * 6),
            ("execution", {"mode": "auto", "reason": "clear"}),
            ("execution", {"mode": "normal", "reason": ""}),
        ):
            data = {**self.assignment, field: value}
            with self.subTest(field=field, value=value):
                self.assertTrue(MODULE.validate(data, self.snapshot))

    def test_only_planning_can_resolve_specialist_decisions(self):
        for status in ("ready", "needs-specialist", "blocked", "unknown", None):
            for mode in ("normal", "plan", "goal"):
                data = copy.deepcopy(self.assignment)
                data["readiness"] = status
                data["execution"]["mode"] = mode
                valid = status == "ready" or (status == "needs-specialist" and mode == "plan")
                with self.subTest(status=status, mode=mode):
                    self.assertEqual(not MODULE.validate(data, self.snapshot), valid)

    def test_goal_needs_no_budget_even_with_legacy_snapshot(self):
        self.assignment["execution"]["mode"] = "goal"
        for legacy in ({}, {"subagent_token_budget": 50000}, {"subagent_token_budget": "retired"}):
            with self.subTest(legacy=legacy):
                self.assertEqual(MODULE.validate(self.assignment, {**self.snapshot, **legacy}), [])

    def test_non_object_input_and_invalid_snapshot(self):
        for data in (None, [], "task", 7):
            self.assertTrue(MODULE.validate(data, self.snapshot))
        for snapshot in (None, [], {}, {"roles": []}, {"roles": "dev"}, {"roles": [None]}):
            self.assertTrue(MODULE.validate(self.assignment, snapshot))

    def test_cli_errors_are_json_and_no_files_are_changed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            snapshot = root / "resolved.json"
            snapshot.write_text(json.dumps(self.snapshot))
            baseline = snapshot.read_bytes()
            for raw, expected in ((json.dumps(self.assignment), 0), ("{bad", 1), ("[]", 1)):
                result = subprocess.run(
                    [sys.executable, str(SCRIPT), "--resolved", str(snapshot)],
                    input=raw, capture_output=True, text=True, cwd=root,
                )
                with self.subTest(raw=raw):
                    self.assertEqual(result.returncode, expected, result.stderr)
                    output = json.loads(result.stdout)
                    self.assertEqual(output["status"], "valid" if expected == 0 else "invalid")
                    self.assertEqual(snapshot.read_bytes(), baseline)
                    self.assertEqual(list(root.iterdir()), [snapshot])
            snapshot.unlink()
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--resolved", str(snapshot)],
                input=json.dumps(self.assignment), capture_output=True, text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(json.loads(result.stdout)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
