---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

The parent finds its own transcript file before fanning out. Use only your host's transcript directory for the active workspace. Do not glob across the host's whole transcript store. That crosses workspace boundaries and reads private chats from unrelated projects. When your host exposes no readable transcript, skip to the digest fallback below.

```bash
ls -t <transcript-dir>/*.jsonl <transcript-dir>/*/*.jsonl <transcript-dir>/*/subagents/*.jsonl 2>/dev/null | head -10
```

Hosts differ in layout. Flat (`<id>.jsonl`), nested (`<id>/<id>.jsonl`), and subagent transcripts under the parent's directory are all common. Match whatever your host writes.

For each candidate, read the first line and check that its message text contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Spawn three reviewers in parallel

Spawn three general-purpose subagents at once, each on its own model binding, with full tool access. **Don't use a restricted read-only mode.** Reviewers need MCP access for context lookups (tickets, chat threads, observability traces referenced in the transcript), and where a host strips MCP access in that mode it disables those lookups entirely. The prompt forbids file writes; the parent applies edits.

| Lens | Model role | Prompt template |
|---|---|---|
| Judgment | `deep-judgment` | `references/judgment-reviewer.md` |
| Tooling | `skeptical-reviewer` | `references/tooling-reviewer.md` |
| Divergent | `deep-judgment`, on a binding distinct from Judgment where your profile provides one | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their response body.

### 3. Synthesize

One general-purpose subagent on your configured `deep-judgment` role, with full tool access. The synthesizer's quality check includes spot-verifying citations, which can require MCP access; a restricted read-only mode strips that on some hosts. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subset to apply and may redirect routings. Skill changes affect every future agent in the org; do not auto-apply.

Backlog items file to whatever devex / backlog tracker your team uses automatically. Those are tracker submissions, not skill edits. Only the Accepted list waits for approval.

For each approved Accepted item, follow the Routing field exactly:

- Trivial existing-skill edit (a one-line bullet, a tightened sentence, a stale fact corrected): parent does directly.
- Substantive existing-skill edit (a new section, a new pattern table, more than ~10 lines): hand to your host's skill-authoring skill and run its draft / test / iterate loop.
- `tune description: <skill path>` (the skill exists but didn't trigger when it should have): hand to the authoring skill and run its description-optimization loop.
- `new skill: <kebab-name>`: hand creation to the authoring skill. Do not invent the shape ad hoc.

If your environment ships a SKILL.md validator, run it on every touched skill before declaring done. Skip this step if it doesn't.

### 6. Summarize for the user

Short list, no preamble:

- Edits applied: `<skill path>`. What changed, one line each.
- New skills created: `<skill path>`. One line each (rare).
- Backlog filed to the devex tracker: `<issue title>` (`<tags>`). One line each.
- Dropped: one line per rejected finding + reason from the synthesizer.
