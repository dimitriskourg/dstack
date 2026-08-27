---
name: setup-dstack
description: Configure dstack model-and-effort profiles and the active workspace transcript directory. Use for setup-dstack, changing profile assignments, or refreshing transcript discovery. Never invent model identifiers, effort support, or transcript paths.
disable-model-invocation: true
---

# Setup dstack

Use `~/.dstack/config.json` as the only configuration source. Its location is fixed; do not honor an environment override or accept another path. Use `scripts/configure.py` for validation and atomic config writes, and `scripts/worker_bindings.py` only for generated worker definitions. Do not create host rule files or edit installed skills.

## 1. Identify the host

Use the current system identity and tool surface to choose the lowercase id of the active harness. This id is always the configuration key; there is no override. If the active harness cannot be identified, stop and report that setup cannot safely choose a host entry.

## 2. Discover models

Use a trustworthy catalog exposed by the active host. Preserve exact model identifiers and the effort levels reported for each model. Never infer a slug or supported effort from a display name, example, another host, or memory.

When no catalog is available, preserve existing concrete bindings. For any unconfigured profile, ask the user for an exact model and effort pair without claiming validation. Do not write until all four profiles have concrete values.

Take the effort levels from the host's own enumeration of them. A host can accept an unknown effort value without complaint and then run the worker at the session effort, so an effort that the host does not enumerate is not a validated value; ask for a replacement instead of saving it.

The four profiles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `skeptical-reviewer`

`auto`, `inherit-parent`, an omitted model, and an omitted effort are invalid profile values.

## 3. Decide how the host binds workers

Inspect the current schema of the host's spawn operation instead of assuming it. Record the result in `worker_binding`.

- `spawn-arguments`: the spawn operation takes both a model and an effort argument, and `definitions_directory` is `null`.
- `worker-definitions`: the spawn operation cannot carry both values, so workers must be declared ahead of time in the host's own worker definition directory. Record that absolute directory in `definitions_directory`.

Choose `worker-definitions` whenever the spawn operation has no effort argument, even when it accepts a model. A spawn that carries only the model leaves the worker on the session effort and breaks the exact-pair contract.

## 4. Find the transcript directory

Search the active host's documented state locations and the current workspace metadata for its transcript directory. The candidate must be scoped to the active workspace. Confirm it by matching the opening user message from the current conversation in a recent transcript. Never glob across every workspace or save a global transcript root.

If no scoped directory can be confirmed, store `null` and say transcript-backed skills will use the visible conversation or user-supplied exports. Do not guess a provider path. If a configured directory already exists and still matches the active workspace, keep it without searching again.

## 5. Reconcile and confirm

Run the configurator's `show` command. Preserve other hosts. For the active host, preserve model-effort pairs still present in the catalog. Put unavailable former pairs in `invalid_bindings`, require a concrete replacement for every affected profile, and remove pairs that become valid again. Never write a profile binding rejected by the available catalog.

Show the current and proposed value for all four profiles, the worker binding mechanism and definitions directory, the transcript directory, invalid bindings, catalog status, and active harness id. Ask only about actual preferences. Do not write before the user confirms.

## 6. Apply

Create a temporary proposal with this exact shape:

```json
{
  "host": "<active-host>",
  "profiles": {
    "fast-explorer": {"model": "<model-id>", "effort": "<effort>"},
    "feature-worker": {"model": "<model-id>", "effort": "<effort>"},
    "bug-worker": {"model": "<model-id>", "effort": "<effort>"},
    "skeptical-reviewer": {"model": "<model-id>", "effort": "<effort>"}
  },
  "invalid_bindings": <reconciled-invalid-bindings>,
  "worker_binding": {"mechanism": "<spawn-arguments|worker-definitions>", "definitions_directory": <absolute-path-or-null>},
  "transcripts_directory": null
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

The command is a no-op for a `spawn-arguments` host. For a `worker-definitions` host, it synchronizes and confirms one definition per profile without touching other files in the directory. Treat a failure as a failed setup: report it and do not tell the user that profiles are ready.

## 7. Report

Return the selected host, configuration path, profile changes, worker binding mechanism, generated worker definitions and their verification result, transcript discovery result, invalid bindings, catalog status, and schema validation result.

If the project lacks a real-app verification harness, offer once to create one. On acceptance, Call the Skill tool with `create-verification-skill`.
