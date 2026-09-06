# AI Development Workflow

I'm Abi, a senior web developer with more than eight years of professional experience. I started well before coding assistants existed, and I have been working through the shift into the AI era one project at a time. That history shapes everything here. Writing the plan down, keeping changes small enough to review, running the checks before trusting a result, and asking for a second pair of eyes on anything risky were how teams shipped safely long before a model could write code. This workflow is my attempt to keep those habits while letting AI do more of the work.

It grew out of real projects rather than a blank page. I use AI for planning, implementation, and cross-checking, and I keep the responsibility for the decisions and the outcome. If you have been doing this for a long time too, I hope it feels familiar. If you are newer, I hope it gives you a gentle structure to lean on while you form your own judgment.

I don't think this is perfect or right for everyone. It is a practical starting point that works for me, and it should keep changing as the tools, the projects, and the evidence change.

## Start here

Point your coding AI at [INTEGRATE.md](INTEGRATE.md), with access to the project you want to update. You can copy this prompt:

```text
Integrate this AI development workflow into my existing project.
Workflow source: <GitHub repository URL or local checkout>
Target project: <local repository path>

Read INTEGRATE.md in the workflow source first. Preserve my project's existing
conventions and choose the smallest useful integration. Use the generic model
preferences unless I select Abi's example. Do not install optional vendor
harnesses, plugins, or tooling unless they are needed and within my request.
Make the changes, run the applicable checks, and report what was integrated
and anything that remains unverified.
```

If you only need a quick edit, use your existing repo instructions. You do not need to install this bundle first.

## The workflow

| Change | Typical path |
| ------ | ------------ |
| Quick, obvious, reversible edit | Update → relevant check → inspect diff → PR |
| Bounded fix or enhancement | Brief plan → implement → targeted checks → independent review when warranted → PR |
| Substantial feature or consequential risk | Spec/plan → independent spec review → implement → tests → independent code review → focused verification if needed → PR |

Risk matters more than line count. A one-line change to authorization can need more care than a large cosmetic change. Quick tasks do not need formal specs, agent teams, or a retrospective.

For substantial work, the workflow records which revision was tested and reviewed. Code review uses a different model from every implementation author; spec review uses a different model from every plan author. A different provider serving the same model does not count as independent. This is a useful cross-check, not a guarantee against shared blind spots.

The full procedure is in [delivery.md](delivery.md). [workflow.md](workflow.md) maps the setup prompts and installed files.

## Choose your models and plugins

- [model-preferences.md](model-preferences.md): editable generic starting point. Choose models you have access to and can verify.
- [model-preferences.abi.md](model-preferences.abi.md): my example, including Grok for spec review, Composer as the default implementation lane with a stronger lane the plan can choose per task, and Codex for code review, with the reasons and fallback rules.

I also want to be open about the plugins in my own setup: superpowers, context7, and ponytail, all for Claude Code. My profile lists what each contributes. The implementer brief preloads two superpowers skills when that plugin is present and works unchanged without it. None of the three is required by the workflow.

My choices are preferences, not benchmark rankings or requirements. Model ids, account limits, and availability need checking when used. Bootstrap puts your selected settings in your project's `docs/ai/vendors.md`; shared workflow instructions use roles instead of hardcoded model choices.

## What to install

| File | Purpose |
| ---- | ------- |
| [INTEGRATE.md](INTEGRATE.md) | Entry point for an AI adapting this to an existing repo |
| [bootstrap.md](bootstrap.md) | Small repo guide set and evidence checker |
| [delivery.md](delivery.md) | Daily routing, substantial work, and improvement loop |
| [harness.md](harness.md) | Optional automation for repeated external reviews |
| [tooling.md](tooling.md) | Optional audit of existing checks and justified tooling gaps |
| [agents/](agents/) | Optional planner, implementation worker, and independent reviewer briefs |
| [ai-state-check.py](ai-state-check.py) | Local state and revision-bound evidence checks |
| [ai-review-run.py](ai-review-run.py) | Optional bounded review subprocess runner |

No plugin, account subscription, or particular provider is required by the workflow itself. The evidence checker needs Git and Python 3.8+. The optional process runner needs POSIX process groups; otherwise use native review sessions. Claude agent files are optional host adapters. Other hosts can use the same role briefs.

Bootstrap adapts to existing guidance and keeps one source of truth. The checker accepts either `AGENTS.md` or `CLAUDE.md`; create host adapters only when they are used.

## Learn across projects

Each substantial feature gets a short retrospective in its existing PR/task record. Escaped defects enter the same record when normal usage or incident work reveals them. Useful lessons and active landmines stay with the repo and feed the next plan.

For cross-repo analysis, copy the blank [run ledger](templates/workflow-runs.csv) and [improvement log](templates/workflow-improvements.md) into a private workspace or this checkout's ignored `.local/` directory. Keep real project metrics, private PR links, and review evidence out of the public templates.

Classify problems by their cause: repository, stack/platform, operator/vendor, or shared workflow. Local constraints remain local. Shared changes need evidence, an explicit trial, and an adopt/revert decision. The records include workflow revisions so results from different installed copies remain distinguishable. There is no background monitoring agent or reporting requirement for quick edits.

## Check the bundle

From this folder:

```sh
python3 ai-state-check-test.py
python3 ai-review-run-test.py
```

Use an installed Python 3 interpreter (`python3`, `python`, or `py -3` as appropriate). Gate tests use disposable Git repositories. Runner tests use subprocess stubs and are skipped on unsupported platforms. Neither suite calls a model or requires API credentials.

These checks verify workflow mechanics. They do not establish model quality, real-world cost savings, or production reliability. The local gate is not a sandbox, cannot authenticate a reviewer's claimed identity, and does not replace required CI or human decisions about material risk.

## Contributing

Useful contributions include reproducible checker bugs, contradictory instructions, or evidence that a step costs more than it contributes. Explain whether the cause is repo-specific or shared, show the smallest practical fix, and run affected checks. Do not submit credentials, private project details, or raw review logs.

I expect this workflow to keep evolving. Adapt it, keep what helps, and use results from your own projects to decide what to change.

## License

[MIT](LICENSE).
