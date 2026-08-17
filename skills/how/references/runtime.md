# Runtime selection

Before a helper or parallel step:

1. Read the installed dstack capability contract under `DSTACK_HOME/contracts/`
   (`DSTACK_HOME` defaults to `~/.dstack`).
2. Select a host with `host-selection.md`.
3. Read that adapter's `capabilities.toml` and `instructions.md`.
4. Reconcile the adapter with the operations actually visible in this session.
5. State the selected adapter at the start of a multi-step orchestration flow.

Do not invent tool parameters, model identifiers, isolation, or persistence.
If a capability is absent or denied, use the fallback from the skill and
adapter. Parent execution is the universal fallback.

