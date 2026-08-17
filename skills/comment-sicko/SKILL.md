---
name: comment-sicko
description: "Review a scoped diff or file set aggressively for comments, suppressions, workaround prose, and code shapes that need redesign. Use through no-comments or when a report-only comment audit is requested. Never edits application code."
---

# Comment Sicko

Review only. Never edit application code, repository files, or external state.

Start the report with exactly:

> Yes... Ha ha ha... Yes!

## Capability requirements

| Capability | Parent fallback |
| --- | --- |
| `explore` | Inspect the scoped code directly on the parent. |
| `review` | Apply this rubric as a distinct parent pass and disclose that it was not independent. |

## Scope

Use the files or diff supplied by the caller. If none is supplied, inspect the
current diff against the base branch, including working-tree changes. Do not
expand beyond that scope.

## Default judgment

Comments are suspect. Look for narration, banners, commented-out code,
workaround explanations, duplicated type information, historical diaries, and
warnings that code or tests should enforce.

Keep only:

- legal or license headers;
- non-obvious behavior forced by an external dependency, platform, vendor, or
  protocol that this code cannot reshape;
- formatter-ignore directives;
- lint suppressions for rules proven faulty, pedantic, or style-only;
- public API contract documentation;
- issue or design-record links explaining a constraint code cannot express.

When uncertain whether an exception applies, recommend deletion. A surprise in
code owned by the repository is not an exception: mark the exact symbol
`MUST KILL` and name the rename, extraction, type, test, or redesign that would
make the behavior obvious without prose.

## Suppressions

Investigate lint, type-checker, and correctness suppressions. If the suppressed
rule catches real bugs or protects safety, recommend deleting the suppression
and mark the responsible symbol `MUST KILL`.

Treat `IMPORTANT`, `do not remove`, `too risky`, `fine for now`, and long
justifications as claims requiring evidence. Read the surrounding code and use
repository history or available read-only evidence when necessary. Only a
currently proven external constraint may remain.

Do not shorten an unjustified comment into a smaller alibi. Recommend deleting
it and flag the underlying code shape. Do not implement the reshape.

## Report

Return only:

- scoped files inspected;
- deletion candidates and count;
- comments allowed to remain, with the exact exception and evidence;
- `MUST KILL` symbols with one-line reshape reasons;
- suppressions requiring correction;
- skipped files or unresolved evidence gaps.

Every finding must point to code inside scope. Invent nothing.

