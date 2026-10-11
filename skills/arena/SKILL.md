---
name: arena
description: "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
---

# Arena

Spawn candidates and judges with the active harness's native subagent tool. Every supported harness can spawn subagents. If a nested spawn is denied, run the affected pass serially in the current agent and disclose the loss of independence.

## Configuration

Before using a profile, map the system-provided product identity to the canonical id `codex`, `claude`, or `cursor`, then read `~/.dstack/config.json` and select `hosts[<active-harness>]`. Never invent an alias or select another host entry. If the file is missing, unreadable, or invalid, the identity is unknown, its host entry is absent, or a required profile is missing or listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Every profile must provide a concrete model and effort pair; do not guess, omit, or inherit a binding.

Apply the profile through `worker_binding`: pass its exact model and effort for `spawn-arguments`; for `worker-definitions`, spawn `dstack-<profile>` without overrides. Stop if the binding is missing, rejected, or different. Never inherit session effort.

Open a todolist with one entry per phase (Frame, Fan out, Cross-judge, Pick, Graft, Verify) before launching anything.

## Phase A: Frame

Every candidate gets the same prompt, so the prompt is the contract.

1. State the artifact each candidate is producing.
2. Derive the rubric, 3-6 concrete gradeable criteria for what success looks like on *this* task. It is the picker's tool in Phase D. Candidates only see the task.
3. Pick the runners. Rotate across `feature-worker`, `bug-worker`, and `fast-explorer` so candidates start from different configured profiles. Repeat a profile when N exceeds three or the work is generation-bound.
4. Give each candidate its own output path under `/tmp/arena-<slug>/candidate-<n>/`. Candidates may read the repository but write only proposal artifacts to their assigned directories. N candidates writing to the same path is shared mutable state and fails the **separate-before-serializing-shared-state** principle skill test. Arena does not fan out repository writers. The parent applies the selected design serially in the active checkout.

## Phase B: Fan out

Launch candidates in bounded waves that fit the active harness's available child capacity. Each gets the task, the path to the shared grounding, its own output path, and instructions to produce the artifact and a short rationale naming the alternatives it considered and what it rejected. Every required candidate runs even when N exceeds the first wave's capacity.

If a required candidate produces no output, retry it in a later wave or run that candidate pass serially in the current agent. Do not reduce N silently. If the user accepts a smaller candidate set after a persistent failure, record the reduced independence in the synthesis note.

## Phase C: Cross-judge

After all Phase B candidates complete, use the configured `skeptical-reviewer` profile. Spawn one read-only judge subagent. It sees the rubric and the candidates by path label, scores each criterion, and recommends a base with rationale. It runs in parallel with your reading in Phase D. Don't spawn it while candidates are still writing.

## Phase D: Pick a base

Read every candidate end to end before picking. Score each against the rubric criterion by criterion, not on holistic feel, and compare with the cross-judge. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base a future maintainer can extend most easily without breaking invariants. When two feel tied, prefer the cleaner boundary or smaller API, per the Laziness Protocol.

Record the pick and the reason in a short synthesis note alongside the base artifact, including the cross-judge's verdict.

## Phase E: Graft

Walk each losing candidate once more for what is worth porting into the base, usually one or two things per candidate, not most of it. Fold each graft in by hand, per the **redesign-from-first-principles** principle skill, so the result stays coherent under one mental model. Don't paste mechanically.

If the candidates converge on one shape, that is strong agreement. Note it and ship the consensus shape. No graft is needed. If they wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

Verify the synthesized artifact like any other output, per the **prove-it-works** principle skill. If verification finds a problem the arena missed, either Phase A was wrong (re-frame and re-run) or a candidate caught it and you missed the graft (go back to Phase E). Don't paper over it.

## Outputs

One synthesized artifact, with a short synthesis note alongside naming the base and why, the cross-judge's verdict, each graft with its source candidate, what was rejected and why, any convergence or dropouts, and the verification result.
