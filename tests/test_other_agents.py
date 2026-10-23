"""Explicit, scoped cleanup of legacy Codex agents with verified rollback."""
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plex_other_agents", ROOT / "setup.py")
I = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(I)
C = I.CONFIG


class OtherAgentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.home = self.root / "codex-home"
        self.home.mkdir()
        self.project = self.root / "project"
        self.project.mkdir()
        self.output = io.StringIO()
        for context in (patch.dict(os.environ, {"CODEX_HOME": str(self.home)}),
                        redirect_stdout(self.output), redirect_stderr(self.output)):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def agent(self, name="legacy", root=None, user=False):
        path = (root or self.project) / ("agents" if user else ".codex/agents") / f"{name}.toml"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f'name = "{name}"\ndescription = "Legacy role"\n')
        return path

    def setup_project(self, *extra):
        return I.main(["--client", "codex", "--project", str(self.project), "--scope", "project",
                       "--team", "pnet", "--model-profile", "plus", "--interaction", "balanced",
                       "--max-agents", "3", "--roles-only", "--yes", *extra])

    def test_default_preserves_agents_and_installs_allowlist(self):
        path = self.agent()
        original = path.read_bytes()
        self.assertEqual(self.setup_project(), 0, self.output.getvalue())
        self.assertEqual(path.read_bytes(), original)
        self.assertIn("Other Codex agents", self.output.getvalue())
        self.assertIn("only to exact `plex-<role>`", (self.project / "AGENTS.md").read_text())

    def test_explicit_archive_includes_unknown_plex_roles_and_preserves_scope(self):
        paths = [self.agent(), self.agent("plex-obsolete")]
        originals = {path.name: path.read_bytes() for path in paths}
        global_path = self.agent(root=self.home, user=True)
        self.assertEqual(self.setup_project("--archive-other-agents"), 0, self.output.getvalue())
        for path in paths:
            self.assertFalse(path.exists())
            copies = list((self.project / ".plex/backups").glob(f"*/codex/other-agents/{path.name}"))
            self.assertEqual(len(copies), 1)
            self.assertEqual(copies[0].read_bytes(), originals[path.name])
        self.assertTrue(global_path.exists())
        self.assertEqual(C.check_project(self.project, "codex")["status"], "in_sync")

    def test_user_scope_does_not_touch_project_agents(self):
        local = self.agent()
        global_path = self.agent(root=self.home, user=True)
        self.assertEqual(self.setup_project("--scope", "user", "--archive-other-agents"), 0, self.output.getvalue())
        self.assertTrue(local.exists())
        self.assertFalse(global_path.exists())
        self.assertTrue(list((self.home / ".plex/backups").glob("*/codex/other-agents/legacy.toml")))

    def test_dry_run_does_not_archive(self):
        path = self.agent()
        self.assertEqual(self.setup_project("--dry-run", "--archive-other-agents"), 0)
        self.assertTrue(path.exists())
        self.assertFalse((self.project / ".plex").exists())

    def test_prompt_only_when_detected_and_defaults_to_keep(self):
        for has_other in (False, True):
            if has_other:
                self.agent()
            def choose(label, choices, default):
                if label == "Other Codex agents":
                    self.assertEqual(default, "keep")
                return "yes" if label == "Apply this plan?" else default
            with patch.object(I.sys.stdin, "isatty", return_value=True), patch.object(I, "choose", side_effect=choose) as menu:
                args = ["--client", "codex", "--project", str(self.project), "--scope", "project", "--team", "pnet",
                        "--model-profile", "plus", "--interaction", "balanced", "--max-agents", "3", "--roles-only"]
                self.assertEqual(I.main(args), 0, self.output.getvalue())
                self.assertEqual(sum(call.args[0] == "Other Codex agents" for call in menu.call_args_list), int(has_other))
        self.assertTrue((self.project / ".codex/agents/legacy.toml").exists())

    def test_cancellation_preserves_selected_files(self):
        path = self.agent()
        def choose(label, choices, default):
            if label == "Other Codex agents": return "archive"
            if label == "Apply this plan?": return "no"
            return default
        with patch.object(I.sys.stdin, "isatty", return_value=True), patch.object(I, "choose", side_effect=choose):
            args = ["--client", "codex", "--project", str(self.project), "--scope", "project", "--team", "pnet",
                    "--model-profile", "plus", "--interaction", "balanced", "--max-agents", "3", "--roles-only"]
            self.assertEqual(I.main(args), 0)
        self.assertTrue(path.exists())
        self.assertFalse((self.project / ".plex").exists())

    def test_role_failure_restores_archived_files(self):
        path = self.agent()
        original = path.read_bytes()
        write = C._atomic_write_bytes
        def fail_role(target, data):
            if target.name == "plex-dev.toml": raise ValueError("injected role failure")
            return write(target, data)
        with patch.object(C, "_atomic_write_bytes", side_effect=fail_role):
            self.assertEqual(self.setup_project("--archive-other-agents"), 1)
        self.assertEqual(path.read_bytes(), original)
        self.assertFalse((self.project / ".plex/applied.json").exists())

    def test_changed_agent_after_preview_is_preserved(self):
        path = self.agent()
        apply = C.apply_project
        def edit_then_apply(*args, **kwargs):
            path.write_text("concurrent edit")
            return apply(*args, **kwargs)
        with patch.object(C, "apply_project", side_effect=edit_then_apply):
            self.assertEqual(self.setup_project("--archive-other-agents"), 1)
        self.assertEqual(path.read_text(), "concurrent edit")
        self.assertFalse((self.project / ".plex/backups").exists())

    def test_managed_and_desired_roles_cannot_be_archived(self):
        self.assertEqual(self.setup_project(), 0)
        protected = self.project / ".codex/agents/plex-dev.toml"
        self.assertEqual(C.other_codex_agents(self.project, ["dev"]), {})
        with self.assertRaises(ValueError):
            C.apply_project(self.project, "codex", archive_agents={".codex/agents/plex-dev.toml": C.sha256_bytes(protected.read_bytes())})
        self.assertTrue(protected.exists())
        with self.assertRaises(ValueError):
            C.apply_project(self.project, "codex", archive_agents={"outside.toml": None})

    def test_symlink_is_not_followed_or_archived(self):
        foreign = self.root / "outside.toml"
        foreign.write_text("outside")
        path = self.project / ".codex/agents/legacy.toml"
        path.parent.mkdir(parents=True)
        path.symlink_to(foreign)
        self.assertEqual(self.setup_project("--archive-other-agents"), 0)
        self.assertTrue(path.is_symlink())
        self.assertEqual(foreign.read_text(), "outside")

    def test_explicit_config_registration_is_preserved(self):
        path = self.agent()
        config = self.project / ".codex/config.toml"
        original = '[agents.legacy]\nconfig_file = "agents/legacy.toml"\n'
        config.write_text(original)
        self.assertEqual(self.setup_project("--archive-other-agents"), 0, self.output.getvalue())
        self.assertTrue(path.exists())
        self.assertIn(original, config.read_text())
        self.assertEqual(tomllib.loads(config.read_text())["agents"], {
            "max_concurrent_threads_per_session": 3,
            "legacy": {"config_file": "agents/legacy.toml"},
        })
        with self.assertRaises(ValueError):
            C.apply_project(self.project, "codex", archive_agents={".codex/agents/legacy.toml": C.sha256_bytes(path.read_bytes())})

    def test_multi_client_forwards_cleanup_only_to_codex(self):
        path = self.agent()
        self.assertEqual(self.setup_project("--client", "claude", "--archive-other-agents"), 0, self.output.getvalue())
        self.assertFalse(path.exists())
        self.assertEqual(C.check_project(self.project, "claude")["status"], "in_sync")


if __name__ == "__main__":
    unittest.main()
