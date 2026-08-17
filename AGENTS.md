# dstack repository instructions

Read `REMAINING.md` before changing skills, adapters, installation, model
configuration, or upstream parity.

## Boundaries

- Treat pstack and ystack as immutable upstream inputs. Port behavior into this
  repository; do not edit an upstream checkout as part of a dstack change.
- Keep portable skills free of provider tool schemas, concrete model slugs,
  provider configuration paths, private transcript layouts, and unsupported
  frontmatter.
- Put host mechanics in `adapters/`, shared semantics in `contracts/`, strict
  data shapes in `schemas/`, and deterministic repeated behavior in scripts.
- Every optional capability used by a skill needs an explicit parent-agent
  fallback.
- Preserve `poteto-mode` -> `dstack-mode` and `setup-pstack` -> `setup-dstack`.
  Do not add legacy aliases without an explicit product decision.
- Never install Bun or another runtime silently.
- Do not add updater, doctor, uninstall, ownership manifests, or configuration
  migrations speculatively. The current product is intentionally minimal.
- Do not claim Codex, Cursor, Claude, wake, history, browser, native, or
  multi-agent conformance from static checks.

## Required validation

Run after relevant changes:

```bash
python3 scripts/audit_portability.py
python3 -m unittest discover -s tests -v
python3 -m json.tool schemas/config.schema.json >/dev/null
```

Validate every changed skill with Skill Creator's `quick_validate.py`. Record
live exercise separately in `conformance/HOST_MATRIX.md`.

## Upstream sync

For a new pstack version, record the exact old and new revisions, inspect the
diff, inventory skills and playbooks, classify each change, and update
`REMAINING.md`. Zero unexplained source differences is the goal; mechanical
provider-name replacement is not a port.
