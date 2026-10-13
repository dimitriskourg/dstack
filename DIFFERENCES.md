# dstack differences from pstack

Updated 2026-10-13. This is the source-of-truth handoff for upstream alignment and project structure. The supported product scope lives in [the scope guide](docs/guide/06-supported-scope.md). dstack is under development, so compatible pre-release shape changes do not bump schema version 2.

## Upstream baseline

- Local source: `/Users/kourgia/projects/plugins/pstack`
- Upstream repository: <https://github.com/cursor/plugins/tree/main/pstack>
- Recorded source commit: `997ffc7fe26bdaa6478a14e7f5b8d5f9ed747102`
- Recorded plugin version: `0.15.21`
- Recorded inventory: 52 skills and 23 `poteto-mode` playbooks

Recheck the local source revision before a future sync. Treat pstack and other plugin folders as immutable inputs.

The 2026-09-09 retained-source refresh absorbed pstack `0.14.1` → `0.15.0` density and punctuation, the two new principle leaves, the TypeScript schemas-before-guards rule, PR-body briefing language, the removal of Critique mode from `how`, and Babysit stop conditions adapted for GitHub and GitLab. Dstack currently diverges on pstack's machine-checked multi-phase plan. Revisit that choice later. These 0.15.0 changes are still unported and remain deliberate follow-ups: Cursor sticky-mode metadata, hardcoded Fable 5.1 / Grok defaults, human-only invocation on Skill-tool callees (`how`, `why`, `unslop`, `typescript-best-practices`), the plugin logo, and `make-bot-ui`.

The 2026-10-06 refresh absorbed the harness-neutral parts of pstack `70b2dc8` (0.15.3) and `b0b9c7a` (0.15.4): instructions Opus 5.5 follows without the text are cut from the principles, playbooks, `interrogate`, `reflect`, `tdd`, `unslop`, `technical-writing`, `blast-radius`, `figure-it-out`, and `show-me-your-work`. `swarm` briefs now name exact SHAs and the measurement method, and a result that omits them is rerun once and then recorded as a gap. `show-me-your-work/scripts/log.sh` writes its header only to an empty log and appends instead of truncating. The concrete model-slug changes in the same commits do not apply, and the `autopilot-full`, `autopilot-stack`, `shipping`, and `multi-phase-plan` hunks stay out with those playbooks' existing divergence.

The same refresh then absorbed pstack `0.15.5` → `0.15.15`. New skills: `correct` and `principle-explain-the-number`, both explicit-only, and `benchmark-checklist`, callable by performance workflows, plus `dstack-help`, a port of `poteto-help` that routes to dstack's own skills, playbooks, setup, and guide and drops Custom Modes, `/loop`, cloud agents, and the excluded playbooks. Retained-skill changes: `architect` screens candidates as an agent contributor would change them and gains the split-ownership, two-ways, importable-internals, and hand-synced-list red flags; `dstack-mode` adds the benchmark trigger, the Explain the Number principle, fresh subagents by default, and claims that carry their evidence or label; Perf issue uses the performance mantras and Hillclimb borrows their order; both vet numbers with `benchmark-checklist`; Opening a PR uses `##` headings and shorter sections; `show-me-your-work` marks each run with a `start` row and audits only its own rows, append-only; `typescript-best-practices` uses a schema-first Zod example; `technical-writing` drops its fetch-date source lines. Not absorbed: model-rule reading, defaults, and the `setup-pstack` budget ask, because profiles live in `~/.dstack/config.json`; the built-in PR tool rule; autopilot owner changes in Babysit and Opening a PR; operator pronoun fixes, which touch only excluded playbooks; `make-bot-ui`, already excluded.

## Deliberate differences

### Curated scope

dstack ports selected pstack material rather than pursuing source completeness. All current standalone skills remain retained, but `dstack-mode` ships 18 local playbooks. Retained source stays as close to pstack as the supported harnesses and team requirements allow. Excluded source remains available through pstack and Git history; dstack does not keep a disabled archive.

### Names

- `poteto-mode` is `dstack-mode`.
- `setup-pstack` is `setup-dstack`.
- `poteto-help` is `dstack-help`.
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
- repository entries keyed by canonical absolute Git root, each containing one absolute transcript directory or `null`.

