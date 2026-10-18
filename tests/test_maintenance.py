"""Read-only status and receipt-owned uninstall, including failure preservation."""
import importlib.util
import io
import json
import os
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('maintenance_setup', ROOT / 'setup.py')
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)
C = S.CONFIG


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob('*') if p.is_file()}


class MaintenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def install(self, host='codex'):
        return C.apply_project(self.root, host, team='pnet', model_profile='inherit', instructions=True)

    def test_status_is_read_only_and_reports_config_and_plugin(self):
        self.install()
        before = snapshot(self.root)
        output = io.StringIO()
        with patch.object(S, 'verify_plugin'), patch.object(S.shutil, 'which', return_value='/stub/client'), redirect_stdout(output):
            self.assertEqual(S.main(['status', '--project', str(self.root), '--scope', 'project', '--client', 'codex', '--json']), 0)
        data = json.loads(output.getvalue())
        self.assertEqual(data['clients'][0]['status'], 'in_sync')
        self.assertEqual(data['clients'][0]['team'], 'pnet')
        self.assertEqual(before, snapshot(self.root))

    def test_status_reports_conflicts_with_nonzero_exit(self):
        self.install()
        (self.root / '.codex/agents/plex-dev.toml').write_text('user change')
        with redirect_stdout(io.StringIO()), patch.object(S, 'verify_plugin'):
            self.assertEqual(S.main(['status', '--project', str(self.root), '--client', 'codex', '--json']), 1)

    def test_uninstall_preserves_user_text_foreign_roles_and_preferences(self):
        text = b'# Personal instructions\n'
        (self.root / 'AGENTS.md').write_bytes(text)
        self.install()
        with (self.root / 'AGENTS.md').open('ab') as stream:
            stream.write(b'\nNew personal rule\n')
        before = snapshot(self.root)
        self.assertEqual(C.uninstall_project(self.root, 'codex', dry_run=True)['status'], 'planned')
        self.assertEqual(before, snapshot(self.root))
        foreign = self.root / '.codex/agents/personal.toml'
        foreign.write_text('mine')
        result = C.uninstall_project(self.root, 'codex')
        self.assertEqual(result['status'], 'uninstalled')
        self.assertTrue((self.root / 'AGENTS.md').read_bytes().startswith(text))
        self.assertNotIn(C.PLEX_START, (self.root / 'AGENTS.md').read_bytes())
        self.assertTrue((self.root / 'AGENTS.md').read_bytes().endswith(b'New personal rule\n'))
        self.assertEqual(foreign.read_text(), 'mine')
        self.assertTrue((self.root / '.plex/preset.toml').exists())
        self.assertFalse((self.root / '.plex/applied.json').exists())
        self.assertTrue((self.root / result['backup_dir'] / 'applied.json').exists())
        self.assertEqual(C.uninstall_project(self.root, 'codex')['status'], 'unconfigured')
        self.install()
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')

    def test_modified_role_or_block_aborts_without_writes(self):
        self.install()
        for path in [self.root / '.codex/agents/plex-dev.toml', self.root / 'AGENTS.md']:
            original = path.read_bytes()
            changed = original.replace(C.PLEX_START, C.PLEX_START + b' changed') if path.name=='AGENTS.md' else original + b'\n# changed'
            path.write_bytes(changed)
            before = snapshot(self.root)
            with self.assertRaises(ValueError):
                C.uninstall_project(self.root, 'codex')
            self.assertEqual(before, snapshot(self.root))
            path.write_bytes(original)

    def test_shared_instruction_block_survives_until_last_client(self):
        self.install()
        self.install('antigravity')
        receipt = json.loads((self.root / '.plex/applied.json').read_text())
        self.assertEqual(receipt['hosts']['codex']['instructions']['relpath'],receipt['hosts']['antigravity']['instructions']['relpath'])
        C.uninstall_project(self.root, 'codex')
        self.assertIn(C.PLEX_START, (self.root / 'AGENTS.md').read_bytes())
        self.assertEqual(C.check_project(self.root, 'antigravity')['status'], 'in_sync')
        C.uninstall_project(self.root, 'antigravity')
        self.assertNotIn(C.PLEX_START, (self.root / 'AGENTS.md').read_bytes())

    def test_user_scope_removal_preserves_project_install(self):
        self.install()
        user = self.root / 'user-home'
        with patch.dict(os.environ, {'CODEX_HOME': str(user)}):
            C.apply_project(self.root, 'codex', team='pnet', model_profile='inherit', scope='user', instructions=True)
            C.uninstall_project(self.root, 'codex', scope='user')
        self.assertEqual(C.check_project(self.root, 'codex')['status'], 'in_sync')

    def test_symlink_and_active_lock_are_refused(self):
        self.install()
        lock = self.root / '.plex/.apply.lock'
        lock.write_text('busy')
        with self.assertRaisesRegex(ValueError, 'holds'):
            C.uninstall_project(self.root, 'codex')
        self.assertEqual(lock.read_text(), 'busy')
        lock.unlink()
        role = self.root / '.codex/agents/plex-dev.toml'
        other = self.root / 'user-file'
        other.write_bytes(role.read_bytes())
        role.unlink();role.symlink_to(other)
        with self.assertRaisesRegex(ValueError, 'symlink'):
            C.uninstall_project(self.root, 'codex')
        self.assertTrue(other.exists())

    def test_failure_rolls_back_owned_files(self):
        self.install()
        before = snapshot(self.root)
        original = C._ApplyTransaction.archive
        count = 0
        def fail(tx, path, backup):
            nonlocal count
            count += 1
            if count==2:
                raise OSError('injected failure')
            return original(tx, path, backup)
        with patch.object(C._ApplyTransaction, 'archive', fail), self.assertRaises(OSError):
            C.uninstall_project(self.root, 'codex')
        after = {k:v for k,v in snapshot(self.root).items() if not k.startswith('.plex/backups/')}
        self.assertEqual(before, after)

    def test_cli_uninstall_requires_confirmation_and_preview_has_no_writes(self):
        self.install();before=snapshot(self.root)
        with redirect_stdout(io.StringIO()),redirect_stderr(io.StringIO()):
            self.assertEqual(S.main(['uninstall','--project',str(self.root),'--client','codex','--dry-run']),0)
            with patch('sys.stdin.isatty',return_value=False):
                self.assertEqual(S.main(['uninstall','--project',str(self.root),'--client','codex']),1)
        self.assertEqual(before,snapshot(self.root))

    def test_concurrent_edit_is_preserved_when_rollback_needs_recovery(self):
        self.install()
        original = C._ApplyTransaction.archive
        moved = []
        def fail(tx, path, backup):
            if moved:
                moved[0].write_bytes(b'new user edit')
                raise OSError('injected failure')
            original(tx, path, backup)
            moved.append(path)
        with patch.object(C._ApplyTransaction, 'archive', fail), self.assertRaisesRegex(ValueError, 'rollback needs recovery'):
            C.uninstall_project(self.root, 'codex')
        self.assertEqual(moved[0].read_bytes(), b'new user edit')
        self.assertFalse((self.root / '.plex/.apply.lock').exists())

    def test_status_reports_missing_plugin_and_stale_configuration(self):
        self.install()
        with patch.object(S.shutil, 'which', return_value='/stub/client'), patch.object(S, 'verify_plugin', side_effect=ValueError('plugin absent')), redirect_stdout(io.StringIO()):
            self.assertEqual(S.main(['status','--project',str(self.root),'--client','codex']),1)
        (self.root / '.plex/resolved.json').unlink()
        with patch.object(S, 'verify_plugin'), redirect_stdout(io.StringIO()):
            self.assertEqual(S.main(['status','--project',str(self.root),'--client','codex']),1)

    def test_interrupted_uninstall_rolls_back(self):
        self.install();before=snapshot(self.root)
        original=C._ApplyTransaction.archive
        moved=[]
        def interrupt(tx,path,backup):
            if moved:raise KeyboardInterrupt()
            original(tx,path,backup);moved.append(path)
        with patch.object(C._ApplyTransaction,'archive',interrupt), self.assertRaises(KeyboardInterrupt):
            C.uninstall_project(self.root,'codex')
        after={k:v for k,v in snapshot(self.root).items() if not k.startswith('.plex/backups/')}
        self.assertEqual(before,after)
