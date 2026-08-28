# Supported scope

dstack is a curated local workflow pack for Codex, Claude Code, and Cursor. Pstack remains the source baseline for retained material, but source completeness is not a product goal. Retained skills stay close to pstack with only justified harness, forge, safety, and team-workflow changes.

## Runtime boundary

- Work runs on the user's computer in an active interactive session.
- Native subagents may parallelize read-only exploration, review, and independent artifacts outside the repository.
- Repository writers are serialized in the active checkout. Dstack does not create, manage, or clean Git worktrees.
- Required fan-out runs in bounded waves when the active harness has fewer child slots than requested. Required slices are not dropped.
- Long-running workflows do not promise scheduled wake, background persistence, or continuation after the active session ends.
- Opening a pull request or merge request is explicit only. No implementation playbook publishes work automatically.
- Babysit is explicit, supports GitHub through `gh` and GitLab through `glab`, and stops at merge-ready. Dstack does not automate merging.
- Transcript-backed workflows select the active harness and current repository. Cross-harness pickup requires an explicit transcript export, path, or branch.

## Retained skills

All current standalone skills remain supported.

### Workflow and orchestration

- `dstack-mode`
- `setup-dstack`
- `automate-me`
- `figure-it-out`
- `arena`
- `swarm`
- `interrogate`
- `show-me-your-work`
- `recall`
- `reflect`

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
- `maintain-verification-skill`
- `tdd`
- `typescript-best-practices`

### Code and prose quality

- `deslop`
- `no-comments`
- `comment-sicko`
- `unslop`
- `technical-writing`

### Principles

- `principle-boundary-discipline`
- `principle-build-the-lever`
- `principle-encode-lessons-in-structure`
- `principle-exhaust-the-design-space`
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
- `principle-type-system-discipline`

## Retained dstack-mode playbooks

- Investigation
- Bug fix
- Performance issue
- Hillclimb
- Runtime forensics
- Trace forensics
- Feature
- Refactoring
- Prototype
- Visual parity
- Authoring or modifying a skill
- Eval
- Babysit
- Session pickup
- Pause safely
- Multi-phase or multi-request plan
- Opening a PR
- Apple development cleanup

Apple development cleanup is a dstack-specific local addition. It is explicit and machine-scoped, with an audit and approval gate before deleting simulator, runtime, Xcode build, or device-support state.

## Intentional exclusions

- **Autonomous run.** Excluded because unattended persistence and wake facilities are not consistent across the supported local harnesses.
- **Autopilot-full.** Excluded because dstack does not support autonomous parallel repository writers or automated merging.
- **Autopilot-stack.** Excluded because dstack does not support autonomous execution or Graphite.
- **Shipping.** Excluded because the source workflow is Graphite-specific. Babysit stops at merge-ready and the team retains merge authority.
- **Worktree cleanup.** Excluded because dstack does not currently create or manage worktrees.
- **Orchestrate.** Excluded with the provider-specific pstack runtime; dstack uses its retained skills and playbooks directly.

Git worktrees remain a possible future capability. Add them only when real team usage justifies a complete creation, repository setup, runtime-resource isolation, integration, and cleanup contract across Codex, Claude Code, and Cursor.

## Document ownership

- This file defines what dstack supports.
- [`DIFFERENCES.md`](../../DIFFERENCES.md) records how that scope and retained source differ from pstack.
- [`KNOWN_ISSUES.md`](../../KNOWN_ISSUES.md) tracks unresolved defects inside this supported scope. Excluded features are not backlog items.