The retained product contract scopes transcripts by both harness and repository. Host keys are exactly `codex`, `claude`, and `cursor`. Each host's `repositories` object is keyed by the canonical absolute Git root and repeats that root inside the entry so consumers can verify the identity before reading transcripts.

The four profiles are `fast-explorer`, `feature-worker`, `bug-worker`, and `skeptical-reviewer`. Panel configuration and the former judgment-only profiles were removed.

Every profile requires a concrete model and effort pair. Parent inheritance and automatic model aliases are invalid. If the active harness rejects a configured pair, the consuming skill stops instead of omitting the model selection.

`worker_binding` records how a host applies a pair, because not every harness accepts both halves as spawn arguments. `spawn-arguments` means the spawn call carries the model and the effort. `worker-definitions` means the host reads the effort from a pre-declared worker definition, so `setup-dstack` synchronizes one definition per profile into the recorded `definitions_directory`. Synchronization verifies the generated definitions and leaves every other file untouched. Setup chooses `worker-definitions` whenever the host's spawn operation has no effort argument, since a model-only override leaves the worker on the session effort.

`pair_encoding` records how a generated definition pins that pair. `sibling-fields` writes separate `model` and `effort` keys. `model-brackets` writes `model: <id>[effort=<value>]` and, when the definition schema can refuse a parent spawn override, sets that refusal. Setup discovers the encoding from the live definition schema. It does not infer it from the harness id. A fused spawn identifier is a partial catalog, not a stored model value.

This is a portable mechanism recorded in configuration, not a provider rule folder: the mechanism and the directory are discovered live by setup in the active harness.

`setup-dstack` searches for and confirms the active repository's transcript directory once. Transcript-backed skills read the entry matching the canonical active-repository root, or a registered checkout that shares that root's `git rev-parse --git-common-dir`, and do not rediscover the transcript directory on every invocation. A Cursor or Git linked worktree therefore uses the already-registered main checkout without a second setup pass. Configuring another repository under the same harness preserves every existing repository entry.

Every independently invocable skill that consumes profiles or transcripts reads the fixed file itself and maps the system-provided product identity to `codex`, `claude`, or `cursor`. There is no alias or host override. Transcript consumers additionally derive the canonical Git root, select that repository entry or a common-dir-linked registered checkout, and verify the selected entry's repeated `repository_root`. Resolution uses `configure.py resolve`. A missing or invalid file, unidentified harness or repository, missing entry, missing required profile, or invalid configured binding stops the skill with an explicit `setup-dstack` instruction.

### Invocation metadata

Invocation has two portable states. Human-only root skills keep `disable-model-invocation: true`; `agents/openai.yaml` mirrors that policy with `allow_implicit_invocation: false`. Skills called through the Skill tool omit both restrictions because a model-disabled skill cannot be an internal callee in Claude Code or Codex. A human-only prerequisite is phrased as an instruction for the user to run the skill, not as a Skill-tool call. See [invocation metadata](docs/agents/invocation.md).

The pstack refresh keeps `benchmark-checklist` callable because the mode and performance playbooks invoke it. Its call sites use the standard Skill-tool phrase. `dstack-help` directs task requests to explicit user invocation of `dstack-mode` and bundles its guide pages under `references/guide/`, which the existing installer copies with the skill. The matching `docs/guide/` pages link to these canonical references instead of duplicating them.

The 2026-10-11 refresh absorbed pstack `00b14f1` (0.15.16) and `978ca6e` (0.15.17), verified by diffing `9f451cf..HEAD` for `pstack/`. 0.15.16 is the token-cutting rewrite: the same rules in fewer words across retained skills (`architect`, `arena`, `benchmark-checklist`, `figure-it-out`, `how`, `interrogate` plus its rubric and reviewer prompt, `reflect` plus its reviewer prompts, `technical-writing`, `unslop`, `why` plus epistemics, investigator, synthesizer, and source playbooks), the ten principle leaves that changed, and the `dstack-mode` playbooks that changed (`opening-a-pr`, `trace-forensics`). Deliberate dstack differences stayed: profile-based model and effort via `~/.dstack/config.json` (no hardcoded model names, Cursor model files, `Task`, or `subagent_type`), the standard Skill-tool call phrase, `reflect`'s transcript lookup through the dstack config, forge-neutral `gh`/`glab`, serialized repository writers, and the excluded playbooks. Human-only invocation on Skill-tool callees is still unported.

