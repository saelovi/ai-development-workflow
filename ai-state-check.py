#!/usr/bin/env python3
"""State and evidence checks for substantial work. Quick changes do not use this gate.

Run from the task worktree root. --help lists the commands. No dependencies beyond
Python 3.8+ and git. Tests: python3 ai-state-check-test.py.

The gate checks revision identity and recorded evidence, not the truth of an LLM's
findings or a human approval. Only --test records test results; reviewers write
reports; the orchestrator alone advances state. This is not a security boundary.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

STATE = Path('.ai/state.json')
REVIEWS = Path('.ai/reviews')
RUN_ARTIFACTS = (STATE, REVIEWS, Path('.ai/test.log'), Path('.ai/tooling-proposal.md'))
GATED = 'implement-with-review-gate'
ORDER = {
    'setup': ['audit', 'files', 'smoke', 'review', 'verify', 'pr'],
    'harness': ['prereq', 'platform', 'scripts', 'vendors', 'smoke', 'review', 'verify', 'pr'],
    'tooling': ['detect', 'audit', 'propose', 'install', 'guides', 'review', 'verify', 'pr'],
    GATED: ['plan', 'spec_review', 'implement', 'test', 'review', 'verify', 'pr'],
}
DEFAULTS = {
    'setup': {'profile': '', 'platform': '', 'stack': '', 'claude_md': False,
              'state_check': False, 'smoke_ok': False},
    'harness': {'claude_md': False, 'platform_ok': False, 'scripts_written': False,
                'vendors_resolved': False, 'smoke_ok': False},
    'tooling': {'profile': '', 'platform': '', 'stack': '', 'audit_done': False,
                'proposal_approved': False, 'installed_tiers': [], 'guides_updated': False},
    GATED: {'spec_path': '', 'plan_path': '', 'plan_models': [],
            'spec_review_skip_reason': '', 'product_check': ''},
}
REQUIRES = {
    ('setup', 'files'): ['profile', 'platform', 'stack'],
    ('setup', 'smoke'): ['claude_md', 'state_check'],
    ('setup', 'review'): ['smoke_ok'],
    ('harness', 'platform'): ['claude_md'],
    ('harness', 'scripts'): ['platform_ok'],
    ('harness', 'vendors'): ['scripts_written'],
    ('harness', 'smoke'): ['vendors_resolved'],
    ('harness', 'review'): ['smoke_ok'],
    ('tooling', 'audit'): ['profile', 'platform', 'stack'],
    ('tooling', 'propose'): ['audit_done'],
    ('tooling', 'install'): ['proposal_approved'],
    ('tooling', 'guides'): ['installed_tiers'],
    ('tooling', 'review'): ['guides_updated'],
    (GATED, 'spec_review'): ['spec_path', 'plan_path', 'plan_models'],
    (GATED, 'implement'): ['spec_path', 'plan_path', 'plan_models'],
    (GATED, 'test'): ['implementation_models'],
    (GATED, 'pr'): ['product_check'],
}
BOOL_FILES = {
    'state_check': ['bin/ai-state-check.py', 'bin/ai-state-check-test.py'],
    'scripts_written': ['bin/ai-review-run.py', 'bin/ai-review-run-test.py'],
    'guides_updated': ['docs/ai/tooling.md'],
}
MANAGED = {'schema', 'workflow', 'step', 'skip', 'base_sha', 'worktree_path', 'suite',
           'spec_hash', 'spec_review_hash', 'review_hash', 'final_review_hash',
           'check_command', 'proposal_hash'}
PLACEHOLDERS = {'', 'todo', 'tbd', '?', 'n/a', 'na', 'none', 'null', '-'}


class Stop(Exception):
    pass


def git(*args):
    result = subprocess.run(['git', *args], capture_output=True, text=True)
    if result.returncode:
        raise Stop(result.stderr.strip() or 'git command failed')
    return result.stdout.strip()


def same_path(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def repo_root():
    if not same_path(git('rev-parse', '--show-toplevel'), str(Path.cwd())):
        raise Stop('run from the task worktree root')


def clean():
    if git('status', '--porcelain', '--untracked-files=all'):
        raise Stop('worktree is dirty; commit the intended changes before recording evidence')


def commit(ref):
    if not isinstance(ref, str) or not re.fullmatch(r'[0-9a-fA-F]{40}|[0-9a-fA-F]{64}', ref):
        raise Stop('evidence sha must be a full commit id')
    return git('rev-parse', '--verify', ref + '^{commit}')


def ancestor(base, head):
    return git('merge-base', base, head) == base


def text_value(value, key):
    if not isinstance(value, str) or value.strip().lower() in PLACEHOLDERS:
        raise Stop(key + ': expected non-placeholder text')


def model_list(value, key):
    if not isinstance(value, list) or not value:
        raise Stop(key + ': expected a non-empty list of actual model ids')
    for model in value:
        text_value(model, key)


def template(workflow):
    return dict(schema=3, workflow=workflow, step='start', skip=[], base_sha='',
                worktree_path='', implementation_models=[], suite={}, check_command=[],
                spec_hash='', spec_review_hash='', review_hash='', final_review_hash='', proposal_hash='',
                **DEFAULTS[workflow])


def load():
    if not STATE.is_file():
        raise Stop('missing .ai/state.json; use --init first')
    state = json.loads(STATE.read_text(encoding='utf-8-sig'))
    if not isinstance(state, dict) or state.get('schema') != 3:
        raise Stop('older state schema; archive the old run and restart with the new workflow')
    if state.get('workflow') not in ORDER:
        raise Stop('unknown workflow in state')
    if state.get('skip') not in ([], ['spec_review']) or (state['skip'] and state['workflow'] != GATED):
        raise Stop('only spec_review may be skipped, and only in a gated run')
    if not same_path(state.get('worktree_path', ''), str(Path.cwd())):
        raise Stop('state belongs to another worktree; run from its root')
    return state


def save(state):
    # ponytail: one orchestrator per worktree; add locking if concurrent writers are needed.
    STATE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STATE.with_suffix('.json.tmp')
    tmp.write_text(json.dumps(state, indent=2) + '\n', encoding='utf-8')
    os.replace(tmp, STATE)


def order(state):
    return [step for step in ORDER[state['workflow']] if step not in state['skip']]


def next_step(state):
    steps = ['start', *order(state)]
    if state['step'] not in steps:
        raise Stop('invalid step in state')
    index = steps.index(state['step']) + 1
    return steps[index] if index < len(steps) else None


def set_values(state, items):
    allowed = set(DEFAULTS[state['workflow']]) | {'implementation_models'}
    for item in items:
        key, sep, raw = item.partition('=')
        if not sep or key not in allowed or key in MANAGED:
            raise Stop('--set accepts only template input keys; control and evidence fields are managed')
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = raw
        if key.endswith('_models'):
            model_list(value, key)
            value = list(dict.fromkeys(model.strip().casefold() for model in value))
            if not set(state.get(key, [])).issubset(value):
                raise Stop(key + ': cannot remove recorded authors; include previous models on fallback')
        state[key] = value


def key_check(state, key):
    value = state.get(key)
    default = DEFAULTS[state['workflow']].get(key)
    if isinstance(default, bool):
        if value is not True:
            raise Stop(key + ': must be JSON true')
        if key == 'claude_md' and not any(Path(p).is_file() for p in ('CLAUDE.md', 'AGENTS.md')):
            raise Stop('CLAUDE.md or AGENTS.md does not exist')
        for path in BOOL_FILES.get(key, []):
            if not Path(path).is_file():
                raise Stop(path + ' does not exist')
    elif key == 'profile':
        if value not in ('small', 'medium', 'large'):
            raise Stop('profile: expected small, medium, or large')
    elif key == 'installed_tiers':
        if not isinstance(value, list) or not value or any(t not in ('essential', 'recommended', 'optional') for t in value):
            raise Stop('installed_tiers: expected non-empty list of approved tiers')
    elif key.endswith('_models'):
        model_list(value, key)
    else:
        text_value(value, key)
        if key in ('spec_path', 'plan_path'):
            path = Path(value).resolve()
            try:
                path.relative_to(Path.cwd())
            except ValueError:
                raise Stop(key + ': must be inside the task worktree')
            if not path.is_file():
                raise Stop(key + ': file not found')
            git('cat-file', '-e', 'HEAD:' + path.relative_to(Path.cwd()).as_posix())


def spec_hash(state):
    digest = hashlib.sha256()
    for key in ('spec_path', 'plan_path'):
        key_check(state, key)
        digest.update(json.dumps([state[key], Path(state[key]).read_text(encoding='utf-8')]).encode())
    return digest.hexdigest()


def file_hash(path):
    if not path.is_file():
        raise Stop(str(path) + ' does not exist')
    content = path.read_bytes()
    if not content.strip():
        raise Stop(str(path) + ' is empty')
    return hashlib.sha256(content).hexdigest()


def unchanged_report(path, state, hash_key, authors):
    if file_hash(path) != state.get(hash_key):
        raise Stop(str(path) + ': accepted report changed; restore it or restart review in a new run')
    return report(path, state, authors, exact=False)


def report(path, state, authors, exact=True):
    if not path.is_file():
        raise Stop(str(path) + ' does not exist')
    header, separator, body = path.read_text(encoding='utf-8-sig').partition('\n\n')
    if not separator or not body.strip():
        raise Stop(str(path) + ': needs a header, blank line, and findings or verification notes')
    fields = {}
    for line in header.splitlines():
        key, sep, value = line.partition(':')
        if not sep or key in fields:
            raise Stop(str(path) + ': malformed or duplicate header field')
        fields[key] = value.strip()
    for key in ('model', 'effort', 'backend', 'base', 'sha', 'blocking'):
        text_value(fields.get(key), str(path) + ': ' + key)
    sha = commit(fields['sha'])
    if commit(fields['base']) != state['base_sha']:
        raise Stop(str(path) + ': wrong review base')
    head = git('rev-parse', 'HEAD')
    if not ancestor(state['base_sha'], sha) or not ancestor(sha, head):
        raise Stop(str(path) + ': reviewed commit is not on this branch after its base')
    if exact and sha != head:
        raise Stop(str(path) + ': stale review; review the current HEAD')
    model_list(authors, 'authors')
    if fields['model'].casefold() in {m.strip().casefold() for m in authors}:
        raise Stop(str(path) + ': reviewer must use a different model from the authors')
    if not re.fullmatch(r'\d+', fields['blocking']):
        raise Stop(str(path) + ': blocking must be a non-negative integer')
    fields['blocking'] = int(fields['blocking'])
    return fields


def suite_check(state):
    suite = state.get('suite', {})
    if suite.get('result') != 'pass' or suite.get('sha') != git('rev-parse', 'HEAD'):
        raise Stop('tests missing, failed, or stale; run --test on the current HEAD')
    if file_hash(Path('.ai/test.log')) != suite.get('log_hash'):
        raise Stop('test log changed; run --test again')


def final_review(state):
    path = REVIEWS / 'round-1.md'
    first = unchanged_report(path, state, 'review_hash', state['implementation_models'])
    if first['sha'] != git('rev-parse', 'HEAD') or first['blocking']:
        path = REVIEWS / 'round-2.md'
        final = report(path, state, state['implementation_models'])
        if final.get('previous') != state['review_hash']:
            raise Stop('round-2.md: previous must identify the accepted round-1 report hash')
        if final['blocking']:
            raise Stop('unresolved blocking findings; keep the PR draft')
    return path


def check_step(state, step):
    for key in REQUIRES.get((state['workflow'], step), []):
        key_check(state, key)
    if state['workflow'] == GATED:
        if step in ('implement', 'test', 'review', 'verify', 'pr'):
            if state.get('spec_hash') != spec_hash(state):
                raise Stop('spec/plan changed after acceptance; restart planning with the revised scope')
            if 'spec_review' in state['skip']:
                key_check(state, 'spec_review_skip_reason')
            else:
                reviewed = unchanged_report(REVIEWS / 'spec-review.md', state, 'spec_review_hash', state['plan_models'])
                if reviewed['blocking']:
                    raise Stop('spec still has blocking findings')
    if state['workflow'] == 'tooling' and step in ('install', 'guides', 'review', 'verify', 'pr'):
        key_check(state, 'proposal_approved')
        if file_hash(Path('.ai/tooling-proposal.md')) != state.get('proposal_hash'):
            raise Stop('approved tooling proposal changed; obtain approval for the revised scope in a new run')
    if step in ('review', 'verify', 'pr'):
        key_check(state, 'implementation_models')
    if step == 'review':
        clean()
        suite_check(state)
    if step == 'verify':
        unchanged_report(REVIEWS / 'round-1.md', state, 'review_hash', state['implementation_models'])
    if step == 'pr':
        clean()
        suite_check(state)
        digest = file_hash(final_review(state))
        if state['final_review_hash'] and digest != state['final_review_hash']:
            raise Stop('accepted final review changed; restore it or restart review in a new run')
        return digest


def run_tests(state, command):
    if not command:
        raise Stop('--test needs a command after --')
    clean()
    if state['check_command'] and command != state['check_command']:
        raise Stop('use the same recorded check command; run targeted checks outside the gate')
    sha = git('rev-parse', 'HEAD')
    state['suite'] = {}  # An interrupted rerun must not leave an old pass behind.
    save(state)
    log = Path('.ai/test.log')
    with log.open('w', encoding='utf-8') as output:
        output.write('command: ' + json.dumps(command) + '\nsha: ' + sha + '\n\n')
        output.flush()
        try:
            result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            passed = result.returncode == 0
        except OSError as exc:
            output.write(str(exc) + '\n')
            passed = False
    passed = passed and git('rev-parse', 'HEAD') == sha and not git('status', '--porcelain', '--untracked-files=all')
    if passed:
        state['check_command'] = command
    state['suite'] = {'sha': sha, 'result': 'pass' if passed else 'fail', 'command': command,
                      'log_hash': file_hash(log)}
    save(state)
    if not passed:
        raise Stop('test command failed or changed the worktree; inspect .ai/test.log')
    print('ok: tests passed on ' + sha + '; log: .ai/test.log')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument('--init', choices=ORDER)
    modes.add_argument('--template', choices=ORDER)
    modes.add_argument('--advance', metavar='STEP')
    modes.add_argument('--print-next', action='store_true')
    modes.add_argument('--test', nargs=argparse.REMAINDER, metavar='COMMAND')
    modes.add_argument('--archive', action='store_true', help='preserve state and evidence before a new run')
    parser.add_argument('step', nargs='?')
    parser.add_argument('--set', action='append', default=[], metavar='KEY=VALUE')
    parser.add_argument('--skip', choices=['spec_review'], action='append', default=[])
    parser.add_argument('--base', help='with --init: PR target ref; required for gated work')
    argv = sys.argv[1:]
    # argparse otherwise treats this separator as ending our optional arguments.
    if '--test' in argv:
        index = argv.index('--test') + 1
        if argv[index:index + 1] == ['--']:
            del argv[index]
    args = parser.parse_args(argv)
    if args.step and any((args.init, args.template, args.advance, args.print_next, args.test is not None, args.archive)):
        raise Stop('choose a step or one command mode')
    if (args.skip or args.base) and not args.init:
        raise Stop('--skip and --base go with --init only')
    if args.set and any((args.step, args.init, args.template, args.print_next, args.test is not None, args.archive)):
        raise Stop('--set goes alone or with --advance')
    if args.template:
        print(json.dumps(template(args.template), indent=2))
        return
    repo_root()
    if args.archive:
        if not any(path.exists() for path in RUN_ARTIFACTS):
            raise Stop('no run to archive')
        destination = Path('.ai/runs') / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        destination.mkdir(parents=True)
        for path in RUN_ARTIFACTS:
            if path.exists():
                path.rename(destination / path.name)
        print('ok: archived run and evidence in ' + str(destination))
        return
    if args.init:
        if any(path.exists() for path in RUN_ARTIFACTS):
            raise Stop('existing run/evidence; resume it or --archive before starting another run')
        if args.skip and args.init != GATED:
            raise Stop('only gated work can skip spec_review')
        if args.init == GATED:
            if not args.base:
                raise Stop('gated work needs --base <PR-target-ref>')
            if same_path(git('rev-parse', '--git-dir'), git('rev-parse', '--git-common-dir')):
                raise Stop('gated work needs a linked worktree, not the main checkout')
        state = template(args.init)
        state.update(worktree_path=str(Path.cwd()), skip=list(dict.fromkeys(args.skip)),
                     base_sha=git('merge-base', 'HEAD', args.base) if args.base else git('rev-parse', 'HEAD'))
        save(state)
        print('ok: initialized ' + args.init)
        return
    state = load()
    allowed = next_step(state)
    if allowed is None:
        raise Stop('run complete; --archive before starting another run')
    if args.test is not None:
        run_tests(state, args.test)
        return
    if args.set:
        set_values(state, args.set)
    if args.set and not args.advance:
        save(state)
        print('ok: inputs saved')
        return
    if args.print_next:
        print(allowed)
        return
    requested = args.advance or args.step
    if requested != allowed:
        raise Stop('next allowed step is ' + allowed)
    check_step(state, allowed)
    if args.advance:
        if allowed == 'plan' and 'spec_review' in state['skip']:
            clean()
            state['spec_hash'] = spec_hash(state)
        if allowed == 'propose':
            state['proposal_hash'] = file_hash(Path('.ai/tooling-proposal.md'))
        if allowed == 'spec_review':
            clean()
            reviewed = report(REVIEWS / 'spec-review.md', state, state['plan_models'])
            if reviewed['blocking']:
                raise Stop('resolve blocking spec findings before implementation')
            state['spec_hash'] = spec_hash(state)
            state['spec_review_hash'] = file_hash(REVIEWS / 'spec-review.md')
        if allowed == 'review':
            report(REVIEWS / 'round-1.md', state, state['implementation_models'])
            state['review_hash'] = file_hash(REVIEWS / 'round-1.md')
        state['step'] = allowed
        following = next_step(state)
        if following:
            evidence = check_step(state, following)
            if allowed == 'verify':
                state['final_review_hash'] = evidence
        save(state)
        print('ok: finished ' + allowed + '; next: ' + (following or 'complete'))
    else:
        print('ok: start ' + allowed)


if __name__ == '__main__':
    try:
        main()
    except (Stop, OSError, ValueError, KeyError, TypeError) as exc:
        sys.exit('ai-state-check: ' + str(exc))
