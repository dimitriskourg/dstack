---
name: setup-dstack
description: "Configure dstack host selection and semantic model-role bindings under DSTACK_HOME. Use for setup-dstack, configuring dstack models, changing role assignments, or reviewing stale model bindings. Never invents model identifiers."
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
catalog. Preserve exact identifiers. Never infer a slug from a display name,
documentation example, another host, or memory.

When no catalog is available:

- preserve existing bindings;
- accept exact identifiers the user explicitly supplies;
- default every unbound role to `inherit-parent`;
- label catalog validation unavailable.

### 3. Reconcile current bindings

Run the bundled configurator's `show` command. A missing `config.json` resolves
to valid defaults. For the selected host:

- preserve bindings still present in the catalog;
- retain removed identifiers but add them to `stale_models`;
- remove an identifier from `stale_models` when it becomes available again;
- show newly available models without assigning them automatically;
- preserve every other host.

The six required roles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `deep-judgment`
- `skeptical-reviewer`
- `independent-judge`

`inherit-parent` is always valid. Missing roles resolve to it.

### 4. Propose, then confirm

Show the current and proposed value for every role, stale bindings, catalog
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
    "fast-explorer": "inherit-parent",
    "feature-worker": "inherit-parent",
    "bug-worker": "inherit-parent",
    "deep-judgment": "inherit-parent",
    "skeptical-reviewer": "inherit-parent",
    "independent-judge": "inherit-parent"
  },
  "stale_models": []
}
```

Invoke the bundled script by its absolute installed path:

```text
python3 <setup-dstack-dir>/scripts/configure.py apply --proposal <temporary-json>
```

The helper validates schema version 1, preserves other hosts, and atomically
replaces `config.json`. Delete the temporary proposal after the command. If it
fails, report its exact error; do not repair or replace the previous file by
hand.

### 6. Report

Return:

- selected host and selection evidence;
- configuration path;
- roles changed and preserved;
- stale and newly available models;
- whether catalog validation was available;
- schema-validation result;
- capabilities still inheriting or unavailable.
