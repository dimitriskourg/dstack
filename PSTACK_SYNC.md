# pstack sync

Pinned: pstack 0.15.28, commit `d457567332aa6989e753ea289f30ea2bfbc80bc0`.

Upstream: <https://github.com/cursor/plugins/tree/main/pstack>. `scripts/pstack_sync.py` reads the pin and the lists below.

## Excluded skills

- `automate-me`: personal mode generation is out of this pack.
- `benchmark-checklist`: Explain the Number already covers a measured number.
- `figure-it-out`: large work splits into a kept playbook instead.
- `make-bot-ui`: provider-specific bot webhook, secrets, and Tailscale workflow.
- `show-me-your-work`: no separate decision-trail skill.
- `control-cli`: not bundled; there is no CLI or TUI harness.

## Excluded playbooks

- `autonomous-run`: unattended wake and persistence differ across hosts.
- `autopilot-full`: no autonomous parallel writers or automated merges.
- `autopilot-stack`: no autonomous execution or Graphite.
- `eval`: no blind skill-eval playbook.
- `hillclimb`: no sustained metric-loop playbook.
- `multi-phase-plan`: Feature or Refactoring cover split work.
- `orchestrate`: depends on the provider-specific runtime.
- `perf-issue`: no dedicated slowness playbook.
- `runtime-forensics`: Bug fix owns defects.
- `shipping`: Graphite-specific; Babysit stops at merge-ready.
- `trace-forensics`: Bug fix owns defects.
- `visual-parity`: Prototype and `control-ui` cover driving a UI.
- `worktree-cleanup`: dstack does not manage worktrees.

## Excluded files

- `poteto-mode/scripts/*`: Bun and TypeScript tooling for excluded playbooks.
- `poteto-mode/references/bugbot-triage.md`: replaced by `automated-review-triage.md`.

## Owned by dstack

- `setup-pstack`: `setup-dstack` and `dstack-config` replace its model setup.

`comment-sicko`, `control-ui`, `deslop`, `dstack-config`, and every `agents/openai.yaml` sidecar exist only in dstack. The sync never touches them.

## Mechanical rewrites

The script applies these on every absorb, to the pinned and target pstack text alike:

1. Paths: `poteto-mode`, `setup-pstack`, and `poteto-help` become `dstack-mode`, `setup-dstack`, and `dstack-help`.
2. Names: those three, then `poteto` and `pstack` in any case, become `dstack`.
3. Skill calls: a sentence that is only "Run, Use, Invoke, or Apply the **name** skill." and "→ the **name** skill." become "Call the Skill tool with `name`." Any other form needs a decision.
4. Frontmatter: drop the Cursor-only `disable-model-invocation`, `paths`, `icon`, and `color` keys. dstack keeps its own frontmatter.
5. Config: a skill keeps its one line "Call the Skill tool with `dstack-config`." where dstack placed it. A result that loses that line needs a decision.

## Weekly procedure

1. Update the read-only pstack checkout: `git -C <pstack> fetch` and pick the target commit.
2. Run `python3 scripts/pstack_sync.py <pstack> <commit> --dry-run` and read the report.
3. Run it again without `--dry-run`. Clean changes land in the working tree.
4. Exit 0 moves the pin. Run the `AGENTS.md` gates and commit.
5. Exit 1 leaves the pin. Settle each needs-decision item with Dimitris, edit by hand, then rerun with `--decided` to move the pin.

## Stop and ask

- A new pstack skill or playbook.
- A change to an excluded skill or playbook that names a kept one, or a kept file that starts naming an excluded one.
- Host-specific tools, paths, or frontmatter.
- Spawn, model, effort, or config wording.
- A kept skill, playbook, or file renamed or deleted upstream.
- A change in or next to lines dstack already changed.
- Any change to a skill owned by dstack.

Everything else applies automatically.

## Open

- Cursor bracket form (`id[effort=value]`) on `Task.model` is documented only for subagent frontmatter, so live proof that its effort sticks is still open.
