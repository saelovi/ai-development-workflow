#!/usr/bin/env python3
"""Offline runner checks in disposable repos; Python 3.8+, git, POSIX only."""
import os
import runpy
import subprocess
import sys
import time
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
fixtures = runpy.run_path(str(HERE / 'ai-state-check-test.py'))
GOOD = "print('blocking: 0\\n\\nChecked feature.txt and its callers; no blockers found.')"


@unittest.skipUnless(os.name == 'posix', 'POSIX process-group runner')
class Runner(unittest.TestCase):
    def setUp(self):
        self.repo = fixtures['Workflow']()
        self.repo.setUp()
        self.addCleanup(self.repo.tearDown)
        self.repo.ok('--init', 'setup')
        self.repo.ok('--set', 'implementation_models=["opus"]')

    def invoke(self, source=GOOD, *options, command_tail=()):
        return subprocess.run(
            [sys.executable, str(HERE / 'ai-review-run.py'), '--kind', 'code',
             '--model', 'codex', '--backend', 'stub', *options, '--', sys.executable, '-c', source, *command_tail],
            cwd=str(self.repo.root), capture_output=True, text=True, timeout=10)

    def test_preamble_is_allowed_but_multiple_counts_are_ambiguous(self):
        result = self.invoke("print('Review complete.\\n'); " + GOOD)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (self.repo.root / '.ai/reviews/round-1.md').read_text()
        self.assertNotIn('Review complete.', text)
        for tail in ("blocking: 2\\n\\nActual findings", "blocking: unknown\\n\\nIncomplete"):
            result = self.invoke(GOOD + "; print('\\n" + tail + "')", '--output', 'ambiguous.md')
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.repo.root / '.ai/reviews/ambiguous.md').exists())

    def test_file_response_is_separate_from_event_stdout(self):
        source = ("from pathlib import Path; import sys; "
                  "print('{\"event\": \"progress\"}'); "
                  "Path(sys.argv[1]).write_text('Finished review.\\n\\nblocking: 0\\n\\nChecked feature.txt; no blockers.')")
        result = self.invoke(source, '--report-file', command_tail=('{report_file}',))
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.repo.root / '.ai/reviews/round-1.md').read_text()
        self.assertNotIn('progress', report)
        self.assertIn('Checked feature.txt', report)
        paths = list((self.repo.root / '.ai/reviews').glob('attempt-*-logs/response.txt'))
        self.assertEqual(len(paths), 1)
        self.assertIn('Finished review.', paths[0].read_text())

    def test_file_mode_requires_fresh_regular_output_and_success(self):
        sources = (GOOD,
                   "from pathlib import Path; import sys; Path(sys.argv[1]).symlink_to('stdout.log'); " + GOOD,
                   "from pathlib import Path; import sys; Path(sys.argv[1]).write_text('blocking: 0\\n\\nClean'); raise SystemExit(7)")
        for source in sources:
            result = self.invoke(source, '--report-file', command_tail=('{report_file}',))
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.repo.root / '.ai/reviews/round-1.md').exists())
        source = "open('.ai/dispatched','w').close()"
        for options, tail in ((('--report-file',), ()), ((), ('{report_file}',))):
            result = self.invoke(source, *options, command_tail=tail)
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse((self.repo.root / '.ai/dispatched').exists())

    def test_success_and_exclusive_publication(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = self.repo.root / '.ai/reviews/round-1.md'
        original = report.read_bytes()
        self.assertIn(('sha: ' + self.repo.head()).encode(), original)
        self.repo.ok('--advance', 'audit', '--set', 'profile=small',
                     '--set', 'platform=linux', '--set', 'stack=python')
        self.repo.ok('--advance', 'files', '--set', 'claude_md=true', '--set', 'state_check=true')
        self.repo.ok('--test', sys.executable, '-c', 'assert True')
        self.repo.ok('--advance', 'smoke', '--set', 'smoke_ok=true')
        self.repo.ok('--advance', 'review')
        result = self.invoke("raise Exception('must not execute')")
        self.assertIn('output exists', result.stderr)
        self.assertEqual(report.read_bytes(), original)

    def test_identity_collision_is_rejected_before_dispatch(self):
        result = self.invoke("open('.ai/dispatched', 'w').close()", '--model', ' OPUS ')
        self.assertIn('independent', result.stderr)
        self.assertFalse((self.repo.root / '.ai/dispatched').exists())

    def test_failure_and_bad_output_never_publish(self):
        for source in (GOOD + '; raise SystemExit(7)', "print('partial')",
                       "print('blocking: -1\\n\\nInvalid count')", "print('blocking: 0\\n\\n')"):
            with self.subTest(source=source):
                result = self.invoke(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.repo.root / '.ai/reviews/round-1.md').exists())
        logs = list((self.repo.root / '.ai/reviews').glob('attempt-*-logs/stdout.log'))
        self.assertEqual(len(logs), 4)
        self.assertTrue(any(p.with_name('status.txt').read_text() == 'exit: 7\n' for p in logs))

    def test_dirty_tree_head_and_state_changes_are_rejected(self):
        sources = ["open('feature.txt', 'a').write('changed'); " + GOOD,
                   "import subprocess; subprocess.run(['git','commit','--allow-empty','-qm','changed'], check=True); " + GOOD,
                   "open('.ai/state.json', 'a').write(' '); " + GOOD]
        state = (self.repo.root / '.ai/state.json').read_bytes()
        for source in sources:
            with self.subTest(source=source):
                result = self.invoke(source)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.repo.root / '.ai/reviews/round-1.md').exists())
                self.repo.git('reset', '--hard', self.repo.base)
                (self.repo.root / '.ai/state.json').write_bytes(state)
        self.repo.write('untracked.txt', 'dirty')
        result = self.invoke("open('.ai/dispatched', 'w').close()")
        self.assertIn('dirty', result.stderr)
        self.assertFalse((self.repo.root / '.ai/dispatched').exists())

    def test_timeout_kills_child_and_preserves_partial_output(self):
        source = ("import subprocess,sys,time; "
                  "subprocess.Popen([sys.executable,'-c',\"import time; time.sleep(1); open('.ai/leaked','w').close()\"]); "
                  "print('partial', flush=True); time.sleep(30)")
        result = self.invoke(source, '--timeout', '0.3')
        self.assertIn('timed out', result.stderr)
        time.sleep(1.1)
        self.assertFalse((self.repo.root / '.ai/leaked').exists())
        logs = list((self.repo.root / '.ai/reviews').glob('attempt-*-logs/stdout.log'))
        self.assertEqual(logs[0].read_text(), 'partial\n')
        self.assertEqual(logs[0].with_name('status.txt').read_text(), 'timeout\n')

    def test_stdin_is_closed_and_leftover_children_are_killed(self):
        source = ("import subprocess,sys; assert sys.stdin.read() == ''; "
                  "subprocess.Popen([sys.executable,'-c',\"import time; time.sleep(1); open('.ai/leaked','w').close()\"]); " + GOOD)
        result = self.invoke(source)
        self.assertEqual(result.returncode, 0, result.stderr)
        time.sleep(1.1)
        self.assertFalse((self.repo.root / '.ai/leaked').exists())

    def test_verify_links_accepted_report_and_gate_accepts(self):
        self.repo.ok('--archive')
        self.repo.reviewed(blocking=1)
        result = self.invoke(GOOD, '--kind', 'verify')
        self.assertEqual(result.returncode, 0, result.stderr)
        report = (self.repo.root / '.ai/reviews/round-2.md').read_text()
        self.assertIn('previous: ' + self.repo.state()['review_hash'], report)
        self.repo.ok('--advance', 'verify', '--set', 'product_check=fixture check only')

    def test_spec_model_and_output_boundaries(self):
        self.repo.ok('--archive')
        self.repo.gated()
        self.repo.ok('--set', 'plan_models=["opus"]')
        result = self.invoke(GOOD, '--kind', 'spec')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.repo.root / '.ai/reviews/spec-review.md').is_file())
        for options in (('--output', '../escape.md'), ('--kind', 'spec', '--output', 'round-1.md'),
                        ('--timeout', 'nan'), ('--backend', 'bad\nheader')):
            result = self.invoke(GOOD, *options)
            self.assertNotEqual(result.returncode, 0)


if __name__ == '__main__':
    unittest.main()
