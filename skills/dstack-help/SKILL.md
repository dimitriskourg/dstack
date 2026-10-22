---
name: dstack-help
description: Short cheat sheet of the locked dstack keep-set. Type /dstack-help with a question about setup, /dstack-mode, a skill, playbook, or principle.
disable-model-invocation: true
---

# dstack help

Answer the question. Hand one prompt the user can send. Link the file the answer came from. Do not start the work.

A message that asks for work, such as "use dstack to fix this bug", is not a help question. Tell the user to invoke `dstack-mode` explicitly with that task.

Give the user the file's public copy: `https://github.com/dimitriskourg/dstack/blob/main/` followed by its path in the repository. Guide pages live in `references/guide/` and ship with this skill.

## Locked keep-set

56 skills, 24 principles, ten playbooks. What is out of this pack lives in [Supported scope](references/guide/06-supported-scope.md), not here.

### Setup and routing

| The user wants to | Skill |
|---|---|
| Install, pick four concrete model-and-effort profiles, record this repository's transcripts | [`/setup-dstack`](../setup-dstack/SKILL.md) |
| Run any non-trivial task with rigor | [`/dstack-mode`](../dstack-mode/SKILL.md) |
| Find their way around this pack | `/dstack-help` |
| Resolve a profile's spawn values or the transcripts directory (called by other skills) | [`dstack-config`](../dstack-config/SKILL.md) |

No `~/.dstack/config.json`, or no entry for the active harness or repository, means `setup-dstack` has not run here. Config-dependent skills read it only through `dstack-config`. On failure it stops and tells the user to invoke `setup-dstack` explicitly.

Preview with `python3 install.py --dry-run`, then install. [Guide page 1](references/guide/01-setup.md) has the command for each harness. Then `/setup-dstack`, then a real task with `/dstack-mode`, a goal, and a check that can pass or fail.

`/dstack-mode` runs in the chat that receives it. That chat matches one playbook, copies its steps into the todo list, and runs the other skills as the steps need them. Do not spawn a subagent to run the playbook itself. [Guide page 2](references/guide/02-dstack-mode.md) has examples. [`references/prompting.md`](references/prompting.md) has how to word a prompt.

### Skills

Name a skill directly when the user wants more or less than the playbook. Read it before you recommend it.

| The user wants to | Skill |
|---|---|
| Check that the agent understood the goal and the problem | [`/in-your-own-words`](../in-your-own-words/SKILL.md) |
| Get a prompt rewritten deeper before sending it, without doing the task | [`/sharpen`](../sharpen/SKILL.md) |
| Know how code works now | [`/how`](../how/SKILL.md) |
| Know why code is shaped this way | [`/why`](../why/SKILL.md) |
| Understand a change, explained plainly | [`/teach`](../teach/SKILL.md) |
| Catch up on recent work across chats | [`/recall`](../recall/SKILL.md) |
| Catch up on this chat since the last user message | [`/ketchup`](../ketchup/SKILL.md) |
| Know what a small diff could break outside itself | [`/blast-radius`](../blast-radius/SKILL.md) |
| Settle types and module shape before code | [`/architect`](../architect/SKILL.md) |
| Get several attempts at one brief | [`/arena`](../arena/SKILL.md) |
| Run parallel checks over slices, or race workers | [`/swarm`](../swarm/SKILL.md) |
| Have different models review a diff | [`/interrogate`](../interrogate/SKILL.md) |
| Fix a bug test-first | [`/tdd`](../tdd/SKILL.md) |
| Apply TypeScript rules | [`/typescript-best-practices`](../typescript-best-practices/SKILL.md) |
| Strip comments before review | [`/no-comments`](../no-comments/SKILL.md) |
| Clean AI tells out of prose | [`/unslop`](../unslop/SKILL.md) |
| Write docs, an RFC, a README, a PR, or a commit | [`/technical-writing`](../technical-writing/SKILL.md) |
| Hear the last reply in plain words | [`/bro`](../bro/SKILL.md) |
| Give agents a scripted way to drive the app | [`/create-verification-skill`](../create-verification-skill/SKILL.md) |
| Bring a verification skill back in line | [`/maintain-verification-skill`](../maintain-verification-skill/SKILL.md) |
| Formally verify a race or invariant | [`/create-formal-verification-skill`](../create-formal-verification-skill/SKILL.md) |
| Bring a formal verification back in line | [`/maintain-formal-verification-skill`](../maintain-formal-verification-skill/SKILL.md) |
| Show what the user sees as a chart checked by a model | [`/statechart`](../statechart/SKILL.md) |
| Turn a finished task into skill edits | [`/reflect`](../reflect/SKILL.md) |
| Stop agents repeating the same mistakes | [`/correct`](../correct/SKILL.md) |

Bundled so the workflow is complete: `/deslop`, `/control-ui`, `/comment-sicko`.

Close calls: `/how` vs `/why` vs `/teach`; `/arena` vs `/swarm`; `/recall` vs `/ketchup` (session pickup resumes one chat or branch); `/architect` implements after it settles, add "with checkpoint" to review first.

`/statechart` needs Java 11 or later and `TLA2TOOLS` set to a `tla2tools.jar`.

### Playbooks

Playbooks are step lists inside `/dstack-mode`, not slash commands. The Playbooks section of [`dstack-mode`](../dstack-mode/SKILL.md) lists when each applies:

- Investigation, Bug fix, Feature, Refactoring, Prototype
- Authoring or modifying a skill
- Babysit (explicit; stops at merge-ready)
- Session pickup, Pause safely
- Opening a PR (explicit only; never an automatic final step)

[Guide page 6](references/guide/06-verify-and-ship.md) covers opening a request and babysitting it to merge-ready.

### Principles

24 one-rule skills. `/dstack-mode` reads and cites them. Steer with the names. Typing `/principle-<name>` still loads one. [Guide page 8](references/guide/08-principles.md) lists them.

## Fix a run

| Symptom | Fix |
|---|---|
| A skill stopped and asked for `setup-dstack` | Run `setup-dstack` in this repository. |
| The mode stopped applying | Start each task with `/dstack-mode`. |
| A new profile choice had no effect | Rerun `setup-dstack`, then check that the profile holds exactly what the host's spawn call takes. |
| Parallel agents overwrote each other | Repository writers serialize. Give parallel workers read-only slices or output outside the repository. |
| Success claimed from a green build | Ask for the real command, flow, stored value, or profile. |

[Guide page 10](references/guide/10-recipes-and-pitfalls.md) has more pitfalls. [Guide page 9](references/guide/09-make-it-yours.md) covers `/reflect`, authoring a skill, and `/correct`.

## Reply

Lead with the answer. Give at most one example prompt in a code block, adapted from [`references/recipes.md`](references/recipes.md) when one fits, then the link to that file. Keep it short unless the user asked for the whole map.
