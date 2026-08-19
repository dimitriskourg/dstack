# Install and configure dstack

This page covers the first installation, optional Claude Code links, and
per-host model choices.

## Preview the installation

Clone or open the repository, then run:

```bash
python3 install.py --dry-run
```

The dry run lists every skill and support directory that would be copied. It
also reports collisions. It performs reads and checks only: no directories,
copies, links, configuration, or dependencies are created.

The normal destinations are:

```text
~/.agents/skills/<skill>/
~/.dstack/adapters/
~/.dstack/contracts/
~/.dstack/schemas/
```

Set `DSTACK_HOME` before running the installer when `~/.dstack` is not the
desired support location.

## Understand collision behavior

Normal installation is intentionally first-install-only. If any destination skill,
support directory, file, valid link, or broken link already exists, the entire
installation stops before writes begin.

This is especially important for generic skill names such as `how`, `why`, and
`architect`. dstack never assumes it owns an existing directory.

Review each collision. Do not delete or replace an existing skill until you
know who owns it and whether anything still depends on it.

## Install

After reviewing a clean dry run:

```bash
python3 install.py
```

The installer copies complete skill packages, including bundled scripts and
references. It copies dstack adapters, contracts, schemas, notices, and any
future shipped runtime into `DSTACK_HOME`.

It does not:

- install Bun or Python dependencies;
- overwrite a previous installation;
- repair or uninstall dstack;
- create a model configuration automatically.

## Add Claude Code compatibility links

`~/.agents/skills` remains canonical. When Claude Code needs compatibility
links, preview and install them explicitly:

```bash
python3 install.py --dry-run --with-claude-links
python3 install.py --with-claude-links
```

This creates one link per dstack-owned skill under `~/.claude/skills`. It never
replaces the complete Claude skills directory.

If the first installation ran without links, add them later with the same flag
on an update. See [Update an installed copy](#update-an-installed-copy).

On Windows the installer creates directory junctions rather than symbolic
links. A junction needs no elevated shell or Developer Mode, and hosts discover
it exactly as they discover a link on macOS and Linux.

## Update an installed copy

From a trusted dstack checkout, preview the exact managed destinations first:

```bash
python3 install.py --update --dry-run
python3 install.py --update
```

Update mode requires the canonical skill and support roots to exist, and refuses
mismatched skill identities or wrong existing destination types before writing.
It creates missing managed artifacts inside those roots, stages every replacement
next to its destination, and
rolls completed replacements back if a later operation fails. It replaces only
the dstack skill packages and support files named by the repository, and preserves
`DSTACK_HOME/config.json`.

An update replaces each managed skill package as a whole. Local edits inside an
installed skill directory are lost. Keep local work outside `~/.agents/skills`.

Without `--with-claude-links`, an update leaves `~/.claude/skills` untouched.

### Add or refresh Claude Code links during an update

Pass the flag to sync links in the same run:

```bash
python3 install.py --update --dry-run --with-claude-links
python3 install.py --update --with-claude-links
```

This links every dstack-owned skill that is not linked yet, including skills
added since the first installation, and leaves correct existing links alone. A
destination that is not a dstack link stops the update before writes: a real
directory reports `expected compatibility link`, and a link aimed somewhere else
reports `compatibility link points elsewhere`. Resolve those by hand, since
dstack never assumes it owns them.

## Configure models in each host

Run `setup-dstack` in Codex, Cursor, or another supported host where you want
custom model assignments.

The skill:

1. selects the active host adapter;
2. enumerates model-effort pairs only from a trustworthy host catalogue;
3. loads the current `DSTACK_HOME/config.json` or implicit defaults;
4. shows current and proposed values for all roles;
5. waits for confirmation;
6. atomically updates only the selected host.

The semantic roles are:

| Role | Intended work |
| --- | --- |
| `fast-explorer` | Broad, inexpensive repository tracing |
| `feature-worker` | Bounded specification-driven implementation |
| `bug-worker` | Evidence-led diagnosis and repair |
| `deep-judgment` | Architecture and synthesis |
| `skeptical-reviewer` | Adversarial review |
| `independent-judge` | Final evaluation separate from candidates |

`inherit-parent` is always valid. It means the host should omit an explicit
model override and use the parent chat's model.

Codex and Cursor mappings coexist:

```json
{
  "schema_version": 2,
  "host_override": "auto",
  "hosts": {
    "codex": {
      "roles": {
        "fast-explorer": {"model": "gpt-5.6-luna", "effort": "xhigh"},
        "feature-worker": {"model": "gpt-5.6-sol", "effort": "medium"},
        "bug-worker": {"model": "gpt-5.6-sol", "effort": "medium"},
        "deep-judgment": {"model": "gpt-5.6-sol", "effort": "medium"},
        "skeptical-reviewer": {"model": "gpt-5.6-sol", "effort": "medium"},
        "independent-judge": {"model": "gpt-5.6-sol", "effort": "medium"}
      },
      "invalid_bindings": []
    }
  },
  "panels": {
    "arena-runners": ["skeptical-reviewer", "deep-judgment"],
    "arena-cross-judge": ["independent-judge"],
    "interrogate-reviewers": [
      "deep-judgment",
      "bug-worker",
      "fast-explorer",
      "skeptical-reviewer"
    ],
    "architect-runners": ["deep-judgment", "skeptical-reviewer"]
  }
}
```

The concrete example is valid only when the current Codex operation or installed
Codex catalog exposes those exact pairs. For any host without a trustworthy
catalog, use `{"model": "inherit-parent", "effort": "inherit-parent"}` or
retain exact user-supplied values while clearly labeling validation unavailable.

## Migrate schema version 1

After updating the installed copy, migrate the existing personal configuration:

```bash
python3 ~/.agents/skills/setup-dstack/scripts/configure.py migrate
```

Migration changes each version 1 model string into a version 2 binding with
`"effort": "inherit-parent"`. It translates stale model entries into invalid
bindings and does not invent a host effort. A later confirmed `setup-dstack`
run can set effort from the active host catalog.

Next: [Understand how dstack works](./02-how-dstack-works.md).
