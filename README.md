# dstack

dstack is a local adaptation of [pstack](https://github.com/cursor/plugins/tree/main/pstack) for Codex, Claude Code, and Cursor. It keeps a closed set of pstack skills and `dstack-mode` playbooks close to upstream, with harness-neutral wording: one skill calls another with "Call the Skill tool with `skill-name`.", and helpers spawn through the active harness's native subagent tool. [`PSTACK_SYNC.md`](PSTACK_SYNC.md) lists what is excluded and how weekly upstream changes are absorbed.

The project is under active development. Configuration is schema version 3; a version 2 file is not migrated, so delete or rewrite `~/.dstack/config.json` and rerun `setup-dstack`.

## Install

Skills install canonically under `~/.agents/skills`. Preview, then install:

```bash
python3 install.py --dry-run
python3 install.py
```

Claude Code also needs the managed compatibility links under `~/.claude/skills`:

```bash
python3 install.py --with-claude-links
```

To remove dstack, run `python3 uninstall.py --skills-only` to keep `~/.dstack`, or `python3 uninstall.py --all` to remove it too. Add `--dry-run` to preview. Unrelated skills are preserved.

## Set up

Invoke `setup-dstack` explicitly in each harness and repository where you use dstack. It maps the harness to `codex`, `claude`, or `cursor`, asks you to confirm four profiles (`fast-explorer`, `feature-worker`, `bug-worker`, `skeptical-reviewer`), each a concrete model and effort, and records this repository's transcript directory in `~/.dstack/config.json`. There is no environment or command-line override for that path.

Skills read the file only through the `dstack-config` skill, which stops and asks you to rerun `setup-dstack` when anything is missing.

Then start a task with `/dstack-mode`, a goal, and a check that can pass or fail. `/dstack-help` explains the rest of the pack.
