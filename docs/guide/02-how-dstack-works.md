# How dstack works

Skills are canonical under `~/.agents/skills`. Portable instructions live with each skill. There is no adapter or capability layer.

When one skill invokes another, it says: Call the Skill tool with `skill-name`. When a workflow delegates, it uses the active harness's native subagent tool. Model and effort selection comes from one of four profiles in the fixed file `~/.dstack/config.json`.

Transcript-backed skills map the system-provided product identity to `codex`, `claude`, or `cursor`, derive the canonical Git repository root, and read that repository entry's `transcripts_directory`. If the current checkout is a linked Git worktree, they select a registered checkout that shares `git rev-parse --git-common-dir` instead of requiring a second `setup-dstack` pass. The selected entry repeats its `repository_root`; a mismatch fails closed. Setup discovers and confirms the path once per harness and repository.

Config-dependent skills read the file themselves. They stop with an explicit `setup-dstack` instruction instead of guessing when the configuration, canonical host entry, or required repository entry is unavailable.

The active harness selects exactly one key under `hosts`: `codex`, `claude`, or `cursor`. The mapping comes from the system-provided product identity, not repository files, transcript paths, or user aliases. Unknown identities fail closed.

Profiles always resolve to concrete model-and-effort pairs. A skill stops if the harness rejects its configured pair; it never omits model selection to inherit the parent conversation.

Each profile holds exactly what the host's native spawn call takes. On `codex` and `claude`, a profile stores `model` and `effort`, and the skill passes them as separate spawn arguments. On `cursor`, a profile stores one `model` id that already carries the effort, either `id[effort=value]` or a listed spawn identifier that encodes the effort, and the skill passes it as the spawn model. Setup generates no worker definitions. An id or call without effort would leave the worker on the session effort, so the configurator rejects it.
