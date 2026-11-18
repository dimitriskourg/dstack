# pstack sync

Pinned: pstack 0.15.43, commit `2f87c854fe3e2fcda44ca86b46ede35aad3c46b7`.

Upstream: repository `cursor/plugins`, subpath `pstack/` (<https://github.com/cursor/plugins/tree/main/pstack>). Never edit pstack. `scripts/pstack_sync.py` shallow-fetches the pinned and target commits itself and reads the pin and the lists below.

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

## Not imported

These pstack items stay out of dstack. Reasons are one line each.

- Default-model / Opus-first routing from 0.15.43 (`claude-opus-5-5-xhigh-fast`, Fable-as-exception, no role above xhigh, setup-pstack `# defaults: 3`). dstack keeps four profiles from `~/.dstack/config.json` via `dstack-config`.
- Origin, watch-pr, and Bugbot text in Opening-a-PR / Babysit. dstack keeps gh/glab forge-neutral overlays and explicit-only Opening a PR.
- Cursor skill-install paths in reflect (`.cursor/skills/`, `plugins/cache/`). dstack keeps `~/.agents/skills/`.

## Kept dstack wording

These hand edits stay on every absorb. Reasons are one line each.

- `blast-radius` and `why` say "pull request or merge request" where pstack says "PR", because dstack supports GitHub and GitLab.
- `recall` step 4 says "Don't use a restricted read-only mode; where a host strips MCP access in that mode it disables MCP-backed investigators" where pstack says "in agent mode because readonly strips MCP access", because agent mode is Cursor-only.

## Guide pages

`dstack-help/references/guide/` copies the pstack `docs/guide/` pages of the same name by hand, with `02-poteto-mode.md` as `02-dstack-mode.md`. `06-supported-scope.md` exists only in dstack. The script does not read `docs/`, so port changes to these pages by hand on each absorb, with the mechanical rewrites applied.

## Mechanical rewrites

The script applies these on every absorb, to the pinned and target pstack text alike:

1. Paths: `poteto-mode`, `setup-pstack`, and `poteto-help` become `dstack-mode`, `setup-dstack`, and `dstack-help`.
2. Names: those three, then `poteto` and `pstack` in any case, become `dstack`.
3. Skill calls: a sentence that is only "Run, Use, Invoke, or Apply the **name** skill." and "→ the **name** skill." become "Call the Skill tool with `name`." Any other form needs a decision.
4. Frontmatter: drop the Cursor-only `disable-model-invocation`, `paths`, `icon`, and `color` keys. dstack keeps its own frontmatter.
5. Config: a skill keeps its one line "Call the Skill tool with `dstack-config`." where dstack placed it. A result that loses that line needs a decision.

## Run it (weekly)

From the repository root, on a clean working tree:

```bash
python3 scripts/pstack_sync.py --dry-run           # report only; target defaults to origin main
python3 scripts/pstack_sync.py <commit>            # write clean changes; moves the pin on exit 0
python3 scripts/pstack_sync.py <commit> --decided  # after hand fixes; moves the pin to <commit>
```

A write run takes only a full commit: the Target the dry run printed. A dry run also takes a branch or tag. `--pstack-dir <folder>` reads a local pstack folder instead of fetching, for offline use only.

Exit 0: run the `AGENTS.md` gates and commit. Exit 1: the report shows, for each needs-decision item, pstack's change and the dstack lines it clashes with. Hand it to an agent to propose a fix per item, get the owner's approval, apply the approved fixes, then rerun with the same commit and `--decided`; those items are then listed as decided by hand.

## Stop and ask

- A new pstack skill or playbook.
- A change to an excluded skill or playbook that names a kept one, or a kept file that starts naming an excluded one.
- Host-specific tools, paths, or frontmatter.
- Spawn, model, effort, or config wording.
- A kept skill, playbook, or file renamed or deleted upstream.
- A change in or next to lines dstack already changed.
- Any change to a skill owned by dstack.

Everything else applies automatically.