The same refresh adopted upstream's naming-by-convention in `dstack-mode` as a separable change. Principles and playbooks are referenced by title. The agent kebab-cases the title (hyphens kept, other punctuation dropped) to find `principle-<title>` or `playbooks/<title>.md`. Explicit names remain only where the title does not map cleanly: **Sequence Work into Verifiable Units** (`principle-sequence-verifiable-units`), **Authoring or modifying a skill** (`playbooks/authoring-a-skill.md`), **Multi-phase or multi-request plan** (`playbooks/multi-phase-plan.md`), and **Apple development cleanup** (`playbooks/apple-dev-cleanup.md`). The owner asked whether Multi-phase should name `references/plan.md`; that file is still the plan template inside the playbook, not the playbook the title resolves to. The portability audit now resolves the same convention and fails when a title does not point at an existing skill or playbook. This can be reverted on its own if the experiment fails.

0.15.17 adds `/ketchup`, ported as `skills/ketchup/`: human-only (`disable-model-invocation: true`, `allow_implicit_invocation: false`), harness-neutral (PR, CI, and agent checks are hedged with "where the harness exposes them"), and routed from `dstack-help` next to `/recall`. `/ketchup` recaps only this chat since the last user message. `/recall` still rebuilds context across recent chats.

The 2026-10-13 refresh absorbed pstack `1b6d44f` (0.15.20) → `997ffc7` (0.15.21), verified by diffing that range for `pstack/`. 0.15.21 (`364a77e`) tells agents where bundled leaf skills live: they set `disable-model-invocation`, so a spawned delegate never sees their paths. `dstack-mode` now names the canonical install at `~/.agents/skills/<name>/SKILL.md`, which is `../<name>/SKILL.md` from its own file, and puts that file's absolute path in every native subagent prompt. The Subagents brief includes the path so the delegate can open a leaf at `../<name>/SKILL.md` from it. Not absorbed: `agents/poteto-agent.md` (dstack has no agent wrappers) and the `plugin.json` version bumps (dstack is not a Cursor plugin package). The portability audit did not need a structural change.

The 2026-10-12 refresh absorbed pstack `978ca6e` (0.15.17) → `1b6d44f` (0.15.20), verified by diffing that range for `pstack/`. 0.15.18 (`ea32d95`) shows each `/ketchup` action item as a before and after, side by side: screenshots or video when the change is visible, otherwise a table, diff, or diagram, made only from what the agent already has. The read-only turn now allows those visuals and still hedges PR, CI, and agent checks. 0.15.19 (`08bd59b`) cuts restated sections from seven retained skills: how's explorer prompt, Babysit's reply line, four principle leaves (encode lessons in structure, exhaust the design space, guard the context window, laziness protocol), and why's code-archaeology, incident-postmortem, sentry, and slack sources. Code-archaeology keeps its forge-neutral PR/MR inventory line; the matching `gh`-only PR-context block was already replaced and then dropped with upstream. Separate logical commits in the same window: `unslop` drops "Must always apply." from its description; `/dstack-mode` runs in the chat that receives it and never spawns a subagent to run the playbook itself; `create-verification-skill` treats ready as a usable app, not a port that answers, reports seed-data gaps in Gotchas instead of weakening the journey, and leaves stand-in-only setup unverified. `dstack-mode` still has no `poteto-agent` wrapper or `subagent_type`; the runner-vs-delegate rule is phrased through the native subagent tool.

Not absorbed from `978ca6e..1b6d44f`: `plugin.json` and the Agent Plugins v1 root manifest (dstack is not a Cursor plugin package); `check-plan.mjs` fenced-code handling (the machine-checked multi-phase plan stays deferred); `watch-pr` review-thread pagination (dstack does not ship the PR watcher); `worktree-audit.sh` default-branch MERGED check and the `worktree-cleanup` section cut (worktrees stay excluded); the Comment Sicko Cursor agent-id rename (`agents/comment-sicko.md` and `subagent_type: "comment-sicko"`), because dstack has no agent wrappers and already invokes `comment-sicko` through the Skill tool; pstack README `poteto-agent` wording beyond the harness-neutral runner rule already taken. The portability audit did not need a structural change for this range.

