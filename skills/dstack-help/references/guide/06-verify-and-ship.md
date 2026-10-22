# Verify the result and open a PR

"It compiles" is not evidence. The [Prove It Works principle](../../../principle-prove-it-works/SKILL.md) makes the agent check the real artifact before it reports success, and your job is to make "the real artifact" checkable. This page covers stating a finish condition, vetting a measured number, generating a verification skill for your app, formally verifying a property tests rarely reach, opening the PR, and driving it to merge-ready.

Verification is the slowest step in most agent work, because it's the step that usually waits on a human. Make the agent able to do it, and you stop being the bottleneck. Skip it, and running more agents only gets you more unchecked work to review.

## State the finish condition up front

Put what done means in the first prompt, in whatever words fit:

```text
/dstack-mode add json output to this command. text output stays byte-identical, the json parses, both run against the sample project. show me the evidence.
```

Now the agent has three checks it can run, not a mood to satisfy. When the reply comes back, it should carry the exact commands and outputs. If a check couldn't run, a good reply says "inconclusive". A confident reply without evidence is a warning sign.

Match the check to the change:

- A CLI change runs the real command.
- A UI change walks the changed flow in the running app.
- A parser or migration replays a saved input.
- A perf change compares before and after profiles.
- A storage change reads back the written value.

Ask for the proof as an artifact you can inspect yourself: the failing test and then the passing one, a before-and-after video, the trace, the screenshot. If the fix already merged, ask for the same check again on main. An artifact beats a plausible explanation, because you can challenge it without replaying the whole run.

For a small diff you don't fully trust, [`/blast-radius`](../../../blast-radius/SKILL.md) finds what it could break elsewhere. It finds the one fact that makes the change safe and proves that fact by running code, not by arguing for it.

## Vet a measured number

A before-and-after number is the easiest evidence to get wrong by accident. A warm cache, a debug build on one side, or work that never ran inside the timed region can each produce a convincing speedup. Before you report or act on a number, apply the [Explain the Number principle](../../../principle-explain-the-number/SKILL.md): name what limits it, rule out that it measured something else, and keep the run count, range, and limiter with the number.

## Create a project verification skill

The UI bullet above hides a real requirement. The agent needs a scripted way to drive your app. If your project has one, great. If not, run:

```text
/create-verification-skill
```

[`/create-verification-skill`](../../../create-verification-skill/SKILL.md) interviews the repository, not you. It works out what a user touches, how the app launches locally, what can drive it (an existing harness first, otherwise browser and CDP, a PTY, or plain HTTP), what evidence proves behavior, and whether two instances can run side by side. It asks you only what the code can't answer.

It writes a project-local `verify-<app>` skill in the active harness’s discoverable skill directory, agent-facing instructions with exact Launch, Doctor, Drive, Evidence, and Cleanup sections, a Helpers section for any script it ships, plus a feature map under `features/` that indexes what the app does and what result proves each feature works. The skill ships a [worked feature-map example](../../../create-verification-skill/) with a README index and one file per feature using the four required H2s. Before handing it over, the generator proves the skill once end to end: launch, doctor check, drive one feature, capture evidence, clean up, then confirm the evidence survived the cleanup. If that proof fails, don't use the output.

From then on, "verify it in the app" is a step any agent can execute, in this repo, with no setup conversation. Name it in the prompt when you want the proof in a specific form:

```text
/dstack-mode build the bulk-archive action. use /verify-<app> to verify your changes and show me a video and screenshots as proof.
```

```text
/dstack-mode repro this with /verify-<app>. if it repros on main, fix it and show me a video as proof.
```

Once the verify skill works, a [`/swarm`](../../../swarm/SKILL.md) can split a full pass by feature-map entry and aggregate the results. A swarm of verifiers also confirms a perf win over a big enough sample, or fuzzes the app for regressions before a PR ships.

Treat the verification skill as infrastructure, not a one-off. Commit it, so every person and every agent on the team drives the app the same way. Then [build the lever](../../../principle-build-the-lever/SKILL.md). When agents keep writing throwaway scripts to click through the app, ask for a small control CLI that the skill calls instead. Agents spend fewer tokens, and every run becomes repeatable. A CLI that agents use well has these traits:

- A few composable commands, each doing real work, rather than many thin ones.
- A `--dry-run` option on anything destructive.
- Subcommands that reveal features gradually instead of all at once.
- Error messages that say what to do instead.
- Rich `--help` text.
- Machine-readable output, such as JSON.

While you're there, make the dev setup repeatable too: seeded data, test users, and one command that brings the environment up the same way every time.

## Keep the verification skill honest

Apps change, and feature maps go out of date. Run this when the app changes or the feature map may have drifted:

```text
/maintain-verification-skill
```

[`/maintain-verification-skill`](../../../maintain-verification-skill/SKILL.md) audits the generated skill: one read-only source reader per feature in parallel, then one live pass that drives every mapped feature. It ends in exactly one of three outcomes. `clean` means full coverage and nothing to ship. `changed` means proven local corrections, confined to the verification skill's own directory. Publication is a separate explicit request. `blocked` names the blocker. It never edits product code. If the live pass catches a product regression, it reports the regression instead of hiding it with a doc edit.

