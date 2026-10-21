"""Managed native selection preserves personal config through the full lifecycle."""
import importlib.util
import json
from pathlib import Path
import tempfile
import tomllib
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('plex_routing_config', ROOT / 'skills/plex-setup/scripts/resolve_config.py')
C = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(C)


class NativeRoutingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = self.root / '.codex/config.toml'
        self.config.parent.mkdir()

    def test_apply_refresh_and_uninstall_preserve_personal_config(self):
        personal = '# personal\nmodel = "unchanged"\n[features.multi_agent_v2]\nwait_agent_enabled = true\n'
        self.config.write_text(personal)
        C.apply_project(self.root, 'codex', team='pnet', interaction='auto')
        installed = self.config.read_bytes()
        self.assertEqual(tomllib.loads(installed.decode())['features']['multi_agent_v2']['hide_spawn_agent_metadata'], False)
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')
        C.apply_project(self.root, 'codex')
        self.assertEqual(self.config.read_bytes(), installed)
        # An unrelated subsequent setting in the same table survives removal.
        self.config.write_text(self.config.read_text() + 'disable_direct_message = true\n')
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')
        self.assertTrue(C.uninstall_project(self.root, 'codex', dry_run=True)['routing_settings_removed'])
        self.assertTrue(C.uninstall_project(self.root, 'codex')['routing_settings_removed'])
        self.assertEqual(self.config.read_text(), personal + 'disable_direct_message = true\n')

    def test_existing_matching_values_are_not_adopted(self):
        original = '[features.multi_agent_v2]\nhide_spawn_agent_metadata = false\ntool_namespace = "agents"\n'
        self.config.write_text(original)
        C.apply_project(self.root, 'codex', team='pnet')
        C.uninstall_project(self.root, 'codex')
        self.assertEqual(self.config.read_text(), original)

    def test_conflicts_symlinks_and_modified_blocks_are_preserved(self):
        self.config.write_text('[features.multi_agent_v2]\nhide_spawn_agent_metadata = true\n')
        original = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'personal setting preserved'):
            C.apply_project(self.root, 'codex', team='pnet')
        self.assertEqual(self.config.read_bytes(), original)
        self.assertFalse((self.root / '.plex/applied.json').exists())
        self.config.unlink()
        target = self.root / 'personal.toml'
        target.write_bytes(original)
        self.config.symlink_to(target)
        with self.assertRaises(ValueError):
            C.apply_project(self.root, 'codex', team='pnet')
        self.assertEqual(target.read_bytes(), original)
        self.config.unlink()
        C.apply_project(self.root, 'codex', team='pnet')
        self.config.write_text(self.config.read_text().replace('tool_namespace = "agents"', 'tool_namespace = "personal"'))
        modified = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'preserved'):
            C.uninstall_project(self.root, 'codex')
        self.assertEqual(self.config.read_bytes(), modified)
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'conflict')

    def test_write_failure_rolls_back_roles_config_and_receipt(self):
        self.config.write_text('# original\n')
        original = C._atomic_write_bytes
        def fail_receipt(path, data):
            if path.name == 'applied.json':
                raise OSError('injected receipt failure')
            return original(path, data)
        with patch.object(C, '_atomic_write_bytes', side_effect=fail_receipt):
            with self.assertRaisesRegex(OSError, 'injected'):
                C.apply_project(self.root, 'codex', team='pnet')
        self.assertEqual(self.config.read_text(), '# original\n')
        self.assertEqual(list((self.root / '.codex/agents').glob('*.toml')), [])
        self.assertFalse((self.root / '.plex/applied.json').exists())

    def test_legacy_install_requires_refresh_for_native_controls(self):
        C.apply_project(self.root, 'codex', team='pnet')
        receipt = self.root / '.plex/applied.json'
        saved = json.loads(receipt.read_text())
        saved['hosts']['codex'].pop('routing')
        receipt.write_text(json.dumps(saved))
        self.config.write_text('# legacy personal config\n')
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'needs_refresh')
        C.apply_project(self.root, 'codex')
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')
        self.assertTrue(self.config.read_text().startswith('# legacy personal config\n'))
