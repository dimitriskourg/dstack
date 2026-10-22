# Recipes and pitfalls

Prompts worth copying, then the mistakes everyone makes once. Swap in your own paths and finish conditions. The recipes are deliberately informal. That's how they get typed in practice, and the skills read intent fine.

## Understand an unfamiliar subsystem

```text
use /how first to understand how this initialization works. then use /why to figure out why it broke recently.
```

Mechanics first, history second. Each skill's report tells you which sources it searched, so you know what the answer is grounded in.

## Restate a noisy report before touching code

```text
/in-your-own-words <long or messy ask>
```

```text
/sharpen <your task>
```

```text
/dstack-mode read this thread. restate the underlying issue in your own words, in plain english. don't change any code yet.
```

A misreading shows up in the restatement, where it costs one message to correct. Keep your own theory to yourself until the agent has stated its own.

## Prototype before you pick

```text
/dstack-mode prototype a few options for the settings layout. put them behind a switcher and send me screenshots of each.
```

You pick from things that run, not from descriptions. The agent answers its own layout and timing questions along the way.

## Get a second opinion on a design

```text
ask /arena for a second opinion on this thread and our approach
```

Your current design becomes one candidate among several, and the synthesis tells you whether the panel found something better or confirmed what you had. It costs little next to a design that is expensive to reverse.

## Check independent slices in parallel

```text
/swarm check every package under packages/ against its check.sh. one worker per package. one report.
```

Each worker owns one package. The parent waits for every slice and returns one `PASS`, `ISSUES`, or `BLOCKED` report instead of raw worker dumps.

## Review a branch skeptically

```text
/interrogate the whole branch, but skeptically. don't change anything yet. no nitpicks unless it's an actual bug or regression in behavior.
```

The qualifiers do real work. "don't change anything yet" keeps it read-only, and the nitpick rule pre-filters the noise so `Act on` findings are worth your time.

## Fix a bug through a failing test

```text
/dstack-mode repro the duplicate write first. if there's a cheap test path, /tdd it. then fix and rerun.
```

"if there's a cheap test path" matters. Forcing a test through brittle mocks proves less than running the real command, and the playbook is allowed to say so.

## Repro and fix a report with proof

```text
/dstack-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof.
```

"if it repros on main" lets the run stop early when the bug is already gone. The video lets you check the fix before you read the diff.

## Formally verify a property tests rarely reach

```text
/create-formal-verification-skill
```

The generator picks the tool from the question, proves one property, and leaves a project-local skill the next agent can rerun on every relevant change. After merges or refactors in that code, run `/maintain-formal-verification-skill`. It updates the check from the code and says whether a failure is drift or a bug.

## Show the PM what the user sees

```text
/statechart what the user sees when they edit a note offline
```

[`/statechart`](../../../statechart/SKILL.md) draws a Mermaid chart from a TLA+ model, marks each state works, still wrong, or fixed, and draws each bug as a numbered path. It also turns an agreed chart into a TLA+ skeleton, or audits the code against an existing spec. It needs Java 11 or later and `TLA2TOOLS` set to a `tla2tools.jar`.

## Stop correcting the same mistake

```text
/correct agents keep adding new config flags without registering them in the schema
```

The fix lands in the repo as architecture, a type, a lint, or a test, so the next agent can't make the mistake.

## Ask how without starting the work

```text
/dstack-help how do i get dstack-mode to stay on every turn?
```

You get an answer, a prompt to send, and a link to the source. Nothing runs until you send that prompt.

## Keep a run honest while you're away

```text
im going to bed, keep going while this active session can supervise the work, until every fixture passes. do not stop. keep a decision log i can audit in the morning.
```

The [mode skill](../../../dstack-mode/SKILL.md#mode-lifetime) defines the active-session boundary. The short form works once the task and finish condition are already in the conversation.

## Redirect a drifting run

Steering prompts are one line:

```text
i said the goal is to repro. i did not ask for a fix yet.
```

```text
apply prove it works. show me the real output, not the build log.
```

```text
/unslop that, no emdashes
```

You rarely need more words. You need the right name, and [the principles page](./08-principles.md) is the vocabulary.

## Get the reply in plain words

```text
/bro
```

That's the whole prompt. [`/bro`](../../../bro/SKILL.md) restates the last message like one human talking to another, no jargon, shorter. Use it when a reply is technically thorough and you still don't know what it said.

## Catch up on a chat you left running

```text
/ketchup
```

[`/ketchup`](../../../ketchup/SKILL.md) tells you in plain words what changed since your last message, then lists each call waiting on you with its pick, evidence, and risk. It changes nothing while it reports.

## The pitfalls

- **Enumerating skills in the prompt.** "use /how then /architect then /arena" reorders steps the playbook already sequences. State the goal and constraints. Name a skill only to override a default.
- **A vague finish condition.** "make it better" gives the agent nothing to check. Give a command or artifact that can pass or fail.
- **Leading with your theory of the cause.** The agent searches wherever you pointed. Ask it to restate the problem first, then share your hunch.
- **Taking the first design.** One attempt locks in the first shape the model thought of. Ask for prototypes or `/architect` and pick from evidence.
- **Polishing an abstract plan.** Adversarial review of a plan with no code behind it invents risks that will never happen. Settle the open questions with prototypes, then review what got built.
- **Parallel agents in one worktree.** They overwrite each other, and nobody can tell which agent changed what. Use read-only slices or independent proposal directories outside the repository, and serialize repository writers.
- **Looping before you trust the loop.** A loop that can't verify its own work only makes unchecked work faster. Get the verification skill working first.
- **Trusting an unvetted number.** A warm cache or a skipped code path can fake a speedup. Apply Explain the Number before the number goes anywhere.
- **Correcting the same mistake by hand.** A correction in chat helps one run. `/correct` fixes the repo so no later run repeats it.
- **Using `/arena` for coverage.** `/arena` repeats one design or code brief, then picks a base and grafts the best parts. `/swarm` partitions slices or declared race arms and aggregates one report.
- **Accepting every review comment.** Bots and humans both file real catches and noise in one list. `/interrogate` sorts findings into act-on and dismissed buckets with reasons, and you can override either way.
- **Using an inherited model or effort.** Dstack requires a concrete model-and-effort pair for every profile. `auto`, `inherit`, and `inherit-parent` are not configuration options. [Setup](./01-setup.md) covers the roles.
- **Reporting success off a green build.** A build proves it compiles. Ask for the real command, flow, stored value, or profile, and expect the evidence in the reply.
- **Writing a `SKILL.md` freehand.** Route it through the [Authoring or modifying a skill playbook](../../../dstack-mode/playbooks/authoring-a-skill.md) so validation and review happen.

That's the guide. If you skipped ahead, go back to [setup](./01-setup.md) and run one real task. The habits stick from use, not from reading.

Back to [Route work through `/dstack-mode`](./02-dstack-mode.md).
