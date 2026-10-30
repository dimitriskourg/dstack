# dstack maintainer instructions

Read `PSTACK_SYNC.md` before changing skills or absorbing pstack. Absorb upstream with `scripts/pstack_sync.py`; never import a new pstack skill or playbook, or add host-specific text, without the owner's agreement.

For a sync review, follow the review checklist in `PSTACK_SYNC.md` and generate its read-only alignment report.

This project is under development. Keep schema version 3 unless the user explicitly asks for a compatibility boundary. Version 2 (the `worker_binding` era) is retired: configs on it fail with an instruction to delete or rewrite `~/.dstack/config.json` and rerun `setup-dstack`, with no automatic migration.

- Never edit pstack. Its upstream is [`cursor/plugins`](https://github.com/cursor/plugins/tree/main/pstack), subpath `pstack/`; `scripts/pstack_sync.py` fetches it read-only.
- Keep skills harness-neutral and close to pstack with the smallest justified edits.
- Use this exact instruction whenever one skill invokes another: Call the Skill tool with `skill-name`.
- Spawn subagents with the active harness's native subagent tool. If a nested spawn is denied, complete the pass in the current agent and disclose the degradation.
- Keep only the four profiles in `schemas/config.schema.json`: `fast-explorer`, `feature-worker`, `bug-worker`, `skeptical-reviewer`.
- Every profile must contain a concrete model and effort pair. Parent-model inheritance and automatic model aliases are not configuration options.
- Each host's profiles hold exactly what its native spawn call takes: `codex` and `claude` store `model` and `effort`, passed as separate spawn arguments; `cursor` stores one `model` id that carries the effort, passed as the spawn model. No worker definitions or generated worker files. A worker never inherits session effort.
- Read profiles and repository-scoped transcript directories only from `~/.dstack/config.json`. Map the system product identity to `codex`, `claude`, or `cursor`; transcript consumers also select and verify the canonical Git-root entry, or a registered checkout that shares its git common directory. The procedure lives only in `skills/dstack-config`; a skill that spawns or reads transcripts uses this exact line at the point of use: Call the Skill tool with `dstack-config`. It stops when the file or required entry is unavailable. Do not re-describe the procedure in any other skill.
- Do not recreate adapters, capability files, or provider-specific rules.
- Human-only skills declare `disable-model-invocation: true` and mirror it in `agents/openai.yaml` with `policy.allow_implicit_invocation: false`. A skill reached through the Skill tool omits both, because a model-disabled skill cannot be an internal callee. A human-only prerequisite is an instruction to the user, not a Skill-tool call.
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

## Pull requests

- One PR per pstack sync, never mixed with our own changes. Open as draft; the owner decides ready and merge.
- Titles stay under about 70 characters. Sync PRs: `sync: pstack <version> (<short commit>)`. Own changes: `<area>: <what changed>`, with area one of sync, config, skills, playbooks, setup, scripts, docs. Name any config-shape or version change in the title. Mark unfinished work as draft, never `WIP` in the title.
- Sync PR description: From and To commits with the pstack compare link; Applied, one line each; Decided, each item with the choice and a one-line why; Not imported, each new pstack skill declined, with the reason also recorded in `PSTACK_SYNC.md`; Checks.
- Own-change PR description: Why; What changed, user-visible first; pstack impact, whether it widens or narrows the diff and which `PSTACK_SYNC.md` rule covers it; Breaking; Checks, adding "static only; not tested in a live harness" when true.
