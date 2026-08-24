# dstack maintainer handoff

Updated 2026-08-19. Read this before changing portability contracts, porting a
new pstack release, or claiming live host support.

## Objective

dstack is a provider-neutral adaptation of Cursor pstack. Its canonical skill
installation is `~/.agents/skills`; its personal configuration, adapters,
contracts, schemas, and optional runtime live under `DSTACK_HOME` (default
`~/.dstack`).

The project favors a small initial product:

- a collision-safe first installer, not a package manager;
- one strict version-2 JSON configuration with a single v1-to-v2 migration,
  not a general migration framework;
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
- The only pstack playbook dstack does not ship is `orchestrate.md`, excluded by
  product decision (see "Deliberate exclusions").
- No legacy `pstack`, `poteto-mode`, or `setup-pstack` aliases are planned.
- Invocation parity is restored. 40 skills are user-invoked; `comment-sicko`,
  `how`, `typescript-best-practices`, `unslop`, and `why` are model-invoked.
  That matches upstream except for `setup-dstack`, which dstack deliberately
  makes user-invoked: configuring host selection and role bindings is the
  human's call, and sibling skills tell the user to run it by name rather than
  calling it. Each skill declares this twice — as
  `disable-model-invocation` in frontmatter for Claude Code and Cursor, and as
  `policy.allow_implicit_invocation` in `agents/openai.yaml` for Codex — and the
  audit fails any skill whose two declarations disagree. See
  `docs/agents/invocation.md`.

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
Ran 51 tests
OK

Skill Creator validation
45 of 45 skill packages valid
```

JSON syntax and Python compilation also passed. These are static results, not
live host proof.

## Deliberate exclusions

These are product decisions, not deferred work. Reopen one only with a new
explicit decision; do not port any of them for file parity.

### 1. Orchestrate playbook and `orch` runtime — excluded

Pstack ships a project-scale coordination playbook plus a tested TypeScript
plain-file store:

```text
pstack/skills/poteto-mode/playbooks/orchestrate.md
pstack/skills/poteto-mode/scripts/orch/orch.ts
pstack/skills/poteto-mode/scripts/orch/store.ts
pstack/skills/poteto-mode/scripts/orch/orch.test.ts
```

The runtime is durable bookkeeping only: units, tracks, standing orders, an
inbox, human gates, verification verdicts keyed by PR plus exact head SHA,
stack frontier, locking, and derived status.

Excluded because the workflow it serves is out of scope for dstack. It targets
multi-day, many-PR programs, and it is the heaviest thing in the upstream
corpus by a wide margin. `orchestrate.md` is the runtime's only consumer, so
the two stand or fall together.

### 2. PR watcher (`watch-pr`) — excluded

```text
pstack/skills/poteto-mode/scripts/watch-pr/
```

The watcher answers one question — can this PR actually merge — by taking
GitHub's own `mergeStateStatus` as the verdict and classifying the blocker as
merge conflicts, review threads, failing checks, or a merge gate. It also
models stacks and merge queues, and polls until a terminal verdict so it can
serve as the event wake.

The Babysit playbook keeps the part that mattered: one authoritative query for
the PR's own merge verdict rather than a picture assembled from per-check
calls. Blocker classification and stack/queue handling stay in the playbook
prose as agent instructions. Review-pass counting was always an agent
instruction upstream too, not watcher output, and it survives unchanged.

### 3. Bun toolchain — excluded

```text
pstack/skills/poteto-mode/scripts/bootstrap.ts
pstack/skills/poteto-mode/scripts/package.json
pstack/skills/poteto-mode/scripts/bun.lock
```

These exist only to install `commander` for `orch` and `watch-pr`, via a silent
first-use bootstrap. With both consumers excluded they have no purpose, and the
bootstrap contradicts the standing rule against installing a runtime silently.

dstack therefore ships exactly one script, `dstack-mode/scripts/worktree-audit.sh`,
and depends on no language runtime beyond the host's own.

### 4. `poteto-agent` wrapper — excluded

Pstack registers a second agent whose only job is to force a full read of the
mode skill before any work begins. dstack ships no counterpart.

It is a provider-registered agent wrapper, the same shape already absorbed into
portable skill behavior elsewhere, and it encodes a routing concern that
belongs to the host rather than to portable content.

### 5. Benny automation — excluded

`pstack/automations/benny/` depends on Cursor Automations, provider UI, Slack
actions, cloud checkouts, and provider configuration. It is not part of dstack's
portable skill scope.

## Differences that are transformations, not gaps

### Worktree audit helper — ported with the transcript path made configurable

`dstack-mode/scripts/worktree-audit.sh` is ported from pstack. It classifies
every git worktree by size, merge state, uncommitted work, remote and PR state,
and the most recent chat that operated in it, then emits a table sorted by size
with a suggested bucket. It never deletes; deletion stays human-gated in the
playbook.

The one change from upstream: the hardcoded Cursor transcript directory became
the `AGENT_TRANSCRIPTS_DIR` environment variable. Set it to the host's
directory for the active workspace and the `LAST_CHAT` column populates; leave
it unset and that column reports `-` while every other column still works. The
helper never scans private history to infer ownership.

### Skill descriptions are not yet typed by invocation mode — open

A user-invoked skill's description is read by a human browsing slash commands,
so it should be a one-line summary. A model-invoked skill's description is read
by the model deciding whether to fire, so it keeps rich trigger phrasing.

Most inherited user-invoked skills still carry model-facing trigger lists
(`principle-fix-root-causes` opens "Apply when debugging", `tdd` opens "Use only
when the user explicitly asks"). Upstream wrote them that way while also marking
them user-invoked, so the text and the setting disagree at the source.

This is cosmetic while the declarations hold: the host, not the description,
enforces invocation. Fix it by rewriting descriptions, never by relaxing a
`disable-model-invocation` setting to match the prose.

### Provider wrappers and defaults — transformed

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

The initial installer remains collision-safe and first-install-only by default.
Real use required one explicit `--update` path: it verifies the expected skill
identity and existing destination topology, creates missing managed artifacts
inside existing canonical roots,
stages replacements, rolls back failures,
and preserves `config.json`. It is not a repair, uninstall, ownership-hash,
doctor, or general package-management workflow.

Schema version 2 stores `{model, effort}` role bindings and invalid pairs. The
configurator accepts version 1 as migration input and provides one atomic
`migrate` command; no general migration framework exists.

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
