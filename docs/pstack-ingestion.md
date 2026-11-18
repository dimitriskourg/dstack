# How dstack takes pstack updates

dstack is a curated, harness-neutral port of pstack, not a mirror. Absorb upstream with `scripts/pstack_sync.py`. Never edit pstack. Keep schema version 3. The pin, exclusion lists, and allowed drift live in `PSTACK_SYNC.md`.

Standing overlays (do not undo):

- Take upstream wording as-is on kept files. Do not paraphrase skill, playbook, or guide text.
- Keep four `dstack-config` profiles (`fast-explorer`, `feature-worker`, `bug-worker`, `skeptical-reviewer`), not Opus-first or default-model routing.
- `worker.md`: keep pstack text plus one Autonomy line (stop before an unauthorized push, PR or MR, ticket update, or comment).

## Classify, then copy

On each absorb:

1. Copy kept files from rewritten upstream. Mechanical rewrites are the only automatic edits (`PSTACK_SYNC.md`).
2. Map `docs/guide/` onto `skills/dstack-help/references/guide/` (`02-poteto-mode.md` → `02-dstack-mode.md`) and treat those pages like kept skills.
3. Never auto-copy a brand-new upstream file (skill, playbook, guide page, or other). It is needs-decision. Check dstack rules, including no unauthorized push, PR, ticket, or comment.
4. Record every skip or kept-dstack choice in the **sync PR description and in `PSTACK_SYNC.md`**. Never only in private notes.
5. Run `--drift`. Paste that output into every sync PR.
6. `--decided` does not move the pin unless every pending file matches rewritten upstream at the target commit or is listed under Not imported / Kept dstack wording / Allowed drift.

## Weekly absorb

From a clean tree at the repository root:

```bash
python3 scripts/pstack_sync.py --drift
python3 scripts/pstack_sync.py --dry-run
python3 scripts/pstack_sync.py <commit>            # clean apply; moves the pin on exit 0
python3 scripts/pstack_sync.py <commit> --decided  # after listed hand fixes only
```

Then the `AGENTS.md` static gates. One PR per pstack sync, never mixed with our own changes. Open as draft. Title: `sync: pstack <version> (<short commit>)`. Description: From and To with the pstack compare link; Applied; Decided (choice and one-line why); Not imported (also in `PSTACK_SYNC.md`); Checks, including pasted `--drift` output.

## Independent review

Before a sync PR is marked ready, a **separate reviewer** (a strong model, not the absorb agent) reviews it using the pasted drift output. That reviewer checks that every unlisted difference is a defect, every listed skip has a reason in the PR body and `PSTACK_SYNC.md`, and standing overlays still hold. The owner decides ready and merge.

## Static gates (not live-harness proof)

```bash
python3 scripts/audit_portability.py
python3 -m unittest discover -s tests -v
python3 -m json.tool schemas/config.schema.json >/dev/null
git diff --check
python3 scripts/pstack_sync.py --drift
```
