"""Piped Bash entrypoint, downloaded helper and terminal input; no network calls."""
import json
import os
from pathlib import Path
import pty
import select
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name);self.project = self.root/'project';self.project.mkdir()
        commands=self.root/'bin';commands.mkdir()
        fixture=self.root/'helper.py'
        fixture.write_text('''import os,sys,json
from pathlib import Path
if os.environ.get('EXPECT_MENU'):assert input('Choose: ')=='continue'
Path(os.environ['RESULT']).write_text(json.dumps({'cwd':os.getcwd(),'tty':os.isatty(0),'args':sys.argv[1:]}))
''')
        curl=commands/'curl';curl.write_text('''#!/usr/bin/env python3
import os,sys,shutil
if os.environ.get('DOWNLOAD_FAILURE'):raise SystemExit(22)
shutil.copyfile(os.environ['HELPER_FIXTURE'],sys.argv[sys.argv.index('-o')+1])
''');curl.chmod(0o700)
        for name,content in [('git','#!/bin/sh\nexit 0\n'),('uv','#!/bin/sh\nshift 2\nexec python3 "$@"\n')]:
            p=commands/name;p.write_text(content);p.chmod(0o700)
        self.env={**os.environ,'HOME':str(self.root/'home'),'PATH':str(commands)+':'+os.environ['PATH'],
                  'HELPER_FIXTURE':str(fixture),'RESULT':str(self.root/'result.json')}

    def run_script(self,*args):
        return subprocess.run(['/bin/bash','-s','--',*args],input=(ROOT/'install.sh').read_text(),text=True,
                              cwd=self.project,env=self.env,capture_output=True,timeout=10)

    def test_forwards_flags_and_preserves_project_directory(self):
        result=self.run_script('--release','v0.2.0','--yes');self.assertEqual(result.returncode,0,result.stderr)
        output=json.loads(Path(self.env['RESULT']).read_text())
        self.assertEqual(output['cwd'],str(self.project));self.assertEqual(output['args'],['--release','v0.2.0','--yes'])
        self.assertEqual(list(self.project.iterdir()),[])

    def test_missing_git_fails_before_download(self):
        self.env['PATH']=str(self.root/'missing-bin')
        self.assertEqual(self.run_script().returncode,127)
        self.assertFalse(Path(self.env['RESULT']).exists())

    def test_failed_download_does_not_run_helper(self):
        self.env['DOWNLOAD_FAILURE']='1'
        self.assertEqual(self.run_script().returncode,22)
        self.assertFalse(Path(self.env['RESULT']).exists())

    def test_pipe_restores_real_terminal_input(self):
        child,terminal=pty.fork()
        if child==0:
            os.chdir(self.project);os.environ.update(self.env,EXPECT_MENU='1',BOOTSTRAP=str(ROOT/'install.sh'))
            os.execl('/bin/bash','bash','-c','cat "$BOOTSTRAP" | bash')
        try:
            output=b'';deadline=time.monotonic()+10
            while b'Choose: ' not in output and time.monotonic()<deadline:
                if select.select([terminal],[],[],.1)[0]:output+=os.read(terminal,4096)
            self.assertIn(b'Choose: ',output);os.write(terminal,b'continue\n')
            while not Path(self.env['RESULT']).exists() and time.monotonic()<deadline:time.sleep(.02)
            self.assertTrue(Path(self.env['RESULT']).exists())
            self.assertTrue(json.loads(Path(self.env['RESULT']).read_text())['tty'])
        finally:
            os.close(terminal)
            try:os.kill(child,15)
            except ProcessLookupError:pass
            os.waitpid(child,0)
