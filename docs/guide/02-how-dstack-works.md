# How dstack works

Skills are canonical under `~/.agents/skills`. Portable instructions live with each skill. There is no adapter or capability layer.

When one skill invokes another, it says: Call the Skill tool with `skill-name`. When a workflow delegates, it uses the active harness's native subagent tool. Model and effort selection comes from one of four profiles in the fixed file `~/.dstack/config.json`.

Transcript-backed skills map the system-provided product identity to `codex`, `claude`, or `cursor`, derive the canonical Git repository root, and read only that repository entry's `transcripts_directory`. The entry repeats its `repository_root`; a mismatch fails closed. Setup discovers and confirms the path once per harness and repository.

Config-dependent skills read the file themselves. They stop with an explicit `setup-dstack` instruction instead of guessing when the configuration, canonical host entry, or required repository entry is unavailable.

The active harness selects exactly one key under `hosts`: `codex`, `claude`, or `cursor`. The mapping comes from the system-provided product identity, not repository files, transcript paths, or user aliases. Unknown identities fail closed.

Profiles always resolve to concrete model-and-effort pairs. A skill stops if the harness rejects its configured pair; it never omits model selection to inherit the parent conversation.

How a pair reaches a worker depends on the host entry's `worker_binding`. With `spawn-arguments`, the skill passes the model and effort in the spawn call. With `worker-definitions`, setup has already generated one worker per profile, named `dstack-<profile>`, and the skill spawns that worker without a per-spawn override. The second mechanism exists because a spawn call that carries only a model leaves the worker on the session effort, which silently breaks the exact-pair contract.
