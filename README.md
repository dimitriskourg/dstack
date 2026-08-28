# dstack

dstack is a curated local adaptation of [pstack](https://github.com/cursor/plugins/tree/main/pstack) for Codex, Claude Code, and Cursor. It keeps retained skills and playbooks close to their source while excluding workflows that do not fit the team's local engineering practice.

The project is under active development. Configuration schema version 2 is intentionally stable while the pre-release shape changes.

## What ships

- All currently selected pstack-derived skills, renamed only where required: `poteto-mode` becomes `dstack-mode` and `setup-pstack` becomes `setup-dstack`.
- A curated 18-playbook `dstack-mode` focused on ordinary local engineering work.
- The external `control-cli`, `control-ui`, and `deslop` skills referenced by pstack.
- Host-neutral subagent instructions for harnesses that provide native subagent spawning.
- Four configurable profiles: `fast-explorer`, `feature-worker`, `bug-worker`, and `skeptical-reviewer`.
- Concrete model-and-effort bindings only; there is no parent-model or automatic fallback profile value.
- Transcript-backed workflows scoped to the canonical harness id and current repository root.
- A collision-safe installer and an atomic setup helper.

dstack has no capability matrix or provider adapter layer. Skills call other skills with this instruction:

```text
Call the Skill tool with `skill-name`.
```

Skills spawn helpers through the active harness's native subagent tool. If a nested spawn is denied, the current agent owns that work directly and reports the loss of independence or parallelism.

Read-only exploration, review, and independent artifacts outside the repository may fan out in bounded waves. Repository writers are serialized. Dstack does not create or manage worktrees, promise unattended persistence, automate merges, or require Graphite. Opening a pull request or merge request is explicit only.

## Layout

```text
skills/                 Portable skill packages
schemas/config.schema.json
install.py              Installer and managed update path
uninstall.py            Ownership-safe skills or full removal path
scripts/audit_portability.py
tests/
DIFFERENCES.md          Exact differences from pstack
```

Personal configuration lives at the fixed path `~/.dstack/config.json`. There is no environment or command-line override. Skills install canonically under `~/.agents/skills`. Claude Code requires the managed compatibility links under `~/.claude/skills`; Codex and Cursor use the canonical installation.

## Install

Preview first:

```bash
python3 install.py --dry-run
```

Install:

```bash
python3 install.py
```

For Claude Code use, install the required managed compatibility links:

```bash
python3 install.py --with-claude-links
```

Then explicitly invoke `setup-dstack` in the harness where you will use dstack. Setup maps the product identity to `codex`, `claude`, or `cursor`, discovers the current model catalog when possible, asks you to confirm the four profiles, records how that harness binds a worker to a model and effort pair, and saves the transcript directory beneath the canonical active-repository root.

Any skill that needs profiles or transcripts reads that file directly and maps the system-provided product identity to the fixed host id `codex`, `claude`, or `cursor`; aliases and host overrides are rejected. Transcript-backed skills also derive the canonical Git repository root and select only that repository entry. If the file is missing or invalid, either identity is unavailable, or a required entry is absent, the skill stops and tells you to run `setup-dstack`; it never falls back to another repository or silently inherits an unconfigured model or session effort. On a harness whose spawn call cannot carry both halves of a pair, setup generates one worker definition per profile so the effort is pinned before any worker starts.

## Uninstall

Remove only dstack skill packages and Claude compatibility links while preserving `~/.dstack` and generated worker definitions:

```bash
python3 uninstall.py --skills-only
```

Remove those skills plus generated dstack worker definitions and the complete `~/.dstack` directory:

```bash
python3 uninstall.py --all
```

Add `--dry-run` to either command to preview every removal. The uninstaller checks all discovered artifacts before deleting anything and stops if a same-named skill, Claude entry, or worker definition cannot be verified as dstack-owned. Unrelated skills and worker definitions are preserved.

## Validate

```bash
python3 scripts/audit_portability.py
python3 -m unittest discover -s tests -v
python3 -m json.tool schemas/config.schema.json >/dev/null
```

Validate every changed skill with Skill Creator's `quick_validate.py`. These are static checks. They do not prove browser, native, live-host, or multi-agent behavior.

See [the guide](docs/guide/README.md), [Supported scope](docs/guide/06-supported-scope.md), and [DIFFERENCES.md](DIFFERENCES.md) for usage and upstream alignment.
