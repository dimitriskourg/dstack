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

The installer is intentionally first-install-only. If any destination skill,
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
- update or uninstall dstack;
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

## Configure models in each host

Run `setup-dstack` in Codex, Cursor, or another supported host where you want
custom model assignments.

The skill:

1. selects the active host adapter;
2. enumerates models only from a trustworthy host catalogue;
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
  "schema_version": 1,
  "host_override": "auto",
  "hosts": {
    "codex": {
      "roles": {
        "fast-explorer": "inherit-parent",
        "feature-worker": "inherit-parent",
        "bug-worker": "inherit-parent",
        "deep-judgment": "inherit-parent",
        "skeptical-reviewer": "inherit-parent",
        "independent-judge": "inherit-parent"
      },
      "stale_models": []
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

The example intentionally uses `inherit-parent`; never invent a real model
identifier from documentation or another host.

Next: [Understand how dstack works](./02-how-dstack-works.md).
