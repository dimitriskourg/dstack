# Host selection

Select one adapter before the first multi-step orchestration action. State the
selection to the user when the workflow will spawn, review in parallel, or
degrade because a capability is missing.

Use this precedence:

1. An explicit per-session host override supplied by the user or dstack-aware
   launcher.
2. A recognized native tool signature together with matching system identity.
3. A recognized host environment that does not conflict with the visible tool
   surface.
4. The `generic` adapter.

An environment variable or filesystem path alone is weak evidence. If identity
and tools disagree, select `generic` and use only the capabilities actually
visible. Never borrow parameters from a guessed provider.

Adapter selection does not prove that every mapped operation is available.
Before the first helper action, reconcile the adapter with the current session:

- helper creation, result collection, follow-up, waiting, and interruption;
- concurrent execution and queue or concurrency limits;
- whether read-only or filesystem isolation is enforced or advisory;
- trustworthy model enumeration or configured bindings;
- verification surfaces and external read connectors;
- permissions or approvals that can deny an otherwise native capability.

If a native action fails or is denied, apply the capability's documented
fallback immediately and report the degradation once. Do not retry by guessing
another host's call shape.

