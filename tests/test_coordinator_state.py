"""Read-only validation of bounded coordinator session state."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "skills/plex/scripts/check_coordinator_state.py"
TEMPLATE = ROOT / "skills/plex/assets/coordinator-state.template"
SPEC = importlib.util.spec_from_file_location("plex_coordinator_state", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def outcome(identifier, **overrides):
    item = {
        "id": identifier,
        "goal": "Finish the approved outcome",
        "reference": f"/tasks/{identifier}",
        "owner": "coordinator",
        "authorization": "user request",
        "priority": "normal",
        "next_action": "Continue the assigned work",
        "blocker": "",
        "resume_condition": "",
    }
    item.update(overrides)
    return item


def decision(identifier, **overrides):
    item = {
        "id": identifier,
        "decision": "Keep the accepted priority",
        "authority": "user",
        "reference": f"/tasks/{identifier}",
    }
    item.update(overrides)
    return item


def completed(identifier, **overrides):
    item = {
        "id": identifier,
        "goal": "Finish the approved outcome",
        "reference": f"/tasks/{identifier}",
        "owner": "coordinator",
        "authorization": "user request",
        "priority": "normal",
        "result_reference": f"/results/{identifier}",
    }
    item.update(overrides)
    return item


def state():
    return {
        "version": 1,
        "session_id": "session-123",
        "primary_id": "main",
        "active": [outcome("main", priority="primary")],
        "queued": [],
        "paused": [],
        "recently_completed": [],
        "decisions": [],
    }


class CoordinatorStateTests(unittest.TestCase):
    def setUp(self):
        self.value = json.loads(TEMPLATE.read_text(encoding="utf-8"))

    def invalid(self, value, needle=None):
        errors = MODULE.validate(value)
        self.assertTrue(errors, value)
        if needle:
            self.assertTrue(any(needle in error for error in errors), errors)

    def test_template_is_valid_and_validation_is_read_only(self):
        before = TEMPLATE.read_bytes()
        self.assertEqual(MODULE.validate(self.value), [])
        self.assertEqual(TEMPLATE.read_bytes(), before)

    def test_private_work_ignore_rule_covers_session_state(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = Path(temp)
            subprocess.run(["git", "init", "-q", str(repo)], check=True)
            work = repo / ".plex/work"
            work.mkdir(parents=True)
            ignore = work / ".gitignore"
            ignore.write_text("# coordinator-owned private state\n*\n", encoding="utf-8")
            state_file = work / "session-1.json"
            state_file.write_text("{}\n", encoding="utf-8")
            result = subprocess.run(
                ["git", "-C", str(repo), "check-ignore", "-q", "--no-index",
                 ".plex/work/session-1.json"],
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode())

    def test_shared_lifecycle_contract_covers_continuation_edges(self):
        reference = " ".join(
            (ROOT / "skills/plex/references/coordinator-state.md").read_text().split()
        )
        checks = (
            "A related followup amends its existing outcome and assignment.",
            "Record an unrelated request in `queued` without launching PM intake or workers.",
            "Before choosing its route or executing it, obtain PM intake",
            "Follow explicit user priorities and supersession decisions.",
            "Compact at substantive transitions and before context compaction.",
            "hand off its result reference to the canonical",
            "Workers receive only their assigned goal, inputs and constraints",
        )
        for statement in checks:
            with self.subTest(statement=statement):
                self.assertIn(statement, reference)

    def test_structure_primary_and_item_ids_are_checked(self):
        for value in (None, [], "state", 1):
            with self.subTest(value=value):
                self.invalid(value)
        for change in (
            lambda data: data.pop("active"),
            lambda data: data.update(extra=True),
            lambda data: data.update(version=True),
            lambda data: data.update(primary_id="missing"),
            lambda data: data["queued"].append(outcome("main")),
            lambda data: data["active"].append({"id": "incomplete"}),
        ):
            data = state()
            change(data)
            with self.subTest(data=data):
                self.invalid(data)

    def test_count_limits_and_recorded_active_limit_override(self):
        data = state()
        data["active"].append(outcome("second"))
        self.assertEqual(MODULE.validate(data), [])
        data["active"].append(outcome("third"))
        self.invalid(data, "active")
        data["decisions"] = [decision("limit", active_limit=3)]
        self.assertEqual(MODULE.validate(data), [])
        data["decisions"][0]["authority"] = "coordinator"
        self.invalid(data, "active_limit")
        data["decisions"][0].update(authority="user", active_limit=2)
        self.invalid(data, "active_limit")

        for field, allowed in (("queued", 8), ("paused", 8), ("recently_completed", 4),
                               ("decisions", 8)):
            data = state()
            if field == "paused":
                data[field] = [outcome(f"paused-{i}", resume_condition="resume after blocker clears")
                               for i in range(allowed)]
            elif field == "recently_completed":
                data[field] = [completed(f"done-{i}")
                               for i in range(allowed)]
            elif field == "decisions":
                data[field] = [decision(f"decision-{i}") for i in range(allowed)]
            else:
                data[field] = [outcome(f"queued-{i}") for i in range(allowed)]
            self.assertEqual(MODULE.validate(data), [], field)
            if field == "paused":
                data[field].append(outcome("paused-over", resume_condition="resume later"))
            elif field == "recently_completed":
                data[field].append(completed("done-over"))
            elif field == "decisions":
                data[field].append(decision("decision-over"))
            else:
                data[field].append(outcome("queued-over"))
            self.invalid(data, field)

    def test_paused_commitments_and_completed_results_need_references(self):
        data = state()
        data["paused"] = [outcome("paused-1")]
        self.invalid(data, "resume_condition")
        data["paused"][0]["resume_condition"] = "resume after approval"
        self.assertEqual(MODULE.validate(data), [])
        data["recently_completed"] = [completed("done-1", result_reference="")]
        self.invalid(data, "result_reference")

    def test_string_limits_count_unicode_characters(self):
        data = state()
        data["active"][0]["goal"] = "界" * 1024
        self.assertEqual(MODULE.validate(data), [])
        data["active"][0]["goal"] += "界"
        self.invalid(data, "goal")

        data = state()
        data["session_id"] = "s" * 512
        data["active"][0]["authorization"] = "a" * 512
        data["active"][0]["priority"] = "p" * 512
        data["active"][0]["reference"] = "界" * 512
        self.assertEqual(MODULE.validate(data), [])
        for field, value in (("session_id", "s" * 513),
                             ("authorization", "a" * 513),
                             ("priority", "p" * 513),
                             ("reference", "界" * 513)):
            invalid = copy.deepcopy(data)
            if field == "session_id":
                invalid[field] = value
            else:
                invalid["active"][0][field] = value
            with self.subTest(field=field):
                self.invalid(invalid, field)

        data = state()
        data["active"][0]["id"] = data["primary_id"] = "i" * 64
        data["active"][0]["owner"] = "o" * 64
        data["active"][0]["next_action"] = "n" * 256
        data["active"][0]["blocker"] = "b" * 256
        data["active"][0]["resume_condition"] = "r" * 256
        data["active"][0]["reference"] = "é" * 512
        self.assertEqual(MODULE.validate(data), [])
        for field, value, needle in (("id", "i" * 65, "id"),
                                     ("owner", "o" * 65, "owner"),
                                     ("next_action", "n" * 257, "next_action"),
                                     ("blocker", "b" * 257, "blocker"),
                                     ("resume_condition", "r" * 257, "resume_condition"),
                                     ("reference", "é" * 513, "reference")):
            invalid = copy.deepcopy(data)
            invalid["active"][0][field] = value
            if field == "id":
                invalid["primary_id"] = value
            with self.subTest(field=field):
                self.invalid(invalid, needle)

    def test_compacted_state_keeps_canonical_refs_and_paused_resume(self):
        original = state()
        original["active"].extend((outcome("active-2"), outcome("active-3")))
        original["queued"] = [outcome("queued-1", next_action="Get PM intake before routing")]
        original["paused"] = [outcome("paused-1", resume_condition="resume after the data repair",
                                       reference="https://tracker.example/paused-1")]
        original["decisions"] = [
            decision("priority-1", reference="https://tracker.example/decision-1"),
            decision("limit-1", active_limit=3,
                     reference="https://tracker.example/active-limit-1"),
        ]
        compacted = copy.deepcopy(original)
        compacted["active"][0]["goal"] = "Complete the approved outcome; see /tasks/main"
        compacted["queued"][0]["goal"] = "Review queued request; see /tasks/queued-1"
        self.assertEqual(MODULE.validate(compacted), [])
        self.assertTrue(compacted["active"][0]["goal"])
        self.assertEqual(compacted["active"][0]["authorization"],
                         original["active"][0]["authorization"])
        self.assertEqual(compacted["paused"][0]["id"], original["paused"][0]["id"])
        self.assertEqual(compacted["paused"][0]["resume_condition"],
                         original["paused"][0]["resume_condition"])
        self.assertEqual(compacted["paused"][0]["reference"], original["paused"][0]["reference"])
        self.assertEqual(compacted["decisions"], original["decisions"])

    def test_utf8_byte_limit_and_cli_are_read_only(self):
        raw = json.dumps(state(), ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        exact = raw + b" " * (8192 - len(raw))
        self.assertEqual(MODULE.validate_bytes(exact), [])
        self.assertTrue(any("8192" in error for error in MODULE.validate_bytes(exact + b" ")))
        self.assertTrue(MODULE.validate_bytes(b"{\xff"))
        self.assertTrue(MODULE.validate_bytes(b'{"version":1,"version":1}'))
        deeply_nested = b"[" * 1100 + b"0" + b"]" * 1100
        recursion_errors = MODULE.validate_bytes(deeply_nested)
        self.assertTrue(recursion_errors, "deeply nested JSON must return a validation error")
        with patch.object(MODULE.json, "loads", side_effect=RecursionError("nested input")):
            recursion_errors = MODULE.validate_bytes(b"{}")
        self.assertTrue(any("invalid state JSON:" in error for error in recursion_errors),
                        recursion_errors)

        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "state.json"
            path.write_bytes(exact)
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                    text=True, capture_output=True, cwd=temp)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "valid")
            self.assertEqual(path.read_bytes(), before)
            self.assertEqual(list(Path(temp).iterdir()), [path])
            path.write_bytes(exact + b" ")
            before = path.read_bytes()
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                    text=True, capture_output=True, cwd=temp)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "invalid")
            self.assertEqual(path.read_bytes(), before)
            path.write_bytes(deeply_nested)
            result = subprocess.run([sys.executable, str(SCRIPT), str(path)],
                                    text=True, capture_output=True, cwd=temp)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout)["status"], "invalid")


if __name__ == "__main__":
    unittest.main()
