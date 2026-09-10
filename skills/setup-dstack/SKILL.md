---
name: setup-dstack
description: Configure dstack model-and-effort profiles and the active repository's transcript directory. Use for setup-dstack, changing profile assignments, or refreshing transcript discovery. Never invent model identifiers, effort support, or transcript paths.
disable-model-invocation: true
---

# Setup dstack

Use `~/.dstack/config.json` as the only configuration source. Its location is fixed; do not honor an environment override or accept another path. Use `scripts/configure.py` for validation and atomic config writes, and `scripts/worker_bindings.py` only for generated worker definitions. Do not create host rule files or edit installed skills.

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
- A fused spawn identifier, with model and effort in one string, is not a complete catalog. Do not store that string as `model`. Ask the user to confirm the model identifier and the effort as two values.
- If the spawn operation lists fewer models or efforts than the host's picker or a host models API, that list is partial: it is only what this session can pass as a spawn argument. Prefer a host models API or CLI that lists entitled models and their effort parameters when one exists. Otherwise ask the user for exact pairs. Never claim validation against a partial list.
- When the catalog is partial, preserve existing concrete bindings. Do not move a pair to `invalid_bindings` only because it is absent from this session's spawn list. Put a pair in `invalid_bindings` only when a complete catalog, or the host itself, rejects it.

When no catalog is available, preserve existing concrete bindings. For any unconfigured profile, ask the user for an exact model and effort pair without claiming validation. Do not write until all four profiles have concrete values.

Take the effort levels from the host's own enumeration of them. A host can accept an unknown effort value without complaint and then run the worker at the session effort, so an effort that the host does not enumerate is not a validated value; ask for a replacement instead of saving it.

The four profiles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `skeptical-reviewer`

`auto`, `inherit-parent`, an omitted model, and an omitted effort are invalid profile values. A fused spawn identifier is also invalid as a stored `model` or `effort` value.

## 3. Decide how the host binds workers

Inspect the current schema of the host's spawn operation instead of assuming it. Record the result in `worker_binding`.

- `spawn-arguments`: the spawn operation takes both a model and an effort argument, `definitions_directory` is `null`, and `pair_encoding` is `null`.
- `worker-definitions`: the spawn operation cannot carry both values, so workers must be declared ahead of time in the host's own worker definition directory. Record that absolute directory in `definitions_directory`. Inspect the definition schema and record `pair_encoding`:
  - `sibling-fields`: definitions have separate `model` and `effort` fields.
  - `model-brackets`: definitions have a `model` field that accepts `id[effort=value]` and no effort field. If the schema can refuse a parent spawn override of that model, set that refusal on every generated definition.

Choose `worker-definitions` whenever the spawn operation has no effort argument, even when it accepts a model. A spawn that carries only the model leaves the worker on the session effort and breaks the exact-pair contract. Do not reconstruct a fused spawn slug to compensate.

Do not choose an encoding from the harness id. Inspect the live spawn operation and definition schema. A host whose spawn call already carries both halves stays on `spawn-arguments` with `pair_encoding` null, including after this setup path changes.

## 4. Find the transcript directory

Search the active host's documented state locations and the current repository metadata for its transcript directory. The candidate must be scoped to the canonical repository root. Confirm it by matching the opening user message from the current conversation in a recent transcript. Never glob across every workspace or save a global transcript root.

If no scoped directory can be confirmed, store `null` and say transcript-backed skills will use the visible conversation or user-supplied exports. Do not guess a provider path. If `hosts[<active-harness>].repositories[<canonical-repository-root>]` already exists, its `repository_root` exactly matches the canonical root, and its configured directory still matches this repository, keep it without searching again.

## 5. Reconcile and confirm

Run the configurator's `show` command. Preserve other hosts. For the active host, when the catalog is complete, preserve model-effort pairs still present in the catalog, put unavailable former pairs in `invalid_bindings`, require a concrete replacement for every affected profile, and remove pairs that become valid again. When the catalog is partial, preserve existing concrete bindings and do not mark them invalid from the session spawn list alone. Never write a profile binding rejected by a complete catalog.

Show the current and proposed value for all four profiles, the worker binding mechanism, pair encoding, and definitions directory, the active repository root and its transcript directory, invalid bindings, catalog status (`complete` or `partial`), and canonical harness id. Preserve every other harness and repository entry. Ask only about actual preferences. Do not write before the user confirms.

## 6. Apply

Create a temporary proposal with this exact shape:

```json
{
  "host": "<codex|claude|cursor>",
  "repository_root": "<canonical-repository-root>",
  "profiles": {
    "fast-explorer": {"model": "<model-id>", "effort": "<effort>"},
    "feature-worker": {"model": "<model-id>", "effort": "<effort>"},
    "bug-worker": {"model": "<model-id>", "effort": "<effort>"},
    "skeptical-reviewer": {"model": "<model-id>", "effort": "<effort>"}
  },
  "invalid_bindings": <reconciled-invalid-bindings>,
  "worker_binding": {"mechanism": "<spawn-arguments|worker-definitions>", "definitions_directory": <absolute-path-or-null>, "pair_encoding": <null|"sibling-fields"|"model-brackets">},
  "transcripts_directory": <absolute-path-or-null>
}
```

```text
python3 <setup-dstack-dir>/scripts/configure.py apply --proposal <temporary-json>
```

Delete the temporary proposal after the command. If it fails, report the exact error and leave the previous file intact.

Then synchronize the workers:

```text
python3 <setup-dstack-dir>/scripts/worker_bindings.py --host <active-host>
```

The command is a no-op for a `spawn-arguments` host. For a `worker-definitions` host, it synchronizes and confirms one definition per profile, using the recorded `pair_encoding`, without touching other files in the directory. Treat a failure as a failed setup: report it and do not tell the user that profiles are ready.

## 7. Report

Return the selected host, configuration path, profile changes, worker binding mechanism, pair encoding, generated worker definitions and their verification result, transcript discovery result, invalid bindings, catalog status, and schema validation result.

If the project lacks a real-app verification harness, offer once to create one. On acceptance, Call the Skill tool with `create-verification-skill`.
