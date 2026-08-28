# Known portability and runtime issues

Updated 2026-08-27. This backlog contains unresolved defects inside dstack's [supported scope](docs/guide/06-supported-scope.md). Intentional exclusions are documented there and in `DIFFERENCES.md`; they are not backlog items. Issue numbers remain stable where an earlier backlog item still applies.

Static validation is not live-host proof. When an item changes runtime behavior, verify it in every affected live harness before checking it off.

## P0: Blocking orchestration failures

### [ ] 1. Prove nested skill calls in live Claude Code, Codex, and Cursor

**Implemented design:** Invocation has two portable states. Human-only roots declare `disable-model-invocation: true` and mirror it with `policy.allow_implicit_invocation: false`. Any skill used as an internal callee omits both restrictions. The portability audit rejects an internal edge to a model-disabled skill.

**Remaining risk:** Static metadata and graph checks do not prove that each live host discovers the installed skill and completes representative nested calls.

**Done when:**

- representative nested calls succeed in live Claude Code, Codex, and Cursor sessions;
- denied nested spawning falls back to the current agent and discloses the lost independence.

### [ ] 2. Scope transcript directories by both harness and repository

**Failure:** `schemas/config.schema.json` stores one `transcripts_directory` per harness. Running `setup-dstack` for the same harness in repository B overwrites the directory saved for repository A. Returning to A can make transcript-backed skills read B's transcripts.

This contradicts the retained repository-scoped contract and can cross a project privacy boundary.

**Affected areas:** `schemas/config.schema.json`, `skills/setup-dstack/scripts/configure.py`, setup, Recall, Reflect, Automate Me, Show Me Your Work, Session Pickup, Eval, documentation, audit rules, and tests.

**Done when:**

- transcript configuration is keyed by a stable active-repository identity beneath each harness;
- setup updates only the active harness/repository entry and preserves every other entry;
- consumers verify the selected entry matches the active repository before reading it;
- switching A -> B -> A returns the correct transcript directory each time;
- no consumer can silently fall back to another repository's directory.

## P1: Model binding and harness identity

### [ ] 4. Validate Codex profiles against the subagent operation, not only the general catalog

**Failure:** `codex debug models` can expose models that the current Codex subagent operation does not accept as overrides. Setup can save a pair that works for a main session and fails for every dstack worker.

**Affected areas:** `skills/setup-dstack/SKILL.md`, profile reconciliation, invalid-binding behavior, tests, and Codex live proof.

**Done when:**

- setup reads the current spawn operation's accepted model and effort values first;
- the general catalog is only a fallback whose spawning limitations are explicit;
- unsupported catalog-only models cannot be saved as validated worker profiles;
- stale or rejected pairs enter `invalid_bindings` and require replacement.

### [ ] 5. Define canonical harness IDs

**Failure:** "the lowercase identity of the active harness" is not deterministic. Different sessions may choose aliases such as `claude` and `claude-code`, causing setup and consuming skills to select different host entries.

**Done when:**

- supported harnesses have the fixed IDs `codex`, `claude`, and `cursor`, unless live inspection requires another stable mapping;
- setup and all consumers derive the same ID from the same rule;
- unknown harnesses fail closed with the observed identity evidence;
- aliases cannot create duplicate entries for one harness.

## P1: Parallel read-only fan-out

### [ ] 6. Apply bounded waves in every retained fan-out workflow

**Failure:** Arena, Swarm, Interrogate, and Reflect now require bounded waves, but How, Why, Eval, Architect composition, and other retained callers can still request more children than the active harness can run simultaneously.

Dstack serializes repository writers. This item concerns read-only exploration, review, and independent artifacts outside the repository.

**Done when:**

- every retained fan-out workflow discovers or conservatively derives available child capacity;
- N greater than capacity runs in bounded waves;
- required slices are retried or completed serially instead of dropped;
- reports distinguish parallel waves, serialized fallback, and lost independence;
- live Codex, Claude Code, and Cursor tests cover N greater than available capacity.

## P1: Forge workflows

### [ ] 15. Prove GitHub and GitLab request flows live

**Implemented design:** Opening a PR resolves the configured remote and uses authenticated `gh` for GitHub or `glab` for GitLab. Babysit is explicit, uses the matching forge verdict, runs only while the active session can supervise it, and stops at merge-ready without authorizing a merge. Why uses local Git first and treats unavailable forge discussion as an evidence gap.

**Remaining risk:** The GitHub and GitLab CLI field mappings, approval states, unresolved-thread handling, pipeline retry behavior, and safe comment-reply calls have not been exercised end to end.

**Done when:**

- opening and verifying a ready request succeeds in a live GitHub and GitLab test repository;
- Babysit `check`, `threads-only`, and `drive` reach correct terminal verdicts on both forges;
- comment bodies are passed as data and cannot become shell input;
- neither flow merges, enables auto-merge, force-pushes, or changes request topology without separate authorization.

## P2: Installation and configuration consistency

### [ ] 9. Prove Claude installation and discovery

**Implemented documentation:** The README and install guide now say `--with-claude-links` is required for local Claude Code use, while Codex and Cursor use the canonical `~/.agents/skills` installation.

**Done when:**

- installation verification proves `setup-dstack` and `dstack-mode` are discoverable in Claude Code;
- Codex and Cursor discovery is verified from the canonical installation;
- unrelated entries under `~/.claude/skills` remain untouched.

### [ ] 10. Make `configure.py validate` fail when the fixed config file is missing

**Failure:** `configure.py validate` currently reports a missing `~/.dstack/config.json` as valid implicit defaults. That conflicts with the rule that config-dependent workflows stop explicitly when the fixed file does not exist.

**Done when:**

- `validate` exits non-zero and names the missing fixed path;
- `show` retains an intentional first-setup behavior;
- config-dependent skills use a deterministic validation path;
- setup remains the only workflow allowed to create the missing file.

### [ ] 11. Preserve reconciled invalid bindings in the setup proposal

**Failure:** Setup requires unavailable former pairs to be recorded in `invalid_bindings`, but its proposal example hardcodes an empty array. Following the example literally erases the reconciliation result.

**Done when:**

- the proposal uses the reconciled invalid-binding list;
- unavailable old pairs remain recorded until they become valid again;
- tests cover a non-empty reconciled list through apply and later restoration.

### [ ] 13. Restore executable validation commands to `AGENTS.md`

**Failure:** `AGENTS.md` says to run "the validation commands in AGENTS.md" but does not contain those commands.

**Done when:**

- `AGENTS.md` contains the exact portability audit, unit-test, JSON, diff, and changed-skill validation commands;
- it states that these are static gates rather than live-host proof;
- the instruction no longer points recursively to missing information.

## Validation baseline

Observed after the 2026-08-27 scope cut:

- `python3 scripts/audit_portability.py`: 0 errors;
- `python3 -m unittest discover -s tests -v`: 68 tests passed;
- `python3 -m json.tool schemas/config.schema.json`: passed;
- `git diff --check`: passed;
- Skill Creator `quick_validate.py`: 8 changed skills passed; 4 were rejected only because the bundled validator does not accept dstack's `disable-model-invocation` extension.

These static results do not prove skill discovery, nested invocation, model/effort enforcement, repository transcript isolation, bounded fan-out, forge behavior, or end-to-end behavior in Codex, Claude Code, or Cursor.

## Completion order

1. Repository-keyed transcript storage and canonical harness IDs.
2. Live nested invocation and Codex spawn-operation profile validation.
3. Bounded fan-out across every retained caller.
4. GitHub and GitLab request-flow proof.
5. Installation and smaller setup/documentation inconsistencies.
