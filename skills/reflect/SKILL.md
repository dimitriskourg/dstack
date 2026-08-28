---
name: reflect
description: Spawn three parallel review subagents over the active transcript, surface learnings, and route each to a concrete edit on an existing skill. Use when the user says reflect.
disable-model-invocation: true
---

# Reflect

Mine the current conversation for durable learnings, then route them into skill edits.

Spawn reviewers with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, run the affected review serially and disclose the loss of independence.

## Configuration

Before locating the transcript or using a profile, map the system-provided product identity to the canonical id `codex`, `claude`, or `cursor`. Resolve the canonical repository root with `git rev-parse --show-toplevel` and symlink resolution. Read `~/.dstack/config.json`, select `hosts[<active-harness>]` and its `repositories[<canonical-repository-root>]`, and verify the repository entry's `repository_root` exactly matches. Never invent an alias or select another host or repository entry. If the file is missing, unreadable, or invalid, either entry is absent, the identity or repository is unknown, or a required profile is missing or listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Every profile must provide a concrete model and effort pair; do not guess, omit, or inherit a binding.

Apply the profile through `worker_binding`: pass its exact model and effort for `spawn-arguments`; for `worker-definitions`, spawn `dstack-<profile>` without overrides. Stop if the binding is missing, rejected, or different. Never inherit session effort.

## When to invoke

- The user said "reflect" or "/reflect".
- A complex task (5+ tool calls) just landed cleanly and the recipe is worth keeping.
- The agent hit dead ends, found the working path, and the path generalizes.
- The user corrected the agent's approach mid-task.
- A non-trivial workflow emerged that isn't captured anywhere.

Skip when the conversation is trivial, off-topic, or already covered by an existing skill the parent followed correctly. One-offs are not learnings.

## Process

### 1. Locate the active transcript

Use the selected repository entry's configured `transcripts_directory`. Do not search again here. When it is `null` or the directory is unreadable, skip to the digest fallback below.

```bash
ls -t <transcript-dir>/*.jsonl <transcript-dir>/*/*.jsonl <transcript-dir>/*/subagents/*.jsonl 2>/dev/null | head -10
```

Hosts differ in layout. Flat (`<id>.jsonl`), nested (`<id>/<id>.jsonl`), and subagent transcripts under the parent's directory are all common. Match whatever your host writes.

For each candidate, read the first line and check that its message text contains the conversation's opening user prompt. Take the matching path. If no path resolves, write a tight digest of the session and pass that instead.

### 2. Run three reviewers

Launch three general-purpose subagents in bounded waves that fit the active harness's available child capacity, each on a different configured profile, with full tool access. **Don't use a restricted read-only mode.** Reviewers need MCP access for context lookups. The prompt forbids file writes; the parent applies edits. Every required reviewer runs even when the first wave cannot hold all three.

| Lens | Model role | Prompt template |
|---|---|---|
| Judgment | `skeptical-reviewer` | `references/judgment-reviewer.md` |
| Tooling | `bug-worker` | `references/tooling-reviewer.md` |
| Divergent | `fast-explorer` | `references/divergent-reviewer.md` |

Pass each template verbatim, substituting the transcript path or digest where marked. Reviewers return findings in their response body.

### 3. Synthesize

One general-purpose subagent on your configured `skeptical-reviewer` role, with full tool access. The synthesizer's quality check includes spot-verifying citations, which can require MCP access; a restricted read-only mode strips that on some hosts. Use `references/synthesizer.md` verbatim, with each reviewer's full output inlined where marked. The synthesizer returns a structured Accepted / Rejected / Backlog list.

### 4. Structural enforcement check

Sanity-check the synthesizer's Accepted list. For any item that would be enforced more reliably by a lint rule, script, metadata flag, or runtime check, move it from Accepted to Backlog. The synthesizer already applies this criterion; this is a final pass before edits land. See the **encode-lessons-in-structure** principle skill.

### 5. Apply

Before applying any Accepted edit or filing any Backlog item, present the synthesizer's full Accepted/Rejected/Backlog output to the user and wait for explicit approval. The user picks which subsets to apply or file and may redirect routings. Skill changes affect every future agent in the org, and tracker writes mutate external state; do not perform either automatically.

When approved Backlog items have no configured tracker or the requested write is unavailable, keep them in the in-chat result without blocking approved skill edits.

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
- Backlog proposed: `<issue title>` (`<tags>`). State `filed` with the tracker link only when the user approved and the write succeeded; otherwise state `not filed`.
- Dropped: one line per rejected finding + reason from the synthesizer.
