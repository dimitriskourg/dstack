---
name: how
description: "Use for \"how does X work\", code walkthroughs before changing something, and placement / ownership / layering questions (\"where should this live\", \"which package owns this\", \"is this the right layer\"). Explains subsystem architecture, runtime flow, onboarding mental models. Use why for motivation."
---

# How

Explore the codebase to answer "how does X work?" questions. Produce architectural explanations at the level of a senior engineer onboarding onto a subsystem, enough to build a working mental model, not so much that it reads like annotated source code.

## Configuration

Before using a profile, map the system-provided product identity to the canonical id `codex`, `claude`, or `cursor`, then read `~/.dstack/config.json` and select `hosts[<active-harness>]`. Never invent an alias or select another host entry. If the file is missing, unreadable, or invalid, the identity is unknown, its host entry is absent, or a required profile is missing or listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Every profile must provide a concrete model and effort pair; do not guess, omit, or inherit a binding.

Apply the profile through `worker_binding`: pass its exact model and effort for `spawn-arguments`; for `worker-definitions`, spawn `dstack-<profile>` without overrides. Stop if the binding is missing, rejected, or different. Never inherit session effort.

Helpers below are read-only. If your host cannot enforce that, instruct the helper not to write and don't describe the boundary as enforced. Explorers use the configured `fast-explorer` profile. Every explainer uses the configured `skeptical-reviewer` profile.

Spawn helpers with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, the current agent performs that pass directly.

## 1. Assess complexity

If the scope is ambiguous, state your interpretation and explore. The user can redirect.

- **Simple** (a single module, a small utility, a narrow question such as "how does function X work"): no explorers. Spawn one explainer that explores and explains in one pass, built from `references/explainer-prompt.md` without the explorer-findings section. Go to step 4.
- **Complex** (a subsystem spanning multiple files or services, a cross-cutting feature, a full architectural overview): go to step 2.

When in doubt, take the simple path.

## 2. Explore (complex only)

Decompose the question into 2 to 4 angles, each a distinct slice of the subsystem. Spawn all explorers in a single message, each with `references/explorer-prompt.md` and its angle filled in.

## 3. Synthesize (complex only)

Once all explorers have returned, spawn one explainer with `references/explainer-prompt.md` and every explorer's findings filled in.

## 4. Present

Present the explainer's output. Light edits for clarity or context from the conversation are fine. Do not substantially rewrite it.

## Output format

The explanation uses the sections defined in `references/explainer-prompt.md`, dropping any that do not apply: Overview, Key Concepts, How It Works, Where Things Live, Gotchas.
