---
name: how
description: "Use for how-does-this-work questions, code walkthroughs before changing something, and placement, ownership, or layering questions. Explains subsystem architecture and runtime flow; optionally critiques the design. Use why for historical motivation."
---

# How

Answer questions about how a subsystem works at the level of a senior engineer
onboarding into it. Build a working mental model, not an annotated source dump.

There are two modes:

1. **Explain** is the default. Trace the system and present one coherent model.
2. **Critique** explains the system first, then independently reviews its design.

## Capability requirements

Read `references/runtime.md` before any helper action.

| Capability | Use | Fallback |
| --- | --- | --- |
| `explore` | Read-only code tracing. | The parent performs the same search and trace. |
| `review` | Independent architectural criticism. | The parent runs a distinct rubric-led pass and discloses that it was not independent. |
| `parallel` | Two to four independent exploration or review slices. | Run slices sequentially and state that fan-out collapsed. |
| `verify` | Exercise a live surface when source cannot settle behavior. | The parent runs available checks and states the remaining evidence gap. |
| `model_role` | Prefer `fast-explorer`, `deep-judgment`, or `skeptical-reviewer`. | Inherit the parent model. |
| `agents.spawn` | Start a bounded explorer or critic. | Execute its task packet on the parent. |
| `agents.wait` | Await active helpers. | Complete the corresponding parent pass. |
| `agents.follow_up` | Resolve a focused gap or contradiction. | Resolve it on the parent from repository evidence. |
| `agents.interrupt` | Stop obsolete or out-of-scope work. | Stop the corresponding parent pass. |
| `agents.collect` | Receive structured findings. | Use the parent pass's notes. |
| `agents.isolation` | Keep exploration and criticism from changing state. | Treat read-only behavior as advisory and disclose that it is not enforced. |

Do not use a write-capable path for this skill. Read-only intent forbids
repository edits and external mutations, while still allowing authorized reads
from evidence systems. Never claim that a prompt creates enforced isolation.

## Explain mode

### 1. Interpret and size the question

Identify the target, requested depth, and likely entry point. If wording is
ambiguous, state the best current interpretation and proceed; let the user
redirect rather than blocking on a fact the repository can answer.

Classify the investigation:

- **Simple:** one function, module, or narrow data path that fits in one pass.
- **Complex:** a subsystem spanning files, services, packages, runtime
  surfaces, or ownership boundaries.

Lean simple when uncertain. Fan out only when independent angles will reduce
blind spots or protect the parent context.

### 2a. Explore a complex subsystem

Split the question into two to four distinct angles, such as:

- data model and state ownership;
- request, event, or command path;
- configuration and dependency wiring;
- persistence, queues, or external boundaries;
- runtime effects, metrics, and failure handling;
- tests and public extension points.

Use `parallel` with one read-only `explore` pass per slice. Request the
`fast-explorer` model role. Each pass follows
`references/explorer-prompt.md` and returns structured findings with exact file
and symbol pointers. File names alone are not evidence.

Use the active adapter's lifecycle operations. If spawning is missing or
denied, execute every slice on the parent, preserve the decomposition, and say
that parallel exploration collapsed. If model selection is missing or denied,
inherit the parent model.

### 2b. Explore a simple target

Perform one read-only `explore` pass on the parent. Spawn a helper only when it
will materially improve tracing, not merely because helpers exist. Request the
`deep-judgment` role if model roles are available.

Read `references/explainer-prompt.md`. Trace the complete path before writing;
do not stop at the first matching symbol.

### 3. Synthesize complex findings

Collect all exploration results. The parent owns synthesis; it may use one
read-only `explore` helper with the `deep-judgment` role when the evidence is
too large for a reliable parent pass.

Reconcile overlap, resolve contradictions by reading the code or sending one
focused follow-up, and distinguish confirmed behavior from inference. Verify
every load-bearing claim that appears only in a helper summary.

### 4. Present

Use the sections that fit the question:

- **Overview:** what the subsystem is, what it does, and where its boundary sits.
- **Key concepts:** the few types, services, state containers, or protocols
  needed to follow the rest.
- **How it works:** a step-by-step runtime or data-flow narrative with exact
  file and symbol references.
- **Where things live:** the files a maintainer should open first.
- **Gotchas:** hidden state, ordering constraints, compatibility paths,
  misleading names, or unverified facts.

Use a diagram only when component relationships or state transitions are
materially clearer than prose. When source cannot settle a live-behavior claim,
use `verify` through the parent and state any remaining evidence gap.

## Critique mode

Critique starts only after Explain mode has established a grounded model.

### 1. Frame the review

State the architecture's goal, confirmed constraints, and review scope.
Reviewers judge the design against that intent, not personal style.

### 2. Run independent critics

Use `parallel` with two or more read-only `review` passes. Request the
`skeptical-reviewer` role and diverse configured bindings when available.
Every critic receives:

1. the explanation;
2. relevant file and symbol pointers;
3. `references/critic-prompt.md`;
4. `references/critique-rubric.md`.

When independent helpers are unavailable, run distinct rubric-led parent passes
sequentially and label the result as non-independent.

### 3. Apply lead judgment

The parent reads the relevant code, deduplicates findings, and classifies them:

- **Act on:** a correctness, operability, or maintainability problem worth
  fixing now.
- **Consider:** a real trade-off whose benefit may not justify current cost.
- **Noted:** valid context with low immediate impact.
- **Dismissed:** incorrect, mitigated, unsupported, or merely stylistic.

Agreement is stronger evidence, not proof. Present the explanation first and
the critique second so the architecture model remains useful by itself.
