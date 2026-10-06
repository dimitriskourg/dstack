### Opening a PR

Explicit only. Run after the user asks to publish already verified local work as a GitHub pull request or GitLab merge request.

**Checkout safety.** Use the current checkout when it is dedicated to this change. Inspect the branch, status, and complete diff before staging. Preserve unrelated tracked and untracked work, stage explicit paths rather than `git add -A`, and stop when the intended patch cannot be separated safely. Never discard repository state, checkout over user changes, or use another destructive recovery shortcut.

**Commits.** Commit liberally; rebase into small, ordered commits before opening PRs. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs in a just-made commit; new commit when separable.

**PRs.** Call the Skill tool with `deslop`. Do so before commit. Call the Skill tool with `no-comments`. Do so before review. For every PR title, description, and commit body, Call the Skill tool with `technical-writing`. Then Call the Skill tool with `unslop`. Apply every technical-writing layer except Diátaxis. Use one word for each action, keep articles, and avoid `-ing` when a plain verb works.

**Titles.** Use Conventional Commits in the form `type(scope): subject`. Use `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf` as the type. Use the changed area, such as `dstack` or `dstack-mode`, as the scope. Keep the subject short and imperative. Apply the same skill passes as the body. Name a real symbol when one carries the change. For example, `fix(dstack): retarget opening-a-pr babysit trigger`. Do not add a trailing period.

**Descriptions.** The request body is a briefing, not the lab notebook. A reviewer who has the diff should learn why the change exists, what it leaves out, what it could break, and how you proved it works, in under a minute. Write short, simple sentences with few identifiers. Do not write walls of text. The squash commit body is the request body. If the body would make the squash commit longer than about 40 lines, cut the body.

Put each section under a `##` heading, not a bold lead-in, so the sections stand apart. Use these sections in order. Drop a section when it has nothing to say.

- `## Why` gives the problem and the approach in one to three short sentences. Do not list SHAs or rebase genealogy. Do not add a "based on main" preamble.
- `## What changed` has one to three short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope` always names what the PR covers and what it deliberately leaves out, for example a related follow-up or a known gap. Use one to three short items. Do not list symbols or paths, and do not write a file-by-file essay.
- `## Tradeoffs` names only rejected alternatives that a reviewer would otherwise ask about. Skip this section when there was no real choice.
- `## Blast Radius` gives one or two sentences on who or what the change touches and why that is safe or risky. If main is red, state the cost of leaving it red.
- `## Verification` has one to three bullets. Each bullet names a real run path and its outcome. For a performance change, report one primary number with its unit in `before → after` form. Link the arena or swarm directory for the remaining evidence. Do not include sample-size methodology, swarm recitals, or metric tables.

After these sections, attach videos or screenshots when they prove a claim. Do not paste full SHAs, swarm or arena lane recitals, lever-correction essays, file-by-file checklists, or "CLEAN" verdicts. Put these details in a linked artifact. A commit body does not restate its subject.

**Size and dependent changes.** Prefer narrow, independently reviewable changes to one large request. When changes are genuinely dependent, preserve their order with ordinary Git branches and the forge's base-branch support. Branch from the default branch only for independent work. Do not introduce a stack manager.

**Forge.** Resolve the repository's configured remote before choosing a CLI. Use authenticated `gh` for GitHub and authenticated `glab` for GitLab. Stop when the remote is ambiguous, the matching CLI is unavailable, or authentication fails. Do not choose a forge because one CLI merely happens to be installed.

**Readiness.** Open every request ready, never as a draft. Verify the created request with the matching CLI before referring to its status. Return the actual forge URL.

**Babysit.** Opening a request does not start Babysit. Post the URL and stop at the requested delivery boundary. Run a separate Babysit pass only when the user explicitly asks for PR or merge-request follow-up.

Before opening the request, Call the Skill tool with `interrogate`. Call the Skill tool with `unslop`. Call the Skill tool with `no-comments`. Return the URL and do not start Babysit.
