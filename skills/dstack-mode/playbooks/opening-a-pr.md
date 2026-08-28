### Opening a PR

Explicit only. Run after the user asks to publish already verified local work as a GitHub pull request or GitLab merge request.

**Checkout safety.** Use the current checkout when it is dedicated to this change. Inspect the branch, status, and complete diff before staging. Preserve unrelated tracked and untracked work, stage explicit paths rather than `git add -A`, and stop when the intended patch cannot be separated safely. Never discard repository state, checkout over user changes, or use another destructive recovery shortcut.

**Commits.** Commit liberally; rebase into small, ordered commits before opening PRs. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs in a just-made commit; new commit when separable.

**PRs.** Call the Skill tool with `deslop`. Do so before commit. Call the Skill tool with `no-comments`. Do so before review. For every PR title, description, and commit body, Call the Skill tool with `technical-writing`. Then Call the Skill tool with `unslop`. Apply every technical-writing layer except Diátaxis. Use one word for each action, keep articles, and avoid `-ing` when a plain verb works.

**Titles.** Use Conventional Commits in the form `type(scope): subject`. Use `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf` as the type. Use the changed area, such as `dstack` or `dstack-mode`, as the scope. Keep the subject short and imperative. Apply the same skill passes as the body. Name a real symbol when one carries the change. For example, `fix(dstack): retarget opening-a-pr babysit trigger`. Do not add a trailing period.

**Descriptions.** Use these sections in order. Drop a section when it is empty.

- `## Why`. State the intent and why this approach fits.
- `## Scope`. State facts from the diff. Name real symbols and paths. Name both sides of a rename or retarget. State what is in and out when the boundary matters.
- `## Tradeoffs`. State real choices only. Skip this section when there are none.
- `## Blast Radius`. State who and what the change touches. Explain why the change is safe or risky. If main is red without the fix, name the continuing cost.
- `## Verification`. State how you ran each check and its rigor. Name the real path, such as the control skill for the surface or the targeted tests. State the outcome of each check, not only the command name.

After these sections, attach videos or screenshots when they prove a claim. Do not use `## Summary` or `## Test plan` boilerplate. A commit body does not restate its subject.

**Size and dependent changes.** Prefer narrow, independently reviewable changes to one large request. When changes are genuinely dependent, preserve their order with ordinary Git branches and the forge's base-branch support. Branch from the default branch only for independent work. Do not introduce a stack manager.

**Forge.** Resolve the repository's configured remote before choosing a CLI. Use authenticated `gh` for GitHub and authenticated `glab` for GitLab. Stop when the remote is ambiguous, the matching CLI is unavailable, or authentication fails. Do not choose a forge because one CLI merely happens to be installed.

**Readiness.** Open every request ready, never as a draft. Verify the created request with the matching CLI before referring to its status. Return the actual forge URL.

**Babysit.** Opening a request does not start Babysit. Post the URL and stop at the requested delivery boundary. Run a separate Babysit pass only when the user explicitly asks for PR or merge-request follow-up.

Before opening the request, Call the Skill tool with `interrogate`. Call the Skill tool with `unslop`. Call the Skill tool with `no-comments`. Return the URL and do not start Babysit.
