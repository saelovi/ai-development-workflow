#!/usr/bin/env python3
"""Optional POSIX review runner. Python 3.8+, git, adjacent ai-state-check.py.

Run from the task worktree root. Pass an installed CLI argument list after --;
stdin is closed. Request blocking: N, blank line, review body; a preamble is OK.
For event streams, --report-file supplies a fresh {report_file} command argument.
Model/backend/effort must describe the actual resolved invocation. This runner
checks evidence formatting and revisions; it cannot attest provider identity.
"""
from __future__ import annotations

import argparse
import math
import os
import re
import runpy
import signal
import subprocess
import sys
import tempfile
from pathlib import Path

gate = runpy.run_path(str(Path(__file__).with_name('ai-state-check.py')))
Stop = gate['Stop']


def run(args):
    if os.name != 'posix':
        raise Stop('runner requires POSIX process groups; use a native review session')
    if not args.command or not math.isfinite(args.timeout) or args.timeout <= 0:
        raise Stop('provide a command and a finite positive timeout')
    if args.report_file != any('{report_file}' in arg for arg in args.command):
        raise Stop('--report-file and a {report_file} command placeholder must be used together')
    gate['repo_root']()
    state = gate['load']()
    if gate['next_step'](state) is None:
        raise Stop('run complete; archive before another review')
    gate['clean']()
    authors = state.get('plan_models', []) if args.kind == 'spec' else state['implementation_models']
    gate['model_list'](authors, 'authors')
    for key in ('model', 'backend', 'effort'):
        value = getattr(args, key)
        gate['text_value'](value, key)
        if '\n' in value or '\r' in value:
            raise Stop(key + ': expected a single line')
    if args.model.strip().casefold() in {m.strip().casefold() for m in authors}:
        raise Stop('select a model independent of all authors before dispatch')
    names = {'spec': 'spec-review.md', 'code': 'round-1.md', 'verify': 'round-2.md'}
    name = args.output or names[args.kind]
    if Path(name).name != name or not name.endswith('.md'):
        raise Stop('--output must be a .md basename inside .ai/reviews')
    if name in names.values() and name != names[args.kind]:
        raise Stop('--output does not match the review kind')
    destination = gate['REVIEWS'] / name
    if destination.exists() or destination.is_symlink():
        raise Stop('output exists; preserve previous attempts instead of overwriting')
    previous = ''
    if args.kind == 'verify':
        gate['unchanged_report'](gate['REVIEWS'] / names['code'], state,
                                 'review_hash', authors)
        previous = 'previous: ' + state['review_hash'] + '\n'
    sha = gate['git']('rev-parse', 'HEAD')
    state_bytes = gate['STATE'].read_bytes()
    destination.parent.mkdir(parents=True, exist_ok=True)
    # ponytail: one dispatcher per worktree; no scheduler or vendor SDK adapters.
    with tempfile.TemporaryDirectory(prefix='attempt-', dir=str(destination.parent)) as scratch:
        # Keep attempts (including failures) outside TemporaryDirectory cleanup.
        attempt = Path(scratch + '-logs')
        attempt.mkdir()
        raw, errors = attempt / 'stdout.log', attempt / 'stderr.log'
        response = attempt / 'response.txt'
        command = [arg.replace('{report_file}', str(response.resolve())) for arg in args.command]
        print('attempt logs: ' + str(attempt), flush=True)
        result = 'launch failed'
        try:
            with raw.open('wb') as out, errors.open('wb') as err:
                child = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                         stdout=out, stderr=err, start_new_session=True)
                try:
                    try:
                        status = child.wait(timeout=args.timeout)
                        result = 'exit: ' + str(status)
                    except subprocess.TimeoutExpired:
                        result = 'timeout'
                        raise Stop('review timed out; attempt logs preserved')
                finally:
                    # Kill only our group, even if its leader exited leaving children.
                    # Detached/daemonized children require a stronger host sandbox.
                    try:
                        os.killpg(child.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                    child.wait()
            if status:
                raise Stop('review command failed (' + str(status) + '); attempt logs preserved')
            if gate['git']('rev-parse', 'HEAD') != sha or gate['STATE'].read_bytes() != state_bytes:
                raise Stop('HEAD or gate state changed during review')
            gate['clean']()
            if args.report_file and (response.is_symlink() or not response.is_file()):
                raise Stop('command did not create a regular response file; attempt logs preserved')
            content = (response if args.report_file else raw).read_text(encoding='utf-8-sig')
            counts = list(re.finditer(r'^blocking:[^\n]*$', content, re.MULTILINE))
            if len(counts) != 1:
                raise Stop('response needs exactly one blocking: count line; missing or ambiguous report')
            content = content[counts[0].start():]
            header, separator, body = content.partition('\n\n')
            if not separator or not header.startswith('blocking:') or '\n' in header:
                raise Stop('response needs blocking: N, a blank line, and review notes')
            candidate = Path(scratch) / 'report.md'
            candidate.write_text(
                'model: ' + args.model.strip() + '\neffort: ' + args.effort.strip() +
                '\nbackend: ' + args.backend.strip() + '\nbase: ' + state['base_sha'] +
                '\nsha: ' + sha + '\n' + header + '\n' + previous + '\n' + body,
                encoding='utf-8')
            gate['report'](candidate, state, authors)
            # Same-filesystem exclusive publication; never clobber an accepted report.
            os.link(candidate, destination)
        finally:
            (attempt / 'status.txt').write_text(result + '\n', encoding='utf-8')
    print('validated report: ' + str(destination) + '; gate acceptance is a separate step')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kind', choices=('spec', 'code', 'verify'), required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--backend', required=True)
    parser.add_argument('--effort', default='default')
    parser.add_argument('--timeout', type=float, default=900)
    parser.add_argument('--output', help='optional .md basename, e.g. smoke.md')
    parser.add_argument('--report-file', action='store_true',
                        help='read fresh final-response file; pass {report_file} in command arguments')
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    if args.command[:1] == ['--']:
        args.command = args.command[1:]
    try:
        run(args)
    except (Stop, OSError, ValueError, KeyboardInterrupt) as exc:
        print('stop: ' + (str(exc) or 'interrupted'), file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
