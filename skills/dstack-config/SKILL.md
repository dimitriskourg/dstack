---
name: dstack-config
description: "Resolve dstack configuration for a skill that is about to spawn a subagent or read transcripts. Returns the spawn values for one named profile, or this repository's transcripts directory, from ~/.dstack/config.json. Use when a dstack skill says to call dstack-config."
---

# dstack config

This is the only procedure for reading dstack configuration. The skill that spawns calls it before the spawn. A spawned worker does not call it to configure itself. Never write the file. Profile changes go through `setup-dstack`.

The caller names one profile (`fast-explorer`, `feature-worker`, `bug-worker`, or `skeptical-reviewer`) or asks for the transcripts directory.

## Resolve

1. Map the system-provided product identity to `codex`, `claude`, or `cursor`. Never invent an alias, derive the id from repository files or transcript paths, or select another host.
2. From the active checkout, resolve the repository entry and read the validated file:

```text
python3 <this-skill-dir>/../setup-dstack/scripts/configure.py resolve --host <active-harness>
python3 <this-skill-dir>/../setup-dstack/scripts/configure.py show
```

Read only `~/.dstack/config.json`, at `schema_version` 3. `configure.py resolve` takes the canonical repository root from `git rev-parse --show-toplevel` with symlinks resolved, selects `hosts[<active-harness>]` and `repositories[<canonical-repository-root>]`, and checks that the entry's `repository_root` exactly matches its key. When that key is absent, it selects the registered checkout that shares `git rev-parse --git-common-dir`. Never use a repository with a different git common directory.

3. If the file is missing, unreadable, invalid, or an old schema version 2 file, the identity is unknown, the host or repository entry is absent, the requested profile is missing, or its value is listed in `invalid_bindings`, stop and name the exact problem. Tell the user to invoke `setup-dstack` explicitly. Never guess, omit, or inherit a value.

## Return

For a profile, return `hosts[<active-harness>].profiles.<profile>` exactly as stored, and say how to pass it: on `codex` and `claude`, `model` and `effort` go as separate spawn arguments; on `cursor`, the `model` id, which already carries effort, goes as the spawn model. Every profile must provide a concrete model and effort pair. The caller never raises, lowers, or drops a value, and never inherits session effort. If the harness rejects the values, the caller stops and reports the rejected profile.

For the transcripts directory, return the resolved `transcripts_directory`. When it is `null`, say so, and the caller uses its own fallback.
