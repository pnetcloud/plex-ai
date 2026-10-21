"""Custom selection, persistence and keyboard interaction without model calls."""

from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
from pathlib import Path
import shutil
import tempfile
import tomllib
import unittest
from unittest.mock import patch

import questionary
from prompt_toolkit.input import create_pipe_input
from prompt_toolkit.output import DummyOutput


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plex_setup", ROOT / "setup.py")
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)
CONFIG = SETUP.CONFIG
MODELS = {
    "test-fast": {"supported_reasoning_levels": [{"effort": "low"}, {"effort": "medium"}]},
    "test-strong": {"supported_reasoning_levels": [{"effort": "high"}, {"effort": "max"}]},
}


class CustomSetupTests(unittest.TestCase):
    def test_team_switch_with_missing_profile_offers_selection_without_writes(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            root = Path(temp).resolve()
            project = root / "project"
            project.mkdir()
            shutil.copytree(ROOT / "teams", root / "teams")
            CONFIG.apply_project(project, "codex", team="bmad", model_profile="openai-plus")
            before = (project / ".plex/preset.toml").read_bytes()
            (root / "teams/pnet/profiles/openai.toml").unlink()
            menus = []
            def select(label, choices, default):
                if label == "Model profile":
                    menus.append(choices)
                    return "inherit"
                return "no" if label == "Apply this plan?" else default
            with patch.object(CONFIG, "ROOT", root), \
                    patch.object(SETUP.sys.stdin, "isatty", return_value=True), \
                    patch.object(SETUP, "choose", side_effect=select):
                result = SETUP.main(["--scope", "project", "--no-instructions", "--project", str(project),
                                     "--host", "codex", "--team", "pnet", "--max-agents", "3", "--dry-run"])
            self.assertEqual(result, 0)
            self.assertEqual(list(menus[0]), ["inherit", "custom"])
            self.assertEqual((project / ".plex/preset.toml").read_bytes(), before)

    def test_profile_menu_filters_hosts_and_preserves_selection(self):
        for host, saved, expected in [
            ("codex", "openai-plus", "openai-plus"),
            ("claude", "anthropic-pro", "anthropic-pro"),
            ("antigravity", "google-pro", "google-pro"),
            ("codex", "anthropic-pro", "custom"),
        ]:
            with self.subTest(host=host, saved=saved), tempfile.TemporaryDirectory() as temp, \
                    redirect_stdout(io.StringIO()):
                project = Path(temp).resolve()
                CONFIG.apply_project(project, host, team="pnet", model_profile=saved)
                before = (project / ".plex/preset.toml").read_bytes()
                menus = []
                def select(label, choices, default):
                    if label == "Model profile":
                        menus.append((choices, default))
                        return "inherit"
                    return "no" if label == "Apply this plan?" else default
                with patch.object(SETUP.sys.stdin, "isatty", return_value=True), \
                        patch.object(SETUP, "choose", side_effect=select), \
                        patch.object(SETUP, "ask_text", side_effect=lambda label, default: default):
                    result = SETUP.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", host, "--team", "pnet", "--roles-only"])
                self.assertEqual(result, 0)
                choices, default = menus[0]
                self.assertEqual(default, expected)
                self.assertEqual(list(choices)[0], "inherit")
                self.assertIn("custom", choices)
                if host == "codex":
                    self.assertEqual(list(choices), ["inherit", "openai-basic", "openai-plus", "openai-pro", "openai-pro-plus", "custom"])
                elif host == "claude":
                    self.assertEqual(list(choices), ["inherit", "anthropic-basic", "anthropic-plus", "anthropic-pro", "anthropic-pro-plus", "custom"])
                else:
                    self.assertEqual(
                        list(choices),
                        [
                            "inherit",
                            "google-basic",
                            "google-plus",
                            "google-pro",
                            "google-pro-plus",
                            "google-anthropic-basic",
                            "google-anthropic-plus",
                            "google-anthropic-pro",
                            "google-anthropic-pro-plus",
                            "custom",
                        ],
                    )
                self.assertEqual((project / ".plex/preset.toml").read_bytes(), before)

    def test_client_checkboxes_use_space_and_validate_empty_selection(self):
        checkbox = questionary.checkbox
        cases = [("\x1b[B \r", ['codex', 'claude']),
                 (" \r\x1b[B \r", ['claude']),
                 ("\x03", None)]
        for keys, expected in cases:
            with self.subTest(keys=keys), create_pipe_input() as pipe:
                pipe.send_text(keys)
                def prompt(*args, **kwargs):
                    return checkbox(*args, **kwargs, input=pipe, output=DummyOutput())
                with patch.object(SETUP, 'terminal_ui', return_value=questionary), \
                        patch.object(questionary, 'checkbox', side_effect=prompt):
                    if expected is None:
                        with self.assertRaises(KeyboardInterrupt):
                            SETUP.choose_clients()
                    else:
                        self.assertEqual(SETUP.choose_clients(), expected)

    def test_multiple_clients_share_one_profile_and_switch_together(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            project = Path(temp).resolve()
            seen = []
            def choose(label, choices, default):
                seen.append(label)
                if label == 'Model profile':
                    self.assertEqual(list(choices), ['inherit', 'basic', 'plus', 'pro', 'pro-plus'])
                    return 'plus'
                return 'yes' if label == 'Apply this plan?' else default
            with patch.object(SETUP.sys.stdin, 'isatty', return_value=True), \
                    patch.object(SETUP, 'choose_clients', return_value=list(CONFIG.HOSTS)), \
                    patch.object(SETUP, 'choose', side_effect=choose), \
                    patch.object(SETUP, 'ask_text', side_effect=lambda label, default: default):
                self.assertEqual(SETUP.main(['--project', temp, '--roles-only', '--max-agents', '3']), 0)
            config = tomllib.loads((project / '.plex/preset.toml').read_text())
            self.assertEqual(config['model_profile'], 'plus')
            self.assertNotIn('model_profiles', config)
            self.assertEqual(seen.count('Installation scope'), 1)
            self.assertEqual(seen.count('Work mode'), 1)
            self.assertEqual(seen.count('Model profile'), 1)
            expected = CONFIG.resolve(config)
            for host, vendor in [('codex','openai'), ('claude','anthropic'), ('antigravity','google')]:
                self.assertEqual(CONFIG.check_project(project, host)['status'], 'in_sync')
                standalone = CONFIG.resolve({'team':'pnet', 'model_profile':f'{vendor}-plus'})
                self.assertEqual(expected['hosts'][host], standalone['hosts'][host])
            self.assertEqual(SETUP.main(['--project', temp, '--client', 'claude', '--roles-only', '--yes', '--model-profile', 'pro']), 0)
            updated = tomllib.loads((project / '.plex/preset.toml').read_text())
            self.assertEqual(updated['model_profile'], 'pro')
            for host in CONFIG.HOSTS:
                self.assertEqual(CONFIG.check_project(project, host)['status'], 'in_sync')
            (project / '.claude/agents/plex-dev.md').write_text('Manual edit')
            before = {p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()}
            with redirect_stderr(io.StringIO()):
                self.assertEqual(SETUP.main(['--project', temp, '--client', 'codex', '--roles-only', '--yes', '--model-profile', 'basic']), 1)
            self.assertEqual(before, {p.relative_to(project):p.read_bytes() for p in project.rglob('*') if p.is_file()})

    def test_multi_client_preview_and_cancel_do_not_write(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            args = ['--project', temp, '--client', 'codex', '--client', 'claude', '--roles-only']
            self.assertEqual(SETUP.main([*args, '--dry-run']), 0)
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])
            with patch.object(SETUP.sys.stdin, 'isatty', return_value=True), \
                    patch.object(SETUP, 'choose', side_effect=lambda label, choices, default: "no" if label == "Apply this plan?" else default), \
                    patch.object(SETUP, 'ask_text', side_effect=lambda label, default: default):
                self.assertEqual(SETUP.main(args), 0)
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def test_arrow_keys_return_value_and_control_c_interrupts(self):
        select = questionary.select
        for keys, expected in [("\x1b[B\r", "custom"), ("\x03", None)]:
            with self.subTest(keys=keys), create_pipe_input() as pipe:
                pipe.send_text(keys)
                def prompt(*args, **kwargs):
                    return select(*args, **kwargs, input=pipe, output=DummyOutput())
                with patch.object(SETUP, "terminal_ui", return_value=questionary), \
                        patch.object(questionary, "select", side_effect=prompt):
                    if expected is None:
                        with self.assertRaises(KeyboardInterrupt):
                            SETUP.choose("Profile", {"inherit": "Defaults", "custom": "Edit"}, "inherit")
                    else:
                        self.assertEqual(SETUP.choose("Profile", {"inherit": "Defaults", "custom": "Edit"}, "inherit"), expected)

    def test_custom_apply_repeat_and_other_host_settings_survive(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            project = Path(temp).resolve()
            CONFIG.apply_project(project, "codex", team="pnet", host_overrides={
                "claude": {"pm": {"model": "opus"}},
                "codex": {"architect": {"reasoning": "high"}},
            })
            answers = ["configure", "pnet", "custom", "pm", "test-strong", "max", "dev", "test-fast", "low",
                       "__done__", "balanced", "yes"]
            with patch.object(SETUP.sys.stdin, "isatty", return_value=True), \
                    patch.object(SETUP, "choose", side_effect=answers), \
                    patch.object(SETUP, "model_catalog", return_value=MODELS), \
                    patch.object(SETUP, "ask_text", side_effect=lambda label, default: default):
                result = SETUP.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex", "--roles-only"])
            self.assertEqual(result, 0)
            source = project / ".plex/preset.toml"
            config = tomllib.loads(source.read_text())
            self.assertEqual(config["model_profile"], "inherit")
            self.assertEqual(config["claude"]["pm"], {"model": "opus"})
            self.assertEqual(config["codex"]["architect"], {"reasoning": "high"})
            pm = tomllib.loads((project / ".codex/agents/plex-pm.toml").read_text())
            self.assertEqual((pm["model"], pm["model_reasoning_effort"]), ("test-strong", "max"))
            dev = tomllib.loads((project / ".codex/agents/plex-dev.toml").read_text())
            self.assertEqual((dev["model"], dev["model_reasoning_effort"]), ("test-fast", "low"))
            before = source.read_bytes()
            CONFIG.apply_project(project, "codex")
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(CONFIG.check_project(project, "codex")["status"], "in_sync")

    def test_custom_cancel_does_not_write(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()):
            with patch.object(SETUP.sys.stdin, "isatty", return_value=True), \
                    patch.object(SETUP, "choose", side_effect=["pnet", "custom", KeyboardInterrupt]), \
                    patch.object(SETUP, "model_catalog", return_value=MODELS), \
                    patch.object(SETUP, "ask_text", side_effect=lambda label, default: default):
                result = SETUP.main(["--scope", "project", "--no-instructions", "--project", temp, "--host", "codex", "--roles-only"])
            self.assertEqual(result, 130)
            self.assertEqual(list(Path(temp).resolve().iterdir()), [])

    def test_model_specific_reasoning_and_default_remove_role_override(self):
        config = {"team": "pnet", "codex": {"pm": {"model": "old", "reasoning": "max"}}}
        original = json.dumps(config)
        with redirect_stdout(io.StringIO()), patch.object(SETUP, "model_catalog", return_value=MODELS), \
                patch.object(SETUP, "choose", side_effect=["pm", "test-fast", "low", "__done__"]) as choose:
            overrides = SETUP.customize_roles(config, "codex", ROOT)
        self.assertEqual(json.dumps(config), original)
        self.assertNotIn("max", choose.call_args_list[2].args[1])
        self.assertEqual(overrides["codex"]["pm"], {"model": "test-fast", "reasoning": "low"})
        with redirect_stdout(io.StringIO()), patch.object(SETUP, "model_catalog", return_value=MODELS), \
                patch.object(SETUP, "choose", side_effect=["pm", "__default__", "__default__", "__done__"]):
            cleared = SETUP.customize_roles(config, "codex", ROOT)
        self.assertEqual(cleared["codex"]["pm"], {})

    def test_claude_custom_model_effort_and_yaml_are_valid(self):
        import yaml
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()), \
                patch.object(SETUP, "choose", side_effect=["pm", "__manual__", "high", "__done__"]), \
                patch.object(SETUP, "ask_text", return_value="provider/model#custom"):
            overrides = SETUP.customize_roles({"team": "pnet"}, "claude", ROOT)
            CONFIG.apply_project(Path(temp).resolve(), "claude", team="pnet", host_overrides=overrides)
            role = (Path(temp).resolve() / ".claude/agents/plex-pm.md").read_text()
            header = yaml.safe_load(role.split("---", 2)[1])
            self.assertEqual(header["model"], "provider/model#custom")
            self.assertEqual(header["effort"], "high")
            self.assertEqual(CONFIG.check_project(Path(temp).resolve(), "claude")["status"], "in_sync")

    def test_catalog_failure_offers_unverified_fallback(self):
        with redirect_stdout(io.StringIO()) as output, \
                patch.object(SETUP.subprocess, "run", side_effect=FileNotFoundError):
            models = SETUP.model_catalog("codex", ROOT)
        self.assertIn("gpt-6-luna", models)
        self.assertIn("unverified", output.getvalue())

    def test_invalid_custom_settings_do_not_replace_existing_configuration(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp).resolve()
            CONFIG.apply_project(project, "codex", team="pnet")
            before = {p: p.read_bytes() for p in project.rglob("*") if p.is_file()}
            with self.assertRaises(ValueError):
                CONFIG.apply_project(project, "codex", host_overrides={"codex": {"pm": {"model": "bad model"}}})
            self.assertEqual(before, {p: p.read_bytes() for p in project.rglob("*") if p.is_file()})


if __name__ == "__main__":
    unittest.main()
