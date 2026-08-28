# dstack maintainer instructions

Read `DIFFERENCES.md` before changing skills, installation, model profiles, transcript handling, or upstream parity.

This project is under development. Keep schema version 2 unless the user explicitly asks for a compatibility boundary.

- Treat `/Users/kourgia/projects/plugins/pstack` and sibling plugin folders as immutable inputs.
- Keep skills harness-neutral and close to pstack with the smallest justified edits.
- Use this exact instruction whenever one skill invokes another: Call the Skill tool with `skill-name`.
- Spawn subagents with the active harness's native subagent tool. If a nested spawn is denied, complete the pass in the current agent and disclose the degradation.
- Keep only the four profiles documented in `DIFFERENCES.md`.
- Every profile must contain a concrete model and effort pair. Parent-model inheritance and automatic model aliases are not configuration options.
- Both halves of a pair must reach the worker through the host entry's `worker_binding`. A worker never inherits session effort.
- Read profiles and repository-scoped transcript directories only from `~/.dstack/config.json`. Map the system product identity to `codex`, `claude`, or `cursor`; transcript consumers also select and verify the canonical Git-root entry. Config-dependent skills stop when the file or required entry is unavailable.
- Do not recreate adapters, capability files, or provider-specific rules.
- Do not infer live-host proof from static validation.

## Validation

Run these static gates from the repository root:

```bash
python3 scripts/audit_portability.py
python3 -m unittest discover -s tests -v
python3 -m json.tool schemas/config.schema.json >/dev/null
git diff --check
```

These commands validate repository structure and static contracts. They do not prove discovery, nested invocation, model-and-effort enforcement, fan-out, forge behavior, or end-to-end behavior in a live harness.
