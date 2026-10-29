### Opening a PR

Explicit only. Run after the user asks to publish already verified local work as a GitHub pull request or GitLab merge request.

**Checkout safety.** Use the current checkout when it is dedicated to this change. Inspect the branch, status, and complete diff before staging. Preserve unrelated tracked and untracked work, stage explicit paths rather than `git add -A`, and stop when the intended patch cannot be separated safely. Never discard repository state, checkout over user changes, or use another destructive recovery shortcut.

**Commits.** Commit liberally. Rebase into small, ordered commits before opening PRs. Each commit is a future PR: landable, ordered to tell the story. Amend when the fix belongs in a just-made commit. New commit when separable. Commit bodies don't restate the subject.

**PRs.** Call the Skill tool with `deslop`. Do so before commit. Call the Skill tool with `no-comments`. Do so before review. For every PR title, description, and commit body, Call the Skill tool with `technical-writing`. Then Call the Skill tool with `unslop`. Apply every technical-writing layer except Diátaxis. Use one word for each action, keep articles, and avoid `-ing` when a plain verb works.

**Titles.** Conventional Commits `type(scope): subject`, no trailing period. Type such as `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, or `perf`. Scope is the area, such as `dstack` or `dstack-mode`. Subject is short, imperative, and names a real symbol when one carries the change, for example `fix(dstack): retarget opening-a-pr babysit trigger`.

**Descriptions.** The request body is a one-minute briefing, not a lab notebook, for a reviewer who has the diff. It says why the change exists, what it leaves out, what it could break, and how you proved it works. Write short, simple sentences with few identifiers, no walls of text. The body becomes the squash commit body, so keep that commit under about 40 lines. Use `##` headings, not bold lead-ins, in this order, and drop a section with nothing to say:

- `## Why`: the problem and approach, 1–3 short sentences. No SHAs, rebase genealogy, or "based on main" preamble.
- `## What changed`: 1–3 short bullets. Name a real symbol or path only when it carries the change. Name both sides of a rename or retarget.
- `## Scope`: always. 1–3 short items on what it covers and what it deliberately leaves out (a follow-up, a known gap). No symbols, paths, or file-by-file essay.
- `## Tradeoffs`: only rejected alternatives a reviewer would otherwise ask about. Skip when there was no real choice.
- `## Blast Radius`: 1–2 sentences on who or what it touches and why that is safe or risky. If main is red, state the cost of leaving it red.
- `## Verification`: 1–3 bullets, each a real run path and its outcome. Perf: one primary number with its unit, `before → after`, and a link to the arena or swarm directory for the rest. No sample-size methodology, swarm recitals, or metric tables.

After the sections, attach videos or screenshots when they prove a claim. Full SHAs, swarm or arena lane recitals, lever-correction essays, file-by-file checklists, and "CLEAN" verdicts go in a linked artifact, not the body.

**Size and dependent changes.** Prefer narrow, independently reviewable changes to one large request. When changes are genuinely dependent, preserve their order with ordinary Git branches and the forge's base-branch support. Branch from the default branch only for independent work. Do not introduce a stack manager.

**Forge.** Resolve the repository's configured remote before choosing a CLI. Use authenticated `gh` for GitHub and authenticated `glab` for GitLab. Stop when the remote is ambiguous, the matching CLI is unavailable, or authentication fails. Do not choose a forge because one CLI merely happens to be installed.

**Readiness.** Open every request ready, never as a draft. Verify the created request with the matching CLI before referring to its status. Return the actual forge URL.

**Babysit.** Opening a request does not start Babysit. Post the URL and stop at the requested delivery boundary. Run a separate Babysit pass only when the user explicitly asks for PR or merge-request follow-up.

Return the URL and do not start Babysit.
