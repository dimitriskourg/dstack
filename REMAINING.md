# dstack maintainer handoff

Updated 2026-08-17. Read this before changing portability contracts, porting a
new pstack release, or claiming live host support.

## Objective

dstack is a provider-neutral adaptation of Cursor pstack. Its canonical skill
installation is `~/.agents/skills`; its personal configuration, adapters,
contracts, schemas, and optional runtime live under `DSTACK_HOME` (default
`~/.dstack`).

The project favors a small initial product:

- a collision-safe first installer, not a package manager;
- one strict version-1 JSON configuration, not a migration framework;
- portable skills with explicit fallbacks, not simulated provider parity;
- static checks separated from live host proof.

## Recorded upstream baselines

### pstack

- Repository: <https://github.com/cursor/plugins/tree/main/pstack>
- Cursor plugin version inspected: `0.14.1`
- Source repository commit inspected:
  `63d938c2e4a165a0fec1bd0f61a8e325f0cb751e`
- Commit date: 2026-08-13
- Inventory at that baseline: 44 skills and 23 `poteto-mode` playbooks.

The local migration source was `/Users/kourgia/projects/plugins/pstack`, but a
future agent must not assume that path exists. Clone or otherwise obtain the
upstream repository and record the exact revision used.

### ystack

- Repository: <https://github.com/Go7hic/ystack>
- Revision previously inspected:
  `fcc4b42b4968b4dbd912d6d9539b75e24688fef9`
- Inspection date: 2026-08-09

ystack informed the capability vocabulary, adapter separation, semantic model
roles, privacy treatment, and portability audit. It is a reference, not an
upstream compatibility target. Reinspect its current revision before borrowing
new ideas or code.

## What is implemented

### Portable content

- All 44 pstack skill names have dstack counterparts.
- `poteto-mode` is renamed `dstack-mode`.
- `setup-pstack` is renamed `setup-dstack`.
- `comment-sicko` is an additional normal skill, bringing the total to 45.
- `dstack-mode` contains 22 portable playbooks.
- The only missing pstack playbook is `orchestrate.md`, intentionally deferred.
- No legacy `pstack`, `poteto-mode`, or `setup-pstack` aliases are planned.

### Portability layer

- `contracts/capabilities.md` defines workflow, agent lifecycle, session, wake,
  and semantic-model capabilities plus required parent fallbacks.
- `contracts/host-selection.md` defines host-selection precedence.
- `adapters/` contains Codex, Cursor, Claude Code, and generic classifications.
- Skills request semantic roles rather than concrete provider model slugs.
- Session workflows use authorized first-class history, explicit transcript
  inputs, visible conversation, and repository evidence. They do not scan
  private provider history directories.

### Installation and configuration

- `install.py` previews a complete plan with `--dry-run`.
- It installs skills into `~/.agents/skills` and support files into
  `DSTACK_HOME`.
- Optional `--with-claude-links` creates one link per skill under
  `~/.claude/skills`; it never replaces that directory.
- Any destination collision stops the complete first installation.
- `setup-dstack/scripts/configure.py` provides `show`, `validate`, and atomic
  `apply` operations for `DSTACK_HOME/config.json`.
- Codex and Cursor mappings coexist; updating one host preserves the others.
- Missing configuration resolves every role to `inherit-parent`.

### Validation

At this handoff:

```text
python3 scripts/audit_portability.py
dstack portability audit: 0 error(s)

python3 -m unittest discover -s tests -v
Ran 20 tests
OK

Skill Creator validation
45 of 45 skill packages valid
```

JSON syntax and Python compilation also passed. These are static results, not
live host proof.

## Exact differences still missing from pstack

### 1. Orchestrate runtime and playbook — deferred TODO

Pstack ships a project-scale coordination playbook and a tested TypeScript
plain-file store. dstack does not currently ship either.

Relevant pstack source files at the recorded baseline:

```text
pstack/skills/poteto-mode/playbooks/orchestrate.md
pstack/skills/poteto-mode/scripts/bootstrap.ts
pstack/skills/poteto-mode/scripts/package.json
pstack/skills/poteto-mode/scripts/bun.lock
pstack/skills/poteto-mode/scripts/orch/orch.ts
pstack/skills/poteto-mode/scripts/orch/store.ts
pstack/skills/poteto-mode/scripts/orch/orch.test.ts
```

The runtime manages durable bookkeeping only: units, standing orders, an inbox,
human gates, verification verdicts keyed by PR plus exact SHA, stack frontier,
locking, recovery, and derived status. It must never pretend to spawn, wait for,
resume, or wake agents; adapters own those operations.

If ported later:

1. Put runtime source under `runtime/orchestrate/` and installed runtime under
   `DSTACK_HOME/runtime/orchestrate/`.
2. Put program state under
   `DSTACK_HOME/orchestrate/<workspace-id>/<program-id>/`.
3. Replace Cursor store paths, Task schemas, cloud-only assumptions, private
   transcript paths, and mandatory Graphite behavior with capabilities and
   explicit fallbacks.
4. Require Bun explicitly if TypeScript remains. Never install Bun silently.
5. Prefer removing the `commander` dependency; otherwise require an explicit
   dependency installation instead of pstack's silent first-use bootstrap.
6. Keep the CLI deterministic and compact; the coordinator retains judgment.
7. Port and extend the source tests before adding `orchestrate.md` to
   `dstack-mode`.
8. Add live scenarios for initialization, lock recovery, inbox draining, gates,
   SHA invalidation, frontier updates, and restart recovery.

Do not route normal single-session work through Orchestrate. It is intended only
for multi-day programs with many units and PRs.

### 2. PR watcher — deferred, not required

