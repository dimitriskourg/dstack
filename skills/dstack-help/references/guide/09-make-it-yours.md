# Make it yours

dstack-mode is one person's style. The playbooks, routing, and model roles underneath it work just as well with yours. This page covers capturing lessons from a session, fixing the repo so agents stop repeating mistakes, and authoring a focused skill.

Start smaller than you think. You don't need many skills on day one, or even this whole plugin. Prompt plainly, watch where agents fail, and add a skill or a check when the same failure shows up twice.

## Capture a session's lessons with `/reflect`

Right after a task that taught you something, run:

```text
/reflect that took way too long. capture what we learned so the next run doesn't repeat it.
```

[`/reflect`](../../../reflect/SKILL.md) sends the transcript to three parallel reviewers, then a synthesizer sorts the proposals into `Accepted`, `Rejected`, and `Backlog` and waits for your approval before any skill changes. Approve a proposal only if it would change a future decision. One weird session is an anecdote, not a rule.

## Fix the environment with `/correct`

When you correct agents for the same mistake again and again, the fix belongs in the repo, not in your next prompt. Rank the options by how well they hold:

1. Make the mistake impossible with architecture or a better data structure.
2. Block it with types, or with a lint or CI check whose error names the fix.
3. Catch it with a test.
4. Write it down as a doc or agent rule. Nothing fails when an agent skips a rule, so this comes last.

Human review isn't on the list. A reviewer who must catch the same mistake on every PR is the problem this fixes. [`/correct`](../../../correct/SKILL.md) does the work:

```text
/correct agents keep calling the database client directly instead of going through the repository layer
```

It reads recent commits, reverts, review comments, and comments that explain workarounds, then groups the mistakes into classes. A class counts once it has happened twice. It fixes the most frequent classes one commit each, at the highest level that works, and proves each new check fails on a real past mistake. It also keeps a table in the agent instruction file that pairs each rule with what enforces it, so a rule that nothing enforces shows up as a repeat. The reply lists each class with its evidence, the level chosen, and why a higher level didn't work.

Run it with no argument and it finds the classes from history on its own. `/reflect` and `/correct` split the work. `/reflect` improves skills from one session. `/correct` changes the repo so a mistake class can't come back. Pair it with `/architect` when the fix is a new boundary.

## Author a focused skill

When you already know the workflow you want to capture:

```text
/dstack-mode write a skill for verifying database migrations in this repo
```

Writing a skill matches the [Authoring or modifying a skill playbook](../../../dstack-mode/playbooks/authoring-a-skill.md), which uses the active harness’s skill-authoring workflow, validates the frontmatter and links, and presents the local result. Opening a PR is explicit only. Agent-facing prose has a higher bar than human prose, because an unhelpful sentence becomes an instruction some future agent follows. Let the playbook hold that bar rather than writing a `SKILL.md` freehand.

Two special cases have their own generators. A skill that must drive your app and prove behavior is a verification skill, so use [`/create-verification-skill`](../../../create-verification-skill/SKILL.md) and [`/maintain-verification-skill`](../../../maintain-verification-skill/SKILL.md) instead. A skill that checks a property of your code with a model checker, a proof, or another verifier is a formal verification skill, so use [`/create-formal-verification-skill`](../../../create-formal-verification-skill/SKILL.md) and [`/maintain-formal-verification-skill`](../../../maintain-formal-verification-skill/SKILL.md). [Verify and ship](./06-verify-and-ship.md#prove-a-property-with-a-formal-verification-skill) covers both kinds.

## Write docs to a standard with `/technical-writing`

Skills aren't the only prose you ship. For docs, RFCs, readmes, PR descriptions, and commit messages:

```text
/technical-writing review the readme changes
```

[`/technical-writing`](../../../technical-writing/SKILL.md) applies a layered standard. Its goal is prose that a tired engineer understands on the first read. It picks the document's mode first (tutorial, how-to, reference, or explanation), then works sentence by sentence: who does what, one thought per sentence, nothing readable two ways. Use it to review what you or an agent just wrote, or name it up front when you ask for a doc.

**Pitfall:** don't edit a skill mid-task because it's misbehaving. Fix it in its own change and keep the task moving. Publish only when explicitly requested. A skill edit that ships tangled into feature work is invisible to review.

Next: [Recipes and pitfalls](./10-recipes-and-pitfalls.md).
