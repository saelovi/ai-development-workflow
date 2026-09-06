# Abi's model preferences — optional example

This is my personal starting point, separate from the workflow's general rules. Select it explicitly or edit [model-preferences.md](model-preferences.md) for your own setup. The generic profile's identity, fallback, and measurement rules apply here too.

These names describe preferences carried over from my working setup, not verified current availability, exact invocation ids, pricing, or benchmark rankings. Resolve actual models and account access when used, and record them in the target repo's `docs/ai/vendors.md`.

| Role | My preferred route | Why / when |
| ---- | ------------------ | ---------- |
| Orchestration and normal planning | Claude Opus | Interactive planning, decisions, state, and direct dispatch |
| Optional delegated planning | Planning worker; Fable when available and useful | Independent exploration for substantial work; not every task |
| Spec review | Grok via Cursor; example preference: Grok 4.6 standard, high effort | Challenge architecture, assumptions, acceptance criteria, and scope |
| Implementation, default lane | Composer via Cursor; example preference: Composer 2.5 standard | Any task the plan judges it sufficient for: mechanical change, decisive check. Fast, and on a separate allowance |
| Implementation, stronger lane | Claude subagent in the same worktree: Sonnet by default, Opus when the plan flags the task as genuinely hard | Chosen per task by the planner: the riskiest task, design judgment, cross-cutting change, auth/payment/data/migration paths |
| Code review | Codex; example preference: GPT Sol | Independent review and focused verification of fixes |

I favor Composer partly because the Cursor allowance available to me has provided a separate, larger budget pool. That is an account-specific reason, not a claim that it is universally cheapest or best. I use standard Cursor implementation ids rather than `-fast`. Change that setting if your own measured results justify it.

My fallback order:

- Spec review: another available Grok model, then an available non-author model through a reviewer worker or separate session.
- Implementation: another suitable Cursor standard model, then a capable implementation worker in the same task worktree. Inspect partial edits before switching.
- Code review: another available Codex model, then another reviewer distinct from every implementation author.

For an Opus-authored artifact, I select a non-Opus reviewer. If both Opus and another fallback authored it, the reviewer must differ from both. A role name is not an identity; I keep the actual cumulative authors in state and verify which model reviewed the work.

## My plugins

The workflow requires no plugin, and the shared procedure never depends on one. I run it with three Claude Code plugins, and the bundle names them where that is useful, so you can see exactly what is in play:

| Plugin | Where I use it | What it contributes |
| ------ | -------------- | ------------------- |
| superpowers | Claude Code | Process skills. Quick and standard work skips its interviews, design pauses, and blanket TDD, as the delivery guide states. Gated planning may use its planning skills inside the plan step. The implementer brief preloads `systematic-debugging` and `verification-before-completion`; without the plugin those entries are skipped and the brief's own rules apply. When I triage spec or code findings, I apply `receiving-code-review`: verify each finding against the code before acting, and decline with reasoning when it is wrong. |
| context7 | Claude Code, Codex, Cursor | Current library documentation on demand, so plans and implementation check real API behavior rather than training memory. |
| ponytail | Claude Code and Codex through hooks; Cursor through rules | A minimal-solution stance: reuse before writing, standard library before a dependency, the smallest correct change. It shapes what gets built, not the delivery procedure. |

Quick edits do not dispatch this roster. The plan assigns a lane per task, so the stronger lane is chosen up front where it reduces repair cycles rather than after a failed round. I compare total cost and human effort per accepted change rather than assuming the lowest-cost implementation call wins. These choices are meant to be revisited, not treated as universal rules.
