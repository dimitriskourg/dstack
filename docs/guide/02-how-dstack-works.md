# How dstack works

Skills are canonical under `~/.agents/skills`. Portable instructions live with each skill. There is no adapter or capability layer.

When one skill invokes another, it says: Call the Skill tool with `skill-name`. When a workflow delegates, it uses the active harness's native subagent tool. Model and effort selection comes from one of four profiles in the fixed file `~/.dstack/config.json`.

Transcript-backed skills read the active host entry's `transcripts_directory`. Setup discovers and confirms that workspace-scoped path once.

Config-dependent skills read the file themselves. They stop with an explicit `setup-dstack` instruction instead of guessing when the configuration or active host entry is unavailable.

The lowercase identity of the active harness is always the key under `hosts`; there is no override to another host's configuration.

Profiles always resolve to concrete model-and-effort pairs. A skill stops if the harness rejects its configured pair; it never omits model selection to inherit the parent conversation.
