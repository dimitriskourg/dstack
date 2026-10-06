---
name: dstack-help
description: Guides users through dstack setup, /dstack-mode, and picking the skill, playbook, or principle for a task. Type /dstack-help with a question.
disable-model-invocation: true
---

# dstack help

Answer the user's question about dstack, hand them a prompt they can send, and link the file the answer came from. For a help question, don't start the work. The user asked how, and a dstack run spends real tokens, so let them send the prompt.

A message that asks for work, such as "use dstack to fix this bug", is not a help question. Tell the user to invoke `dstack-mode` explicitly with that task.

This file maps questions to the skills and guide pages that hold the answers. Those files own the details. Read the file you route to before you quote it, and trust it when it disagrees with this map. The links here point into the installed skills, which the user may not be able to open, so give the user the file's public copy: `https://github.com/dimitriskourg/dstack/blob/main/` followed by its path in the repository.

Guide pages live in `references/guide/` and ship with this skill. Read them locally when the answer needs them.

## Find out what they need

Infer the need from the message and the conversation. A named situation, such as "which skill reviews a PR?", goes straight to its section. If the need is still unclear, ask one multiple-choice question with these options, then answer only the section they pick:

- Get set up
- Start a task with `/dstack-mode`
- Pick a skill for a situation
- Fix a run that went wrong
- Make dstack my own

Check the state that changes the answer, and mention it only when it does:

- No `~/.dstack/config.json`, or no entry for the active harness or repository, means `setup-dstack` has not run here. Config-dependent skills require it before real work.
- No `verify-*` skill or other app harness in the project means agents have no scripted way to drive the app. Mention `/create-verification-skill` when the question is about proving a change works.

When setup is missing and it matters, ask whether the user wants to pick a concrete model and effort for each profile now. It matters when the user is new, the question is about setup or cost, or the answer depends on which models run. Ask at most once per chat. If the need is also unclear, ask both questions together. Offer two choices:

- Now: give them `/setup-dstack` to type, and answer their question too.
- Later: answer their question, and add one line saying config-dependent work needs `/setup-dstack` before it starts.

## Get set up

1. Preview the install with `python3 install.py --dry-run`, then install. [Guide page 1](references/guide/01-setup.md) has the exact command for each harness.
2. Run [`/setup-dstack`](../setup-dstack/SKILL.md). It confirms a concrete model and effort for each of the four profiles (`fast-explorer`, `feature-worker`, `bug-worker`, `skeptical-reviewer`) and records this repository's transcript directory in `~/.dstack/config.json`.
3. Start a real task with `/dstack-mode`, a goal, and a check that can pass or fail.

Installing changes nothing until the user invokes a skill. Offer to word their first prompt with them, per [`references/prompting.md`](references/prompting.md).

If cost is the worry, say where the tokens go and how to spend fewer. dstack spends extra tokens on subagents and review panels. Rerun `setup-dstack` and assign cheaper models or lower efforts to the profiles. Save `/dstack-mode` for work that needs rigor.

## Start a task with `/dstack-mode`

`/dstack-mode` matches the task to a playbook, copies the playbook's steps into the todo list, and runs the other skills as the steps need them. A step it skips stays in the list as `skip: <reason>`. A good prompt states the goal and how to tell it's done. It doesn't list skills, because a hand-written sequence tends to drop or reorder steps the playbook would keep. Read [`references/prompting.md`](references/prompting.md) before you help word one. [Guide page 2](references/guide/02-dstack-mode.md) has examples.

The mode lasts as long as the host keeps it in context. Read its Mode lifetime section before you answer how long it stays on. In a fresh session, after a compaction, or on a new task, start with `/dstack-mode` again. Mid-chat, "new task" makes the mode match a fresh playbook.

## Pick a skill

The default answer is `/dstack-mode`, which runs most of the others when its steps need them. Name a skill directly when the user wants more or less of something than the playbook gives. Read the skill before you recommend it, and give one example prompt.

| The user wants to | Skill |
|---|---|
| Do any non-trivial task with rigor | [`/dstack-mode`](../dstack-mode/SKILL.md) |
| Know how code works now, or where new code should live | [`/how`](../how/SKILL.md) |
| Know why code is shaped this way, or where a number came from | [`/why`](../why/SKILL.md) |
| Understand a change or subsystem, explained plainly | [`/teach`](../teach/SKILL.md) |
| Catch up on their own recent work on a topic | [`/recall`](../recall/SKILL.md) |
| Know what a small diff could break outside itself | [`/blast-radius`](../blast-radius/SKILL.md) |
| Settle types and module shape before code that crosses a function boundary | [`/architect`](../architect/SKILL.md) |
| Get several attempts at one brief, merged into the best one | [`/arena`](../arena/SKILL.md) |
| Run parallel checks over slices, or race workers, using local subagents | [`/swarm`](../swarm/SKILL.md) |
| Have different models review a diff and try to break it | [`/interrogate`](../interrogate/SKILL.md) |
| Fix a bug test-first when a cheap local test exists | [`/tdd`](../tdd/SKILL.md) |
| Apply TypeScript rules to `.ts` or `.tsx` work | [`/typescript-best-practices`](../typescript-best-practices/SKILL.md) |
| Strip comments before review, using a reviewer that didn't write them | [`/no-comments`](../no-comments/SKILL.md) |
| Clean AI tells out of prose | [`/unslop`](../unslop/SKILL.md) |
| Write docs, an RFC, a README, a PR description, or a commit message to a standard | [`/technical-writing`](../technical-writing/SKILL.md) |
| Hear the last reply again in plain words | [`/bro`](../bro/SKILL.md) |
| Give agents a scripted way to drive the app and prove behavior | [`/create-verification-skill`](../create-verification-skill/SKILL.md) |
| Bring a verification skill and its feature map back in line with the app | [`/maintain-verification-skill`](../maintain-verification-skill/SKILL.md) |
| Vet a performance number before reporting or acting on it | [`/benchmark-checklist`](../benchmark-checklist/SKILL.md) |
| Run a large or cross-cutting change, or one to review after stepping away | [`/figure-it-out`](../figure-it-out/SKILL.md) |
| Keep a decision log during a run, and review it afterward | [`/show-me-your-work`](../show-me-your-work/SKILL.md) |
| Pick a concrete model and effort for each profile | [`/setup-dstack`](../setup-dstack/SKILL.md) |
| Turn their own working habits into a personal mode skill | [`/automate-me`](../automate-me/SKILL.md) |
| Turn what a finished task taught into skill edits | [`/reflect`](../reflect/SKILL.md) |
| Stop agents from repeating the same mistakes in this repo | [`/correct`](../correct/SKILL.md) |
| Find their way around dstack | `/dstack-help` |

