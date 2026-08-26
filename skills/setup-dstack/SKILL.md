---
name: setup-dstack
description: Configure dstack model-and-effort profiles and the active workspace transcript directory. Use for setup-dstack, changing profile assignments, or refreshing transcript discovery. Never invent model identifiers, effort support, or transcript paths.
disable-model-invocation: true
---

# Setup dstack

Read and write only `DSTACK_HOME/config.json`, defaulting `DSTACK_HOME` to `~/.dstack`. Use `scripts/configure.py` for validation and atomic writes. Do not create host rule files or edit installed skills.

## 1. Identify the host

Use the current system identity and tool surface to choose a lowercase host id. Set a persistent `host_override` only when the user asks. Otherwise retain `auto`.

## 2. Discover models

Use a trustworthy catalog exposed by the active host. Preserve exact model identifiers and the effort levels reported for each model. Never infer a slug or supported effort from a display name, example, another host, or memory.

When no catalog is available, preserve existing bindings, accept exact values supplied by the user without claiming validation, and use `inherit-parent` for unknowns.

The four profiles are:

- `fast-explorer`
- `feature-worker`
- `bug-worker`
- `skeptical-reviewer`

`{"model": "inherit-parent", "effort": "inherit-parent"}` is always valid.

## 3. Find the transcript directory

Search the active host's documented state locations and the current workspace metadata for its transcript directory. The candidate must be scoped to the active workspace. Confirm it by matching the opening user message from the current conversation in a recent transcript. Never glob across every workspace or save a global transcript root.

If no scoped directory can be confirmed, store `null` and say transcript-backed skills will use the visible conversation or user-supplied exports. Do not guess a provider path. If a configured directory already exists and still matches the active workspace, keep it without searching again.

## 4. Reconcile and confirm

Run the configurator's `show` command. Preserve other hosts. For the active host, preserve model-effort pairs still present in the catalog, list unavailable pairs in `invalid_bindings`, and remove pairs that become valid again.

Show the current and proposed value for all four profiles, the transcript directory, invalid bindings, catalog status, and host override. Ask only about actual preferences. Do not write before the user confirms.

## 5. Apply

Create a temporary proposal with this exact shape:

```json
{
  "host": "<active-host>",
  "profiles": {
    "fast-explorer": {"model": "inherit-parent", "effort": "inherit-parent"},
    "feature-worker": {"model": "inherit-parent", "effort": "inherit-parent"},
    "bug-worker": {"model": "inherit-parent", "effort": "inherit-parent"},
    "skeptical-reviewer": {"model": "inherit-parent", "effort": "inherit-parent"}
  },
  "invalid_bindings": [],
  "transcripts_directory": null
}
```

Include `host_override` only when the user explicitly changes it. Run:

```text
python3 <setup-dstack-dir>/scripts/configure.py apply --proposal <temporary-json>
```

Delete the temporary proposal after the command. If it fails, report the exact error and leave the previous file intact.

## 6. Report

Return the selected host, configuration path, profile changes, transcript discovery result, invalid bindings, catalog status, and schema validation result.

If the project lacks a real-app verification harness, offer once to create one. On acceptance, Call the Skill tool with `create-verification-skill`.
