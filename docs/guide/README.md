# The dstack guide

dstack keeps pstack's engineering workflows while making model selection,
agent lifecycle, and capability degradation explicit across hosts.

Read these pages in order the first time:

1. [Install and configure dstack](./01-install-and-configure.md)
2. [Understand how dstack works](./02-how-dstack-works.md)
3. [Route work through dstack-mode](./03-dstack-mode.md)
4. [Choose focused workflows](./04-workflows.md)
5. [Maintain dstack and sync pstack](./05-maintaining-dstack.md)

If you remember one thing, give the agent a concrete goal and a checkable
finish condition:

```text
dstack-mode: retries produce duplicate rows. Reproduce the failure, fix the
cause, and prove both normal and retry paths with the real command.
```

You do not need to manually sequence `how`, `architect`, `arena`, and the other
skills. `dstack-mode` selects the playbook and invokes focused workflows when
their decision point arrives.

Maintainers should read [REMAINING.md](../../REMAINING.md) before syncing an
upstream release or changing a portability boundary.
