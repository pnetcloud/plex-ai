"""Human output, terminal styling and clean machine-readable CLI responses."""
from contextlib import redirect_stdout, redirect_stderr
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("plex_cli_output", ROOT / "setup.py")
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)


class Terminal(io.StringIO):
    def isatty(self):
        return True


class OutputTests(unittest.TestCase):
    def test_styles_follow_each_stream_and_respect_plain_terminal_settings(self):
        with patch.dict(os.environ, {"TERM": "xterm"}, clear=True), redirect_stdout(Terminal()):
            self.assertIn("\033[", S.style("Ready", "ok"))
            self.assertNotIn("\033[", S.style("Ready", "ok", file=io.StringIO()))
            with patch.dict(os.environ, {"NO_COLOR": ""}):
                self.assertEqual(S.style("Ready", "ok"), "Ready")
                self.assertIsNone(S.terminal_ui())
            with patch.dict(os.environ, {"TERM": "dumb"}):
                self.assertEqual(S.style("Ready", "ok"), "Ready")
                self.assertIsNone(S.terminal_ui())
        with redirect_stdout(io.StringIO()):
            self.assertEqual(S.style("Ready", "ok"), "Ready")

    def test_preview_has_compact_sections_and_copyable_commands_without_template_dump(self):
        with tempfile.TemporaryDirectory(prefix="plex cli ") as temp, redirect_stdout(io.StringIO()) as output:
            self.assertEqual(S.main(["--project", temp, "--client", "codex", "--model-profile", "plus", "--dry-run"]), 0)
            text = output.getvalue()
            self.assertIn("Installation plan", text)
            self.assertIn("Skills and dependencies", text)
            self.assertIn("AGENT", text)
            self.assertIn("REASONING", text)
            self.assertIn("plex-dev", text)
            self.assertIn("$ codex plugin marketplace add", text)
            self.assertNotIn("<!-- plex:managed:start -->", text)
            self.assertNotIn("\033[", text)
            self.assertEqual(list(Path(temp).iterdir()), [])
        with redirect_stdout(io.StringIO()) as output:
            S.show_command(["plex", "--project", "/a path/with spaces"])
        self.assertIn("$ plex --project '/a path/with spaces'", output.getvalue())

    def test_status_json_stays_clean_even_on_a_color_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            S.CONFIG.apply_project(project, "codex")
            with redirect_stdout(Terminal()) as output, patch.object(S, "verify_plugin"), \
                    patch.object(S.shutil, "which", return_value="/stub/codex"), \
                    patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
                self.assertEqual(S.main(["status", "--project", temp, "--client", "codex", "--json"]), 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["clients"][0]["status"], "in_sync")
            self.assertNotIn("\033[", output.getvalue())

    def test_uninstall_human_preview_and_json_preview_removal_and_cancel(self):
        for json_mode in (False, True):
            with self.subTest(json=json_mode), tempfile.TemporaryDirectory() as temp:
                project = Path(temp)
                S.CONFIG.apply_project(project, "codex", instructions=True)
                options = ["uninstall", "--project", temp, "--client", "codex"] + (["--json"] if json_mode else [])
                with redirect_stdout(Terminal()) as output:
                    self.assertEqual(S.main([*options, "--dry-run"]), 0)
                if json_mode:
                    self.assertEqual(json.loads(output.getvalue())[0]["status"], "planned")
                    with redirect_stdout(Terminal()) as output, redirect_stderr(io.StringIO()) as errors, \
                            patch.object(S.sys.stdin, "isatty", return_value=True), patch("builtins.input", return_value="no"):
                        self.assertEqual(S.main(options), 0)
                    self.assertEqual(json.loads(output.getvalue()), [])
                    self.assertIn("Remove these Plex roles", errors.getvalue())
                else:
                    self.assertIn("Removal preview", output.getvalue())
                    self.assertIn("Remove roles", output.getvalue())
                    self.assertNotIn('"removed_roles"', output.getvalue())
                self.assertTrue((project / ".codex/agents/plex-dev.toml").exists())
                with redirect_stdout(Terminal()) as output:
                    self.assertEqual(S.main([*options, "--yes"]), 0)
                if json_mode:
                    self.assertEqual(json.loads(output.getvalue())[0]["status"], "uninstalled")
                    self.assertNotIn("\033[", output.getvalue())
                else:
                    self.assertIn("Uninstall complete", output.getvalue())
                    self.assertIn("Backups", output.getvalue())
                self.assertFalse((project / ".codex/agents/plex-dev.toml").exists())

    def test_narrow_output_wraps_notes_and_stacks_roles(self):
        with patch.object(S.shutil, "get_terminal_size", return_value=os.terminal_size((40, 20))), \
                redirect_stdout(io.StringIO()) as output:
            S.notice("Keep the current project settings and refresh the managed files only.", "warn")
            self.assertTrue(all(len(line) <= 40 for line in output.getvalue().splitlines()))
        with patch.object(S.shutil, "get_terminal_size", return_value=os.terminal_size((40, 20))), \
                redirect_stdout(io.StringIO()) as output:
            S.role_table({"researcher": {"model": "a-long-provider-model-name", "reasoning": "high"}})
        self.assertIn("plex-researcher\n    a-long-provider-model-name / high", output.getvalue())

    def test_help_is_grouped_and_does_not_require_optional_ui_dependencies(self):
        with redirect_stdout(io.StringIO()) as output, self.assertRaises(SystemExit) as exit:
            S.main(["--help"])
        self.assertEqual(exit.exception.code, 0)
        for label in ("usage: plex", "Clients and scope", "Team and models", "BMad dependencies", "Execution and output", "Source updates", "Examples:"):
            self.assertIn(label, output.getvalue())
        self.assertNotIn("\033[", output.getvalue())

    def test_configuration_errors_style_stderr_without_contaminating_stdout(self):
        with tempfile.TemporaryDirectory() as temp, redirect_stdout(io.StringIO()) as output, \
                redirect_stderr(Terminal()) as errors, patch.dict(os.environ, {"TERM": "xterm"}, clear=True):
            self.assertEqual(S.CONFIG.main(["resolve", str(Path(temp) / "missing.toml")]), 1)
        self.assertEqual(output.getvalue(), "")
        self.assertIn("\033[1;31mERROR", errors.getvalue())

    def test_downloaded_bootstrap_remains_standalone(self):
        with tempfile.TemporaryDirectory() as temp:
            script = Path(temp) / "releases.py"
            shutil.copy2(ROOT / "skills/plex-setup/scripts/releases.py", script)
            result = subprocess.run([sys.executable, str(script), "--help"], capture_output=True, text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("--release", result.stdout)
            self.assertNotIn("\033[", result.stdout)
