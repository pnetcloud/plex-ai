"""Installer entry points, unattended runs and isolated native installation."""

import json
import importlib.util
import io
from contextlib import redirect_stdout, redirect_stderr
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import tomllib
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]


class InstallerTests(unittest.TestCase):
    def test_preview_and_roles_only_do_not_build_plugins(self):
        spec = importlib.util.spec_from_file_location("plex_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), \
                patch.object(installer, "build_plugin") as build:
            for host in ("codex", "claude", "antigravity"):
                self.assertEqual(installer.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", host,
                                                 "--dry-run"]), 0)
            self.assertEqual(installer.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex",
                                             "--roles-only", "--yes"]), 0)
            build.assert_not_called()

    def test_user_command_install_repeat_and_run_from_project(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {
                **os.environ,
                "HOME": temp,
                "UV_CACHE_DIR": os.environ.get("UV_CACHE_DIR", str(Path.home() / ".cache/uv")),
                "UV_PYTHON_INSTALL_DIR": os.environ.get("UV_PYTHON_INSTALL_DIR", str(Path.home() / ".local/share/uv/python")),
                "PATH": f"{Path(shutil.which('uv')).parent}:/usr/bin:/bin",
            }
            command = Path(temp).resolve() / ".local/bin/plex"
            for _ in range(2):
                result = self.run_setup("--install-command", env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(command.resolve(), ROOT / "setup.sh")
                self.assertIn('export PATH=', result.stdout)
            project = Path(temp).resolve() / "project with spaces"
            project.mkdir()
            result = subprocess.run(
                [str(command), "--project", ".", "--host", "codex", "--dry-run"],
                cwd=project, env=env, input="", capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn(str(project), result.stdout)
            self.assertEqual(list(project.iterdir()), [])
            fallback_bin = Path(temp).resolve() / "fallback-bin"
            fallback_bin.mkdir()
            (fallback_bin / "python3").symlink_to(sys.executable)
            fallback = subprocess.run(
                [str(command), "--project", ".", "--host", "codex", "--roles-only", "--yes"],
                cwd=project, env={**env, "PATH": f"{fallback_bin}:/usr/bin:/bin"}, input="",
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertTrue((project / ".plex/applied.json").is_file())

    def test_full_install_shares_plugin_and_creates_command_with_local_team(self):
        spec = importlib.util.spec_from_file_location("plex_full_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()) as output:
            home = Path(temp).resolve() / "home"
            project = Path(temp).resolve() / "project"
            project.mkdir()
            (project / "CLAUDE.md").write_text("Personal rules.\n")
            env = {"HOME": str(home), "CLAUDE_CONFIG_DIR": str(home / ".claude")}
            inventory = json.dumps([{"id": "pnet-plex@pnet-plex", "scope": "user", "enabled": True}])
            with patch.dict(os.environ, env), patch.object(installer, "build_plugin"), \
                    patch.object(installer.shutil, "which", return_value="/bin/claude"), \
                    patch.object(installer, "run", return_value=inventory) as run:
                args = ["--host", "claude", "--project", str(project), "--yes"]
                self.assertEqual(installer.main(args), 0)
                self.assertIn(["claude", "plugin", "install", "pnet-plex@pnet-plex", "--scope", "user"],
                              [call.args[0] for call in run.call_args_list])
                self.assertEqual((home / ".local/bin/plex").resolve(), ROOT / "setup.sh")
                self.assertEqual(len(list((project / ".claude/agents").glob("plex-*.md"))), 6)
                self.assertTrue((project / "CLAUDE.md").read_text().startswith("Personal rules.\n"))
                self.assertFalse((project / "skills").exists())
                before = {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()}
                self.assertEqual(installer.main(args), 0)
                self.assertEqual(before, {p.relative_to(project): p.read_bytes() for p in project.rglob('*') if p.is_file()})
            self.assertIn("No separate plex-setup step", output.getvalue())

    def test_disabled_plugin_stops_before_team_or_command_writes(self):
        spec = importlib.util.spec_from_file_location("plex_failed_plugin", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            project = Path(temp).resolve() / "project"
            project.mkdir()
            with patch.dict(os.environ, {"HOME": str(Path(temp).resolve() / "home")}), \
                    patch.object(installer, "build_plugin"), \
                    patch.object(installer.shutil, "which", return_value="/bin/claude"), \
                    patch.object(installer, "run", return_value="[]"):
                self.assertEqual(installer.main(["--host", "claude", "--project", str(project), "--yes"]), 1)
            self.assertEqual(list(project.iterdir()), [])
            self.assertFalse((Path(temp).resolve() / "home/.local/bin/plex").exists())

    def test_user_command_upgrades_this_checkouts_previous_shortcut(self):
        with tempfile.TemporaryDirectory() as temp:
            command = Path(temp).resolve() / ".local/bin/plex"
            command.parent.mkdir(parents=True)
            command.symlink_to(ROOT / "setup.py")
            result = self.run_setup("--install-command", env={**os.environ, "HOME": temp})
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(command.resolve(), ROOT / "setup.sh")

    def test_source_checkout_is_not_the_implicit_target_project(self):
        spec = importlib.util.spec_from_file_location("plex_target_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch.object(installer.Path, "cwd", return_value=ROOT), \
                    patch.object(installer, "choose", side_effect=lambda label, choices, default: default), \
                    patch.object(installer, "ask_text", side_effect=["", temp, "3"]) as prompt:
                self.assertEqual(installer.main(["--host", "codex", "--roles-only"]), 0)
            self.assertEqual(prompt.call_args_list[0].args, ("Project directory", ""))
            self.assertEqual(prompt.call_args_list[1].args, ("Project directory", ""))
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def test_user_command_preserves_foreign_file_and_broken_link(self):
        with tempfile.TemporaryDirectory() as temp:
            env = {**os.environ, "HOME": temp}
            command = Path(temp).resolve() / ".local/bin/plex"
            command.parent.mkdir(parents=True)
            command.write_text("existing command")
            result = self.run_setup("--install-command", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(command.read_text(), "existing command")
            command.unlink()
            command.symlink_to(Path(temp).resolve() / "missing")
            result = self.run_setup("--install-command", env=env)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(os.readlink(command), str(Path(temp).resolve() / "missing"))

    def test_interactive_menu_can_cancel_without_writes(self):
        spec = importlib.util.spec_from_file_location("plex_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()) as output:
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch("builtins.input", side_effect=["invalid", "pnet", "inherit", "0", "bad", "", "no"]):
                result = installer.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex", "--roles-only"])
            self.assertEqual(result, 0)
            self.assertIn("Choose a listed name", output.getvalue())
            self.assertIn("Cancelled", output.getvalue())
            self.assertIn("Enter a positive whole number", output.getvalue())
            self.assertLess(output.getvalue().index("1. inherit"), output.getvalue().index("openai-basic"))
            self.assertIn("user/session default model and reasoning", output.getvalue())
            self.assertIn("gpt-6.1-sol /", output.getvalue())
            self.assertIn("dev: gpt-6-luna /", output.getvalue())
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def test_shared_concurrency_prompt_persists_and_cli_can_override(self):
        spec = importlib.util.spec_from_file_location("plex_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            common = ["--project", temp, "--host", "codex", "--roles-only", "--scope", "project", "--no-instructions"]
            for default in ("3", "6"):
                with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                        patch.object(installer, "choose", side_effect=["pnet", "inherit", "yes"]), \
                        patch.object(installer, "ask_text", return_value="6") as prompt:
                    self.assertEqual(installer.main(common), 0)
                prompt.assert_called_once_with("Parallel agents", default)
                source = Path(temp).resolve() / ".plex/preset.toml"
                self.assertEqual(tomllib.loads(source.read_text())["max_agents"], 6)
            result = self.run_setup(*common, "--yes", "--max-agents", "2")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(tomllib.loads(source.read_text())["max_agents"], 2)
            result = self.run_setup(*common, "--yes", "--model-profile", "openai-plus")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(tomllib.loads(source.read_text())["max_agents"], 2)

    def test_interactive_bmad_without_runtime_stops_before_model_selection(self):
        spec = importlib.util.spec_from_file_location("plex_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()) as output, \
                redirect_stderr(io.StringIO()) as errors:
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch("builtins.input", side_effect=["bmad"]), \
                    patch.object(installer, "run") as run, \
                    patch.object(installer.shutil, "which", return_value="/mock/codex"):
                result = installer.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex"])
            self.assertEqual(result, 1)
            self.assertIn("bmad setup", errors.getvalue())
            self.assertNotIn("Model profile", output.getvalue())
            run.assert_not_called()
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def run_setup(self, *args, env=None, stdin=""):
        return subprocess.run(
            [sys.executable, str(ROOT / "setup.py"), *map(str, args)],
            input=stdin, capture_output=True, text=True, timeout=60, env=env,
        )

    def test_preview_is_read_only_without_host_cli(self):
        with tempfile.TemporaryDirectory(prefix="plex-preview-") as temp:
            result = self.run_setup("--project", temp, "--host", "claude", "--team", "pnet",
                                    "--model-profile", "anthropic-pro", "--dry-run")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("claude plugin install", result.stdout)
            self.assertIn("sonnet", result.stdout)
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])
            self.assertNotIn("\033", result.stdout)
            ag_res = self.run_setup("--project", temp, "--host", "antigravity", "--team", "pnet",
                                    "--model-profile", "google-plus", "--dry-run")
            self.assertEqual(ag_res.returncode, 0, ag_res.stderr)
            self.assertIn("agy plugin install", ag_res.stdout)
            self.assertIn("flash", ag_res.stdout)
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def test_roles_only_setup_repeat_and_profile_switch_preserve_overrides(self):
        with tempfile.TemporaryDirectory(prefix="plex-installer-") as temp:
            common = ["--project", temp, "--host", "codex", "--roles-only", "--yes"]
            result = self.run_setup(*common, "--team", "pnet", "--model-profile", "openai-plus")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("configuration in sync", result.stdout)
            root = Path(temp).resolve()
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            result = self.run_setup(*common)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})
            preset = root / ".plex/preset.toml"
            preset.write_text(preset.read_text() + '\n[codex.dev]\nreasoning = "max"\n')
            result = self.run_setup(*common, "--model-profile", "openai-pro")
            self.assertEqual(result.returncode, 0, result.stderr)
            worker = tomllib.loads((root / ".codex/agents/plex-dev.toml").read_text())
            reviewer = tomllib.loads((root / ".codex/agents/plex-reviewer.toml").read_text())
            self.assertEqual(worker["model_reasoning_effort"], "max")
            self.assertEqual(reviewer["model"], "gpt-6.1-sol")

    def test_invalid_input_and_missing_bmad_stop_without_writes(self):
        with tempfile.TemporaryDirectory(prefix="plex-installer-invalid-") as temp:
            cases = [
                ["--max-agents", "0", "--yes"],
                ["--max-agents", "-1", "--yes"],
                ["--team", "missing", "--yes"],
                ["--team", "bmad", "--yes"],
                ["--team", "pnet"],
            ]
            for extra in cases:
                with self.subTest(extra=extra):
                    result = self.run_setup("--project", temp, "--host", "codex", "--roles-only", *extra)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    @unittest.skipUnless(shutil.which("sh"), "POSIX shell unavailable")
    def test_shell_entry_works_from_another_directory(self):
        with tempfile.TemporaryDirectory() as temp:
            result = subprocess.run(["sh", str(ROOT / "setup.sh"), "--help"], cwd=temp,
                                    capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--roles-only", result.stdout)
            fallback_bin = Path(temp).resolve() / "fallback-bin"
            fallback_bin.mkdir()
            (fallback_bin / "python3").symlink_to(sys.executable)
            env = {**os.environ, "PATH": f"{fallback_bin}:/usr/bin:/bin"}
            fallback = subprocess.run(["sh", str(ROOT / "setup.sh"), "--help"], cwd=temp,
                                      env=env, capture_output=True, text=True, timeout=10)
            self.assertEqual(fallback.returncode, 0, fallback.stderr)
            self.assertIn("--command", fallback.stdout)

    @unittest.skipUnless(shutil.which("codex"), "Codex CLI unavailable")
    def test_native_install_uses_only_disposable_codex_profile(self):
        with tempfile.TemporaryDirectory(prefix="plex-installer-native-") as temp:
            project = Path(temp).resolve() / "project with spaces"
            project.mkdir()
            profile = Path(temp).resolve() / "profile"
            profile.mkdir()
            env = {**os.environ, "HOME": temp, "CODEX_HOME": str(profile)}
            result = self.run_setup("--project", project, "--host", "codex", "--team", "pnet",
                                    "--model-profile", "inherit", "--yes", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = subprocess.run(["codex", "plugin", "list", "--json"], env=env,
                                       capture_output=True, text=True, timeout=30)
            self.assertEqual(inventory.returncode, 0, inventory.stderr)
            installed = json.loads(inventory.stdout)["installed"]
            self.assertTrue(any(p["name"] == "pnet-plex" and p["enabled"] for p in installed))
            self.assertTrue((project / ".plex/applied.json").is_file())
            self.assertEqual(
                {path.stem for path in (project / ".codex/agents").glob("*.toml")},
                {"plex-pm", "plex-explorer", "plex-researcher", "plex-dev", "plex-reviewer", "plex-qa"},
            )

    @unittest.skipUnless(shutil.which("codex") and shutil.which("agy"), "Codex and Antigravity CLIs required")
    def test_multi_client_native_install_and_repeat(self):
        with tempfile.TemporaryDirectory(prefix="plex-multi-client-") as temp:
            root = Path(temp).resolve()
            project = root / 'project'
            project.mkdir()
            profile = root / 'codex'
            profile.mkdir()
            env = {**os.environ, 'HOME':temp, 'CODEX_HOME':str(profile)}
            args = ['--project', project, '--client', 'codex', '--client', 'antigravity',
                    '--team', 'pnet', '--model-profile', 'plus', '--yes']
            for _ in range(2):
                before = {p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}
                result = self.run_setup(*args, env=env)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn('All selected clients are in sync', result.stdout)
                if before:
                    self.assertEqual(before, {p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()})
            self.assertEqual(len(list((project / '.codex/agents').glob('plex-*.toml'))), 6)
            self.assertEqual(len(list((project / '.agents/agents').glob('plex-*.md'))), 6)
            self.assertEqual((root / '.local/bin/plex').resolve(), ROOT / 'setup.sh')

    @unittest.skipUnless(shutil.which("agy"), "Antigravity CLI unavailable")
    def test_native_install_uses_only_disposable_antigravity_home(self):
        with tempfile.TemporaryDirectory(prefix="plex-installer-agy-") as temp:
            project = Path(temp).resolve() / "project with spaces"
            project.mkdir()
            home = Path(temp).resolve() / "home"
            home.mkdir()
            env = {**os.environ, "HOME": str(home)}
            result = self.run_setup("--project", project, "--host", "antigravity", "--team", "pnet",
                                    "--model-profile", "google-plus", "--yes", env=env)
            self.assertEqual(result.returncode, 0, result.stderr)
            inventory = subprocess.run(["agy", "plugin", "list", "--json"], env=env,
                                       capture_output=True, text=True, timeout=30)
            self.assertEqual(inventory.returncode, 0, inventory.stderr)
            installed = json.loads(inventory.stdout)
            self.assertTrue(any(p["name"] == "pnet-plex" and p["enabled"] for p in installed))
            self.assertTrue((project / ".plex/applied.json").is_file())
            self.assertEqual(
                {path.stem for path in (project / ".agents/agents").glob("*.md")},
                {"plex-pm", "plex-explorer", "plex-researcher", "plex-dev", "plex-reviewer", "plex-qa"},
            )


if __name__ == "__main__":
    unittest.main()
