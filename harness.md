# Task: Install optional review automation

Use a new task worktree after bootstrap merges. Prerequisites: `AGENTS.md` or `CLAUDE.md`, `docs/ai/workflows.md`, `docs/ai/overrides.md`, and both `bin/ai-state-check*.py` files. Adapt an existing working harness first. This task does not install linters or CI.

Install only when repeated external reviews justify it. The reference runner needs Python 3.8+, Git, and POSIX process groups (Linux/macOS/WSL); Git Bash alone does not establish that support. Other platforms use native independent review sessions until there is a tested native runner. Missing automation never waives required independent review.

From the task worktree root: `<py> bin/ai-state-check.py --init harness`. Steps: `prereq → platform → scripts → vendors → smoke → review → verify → pr`. Check/advance each step with the gate; no skips. The existing delivery guide defines evidence and review budgets.

## prereq → platform

Confirm bootstrap, then `--advance prereq --set claude_md=true`. Verify Python, Git, and process-group support. If unsupported, record that limitation and use native review sessions; do not mark this optional installation complete. Otherwise `--advance platform --set platform_ok=true`.

## scripts

Copy `ai-review-run.py` and `ai-review-run-test.py` from this bundle verbatim into `bin/`, beside both checker files. Update checker/tests together because `scripts_written` now checks these reference filenames. Finish an active installation with its existing checker before upgrading when practical.

Keep the actual CLI invocation recipes in `docs/ai/vendors.md`. Verify installed CLI help/current official docs when configuring a route. Use the CLI's plain final-response output or a final-response file. Use `--report-file` for CLIs that stream events; do not parse arbitrary event logs as review prose.

```
<py> bin/ai-review-run.py --kind code --model <actual-canonical-id> --backend <actual-cli> --effort <actual-setting> --timeout 900 -- <cli> <verified-noninteractive-arguments>
```

Pass prompts/files through the CLI's supported arguments; stdin is closed. Include base/HEAD, review scope, author ids, spec/plan and test pointers, and the delivery review checklist. Ask the final response to contain a single count line, blank line, and review body:

```
blocking: <non-negative integer>

<findings with stable ids and evidence, or concrete clean-review notes>
```

A short preamble is allowed. Multiple `blocking:` lines are ambiguous and rejected; the runner never chooses the first count from competing reports. Prefer a fresh final-response file when stdout carries events:

```
<py> bin/ai-review-run.py --kind code --model <actual-id> --backend <actual-cli> --report-file -- <cli> <verified-arguments> <final-output-option> '{report_file}'
```

The runner substitutes `{report_file}` with a new private attempt path. The CLI must create it during this successful call; missing/symlink output is rejected. Stdout/stderr remain diagnostic logs. For Codex, `exec --output-last-message '{report_file}'` supplies the final message, including with `--json`; verify the installed flags. Default `codex exec` sends progress to stderr and the final message to stdout. See [official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode). The file still needs a valid count and review body; no default-zero fallback.

The runner stamps invocation identity and current revisions, then reuses the checker's report parser. `--kind spec|code|verify` chooses `spec-review.md`, `round-1.md`, or `round-2.md`; verification binds the accepted round-1 hash. `--output smoke.md` publishes a smoke artifact instead. Output is restricted to `.ai/reviews/` basenames, and any existing output is refused. Keep earlier attempts under distinct names before an unaccepted retry; never move/replace a gate-accepted report.

The runner rejects known author/model collisions before dispatch, dirty work before/after, changed HEAD/state, nonzero exit, invalid output, and elapsed time beyond the ceiling. It terminates its own process group, including children remaining after the leader exits. It preserves stdout/stderr and child status under `.ai/reviews/attempt-*-logs/`, and publishes only a validated report. It never advances state. A zero-blocker count is a reviewer claim, not proof of correctness.

Identity arguments must match the actual resolved invocation. Check provider/session metadata for silent fallback; this generic runner cannot attest model identity or detect aliases. Review permissions must stay read-only except report output; the runner checks changes after execution and is not a sandbox. Detached/daemonized children need stronger host isolation. Logs stay local and ignored; follow repo evidence-retention policy.

No separate probe script, vendor SDK, runner agent, automatic retry scheduler, or no-growth watchdog. A bounded real review is the useful first availability check; setup/diagnostic probes are only for unresolved configuration. Exit 0 means validated output; exit 1 means inspect preserved diagnostics. Provider exit status is in `status.txt`; timeout is not proof of exhausted credit. One fallback attempt per configured alternate; keep the same review round and carry forward valid unresolved findings from failed attempts.

The orchestrator invokes implementation directly using host-native timeout/cleanup safeguards; this script is review-only. Never automatically retry implementation after partial edits: inspect and resume the actual worktree. Honor any selected profile's model/effort restrictions at route selection; model policy belongs in vendors, not the generic process runner.

Regenerate derived guide pointers as needed. `--advance scripts --set scripts_written=true`.

## vendors

Seed `docs/ai/vendors.md` from the selected profile: generic `model-preferences.md` by default, or `model-preferences.abi.md` when explicitly requested. Keep operator preferences, verified ids/dates, command recipes, and a short fallback chain in this single document. Resolve full model listings without inferring absence from truncated output; verify alternate ids only when needed.

Reserve a reviewer distinct from all actual authors. Use the selection rules in `docs/ai/vendors.md`. If independence/availability cannot be established, leave review pending or draft. Record all authors when switching implementers.

Resolve primary routes and verify configuration using bounded calls; reuse a successful real call instead of buying a duplicate probe. Distinguish verified routes from untested preferences, and list unavailable primaries and verified substitutes. Then `--advance vendors --set vendors_resolved=true`.

## smoke → review → verify → pr

Run `<py> bin/ai-review-run-test.py` and add it to the repo's existing check entry point alongside checker tests. The stubs exercise failures, malformed output, timeout/child cleanup, dirty/stale evidence, independence, immutable publication, and verification binding without model charges.

Run one real review invocation with `--output smoke.md` to verify the installed CLI's actual output and identity handling; reuse it as that route's setup verification. Stub success alone is not live vendor validation. Commit changes, record all author ids, capture repo checks through `--test`, then `--advance smoke --set smoke_ok=true`.

Review the committed harness with an independent model, using the configured code-review route; write round 1 and `--advance review`. Fix/commit findings, rerun checks and focused round 2 only when required. `--advance verify`, open the PR, `--advance pr`. Hand off verified routes, untested fallbacks, cleanup limits, and evidence. Never mark an unexecuted vendor call as verified.
