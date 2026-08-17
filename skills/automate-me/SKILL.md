---
name: automate-me
description: "Use for \"automate me\", \"create or update my mode skill\", \"capture my working style\", or wanting future coding agents to follow the user's recurring conventions. Mines authorized recent evidence, asks for confirmation, and drafts or revises one personal -mode skill through the active host's skill-authoring workflow."
---

# Automate me

## Capability requirements

| Capability | Parent fallback |
| --- | --- |
| `explore` | The parent performs the same read-only pass. |
| `review` | The parent performs a separate rubric-led pass and discloses that it was not independent. |
| `parallel` | Run the slices sequentially and state that fan-out collapsed. |
| `ask_user` | Ask in ordinary conversation. |
| `model_role` | Inherit the parent model. |
| `session.history` | Use user-confirmed preferences and visible evidence; state the history gap. |

## Portability (required)

1. Read the `dstack` capability contract and the active host adapter before delegation.
2. Discover skill locations, `session.history`, authoring tools, and invocation controls through the active host. Do not assume one vendor directory or frontmatter flag.
3. Use `parallel` with read-only `explore` helpers for authorized history slices. Use the host's skill-authoring and validation workflow for the draft.
4. Resolve mining through `model_role:fast-explorer`, drafting through `model_role:deep-judgment`, and independent review through `model_role:skeptical-reviewer` when available.
5. When history is unavailable, rely on user-confirmed preferences and current evidence rather than inventing habits.

## Purpose

Turn the user's recurring working conventions into one concise `-mode` skill that future agents can invoke. Examples include response style, autonomy, delegation, verification, code discipline, Git workflow, and skill-maintenance habits.

The output is a mode skill tailored to the user, not a copy of `dstack-mode` and not a general manual.

## Flow

### 0. Find an existing mode skill

Search canonical user skills under `~/.agents/skills/` and any project-local
`.agents/skills/` directory explicitly selected for this project. Preserve the
existing canonical location when updating. Do not treat compatibility links as
independent skills.

When one exists, default to updating it unless the user explicitly asks to start over. Determine the last meaningful edit through repository history or file metadata when available, then mine only newer evidence.

When several candidates exist, show their paths and recommend the one already active for the current host. Do not merge personal mode skills silently.

### 1. Gather authorized evidence

Use the best available sources:

1. user-provided examples, corrections, or an existing mode skill;
2. first-class conversation-history resources scoped to the current user and workspace;
3. explicitly supplied handoffs, exports, or transcript references;
4. the visible current conversation;
5. repository conventions that the user repeatedly enforced.

Never scan broad history directories to guess which conversations belong to this task. Do not read unrelated workspaces.

For a broad history window, use `parallel` with several read-only `explore` helpers split by time or topic. Each returns patterns with evidence pointers and counterexamples.

Look for:

- response length, tone, structure, and corrections;
- when the user wants autonomy versus checkpoints;
- delegation, parallelism, and model-role preferences;
- what counts as verification and completion;
- code, type, comment, and prose discipline;
- worktree, commit, pull-request, review, and merge conventions;
- repeated skill or tooling improvements;
- explicit dislike of particular behaviors.

Require repeated evidence before promoting a pattern. A preference seen in two or more independent contexts is stronger than one isolated correction. Contradictory evidence stays unresolved until the user decides.

### 2. Ask the user to confirm intent

Mining reveals behavior, not necessarily enduring preference.

Use `ask_user` for one or two structured rounds with a recommended selection and several concrete options. Allow multiple selections for categories such as autonomy, verification, or response style. End with one free-form question for anything the options missed.

For an update, ask what changed, what the existing skill gets wrong, and whether any old rule should be removed. Do not restart the onboarding interview from zero.

### 3. Cluster the confirmed rules

Use only sections the evidence supports. Common sections include:

- **Response style**
- **Autonomy and checkpoints**
- **Understand before changing**
- **Delegation and parallelism**
- **Code and prose discipline**
- **Review and verification**
- **Git and delivery process**
- **Skill and tooling maintenance**

Each rule must be operational and distinguish the user from reasonable defaults. “Communicate clearly” does not earn a line. “Use short paragraphs; use tables for comparisons; avoid long bullet walls” does.

Read `dstack-mode` for granularity and structure, not content. The user's rules may be much smaller.

### 4. Draft or update the skill

Use an available skill-authoring workflow. Preserve portable validation rules
and the existing category layout; keep provider configuration out of the skill
package.

For a new skill:

- choose the user's handle or requested identifier;
- name it `<handle>-mode`;
- place it under `~/.agents/skills/` by default, or under project-local `.agents/skills/` only when the user explicitly requests repository ownership;
- make the description trigger on the handle, slash command, and “work in this person's style,” not generic coding words;
- prefer explicit human invocation for heavy personal modes when the host supports invocation policy;
- document mode lifetime honestly when the host cannot persist it across sessions or compaction.

For an update:

- preserve sections not contradicted by new evidence;
- revise stale rules in place;
- remove disproven or unwanted rules;
- add a section only for a genuinely new cluster;
- keep the diff focused and reviewable.

Do not copy other skills inline. Reference them by name and let them own their detailed workflows.

### 5. Tighten and review

Apply **unslop** to every line. Keep instructions concise, declarative, and testable.

Show the draft and the evidence-to-rule mapping to the user. Expect iterations. Cut rules that are generic, ambiguous, contradictory, or supported by only one weak example.

When helpers are available, use one read-only `review` pass with `model_role:skeptical-reviewer` to look for overfitting, dangerous autonomy, conflicting rules, and trigger overreach.

### 6. Validate trigger and behavior

Run the host's Skill validator when one exists.

Check:

- the description triggers on the user's explicit mode request;
- unrelated coding requests do not activate it unexpectedly;
- every referenced skill is available or has a fallback;
- host-specific metadata appears only where supported;
- the mode works after the expected session lifecycle event;
- the generated prose matches the user's confirmed style.

A full benchmark may be unnecessary for a subjective personal mode, but trigger accuracy and dangerous autonomy rules still need explicit checks.

### 7. Land it

Use a clean branch or worktree according to the repository workflow. Commit the focused mode-skill change and open a pull request when the project uses review. Do not push directly to a protected main branch.

Report the path, invocation, evidence window, key rules added or changed, validation performed, and any host-lifecycle limitation.

## Guardrails

- Do not overfit one conversation.
- Do not codify inferred sensitive traits or private information.
- Do not grant irreversible autonomy by default.
- Do not write poetic or motivational prose for an agent reader.
- Do not force every possible section into the skill.
- Use “the user” or “the human” in operational instructions rather than repeatedly naming the author.
- A narrow workflow such as commit-message style may deserve a normal skill rather than a global mode.

## Model roles

| Role | Use |
| --- | --- |
| `fast-explorer` | scoped history mining |
| `deep-judgment` | clustering, drafting, and user-intent synthesis |
| `skeptical-reviewer` | overfitting and trigger-safety review |

If no role override is available, inherit the parent session model.