Pstack's `watch-pr/` runtime is not present. The portable Babysit playbook uses
an existing repository watcher when one exists, otherwise bounded forge
polling.

Before porting, make these configurable:

- forge and authentication behavior;
- automated-review bot identities;
- stack discovery and Graphite assumptions;
- polling interval, timeout, and wake behavior;
- policy for comments, CI, conflicts, and stale heads.

Do not port it merely to claim file parity. Port it only when live use shows the
fallback is insufficient.

### 3. Worktree audit helper — intentionally excluded

Pstack's helper inspects a private Cursor transcript layout. dstack's Worktree
cleanup playbook instead derives candidates from
`git worktree list --porcelain` and permits only authorized first-class session
evidence.

A future deterministic helper may inventory worktrees, disk use, merge state,
and uncommitted files. It must not infer ownership by scanning private history.

### 4. Benny automation — intentionally excluded

`pstack/automations/benny/` depends on Cursor Automations, provider UI, Slack
actions, cloud checkouts, and provider configuration. It is not part of dstack's
portable skill scope.

### 5. Provider wrappers and defaults — intentionally transformed

These are differences, not missing work:

- Pstack's provider-registered agent wrappers were absorbed into portable skill
  behavior and adapter instructions.
- Concrete default model identifiers were replaced by semantic roles and
  `inherit-parent`.
- Provider-specific rule files were replaced by central `config.json`.
- Generated verification skills default to `~/.agents/skills`, with
  project-local output only when explicitly requested.

Do not reintroduce these source shapes for superficial parity.

## Remaining release proof

### Live conformance

`conformance/HOST_MATRIX.md` is intentionally empty until scenarios are
actually exercised. At minimum test Codex and Cursor:

- simple `how` avoids unnecessary fan-out;
- complex `how` uses bounded explorers when supported;
- denied spawn collapses to the parent and is disclosed;
- denied model selection inherits the parent;
- model configuration for Codex and Cursor coexists in `config.json`;
- panels resolve semantic roles to the active host only;
- independent review remains genuinely separate when supported;
- write workers have disjoint scopes or serialization;
- session/history and wake gaps degrade exactly as documented;
- installer dry run and first installation work on the real target paths.

Record `pass`, `pass-degraded:<reason>`, or `fail:<reason>` only from live
exercise. Tests, builds, successful copies, and static audits are separate
evidence.

### Minimal installer limitations

The initial installer deliberately has no overwrite, update, repair, uninstall,
ownership-hash, or doctor workflow. A configuration migration engine is also
deferred until schema version 2 exists.

Do not add this machinery speculatively. If real use demands updates, first
define ownership and collision behavior against actual installations.

### Adapter classifications

`session.history` and `session.transcript` are conservatively unavailable in
baseline adapters. `runtime.wake` is tentatively native only for Cursor. Live
inspection may justify changing those cells; static documentation does not.

## How to sync a future pstack release

Treat upstream as immutable input and make the comparison reproducible.

1. Obtain the current pstack repository.
2. Record its repository URL, plugin version, commit SHA, and commit date above.
3. Diff the recorded baseline SHA against the new SHA before copying anything.
4. Inventory skill names, playbooks, agent wrappers, scripts, docs, and
   automations separately.
5. Classify each upstream change as:
   - portable skill behavior;
   - provider-specific adapter behavior;
   - deterministic local runtime;
   - documentation;
   - intentionally excluded provider automation.
6. Port behavior, not provider call syntax. Never mechanically replace provider
   names inside prompts or tool schemas.
7. Preserve the deliberate renames and the absence of compatibility aliases.
8. Reject concrete model slugs, provider skill/config paths, private transcript
   layouts, unsupported frontmatter, and capability assumptions without a
   fallback.
9. Update tests and `scripts/audit_portability.py` when the portable contract
   gains a real new invariant.
10. Run static validation, then exercise affected flows on live hosts.
11. Update this baseline and the exact difference list in the same change.

Useful inventory commands when pstack is available as `<pstack-dir>`:

```bash
find <pstack-dir>/skills -mindepth 1 -maxdepth 1 -type d -print | sort
find skills -mindepth 1 -maxdepth 1 -type d -print | sort
find <pstack-dir>/skills/poteto-mode/playbooks -maxdepth 1 -type f -print | sort
find skills/dstack-mode/playbooks -maxdepth 1 -type f -print | sort
```

After a sync, require zero unexplained skill-name differences. Playbook and
runtime differences must be either ported or listed explicitly in this file.

## Short note about ystack

The previously inspected ystack revision had strong portability audits,
adapter references, semantic model overrides, and privacy guidance. It did not
provide dstack's desired canonical `~/.agents/skills` ownership, central
configuration, safe collision contract, or a working Orchestrate runtime; its
Orchestrate playbook referenced runtime files that were not shipped at that
revision.

Do not treat those observations as current facts. Reinspect the latest ystack
revision. Retain its MIT attribution when adapting code rather than concepts,
and avoid importing its legacy pstack aliases or mirrored provider trees unless
dstack deliberately changes its architecture.

## Cold-start checklist for the next agent

1. Read `README.md`, this file, `contracts/capabilities.md`, and
   `contracts/host-selection.md`.
2. Run the portability audit and all unit tests before editing.
3. Confirm the worktree is clean and preserve unrelated changes.
4. Identify whether the task changes portable behavior, an adapter, local
   runtime, installation, or docs; keep those boundaries explicit.
5. Never claim live support from static checks.
6. Update this handoff when an intentional difference is added, removed, or
   reclassified.

## Immediate project state

The next required work is live installation, per-host configuration, and
Codex/Cursor conformance. Orchestrate, the PR watcher, lifecycle management, and
the worktree helper are later TODOs, not blockers for normal dstack use.
