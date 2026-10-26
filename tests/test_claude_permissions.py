"""Managed Claude allow rules let roles read the registered Plex package without prompts."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('plex_claude_permissions', ROOT / 'skills/plex-setup/scripts/resolve_config.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


class ClaudePermissionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.settings = self.root / '.claude/settings.local.json'
        patcher = patch.dict(os.environ, {'CLAUDE_CONFIG_DIR': str(self.root / 'claude-home')})
        patcher.start()
        self.addCleanup(patcher.stop)

    def receipt(self):
        return tomllib.loads((self.root / '.plex/applied.toml').read_text())['hosts']['claude']

    def test_rules_cover_package_references_and_checkers(self):
        package = C.claude_package_root()
        rules = C.claude_permission_rules()
        self.assertEqual(rules[0], f'Read(/{package}/**)')
        self.assertIn(f'Bash(python3 {package}/skills/plex/scripts/check_assignment.py:*)', rules)
        self.assertTrue(all(str(package) in rule for rule in rules))

    def test_new_settings_are_created_owned_and_removed(self):
        C.apply_project(self.root, 'claude', team='pnet')
        allow = json.loads(self.settings.read_text())['permissions']['allow']
        self.assertEqual(allow, C.claude_permission_rules())
        self.assertEqual(self.receipt()['permissions'], {
            'relpath': '.claude/settings.local.json', 'rules': allow, 'created': True, 'package': str(C.ROOT)})
        self.assertEqual(C.check_project(self.root, 'claude')['status'], 'in_sync')
        result = C.uninstall_project(self.root, 'claude')
        self.assertTrue(result['permission_rules_removed'])
        self.assertFalse(self.settings.exists())

    def test_personal_settings_and_rules_are_preserved(self):
        package_rule = C.claude_permission_rules()[0]
        self.settings.parent.mkdir()
        self.settings.write_text(json.dumps({
            'model': 'sonnet', 'permissions': {'allow': ['Bash(npm test:*)', package_rule], 'deny': ['Read(.env)']}}))
        C.apply_project(self.root, 'claude', team='pnet')
        data = json.loads(self.settings.read_text())
        self.assertEqual(data['model'], 'sonnet')
        self.assertEqual(data['permissions']['deny'], ['Read(.env)'])
        self.assertEqual(data['permissions']['allow'][:2], ['Bash(npm test:*)', package_rule])
        owned = self.receipt()['permissions']
        self.assertNotIn(package_rule, owned['rules'])
        self.assertFalse(owned['created'])
        C.uninstall_project(self.root, 'claude')
        self.assertEqual(json.loads(self.settings.read_text()), {
            'model': 'sonnet', 'permissions': {'allow': ['Bash(npm test:*)', package_rule], 'deny': ['Read(.env)']}})

    def test_removed_owned_rule_is_a_conflict(self):
        C.apply_project(self.root, 'claude', team='pnet')
        data = json.loads(self.settings.read_text())
        data['permissions']['allow'] = data['permissions']['allow'][1:]
        self.settings.write_text(json.dumps(data))
        report = C.check_project(self.root, 'claude')
        self.assertEqual(report['status'], 'conflict')
        with self.assertRaisesRegex(ValueError, 'Claude permission rules changed or missing'):
            C.apply_project(self.root, 'claude', team='pnet')

    def test_moved_package_replaces_only_owned_rules(self):
        C.apply_project(self.root, 'claude', team='pnet')
        old = self.receipt()['permissions']['rules']
        moved = self.root / 'moved-package'
        C.apply_project(self.root, 'claude', team='pnet', claude_package=moved)
        allow = json.loads(self.settings.read_text())['permissions']['allow']
        self.assertEqual(allow, C.claude_permission_rules(package=moved))
        self.assertEqual(C.check_project(self.root, 'claude')['status'], 'in_sync')
        self.assertFalse(set(old) & set(allow))

    def test_legacy_receipt_without_rules_needs_refresh(self):
        C.apply_project(self.root, 'claude', team='pnet')
        receipt = tomllib.loads((self.root / '.plex/applied.toml').read_text())
        del receipt['hosts']['claude']['permissions']
        (self.root / '.plex/applied.toml').write_text(C.metadata_toml(receipt))
        self.settings.unlink()
        self.assertEqual(C.check_project(self.root, 'claude')['status'], 'needs_refresh')
        C.apply_project(self.root, 'claude', team='pnet')
        self.assertEqual(C.check_project(self.root, 'claude')['status'], 'in_sync')

    def test_invalid_settings_are_preserved(self):
        self.settings.parent.mkdir()
        self.settings.write_text('{not json')
        with self.assertRaisesRegex(ValueError, 'Invalid Claude settings'):
            C.apply_project(self.root, 'claude', team='pnet')
        self.assertEqual(self.settings.read_text(), '{not json')
        self.assertFalse((self.root / '.claude/agents/plex-pm.md').exists())

    def test_user_scope_uses_user_settings(self):
        C.apply_project(self.root, 'claude', team='pnet', scope='user')
        settings = self.root / 'claude-home/settings.json'
        self.assertEqual(json.loads(settings.read_text())['permissions']['allow'], C.claude_permission_rules())
        self.assertFalse(self.settings.exists())
        C.uninstall_project(self.root, 'claude', scope='user')
        self.assertFalse(settings.exists())

    def test_bmad_rules_cover_skills_without_granting_runtime_execution(self):
        C.apply_project(self.root, 'claude', team='bmad')
        allow = json.loads(self.settings.read_text())['permissions']['allow']
        self.assertIn(f'Read(/{self.root}/claude-home/skills/bmad*/**)', allow)
        self.assertFalse(any('uv run' in rule for rule in allow))
        C.apply_project(self.root, 'claude', team='pnet')
        allow = json.loads(self.settings.read_text())['permissions']['allow']
        self.assertEqual(allow, C.claude_permission_rules())
        self.assertEqual(C.check_project(self.root, 'claude')['status'], 'in_sync')

    def test_user_scope_bmad_rules_omit_project_runtime(self):
        rules = C.claude_permission_rules(process='bmad')
        self.assertTrue(any('/bmad*/**' in rule for rule in rules))
        self.assertFalse(any('_bmad/scripts' in rule for rule in rules))

    def test_permissions_rollback_with_the_existing_transaction(self):
        self.settings.parent.mkdir()
        original = b'{"model":"personal", "permissions":{"deny":["Read(.env)"]}}'
        self.settings.write_bytes(original)
        write = C._atomic_write_bytes
        def fail_receipt(path, data):
            if path.name == 'applied.toml':
                raise OSError('receipt write failed')
            return write(path, data)
        with patch.object(C, '_atomic_write_bytes', side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, 'receipt write failed'):
                C.apply_project(self.root, 'claude', team='pnet')
        self.assertEqual(self.settings.read_bytes(), original)
        self.assertFalse((self.root / '.plex/applied.toml').exists())

    def test_settings_symlink_and_concurrent_write_are_preserved(self):
        self.settings.parent.mkdir()
        external = self.root / 'external.json'
        external.write_text('{"model":"personal"}')
        self.settings.symlink_to(external)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            C.apply_project(self.root, 'claude', team='pnet')
        self.assertEqual(external.read_text(), '{"model":"personal"}')
        self.settings.unlink()
        self.settings.write_text('{}')
        write = C._atomic_write_bytes
        def race(path, data):
            result = write(path, data)
            if path == self.settings:
                self.settings.write_text('{"model":"concurrent"}')
            return result
        with patch.object(C, '_atomic_write_bytes', side_effect=race):
            with self.assertRaises(ValueError):
                C.apply_project(self.root, 'claude', team='pnet')
        self.assertEqual(json.loads(self.settings.read_text()), {'model': 'concurrent'})

    def test_quoted_package_paths_and_explicit_cache_survive_refresh(self):
        import shlex
        package = self.root / 'plugin path with spaces'
        C.apply_project(self.root, 'claude', team='pnet', claude_package=package)
        allow = json.loads(self.settings.read_text())['permissions']['allow']
        script = package / 'skills/plex/scripts/check_assignment.py'
        self.assertIn('Bash(' + shlex.join(['python3', str(script)]) + ':*)', allow)
        self.assertIn(f'Read(/{package}/**)', allow)
        before = self.settings.read_bytes()
        C.apply_project(self.root, 'claude', team='pnet')
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertEqual(self.receipt()['permissions']['package'], str(package))
        self.assertEqual(C.check_project(self.root, 'claude')['status'], 'in_sync')

    def test_other_hosts_do_not_touch_claude_settings(self):
        with patch.dict(os.environ, {'CODEX_HOME': str(self.root / 'codex-home')}):
            C.apply_project(self.root, 'antigravity', team='pnet')
        self.assertFalse(self.settings.exists())


if __name__ == '__main__':
    unittest.main()
