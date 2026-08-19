---
name: setup-dstack
description: "Configure dstack host selection and semantic model-and-effort role bindings under DSTACK_HOME. Use for setup-dstack, configuring dstack models or reasoning effort, changing role assignments, migrating schema version 1, or reviewing invalid bindings. Never invents model identifiers or effort support."
---

# Setup dstack

Manage personal dstack configuration without changing installed skills,
adapters, runtime files, or compatibility links.

## Capability requirements

| Capability | Parent fallback |
| --- | --- |
| `explore` | Inspect configuration and the available host catalog directly. |
| `ask_user` | Present the proposed bindings in ordinary conversation and wait for confirmation. |

## Files

Use `DSTACK_HOME` when set; otherwise use `~/.dstack`.

- Read the capability and host-selection contracts under
  `DSTACK_HOME/contracts/`.
- Read the selected adapter's `capabilities.toml` and `profiles.toml`.
- Read and write only `DSTACK_HOME/config.json` for personal choices.
- Validate the resulting object against `DSTACK_HOME/schemas/config.schema.json`.
- Use the bundled `scripts/configure.py` for reads, validation, and writes. Do
  not hand-edit the configuration.

Do not write provider rule files. Do not alter canonical skills or managed
compatibility links.

## Process

### 1. Select the host

Apply the documented precedence: explicit session override, matching native
identity and tool signature, recognized environment, then generic.

State the detected host and evidence. If identity is ambiguous, use `generic`.
An explicit persistent `host_override` is allowed only when the user requests
it; otherwise retain `auto`.

### 2. Discover models honestly

Enumerate models only when the selected host exposes a trustworthy current
catalog. Read the selected adapter's discovery procedure and preserve exact
model identifiers and the effort levels reported for each model. Prefer the
current operation's tool schema when it enumerates accepted model and effort
values. Never infer a slug or supported effort from a display name,
documentation example, another host, or memory.

When no catalog is available:

- preserve existing bindings;
- accept exact model and effort values the user explicitly supplies, without
  claiming they were catalog-validated;
- default every unbound role to `inherit-parent`;
- label catalog validation unavailable.

### 3. Reconcile current bindings

Run the bundled configurator's `show` command. A missing `config.json` resolves
to valid defaults. For the selected host:

- preserve bindings whose model-effort pair is still present in the catalog;
- retain unavailable pairs but add them to `invalid_bindings`;
- remove a pair from `invalid_bindings` when it becomes valid again;
- show newly available models without assigning them automatically;
- preserve every other host.

The six required roles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `deep-judgment`
- `skeptical-reviewer`
- `independent-judge`

`{"model": "inherit-parent", "effort": "inherit-parent"}` is always valid.
Missing roles resolve to that binding. A concrete model may use
`"effort": "inherit-parent"` when the active host cannot map effort explicitly;
do not claim pair validation in that case.

### 4. Propose, then confirm

Show the current and proposed model and effort for every role, invalid bindings, catalog
status, and the persistent host override. Use `ask_user` only for actual
preferences. Recommend retaining valid bindings and using `inherit-parent` for
unknowns.

Do not write before the user confirms the proposed mapping.

### 5. Apply the confirmed proposal

After confirmation, create a temporary JSON proposal containing exactly one
complete host mapping. Include `panels` only when changing the shared semantic
panel composition. Include `host_override` only when the user explicitly asks
to change it.

```json
{
  "host": "<selected-host>",
  "roles": {
    "fast-explorer": {"model": "inherit-parent", "effort": "inherit-parent"},
    "feature-worker": {"model": "inherit-parent", "effort": "inherit-parent"},
    "bug-worker": {"model": "inherit-parent", "effort": "inherit-parent"},
    "deep-judgment": {"model": "inherit-parent", "effort": "inherit-parent"},
    "skeptical-reviewer": {"model": "inherit-parent", "effort": "inherit-parent"},
    "independent-judge": {"model": "inherit-parent", "effort": "inherit-parent"}
  },
  "invalid_bindings": []
}
```

Invoke the bundled script by its absolute installed path:

```text
python3 <setup-dstack-dir>/scripts/configure.py apply --proposal <temporary-json>
```

The helper accepts schema version 1 as migration input, writes schema version
2, preserves other hosts, and atomically
replaces `config.json`. Delete the temporary proposal after the command. If it
fails, report its exact error; do not repair or replace the previous file by
hand.

To migrate without changing any role choices, run:

```text
python3 <setup-dstack-dir>/scripts/configure.py migrate
```

Version 1 model strings become version 2 bindings with
`"effort": "inherit-parent"`; no effort is guessed.

### 6. Report

Return:

- selected host and selection evidence;
- configuration path;
- roles changed and preserved;
- invalid and newly available model-effort bindings;
- whether catalog validation was available;
- schema-validation result;
- capabilities still inheriting or unavailable.
