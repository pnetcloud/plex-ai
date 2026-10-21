"""Project-local checkout skills, plugin isolation and reversible ownership."""
import importlib.util
import io
import json
import os
import shutil
import subprocess
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plex_dev_installer", ROOT / "setup.py")
I = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(I)


class DevTests(unittest.TestCase):
    def setup_project(self, project, *options):
        return I.main(["--project", str(project), "--client", "codex", "--scope", "project",
                       "--team", "pnet", "--yes", "--no-command", *options])

    def test_live_source_instructions_status_refresh_and_exit(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), \
                patch.object(I, "build_plugin") as build, patch.object(I, "run") as run:
            project = Path(temp)
            (project / "AGENTS.md").write_text("Personal rules.\n")
            (project / ".codex").mkdir()
            config = project / ".codex/config.toml"
            config.write_text('model = "custom"\n')
            self.assertEqual(self.setup_project(project, "--dev"), 0)
            build.assert_not_called()
            run.assert_not_called()
            self.assertFalse(tomllib.loads(config.read_text())["plugins"][I.DEV_PLUGIN]["enabled"])
            for name in I.DEV_SKILLS:
                link = project / ".agents/skills" / name
                self.assertEqual(link.resolve(), ROOT / "skills" / name)
                self.assertEqual((link / "SKILL.md").read_bytes(), (ROOT / "skills" / name / "SKILL.md").read_bytes())
                self.assertTrue((link.resolve().parents[1] / "teams/pnet/coordinator.md").is_file())
            instructions = (project / "AGENTS.md").read_text()
            self.assertTrue(instructions.startswith("Personal rules.\n"))
            self.assertIn("use only this project's `.agents/skills/plex/SKILL.md`", instructions)
            self.assertIn("BMad workflows still use", instructions)
            self.assertEqual(self.setup_project(project, "--roles-only"), 0)  # preserve dev mode
            result = I.plex_status(project, ["codex"])["clients"][0]
            self.assertEqual(result["status"], "in_sync")
            self.assertEqual(result["plugin"], "development")
            self.assertEqual(result["dev_source"], str(ROOT))
            config.write_text(config.read_text() + '\n[features]\nsome_flag = true\n')
            self.assertEqual(self.setup_project(project, "--no-dev", "--roles-only"), 0)
            self.assertFalse((project / ".plex/dev.json").exists())
            self.assertFalse((project / ".agents/skills/plex").is_symlink())
            self.assertNotIn("Plex development source", (project / "AGENTS.md").read_text())
            self.assertEqual(tomllib.loads(config.read_text()), {"model": "custom", "features": {"some_flag": True}})

    def test_dry_run_and_unsupported_modes_never_write(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            project = Path(temp)
            self.assertEqual(I.main(["--project", temp, "--client", "codex", "--dev", "--dry-run"]), 0)
            self.assertEqual(list(project.iterdir()), [])
            for extra in (["--scope", "user"], ["--client", "claude"], ["--no-instructions"]):
                self.assertEqual(self.setup_project(project, "--dev", *extra), 1)
                self.assertEqual(list(project.iterdir()), [])

    def test_foreign_links_and_enabled_override_are_preserved(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            project = Path(temp)
            foreign = project / ".agents/skills/plex"
            foreign.mkdir(parents=True)
            (foreign / "SKILL.md").write_text("Manual skill")
            self.assertEqual(self.setup_project(project, "--dev"), 1)
            self.assertEqual((foreign / "SKILL.md").read_text(), "Manual skill")
            self.assertFalse((project / ".plex").exists())
            (foreign / "SKILL.md").unlink()
            foreign.rmdir()
            config = project / ".codex/config.toml"
            config.parent.mkdir()
            original = '[plugins."pnet-plex@pnet-plex"]\nenabled = true\n'
            config.write_text(original)
            self.assertEqual(self.setup_project(project, "--dev"), 1)
            self.assertEqual(config.read_text(), original)
            self.assertFalse(foreign.is_symlink())

    def test_preexisting_disabled_plugin_is_not_removed(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            project = Path(temp)
            config = project / ".codex/config.toml"
            config.parent.mkdir()
            original = '[plugins."pnet-plex@pnet-plex"]\nenabled = false\n'
            config.write_text(original)
            self.assertEqual(self.setup_project(project, "--dev"), 0)
            self.assertEqual(I.main(["uninstall", "--project", temp, "--client", "codex", "--yes"]), 0)
            self.assertEqual(config.read_text(), original)
            self.assertFalse((project / ".plex/dev.json").exists())
            self.assertNotIn("plex:managed:start", (project / "AGENTS.md").read_text())

    def test_role_failure_rolls_back_dev_state(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()), \
                patch.object(I.CONFIG, "apply_project", side_effect=ValueError("role failure")):
            project = Path(temp)
            self.assertEqual(self.setup_project(project, "--dev"), 1)
            self.assertFalse((project / ".plex/dev.json").exists())
            self.assertFalse((project / ".codex/config.toml").exists())
            for name in I.DEV_SKILLS:
                self.assertFalse((project / ".agents/skills" / name).is_symlink())

    def test_tampered_link_blocks_uninstall_and_reports_status_failure(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            project = Path(temp)
            self.assertEqual(self.setup_project(project, "--dev"), 0)
            link = project / ".agents/skills/plex"
            link.unlink()
            link.symlink_to(project / "foreign")
            self.assertNotEqual(I.plex_status(project, ["codex"])["clients"][0]["plugin"], "development")
            self.assertEqual(I.main(["uninstall", "--project", temp, "--client", "codex", "--yes"]), 1)
            self.assertTrue(link.is_symlink())
            self.assertTrue((project / ".codex/agents/plex-dev.toml").exists())

    def test_source_edits_are_visible_without_installing_again(self):
        with tempfile.TemporaryDirectory() as temp:
            project, checkout = Path(temp) / "project", Path(temp) / "checkout"
            project.mkdir()
            for name in I.DEV_SKILLS:
                source = checkout / "skills" / name / "SKILL.md"
                source.parent.mkdir(parents=True)
                source.write_text("before")
            with patch.object(I, "ROOT", checkout), I.apply_skills(I.plan_skills(project, True)):
                pass
            skill = checkout / "skills/plex/SKILL.md"
            skill.write_text("after")
            self.assertEqual((project / ".agents/skills/plex/SKILL.md").read_text(), "after")

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI is not installed")
    def test_native_codex_disables_only_this_project_and_restores_plugin(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp).resolve()
            project, other, profile = base / "project", base / "other", base / "profile"
            for directory in (project, other, profile):
                directory.mkdir()
            subprocess.run(["git", "init", "-q", str(project)], check=True)
            subprocess.run(["git", "init", "-q", str(other)], check=True)
            config = profile / "config.toml"
            config.write_text("".join('[projects.' + json.dumps(str(p)) + ']\ntrust_level = "trusted"\n'
                                      for p in (project, other)))
            env = {**os.environ, "HOME": str(base), "CODEX_HOME": str(profile)}
            def run(*args, cwd=project):
                result = subprocess.run(["codex", *args], cwd=cwd, env=env,
                                        capture_output=True, text=True, timeout=60)
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)
            def enabled(cwd):
                inventory = run("plugin", "list", "--json", cwd=cwd)
                return next(item["enabled"] for item in inventory["installed"] if item["name"] == "pnet-plex")
            I.build_plugin("codex")
            run("plugin", "marketplace", "add", str(ROOT), "--json")
            run("plugin", "add", I.DEV_PLUGIN, "--json")
            original = config.read_bytes()
            self.assertTrue(enabled(project))
            with I.apply_skills(I.plan_skills(project, True)):
                pass
            self.assertFalse(enabled(project))
            self.assertTrue(enabled(other))
            with I.apply_skills(I.plan_skills(project, False)):
                pass
            self.assertTrue(enabled(project))
            self.assertEqual(config.read_bytes(), original)

    def test_concurrent_edit_is_preserved_on_rollback(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            config = project / ".codex/config.toml"
            with self.assertRaisesRegex(ValueError, "recovery"):
                with I.apply_skills(I.plan_skills(project, True)):
                    config.write_text('model = "concurrent"\n')
                    raise ValueError("failed")
            self.assertEqual(config.read_text(), 'model = "concurrent"\n')


if __name__ == "__main__":
    unittest.main()
