---
name: arena
description: "Spawn N parallel candidates at the same task, pick a base, graft the strongest parts of the losers into it. Use for /arena, 'arena this', 'throw it in the arena', or when one attempt at a non-trivial artifact would lock in the wrong shape."
---

# Arena

## Capability requirements

| Capability | Parent fallback |
| --- | --- |
| `explore` | The parent performs the same read-only pass. |
| `implement` | The parent implements the bounded change. |
| `review` | The parent performs a separate rubric-led pass and discloses that it was not independent. |
| `parallel` | Run the slices sequentially and state that fan-out collapsed. |
| `verify` | Run the checks available to the parent and state the remaining evidence gap. |
| `model_role` | Inherit the parent model. |

## Portability (required)

This skill is part of the portable **dstack** pack.

1. Read the `dstack` capability contract and the adapter for the active coding agent before delegation.
2. Use `parallel` with `implement` helpers for writable candidates, `review` for the cross-judge, and `verify` for the synthesized result.
3. Keep candidate write scopes disjoint (worktrees or separate output directories). Never let N candidates share one mutable path.
4. Resolve models through `model_role`; never require a vendor-specific model identifier or helper type.
5. When helper spawning is unavailable, run candidates sequentially on the lead agent, keep their outputs separated, and state that the arena collapsed.

## Purpose

Fan out N parallel attempts at the same task. Read every candidate end to end. Pick the strongest as the base. Graft the best ideas from the others into it. Verify the synthesized result.

Use **swarm** when the goal is independent coverage or aggregation. Use **arena** when the goal is one synthesized artifact chosen from competing candidates.

## Start

Create an explicit phase checklist before launching anything. Use a host plan or
todo surface when available; otherwise keep the numbered checklist in working
notes. The list keeps phases from silently disappearing.

1. Frame
2. Fan out
3. Cross-judge
4. Pick
5. Graft
6. Verify

## Phase A: Frame

The N candidates receive the same prompt, so the prompt is the contract. Get it right before spawning anything.

1. State the artifact each candidate is producing.
2. Derive the rubric. State what success looks like for *this* task, then turn it into 3–6 concrete gradeable criteria. Concrete: `Adds a --dry-run flag that skips writes`. Vague: `code is correct`. The rubric is the picker's tool in Phase D; candidates only see the task.
3. Pick the runners. Prefer `panels.arena-runners` from `DSTACK_HOME/config.json`. Otherwise use `model_role:skeptical-reviewer` and `model_role:deep-judgment`, requesting diverse configured bindings when available. Spawn more candidates when the arena covers multiple design directions. Use the same role N times only when the work is generation-bound rather than judgment-sensitive.
4. Assign output paths. Each candidate writes to its own location: a git worktree when the adapter supports isolation, otherwise a dedicated directory under the host's safe temporary root. Shared mutable output fails the **separate-before-serializing-shared-state** principle.

## Phase B: Fan out

Use `parallel` to launch all N candidates in one turn when the host supports it. Each helper receives:

- the shared task prompt;
- pointers to shared grounding evidence;
- its exclusive output path;
- instructions to produce both the artifact and a short rationale.

Prefer `implement` for candidates that must write code or files. Prefer `explore` only when the artifact is a read-only design package that must not edit the repo. Pass non-blocking delegation only when the active adapter supports it and the lead continues non-overlapping work.

The rationale is mandatory. Without it, the parent cannot tell whether a candidate's structure is principled or accidental, which makes Phase E grafting unreliable. Each rationale names the alternatives the candidate considered and what it rejected.

If a candidate fails to produce output, proceed with N-1 and note the dropout in the synthesis record.

## Phase C: Cross-judge

After all Phase B candidates complete, use `panels.arena-cross-judge` when configured; otherwise request `model_role:independent-judge`, falling back to `model_role:deep-judgment`. Prefer a binding distinct from the lead when the adapter supports selection.

Spawn one read-only `review` helper. It sees the rubric and the candidates by path label, scores each criterion, and recommends a base with rationale. Run it in parallel with the lead's own reading in Phase D, not while candidates are still writing. Judging partial outputs creates false dropouts.

## Phase D: Pick a base

Read every candidate end to end before picking. Skimming N candidates surfaces only the candidate whose surface looks most familiar.

Score each candidate against the rubric criterion by criterion, not on holistic feel. Compare against the cross-judge. Agreement on the base confirms the pick. Disagreement means one of you is biased or the rubric was ambiguous. Read both rationales before deciding.

Pick the base on which a future maintainer can extend most easily without breaking invariants. Prefer the cleaner boundary or smaller surface area when two feel tied, per the Laziness Protocol.

Record the pick and the reason in a short synthesis note alongside the base artifact, including the cross-judge's verdict. The lead owns the final pick.

## Phase E: Graft

Walk each losing candidate once more and identify what is worth porting into the base. The signal is usually one or two things per candidate, not most of it.

Fold each graft in by hand, per the **redesign-from-first-principles** principle. Do not paste mechanically. The result has to remain coherent under one mental model.

Record what was grafted, from which candidate, and what was rejected and why. The rejection notes are the highest-signal part of the record. Future readers learn from what you considered and dropped, not just what you kept.

When N candidates converge on the same shape, that is a strong agreement signal. Note the convergence and ship the consensus shape; no graft is needed. When N candidates wildly diverge, Phase A was under-specified. Reframe and re-run rather than averaging the divergence.

## Phase F: Verify

The synthesized artifact has to hold up under the same scrutiny as any other output, per the **prove-it-works** principle. The arena does not earn a pass.

Use `verify` on the narrowest meaningful real surface. If verification surfaces a problem the arena did not catch, either Phase A was wrong (re-frame and re-run) or one candidate caught it and you missed the graft (return to Phase E). Do not paper over.

## Outputs

One synthesized artifact. One short synthesis note alongside it, naming the base, the grafts (with source candidate), the rejections, the dropouts if any, and the verification result.

## Model roles

| Role | Use |
| --- | --- |
| `fast-explorer` | mechanical or generation-bound candidate work |
| `feature-worker` | spec-driven implementation candidates |
| `bug-worker` | evidence-backed fix candidates |
| `deep-judgment` | synthesis, base selection support, prose artifacts |
| `skeptical-reviewer` | diverse candidates and cross-judge pressure |
| `independent-judge` | cross-judging when a distinct binding is available |

If no role override is available, inherit the parent session model and say so.
