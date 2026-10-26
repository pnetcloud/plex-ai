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

    def test_cli_reads_legacy_json_and_redirects_after_toml_migration(self):
        with tempfile.TemporaryDirectory() as temp:
            legacy = Path(temp) / "resolved.json"
            legacy.write_text(json.dumps(self.snapshot))
            for migrated in (False, True):
                if migrated:
                    legacy.unlink()
                    legacy.with_suffix(".toml").write_text('roles = ["pm", "dev", "reviewer"]\n')
                result = subprocess.run([sys.executable, str(SCRIPT), "--resolved", str(legacy)],
                                        input=json.dumps(self.assignment), capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "valid")

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
            snapshot = root / "resolved.toml"
            snapshot.write_text('roles = ["pm", "dev", "reviewer"]\n')
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


class ResponseTests(unittest.TestCase):
    def setUp(self):
        self.assignment = json.loads(TEMPLATE.read_text())
        self.response = json.loads((ROOT / "skills/plex/assets/response.json.template").read_text())
        self.snapshot = {"roles": ["pm", "po", "dev", "architect", "ux", "reviewer", "qa"]}

    def check(self, response=None, assignment=None):
        return MODULE.validate_response(
            self.response if response is None else response,
            self.assignment if assignment is None else assignment, self.snapshot)

    def test_all_roles_can_return_without_files(self):
        for role in self.snapshot["roles"]:
            self.assignment["role"] = self.response["role"] = "plex-" + role
            self.assertEqual(self.check(), [])
        self.response["findings"] = ["A demonstrated implementation defect"]
        self.assertEqual(self.check(), [])  # A completed review need not approve the code.

    def test_identity_and_current_revision(self):
        for key, values in {"assignment": ["another", "", None],
                            "revision": [0, 2, True, 1.0, "1"],
                            "role": ["dev", "plex-old", "plex-pm", []]}.items():
            for value in values:
                with self.subTest(key=key, value=value):
                    self.assertTrue(self.check({**self.response, key: value}))
        old = {k: v for k, v in self.assignment.items() if k not in ("assignment", "revision")}
        self.assertEqual(MODULE.validate(old, self.snapshot), [])
        self.assertTrue(self.check(assignment=old))

    def test_complete_requires_all_evidence_and_no_open_request(self):
        for field in self.response:
            data = copy.deepcopy(self.response)
            del data[field]
            self.assertTrue(self.check(data), field)
        for criteria in ([], None, [None], [{"index": 1, "state": "pending", "evidence": []}],
                         [{"index": 1, "state": "failed", "evidence": ["failure"]}],
                         [{"index": 1, "state": "passed", "evidence": []}],
                         self.response["criteria"] * 2):
            self.assertTrue(self.check({**self.response, "criteria": criteria}))
        for index in (True, 1.0, 0, 2, "1", [], None):
            data = copy.deepcopy(self.response)
            data["criteria"][0]["index"] = index
            self.assertTrue(self.check(data))
        for field in ("request", "blocker"):
            self.assertTrue(self.check({**self.response, field: {}}))
        self.assignment["acceptance"] *= 2
        self.assertTrue(self.check())
        self.response["criteria"].append({"index": 2, "state": "passed", "evidence": ["check 2"]})
        self.assertEqual(self.check(), [])

    def test_progress_is_a_delta_without_completion_requirements(self):
        data = {key: self.response[key] for key in ("assignment", "revision", "role", "summary")}
        data.update(status="progress", evidence=["check A passed at revision X"], next="Run check B")
        self.assertEqual(self.check(data), [])
        for field in ("evidence", "next"):
            invalid = dict(data)
            del invalid[field]
            self.assertTrue(self.check(invalid))
        data["criteria"] = [{"index": 1, "state": "pending", "evidence": []}]
        self.assertEqual(self.check(data), [])

    def test_decision_request_and_blocker_are_distinct(self):
        data = {key: self.response[key] for key in ("assignment", "revision", "role", "summary")}
        request = {"kind": "technical", "question": "Which contract applies?",
                   "attempted": ["Compared spec and public API"], "recommendation": "Preserve public API"}
        data.update(status="needs-decision", request=request, next="Continue after architect decision")
        self.assertEqual(self.check(data), [])
        for field in request:
            invalid = copy.deepcopy(data)
            del invalid["request"][field]
            self.assertTrue(self.check(invalid))
        self.assertTrue(self.check({**data, "request": {**request, "kind": "unknown"}}))
        blocker = {"constraint": "Required permission denied", "evidence": ["Tool denial"],
                   "resume": "Authority owner grants required access"}
        data = {**data, "status": "blocked", "blocker": blocker}
        del data["request"]
        self.assertEqual(self.check(data), [])
        for field in blocker:
            invalid = copy.deepcopy(data)
            del invalid["blocker"][field]
            self.assertTrue(self.check(invalid))

    def test_malformed_objects_fail_without_exceptions(self):
        for data in (None, 1, [], "text"):
            self.assertTrue(MODULE.validate_response(data, self.assignment, self.snapshot))
        for assignment in (None, [], {}, {"role": "plex-dev"}):
            self.assertTrue(MODULE.validate_response(self.response, assignment, self.snapshot))
        for field in ("status", "summary", "artifacts", "criteria"):
            for value in (None, {}, 3, True):
                self.assertTrue(self.check({**self.response, field: value}))

    def test_response_cli_and_source_files_are_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            paths = [root / "assignment.json", root / "resolved.toml"]
            paths[0].write_text(json.dumps(self.assignment))
            paths[1].write_text('roles = ["pm", "dev", "reviewer"]\n')
            before = [p.read_bytes() for p in paths]
            for raw, expected in ((json.dumps(self.response), 0), ("{broken", 1), ("[]", 1),
                                  (json.dumps({**self.response, "revision": 2}), 1)):
                result = subprocess.run([sys.executable, str(SCRIPT), "--resolved", str(paths[1]),
                                         "--assignment", str(paths[0])], input=raw,
                                        text=True, capture_output=True)
                self.assertEqual(result.returncode, expected, result.stderr)
                self.assertEqual(json.loads(result.stdout)["status"], "valid" if expected == 0 else "invalid")
            self.assertEqual([p.read_bytes() for p in paths], before)
            self.assertEqual(set(root.iterdir()), set(paths))


if __name__ == "__main__":
    unittest.main()
