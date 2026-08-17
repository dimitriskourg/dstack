# dstack capability contract

Version: `1.0.0`

Portable skills describe intent with this contract. Host adapters map that
intent to mechanics available in the active session. A skill must never invent
tool names, parameters, model identifiers, isolation, or persistence that the
selected adapter does not provide.

## Support classifications

Every adapter classifies every capability with exactly one status:

| Status | Meaning |
| --- | --- |
| `enforced` | The host technically guarantees the requested boundary. |
| `native` | The host provides the operation, but policy details still belong in the task prompt. |
| `advisory` | Instructions request the behavior; the host does not enforce it. |
| `approval-required` | The operation exists only after a user or administrator grants permission. |
| `unavailable` | The host cannot provide the operation in this session. |

Support is session-specific. An adapter describes the normal host mapping, but
the lead must downgrade it when a tool is absent, denied, or more constrained
than the adapter expects.

## Workflow capabilities

| Capability | Intent | Required | Parent-agent fallback |
| --- | --- | --- | --- |
| `explore` | Search and trace code without changing repository or external state. | yes | The parent searches and reads directly. |
| `implement` | Make bounded changes with an explicit write scope. | yes | The parent edits directly. |
| `review` | Apply an independent or deliberately separate critique rubric. | yes | The parent performs a distinct review pass and discloses that it was not independent. |
| `parallel` | Run independent slices concurrently. | no | Run the slices sequentially and state that parallel work collapsed. |
| `ask_user` | Obtain a product, preference, permission, or genuinely missing decision. | yes | Ask in ordinary conversation. Never ask for facts that can be observed safely. |
| `verify` | Exercise the narrowest meaningful check on the real target surface. | yes | Run the checks available to the parent and state the remaining evidence gap. |
| `model_role` | Prefer a configured semantic model role. | no | Inherit the parent model without inventing an identifier. |

## Agent lifecycle capabilities

These distinctions exist because `how` may coordinate read-only explorers and
critics. They describe lifecycle, not abstract work. A deterministic local CLI
must not claim to implement them.

| Capability | Intent | Required by `how` | Parent-agent fallback |
| --- | --- | --- | --- |
| `agents.spawn` | Start a bounded helper with a task packet. | no | Execute the packet on the parent. |
| `agents.wait` | Wait for an active helper without polling private state. | no | Continue or complete the corresponding parent pass. |
| `agents.follow_up` | Ask an existing helper to resolve a focused gap or contradiction. | no | Resolve it on the parent from repository evidence. |
| `agents.interrupt` | Stop a helper whose work is obsolete, unsafe, or out of scope. | no | Stop the corresponding parent pass. |
| `agents.collect` | Receive a helper's explicit structured result. | no | Use the parent pass's notes; never scrape transcripts. |
| `agents.isolation` | Separate helper permissions or filesystem writes from the parent. | no | Treat the boundary as advisory and disclose that it is not enforced. |

## Session and wake capabilities

| Capability | Intent | Required | Parent-agent fallback |
| --- | --- | --- | --- |
| `session.history` | Search first-class conversation history within an authorized user and workspace scope. | no | Use user-supplied handoffs, visible conversation, and repository state; state the gap. |
| `session.transcript` | Read an explicit current-session transcript or export without scanning private history directories. | no | Use the visible conversation or a compact parent digest; state the gap. |
| `runtime.wake` | Resume or notify a long-running workflow after an event or bounded interval. | no | Continue only while the parent session remains active; leave a durable handoff instead of claiming persistence. |

## Semantic model roles

Roles are configuration keys, never model names. Version 1 defines:

| Role | Typical use |
| --- | --- |
| `fast-explorer` | Broad read-only tracing. |
| `feature-worker` | Spec-driven implementation. |
| `bug-worker` | Evidence-led diagnosis and repair. |
| `deep-judgment` | Synthesis and difficult design decisions. |
| `skeptical-reviewer` | Adversarial critique. |
| `independent-judge` | Final evaluation independent of candidate work. |

Every role defaults to `inherit-parent`. A concrete binding is valid only when
the active host exposes a trustworthy catalog or the user supplies the exact
identifier.

## Rules for portable skills

1. Use capability names, not provider tool schemas.
2. State a parent-agent fallback for every optional operation used.
3. Treat read-only intent separately from enforced isolation. A prompt can be
   advisory even when the host natively supports helper sessions.
4. The lead owns decomposition, synthesis, final judgment, and verification.
5. Helper summaries are evidence pointers, not proof. Recheck load-bearing
   claims against code or real artifacts.
6. Missing model selection inherits the parent model.
7. Missing spawn support collapses work onto the parent and must be disclosed
   when the requested workflow would otherwise have fanned out.
