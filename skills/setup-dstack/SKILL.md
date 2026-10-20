---
name: setup-dstack
description: Configure dstack model-and-effort profiles and the active repository's transcript directory. Use for setup-dstack, changing profile assignments, or refreshing transcript discovery. Never invent model identifiers, effort support, or transcript paths.
disable-model-invocation: true
---

# Setup dstack

Use `~/.dstack/config.json` as the only configuration source. Its location is fixed; do not honor an environment override or accept another path. Use `scripts/configure.py` for validation and atomic config writes. Do not create host rule files or worker definition files, and do not edit installed skills.

## 1. Identify the host

Map the system-provided product identity to exactly one canonical harness id: Codex is `codex`, Claude Code is `claude`, and Cursor is `cursor`. Never derive the id from repository files, transcript paths, or user-provided aliases. This id is always the configuration key; there is no override. If the product identity is unavailable or is not one of those three, stop and report the observed identity evidence.

Resolve the active repository with `git rev-parse --show-toplevel`, then canonicalize that absolute path by resolving symlinks. This canonical repository root is the repository id written by setup. If there is no active Git repository or the root cannot be canonicalized, stop; never reuse another project's repository entry. Linked Git worktrees of an already-registered repository do not need a second setup pass. Consumers resolve them with:

```text
python3 <setup-dstack-dir>/scripts/configure.py resolve --host <active-harness>
```

That command selects a registered checkout that shares `git rev-parse --git-common-dir`.

## 2. Discover models

Use a trustworthy catalog exposed by the active host. Preserve exact model identifiers and the effort levels reported for each model. Never infer a slug or supported effort from a display name, example, another host, or memory.

Inspect how the catalog is shaped before treating it as complete:

- A complete catalog enumerates model identifiers and, separately, the effort values each model accepts.
- A fused spawn identifier carries model and effort in one string. On `codex` and `claude`, never store it; ask the user to confirm the model identifier and the effort as two values. On `cursor`, a fused identifier the spawn operation lists is a valid profile value, stored unchanged.
- If the spawn operation lists fewer models or efforts than the host's picker or a host models API, that list is partial: it is only what this session can pass as a spawn argument. Prefer a host models API or CLI that lists entitled models and their effort parameters when one exists. Otherwise ask the user for exact pairs. Never claim validation against a partial list.
- When the catalog is partial, preserve existing concrete bindings. Do not move a pair to `invalid_bindings` only because it is absent from this session's spawn list. Put a pair in `invalid_bindings` only when a complete catalog, or the host itself, rejects it.

When no catalog is available, preserve existing concrete bindings. For any unconfigured profile, ask the user for an exact model and effort pair without claiming validation. Do not write until all four profiles have concrete values.

Take the effort levels from the host's own enumeration of them. A host can accept an unknown effort value without complaint and then run the worker at the session effort, so an effort that the host does not enumerate is not a validated value; ask for a replacement instead of saving it.

The four profiles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `skeptical-reviewer`

## 3. Shape each profile for the spawn call

Each profile holds exactly what the host's native spawn call takes, so setup never generates worker definitions. On `codex` and `claude`, the pair hosts, a profile is `{"model": "<model-id>", "effort": "<effort>"}`, passed as separate spawn arguments, and neither value may contain brackets. On `cursor`, the single-id host, a profile is `{"model": "<spawn-model-id>"}` with no `effort` field, passed as the spawn model. The id must be a listed spawn identifier that already encodes the effort, with no brackets. Do not store `<model-id>[effort=<effort>]`; live spawn rejects it.

On the single-id host, inspect the live spawn operation's listed identifiers and store one that encodes the chosen effort. Never store an id that carries no effort, because the worker would then run at the session effort.

`auto`, `inherit`, `inherit-parent`, an omitted model, an omitted effort on a pair host, and an id without effort on the single-id host are invalid profile values.

## 4. Find the transcript directory

Search the active host's documented state locations and the current repository metadata for its transcript directory. The candidate must be scoped to the canonical repository root. Confirm it by matching the opening user message from the current conversation in a recent transcript. Never glob across every workspace or save a global transcript root.

If no scoped directory can be confirmed, store `null` and say transcript-backed skills will use the visible conversation or user-supplied exports. Do not guess a provider path. If `hosts[<active-harness>].repositories[<canonical-repository-root>]` already exists, its `repository_root` exactly matches the canonical root, and its configured directory still matches this repository, keep it without searching again.

## 5. Reconcile and confirm

Run the configurator's `show` command. The configuration uses `schema_version` 3. If `show` reports an old schema version 2 config, stop and relay that error: do not migrate or rewrite the file yourself. The user deletes or rewrites `~/.dstack/config.json`, then reruns `setup-dstack`. Preserve other hosts. For the active host, when the catalog is complete, preserve model-effort pairs still present in the catalog, put unavailable former pairs in `invalid_bindings`, require a concrete replacement for every affected profile, and remove pairs that become valid again. When the catalog is partial, preserve existing concrete bindings and do not mark them invalid from the session spawn list alone. Never write a profile binding rejected by a complete catalog.

Show the current and proposed value for all four profiles, the active repository root and its transcript directory, invalid bindings, catalog status (`complete` or `partial`), and canonical harness id. Preserve every other harness and repository entry. Ask only about actual preferences. Do not write before the user confirms.

## 6. Apply

Create a temporary proposal with this exact shape:

```json
{
  "host": "<codex|claude|cursor>",
  "repository_root": "<canonical-repository-root>",
  "profiles": {
    "fast-explorer": <profile>,
    "feature-worker": <profile>,
    "bug-worker": <profile>,
    "skeptical-reviewer": <profile>
  },
  "invalid_bindings": <reconciled-invalid-bindings>,
  "transcripts_directory": <absolute-path-or-null>
}
```

Each `<profile>`, and each entry of `invalid_bindings`, uses the shape from step 3 for the active host.

```text
python3 <setup-dstack-dir>/scripts/configure.py apply --proposal <temporary-json>
```

Delete the temporary proposal after the command. If it fails, report the exact error and leave the previous file intact.

## 7. Report

Return the selected host, configuration path, profile changes, transcript discovery result, invalid bindings, catalog status, and schema validation result.

If the project lacks a real-app verification harness, offer once to create one. On acceptance, Call the Skill tool with `create-verification-skill`.

If the project lacks a formal verification skill (a project skill that runs a model checker, a proof, or another verifier against the code), offer once: "want a formal verification skill, so agents can prove a key property of your code holds in every case in scope, not only the cases tests reach? I can generate one with create-formal-verification-skill." On yes, tell the user to invoke `create-formal-verification-skill` explicitly. On no, move on without pushing.
