# dstack differences from pstack

Durable contract for absorbing pstack. Pair this file with `AGENTS.md`. Do not infer live-host proof from static validation. Schema version stays 3 unless a compatibility boundary is requested.

Local comparison tree: `/Users/kourgia/projects/pstack` (plugin 0.15.28, commit `d457567332aa6989e753ea289f30ea2bfbc80bc0`). Upstream: <https://github.com/cursor/plugins/tree/main/pstack>. `/Users/kourgia/projects/plugins/pstack` and sibling plugin folders are immutable inputs.

Product exclusions also live in [Supported scope](docs/guide/06-supported-scope.md).

## Keep-set inventory

dstack ships 55 skills and 10 `dstack-mode` playbooks. The keep-set is closed.

**Kept skills.** `architect`, `arena`, `blast-radius`, `bro`, `comment-sicko`, `control-ui`, `correct`, `create-formal-verification-skill`, `create-verification-skill`, `deslop`, `dstack-config`, `dstack-help`, `dstack-mode`, `how`, `in-your-own-words`, `interrogate`, `ketchup`, `maintain-formal-verification-skill`, `maintain-verification-skill`, `no-comments`, `recall`, `reflect`, `setup-dstack`, `sharpen`, `swarm`, `tdd`, `teach`, `technical-writing`, `typescript-best-practices`, `unslop`, `why`, and the 24 `principle-*` leaves.

**Kept playbooks.** Authoring a skill, Babysit, Bug fix, Feature, Investigation, Opening a PR, Pause safely, Prototype, Refactoring, Session pickup.

**Out (do not copy back).** Skills: `automate-me`, `benchmark-checklist`, `figure-it-out`, `make-bot-ui`, `show-me-your-work`. Playbooks: `autonomous-run`, `autopilot-full`, `autopilot-stack`, `eval`, `hillclimb`, `multi-phase-plan`, `orchestrate`, `perf-issue`, `runtime-forensics`, `shipping`, `trace-forensics`, `visual-parity`, `worktree-cleanup`. Also out: `control-cli` (no bundled CLI/TUI harness), Apple development cleanup (never a pstack 0.15.28 playbook), `watch-pr`, `bootstrap.ts`, Bun lockfile, `bugbot-triage.md`, `references/plan.md`, `check-plan.mjs`, `worktree-audit.sh`, `scripts/orch/`, `worker_bindings.py`, and generated worker definitions.

Renames, no aliases: `poteto-mode` → `dstack-mode`, `setup-pstack` → `setup-dstack`, `poteto-help` → `dstack-help`.

## What must stay different

- Names above. Personal config is only `~/.dstack/config.json`. No environment or command-line override.
- Schema version 3, the compatibility boundary for removing `worker_binding`. A version 2 config fails with an instruction to delete or rewrite `~/.dstack/config.json` and rerun `setup-dstack`; there is no automatic migration. Host keys are exactly `codex`, `claude`, `cursor`.
- Four profiles only: `fast-explorer`, `feature-worker`, `bug-worker`, `skeptical-reviewer`. Every profile is a concrete model **and** effort pair. `auto`, `inherit`, and `inherit-parent` are invalid. No parent-model inheritance and no automatic aliases.
- Each host's profiles hold exactly what that host's native spawn call takes. A host entry is only `profiles`, `invalid_bindings`, and `repositories`; `invalid_bindings` entries use the same shape as that host's profiles.
  - `codex`, `claude`: `{"model": "<id>", "effort": "<effort>"}`, passed as separate spawn arguments (Claude `Agent` model and effort; Codex `spawn_agent` model and `reasoning_effort`). Neither value may contain brackets.
  - `cursor`: `{"model": "<cursor-form id>"}` with no `effort` field, passed as `Task.model`. The id carries the effort: `id[effort=value]` (exactly one `effort` option) or a catalog slug that encodes effort.
- No `worker_binding`, `definitions_directory`, `pair_encoding`, `spawn-arguments` / `worker-definitions` mechanisms, or generated `dstack-<profile>` worker files. A worker never inherits session effort.
- `dstack-config` is a dstack-only skill and the single owner of the config read procedure. It maps the system-provided product identity to those three host ids, selects and verifies `repositories[<canonical-repository-root>]` or a registered checkout that shares `git rev-parse --git-common-dir`, returns one named profile's spawn values or the transcripts directory, and stops with an explicit `setup-dstack` instruction on failure. `setup-dstack` owns writing the file.
- A skill that spawns (`dstack-mode`, `arena`, `how`, `why`, `interrogate`, `swarm`, `recall`, `reflect`) carries one line at the point of use: Call the Skill tool with `dstack-config`. Spawned workers do not call it. Around that line the text stays at pstack 0.15.28 wording except for the harness-neutral edits. The audit fails any other skill that re-describes the procedure.
- Spawn uses the active harness's native subagent tool. A denied nested spawn collapses onto the current agent and is disclosed. The chat that receives `/dstack-mode` runs the playbook and never spawns a subagent to run the playbook itself.
- Skill-to-skill instruction is exact: Call the Skill tool with `skill-name`.
- No adapters, capability files, provider-specific rules, `poteto-agent`, or `subagent_type`. Skills say "native spawn call"; only this file names `Task`, `Agent`, or `spawn_agent`.
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

## Cursor spawn evidence (static)

Recorded 2026-10-20 from documentation and an inspected tool schema. This is static evidence, not live-host proof.

- [Cursor subagents docs](https://cursor.com/docs/subagents), "Model parameters": square-bracket `id=value` options (`claude-opus-5[effort=high]`, `composer-2.5[fast=false]`) are documented for the custom-subagent frontmatter `model` field. The same page says the parent "can name a model when it launches a subagent" but says nothing about bracket options on that launch-time model.
- `Task` tool schema in a Cursor cloud-agent session: `model` is an optional string that "must resolve to one of the available model slugs"; an invalid slug fails the call with the allowed list; omitting it uses the parent model, and the description recommends `inherit`. The listed slugs encode effort as a suffix (for example `claude-opus-5-5-high`, `gpt-5.6-sol-xhigh`); some, such as `composer-2.5`, carry none.
- Result: a listed effort-encoding slug is the documented `Task.model` form. Bracket form on `Task.model` is neither documented nor ruled out. The config accepts both, and `setup-dstack` stores a listed slug when the spawn schema requires listed slugs. `inherit` is rejected as a profile value. A live spawn that proves a bracket-form effort sticks is still open (`KNOWN_ISSUES.md` item 16).

## How to absorb a new pstack version

1. Recheck the local comparison-tree revision. Do not overwrite immutable plugin folders.
2. Diff the old and new pstack revisions for keep-set paths only.
3. Copy only keep-set skills and playbooks. Do not pull dropped items. Do not recreate adapters, `poteto-agent`, capability files, or provider rules.
4. Apply the standard token transforms, then the required stay-different substitutions.
5. Update the recorded plugin version and source commit in this file. Do not turn this file back into a historical absorb diary.
6. Run the static gates in `AGENTS.md`. Static checks are not live harness proof.

## Codex sidecars and invocation

Each skill has `agents/openai.yaml`. Human-only roots keep `disable-model-invocation: true` and `policy.allow_implicit_invocation: false`. Skills that playbooks or other skills call through the Skill tool omit both restrictions, because a model-disabled skill cannot be an internal callee in Claude Code or Codex. A human-only prerequisite is an instruction for the user to invoke the skill, not a Skill-tool call. See [invocation metadata](docs/agents/invocation.md).
