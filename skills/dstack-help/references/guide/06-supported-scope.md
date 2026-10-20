# Supported scope

dstack is a curated local workflow pack for Codex, Claude Code, and Cursor. Upstream remains the source baseline for retained material, but source completeness is not a product goal. Retained skills stay close to upstream with only justified harness, forge, safety, and team-workflow changes.

## Runtime boundary

- Work runs on the user's computer in an active interactive session.
- Native subagents may parallelize read-only exploration, review, and independent artifacts outside the repository.
- Repository writers are serialized in the active checkout. Dstack does not create, manage, or clean Git worktrees. Linked worktrees of a registered checkout reuse that repository entry through `git rev-parse --git-common-dir`; they do not need their own `setup-dstack` pass.
- Required fan-out runs in bounded waves when the active harness has fewer child slots than requested. Required slices are not dropped.
- Long-running workflows do not promise scheduled wake, background persistence, or continuation after the active session ends.
- Opening a pull request or merge request is explicit only. No implementation playbook publishes work automatically.
- Babysit is explicit, supports GitHub through `gh` and GitLab through `glab`, and stops at merge-ready. GitHub's merge queue and GitLab's merge train count as merge-ready. Dstack does not automate merging.
- Transcript-backed workflows select the active harness and current repository. Cross-harness pickup requires an explicit transcript export, path, or branch.

## Retained skills

The skills below remain supported. This keep-set will shrink further; `figure-it-out`, `show-me-your-work`, and `automate-me` are already out.

### Workflow and orchestration

- `dstack-mode`
- `dstack-help`
- `setup-dstack`
- `arena`
- `swarm`
- `interrogate`
- `recall`
- `ketchup`
- `in-your-own-words`
- `sharpen`
- `reflect`
- `correct`

### Understanding and design

- `how`
- `why`
- `teach`
- `architect`
- `blast-radius`
- `bro`

### Verification and language guidance

- `control-cli`
- `control-ui`
- `create-verification-skill`
- `create-formal-verification-skill`
- `maintain-formal-verification-skill`
- `maintain-verification-skill`
- `tdd`
- `benchmark-checklist`
- `typescript-best-practices`

### Code and prose quality

- `deslop`
- `no-comments`
- `comment-sicko`
- `unslop`
- `technical-writing`

### Principles

- `principle-attack-the-premise`
- `principle-boundary-discipline`
- `principle-build-the-lever`
- `principle-encode-lessons-in-structure`
- `principle-exhaust-the-design-space`
- `principle-explain-the-number`
- `principle-experience-first`
- `principle-fix-root-causes`
- `principle-foundational-thinking`
- `principle-guard-the-context-window`
- `principle-laziness-protocol`
- `principle-make-operations-idempotent`
- `principle-migrate-callers-then-delete-legacy-apis`
- `principle-minimize-reader-load`
- `principle-model-the-domain`
- `principle-never-block-on-the-human`
- `principle-outcome-oriented-execution`
- `principle-prove-it-works`
- `principle-redesign-from-first-principles`
- `principle-separate-before-serializing-shared-state`
- `principle-sequence-verifiable-units`
- `principle-subtract-before-you-add`
- `principle-test-behavior-not-implementation`
- `principle-type-system-discipline`

## Retained dstack-mode playbooks

- Investigation
- Bug fix
- Performance issue
- Feature
- Refactoring
- Prototype
- Authoring or modifying a skill
- Eval
- Babysit
- Session pickup
- Pause safely
- Multi-phase or multi-request plan
- Opening a PR

## Intentional exclusions

- **Autonomous run.** Excluded because unattended persistence and wake facilities are not consistent across the supported local harnesses.
- **Autopilot-full.** Excluded because dstack does not support autonomous parallel repository writers or automated merging.
- **Autopilot-stack.** Excluded because dstack does not support autonomous execution or Graphite.
- **Shipping.** Excluded because the source workflow is Graphite-specific. Babysit stops at merge-ready and the team retains merge authority.
- **Worktree cleanup.** Excluded because dstack does not currently create or manage worktrees.
- **Orchestrate.** Excluded with the provider-specific upstream runtime; dstack uses its retained skills and playbooks directly.
- **Make Bot UI.** Excluded because the source skill is a provider-specific bot webhook, secret-request, and Tailscale workflow.
- **figure-it-out.** Dropped from the everyday keep-set. Large or cross-cutting work matches a retained playbook, or is split into playbook-sized units.
- **show-me-your-work.** Dropped from the everyday keep-set. There is no separate decision-trail skill.
- **automate-me.** Dropped from the everyday keep-set. Personal mode generation is out of this pack.
- **Hillclimb.** Dropped from the everyday keep-set. One-off measured slowness stays on Perf issue.
- **Runtime forensics.** Dropped from the everyday keep-set. Live-instrumentation diagnosis is out; Bug fix and Perf issue still own defects and measured slowness.
- **Trace forensics.** Dropped from the everyday keep-set. Captured-artifact diagnosis is out; Bug fix and Perf issue still own defects and measured slowness.
- **Visual parity.** Dropped from the everyday keep-set. Pixel-exact matching is out; Prototype and `control-ui` still cover driving a UI.
- **Apple development cleanup.** Dropped from the everyday keep-set. Machine-wide Apple simulator and runtime cleanup is out.

Git worktrees remain a possible future capability for creation, isolation, and cleanup. Add those only when real team usage justifies a complete contract across Codex, Claude Code, and Cursor. Recognizing an existing linked worktree as the same registered repository is already in scope.

## Document ownership

- This file defines what dstack supports.
- [`DIFFERENCES.md`](https://github.com/dimitriskourg/dstack/blob/main/DIFFERENCES.md) records how that scope and retained source differ from upstream.
- [`KNOWN_ISSUES.md`](https://github.com/dimitriskourg/dstack/blob/main/KNOWN_ISSUES.md) tracks unresolved defects inside this supported scope. Excluded features are not backlog items.
