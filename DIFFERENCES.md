# dstack differences from pstack

Durable contract for absorbing pstack. Pair this file with `AGENTS.md`. Do not infer live-host proof from static validation. Schema version stays 2 unless a compatibility boundary is requested.

Local comparison tree: `/Users/kourgia/projects/pstack` (plugin 0.15.28, commit `d457567332aa6989e753ea289f30ea2bfbc80bc0`). Upstream: <https://github.com/cursor/plugins/tree/main/pstack>. `/Users/kourgia/projects/plugins/pstack` and sibling plugin folders are immutable inputs.

Product exclusions also live in [Supported scope](docs/guide/06-supported-scope.md).

## Keep-set inventory

dstack ships 54 skills and 10 `dstack-mode` playbooks. The keep-set is closed.

**Kept skills.** `architect`, `arena`, `blast-radius`, `bro`, `comment-sicko`, `control-ui`, `correct`, `create-formal-verification-skill`, `create-verification-skill`, `deslop`, `dstack-help`, `dstack-mode`, `how`, `in-your-own-words`, `interrogate`, `ketchup`, `maintain-formal-verification-skill`, `maintain-verification-skill`, `no-comments`, `recall`, `reflect`, `setup-dstack`, `sharpen`, `swarm`, `tdd`, `teach`, `technical-writing`, `typescript-best-practices`, `unslop`, `why`, and the 24 `principle-*` leaves.

**Kept playbooks.** Authoring a skill, Babysit, Bug fix, Feature, Investigation, Opening a PR, Pause safely, Prototype, Refactoring, Session pickup.

**Out (do not copy back).** Skills: `automate-me`, `benchmark-checklist`, `figure-it-out`, `make-bot-ui`, `show-me-your-work`. Playbooks: `autonomous-run`, `autopilot-full`, `autopilot-stack`, `eval`, `hillclimb`, `multi-phase-plan`, `orchestrate`, `perf-issue`, `runtime-forensics`, `shipping`, `trace-forensics`, `visual-parity`, `worktree-cleanup`. Also out: `control-cli` (no bundled CLI/TUI harness), Apple development cleanup (never a pstack 0.15.28 playbook), `watch-pr`, `bootstrap.ts`, Bun lockfile, `bugbot-triage.md`, `references/plan.md`, `check-plan.mjs`, `worktree-audit.sh`, `scripts/orch/`.

Renames, no aliases: `poteto-mode` → `dstack-mode`, `setup-pstack` → `setup-dstack`, `poteto-help` → `dstack-help`.

## What must stay different

- Names above. Personal config is only `~/.dstack/config.json`. No environment or command-line override.
- Schema version 2. Host keys are exactly `codex`, `claude`, `cursor`.
- Four profiles only: `fast-explorer`, `feature-worker`, `bug-worker`, `skeptical-reviewer`. Every profile is a concrete model **and** effort pair. `auto` and `inherit-parent` are invalid. No parent-model inheritance and no automatic aliases.
- Both halves of a pair reach the worker through that host entry's `worker_binding` (`spawn-arguments` or `worker-definitions`). A worker never inherits session effort. `dstack-<profile>` names exist only for `worker-definitions` hosts.
- Config-dependent skills read the file themselves, map the system-provided product identity to those three host ids, and stop with an explicit `setup-dstack` instruction on failure. Transcript consumers also select and verify `repositories[<canonical-repository-root>]`, or a registered checkout that shares `git rev-parse --git-common-dir`.
- Full resolve text lives in `dstack-mode` and `setup-dstack`. Other config-dependent skills point at that section and keep one `worker_binding` sentence (transcript skills also keep the repository-resolve strings the audit requires).
- Spawn uses the active harness's native subagent tool. A denied nested spawn collapses onto the current agent and is disclosed. The chat that receives `/dstack-mode` runs the playbook and never spawns a subagent to run the playbook itself.
- Skill-to-skill instruction is exact: Call the Skill tool with `skill-name`.
- No adapters, capability files, provider-specific rules, `poteto-agent`, `Task` tool, or `subagent_type`.
- Bundled as ordinary skills so the workflow is complete: `control-ui`, `deslop`, `comment-sicko`. `no-comments` tells a native subagent to Call the Skill tool with `comment-sicko`.
- Installer is `install.py` / `uninstall.py`, not a plugin package. No `plugin.json`, marketplace install, or generated-tree adapters.
- Opening a PR is explicit only. GitHub uses `gh`, GitLab uses `glab`. Babysit is a separate explicit follow-up and stops at merge-ready. Repository writers serialize in the active checkout. No Graphite, Origin, worktrees, built-in PR-tool rule, `/loop`, or `/visualize`.
- Authoring a skill uses the host's skill-authoring skill, not Cursor `create-skill`.

## What must stay 1-1 with pstack

For keep-set skills and playbooks, copy pstack and apply only these standard token transforms:

- `poteto` → `dstack`, `Poteto` → `Dstack`
- `pstack` → `dstack`, `Pstack` → `Dstack`
- `poteto-mode` / `setup-pstack` / `poteto-help` → `dstack-mode` / `setup-dstack` / `dstack-help`
- Wrap each skill invocation as `Call the Skill tool with \`name\`.`

Keep only the harness-neutral substitutions listed under **What must stay different**. Do not add paraphrase around those substitutions. Do not restore dropped skills or playbooks in order to make a retained file match.

Do not restore `disable-model-invocation` on Skill-tool callees (`how`, `why`, `unslop`, `technical-writing`, `typescript-best-practices`, and any other skill a playbook or skill calls through the Skill tool).

## How to absorb a new pstack version

1. Recheck the local comparison-tree revision. Do not overwrite immutable plugin folders.
2. Diff the old and new pstack revisions for keep-set paths only.
3. Copy only keep-set skills and playbooks. Do not pull dropped items. Do not recreate adapters, `poteto-agent`, capability files, or provider rules.
4. Apply the standard token transforms, then the required stay-different substitutions.
5. Update the recorded plugin version and source commit in this file. Do not turn this file back into a historical absorb diary.
6. Run the static gates in `AGENTS.md`. Static checks are not live harness proof.

## Codex sidecars and invocation

Each skill has `agents/openai.yaml`. Human-only roots keep `disable-model-invocation: true` and `policy.allow_implicit_invocation: false`. Skills that playbooks or other skills call through the Skill tool omit both restrictions, because a model-disabled skill cannot be an internal callee in Claude Code or Codex. A human-only prerequisite is an instruction for the user to invoke the skill, not a Skill-tool call. See [invocation metadata](docs/agents/invocation.md).
