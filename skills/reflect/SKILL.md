---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Spawn reviewers with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, run the affected review serially and disclose the loss of independence. Pick each subagent's configured profile for the job, per the Subagents section of the **dstack-mode** skill.

Invoke when the user says "reflect" or "/reflect". Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## 1. Locate the active transcript

Call the Skill tool with `dstack-config`. Ask for the transcripts directory. Do not search again here. When it has none or the directory is unreadable, skip to the digest fallback below.

```bash
ls -t <transcript-dir>/*.jsonl <transcript-dir>/*/*.jsonl <transcript-dir>/*/subagents/*.jsonl 2>/dev/null | head -10
```

Hosts differ in layout. Flat (`<id>.jsonl`), nested (`<id>/<id>.jsonl`), and subagent transcripts under the parent's directory are all common. Match whatever your host writes.

For each candidate, read the first line and check that its message text contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

## 2. Run three reviewers

Launch three general-purpose subagents in bounded waves that fit the active harness's available child capacity, each on a different configured profile, with full tool access. **Don't use a restricted read-only mode.** Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript). The prompt forbids file writes. The parent applies edits. Every required reviewer runs even when the first wave cannot hold all three. Call the Skill tool with `dstack-config`. Name each reviewer's profile from the table.

| Lens | Model role | Prompt template |
|---|---|---|
| Judgment | `skeptical-reviewer` | `references/judgment-reviewer.md` |
| Tooling | `bug-worker` | `references/tooling-reviewer.md` |
| Divergent | `fast-explorer` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their response body.

## 3. Synthesize

Call the Skill tool with `dstack-config`. Name the `skeptical-reviewer` profile. Spawn one general-purpose subagent on it, with full tool access. It spot-verifies citations through MCP, and a restricted read-only mode strips that on some hosts. Pass `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. It returns an Accepted / Rejected / Backlog list.

## 4. Structural enforcement check

Move any Accepted item that a lint rule, script, metadata flag, or runtime check would enforce more reliably to Backlog. See the **encode-lessons-in-structure** principle skill.

## 5. Apply

Present the synthesizer's full Accepted / Rejected / Backlog output and wait for explicit approval before applying any Accepted edit or filing any Backlog item. The user picks the subset and may redirect routings. Skill changes affect every future agent in the org, and tracker writes mutate external state. Do not perform either automatically.

When approved Backlog items have no configured tracker or the requested write is unavailable, keep them in the in-chat result without blocking approved skill edits.

Follow each approved row's Routing exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): the parent does it directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to your host's skill-authoring skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to the authoring skill and run its description-optimization loop.
- `new skill: <kebab-name>`: hand creation to the authoring skill. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done.

## 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog proposed: `<issue title>` (`<tags>`). State `filed` with the tracker link only when the user approved and the write succeeded. Otherwise state `not filed`.
- Dropped: one line per rejected finding + reason from the synthesizer.
