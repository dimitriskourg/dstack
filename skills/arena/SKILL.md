---
name: arena
description: "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
---

# Arena

Fan out N parallel attempts at the same task. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the synthesized result.

Spawn candidates and judges with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, run the affected pass serially in the current agent and disclose the loss of independence.

## Configuration

Before using a profile, map the system-provided product identity to the canonical id `codex`, `claude`, or `cursor`, then read `~/.dstack/config.json` and select `hosts[<active-harness>]`. Never invent an alias or select another host entry. If the file is missing, unreadable, or invalid, the identity is unknown, its host entry is absent, or a required profile is missing or listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Every profile must provide a concrete model and effort pair; do not guess, omit, or inherit a binding.

Apply the profile through `worker_binding`: pass its exact model and effort for `spawn-arguments`; for `worker-definitions`, spawn `dstack-<profile>` without overrides. Stop if the binding is missing, rejected, or different. Never inherit session effort.

## Start

Open a todolist with one entry per phase before launching anything. The arena runs autonomously and the list keeps phases from silently disappearing.

1. Frame
2. Fan out
3. Cross-judge
4. Pick
5. Graft
6. Verify

## Phase A: Frame

The N candidates will receive the same prompt, so the prompt is the contract. Get it right before spawning anything.

1. State the artifact each candidate is producing.
2. Derive the rubric. State what success looks like for *this* task, then turn it into 3-6 concrete gradeable criteria. Concrete: `Adds a --dry-run flag that skips writes`. Vague: `code is correct`. The rubric is the picker's tool in Phase D; candidates only see the task.
3. Pick the runners. Rotate across `feature-worker`, `bug-worker`, and `fast-explorer` so candidates start from different configured profiles. Repeat a profile when N exceeds three or the work is generation-bound.
4. Assign output paths under `/tmp/arena-<slug>/candidate-<n>/`. Candidates may read the repository but write only proposal artifacts to their assigned directories. N candidates writing to the same path is shared mutable state and fails the **separate-before-serializing-shared-state** principle skill test. Arena does not fan out repository writers; the parent applies the selected design serially in the active checkout.

## Phase B: Fan out

Launch candidates in bounded waves that fit the active harness's available child capacity. Each gets the task, the path to the shared grounding, its own output path, and instructions to produce both the artifact and a short rationale. Every required candidate runs even when N exceeds the first wave's capacity.

The rationale is mandatory. Without it, the parent cannot tell whether a candidate's structure is principled or accidental, which makes Phase E grafting unreliable. Each rationale names the alternatives the candidate considered and what it rejected.

If a required candidate fails to produce output, retry it in a later wave or run that candidate pass serially in the current agent. Do not reduce N silently. If the user accepts a smaller candidate set after a persistent failure, record the reduced independence in the synthesis note.

## Phase C: Cross-judge

After all Phase B candidates complete, use the configured `skeptical-reviewer` profile. Spawn one read-only judge subagent. It sees the rubric and candidates by path label, scores each criterion, and recommends a base with rationale. It runs in parallel with the parent's reading in Phase D, not with candidates that are still writing.

## Phase D: Pick a base

Read every candidate end to end before picking. Skimming N candidates surfaces only the candidate whose surface looks most familiar.

Score each candidate against the rubric criterion by criterion, not on holistic feel. Compare against the cross-judge. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base on which candidate a future maintainer can extend most easily without breaking invariants. Prefer the cleaner boundary or smaller surface area when two feel tied, per the Laziness Protocol.

Record the pick and the reason in a short synthesis note alongside the base artifact, including the cross-judge's verdict.

## Phase E: Graft

Walk each losing candidate once more and identify what is worth porting into the base. The signal is usually one or two things per candidate, not most of it.

Fold each graft in by hand, per the **redesign-from-first-principles** principle skill. Don't paste mechanically. The result has to remain coherent under one mental model.

Record what was grafted, from which candidate, and what was rejected and why. The rejection notes are the highest-signal part of the record. Future readers learn from what you considered and dropped, not just what you kept.

When N candidates converge on the same shape, that is a strong agreement signal. Note the convergence in the record and ship the consensus shape. No graft is needed. When N candidates wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

The synthesized artifact has to hold up under the same scrutiny as any other output, per the **prove-it-works** principle skill. The arena does not earn you a pass.

If verification surfaces a problem the arena did not catch, either Phase A was wrong (re-frame and re-run) or one candidate caught it and you missed the graft (go back to Phase E). Don't paper over.

## Outputs

One synthesized artifact. One short synthesis note alongside, naming the base, the grafts (with source candidate), the rejections, the dropouts if any, and the verification result.
