"""Release selection and real Git updates against a local fixture repository."""
from pathlib import Path
import importlib.util
import io
import json
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT=Path(__file__).resolve().parents[1]
SPEC=importlib.util.spec_from_file_location('test_releases',ROOT/'skills/plex-setup/scripts/releases.py')
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


class ReleaseTests(unittest.TestCase):
    def test_newest_published_release_includes_preview_and_skips_draft(self):
        releases=[{'tag_name':'v0.1.0','published_at':'2026-10-17'},
                  {'tag_name':'v0.2.0','published_at':'2026-10-18','prerelease':True},
                  {'tag_name':'v9.0.0','published_at':'2026-10-19','draft':True},
                  {'tag_name':'main','published_at':'2026-10-20'}]
        with patch.object(M.urllib.request,'urlopen',return_value=io.BytesIO(json.dumps(releases).encode())):
            self.assertEqual(M.published_release(),'v0.2.0')

    def test_explicit_tag_and_api_failure_do_not_touch_checkout(self):
        with patch.object(M.urllib.request,'urlopen',return_value=io.BytesIO(b'{"tag_name":"v0.1.0","published_at":"2026-10-17"}')):
            self.assertEqual(M.published_release('v0.1.0'),'v0.1.0')
        with tempfile.TemporaryDirectory() as temp,patch.object(M,'published_release',side_effect=ValueError('network')):
            checkout=Path(temp).resolve()/'checkout'
            with self.assertRaises(ValueError):M.update_checkout(checkout)
            self.assertFalse(checkout.exists())

    def test_tag_update_dirty_guard_explicit_main_and_dry_run(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp).resolve();repo=base/'origin';repo.mkdir()
            subprocess.run(['git','init','-q','-b','main',str(repo)],check=True)
            def git(*args):return M.git(repo,*args)
            git('config','user.name','Test');git('config','user.email','test@example.com')
            (repo/'marker').write_text('release');git('add','.');git('commit','-qm','release');git('tag','v0.1.0')
            (repo/'marker').write_text('development');git('commit','-qam','development')
            checkout=base/'checkout'
            with patch.object(M,'REPOSITORY',str(repo)),patch.object(M,'published_release',return_value='v0.1.0'):
                M.update_checkout(checkout,dry_run=True);self.assertFalse(checkout.exists())
                M.update_checkout(checkout);self.assertEqual((checkout/'marker').read_text(),'release')
                (checkout/'marker').write_text('mine')
                with self.assertRaisesRegex(ValueError,'local changes'):M.update_checkout(checkout,development=True)
                self.assertEqual((checkout/'marker').read_text(),'mine')
                M.git(checkout,'restore','marker');M.update_checkout(checkout,development=True)
                self.assertEqual((checkout/'marker').read_text(),'development')
                M.update_checkout(checkout);self.assertEqual((checkout/'marker').read_text(),'release')
                other=base/'unrelated';other.mkdir();(other/'personal').write_text('mine')
                with self.assertRaises(ValueError):M.update_checkout(other)
                self.assertEqual((other/'personal').read_text(),'mine')

    def test_main_forwards_setup_flags_and_preview_does_not_run_setup(self):
        with patch.object(M,'update_checkout') as update,patch.object(M.subprocess,'call',return_value=0) as setup:
            self.assertEqual(M.main(['--checkout',str(ROOT),'--release','v0.2.0','--project','/example','--yes']),0)
            self.assertEqual(setup.call_args.args[0],[str(ROOT/'setup.sh'),'--project','/example','--yes'])
            self.assertEqual(M.main(['--checkout',str(ROOT),'--dry-run']),0)
            self.assertEqual(setup.call_count,1)

    def test_version_transition_is_shown_before_fetch_and_in_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            checkout = Path(temp)
            (checkout / '.git').mkdir()
            manifest = checkout / 'plugins/codex/.codex-plugin/plugin.json'
            manifest.parent.mkdir(parents=True)
            def git(path, *args):
                if args == ('remote', 'get-url', 'origin'): return M.REPOSITORY
                if args == ('status', '--porcelain'): return ''
                if args[0] == 'fetch':
                    self.assertIn('Plex update: v0.17.0 → v0.17.1', output.getvalue())
                return 'abc1234'
            for dry_run in (True, False):
                manifest.write_text('{"version":"0.17.0"}')
                with patch.object(M, 'published_release', return_value='v0.17.1'), patch.object(M, 'git', side_effect=git) as calls, redirect_stdout(io.StringIO()) as output:
                    M.update_checkout(checkout, dry_run=dry_run)
                self.assertIn('Plex update: v0.17.0 → v0.17.1', output.getvalue())
                self.assertEqual(any(call.args[1] == 'fetch' for call in calls.call_args_list), not dry_run)
            for raw in ('{broken', '{"version":null}', '[]'):
                manifest.write_text(raw)
                with patch.object(M, 'published_release', return_value='v0.17.1'), patch.object(M, 'git', side_effect=lambda path, *args: M.REPOSITORY if args[0]=='remote' else ''), redirect_stdout(io.StringIO()) as output:
                    M.update_checkout(checkout, dry_run=True)
                self.assertIn('Plex update: unknown → v0.17.1', output.getvalue())
            manifest.unlink()
            with patch.object(M, 'git', side_effect=lambda path, *args: M.REPOSITORY if args[0]=='remote' else ''), redirect_stdout(io.StringIO()) as output:
                M.update_checkout(checkout, development=True, dry_run=True)
            self.assertIn('Plex update: unknown → main', output.getvalue())

    def test_initial_install_and_same_version_are_explicit(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(M, 'published_release', return_value='v0.17.0'):
            checkout = Path(temp) / 'absent'
            with redirect_stdout(io.StringIO()) as output:
                M.update_checkout(checkout, dry_run=True)
            self.assertIn('Plex install: not installed → v0.17.0', output.getvalue())
            self.assertFalse(checkout.exists())
            (checkout / '.git').mkdir(parents=True)
            manifest = checkout / 'plugins/codex/.codex-plugin/plugin.json'
            manifest.parent.mkdir(parents=True)
            manifest.write_text('{"version":"0.17.0"}')
            with patch.object(M, 'git', side_effect=lambda path, *args: M.REPOSITORY if args[0]=='remote' else ''), redirect_stdout(io.StringIO()) as output:
                M.update_checkout(checkout, dry_run=True)
            self.assertIn('Plex update: v0.17.0 → v0.17.0', output.getvalue())
