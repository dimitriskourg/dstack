# dstack maintainer instructions

Read `DIFFERENCES.md` before changing skills, installation, model profiles, transcript handling, or upstream parity.

This project is under development. Keep schema version 2 unless the user explicitly asks for a compatibility boundary.

- Treat `/Users/kourgia/projects/plugins/pstack` and sibling plugin folders as immutable inputs.
- Keep skills harness-neutral and close to pstack with the smallest justified edits.
- Use this exact instruction whenever one skill invokes another: Call the Skill tool with `skill-name`.
- Spawn subagents with the active harness's native subagent tool. If a nested spawn is denied, complete the pass in the current agent and disclose the degradation.
- Keep only the four profiles documented in `DIFFERENCES.md`.
- Use the configured workspace-scoped transcript directory from `DSTACK_HOME/config.json`; do not search again from each skill.
- Do not recreate adapters, capability files, or provider-specific rules.
- Do not infer live-host proof from static validation.

Run the validation commands in `AGENTS.md` and validate every changed skill with Skill Creator's `quick_validate.py`.
