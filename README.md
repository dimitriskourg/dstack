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
- Transcript-backed workflows scoped to the active harness and current repository; the remaining configuration gap is tracked in `KNOWN_ISSUES.md`.
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

Then explicitly invoke `setup-dstack` in the harness where you will use dstack. Setup discovers the current model catalog when possible, asks you to confirm the four profiles, records how that harness binds a worker to a model and effort pair, finds the active workspace's transcript directory, and writes one host entry to `config.json`.

Any skill that needs profiles or transcripts reads that file directly and selects the entry matching the lowercase identity of the active harness. There is no host override. If the file is missing or invalid, the harness cannot be identified, or its host entry is absent, the skill stops and tells you to run `setup-dstack`; it does not guess or silently inherit an unconfigured model or session effort. On a harness whose spawn call cannot carry both halves of a pair, setup generates one worker definition per profile so the effort is pinned before any worker starts.

## Validate

```bash
python3 scripts/audit_portability.py
python3 -m unittest discover -s tests -v
python3 -m json.tool schemas/config.schema.json >/dev/null
```

Validate every changed skill with Skill Creator's `quick_validate.py`. These are static checks. They do not prove browser, native, live-host, or multi-agent behavior.

See [the guide](docs/guide/README.md), [Supported scope](docs/guide/06-supported-scope.md), and [DIFFERENCES.md](DIFFERENCES.md) for usage and upstream alignment.
