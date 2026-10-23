"""Managed native selection preserves personal config through the full lifecycle."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
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
        self.codex_home = self.root / 'codex-home'
        self.codex_home.mkdir()
        patcher = patch.dict(os.environ, {'CODEX_HOME': str(self.codex_home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_apply_refresh_and_uninstall_preserve_personal_config(self):
        personal = '# personal\nmodel = "unchanged"\n[features.multi_agent_v2]\nwait_agent_enabled = true\n'
        self.config.write_text(personal)
        C.apply_project(self.root, 'codex', team='pnet', interaction='auto', max_agents=4)
        installed = self.config.read_bytes()
        self.assertEqual(tomllib.loads(installed.decode())['features']['multi_agent_v2']['hide_spawn_agent_metadata'], False)
        self.assertEqual(tomllib.loads(installed.decode())['agents']['max_concurrent_threads_per_session'], 4)
        receipt = json.loads((self.root / '.plex/applied.json').read_text())['hosts']['codex']
        self.assertIn('capacity', receipt)
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')
        C.apply_project(self.root, 'codex')
        self.assertEqual(self.config.read_bytes(), installed)
        # An unrelated subsequent setting in the same table survives removal.
        self.config.write_text(self.config.read_text() + 'disable_direct_message = true\n')
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')
        self.assertTrue(C.uninstall_project(self.root, 'codex', dry_run=True)['routing_settings_removed'])
        self.assertTrue(C.uninstall_project(self.root, 'codex')['routing_settings_removed'])
        self.assertEqual(self.config.read_text(), personal + '\n[agents]\ndisable_direct_message = true\n')

    def test_existing_matching_values_are_not_adopted(self):
        original = '[features.multi_agent_v2]\nhide_spawn_agent_metadata = false\ntool_namespace = "agents"\n'
        self.config.write_text(original)
        C.apply_project(self.root, 'codex', team='pnet')
        C.uninstall_project(self.root, 'codex')
        self.assertEqual(self.config.read_text(), original + '\n[agents]\n')

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

    def test_capacity_aliases_and_invalid_values_are_deterministic(self):
        cases = (
            ('canonical', '[agents]\nmax_concurrent_threads_per_session = 3\n', 3, None, 3),
            ('legacy', '[agents]\nmax_threads = 2\n', None, 2, 2),
            ('equal-aliases', '[agents]\nmax_concurrent_threads_per_session = 4\nmax_threads = 4\n', 4, 4, 4),
            ('canonical-max', f'[agents]\nmax_concurrent_threads_per_session = {C.NATIVE_CODEX_INTEGER_MAX}\n', C.NATIVE_CODEX_INTEGER_MAX, None, C.NATIVE_CODEX_INTEGER_MAX),
        )
        for name, config, canonical, legacy, expected in cases:
            with self.subTest(name=name):
                self.config.write_text(config)
                C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
                parsed = tomllib.loads(self.config.read_text())['agents']
                self.assertEqual(parsed.get('max_concurrent_threads_per_session'), canonical)
                self.assertEqual(parsed.get('max_threads'), legacy)
                self.assertNotIn('capacity', json.loads((self.root / '.plex/applied.json').read_text())['hosts']['codex'])
                native = C.check_project(self.root, 'codex')['hosts']['codex']['native_capacity']
                self.assertEqual(native['value'], expected)
                self.assertEqual(native['mismatch'], expected < 4)
                C.uninstall_project(self.root, 'codex')
                self.assertEqual(self.config.read_text(), config + '\n[features.multi_agent_v2]\n')
                for child in self.root.iterdir():
                    if child.name != 'codex-home':
                        if child.is_dir():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
                self.config.parent.mkdir(parents=True, exist_ok=True)

        invalid = (
            '[agents]\nmax_concurrent_threads_per_session = true\n',
            '[agents]\nmax_concurrent_threads_per_session = 1.5\n',
            '[agents]\nmax_threads = 0\n',
            '[agents]\nmax_concurrent_threads_per_session = 5\nmax_threads = 4\n',
            f'[agents]\nmax_concurrent_threads_per_session = {C.NATIVE_CODEX_INTEGER_MAX + 1}\n',
            '[agents]\nmax_threads = 1000000000000000000000000000000\n',
        )
        for config in invalid:
            with self.subTest(config=config):
                self.config.write_text(config)
                before = self.config.read_bytes()
                with self.assertRaises(ValueError):
                    C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
                self.assertEqual(self.config.read_bytes(), before)
                self.assertFalse((self.root / '.plex/applied.json').exists())
                for child in self.root.iterdir():
                    if child.name != 'codex-home':
                        if child.is_dir():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
                self.config.parent.mkdir(parents=True, exist_ok=True)

    def test_generated_codex_capacity_has_proven_signed_64bit_boundary(self):
        for index, limit in enumerate((C.NATIVE_CODEX_INTEGER_MAX + 1, 10**30)):
            with self.subTest(limit=limit):
                project = self.root / f'overflow-{index}'
                target = project / '.codex/config.toml'
                target.parent.mkdir(parents=True)
                target.write_text('# personal config\n')
                before = {path.relative_to(project): path.read_bytes()
                          for path in project.rglob('*') if path.is_file()}
                with self.assertRaisesRegex(ValueError, 'signed 64-bit'):
                    C.apply_project(project, 'codex', team='pnet', max_agents=limit)
                after = {path.relative_to(project): path.read_bytes()
                         for path in project.rglob('*') if path.is_file()}
                self.assertEqual(after, before)
                self.assertFalse((project / '.plex/applied.json').exists())
                self.assertFalse((project / '.codex/agents').exists())

        C.apply_project(self.root, 'codex', team='pnet', max_agents=C.NATIVE_CODEX_INTEGER_MAX)
        self.assertEqual(
            tomllib.loads(self.config.read_text())['agents']['max_concurrent_threads_per_session'],
            C.NATIVE_CODEX_INTEGER_MAX,
        )

    def test_non_codex_assignment_limit_keeps_python_integer_range(self):
        project = self.root / 'claude-project'
        project.mkdir()
        limit = 10**30
        result = C.apply_project(project, 'claude', team='pnet', max_agents=limit)
        self.assertEqual(result['status'], 'applied')
        self.assertIsNone(result['native_capacity'])
        saved = tomllib.loads((project / '.plex/preset.toml').read_text())
        self.assertEqual(saved['max_agents'], limit)

    def test_capacity_inheritance_and_profile_uncertainty_suppress_writes(self):
        global_config = self.codex_home / 'config.toml'
        global_config.write_text('[agents]\nmax_threads = 2\n')
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        parsed = tomllib.loads(self.config.read_text())
        self.assertNotIn('agents', parsed)
        native = C.check_project(self.root, 'codex')['hosts']['codex']['native_capacity']
        self.assertEqual((native['value'], native['origin'], native['mismatch']), (2, 'inherited', True))
        self.assertNotIn('capacity', json.loads((self.root / '.plex/applied.json').read_text())['hosts']['codex'])

        C.uninstall_project(self.root, 'codex')
        global_config.unlink()
        profile = self.codex_home / 'work.config.toml'
        profile.write_text('[agents]\nmax_concurrent_threads_per_session = 3\n')
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        parsed = tomllib.loads(self.config.read_text())
        self.assertNotIn('agents', parsed)
        native = C.check_project(self.root, 'codex')['hosts']['codex']['native_capacity']
        self.assertIsNone(native['value'])
        self.assertEqual(native['origin'], 'unknown')
        self.assertIsNone(native['mismatch'])
        self.assertTrue(native['uncertain'])

        C.uninstall_project(self.root, 'codex')
        profile.unlink()
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        original_block = '# plex-capacity:start\nmax_concurrent_threads_per_session = 4\n# plex-capacity:end\n'
        self.assertIn(original_block, self.config.read_text())
        receipt_path = self.root / '.plex/applied.json'
        original_capacity_receipt = json.loads(receipt_path.read_text())['hosts']['codex']['capacity']
        profile.write_text('[agents]\nmax_concurrent_threads_per_session = 3\n')
        result = C.apply_project(self.root, 'codex', team='pnet', max_agents=8)
        self.assertIn(original_block, self.config.read_text())
        self.assertEqual(json.loads(receipt_path.read_text())['hosts']['codex']['capacity'], original_capacity_receipt)
        self.assertEqual(result['native_capacity']['saved_target'], {'value': 4, 'origin': 'plex'})
        native = C.check_project(self.root, 'codex')['hosts']['codex']['native_capacity']
        self.assertIsNone(native['value'])
        self.assertEqual(native['origin'], 'unknown')
        self.assertEqual(native['saved_target'], {'value': 4, 'origin': 'plex'})
        self.assertTrue(native['uncertain'])

    def test_uncertain_capacity_refresh_skips_fake_agents_header_inside_string(self):
        self.config.write_text('prompt = """example\n[agents]\nstill prompt text\n"""\n')
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        original_block = '# plex-capacity:start\nmax_concurrent_threads_per_session = 4\n# plex-capacity:end\n'
        self.assertIn(original_block, self.config.read_text())
        self.config.write_text(self.config.read_text() + 'max_threads = 4\n')
        receipt_path = self.root / '.plex/applied.json'
        original_record = json.loads(receipt_path.read_text())['hosts']['codex']['capacity']
        (self.codex_home / 'work.config.toml').write_text(
            '[agents]\nmax_concurrent_threads_per_session = 3\n'
        )

        result = C.apply_project(self.root, 'codex', team='pnet', max_agents=8)
        updated = self.config.read_text()
        parsed = tomllib.loads(updated)
        self.assertIn('[agents]\nstill prompt text', parsed['prompt'])
        self.assertEqual(parsed['agents']['max_concurrent_threads_per_session'], 4)
        self.assertEqual(parsed['agents']['max_threads'], 4)
        self.assertIn(original_block, updated)
        self.assertEqual(json.loads(receipt_path.read_text())['hosts']['codex']['capacity'], original_record)
        self.assertEqual(result['native_capacity']['saved_target'], {'value': 4, 'origin': 'plex'})

    def test_ancestor_candidate_is_unknown_until_layer_applicability_is_proven(self):
        nested = self.root / 'nested-project'
        nested.mkdir()
        self.config.write_text('[agents]\nmax_threads = 2\n')
        C.apply_project(nested, 'codex', team='pnet', max_agents=4)
        target = nested / '.codex/config.toml'
        parsed = tomllib.loads(target.read_text())
        self.assertNotIn('agents', parsed)
        native = C.check_project(nested, 'codex')['hosts']['codex']['native_capacity']
        self.assertIsNone(native['value'])
        self.assertEqual(native['origin'], 'unknown')
        self.assertTrue(native['uncertain'])
        self.assertNotIn('capacity', json.loads((nested / '.plex/applied.json').read_text())['hosts']['codex'])

        self.config.unlink()
        managed = self.root / 'managed-project'
        managed.mkdir()
        C.apply_project(managed, 'codex', team='pnet', max_agents=4)
        target = managed / '.codex/config.toml'
        capacity_before = '# plex-capacity:start\nmax_concurrent_threads_per_session = 4\n# plex-capacity:end\n'
        self.assertIn(capacity_before, target.read_text())
        receipt_path = managed / '.plex/applied.json'
        capacity_receipt = json.loads(receipt_path.read_text())['hosts']['codex']['capacity']
        self.config.write_text('[agents]\nmax_concurrent_threads_per_session = 2\n')
        C.apply_project(managed, 'codex', max_agents=8)
        self.assertIn(capacity_before, target.read_text())
        self.assertEqual(json.loads(receipt_path.read_text())['hosts']['codex']['capacity'], capacity_receipt)
        status = C.check_project(managed, 'codex')['hosts']['codex']['native_capacity']
        self.assertIsNone(status['value'])
        self.assertEqual(status['saved_target'], {'value': 4, 'origin': 'plex'})

    def test_ancestor_dotcodex_file_is_treated_as_absent_candidate(self):
        nested = self.root / 'nested-project'
        nested.mkdir()
        shutil.rmtree(self.config.parent)
        self.config.parent.write_text('personal file, not a directory')
        C.apply_project(nested, 'codex', team='pnet', max_agents=4)
        target = nested / '.codex/config.toml'
        self.assertEqual(tomllib.loads(target.read_text())['agents']['max_concurrent_threads_per_session'], 4)

    def test_uninstall_ignores_broken_unrelated_profile_configs(self):
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        target_before = self.config.read_bytes()
        profile = self.codex_home / 'unused.config.toml'
        profile.write_text('[agents\ninvalid = true\n')
        result = C.uninstall_project(self.root, 'codex')
        self.assertEqual(result['status'], 'uninstalled')
        self.assertNotIn('plex-capacity:start', self.config.read_text())
        self.assertNotEqual(self.config.read_bytes(), target_before)

    def test_capacity_marker_moved_outside_agents_conflicts(self):
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        self.config.write_text(self.config.read_text().replace('[agents]', '[unrelated]'))
        edited = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'outside the \\[agents\\] table'):
            C.uninstall_project(self.root, 'codex')
        self.assertEqual(self.config.read_bytes(), edited)

    def test_capacity_preview_rejects_target_and_inherited_drift(self):
        self.config.write_text('# personal\n')
        preview = C.plan_codex_routing(self.root, 'project', max_agents=4)
        self.config.write_text('[agents]\nmax_threads = 2\n')
        changed_target = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'changed after preview'):
            C.apply_project(self.root, 'codex', team='pnet', max_agents=4,
                            expected_routing_plan=preview)
        self.assertEqual(self.config.read_bytes(), changed_target)
        self.assertFalse((self.root / '.plex/applied.json').exists())

        self.config.write_text('# personal\n')
        preview = C.plan_codex_routing(self.root, 'project', max_agents=4)
        inherited = self.codex_home / 'config.toml'
        inherited.write_text('[agents]\nmax_threads = 2\n')
        with self.assertRaisesRegex(ValueError, 'changed after preview'):
            C.apply_project(self.root, 'codex', team='pnet', max_agents=4,
                            expected_routing_plan=preview)
        self.assertEqual(self.config.read_text(), '# personal\n')
        self.assertFalse((self.root / '.plex/applied.json').exists())

    def test_capacity_layouts_render_under_the_real_agents_table(self):
        cases = (
            ('quoted table', '["agents"]\ndisable_direct_message = true\n'),
            ('dotted table', 'agents.foo.description = "personal"\n[agents.bar]\nenabled = true\n'),
            ('multiline string header', 'prompt = """\n[agents]\n"""\n[agents.foo]\ndescription = "personal"\n'),
            ('multiline fake before real table', 'prompt = """\n[agents]\n"""\n[agents]\ndisable_direct_message = true\n'),
        )
        for name, original in cases:
            with self.subTest(name=name):
                self.config.write_text(original)
                C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
                parsed = tomllib.loads(self.config.read_text())
                self.assertEqual(parsed['agents']['max_concurrent_threads_per_session'], 4)
                if name == 'multiline string header':
                    self.assertEqual(parsed['prompt'], '[agents]\n')
                if name == 'multiline fake before real table':
                    self.assertEqual(parsed['prompt'], '[agents]\n')
                    self.assertTrue(parsed['agents']['disable_direct_message'])
                C.uninstall_project(self.root, 'codex')
                for child in self.root.iterdir():
                    if child.name != 'codex-home':
                        if child.is_dir():
                            shutil.rmtree(child)
                        else:
                            child.unlink()
                self.config.parent.mkdir(parents=True, exist_ok=True)

    def test_user_scope_capacity_refresh_uncertainty_and_uninstall(self):
        user_config = self.codex_home / 'config.toml'
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4, scope='user')
        self.assertEqual(tomllib.loads(user_config.read_text())['agents']['max_concurrent_threads_per_session'], 4)
        C.apply_project(self.root, 'codex', max_agents=8, scope='user')
        self.assertEqual(tomllib.loads(user_config.read_text())['agents']['max_concurrent_threads_per_session'], 8)
        original_receipt = json.loads((self.codex_home / '.plex/applied.json').read_text())['hosts']['codex']['capacity']
        profile = self.codex_home / 'work.config.toml'
        profile.write_text('[agents]\nmax_threads = 2\n')
        C.apply_project(self.root, 'codex', max_agents=10, scope='user')
        self.assertEqual(tomllib.loads(user_config.read_text())['agents']['max_concurrent_threads_per_session'], 8)
        saved = json.loads((self.codex_home / '.plex/applied.json').read_text())['hosts']['codex']['capacity']
        self.assertEqual(saved, original_receipt)
        profile.write_text('[agents\ninvalid = true\n')
        C.uninstall_project(self.root, 'codex', scope='user')
        self.assertNotIn('plex-capacity:start', user_config.read_text())

    def test_new_inherited_limit_relinquishes_owned_block_and_uninstall_preserves_it(self):
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        self.assertIn('plex-capacity:start', self.config.read_text())
        inherited = self.codex_home / 'config.toml'
        inherited.write_text('[agents]\nmax_concurrent_threads_per_session = 2\n')
        state = C.check_project(self.root, 'codex')['hosts']['codex']
        self.assertEqual(state['status'], 'needs_refresh')
        self.assertEqual(state['native_capacity']['value'], 4)
        self.assertEqual(state['proposed_capacity']['value'], 2)
        self.assertEqual(state['proposed_capacity']['origin'], 'inherited')
        C.apply_project(self.root, 'codex')
        current = self.config.read_text()
        self.assertNotIn('plex-capacity:start', current)
        self.assertIn('plex-routing:start', current)
        self.assertNotIn('capacity', json.loads((self.root / '.plex/applied.json').read_text())['hosts']['codex'])
        C.uninstall_project(self.root, 'codex')
        self.assertEqual(inherited.read_text(), '[agents]\nmax_concurrent_threads_per_session = 2\n')

    def test_equal_user_alias_relinquishes_owned_key_but_different_alias_conflicts(self):
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        self.config.write_text(self.config.read_text() + 'max_threads = 4\n')
        C.apply_project(self.root, 'codex')
        current = tomllib.loads(self.config.read_text())['agents']
        self.assertNotIn('max_concurrent_threads_per_session', current)
        self.assertEqual(current['max_threads'], 4)
        self.assertNotIn('capacity', json.loads((self.root / '.plex/applied.json').read_text())['hosts']['codex'])

        C.uninstall_project(self.root, 'codex')
        shutil.rmtree(self.root / '.plex', ignore_errors=True)
        shutil.rmtree(self.root / '.codex', ignore_errors=True)
        self.config.parent.mkdir(parents=True, exist_ok=True)
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        self.config.write_text(self.config.read_text() + 'max_threads = 3\n')
        before = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'aliases conflict'):
            C.apply_project(self.root, 'codex')
        self.assertEqual(self.config.read_bytes(), before)

    def test_check_separates_saved_capacity_from_proposed_refresh(self):
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        config_before = self.config.read_bytes()
        preset = self.root / '.plex/preset.toml'
        preset.write_text(preset.read_text().replace('max_agents = 4', 'max_agents = 8'))
        state = C.check_project(self.root, 'codex')['hosts']['codex']
        self.assertEqual(state['native_capacity']['value'], 4)
        self.assertEqual(state['native_capacity']['origin'], 'plex')
        self.assertEqual(state['native_capacity']['mismatch'], True)
        self.assertEqual(state['proposed_capacity']['value'], 8)
        self.assertEqual(state['proposed_capacity']['origin'], 'plex')
        self.assertEqual(self.config.read_bytes(), config_before)

    def test_edited_capacity_block_and_inherited_input_drift_conflict_preserving_state(self):
        C.apply_project(self.root, 'codex', team='pnet', max_agents=4)
        original = self.config.read_bytes()
        self.config.write_text(self.config.read_text().replace('= 4', '= 7'))
        edited = self.config.read_bytes()
        with self.assertRaisesRegex(ValueError, 'capacity changed'):
            C.uninstall_project(self.root, 'codex')
        self.assertEqual(self.config.read_bytes(), edited)

        self.config.write_bytes(original)
        inherited = self.codex_home / 'config.toml'
        original_write = C._check_capacity_input_snapshot
        calls = 0

        def drift_on_config_write(snapshot):
            nonlocal calls
            calls += 1
            if calls == 2:
                inherited.write_text('[agents]\nmax_threads = 2\n')
            return original_write(snapshot)

        with patch.object(C, '_check_capacity_input_snapshot', side_effect=drift_on_config_write):
            with self.assertRaisesRegex(ValueError, 'Inherited Codex config changed'):
                C.apply_project(self.root, 'codex', team='pnet', max_agents=5)
        self.assertEqual(self.config.read_bytes(), original)
        self.assertTrue((self.root / '.plex/applied.json').is_file())
        self.assertFalse((self.root / '.plex/.apply.lock').exists())

    def test_legacy_install_requires_refresh_for_native_controls(self):
        C.apply_project(self.root, 'codex', team='pnet')
        receipt = self.root / '.plex/applied.json'
        saved = json.loads(receipt.read_text())
        saved['hosts']['codex'].pop('routing')
        saved['hosts']['codex'].pop('capacity')
        receipt.write_text(json.dumps(saved))
        self.config.write_text('# legacy personal config\n')
        state = C.check_project(self.root, 'codex')['hosts']['codex']
        self.assertEqual(state['status'], 'needs_refresh')
        self.assertIsNone(state['native_capacity']['value'])
        self.assertEqual(state['native_capacity']['origin'], 'absent')
        self.assertEqual(state['proposed_capacity']['value'], saved['hosts']['codex']['max_agents'])
        C.apply_project(self.root, 'codex')
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')
        self.assertTrue(self.config.read_text().startswith('# legacy personal config\n'))