If a skill directory next to this one is missing from the table, read its frontmatter and route by its description. The `principle-*` directories are covered under principles below.

Close calls:

- `/how` explains what the code does. `/why` explains the reasons. `/teach` runs one or both and explains the result plainly.
- `/arena` gives every worker the same brief and merges the best parts. `/swarm` splits work into slices or a race and returns one report.
- `/architect` implements right after it settles the design. Add "with checkpoint" to review the design before it writes code.
- `/interrogate` reviews the diff. `/blast-radius` looks for breakage outside the diff and proves the one fact that makes the change safe.
- `/recall` rebuilds context across recent chats. Resuming one specific chat or branch is the Session pickup playbook.
- `/figure-it-out` designs one rigorous run.

Bundled alongside the retained skills:

- `/deslop`, `control-cli`, and `control-ui` ship with dstack.
- Autonomous runs, autopilot, shipping, and worktree management are excluded. See [Supported scope](references/guide/06-supported-scope.md).

## Playbooks and principles

Playbooks are step lists inside `/dstack-mode`, not skills, so they have no slash command. Inside `/dstack-mode`, describing the task picks one, and these phrases name one directly:

- "babysit this pr" or "check on pr 123" runs Babysit. It drives the PR to merge-ready and stops there. dstack stops at merge-ready and leaves merging to the team.
- "take over this branch" runs Session pickup.
- "pause safely" runs Pause safely.
- "run the eval playbook" runs Eval.

Without `/dstack-mode`, a phrase such as "babysit this pr" can start a host built-in for the same job instead. The Playbooks section of [`dstack-mode`](../dstack-mode/SKILL.md) lists every playbook and when it applies. [Guide page 6](references/guide/06-verify-and-ship.md) covers opening a request and babysitting it to merge-ready.

dstack has no standalone planning skill. For work that spans phases or dependent PRs, asking `/dstack-mode` for a plan runs the [Multi-phase plan playbook](../dstack-mode/playbooks/multi-phase-plan.md), which writes the plan and doesn't implement it. For a design question, the Prototype playbook or `/architect` settles it in code first.

Principles are one-rule skills that `/dstack-mode` reads and cites in its replies. The user rarely invokes one. They steer with the names instead, as in "apply prove it works. show me the real output." Typing `/principle-<name>` still loads one on demand. [Guide page 8](references/guide/08-principles.md) lists them.

## Fix a run that went wrong

| Symptom | Fix |
|---|---|
| A skill stopped and asked for `setup-dstack` | The config file, the harness entry, or this repository's entry is missing. Run `setup-dstack` in this repository. |
| The mode stopped applying after a few turns | The host dropped it from context. Start each task with `/dstack-mode`. |
| A question got treated as the next step of the last task | Say "new task", or say the turn doesn't need the mode. |
| A new profile choice had no effect | Rerun `setup-dstack` and check that it reports the pair as applied. Start a new chat if the host reads worker definitions only at startup. |
| Runs cost more than expected | See the cost paragraph under Get set up. |
| A skill didn't load on its own | Most dstack skills load only when the user types them or when `/dstack-mode` runs them, and it doesn't run every skill. |
| Parallel agents overwrote each other | dstack serializes repository writers. Give parallel workers read-only slices or their own output directories outside the repository. |
| The reply claims success from a green build | Ask for the real command, flow, stored value, or profile. That's the prove-it-works principle. |

For a run that drifts, [`references/prompting.md`](references/prompting.md) has one-line steers. [Guide page 10](references/guide/10-recipes-and-pitfalls.md) has more pitfalls and the recipes worth copying.

## Make dstack my own

- [`/automate-me`](../automate-me/SKILL.md) drafts a personal mode skill from the user's own history, to use alongside `/dstack-mode`.
- [`/reflect`](../reflect/SKILL.md) after a session turns its lessons into skill edits the user approves.
- `/dstack-mode write a skill for <workflow>` runs the authoring playbook. The eval playbook tests a skill change blind.
- Fix a misbehaving skill in its own change, not inside the feature work where it went wrong.

[Guide page 9](references/guide/09-make-it-yours.md) covers each of these.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
