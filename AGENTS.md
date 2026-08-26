# dstack maintainer instructions

Read `DIFFERENCES.md` before changing skills, installation, model profiles, transcript handling, or upstream parity.

This project is under development. Keep schema version 2 unless the user explicitly asks for a compatibility boundary.

- Treat `/Users/kourgia/projects/plugins/pstack` and sibling plugin folders as immutable inputs.
- Keep skills harness-neutral and close to pstack with the smallest justified edits.
- Use this exact instruction whenever one skill invokes another: Call the Skill tool with `skill-name`.
- Spawn subagents with the active harness's native subagent tool. If a nested spawn is denied, complete the pass in the current agent and disclose the degradation.
- Keep only the four profiles documented in `DIFFERENCES.md`.
- Every profile must contain a concrete model and effort pair. Parent-model inheritance and automatic model aliases are not configuration options.
- Read profiles and the workspace-scoped transcript directory only from `~/.dstack/config.json`. The location is fixed. Config-dependent skills stop when it or the active host entry is unavailable.
- Do not recreate adapters, capability files, or provider-specific rules.
- Do not infer live-host proof from static validation.

Run the validation commands in `AGENTS.md` and validate every changed skill with Skill Creator's `quick_validate.py`.
