#!/usr/bin/env python3
"""Workflow/evidence regression checks. Run with Python 3.8+; git is required.

All mutations and subprocess checks run in disposable repositories. No models,
network calls, or third-party testing dependencies are needed.
"""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKER = HERE / 'ai-state-check.py'
GATED = 'implement-with-review-gate'
PY = sys.executable


def sh(args, cwd):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True)


def rm_readonly(func, path, _exc):
    os.chmod(path, stat.S_IWRITE)
    func(path)


class Workflow(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='aisc-')).resolve()
        self.main = self.tmp / 'repo'
        self.main.mkdir()
        self.root = self.main
        self.git('init', '-q')
        self.git('config', 'user.email', 'test@example.com')
        self.git('config', 'user.name', 'Test')
        self.git('config', 'commit.gpgsign', 'false')
        for name, content in {
            '.gitignore': '.ai/\n', 'CLAUDE.md': '# Repo guidance\n',
            'docs/ai/tooling.md': '# Checks\n', 'spec.md': 'Initial scope\n',
            'plan.md': 'Initial plan\n', 'feature.txt': 'old\n',
        }.items():
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding='utf-8')
        (self.root / 'bin').mkdir()
        for source in (CHECKER, Path(__file__).resolve()):
            shutil.copy(source, self.root / 'bin' / source.name)
        self.commit('baseline')
        self.base = self.head()

    def tearDown(self):
        shutil.rmtree(self.tmp, onerror=rm_readonly)

    def git(self, *args):
        result = sh(['git', *args], self.root)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def head(self):
        return self.git('rev-parse', 'HEAD')

    def commit(self, message):
        self.git('add', '.')
        self.git('commit', '-q', '-m', message)

    def check(self, *args):
        return sh([PY, str(CHECKER), *args], self.root)

    def ok(self, *args):
        result = self.check(*args)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout.strip()

    def blocked(self, *args, contains):
        result = self.check(*args)
        self.assertNotEqual(result.returncode, 0, result.stdout)
        self.assertIn(contains, result.stderr)

    def state(self):
        return json.loads((self.root / '.ai/state.json').read_text('utf-8'))

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf-8')

    def gated(self, skip=False):
        wt = self.tmp / 'task'
        self.git('worktree', 'add', '-q', '-b', 'task', str(wt))
        self.root = wt
        args = ['--init', GATED, '--base', self.base]
        if skip:
            args += ['--skip', 'spec_review']
        self.ok(*args)

    def report(self, name='round-1.md', model='codex', blocking=0, sha=None, base=None):
        previous = 'previous: ' + self.state()['review_hash'] + '\n' if name == 'round-2.md' else ''
        self.write('.ai/reviews/' + name,
                   f'model: {model}\neffort: high\nbackend: test\n'
                   f'base: {base or self.base}\nsha: {sha or self.head()}\nblocking: {blocking}\n{previous}\n'
                   'Reviewed feature.txt against the plan; findings/verification recorded here.\n')

    def plan(self, skip=False):
        self.gated(skip)
        self.write('spec.md', 'Change feature.txt to new; preserve existing behavior elsewhere.\n')
        self.write('plan.md', 'Update feature.txt and check its content.\n')
        self.commit('docs: plan feature')
        args = ['--advance', 'plan', '--set', 'spec_path=spec.md', '--set', 'plan_path=plan.md',
                '--set', 'plan_models=["opus"]']
        if skip:
            args += ['--set', 'spec_review_skip_reason=Established design; narrow risk fix']
        self.ok(*args)
        if not skip:
            self.report('spec-review.md', model='grok')
            self.ok('--advance', 'spec_review')

    def implementation(self, skip=False):
        self.plan(skip)
        self.write('feature.txt', 'new\n')
        self.commit('feat: update feature')
        self.ok('--advance', 'implement', '--set', 'implementation_models=["composer"]')

    def run_passing_check(self):
        self.ok('--test', PY, '-c', 'from pathlib import Path; assert Path("feature.txt").read_text().strip() == "new"')

    def reviewed(self, skip=False, blocking=0):
        self.implementation(skip)
        self.run_passing_check()
        self.ok('--advance', 'test')
        self.report(blocking=blocking)
        self.ok('--advance', 'review')

    def finish(self):
        self.ok('--advance', 'verify', '--set', 'product_check=File content verified')
        self.ok('pr')
        self.ok('--advance', 'pr')

    def test_complete_gated_run_without_second_review(self):
        self.reviewed()
        self.finish()
        self.assertFalse((self.root / '.ai/reviews/round-2.md').exists())
        self.blocked('--print-next', contains='run complete')

    def test_fixes_require_fresh_tests_and_focused_review(self):
        self.reviewed(skip=True, blocking=3)
        self.write('fix.txt', 'Regression fix\n')
        self.commit('fix: review findings')
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='tests missing, failed, or stale')
        self.run_passing_check()
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='round-2.md does not exist')
        self.report('round-2.md', blocking=1)
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='unresolved blocking')
        self.report('round-2.md')
        self.write('fix.txt', 'Final regression fix\n')
        self.commit('fix: finish review changes')
        self.run_passing_check()
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='stale review')
        self.report('round-2.md')
        self.finish()

    def test_blockers_require_verification_even_without_code_changes(self):
        self.reviewed(blocking=1)
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='round-2.md does not exist')
        self.report('round-2.md')
        self.finish()

    def test_dirty_tree_and_failed_tests_never_pass(self):
        self.reviewed()
        self.write('feature.txt', 'untested\n')
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='worktree is dirty')
        self.blocked('--test', PY, '-c', 'pass', contains='worktree is dirty')
        self.commit('fix: further change')
        self.blocked('--test', *self.state()['check_command'], contains='test command failed')
        self.assertEqual(self.state()['suite']['result'], 'fail')
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='tests missing, failed, or stale')

    def test_test_command_cannot_mutate_worktree_or_use_missing_executable(self):
        self.implementation()
        self.blocked('--test', PY, '-c', 'from pathlib import Path; Path("feature.txt").write_text("changed")', contains='changed the worktree')
        self.git('restore', 'feature.txt')
        self.blocked('--test', str(self.tmp / 'no-command'), contains='test command failed')
        self.assertEqual(self.state()['suite']['result'], 'fail')

    def test_test_command_double_dash_and_literal_arguments(self):
        self.implementation()
        self.ok('--test', '--', PY, '-c', 'import sys; assert sys.argv[1] == "a b;$literal"', 'a b;$literal')
        self.assertEqual(self.state()['suite']['command'][-1], 'a b;$literal')

    def test_stale_wrong_base_and_incomplete_review_are_rejected(self):
        self.implementation()
        self.run_passing_check()
        self.ok('--advance', 'test')
        self.report(sha=self.base)
        self.blocked('--advance', 'review', contains='stale review')
        self.report(base=self.head())
        self.blocked('--advance', 'review', contains='wrong review base')
        self.report()
        path = self.root / '.ai/reviews/round-1.md'
        original = path.read_text()
        for field in ('model', 'effort', 'backend', 'base', 'sha', 'blocking'):
            path.write_text('\n'.join(line for line in original.split('\n') if not line.startswith(field + ':')))
            self.blocked('--advance', 'review', contains=field)
        self.report()
        self.ok('--advance', 'review')

    def test_review_models_must_differ_from_all_authors(self):
        self.implementation()
        self.run_passing_check()
        self.ok('--advance', 'test')
        self.ok('--set', 'implementation_models=["composer","sonnet"]')
        self.report(model='SONNET')
        self.blocked('--advance', 'review', contains='different model')
        self.report()
        self.ok('--advance', 'review')
        self.finish()

    def test_missing_spec_review_and_self_review_block_implementation(self):
        self.gated()
        self.ok('--advance', 'plan', '--set', 'spec_path=spec.md', '--set', 'plan_path=plan.md', '--set', 'plan_models=["opus"]')
        self.blocked('--advance', 'spec_review', contains='spec-review.md does not exist')
        self.report('spec-review.md', model='opus')
        self.blocked('--advance', 'spec_review', contains='different model')
        self.report('spec-review.md', model='grok', blocking=1)
        self.blocked('--advance', 'spec_review', contains='blocking spec findings')

    def test_changed_accepted_plan_blocks_later_steps(self):
        self.plan()
        self.write('plan.md', 'Unreviewed new architecture\n')
        self.commit('docs: change plan')
        self.blocked('implement', contains='spec/plan changed')

    def test_skip_requires_reason_and_does_not_allow_other_skips(self):
        self.gated(skip=True)
        self.blocked('--advance', 'plan', '--set', 'spec_path=spec.md', '--set', 'plan_path=plan.md', '--set', 'plan_models=["opus"]', contains='spec_review_skip_reason')
        self.assertEqual(self.state()['step'], 'start')
        self.blocked('--set', 'skip=[]', contains='managed')
        self.blocked('--skip', 'review', contains='invalid choice')

    def test_actual_worktree_required_and_state_is_local(self):
        self.blocked('--init', GATED, '--base', self.base, contains='linked worktree')
        self.gated()
        self.assertEqual(self.state()['worktree_path'], str(self.root))
        self.ok('plan')
        self.root = self.main
        self.blocked('--print-next', contains='missing .ai/state.json')
        self.root = self.tmp / 'task' / 'bin'
        self.blocked('plan', contains='task worktree root')

    def test_control_fields_and_test_evidence_cannot_be_self_reported(self):
        self.gated()
        for key in ('suite', 'suite.sha', 'step', 'base_sha', 'worktree_path', 'spec_hash',
                    'spec_review_hash', 'review_hash', 'final_review_hash', 'check_command', 'proposal_hash', 'unknown'):
            self.blocked('--set', key + '=true', contains='managed')
        self.assertEqual(self.state()['suite'], {})
        self.blocked('--advance', 'pr', contains='next allowed step is plan')

    def test_setup_harness_and_tooling_complete_paths(self):
        for workflow in ('setup', 'harness', 'tooling'):
            with self.subTest(workflow=workflow):
                self.ok('--init', workflow)
                if workflow == 'tooling':
                    self.write('.ai/tooling-proposal.md', 'Approved: existing check command only.\n')
                steps = {
                    'setup': [('audit', ['profile=small', 'platform=linux', 'stack=python']),
                              ('files', ['claude_md=true', 'state_check=true'])],
                    'harness': [('prereq', ['claude_md=true']), ('platform', ['platform_ok=true']),
                                ('scripts', ['scripts_written=true']), ('vendors', ['vendors_resolved=true'])],
                    'tooling': [('detect', ['profile=small', 'platform=linux', 'stack=python']),
                                ('audit', ['audit_done=true']), ('propose', ['proposal_approved=true']),
                                ('install', ['installed_tiers=["essential"]'])],
                }[workflow]
                if workflow == 'harness':
                    for script in ('ai-review-run.py', 'ai-review-run-test.py'):
                        self.write('bin/' + script, '# Harness presence fixture; runner behavior tested separately.\n')
                    self.commit('build: harness fixtures')
                for step, values in steps:
                    args = ['--advance', step]
                    for value in values:
                        args += ['--set', value]
                    self.ok(*args)
                self.ok('--set', 'implementation_models=["opus"]')
                self.ok('--test', PY, '-c', 'from pathlib import Path; assert Path("CLAUDE.md").is_file()')
                self.ok('--advance', 'guides' if workflow == 'tooling' else 'smoke', '--set',
                        'guides_updated=true' if workflow == 'tooling' else 'smoke_ok=true')
                self.report(base=self.state()['base_sha'])
                self.ok('--advance', 'review')
                self.ok('--advance', 'verify')
                self.ok('--advance', 'pr')
                self.ok('--archive')
        self.assertEqual(len(list((self.root / '.ai/runs').iterdir())), 3)

    def test_root_guidance_can_be_agents_without_claude(self):
        (self.root / 'CLAUDE.md').unlink()
        for workflow in ('setup', 'harness'):
            with self.subTest(workflow=workflow):
                self.ok('--init', workflow)
                if workflow == 'setup':
                    self.ok('--advance', 'audit', '--set', 'profile=small',
                            '--set', 'platform=linux', '--set', 'stack=python')
                step = 'files' if workflow == 'setup' else 'prereq'
                args = ['--advance', step, '--set', 'claude_md=true']
                if workflow == 'setup':
                    args += ['--set', 'state_check=true']
                for directory in (False, True):
                    if directory:
                        (self.root / 'AGENTS.md').mkdir()
                    self.blocked(*args, contains='CLAUDE.md')
                    self.assertNotEqual(self.state()['step'], step)
                    if directory:
                        (self.root / 'AGENTS.md').rmdir()
                self.write('AGENTS.md', '# Canonical root guidance\n')
                self.ok(*args)
                self.ok('--archive')
                (self.root / 'AGENTS.md').unlink()

    def test_tooling_approval_type_and_physical_files(self):
        self.ok('--init', 'tooling')
        self.write('.ai/tooling-proposal.md', 'Approved: existing check command only.\n')
        self.ok('--advance', 'detect', '--set', 'profile=small', '--set', 'platform=linux', '--set', 'stack=python')
        self.ok('--advance', 'audit', '--set', 'audit_done=true')
        for value in ('yes', '1', '"true"'):
            self.blocked('--advance', 'propose', '--set', 'proposal_approved=' + value, contains='must be JSON true')
        self.assertEqual(self.state()['step'], 'audit')
        self.ok('--advance', 'propose', '--set', 'proposal_approved=true')
        self.ok('--advance', 'install', '--set', 'installed_tiers=["essential"]')
        (self.root / 'docs/ai/tooling.md').unlink()
        self.blocked('review', contains='next allowed step is guides')
        self.blocked('--advance', 'guides', '--set', 'guides_updated=true', contains='does not exist')

    def test_archive_preserves_evidence_and_old_schema_can_be_archived(self):
        self.reviewed()
        self.blocked('--init', GATED, '--base', self.base, contains='existing run')
        self.ok('--archive')
        archives = list((self.root / '.ai/runs').iterdir())
        self.assertTrue((archives[0] / 'reviews/round-1.md').is_file())
        self.assertTrue((archives[0] / 'test.log').is_file())
        self.ok('--init', GATED, '--base', self.base)
        self.write('.ai/state.json', '{"workflow":"setup","step":"review"}')
        self.blocked('--print-next', contains='older state schema')
        self.ok('--archive')

    def test_accepted_findings_cannot_be_rewritten_or_cleared_by_unrelated_verification(self):
        self.reviewed(blocking=1)
        path = self.root / '.ai/reviews/round-1.md'
        accepted = path.read_text()
        self.report(blocking=0)
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='accepted report changed')
        path.write_text(accepted)
        self.report('round-2.md')
        second = self.root / '.ai/reviews/round-2.md'
        second.write_text(second.read_text().replace(self.state()['review_hash'], '0' * 64))
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='previous must identify')
        self.report('round-2.md')
        self.ok('--advance', 'verify', '--set', 'product_check=Verified')
        accepted_second = second.read_text()
        second.write_text(accepted_second + 'Unaccepted amendment\n')
        self.blocked('pr', contains='accepted final review changed')
        second.write_text(accepted_second)
        self.ok('--advance', 'pr')
        self.blocked('--set', 'implementation_models=["composer","other"]', contains='run complete')
        self.blocked('--test', *self.state()['check_command'], contains='run complete')

    def test_author_history_survives_fallbacks_and_normalizes_identity(self):
        self.implementation()
        self.ok('--set', 'implementation_models=[" composer "," SONNET "]')
        self.assertEqual(self.state()['implementation_models'], ['composer', 'sonnet'])
        self.blocked('--set', 'implementation_models=["composer"]', contains='cannot remove recorded authors')
        self.run_passing_check()
        self.ok('--advance', 'test')
        self.report(model='sonnet')
        self.blocked('--advance', 'review', contains='different model')

    def test_accepted_spec_evidence_is_required_when_resuming(self):
        self.plan()
        path = self.root / '.ai/reviews/spec-review.md'
        accepted = path.read_text()
        path.unlink()
        self.blocked('implement', contains='spec-review.md does not exist')
        self.write('.ai/reviews/spec-review.md', accepted + 'Unaccepted amendment\n')
        self.blocked('implement', contains='accepted report changed')
        path.write_text(accepted)
        self.ok('implement')

    def test_narrow_fix_plan_cannot_drift_after_skipping_spec_review(self):
        self.plan(skip=True)
        self.write('plan.md', 'New design outside the narrow fix\n')
        self.commit('docs: change scope')
        self.blocked('implement', contains='spec/plan changed')

    def test_recorded_check_cannot_be_replaced_with_a_weaker_command_or_log(self):
        self.reviewed()
        self.blocked('--test', PY, '-c', 'pass', contains='same recorded check command')
        self.write('.ai/test.log', 'Different check result\n')
        self.blocked('--advance', 'verify', '--set', 'product_check=Verified', contains='test log changed')
        self.run_passing_check()
        self.finish()

    def test_approved_tooling_scope_is_preserved_until_install_and_archive(self):
        self.ok('--init', 'tooling')
        self.ok('--advance', 'detect', '--set', 'profile=small', '--set', 'platform=linux', '--set', 'stack=python')
        self.ok('--advance', 'audit', '--set', 'audit_done=true')
        self.blocked('--advance', 'propose', '--set', 'proposal_approved=true', contains='tooling-proposal.md does not exist')
        self.write('.ai/tooling-proposal.md', 'Install approved formatter only\n')
        self.ok('--advance', 'propose', '--set', 'proposal_approved=true')
        self.write('.ai/tooling-proposal.md', 'Install additional unapproved dependency\n')
        self.blocked('install', contains='approved tooling proposal changed')
        self.write('.ai/tooling-proposal.md', 'Install approved formatter only\n')
        self.ok('install')
        self.ok('--set', 'proposal_approved=false')
        self.blocked('install', contains='must be JSON true')
        self.ok('--archive')
        saved = list((self.root / '.ai/runs').glob('*/tooling-proposal.md'))
        self.assertEqual(saved[0].read_text(), 'Install approved formatter only\n')

    def test_orphaned_evidence_can_be_archived_without_overwriting_it(self):
        self.reviewed()
        (self.root / '.ai/state.json').unlink()
        self.blocked('--init', GATED, '--base', self.base, contains='existing run/evidence')
        self.ok('--archive')
        self.assertTrue(list((self.root / '.ai/runs').glob('*/reviews/round-1.md')))
        self.ok('--init', GATED, '--base', self.base)


if __name__ == '__main__':
    unittest.main(verbosity=1)
