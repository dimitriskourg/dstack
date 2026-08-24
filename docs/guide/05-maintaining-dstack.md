# Maintain dstack and sync pstack

This page is for repository maintainers. Read
[`REMAINING.md`](../../REMAINING.md) for the authoritative baseline, intentional
exclusions, and deferred work.

## Start every change with the baseline

```bash
python3 scripts/audit_portability.py
python3 -m unittest discover -s tests -v
```

Inspect the worktree before editing and preserve unrelated changes. Static
checks establish a baseline; they do not prove live host behavior.

## Put changes in the owning layer

| Change | Owning location |
| --- | --- |
| Portable workflow behavior | `skills/` |
| Host operation mapping | `adapters/` |
| Stable semantic capability | `contracts/` |
| Strict persisted shape | `schemas/` |
| Deterministic repeated operation | bundled or root script |
| Upstream delta and deferred scope | `REMAINING.md` |

Do not solve an adapter problem by placing provider syntax in every skill.

## Sync a new pstack version

1. Obtain the upstream pstack repository.
2. Record the exact old and new commit SHAs and plugin versions.
3. Review the upstream diff before copying files.
4. Inventory skills, playbooks, agents, scripts, docs, and automations
   separately.
5. Classify each change as portable behavior, adapter behavior, deterministic
   runtime, documentation, or excluded provider automation.
6. Port behavior rather than mechanically replacing provider names.
7. Preserve dstack's intentional renames and lack of legacy aliases.
8. Run the audit, unit tests, and changed-skill validation.
9. Exercise affected workflows on live hosts.
10. Update `REMAINING.md` with the new baseline and every explained difference.

Reject these from portable skills:

- provider-specific skill and configuration paths;
- provider tool-call schemas;
- concrete model slugs;
- private transcript directory assumptions;
- cloud, wake, or persistent-mode assumptions without fallbacks;
- unsupported frontmatter (`disable-model-invocation` is supported; see
  `docs/agents/invocation.md`);
- references to missing assets, scripts, or sibling skills.

## Keep static and live evidence separate

The audit, the unit tests, and a successful install prove repository structure
and deterministic helpers. They do not prove a skill behaves correctly on Codex,
Cursor, or Claude Code. Only running it there does.

Never describe a host as conformant on the strength of a static check.

## What dstack does not ship

Excluded by decision, recorded with reasons in
[REMAINING.md](../../REMAINING.md):

- Pstack's Orchestrate playbook and its `orch` runtime.
- The bundled PR watcher. Babysit asks the forge for the merge verdict directly.
- The Bun toolchain those two required.
- Pstack's `poteto-agent` wrapper.

Deferred until a concrete need appears:

- General repair, doctor, uninstall, and ownership hashes. The explicit update
  mode only refreshes a verified existing dstack topology from a trusted
  checkout; it is not a package manager or repair tool.
- Migrations beyond the implemented schema version 1 to version 2 conversion.
- Stronger history, transcript, and wake classifications until live evidence
  supports them.

When one of these becomes necessary, begin with the concrete failure or user
need. Do not import the full source implementation merely for file parity.

## ystack

ystack is a valuable portability reference. Reinspect its latest revision before
using it: the recorded 2026-08-09 snapshot had strong audits and adapter ideas
but a different installation architecture.
Retain MIT attribution for adapted code and avoid importing legacy aliases or
mirrored provider trees by accident.
