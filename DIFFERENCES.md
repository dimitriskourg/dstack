# dstack differences from pstack

Updated 2026-08-27. This is the source-of-truth handoff for upstream alignment and project structure. The supported product scope lives in [the scope guide](docs/guide/06-supported-scope.md). dstack is under development, so compatible pre-release shape changes do not bump schema version 2.

## Upstream baseline

- Local source: `/Users/kourgia/projects/plugins/pstack`
- Upstream repository: <https://github.com/cursor/plugins/tree/main/pstack>
- Recorded source commit: `63d938c2e4a165a0fec1bd0f61a8e325f0cb751e`
- Recorded plugin version: `0.14.1`
- Recorded inventory: 44 skills and 23 `poteto-mode` playbooks

Recheck the local source revision before a future sync. Treat pstack and other plugin folders as immutable inputs.

## Deliberate differences

### Curated scope

dstack ports selected pstack material rather than pursuing source completeness. All current standalone skills remain retained, but `dstack-mode` ships 18 local playbooks. Retained source stays as close to pstack as the supported harnesses and team requirements allow. Excluded source remains available through pstack and Git history; dstack does not keep a disabled archive.

### Names

- `poteto-mode` is `dstack-mode`.
- `setup-pstack` is `setup-dstack`.
- No legacy aliases are shipped.

### Referenced external skills

pstack explicitly references three skills from the general plugin collection. dstack bundles them so the workflow is complete:

- `control-cli`
- `control-ui`
- `deslop`

The separate general `orchestrate` plugin is not copied. Pstack's Orchestrate route is its own bundled playbook and runtime. The external plugin is a different provider-SDK and Slack product.

### Harness neutrality

- Provider task schemas, cloud-agent assumptions, provider rule paths, and concrete default model slugs are removed from portable skills.
- Skill-to-skill instructions use this exact phrase: Call the Skill tool with `skill-name`.
- Subagent instructions say to use the active harness's native subagent tool. Supported harnesses are expected to provide spawning. A denied nested spawn collapses onto the current agent and is disclosed.
- There is no capability contract, capability TOML, adapter matrix, or provider instruction folder.

### Configuration

`~/.dstack/config.json` is the only personal configuration. Its location is fixed: there is no environment or command-line override. It keeps independent entries by lowercase harness id. Each entry contains:

- four model-and-effort profiles;
- invalid model-and-effort bindings;
- the worker binding mechanism for that harness;
- one absolute transcript directory, or `null`.

The retained product contract scopes transcripts by both harness and repository. The current schema still stores one directory per harness; [known issue 2](KNOWN_ISSUES.md) tracks the required correction.

The four profiles are `fast-explorer`, `feature-worker`, `bug-worker`, and `skeptical-reviewer`. Panel configuration and the former judgment-only profiles were removed.

Every profile requires a concrete model and effort pair. Parent inheritance and automatic model aliases are invalid. If the active harness rejects a configured pair, the consuming skill stops instead of omitting the model selection.

`worker_binding` records how a host applies a pair, because not every harness accepts both halves as spawn arguments. `spawn-arguments` means the spawn call carries the model and the effort. `worker-definitions` means the host reads the effort from a pre-declared worker definition, so `setup-dstack` synchronizes one definition per profile into the recorded `definitions_directory`. Synchronization verifies the generated definitions and leaves every other file untouched. Setup chooses `worker-definitions` whenever the host's spawn operation has no effort argument, since a model-only override leaves the worker on the session effort.

This is a portable mechanism recorded in configuration, not a provider rule folder: the mechanism and the directory are discovered live by setup in the active harness.

`setup-dstack` searches for and confirms the active repository's transcript directory once. Transcript-backed skills read the saved path and do not rediscover it on every invocation. Until known issue 2 is resolved, configuring another repository under the same harness can overwrite that saved path.

Every independently invocable skill that consumes profiles or transcripts reads the fixed file itself and selects the entry keyed by the lowercase identity of the active harness. There is no host override. A missing or invalid file, unidentified harness, missing host entry, missing required profile, or invalid configured binding stops the skill with an explicit `setup-dstack` instruction.

### Invocation metadata

Invocation has two portable states. Human-only root skills keep `disable-model-invocation: true`; `agents/openai.yaml` mirrors that policy with `allow_implicit_invocation: false`. Skills called through the Skill tool omit both restrictions because a model-disabled skill cannot be an internal callee in Claude Code or Codex. A human-only prerequisite is phrased as an instruction for the user to run the skill, not as a Skill-tool call. See [invocation metadata](docs/agents/invocation.md).

The portability audit treats Skill-tool calls as invocation-graph edges and rejects any edge whose target is model-disabled. This preserves explicit-only roots without pretending either host supports a third state for internal-only invocation.

The currently bundled Skill Creator validator rejects that portable frontmatter key. This is a validator mismatch, not a reason to remove invocation metadata. The dstack portability audit checks the cross-host declarations together.

### Additional skill

`comment-sicko` remains an additional normal skill.

### Additional playbook

`apple-dev-cleanup` is a dstack-specific explicit playbook. The pstack worktree-and-simulator cleanup workflow mixed repository cleanup with machine-wide Apple development state. Dstack excludes worktree management and retains the Apple cleanup value behind a separate audit and approval gate.

### Excluded pstack runtime

dstack does not ship pstack's provider-specific automation, agent wrappers, silent Bun bootstrap, PR watcher, or heavyweight Orchestrate runtime. The curated `dstack-mode` also excludes:

- `autonomous-run`, because supported local sessions do not promise unattended wake or persistence;
- `autopilot-full`, because dstack does not support autonomous parallel repository writers or automated merging;
- `autopilot-stack`, because dstack does not support that autonomy or Graphite;
- `shipping`, because the source playbook is Graphite-specific and dstack stops at merge-ready;
- `worktree-cleanup` and its audit script, because dstack does not create or manage worktrees.

These are intentional scope choices, not capability gaps or known issues. Repository writers serialize. Read-only exploration, review, and independent artifacts outside the repository may still fan out in bounded waves.

### Forge support

Opening a request and Babysit resolve the repository remote first. GitHub uses authenticated `gh`; GitLab uses authenticated `glab`. Opening a pull request or merge request is explicit only, Babysit is a separate explicit follow-up, and merge authority remains with the team.

## Structure

Portable behavior lives inside `skills/`. Deterministic helpers live with the skill that owns them. Strict personal configuration shape lives in `schemas/config.schema.json`. The installer copies skills, the schema, license, and notice. There is no parallel adapter hierarchy to keep synchronized.

## Sync procedure

1. Record the exact old and new pstack revisions.
2. Diff those revisions before copying anything.
3. Inventory skills, playbooks, references, scripts, agents, and automations separately.
4. Copy only supported portable source with the smallest possible edits.
5. Apply only the deliberate transformations above.
6. Inventory skill names referenced outside pstack and copy matching general-plugin skills when they are real dependencies.
7. Update this file for every explained source difference.
8. Run static validation and then exercise affected workflows in each live harness.

Zero unexplained source differences is the goal. Static checks are not live harness proof.
