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
    def test_interaction_is_shared_between_clients_and_preserved_on_refresh(self):
        spec = importlib.util.spec_from_file_location("plex_interaction_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            options = ["--scope", "project", "--project", temp, "--roles-only", "--yes", "--no-instructions"]
            self.assertEqual(installer.main([*options, "--client", "codex", "--client", "claude", "--interaction", "auto"]), 0)
            self.assertEqual(installer.main([*options, "--client", "codex", "--model-profile", "plus"]), 0)
            preset = tomllib.loads((Path(temp) / ".plex/preset.toml").read_text())
            self.assertEqual(preset["coordinator_token_budget"], 0)
            self.assertEqual(preset["subagent_token_budget"], 0)
            snapshot = json.loads((Path(temp) / ".plex/resolved.json").read_text())
            self.assertEqual(snapshot["interaction"], "auto")
            for host in ("codex", "claude"):
                self.assertEqual(installer.CONFIG.check_project(Path(temp), host)["status"], "in_sync")

    def test_interactive_interaction_is_selected_once_shared_and_reused(self):
        spec = importlib.util.spec_from_file_location("plex_mode_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            options = ["--project", temp, "--scope", "project", "--roles-only", "--no-instructions",
                       "--team", "pnet", "--model-profile", "plus", "--max-agents", "2",
                       "--client", "codex", "--client", "claude"]
            for expected_default in ("balanced", "auto"):
                def choose(label, choices, default):
                    if label == "Interaction mode":
                        self.assertEqual(default, expected_default)
                        self.assertEqual(set(choices), set(installer.CONFIG.INTERACTIONS))
                        return "auto"
                    if label == "Apply this plan?":
                        self.assertEqual(default, "yes")
                    return default
                with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                        patch.object(installer, "choose", side_effect=choose) as menu:
                    self.assertEqual(installer.main(options), 0)
                self.assertEqual(sum(call.args[0] == "Interaction mode" for call in menu.call_args_list), 1)
                self.assertEqual(tomllib.loads((Path(temp) / ".plex/preset.toml").read_text())["interaction"], "auto")
                for host in ("codex", "claude"):
                    state = installer.CONFIG.check_project(Path(temp), host)
                    self.assertEqual(state["resolved"]["interaction"], "auto")
                    self.assertEqual(state["status"], "in_sync")
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch.object(installer, "choose", return_value="yes") as menu:
                self.assertEqual(installer.main([*options, "--interaction", "interactive"]), 0)
                self.assertNotIn("Interaction mode", [call.args[0] for call in menu.call_args_list])
            self.assertEqual(tomllib.loads((Path(temp) / ".plex/preset.toml").read_text())["interaction"], "interactive")

    def test_existing_installation_refresh_skips_menus_preserves_legacy_profile_and_instruction_choices(self):
        spec = importlib.util.spec_from_file_location("plex_refresh_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            project = Path(temp).resolve()
            installer.CONFIG.apply_project(project, "codex", team="pnet", model_profile="openai-plus",
                                           interaction="auto", max_agents=2,
                                           host_overrides={"codex": {"dev": {"reasoning": "high"}}})
            installer.CONFIG.apply_project(project, "claude", instructions=True)
            preset = project / ".plex/preset.toml"
            before = preset.read_bytes()
            def choose(label, choices, default):
                if label == "Existing Plex installation":
                    self.assertEqual(default, "refresh")
                    return "refresh"
                self.assertEqual(label, "Apply this plan?")
                self.assertEqual(default, "yes")
                return default
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch.object(installer, "choose", side_effect=choose) as menu, \
                    patch.object(installer, "ask_text", side_effect=AssertionError("Unexpected settings question")):
                self.assertEqual(installer.main(["--project", temp, "--scope", "project", "--roles-only",
                                                 "--client", "codex", "--client", "claude"]), 0)
            self.assertEqual(sum(call.args[0] == "Existing Plex installation" for call in menu.call_args_list), 1)
            self.assertEqual(preset.read_bytes(), before)
            self.assertFalse((project / "AGENTS.md").exists())
            self.assertTrue((project / "CLAUDE.md").is_file())
            for host in ("codex", "claude"):
                self.assertEqual(installer.CONFIG.check_project(project, host)["status"], "in_sync")

    def test_refresh_applies_compatibility_fixes_and_retains_overrides(self):
        spec = importlib.util.spec_from_file_location("plex_upgrade_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            project = Path(temp).resolve()
            installer.CONFIG.apply_project(project, "codex", team="pnet", model_profile="plus",
                                           host_overrides={"codex": {"dev": {"reasoning": "high"}}}, instructions=True)
            preset = project / ".plex/preset.toml"
            preset.write_text(preset.read_text().replace('interaction = "balanced"\n', ''))
            file = project / "AGENTS.md"
            content = file.read_bytes()
            start, end = installer.CONFIG.instruction_span(content)
            legacy = content[start:end].replace(installer.CONFIG.PLEX_START, b"<!-- plex:start -->").replace(installer.CONFIG.PLEX_END, b"<!-- plex:end -->")
            file.write_bytes(b"Personal instructions.\n" + legacy + b"\n")
            receipt_path = project / ".plex/applied.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["hosts"]["codex"]["instructions"]["sha256"] = installer.CONFIG.sha256_bytes(legacy)
            receipt_path.write_text(json.dumps(receipt))
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch.object(installer, "choose", side_effect=lambda label, choices, default: "refresh" if label == "Existing Plex installation" else "yes"):
                self.assertEqual(installer.main(["--project", temp, "--scope", "project", "--client", "codex", "--roles-only"]), 0)
            saved = tomllib.loads(preset.read_text())
            self.assertEqual(saved["interaction"], "balanced")
            self.assertEqual(saved["codex"]["dev"], {"reasoning": "high"})
            self.assertTrue(file.read_bytes().startswith(b"Personal instructions.\n"))
            self.assertIn(installer.CONFIG.PLEX_START, file.read_bytes())
            self.assertNotIn(b"<!-- plex:start -->", file.read_bytes())
            self.assertEqual(installer.CONFIG.check_project(project, "codex")["status"], "in_sync")

    def test_unknown_receipt_format_stops_before_plugin_or_role_writes(self):
        spec = importlib.util.spec_from_file_location("plex_future_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            project = Path(temp).resolve()
            installer.CONFIG.apply_project(project, "codex")
            receipt_path = project / ".plex/applied.json"
            receipt = json.loads(receipt_path.read_text())
            receipt["future_format"] = 999
            receipt_path.write_text(json.dumps(receipt))
            before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
            with patch.object(installer, "build_plugin") as build:
                self.assertEqual(installer.main(["--project", temp, "--client", "codex", "--roles-only", "--yes"]), 1)
                build.assert_not_called()
            self.assertEqual(before, {p: p.read_bytes() for p in project.rglob("*") if p.is_file()})

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

    def test_existing_other_checkout_or_foreign_command_does_not_block_setup(self):
        spec = importlib.util.spec_from_file_location("plex_existing_command", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for kind in ("other-checkout", "foreign-file", "broken-link"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory() as temp, \
                    redirect_stdout(io.StringIO()) as output:
                root = Path(temp).resolve()
                home, project = root / "home", root / "project"
                project.mkdir()
                command = home / ".local/bin/plex"
                command.parent.mkdir(parents=True)
                if kind == "foreign-file":
                    command.write_text("personal command")
                else:
                    target = root / "other/setup.sh"
                    if kind == "other-checkout":
                        target.parent.mkdir()
                        target.write_text("existing Plex checkout")
                    command.symlink_to(target)
                before = os.readlink(command) if command.is_symlink() else command.read_text()
                inventory = json.dumps([{"id": "pnet-plex@pnet-plex", "scope": "user", "enabled": True}])
                with patch.dict(os.environ, {"HOME": str(home)}), \
                        patch.object(installer, "build_plugin"), \
                        patch.object(installer.shutil, "which", return_value="/bin/claude"), \
                        patch.object(installer, "run", return_value=inventory):
                    self.assertEqual(installer.main(["--host", "claude", "--project", str(project), "--yes"]), 0)
                self.assertEqual(before, os.readlink(command) if command.is_symlink() else command.read_text())
                self.assertEqual(installer.CONFIG.check_project(project, "claude")["status"], "in_sync")
                self.assertIn("Keeping existing command", output.getvalue())

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
                    patch.object(installer, "choose", side_effect=lambda label, choices, default: "no" if label == "Apply this plan?" else default), \
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
                    patch("builtins.input", side_effect=["invalid", "pnet", "inherit", "balanced", "0", "bad", "", "no"]):
                result = installer.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex", "--roles-only"])
            self.assertEqual(result, 0)
            self.assertIn("Choose a listed name", output.getvalue())
            self.assertIn("Cancelled", output.getvalue())
            self.assertIn("Enter a positive whole number", output.getvalue())
            self.assertLess(output.getvalue().index("1. inherit"), output.getvalue().index("openai-basic"))
            self.assertIn("Use client defaults for subagent models and reasoning", output.getvalue())
            self.assertIn("Mixed models for execution, planning and review", output.getvalue())
            self.assertIn("Root coordinator", output.getvalue())
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def test_shared_concurrency_prompt_persists_and_cli_can_override(self):
        spec = importlib.util.spec_from_file_location("plex_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            common = ["--project", temp, "--host", "codex", "--roles-only", "--scope", "project", "--no-instructions"]
            for default in ("3", "6"):
                with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                        patch.object(installer, "choose", side_effect=lambda label, choices, default: {
                            "Existing Plex installation": "configure", "Work mode": "pnet",
                            "Model profile": "inherit", "Interaction mode": "balanced", "Apply this plan?": "yes",
                        }.get(label, default)), \
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

    def test_missing_bmad_can_switch_to_pnet_without_initialization(self):
        spec = importlib.util.spec_from_file_location("plex_bmad_fallback", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        def choose(label, choices, default):
            if "runtime" in label:
                return "pnet"
            return "yes" if label == "Apply this plan?" else default
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), \
                patch.object(installer.sys.stdin, "isatty", return_value=True), \
                patch.object(installer, "choose", side_effect=choose), \
                patch.object(installer, "ask_text", side_effect=lambda label, default: default), \
                patch.object(installer, "plan_bmad_init") as plan:
            self.assertEqual(installer.main(["--project", temp, "--host", "codex", "--scope", "project",
                                             "--team", "bmad", "--roles-only", "--no-instructions"]), 0)
            plan.assert_not_called()
            self.assertFalse((Path(temp) / "_bmad").exists())
            self.assertEqual(json.loads((Path(temp) / ".plex/resolved.json").read_text())["team"], "pnet")

    def test_bmad_init_dry_run_never_discovers_or_writes_runtime(self):
        spec = importlib.util.spec_from_file_location("plex_bmad_preview", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), \
                patch.object(installer, "plan_bmad_init") as plan:
            self.assertEqual(installer.main(["--project", temp, "--host", "codex", "--scope", "project",
                                             "--team", "bmad", "--init-bmad", "--dry-run"]), 0)
            plan.assert_not_called()
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_bmad_dependency_installation_is_selected_and_verified_for_each_client(self):
        spec = importlib.util.spec_from_file_location("plex_bmad_dependencies", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for host, agent in installer.BMAD_AGENTS.items():
            with self.subTest(host=host), tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
                root = Path(temp)
                def run(command, project):
                    self.assertIn(installer.BMAD_SKILLS_SOURCE, command)
                    self.assertEqual(command[command.index("--agent") + 1], agent)
                    self.assertIn("bmad-agent-po", command)
                    self.assertNotIn("*", command)
                    for name in installer.bmad_required_skills():
                        path = root / name / "SKILL.md"
                        path.parent.mkdir(parents=True, exist_ok=True)
                        path.write_text("fixture")
                with patch.object(installer.shutil, "which", return_value="npx"), \
                        patch.object(installer, "bmad_user_skills", return_value=root), \
                        patch.object(installer, "run", side_effect=run):
                    installer.install_bmad_dependencies(ROOT, host)
                (root / "bmad-agent-po/SKILL.md").unlink()
                with patch.object(installer.shutil, "which", return_value="npx"), \
                        patch.object(installer, "bmad_user_skills", return_value=root), \
                        patch.object(installer, "run"):
                    with self.assertRaisesRegex(ValueError, "bmad-agent-po"):
                        installer.install_bmad_dependencies(ROOT, host)

    def test_missing_bmad_plugins_offer_installation_or_clean_cancel(self):
        spec = importlib.util.spec_from_file_location("plex_bmad_offer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        for answer in ("yes", "no"):
            with self.subTest(answer=answer), tempfile.TemporaryDirectory() as temp, \
                    redirect_stdout(io.StringIO()):
                project = Path(temp).resolve()
                plan = {"skill": project / "installed/bmad", "command": [], "answers": {}}
                def choose(label, choices, default):
                    if label == "Install required official BMad skills for this user?":
                        return answer
                    return "yes" if label == "Apply this plan?" else default
                def initialize(project, plan):
                    scripts = project / "_bmad/scripts"
                    scripts.mkdir(parents=True)
                    for name in installer.BMAD_RUNTIME_SCRIPTS:
                        (scripts / name).write_text("print('{}')")
                with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                        patch.object(installer, "choose", side_effect=choose), \
                        patch.object(installer, "ask_text", side_effect=lambda label, default: default), \
                        patch.object(installer, "plan_bmad_init", side_effect=[installer.BMadNotInstalled("missing"), plan]), \
                        patch.object(installer, "install_bmad_dependencies") as install, \
                        patch.object(installer, "initialize_bmad", side_effect=initialize):
                    self.assertEqual(installer.main(["--project", str(project), "--scope", "project", "--host", "codex",
                                                     "--team", "bmad", "--roles-only", "--no-instructions"]), 0)
                    if answer == "yes":
                        install.assert_called_once_with(project, "codex")
                        self.assertEqual(len(list((project / ".codex/agents").glob("plex-*.toml"))), 7)
                    else:
                        install.assert_not_called()
                        self.assertEqual(list(project.iterdir()), [])

    def test_bmad_init_plan_asks_only_official_questions_and_cleans_answer_file(self):
        spec = importlib.util.spec_from_file_location("plex_bmad_init", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            project = Path(temp).resolve()
            skill = project / "installed/bmad"
            questions = [{"module": "method", "key": "output.folder", "prompt": "Output folder?",
                          "default": "docs"}]
            def run(command, cwd):
                if "--list-config-questions" in command:
                    return json.dumps(questions)
                answers = Path(command[command.index("--module-answers") + 1])
                parsed = tomllib.loads(answers.read_text())
                self.assertEqual(parsed, {"modules": {"method": {"output.folder": 'a"b\nc'}}})
                runtime = project / "_bmad/scripts"
                runtime.mkdir(parents=True)
                for name in installer.BMAD_RUNTIME_SCRIPTS:
                    (runtime / name).write_text("# official fixture")
                paths.append(answers)
                return ""
            paths = []
            with patch.object(installer, "find_bmad_skill", return_value=skill), \
                    patch.object(installer.shutil, "which", return_value="uv"), \
                    patch.object(installer, "ask_text", return_value='a"b\nc') as ask, \
                    patch.object(installer, "run", side_effect=run):
                plan = installer.plan_bmad_init(project, "codex", None, True)
                ask.assert_called_once_with("Output folder?", "docs")
                self.assertFalse((project / "_bmad").exists())
                installer.initialize_bmad(project, plan)
            self.assertTrue(installer.bmad_runtime_ready(project))
            self.assertFalse(paths[0].exists())

    def test_bmad_setup_discovery_requires_enabled_installed_codex_plugin(self):
        spec = importlib.util.spec_from_file_location("plex_bmad_discovery", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp:
            home = Path(temp).resolve()
            project = home / "project"
            project.mkdir()
            skill = home / ".codex/plugins/cache/bmad/bmad-toolbox/1.0.0/skills/bmad"
            for name in ("SKILL.md", "module-manifest.toml", "scripts/setup.py", "assets/config.template.toml"):
                target = skill / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture")
            entry = {"name": "bmad-toolbox", "installed": True, "enabled": True,
                     "marketplaceName": "bmad", "version": "1.0.0"}
            with patch.dict(os.environ, {"HOME": str(home), "CODEX_HOME": str(home / ".codex")}), \
                    patch.object(installer, "run", return_value=json.dumps({"installed": [entry]})):
                self.assertEqual(installer.find_bmad_skill(project, "codex"), skill)
            for inventory in ({"installed": []}, {"installed": [{**entry, "enabled": False}]}):
                with patch.dict(os.environ, {"HOME": str(home), "CODEX_HOME": str(home / ".codex")}), \
                        patch.object(installer, "run", return_value=json.dumps(inventory)):
                    with self.assertRaisesRegex(ValueError, "Install the official BMad Toolbox"):
                        installer.find_bmad_skill(project, "codex")

    def test_interactive_bmad_init_can_be_cancelled_without_writes(self):
        spec = importlib.util.spec_from_file_location("plex_installer", ROOT / "setup.py")
        installer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(installer)
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()) as output, \
                redirect_stderr(io.StringIO()) as errors:
            with patch.object(installer.sys.stdin, "isatty", return_value=True), \
                    patch("builtins.input", side_effect=["bmad", "cancel"]), \
                    patch.object(installer, "run") as run, \
                    patch.object(installer.shutil, "which", return_value="/mock/codex"):
                result = installer.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex"])
            self.assertEqual(result, 0)
            self.assertEqual(errors.getvalue(), "")
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
