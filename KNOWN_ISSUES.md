# Known portability and runtime issues

Updated 2026-08-26. This is the working backlog for failures that can still occur when dstack runs in Codex or Claude Code. Work through the items independently in priority order. Keep schema version 2 while the project remains under development.

Static validation is not live-host proof. When an item changes runtime behavior, verify it in the affected live harness before checking it off.

## P0: Blocking orchestration failures

### [ ] 1. Prove nested skill calls in live Claude Code and Codex

**Resolved design:** Invocation has two portable states. Human-only root skills declare `disable-model-invocation: true` and mirror it with `policy.allow_implicit_invocation: false`. Any skill used as an internal callee omits both restrictions. Neither host provides a portable third state for a skill that is hidden from autonomous selection but callable by another skill.

**Implemented:** Internal callees such as `architect`, `arena`, `interrogate`, `swarm`, `show-me-your-work`, `figure-it-out`, `no-comments`, and `technical-writing` are model-invokable in both host declarations. `setup-dstack` remains human-only; config-dependent skills tell the user to invoke it explicitly instead of attempting a Skill-tool call. `scripts/audit_portability.py` now rejects a model-disabled target on any `Call the Skill tool with ...` edge, with unit coverage for both forbidden internal calls and valid human-only guidance.

**Remaining risk:** These changes establish the static invocation graph only. Skill discovery and nested execution still require live-host proof.

**Done when:**

- representative nested calls succeed in live Claude Code and Codex sessions.

