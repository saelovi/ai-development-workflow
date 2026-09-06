# Model preferences — generic starting point

Copy/adapt this profile into the target repo's `docs/ai/vendors.md`. These are editable operator settings, separate from the shared workflow. Start with existing user preferences and available accounts. Abi's optional example is [model-preferences.abi.md](model-preferences.abi.md).

| Role | Selection | Backend / exact id / effort | Verification |
| ---- | --------- | --------------------------- | ------------ |
| Orchestration and planning | Current capable coding assistant | Resolve from the active session | Unresolved until inspected |
| Optional delegated planning | Use only for useful separate exploration | Choose when needed | Not required by default |
| Spec review | Available model distinct from all plan authors | Choose when needed | Unresolved |
| Implementation | Available model suited to task complexity and budget | Choose when needed | Unresolved |
| Code review / focused verification | Available model distinct from all implementation authors | Choose when needed | Unresolved |

The table is not a roster to dispatch for every task. Quick changes normally use only the current assistant. Standard work adds independent review when warranted. Gated work requires independent spec/code review according to the delivery guide. A fresh session on the same model is not model independence.

## Fill in your choices

Record the actual canonical model id, backend, effort setting, verification date/result, and a short fallback order for each route when it is used. Use installed help or current official documentation for configuration. Model names in examples are not automatically current API/CLI ids. Do not infer absence from truncated model listings or probe unused fallbacks speculatively.

Choose implementation based on demonstrated fit and total delivery cost: implementation plus review, repairs, context transfer, and human effort. Prefer available allowances when they help, but do not assume they mean zero resource cost. Name a default implementer lane and at least one stronger lane; the accepted plan assigns a lane per task, using the default when it suffices. If the same substantive error survives one focused repair, inspect the cause and consider switching once with a concise handoff. Model/effort restrictions belong here.

## Independence and fallback

Before dispatch, compare the resolved reviewer against every relevant author. The optional Claude role files use `model: inherit`; that is a convenience default, not proof of independence. Explicitly select a non-author reviewer when inheritance would reuse an author model. Account/environment overrides and silent provider substitutions must be checked from actual session metadata.

Keep all actual author ids when an orchestrator or fallback makes changes. A model served through a different provider remains the same model for this rule. Reserve a reviewer before selecting fallback implementers; do not turn an already-used reviewer into an author during the same review cycle.

Use one bounded real call first. Diagnose a failed call before choosing a fallback; a timeout does not prove exhausted credit. Preserve rejected output and any valid unresolved findings. Never automatically repeat implementation after partial edits: inspect and resume the actual worktree. If no independent route is available, leave the review pending/draft and report the limitation.

Keep credentials and private account configuration outside this file. Never stamp a preferred identity over the actual fallback. Maintain private measurements using the delivery guide's improvement loop; revise these preferences when comparable results justify it.
