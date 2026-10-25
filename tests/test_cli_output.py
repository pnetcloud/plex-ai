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
        with tempfile.TemporaryDirectory(prefix="plex cli ") as temp, tempfile.TemporaryDirectory() as home, redirect_stdout(io.StringIO()) as output:
            codex_home = Path(home)
            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
                self.assertEqual(S.main(["--project", temp, "--client", "codex", "--model-profile", "plus", "--dry-run"]), 0)
            text = output.getvalue()
            self.assertIn("Installation plan", text)
            self.assertIn("Skills and dependencies", text)
            self.assertIn("Plex assignments", text)
            self.assertIn("Codex limit", text)
            self.assertIn("primary excluded", text)
            self.assertIn("Session activation", text)
            self.assertIn("AGENT", text)
            self.assertIn("REASONING", text)
            self.assertIn("plex-dev", text)
            self.assertIn("Root coordinator · your main chat", text)
            self.assertIn("gpt-6-luna / high", text)
            self.assertLess(text.index("Root coordinator"), text.index("SUBAGENT"))
            self.assertIn("$ codex plugin marketplace add", text)
            self.assertNotIn("<!-- plex:managed:start -->", text)
            self.assertNotIn("\033[", text)
            self.assertEqual(list(Path(temp).iterdir()), [])
        with redirect_stdout(io.StringIO()) as output:
            S.show_command(["plex", "--project", "/a path/with spaces"])
        self.assertIn("$ plex --project '/a path/with spaces'", output.getvalue())

    def test_coordinator_guidance_follows_profile_without_becoming_a_role(self):
        expected = {
            "pnet": {
                "basic": "gpt-6-luna / high", "plus": "gpt-6-luna / high",
                "pro": "gpt-6-luna / xhigh", "pro-plus": "gpt-6-luna / max",
                "ultra": "gpt-6.1-sol / low", "ultra-plus": "gpt-6.1-sol / high",
            },
            "bmad": {
                "basic": "gpt-6-luna / high", "plus": "gpt-6-luna / high",
                "pro": "gpt-6-luna / xhigh", "pro-plus": "gpt-6-luna / xhigh",
                "ultra": "gpt-6.1-sol / medium", "ultra-plus": "gpt-6.1-sol / high",
            },
        }
        for team in ("pnet", "bmad"):
            for tier, text in expected[team].items():
                for profile in (tier, f"openai-{tier}"):
                    with self.subTest(team=team, profile=profile), redirect_stdout(io.StringIO()) as output:
                        resolved = S.CONFIG.resolve({"team": team, "model_profile": profile})
                        S.coordinator_summary(resolved, "codex")
                        self.assertIn(text, output.getvalue())
                        self.assertIn("Plex keeps your session model", " ".join(output.getvalue().split()))
                        self.assertNotIn("coordinator", resolved["roles"])
                        self.assertNotIn("coordinator", S.CONFIG.render_host_roles(resolved, "codex"))
        for host in S.CONFIG.HOSTS:
            with self.subTest(host=host), redirect_stdout(io.StringIO()) as output:
                S.coordinator_summary(S.CONFIG.resolve({"team": "pnet"}), host)
                self.assertIn("no profile recommendation", output.getvalue())

    def test_fields_separate_long_labels_and_align_continuation_lines(self):
        with redirect_stdout(io.StringIO()) as output:
            S.field("Project skills", ".agents/skills/plex\n.agents/skills/plex-setup")
            S.field("A longer field label", "value\ncontinued")
        lines = output.getvalue().splitlines()
        self.assertIn("Project skills  .agents/skills/plex", lines[0])
        self.assertEqual(lines[0].index(".agents"), lines[1].index(".agents"))
        self.assertIn("A longer field label  value", lines[2])
        self.assertEqual(lines[2].index("value"), lines[3].index("continued"))

    def test_planned_lower_native_limit_is_reported_separately(self):
        current = {"value": 4, "origin": "plex", "mismatch": False, "activation": "unknown"}
        planned = {"value": 2, "origin": "inherited", "mismatch": True, "uncertain": False}
        with redirect_stdout(io.StringIO()) as output:
            S.capacity_summary(current, planned)
        text = output.getvalue()
        self.assertIn("Codex limit", text)
        self.assertIn("Planned limit", text)
        self.assertIn("planned native thread limit is below", text)

    def test_uncertain_native_value_keeps_saved_target_separate(self):
        current = {
            "value": None, "origin": "unknown", "mismatch": None,
            "activation": "unknown", "uncertain": True,
            "saved_target": {"value": 4, "origin": "plex"},
        }
        with redirect_stdout(io.StringIO()) as output:
            S.capacity_summary(current, current)
        self.assertIn("Codex limit", output.getvalue())
        self.assertIn("Saved target", output.getvalue())
        self.assertIn("4 max open child threads · plex", output.getvalue())

    def test_capacity_preview_guard_checks_target_and_inherited_inputs(self):
        with tempfile.TemporaryDirectory() as temp, tempfile.TemporaryDirectory() as home:
            project = Path(temp)
            codex_home = Path(home)
            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
                plan = S.CONFIG.plan_codex_routing(project, "project", max_agents=4)
                S.check_capacity_preview(plan)
                config = project / ".codex/config.toml"
                config.parent.mkdir(parents=True)
                config.write_text("# changed after preview\n")
                with self.assertRaisesRegex(ValueError, "Codex config changed after preview"):
                    S.check_capacity_preview(plan)

                config.unlink()
                plan = S.CONFIG.plan_codex_routing(project, "project", max_agents=4)
                (codex_home / "config.toml").write_text("[agents]\nmax_threads = 2\n")
                with self.assertRaisesRegex(ValueError, "Inherited Codex config changed"):
                    S.check_capacity_preview(plan)

    def test_status_json_stays_clean_even_on_a_color_terminal(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)
            codex_home = project / "codex-home"
            codex_home.mkdir()
            with patch.dict(os.environ, {"CODEX_HOME": str(codex_home)}):
                S.CONFIG.apply_project(project, "codex", max_agents=4)
                with redirect_stdout(Terminal()) as output, patch.object(S, "verify_plugin"), \
                        patch.object(S.shutil, "which", return_value="/stub/codex"), \
                        patch.dict(os.environ, {"TERM": "xterm", "CODEX_HOME": str(codex_home)}, clear=True):
                    self.assertEqual(S.main(["status", "--project", temp, "--client", "codex", "--json"]), 0)
            data = json.loads(output.getvalue())
            self.assertEqual(data["clients"][0]["status"], "in_sync")
            self.assertEqual(data["clients"][0]["native_capacity"]["assignment_limit"], 4)
            self.assertEqual(data["clients"][0]["native_capacity"]["value"], 4)
            self.assertEqual(data["clients"][0]["native_capacity"]["activation"], "unknown")
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