Reference: [Claude Code skill invocation](https://code.claude.com/docs/en/slash-commands#control-who-invokes-a-skill).

### [ ] 2. Scope transcript directories by both harness and workspace

**Failure:** `schemas/config.schema.json` stores one `transcripts_directory` per harness. Running `setup-dstack` for the same harness in workspace B overwrites the directory saved for workspace A. Returning to A can make transcript-backed skills read B's transcripts.

This contradicts the documented workspace-scoped guarantee and can cross a project privacy boundary.

**Affected areas:** `schemas/config.schema.json`, `skills/setup-dstack/scripts/configure.py`, `setup-dstack`, `recall`, `reflect`, `show-me-your-work`, `dstack-mode` transcript-backed playbooks, documentation, audit rules, and tests.

**Done when:**

- transcript configuration is keyed by a stable active-workspace identity beneath each harness;
- setup updates only the active harness/workspace entry and preserves every other entry;
- consumers verify that the selected entry matches the active workspace before reading it;
- switching A -> B -> A returns the correct transcript directory each time;
- no consumer can silently fall back to another workspace's directory.

## P1: Model binding and harness identity

### [ ] 3. Define how Claude Code applies both model and effort to a spawned subagent

**Failure:** Claude Code documents `model` and `effort` on subagent definitions, but documents only a per-invocation `model` override. Dstack installs no profile-backed definitions under `~/.claude/agents/`. A generic Agent-tool call may therefore use the configured model while inheriting the session effort, violating dstack's exact-pair contract.

**Affected areas:** `setup-dstack`, every profile-consuming skill, installer structure if generated Claude agents are needed, and live-host conformance tests.

**Done when:**

- the current Claude Agent tool schema is inspected rather than inferred;
- dstack has an executable, documented way to apply both values from a profile;
- the consuming skill can confirm or detect rejection of the requested pair;
- no skill silently inherits session effort;
- at least one non-parent model/effort pair is proven in a live Claude Code subagent.

Reference: [Claude Code subagent fields and model selection](https://code.claude.com/docs/en/sub-agents#supported-frontmatter-fields).

### [ ] 4. Validate Codex profiles against the subagent operation, not only the general catalog

**Failure:** `codex debug models` can expose models that the current Codex subagent tool does not accept as overrides. On the 2026-08-26 inspection, the catalog included `gpt-reserve`, `gpt-5.4-mini`, and `codex-auto-review`, while the active spawn operation did not accept them.

`setup-dstack` currently says to use a trustworthy host catalog but does not require the active subagent tool schema to take precedence. Setup can save a pair that works for a main session and fails for every dstack worker.

**Affected areas:** `skills/setup-dstack/SKILL.md`, profile reconciliation, invalid-binding behavior, tests, and Codex live proof.

**Done when:**

- setup reads the current spawn operation's accepted model and effort values first;
- `codex debug models` is only a fallback when its results can be intersected with spawn support or are clearly reported as unverified for spawning;
- unsupported catalog-only models cannot be saved as validated worker profiles;
- stale or rejected pairs enter `invalid_bindings` and require replacement.

### [ ] 5. Define canonical harness IDs

**Failure:** "the lowercase identity of the active harness" is not deterministic. Different sessions may reasonably choose `claude`, `claude-code`, or another variant, causing setup and consuming skills to select different host entries.

Removing `host_override` makes canonical identity more important because there is no recovery path when two agents normalize the host differently.

**Affected areas:** `setup-dstack`, every config-dependent skill, schema validation, audit rules, tests, and documentation.

**Done when:**

- supported harnesses have fixed canonical IDs, initially `codex`, `claude`, and `cursor` unless live inspection shows a better stable mapping;
- setup and all consumers derive the same ID from the same rule;
- unknown harnesses fail closed with the exact observed identity evidence;
- aliases cannot create duplicate entries for one harness.

## P1: Parallelism and isolation

### [ ] 6. Batch fan-out to the active harness's concurrency limit

**Failure:** `arena` and `swarm` require all N workers to spawn at once. `how` can request four explorers, and `why` can request up to seven source investigators. A Codex session with three child slots cannot satisfy those instructions simultaneously.

Dropouts are not acceptable when every coverage slice is required, and performing the missing passes in the parent can destroy the intended independence.

**Affected areas:** `arena`, `swarm`, `how`, `why`, `reflect`, `interrogate`, and any `dstack-mode` playbook that fans out workers.

**Done when:**

- each workflow discovers or conservatively derives available child capacity;
- work is launched in bounded waves when N exceeds that capacity;
- required coverage slices are not treated as optional dropouts;
- the report distinguishes parallel waves, serialized fallback, and lost independence;
- live Codex and Claude tests cover N greater than the available child capacity.

### [ ] 7. Remove the false automatic-worktree assumption and destructive fallback

**Failure:** `skills/dstack-mode/playbooks/opening-a-pr.md` says multiple `Task` calls on one branch each receive their own worktree. Ordinary Codex and Claude subagents share the current working directory unless isolation is explicitly arranged. The same instruction suggests `git reset --hard`, which can destroy uncommitted work.

**Affected areas:** `opening-a-pr.md`, `arena`, `swarm`, feature and autopilot playbooks, and any instructions that allow multiple writers.

**Done when:**

- no skill claims that native spawning automatically creates a worktree;
- every parallel writer receives an explicitly created and verified isolated directory or worktree;
- read-only workers may share a checkout only when their tool boundary really prevents writes, or the limitation is disclosed;
- no generic recovery path uses `git reset --hard` or overwrites user work;
- isolation is proven in both live harnesses with two simultaneous writers.

## P1: Conditional runtime dependencies

### [ ] 8. Preflight or conditionalize non-generic dstack-mode playbooks

**Failure:** Several retained playbooks require features that are not implied by having a Skill tool and native subagents:

- `/goal` or an equivalent persistent goal mechanism;
- scheduled wake or loop facilities;
- background liveness probes and replacement workers;
- Graphite and the `gt` CLI;
- GitHub authentication and repository permissions;
- long-running persistence after the interactive session ends.

The strongest examples are `autopilot-full.md`, `autopilot-stack.md`, `autonomous-run.md`, `babysit.md`, and `shipping.md`.

**Affected areas:** `dstack-mode` router, the playbooks above, README claims, and live conformance documentation.

**Done when:**

- each conditional playbook names its prerequisites before performing work;
- missing Graphite, GitHub authentication, goal, wake, or persistence support stops or selects a documented reduced workflow;
- a reduced workflow never claims unattended persistence or automatic wake behavior;
- provider-era names such as `Task` are removed from executable instructions;
- generic dstack documentation does not imply these conditional workflows work everywhere.

## P2: Installation and configuration consistency

### [ ] 9. Make Claude installation requirements explicit

**Failure:** README calls the `~/.claude/skills` links optional, but local Claude Code discovers personal skills from `~/.claude/skills/`, not `~/.agents/skills/`. Running only `python3 install.py` installs for Codex but leaves Claude without dstack.

**Affected areas:** `README.md`, `docs/guide/01-install-and-configure.md`, installer help text, and installation tests.

**Done when:**

- documentation says `--with-claude-links` is required for local Claude Code use;
- the default Codex-only path and combined Codex/Claude path are shown separately;
- installation verification checks that both harnesses discover `setup-dstack` and `dstack-mode`;
- unrelated entries under `~/.claude/skills` remain untouched.

Reference: [Claude Code personal skill locations](https://code.claude.com/docs/en/slash-commands#where-skills-live).

### [ ] 10. Make `configure.py validate` fail when the fixed config file is missing

**Failure:** `configure.py validate` currently reports a missing `~/.dstack/config.json` as valid "implicit defaults". That conflicts with the product rule that config-dependent workflows stop explicitly when the fixed file does not exist.

`show` may still need an empty initial state for first-time setup, but `validate` should not present absence as configured success.

**Affected areas:** `skills/setup-dstack/scripts/configure.py` and `tests/test_configure.py`.

**Done when:**

- `validate` exits non-zero and names the missing fixed path;
- `show` retains an intentional first-setup behavior if setup needs it;
- config-dependent skills use a deterministic validation path rather than manually approximating schema validation;
- setup remains the only workflow allowed to create the missing file.

### [ ] 11. Preserve reconciled invalid bindings in the setup proposal

**Failure:** `setup-dstack` requires unavailable former pairs to be recorded in `invalid_bindings`, but its "exact" proposal example hardcodes an empty array. Following the example literally erases the reconciliation result.

**Affected areas:** `skills/setup-dstack/SKILL.md`, configurator tests, and reconciliation reporting.

**Done when:**

- the proposal example uses the reconciled invalid-binding list rather than `[]` as an unconditional value;
- unavailable old pairs remain recorded until they become valid again;
- a test covers a non-empty reconciled list through `apply` and a later refresh that removes a restored pair.

### [ ] 12. Correct the `interrogate` profile assignment contradiction

**Failure:** `interrogate` says to launch reviewers across all four profiles, but the per-reviewer instructions assign every reviewer a `skeptical-reviewer` binding. This removes the intended model diversity.

**Affected area:** `skills/interrogate/SKILL.md` around Steps 3 and 4.

**Done when:**

- every reviewer receives the concrete binding selected for its named profile;
- repeated bindings are disclosed as reduced model diversity;
- the output reports the actual model and effort used by each reviewer.

### [ ] 13. Restore executable validation commands to `AGENTS.md`

**Failure:** `AGENTS.md` says to run "the validation commands in AGENTS.md" but does not contain those commands. A maintainer following only repository instructions cannot know the required gate set.

**Affected areas:** `AGENTS.md` and its `CLAUDE.md` symlink consumer.

**Done when:**

- `AGENTS.md` contains the exact portability audit, unit-test, JSON, and changed-skill validation commands;
- it states that these are static gates rather than live-host proof;
- the instruction does not point recursively to itself for missing information.

### [ ] 14. Require authorization before `reflect` files external backlog items

**Failure:** `reflect` says Backlog findings are filed automatically. A reflection request does not necessarily authorize creating tickets or mutating an external tracker.

**Affected areas:** `skills/reflect/SKILL.md` and its synthesizer output contract.

**Done when:**

- `reflect` presents proposed backlog items with the Accepted/Rejected/Backlog result;
- it asks for explicit approval before any external write;
- absence of a tracker or authorization leaves an in-chat backlog without blocking skill edits;
- the final report distinguishes proposed from actually filed items.

## Validation baseline

Baseline observed on 2026-08-26:

- `python3 scripts/audit_portability.py`: 0 errors;
- `python3 -m unittest discover -s tests -v`: 56 tests passed;
- `python3 -m json.tool schemas/config.schema.json`: passed;
- Skill Creator `quick_validate.py`: 18 valid, 30 rejected only because the bundled validator does not recognize `disable-model-invocation`.

These results prove repository structure and static contracts only. They do not prove skill discovery, cross-skill invocation, model/effort enforcement, transcript isolation, worktree isolation, bounded fan-out, wake persistence, or end-to-end behavior in Codex or Claude Code.

## Completion order

Work in this order to avoid validating behavior on top of broken foundations:

1. Live Claude Code and Codex proof for the resolved skill-to-skill invocation policy.
2. Workspace-keyed transcript storage.
3. Canonical harness IDs.
4. Claude and Codex model/effort application.
5. Bounded fan-out and explicit worktree isolation.
6. Conditional runtime playbooks.
7. Installation and smaller configuration/documentation inconsistencies.