Not absorbed from the earlier 0.15.16–0.15.17 commits: `plugin.json` and the pstack README (dstack is not a Cursor plugin package); pstack model-rule, `Task`, `subagent_type`, hardcoded slugs, and `pstack-models.mdc` hunks, because profiles live in `~/.dstack/config.json`; the built-in PR tool rule; autopilot owner paragraphs in Opening a PR; worktree, stack-manager, Origin, and Graphite language in Opening a PR; Shipping, autonomous-run, autopilot-full/stack, Orchestrate, and worktree-cleanup, which stay excluded; `make-bot-ui`, already excluded. `dstack-mode` still keeps its configuration, Skill-tool, native-subagent, and local-autonomy paragraphs, which 0.15.16 did not replace.

The help and guide alignment was rechecked against `997ffc7` (plugin 0.15.21). `dstack-help` starts from the upstream help file and retains its section order, question routing, skill comparisons, prompting references, and reply format, plus the `/ketchup` row, the recall/ketchup close call, and the `/dstack-mode` chat-as-runner sentence. Only the six upstream guide chapters directly linked by the help skill ship as local references (setup, mode, verification, principles, customization, and recipes), plus dstack’s supported-scope reference. The unneeded guide index, understanding, design, build-and-clean, and overnight chapters and all decorative images are omitted. Retained guide links point to the shipped chapters or the owning skills. Installation and setup use dstack’s fixed configuration and four concrete profiles; external helper skills are bundled; mode lifetime is host-neutral; repository writers serialize; publication is explicit and Babysit stops at merge-ready. Cloud work, automatic wake, autopilot, Shipping, worktree management, bot UI, and the automation pack remain excluded. Retained chapters preserve upstream examples and Mermaid diagrams; sibling-skill links resolve inside the installed skill collection.

The portability audit treats Skill-tool calls as invocation-graph edges and rejects any edge whose target is model-disabled. This preserves explicit-only roots without pretending either host supports a third state for internal-only invocation.

The currently bundled Skill Creator validator rejects that portable frontmatter key. This is a validator mismatch, not a reason to remove invocation metadata. The dstack portability audit checks the cross-host declarations together.

### Additional skill

`comment-sicko` remains an additional normal skill.

### Additional playbook

`apple-dev-cleanup` is a dstack-specific explicit playbook. The pstack worktree-and-simulator cleanup workflow mixed repository cleanup with machine-wide Apple development state. Dstack excludes worktree management and retains the Apple cleanup value behind a separate audit and approval gate.

### Multi-phase plan

dstack still uses `references/plan.md`. It has not taken pstack's checkbox skeleton or `check-plan.mjs`. That checker is built for pstack's autopilot runtime, cloud lanes, and a hardcoded model. Whether dstack should add a similar local checker, without that runtime, is undecided. Revisit this on the next sync.

### Excluded pstack runtime

dstack does not ship pstack's provider-specific automation, agent wrappers, silent Bun bootstrap, PR watcher, or heavyweight Orchestrate runtime. `make-bot-ui` is excluded because it is a Cursor Grok Bot webhook, secret-request, and Tailscale workflow, not a portable local skill. The curated `dstack-mode` also excludes:

- `autonomous-run`, because supported local sessions do not promise unattended wake or persistence;
- `autopilot-full`, because dstack does not support autonomous parallel repository writers or automated merging;
- `autopilot-stack`, because dstack does not support that autonomy or Graphite;
- `shipping`, because the source playbook is Graphite-specific and dstack stops at merge-ready;
- `worktree-cleanup` and its audit script, because dstack does not create or manage worktrees.

These are intentional scope choices, not capability gaps or known issues. Repository writers serialize. Read-only exploration, review, and independent artifacts outside the repository may still fan out in bounded waves.

### Forge support

Opening a request and Babysit resolve the repository remote first. GitHub uses authenticated `gh`; GitLab uses authenticated `glab`. Babysit stop conditions are forge-specific. A request already in GitHub's merge queue or GitLab's merge train, with no remaining blockers, is merge-ready. Babysit does not wait for the merge itself. Opening a pull request or merge request is explicit only, Babysit is a separate explicit follow-up, and merge authority remains with the team.

## Structure

Portable behavior lives inside `skills/`. Deterministic helpers live with the skill that owns them. Strict personal configuration shape lives in `schemas/config.schema.json`. The installer copies skills, the schema, license, and notice. The uninstaller has explicit skills-only and complete-removal modes; it verifies dstack ownership before removing canonical skills, compatibility links, or generated worker definitions. There is no parallel adapter hierarchy to keep synchronized.

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
