# How dstack works

Skills are canonical under `~/.agents/skills`. Portable instructions live with each skill. There is no adapter or capability layer.

When one skill invokes another, it says: Call the Skill tool with `skill-name`. When a workflow delegates, it uses the active harness's native subagent tool. Model and effort selection comes from one of four profiles in `DSTACK_HOME/config.json`.

Transcript-backed skills read the active host entry's `transcripts_directory`. Setup discovers and confirms that workspace-scoped path once.
