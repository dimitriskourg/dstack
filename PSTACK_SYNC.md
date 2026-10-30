# pstack sync

Pinned: pstack 0.15.36, commit `1ba91fc25c0977741dd0e267849e6234b037ed0a`.

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
- `comment-sicko`: dstack's comment reviewer.
- `control-ui`: dstack's local UI harness.
- `deslop`: dstack's code cleanup workflow.
- `dstack-config`: dstack's configuration reader.

Every `agents/openai.yaml` sidecar is also owned by dstack. The sync never touches these skills or sidecars.

## Mechanical rewrites

The script applies these on every absorb, to the pinned and target pstack text alike:

1. Paths: `poteto-mode`, `setup-pstack`, and `poteto-help` become `dstack-mode`, `setup-dstack`, and `dstack-help`.
2. Names: those three, then `poteto` and `pstack` in any case, become `dstack`.
3. Skill calls: a sentence that is only "Run, Use, Invoke, or Apply the **name** skill." and "→ the **name** skill." become "Call the Skill tool with `name`." Any other form needs a decision.
4. Frontmatter: drop the Cursor-only `disable-model-invocation`, `paths`, `icon`, and `color` keys. dstack keeps its own frontmatter.
5. Config: a skill keeps its one line "Call the Skill tool with `dstack-config`." where dstack placed it. A result that loses that line needs a decision.

## Maintained adaptations

- `interrogate` reuses Arena's process, not its runner selection. Choose reviewer profiles instead of Arena's runner rotation, always including `skeptical-reviewer`. This preserves upstream's separate `interrogate reviewers` selection using dstack's existing profiles.
- `statechart` is an internal callee: generated formal-verification skills call it through the standard Skill-tool instruction. Omit both `disable-model-invocation` and the sidecar's `allow_implicit_invocation` restriction. This differs from upstream's human-only setting so the generated workflow can run without another user invocation.

These notes explain the decisions; the skills own their instructions. Keep configuration resolution only in `skills/dstack-config`.

## Run it (weekly)

From the repository root, on a clean working tree:

```bash
python3 scripts/pstack_sync.py --dry-run           # report only; target defaults to origin main
python3 scripts/pstack_sync.py <commit>            # write clean changes; moves the pin on exit 0
python3 scripts/pstack_sync.py <commit> --decided  # after hand fixes; moves the pin to <commit>
```

A write run takes only a full commit: the Target the dry run printed. A dry run also takes a branch or tag. `--pstack-dir <folder>` reads a local pstack folder instead of fetching, for offline use only.

Exit 0: run the `AGENTS.md` gates and commit. Exit 1: the report shows, for each needs-decision item, pstack's change and the dstack lines it clashes with. Hand it to an agent to propose a fix per item, get the owner's approval, apply the approved fixes, then rerun with the same commit and `--decided`; those items are then listed as decided by hand.

## Inspect alignment (read-only)

The sync dry run compares two upstream commits. After the pin advances, comparing it to the same target is a no-op; it does not check dstack's alignment. To compare the whole retained tree to upstream, run:

```bash
python3 scripts/pstack_sync.py --check-alignment
python3 scripts/pstack_sync.py --check-alignment --format json --report /tmp/dstack-alignment.json
python3 scripts/pstack_sync.py <commit> --check-alignment
```

The default is the pinned commit, not upstream main. An explicit target lets you inspect a candidate without advancing the pin. `--pstack-dir` also works offline; the comparison reads the Git snapshot, not uncommitted upstream files.

The report separates byte-identical files, matches after mechanical rewrites, remaining differences, missing local files, and local-only files. It lists dstack-owned skills and sidecars, policy exclusions with their reasons, and upstream skills or playbooks not imported without a recorded exclusion. Dstack-owned entries are inventoried, not compared. A local-only file is not automatically an approved adaptation; it may have been deleted upstream.

Markdown shows the remaining normalized diffs. JSON also keeps raw diffs, relative source paths, and SHA-256 content hashes for a future side-by-side viewer. Binary files are compared by bytes and reported by hash, not normalized as text. Both formats use sorted paths and omit timestamps, so the same inputs produce the same output. Content comparison does not check executable permissions or prove behavior.

This mode never changes skills or the pin. It may fetch into the existing upstream cache and write an explicitly requested report outside the dstack and offline upstream source trees. It cannot be combined with `--dry-run` or `--decided`. Exit 0 means the report was generated, not that every difference is approved. Run the static gates separately.

## Review a sync

1. Record the PR head and merge base, plus the old and target upstream commits. Use those exact revisions throughout the review.
2. Compare upstream's change, dstack's PR diff, and the remaining difference from the target. Generate the alignment report; do not treat a sync no-op as alignment proof. Start with the adaptations rather than re-reviewing byte-identical imports.
3. For delegated workflows, check which profiles perform each job and which phases run or are skipped. Preserving a `dstack-config` call is not enough if the caller now selects the wrong profiles.
4. When a skill gains a dependency, check the target's frontmatter and sidecar together. An internal callee must be model-invokable and use the standard Skill-tool instruction. Check instructions emitted into generated skills too.
5. Label each finding as introduced by the port, inherited upstream, or an intentional adaptation. For every new non-obvious adaptation, record the choice and reason here; keep detailed instructions in the owning skill. Obtain approval for changes covered by Stop and ask.
6. Run the `AGENTS.md` gates and any relevant upstream tests. Separate static results from live-harness proof, and report skipped checks and environment-specific failures. Include the upstream compare link, decisions, and checks in the PR description.

## Stop and ask

- A new pstack skill or playbook.
- A change to an excluded skill or playbook that names a kept one, or a kept file that starts naming an excluded one.
- Host-specific tools, paths, or frontmatter.
- Spawn, model, effort, or config wording.
- A kept skill, playbook, or file renamed or deleted upstream.
- A change in or next to lines dstack already changed.
- Any change to a skill owned by dstack.

Everything else applies automatically.
