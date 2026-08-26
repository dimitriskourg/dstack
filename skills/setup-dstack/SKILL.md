---
name: setup-dstack
description: Configure dstack model-and-effort profiles and the active workspace transcript directory. Use for setup-dstack, changing profile assignments, or refreshing transcript discovery. Never invent model identifiers, effort support, or transcript paths.
disable-model-invocation: true
---

# Setup dstack

Read and write only `~/.dstack/config.json`. This location is fixed; do not honor an environment override or accept another path. Use `scripts/configure.py` for validation and atomic writes. Do not create host rule files or edit installed skills.

## 1. Identify the host

Use the current system identity and tool surface to choose the lowercase id of the active harness. This id is always the configuration key; there is no override. If the active harness cannot be identified, stop and report that setup cannot safely choose a host entry.

## 2. Discover models

Use a trustworthy catalog exposed by the active host. Preserve exact model identifiers and the effort levels reported for each model. Never infer a slug or supported effort from a display name, example, another host, or memory.

When no catalog is available, preserve existing concrete bindings. For any unconfigured profile, ask the user for an exact model and effort pair without claiming validation. Do not write until all four profiles have concrete values.

The four profiles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `skeptical-reviewer`

`auto`, `inherit-parent`, an omitted model, and an omitted effort are invalid profile values.

## 3. Find the transcript directory

Search the active host's documented state locations and the current workspace metadata for its transcript directory. The candidate must be scoped to the active workspace. Confirm it by matching the opening user message from the current conversation in a recent transcript. Never glob across every workspace or save a global transcript root.

If no scoped directory can be confirmed, store `null` and say transcript-backed skills will use the visible conversation or user-supplied exports. Do not guess a provider path. If a configured directory already exists and still matches the active workspace, keep it without searching again.

## 4. Reconcile and confirm

Run the configurator's `show` command. Preserve other hosts. For the active host, preserve model-effort pairs still present in the catalog. Put unavailable former pairs in `invalid_bindings`, require a concrete replacement for every affected profile, and remove pairs that become valid again. Never write a profile binding rejected by the available catalog.

Show the current and proposed value for all four profiles, the transcript directory, invalid bindings, catalog status, and active harness id. Ask only about actual preferences. Do not write before the user confirms.

## 5. Apply

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
  "invalid_bindings": [],
  "transcripts_directory": null
}
```

```text
python3 <setup-dstack-dir>/scripts/configure.py apply --proposal <temporary-json>
```

Delete the temporary proposal after the command. If it fails, report the exact error and leave the previous file intact.

## 6. Report

Return the selected host, configuration path, profile changes, transcript discovery result, invalid bindings, catalog status, and schema validation result.

If the project lacks a real-app verification harness, offer once to create one. On acceptance, Call the Skill tool with `create-verification-skill`.
