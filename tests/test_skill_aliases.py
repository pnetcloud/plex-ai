"""Owned Codex short-name links: scopes, transitions, conflicts and rollback."""
import importlib.util
import io
import json
import os
import select
import shutil
import subprocess
import time
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plex_alias_installer", ROOT / "setup.py")
I = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(I)


class SkillAliasTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.project = self.base / "project"
        self.project.mkdir()
        self.user = self.base / "codex-home"
        self.user.mkdir()
        for context in (patch.dict(os.environ, {"CODEX_HOME": str(self.user)}),
                        patch.object(I, "run"), patch.object(I, "verify_plugin"),
                        patch.object(I.shutil, "which", return_value="/stub/codex"),
                        redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO())):
            context.__enter__()
            self.addCleanup(context.__exit__, None, None, None)

    def setup_project(self, *extra):
        return I.main(["--project", str(self.project), "--client", "codex", "--scope", "project",
                       "--team", "pnet", "--yes", "--no-command", *extra])

    def test_project_setup_refresh_status_and_removal(self):
        self.assertEqual(self.setup_project(), 0)
        links = [self.project / ".agents/skills" / name for name in I.DEV_SKILLS]
        for path in links:
            self.assertTrue(path.is_symlink())
            self.assertEqual(path.resolve(), ROOT / "skills" / path.name)
        receipt = self.project / ".plex/skill-aliases.json"
        before = receipt.read_bytes()
        self.assertEqual(self.setup_project("--roles-only"), 0)
        self.assertEqual(receipt.read_bytes(), before)
        self.assertEqual(I.plex_status(self.project, ["codex"])["clients"][0]["skill_aliases"], "enabled")
        self.assertEqual(I.main(["uninstall", "--project", str(self.project), "--client", "codex", "--yes"]), 0)
        self.assertFalse(receipt.exists())
        self.assertTrue(all(not path.is_symlink() for path in links))
        self.assertTrue((ROOT / ".build/plugins/codex/skills/plex/SKILL.md").is_file())

    def test_user_links_and_config_are_separate_from_project_removal(self):
        config = self.user / "config.toml"
        original = 'model = "personal-model"\n'
        config.write_text(original)
        self.assertEqual(self.setup_project("--scope", "user"), 0)
        self.assertTrue((self.user / "skills/plex").is_symlink())
        self.assertEqual(I.plex_status(self.project, ["codex"])["clients"][0]["skill_aliases"], "enabled")
        self.assertFalse((self.project / ".agents").exists())
        self.assertEqual(config.read_text(), original)
        self.assertEqual(I.main(["uninstall", "--project", str(self.project), "--client", "codex", "--yes"]), 0)
        self.assertTrue((self.user / "skills/plex").is_symlink())
        self.assertEqual(I.main(["uninstall", "--project", str(self.project), "--client", "codex", "--scope", "user", "--yes"]), 0)
        self.assertFalse((self.user / "skills/plex").is_symlink())
        self.assertEqual(config.read_text(), original)

    def test_dev_transitions_reuse_owned_links_and_restore_override(self):
        self.assertEqual(self.setup_project(), 0)
        self.assertEqual(self.setup_project("--dev"), 0)
        link = self.project / ".agents/skills/plex"
        self.assertEqual(link.resolve(), ROOT / "skills/plex")
        self.assertFalse((self.project / ".plex/skill-aliases.json").exists())
        self.assertEqual(self.setup_project("--no-dev"), 0)
        self.assertEqual(link.resolve(), ROOT / "skills/plex")
        self.assertFalse((self.project / ".plex/dev.json").exists())
        config = self.project / ".codex/config.toml"
        self.assertNotIn(I.DEV_BLOCK, config.read_text() if config.exists() else "")

    def test_foreign_skill_blocks_setup_before_native_plugin_changes(self):
        foreign = self.project / ".agents/skills/plex"
        foreign.mkdir(parents=True)
        (foreign / "SKILL.md").write_text("Manual skill")
        self.assertEqual(self.setup_project(), 1)
        I.run.assert_not_called()
        self.assertEqual((foreign / "SKILL.md").read_text(), "Manual skill")
        self.assertFalse((self.project / ".plex").exists())

    def test_modified_link_blocks_status_and_uninstall(self):
        self.assertEqual(self.setup_project(), 0)
        link = self.project / ".agents/skills/plex"
        link.unlink()
        link.symlink_to(self.base / "foreign")
        self.assertEqual(I.main(["status", "--project", str(self.project), "--client", "codex", "--json"]), 1)
        self.assertEqual(I.main(["uninstall", "--project", str(self.project), "--client", "codex", "--yes"]), 1)
        self.assertEqual(os.readlink(link), str(self.base / "foreign"))
        self.assertTrue((self.project / ".plex/skill-aliases.json").is_file())

    def test_role_failure_rolls_back_aliases(self):
        with patch.object(I.CONFIG, "apply_project", side_effect=ValueError("role failure")) as apply:
            self.assertEqual(self.setup_project(), 1)
            apply.assert_called_once()
        self.assertFalse((self.project / ".agents/skills/plex").is_symlink())
        self.assertFalse((self.project / ".plex/skill-aliases.json").exists())

    def test_preview_and_roles_only_do_not_add_aliases(self):
        self.assertEqual(self.setup_project("--dry-run"), 0)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(self.setup_project("--roles-only"), 0)
        self.assertFalse((self.project / ".agents/skills/plex").is_symlink())

    def test_missing_shared_source_is_reported_without_mutation(self):
        self.assertEqual(self.setup_project(), 0)
        with patch.object(I, "ROOT", self.base / "missing-source"):
            with self.assertRaises(ValueError):
                I.plan_skills(self.project, aliases=True)
        self.assertTrue((self.project / ".agents/skills/plex").is_symlink())

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_native_codex_discovers_short_names_in_both_scopes(self):
        for scope in ("project", "user"):
            with self.subTest(scope=scope):
                with I.apply_skills(I.plan_skills(self.project, aliases=True, scope=scope)):
                    pass
                env = {**os.environ, "HOME": str(self.base)}
                process = subprocess.Popen(["codex", "app-server", "--stdio"], cwd=self.project,
                                           env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                           stderr=subprocess.DEVNULL, text=True)
                def call(ident, method, params):
                    process.stdin.write(json.dumps({"id": ident, "method": method, "params": params}) + "\n")
                    process.stdin.flush()
                    deadline = time.monotonic() + 20
                    while time.monotonic() < deadline:
                        if not select.select([process.stdout], [], [], 1)[0]:
                            continue
                        line = process.stdout.readline()
                        if not line:
                            self.fail("Codex app-server exited before skill discovery")
                        response = json.loads(line)
                        if response.get("id") == ident:
                            self.assertNotIn("error", response)
                            return response["result"]
                    self.fail(f"Codex app-server timed out: {method}")
                try:
                    call(1, "initialize", {"clientInfo": {"name": "plex-alias-test", "version": "0.1"}})
                    process.stdin.write('{"method":"initialized"}\n')
                    process.stdin.flush()
                    result = call(2, "skills/list", {"cwds": [str(self.project)], "forceReload": True})
                    skills = [skill for item in result["data"] for skill in item["skills"]
                              if skill["name"] in I.DEV_SKILLS]
                    self.assertEqual({skill["name"] for skill in skills}, set(I.DEV_SKILLS))
                    self.assertTrue(all(skill["enabled"] for skill in skills))
                finally:
                    process.terminate()
                    try:
                        process.wait(timeout=3)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.wait()
                    process.stdin.close()
                    process.stdout.close()
                with I.apply_skills(I.plan_skills(self.project, scope=scope)):
                    pass

    def test_invalid_receipt_is_preserved(self):
        receipt = self.project / ".plex/skill-aliases.json"
        receipt.parent.mkdir()
        receipt.write_text("null")
        self.assertEqual(self.setup_project(), 1)
        I.run.assert_not_called()
        self.assertEqual(receipt.read_text(), "null")


if __name__ == "__main__":
    unittest.main()