## Prove a property with a formal verification skill

A verification skill proves the paths you drive. Some bugs live on paths nobody drives: two retries that overlap, a lock that expires mid-write, a state change that arrives out of order. Tests rarely reach those cases. For code where such a bug is costly, run:

```text
/create-formal-verification-skill
```

[`/create-formal-verification-skill`](../../../create-formal-verification-skill/SKILL.md) picks the target from the code: a promise the code makes, where a break harms users and tests rarely reach the case that breaks it. It picks the strongest target, not the easiest to verify. Name an area or a bug to start there instead:

```text
/create-formal-verification-skill the job lease and retry logic. a job must never run twice at once.
```

The question picks the tool. Whether events can happen in a bad order suits a model checker over a small model of the design, and TLA+ is the default for that in any language. Whether the code behaves for every input suits a verifier that runs on the code. If no verifier runs on your language, the agent says so and tests the real code with generated inputs, not a hand-written model of the function. A property that must hold at every size can need a proof. The agent tells you which tool it chose and why.

It verifies one property and shows that property failing on a broken variant of the code, because a check you've never seen fail proves nothing. When the current code already breaks the property, you get the counterexample as a short sequence of steps in your code's terms. The property stays as stated, so the finding stays a finding. Product code doesn't change unless you ask.

It writes a project-local skill that tells the next agent whether a change touches the verified code, how to run the check with one command, and how to tell a real bug from a modeling error. Before handing it over, the generator follows that skill once on a scratch change that breaks the property, and the check must catch it. The handoff says what was verified, with which tool and bounds, what the check found, and what it doesn't cover. A pass covers the model or the bound, not the whole system.

The skill also records which code each check covers and the commit where the check last matched it. Merges and refactors that skip the skill can leave the check passing on a description of code that's gone. After them, run [`/maintain-formal-verification-skill`](../../../maintain-formal-verification-skill/SKILL.md). It updates the verification from the code, reruns it, shows that each updated check can still fail, and tells you whether each failure is drift in the verification or a bug in the code.

## Show the behavior as a statechart

A counterexample in model terms convinces you. The PM or designer who owns the behavior needs to see it in their terms. Run:

```text
/statechart what the user sees when they edit a note offline
```

[`/statechart`](../../../statechart/SKILL.md) draws a Mermaid statechart of what the user sees, generated from a TLA+ model, so the picture and the checked model can't drift apart. The reader's rules ("you never see Synced while you're offline") become invariants. Each bug TLC finds is a numbered path in the reader's words, and each state is marked works, still wrong, or fixed by your open PR. Before the hand-off, the agent reproduces each bug path in the real code, so a modeling error doesn't reach the reader as a bug.

It also runs the other way. Sketch the behavior as a chart, agree on it with the reader, and the skill writes a TLA+ skeleton from it. TLC checks the agreed chart's rules before any code exists. As guards from the real code go into the spec, each place the code departs from the chart shows up as a difference for the reader to decide.

When the code already has a TLA+ spec, the skill can audit the code against it. The agent models what the code does and checks that model next to the unchanged spec. The chart marks the steps where the two differ, and each rule either one breaks is a numbered path.

TLC needs Java 11 or later and `TLA2TOOLS` set to a `tla2tools.jar` from a TLA+ release. Set `JAVA` if `java` is not on PATH.

## Open the PR

```text
/dstack-mode open the pr. small ordered commits, evidence in the description.
```

The [Opening a PR playbook](../../../dstack-mode/playbooks/opening-a-pr.md) preserves unrelated work in the current checkout, rebases the work into small ordered commits, cleans the diff, unslops the prose, and returns the PR link. Narrow PRs keep changes reviewable. Dependent follow-ups use ordinary branches and the forge’s base-branch support.

## Drive the PR to merge-ready with Babysit

An open PR starts collecting blockers immediately. Checks fail, reviewers comment, trunk moves. Hand that churn to the [Babysit playbook](../../../dstack-mode/playbooks/babysit.md):

```text
/dstack-mode babysit this pr. get it green.
```

Babysit polls through the authenticated forge CLI (`gh` or `glab`) and takes blockers in order: conflicts, then review threads, then CI. Every known fix batches into one push, so the checks restart once instead of after every fix. The comment triage is skeptical, because humans and bots file real catches and noise in the same list. A real finding gets a fix, and noise gets dismissed with the disproof posted on the thread. When all you want is status, ask smaller and Babysit answers without starting the loop:

```text
/dstack-mode check on pr 123. anything outstanding?
```

Babysit stops at merge-ready. It never merges, even with everything green, because merging is a different decision.

## Leave merging to the team

Dstack stops at merge-ready. It does not ship the upstream Shipping playbook or automate merging. A request in the forge's merge queue or merge train with no remaining blockers counts as merge-ready.

Next: [Steer with principle names](./08-principles.md).
