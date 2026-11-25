# pstack sync

Pinned: pstack 0.15.48, commit `9e278fe4d4ecd8bfe98b1b79bf4be662efb338cc`.

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
- Gemini 4 Neon panel pins from 0.15.44–0.15.45 (`gemini-4-neon-xhigh` in arena runners, cross-judge pool, interrogate reviewers, and setup-pstack defaults). dstack keeps four profiles from `~/.dstack/config.json` via `dstack-config`.
- Origin, watch-pr, and Bugbot text in Opening-a-PR / Babysit. dstack keeps gh/glab forge-neutral overlays and explicit-only Opening a PR.
- Cursor skill-install paths in reflect (`.cursor/skills/`, `plugins/cache/`). dstack keeps `~/.agents/skills/`.

## Kept dstack wording

These hand edits stay on every absorb. Reasons are one line each.

- `blast-radius` and `why` say "pull request or merge request" where pstack says "PR", because dstack supports GitHub and GitLab.
- `recall` step 4 says "Don't use a restricted read-only mode; where a host strips MCP access in that mode it disables MCP-backed investigators" where pstack says "in agent mode because readonly strips MCP access", because agent mode is Cursor-only.
- `dstack-mode/worker.md` adds one line after the stop rule: "Also stop for any external write the operator has not authorized: a push, a PR or MR, a ticket update, or a comment." dstack's Autonomy section requires explicit authorization for external writes, and pstack's stop rule does not cover them.

## Guide pages

`scripts/pstack_sync.py` maps pstack `docs/guide/` onto `dstack-help/references/guide/`, with `02-poteto-mode.md` as `02-dstack-mode.md`, and treats those pages like kept skills. `06-supported-scope.md` exists only in dstack. Pages dstack does not keep (03, 04, 05, 07, README, images) stay out; a brand-new upstream file is never copied.

## Allowed drift

Kept files that may differ from rewritten upstream at the pin. `--drift` and `--decided` treat backtick paths here, and in Not imported / Kept dstack wording / Owned by dstack, as listed. Any other kept skill, principle, playbook, or guide-page difference fails.

dstack-help (keep-set cheat sheet, excluded playbooks, bundled guide):

- `skills/dstack-help/SKILL.md`
- `skills/dstack-help/references/prompting.md`
- `skills/dstack-help/references/recipes.md`
- `skills/dstack-help/references/guide/01-setup.md`
- `skills/dstack-help/references/guide/02-dstack-mode.md`
- `skills/dstack-help/references/guide/06-verify-and-ship.md`
- `skills/dstack-help/references/guide/08-principles.md`
- `skills/dstack-help/references/guide/09-make-it-yours.md`
- `skills/dstack-help/references/guide/10-recipes-and-pitfalls.md`
- `skills/dstack-help/references/guide/06-supported-scope.md`

Four profiles, `dstack-config`, and native subagent spawn (not Opus-first / default-model routing):

- `skills/dstack-mode/SKILL.md`
- `skills/arena/SKILL.md`
- `skills/how/SKILL.md`
- `skills/interrogate/SKILL.md`
- `skills/swarm/SKILL.md`
- `skills/recall/SKILL.md`

Provider-neutral Skill-tool phrase, install path, and forge wording:

- `skills/architect/SKILL.md`
- `skills/blast-radius/SKILL.md`
- `skills/create-formal-verification-skill/SKILL.md`
- `skills/create-verification-skill/SKILL.md`
- `skills/ketchup/SKILL.md`
- `skills/maintain-verification-skill/SKILL.md`
- `skills/no-comments/SKILL.md`
- `skills/principle-explain-the-number/SKILL.md`
- `skills/reflect/SKILL.md`
- `skills/statechart/SKILL.md`
- `skills/technical-writing/SKILL.md`
- `skills/why/SKILL.md`

`worker.md` Autonomy overlay and playbook overlays (Skill-tool phrase, four profiles, gh/glab, explicit-only Opening a PR):

- `skills/dstack-mode/worker.md`
- `skills/dstack-mode/playbooks/authoring-a-skill.md`
- `skills/dstack-mode/playbooks/babysit.md`
- `skills/dstack-mode/playbooks/bug-fix.md`
- `skills/dstack-mode/playbooks/feature.md`
- `skills/dstack-mode/playbooks/investigation.md`
- `skills/dstack-mode/playbooks/opening-a-pr.md`
- `skills/dstack-mode/playbooks/pause-safely.md`
- `skills/dstack-mode/playbooks/prototype.md`
- `skills/dstack-mode/playbooks/refactoring.md`
- `skills/dstack-mode/playbooks/session-pickup.md`
- `skills/dstack-mode/references/automated-review-triage.md`

## Mechanical rewrites

The script applies these on every absorb, to the pinned and target pstack text alike:

1. Paths: `poteto-mode`, `setup-pstack`, and `poteto-help` become `dstack-mode`, `setup-dstack`, and `dstack-help`.
2. Names: those three, then `poteto` and `pstack` in any case, become `dstack`.
3. Skill calls: a sentence that is only "Run, Use, Invoke, or Apply the **name** skill." and "→ the **name** skill." become "Call the Skill tool with `name`." Any other form needs a decision.
4. Frontmatter: drop the Cursor-only `disable-model-invocation`, `paths`, `icon`, and `color` keys. dstack keeps its own frontmatter.
5. Config: a skill keeps its one line "Call the Skill tool with `dstack-config`." where dstack placed it. A result that loses that line needs a decision.

## Run it (weekly)

From the repository root, on a clean working tree. Copy upstream wording verbatim on kept files. Record every skip or kept-dstack choice in the sync PR description and in this file (never only in private notes). Paste `--drift` output into every sync PR.

```bash
python3 scripts/pstack_sync.py --drift             # kept files vs rewritten upstream at the pin
python3 scripts/pstack_sync.py --dry-run           # report only; target defaults to origin main
python3 scripts/pstack_sync.py <commit>            # write clean changes; moves the pin on exit 0
python3 scripts/pstack_sync.py <commit> --decided  # after hand fixes; moves the pin only if settled
```

A write run takes only a full commit: the Target the dry run printed. A dry run also takes a branch or tag. `--pstack-dir <folder>` reads a local pstack folder instead of fetching, for offline use only.

`--decided` does not move the pin unless every pending file either matches rewritten upstream at the target commit or is listed under Not imported / Kept dstack wording / Allowed drift.

Exit 0: run the `AGENTS.md` gates and commit. Exit 1: the report shows, for each needs-decision item, pstack's change and the dstack lines it clashes with, or `--drift` names an unlisted difference, or `--decided` refused the pin. Hand needs-decision items to an agent to propose a fix per item, get the owner's approval, apply the approved fixes, list each skip or kept-dstack choice here, then rerun with the same commit and `--decided`.

Before marking a sync PR ready, a separate reviewer (a strong model, not the absorb agent) reviews it using the pasted drift output. Open sync PRs as draft until that review lands. The owner decides ready and merge.

## Stop and ask

- A new pstack skill, playbook, guide page, or any other new upstream file. Never auto-copy. Check dstack rules: no unauthorized push, PR, ticket, or comment (including a `worker.md` Autonomy overlay when the file is a subagent brief).
- A change to an excluded skill or playbook that names a kept one, or a kept file that starts naming an excluded one.
- Host-specific tools, paths, or frontmatter.
- Spawn, model, effort, or config wording.
- A kept skill, playbook, guide page, or file renamed or deleted upstream.
- A change in or next to lines dstack already changed.
- Any change to a skill owned by dstack.

Everything else applies automatically.
