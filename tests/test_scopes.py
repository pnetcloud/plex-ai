"""Isolated installation scopes and byte-preserving managed instruction blocks."""
import importlib.util
import io
import json
import os
import shutil
from pathlib import Path
import subprocess
import sys
import tempfile
import tomllib
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('plex_scope_installer', ROOT / 'setup.py')
SETUP = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SETUP)
C = SETUP.CONFIG


class ScopeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.home = self.base / 'home'
        self.home.mkdir()
        self.project = self.base / 'project'
        self.project.mkdir()
        env = {'HOME': str(self.home), 'CODEX_HOME': str(self.home / '.codex'),
               'CLAUDE_CONFIG_DIR': str(self.home / '.claude')}
        self.env = patch.dict(os.environ, env)
        self.env.start()
        self.addCleanup(self.env.stop)

    def files(self, root):
        return {p.relative_to(root): p.read_bytes() for p in root.rglob('*') if p.is_file()}

    def test_user_roles_and_state_are_separate_for_each_host_and_project_wins(self):
        for host in C.HOSTS:
            result = C.apply_project(self.project, host, team='pnet', model_profile='inherit',
                                     scope='user', instructions=True)
            root = C.user_root(host)
            rel = C.host_agents_relpath(host, 'user')
            self.assertEqual({p.stem for p in (root / rel).glob('plex-*')},
                             {'plex-pm', 'plex-explorer', 'plex-researcher', 'plex-dev', 'plex-reviewer', 'plex-qa', 'plex-devops'})
            self.assertTrue((root / '.plex/preset.toml').is_file())
            self.assertEqual(result['scope'], 'user')
            self.assertEqual(tomllib.loads((root / '.plex/preset.toml').read_text())['interaction'], 'balanced')
            state = C.check_project(self.project, host, scope='auto')
            self.assertEqual(state['status'], 'in_sync')
            self.assertEqual(state['scope'], 'user')
        self.assertEqual(list(self.project.iterdir()), [])
        before = self.files(self.home)
        C.apply_project(self.project, 'codex', team='pnet', model_profile='openai-basic', instructions=True)
        self.assertEqual(before, self.files(self.home))
        self.assertEqual(C.check_project(self.project, 'codex', 'auto')['scope'], 'project')
        (self.project / '.codex/agents/plex-dev.toml').write_text('manual edit')
        state = C.check_project(self.project, 'codex', 'auto')
        self.assertEqual(state['status'], 'conflict')
        self.assertEqual(state['scope'], 'project')

    def test_install_refresh_and_uninstall_preserve_coordinator_state(self):
        state = self.project / ".plex/work/session-1.json"
        state.parent.mkdir(parents=True)
        sentinel = b'{"session_id":"session-1","preserve":true}\n'
        state.write_bytes(sentinel)
        for profile in ("inherit", "plus"):
            C.apply_project(self.project, "codex", team="pnet", model_profile=profile,
                            scope="project", instructions=True)
            self.assertEqual(state.read_bytes(), sentinel)
        C.uninstall_project(self.project, "codex")
        self.assertEqual(state.read_bytes(), sentinel)

    def test_instruction_template_rejects_invalid_managed_boundaries(self):
        template = self.base / 'skills/plex-setup/assets/AGENTS.md.template'
        template.parent.mkdir(parents=True)
        valid = C.PLEX_START + b'\nCustom instructions.\n' + C.PLEX_END
        with patch.object(C, 'ROOT', self.base):
            template.write_bytes(valid + b'\n')
            self.assertEqual(C.instruction_block(), valid)
            invalid = (b'No markers', C.PLEX_START, C.PLEX_END + C.PLEX_START,
                       valid + valid, b'Outside\n' + valid, valid + b'\nOutside')
            for block in invalid:
                with self.subTest(block=block):
                    template.write_bytes(block)
                    with self.assertRaises(ValueError):
                        C.instruction_block()

    def test_legacy_instruction_markers_migrate_or_uninstall_using_receipt(self):
        for action in ("refresh", "uninstall"):
            with self.subTest(action=action):
                project = self.base / action
                project.mkdir()
                file = project / "AGENTS.md"
                file.write_bytes(b"# Personal\r\nPreserve exactly.\r\n")
                C.apply_project(project, "codex", instructions=True)
                content = file.read_bytes()
                start, end = C.instruction_span(content)
                legacy = content[start:end].replace(C.PLEX_START, C.LEGACY_PLEX_MARKERS[0]).replace(C.PLEX_END, C.LEGACY_PLEX_MARKERS[1])
                file.write_bytes(content[:start] + legacy + content[end:])
                receipt_path = project / ".plex/applied.json"
                receipt = json.loads(receipt_path.read_text())
                receipt["hosts"]["codex"]["instructions"]["sha256"] = C.sha256_bytes(legacy)
                receipt_path.write_text(json.dumps(receipt))
                if action == "refresh":
                    self.assertEqual(C.check_project(project, "codex")["status"], "needs_refresh")
                    C.apply_project(project, "codex", instructions=True)
                    self.assertEqual(file.read_bytes(), content)
                    self.assertEqual(C.check_project(project, "codex")["status"], "in_sync")
                else:
                    C.uninstall_project(project, "codex")
                    self.assertTrue(file.read_bytes().startswith(b"# Personal\r\nPreserve exactly.\r\n"))
                    self.assertIsNone(C.instruction_span(file.read_bytes()))

    def test_mixed_instruction_marker_formats_are_rejected(self):
        for block in (C.PLEX_START + C.LEGACY_PLEX_MARKERS[1],
                      C.instruction_block() + C.LEGACY_PLEX_MARKERS[0] + C.LEGACY_PLEX_MARKERS[1]):
            with self.subTest(block=block), self.assertRaisesRegex(ValueError, "Mixed"):
                C.instruction_span(block)

    def test_instruction_updates_preserve_outside_bytes_and_back_up_original(self):
        file = self.project / 'AGENTS.md'
        original = b'# Personal\r\nUnrelated rules.\r\n'
        file.write_bytes(original)
        C.apply_project(self.project, 'codex', instructions=True)
        first = file.read_bytes()
        self.assertTrue(first.startswith(original))
        C.apply_project(self.project, 'codex', instructions=True)
        self.assertEqual(file.read_bytes(), first)
        outside = b'\r\n# Later notes\r\nKeep exactly.\r\n'
        file.write_bytes(first + outside)
        self.assertEqual(C.check_project(self.project, 'codex')['status'], 'in_sync')
        new_block = C.instruction_block().replace(b'## Plex agent coordination', b'## Plex coordination v2')
        with patch.object(C, 'instruction_block', return_value=new_block):
            self.assertEqual(C.check_project(self.project, 'codex')['status'], 'needs_refresh')
            result = C.apply_project(self.project, 'codex', instructions=True)
            self.assertEqual(C.check_project(self.project, 'codex')['status'], 'in_sync')
        updated = file.read_bytes()
        start, end = C.instruction_span(first)
        self.assertEqual(updated, first[:start] + new_block + first[end:] + outside)
        backup = self.project / result['backup_dir'] / 'instructions.before.md'
        self.assertEqual(backup.read_bytes(), first + outside)

    def test_manual_block_edit_and_malformed_markers_stop_before_role_changes(self):
        C.apply_project(self.project, 'codex', instructions=True)
        file = self.project / 'AGENTS.md'
        file.write_bytes(file.read_bytes().replace(b'## Plex agent coordination', b'## Manually changed coordination'))
        before = self.files(self.project)
        with self.assertRaisesRegex(ValueError, 'modified or removed'):
            C.apply_project(self.project, 'codex', model_profile='openai-plus', instructions=True)
        self.assertEqual(before, self.files(self.project))
        other = self.base / 'other'
        other.mkdir()
        (other / 'AGENTS.md').write_bytes(C.PLEX_START + b'\nmissing end')
        with self.assertRaisesRegex(ValueError, 'unbalanced'):
            C.apply_project(other, 'codex', instructions=True)
        self.assertFalse((other / '.codex/agents').exists())

    def test_override_and_fallback_selection_without_changing_global_config(self):
        root = C.user_root('codex')
        root.mkdir()
        ordinary = root / 'AGENTS.md'
        ordinary.write_text('personal ordinary')
        override = root / 'AGENTS.override.md'
        override.write_text('personal override')
        C.apply_project(self.project, 'codex', scope='user', instructions=True)
        self.assertEqual(ordinary.read_text(), 'personal ordinary')
        self.assertIn(C.PLEX_START, override.read_bytes())
        config = root / 'config.toml'
        config.write_text('project_doc_fallback_filenames = ["TEAM_GUIDE.md"]\n')
        fallback = self.project / 'TEAM_GUIDE.md'
        fallback.write_text('team instructions')
        C.apply_project(self.project, 'codex', instructions=True)
        self.assertIn(C.PLEX_START, fallback.read_bytes())
        self.assertFalse((self.project / 'AGENTS.md').exists())
        self.assertEqual(config.read_text(), 'project_doc_fallback_filenames = ["TEAM_GUIDE.md"]\n')
        (self.project / 'AGENTS.override.md').write_text('now masks the managed fallback')
        self.assertEqual(C.check_project(self.project, 'codex')['status'], 'conflict')

    def test_instruction_write_rolls_back_with_roles_and_receipt(self):
        file = self.project / 'AGENTS.md'
        file.write_text('personal text')
        original_write = C._atomic_write_bytes
        def fail_receipt(path, data):
            if path.name == 'applied.json':
                raise OSError('receipt failure')
            return original_write(path, data)
        with patch.object(C, '_atomic_write_bytes', side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, 'receipt failure'):
                C.apply_project(self.project, 'codex', instructions=True)
        self.assertEqual(file.read_text(), 'personal text')
        self.assertFalse(any((self.project / '.codex/agents').glob('plex-*')))
        self.assertFalse((self.project / '.plex/applied.json').exists())

    def test_concurrent_outside_instruction_edit_is_preserved_on_rollback(self):
        file = self.project / 'AGENTS.md'
        file.write_text('personal text')
        original_write = C._atomic_write_bytes
        edited = False
        def concurrent_edit(path, data):
            nonlocal edited
            result = original_write(path, data)
            if path.parent.name == 'agents' and not edited:
                edited = True
                file.write_text('personal text\nconcurrent user note')
            return result
        with patch.object(C, '_atomic_write_bytes', side_effect=concurrent_edit):
            with self.assertRaisesRegex(ValueError, 'Concurrent modification'):
                C.apply_project(self.project, 'codex', instructions=True)
        self.assertEqual(file.read_text(), 'personal text\nconcurrent user note')
        self.assertFalse((self.project / '.plex/applied.json').exists())

    @unittest.skipUnless(shutil.which('codex'), 'Codex CLI unavailable')
    def test_native_user_codex_install_and_config_loading(self):
        root = C.user_root('codex')
        root.mkdir()
        result = subprocess.run([sys.executable, str(ROOT / 'setup.py'), '--project', str(self.project),
            '--host', 'codex', '--scope', 'user', '--yes'], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        doctor = subprocess.run(['codex', 'doctor', '--json'], cwd=self.project,
                                capture_output=True, text=True, timeout=60)
        self.assertEqual(json.loads(doctor.stdout)['checks']['config.load']['status'], 'ok')
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertTrue((root / 'agents/plex-pm.toml').is_file())
        self.assertTrue((root / 'AGENTS.md').is_file())
        (self.project / 'AGENTS.md').write_text('PROJECT_PERSONAL_RULE_PRESERVED')
        prompt = subprocess.run(['codex', 'debug', 'prompt-input', 'Inspect configuration only'],
                               cwd=self.project, capture_output=True, text=True, timeout=60)
        self.assertEqual(prompt.returncode, 0, prompt.stderr)
        visible = json.dumps(json.loads(prompt.stdout))
        self.assertIn('plex:managed:start', visible)
        self.assertIn('PROJECT_PERSONAL_RULE_PRESERVED', visible)

    @unittest.skipUnless(shutil.which('agy'), 'Antigravity CLI unavailable')
    def test_native_user_antigravity_install_and_role_validation(self):
        result = subprocess.run([sys.executable, str(ROOT / 'setup.py'), '--project', str(self.project),
            '--host', 'antigravity', '--scope', 'user', '--yes'], capture_output=True, text=True, timeout=60)
        self.assertEqual(result.returncode, 0, result.stderr)
        config = C.user_root('antigravity') / 'config'
        (config / 'plugin.json').write_text('{"name":"disposable-role-validation"}')
        validated = subprocess.run(['agy', 'plugin', 'validate', str(config), '--strict', '--json'],
                                   capture_output=True, text=True, timeout=30)
        self.assertEqual(validated.returncode, 0, validated.stderr or validated.stdout)
        self.assertEqual(json.loads(validated.stdout)['components']['agents'], 7)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertTrue((C.user_root('antigravity') / 'GEMINI.md').is_file())

    def test_symlinked_instruction_file_is_never_followed(self):
        target = self.base / 'personal.md'
        target.write_text('outside')
        (self.project / 'AGENTS.md').symlink_to(target)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            C.apply_project(self.project, 'codex', instructions=True)
        self.assertEqual(target.read_text(), 'outside')

    def test_unattended_user_install_and_dry_run_do_not_touch_project(self):
        command = [sys.executable, str(ROOT / 'setup.py'), '--host', 'codex', '--scope', 'user',
                   '--roles-only', '--project', str(self.project)]
        dry = subprocess.run([*command, '--dry-run'], capture_output=True, text=True)
        self.assertEqual(dry.returncode, 0, dry.stderr)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.project.iterdir()), [])
        for _ in range(2):
            result = subprocess.run([*command, '--yes'], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual((C.user_root('codex') / 'AGENTS.md').read_bytes().count(C.PLEX_START), 1)
        self.assertEqual(SETUP.plugin_commands('claude', 'user')[-1][-2:], ['--scope', 'user'])

    def test_scope_menu_defaults_to_project_and_cancel_writes_nothing(self):
        seen = []
        def choose(label, choices, default):
            seen.append((label, default))
            return "no" if label == "Apply this plan?" else default
        with patch.object(SETUP.sys.stdin, 'isatty', return_value=True), \
                patch.object(SETUP, 'choose', side_effect=choose), \
                patch.object(SETUP, 'choose_clients', return_value=['codex']), \
                patch.object(SETUP, 'ask_text', side_effect=lambda label, default: default), \
                redirect_stdout(io.StringIO()):
            result = SETUP.main(['--project', str(self.project), '--roles-only'])
        self.assertEqual(result, 0)
        self.assertEqual(seen[0], ('Installation scope', 'project'))
        self.assertNotIn(('Plex instructions', 'yes'), seen)
        self.assertEqual(SETUP.plugin_commands('claude', 'project')[-1][-2:], ['--scope', 'user'])
        self.assertEqual(list(self.project.iterdir()), [])
        self.assertEqual(list(self.home.iterdir()), [])


if __name__ == '__main__':
    unittest.main()
